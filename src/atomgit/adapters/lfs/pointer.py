"""Canonical Git LFS pointer protocol for AtomGit's HF-compatible API."""

import base64
import http.client
import json
import re
import socket
import ssl
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional
from urllib.parse import quote, urlencode

import huggingface_hub.hf_api as hf_api

from ...core.contracts import _RESUMABLE_DEFAULT_REQUEST_TIMEOUT

_ATOMGIT_V5_API_BASE = "https://api.atomgit.com/api/v5"
_MAX_POINTER_RESPONSE_BYTES = 64 * 1024
_POINTER_VERIFICATION_BACKOFF_SECONDS = (2.0, 4.0)
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_COMMIT_REVISION_PATTERN = re.compile(r"[0-9a-f]{40,64}")
_CONFIRMATION_FAILURE_CODES = frozenset(
    {
        "authentication_failed",
        "permission_denied",
        "pointer_unavailable",
        "rate_limited",
        "service_unavailable",
        "request_timeout",
        "connection_failed",
        "request_rejected",
        "response_too_large",
        "response_malformed",
        "content_mismatch",
        "unknown_read_failure",
    }
)
_PATCH_LOCK = threading.Lock()
_EXPECTATIONS: ContextVar[Optional[List["CanonicalLfsPointer"]]] = ContextVar(
    "atomgit_canonical_lfs_expectations", default=None
)


class CanonicalLfsPointerError(RuntimeError):
    """AtomGit could not produce or verify a canonical Git LFS pointer."""

    confirmation_failure = None

    @classmethod
    def _for_confirmation_failure(cls, message: str, confirmation_failure):
        error = cls(message)
        error.confirmation_failure = (
            confirmation_failure
            if isinstance(confirmation_failure, str)
            and confirmation_failure in _CONFIRMATION_FAILURE_CODES
            else "unknown_read_failure"
        )
        return error


def _validated_commit_revision(commit_revision: str) -> str:
    if (
        not isinstance(commit_revision, str)
        or _COMMIT_REVISION_PATTERN.fullmatch(commit_revision) is None
    ):
        raise CanonicalLfsPointerError("commit revision is unavailable")
    return commit_revision


class CanonicalLfsCommitUnconfirmedError(CanonicalLfsPointerError):
    """A returned remote commit could not be confirmed by pointer checks."""

    remote_commit_status = "created"
    local_confirmation_status = "unconfirmed"
    confirmation_failure = "unknown_read_failure"

    def __init__(self, commit_revision: str):
        self.commit_revision = _validated_commit_revision(commit_revision)
        super().__init__(
            "remote commit was created but its LFS pointers are unconfirmed"
        )


@dataclass(frozen=True)
class CanonicalLfsPointer:
    """Expected raw Git blob for one committed LFS path."""

    path_in_repo: str
    oid: str
    size: int
    content: bytes


def canonical_lfs_pointer(oid: str, size: int) -> bytes:
    """Serialize one strict Git LFS v1 pointer using fixed ASCII LF bytes."""
    if not isinstance(oid, str) or _SHA256_PATTERN.fullmatch(oid) is None:
        raise CanonicalLfsPointerError("LFS SHA-256 metadata is invalid")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise CanonicalLfsPointerError("LFS size metadata is invalid")
    return (
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{oid}\n"
        f"size {size}\n"
    ).encode("ascii")


def _record_expectation(
    expectations: List[CanonicalLfsPointer],
    expectation: CanonicalLfsPointer,
) -> None:
    for existing in expectations:
        if existing.path_in_repo != expectation.path_in_repo:
            continue
        if existing != expectation:
            raise CanonicalLfsPointerError(
                "conflicting LFS metadata for " + repr(expectation.path_in_repo)
            )
        return
    expectations.append(expectation)


def _expectation(path_in_repo, oid, size) -> CanonicalLfsPointer:
    if not isinstance(path_in_repo, str) or not path_in_repo:
        raise CanonicalLfsPointerError("LFS repository path is invalid")
    pointer = canonical_lfs_pointer(oid, size)
    return CanonicalLfsPointer(
        path_in_repo=path_in_repo,
        oid=oid,
        size=size,
        content=pointer,
    )


def _canonical_payload_wrapper(original_prepare):
    def prepare(*args, **kwargs):
        for item in original_prepare(*args, **kwargs):
            expectations = _EXPECTATIONS.get()
            if expectations is None or item.get("key") != "lfsFile":
                yield item
                continue
            value = item.get("value")
            if not isinstance(value, dict):
                raise CanonicalLfsPointerError("LFS commit metadata is malformed")
            if value.get("algo") != "sha256":
                raise CanonicalLfsPointerError("LFS algorithm metadata is invalid")
            expectation = _expectation(
                value.get("path"), value.get("oid"), value.get("size")
            )
            _record_expectation(expectations, expectation)
            yield {
                "key": "file",
                "value": {
                    "content": base64.b64encode(expectation.content).decode("ascii"),
                    "path": expectation.path_in_repo,
                    "encoding": "base64",
                },
            }

    prepare._atomgit_canonical_lfs_wrapper = True
    return prepare


def _preupload_wrapper(original_preupload):
    def preupload(self, *args, **kwargs):
        expectations = _EXPECTATIONS.get()
        if expectations is None:
            return original_preupload(self, *args, **kwargs)
        call_args = list(args)
        call_kwargs = dict(kwargs)
        if "additions" in call_kwargs:
            additions = list(call_kwargs["additions"])
            call_kwargs["additions"] = additions
        elif len(call_args) >= 2:
            additions = list(call_args[1])
            call_args[1] = additions
        else:
            raise CanonicalLfsPointerError(
                "locked HF preupload additions are unavailable"
            )
        result = original_preupload(self, *call_args, **call_kwargs)
        for addition in additions:
            if getattr(addition, "_upload_mode", None) != "lfs" or getattr(
                addition, "_should_ignore", False
            ):
                continue
            upload_info = getattr(addition, "upload_info", None)
            sha256 = getattr(upload_info, "sha256", None)
            size = getattr(upload_info, "size", None)
            if not isinstance(sha256, bytes):
                raise CanonicalLfsPointerError("LFS SHA-256 metadata is invalid")
            expectation = _expectation(
                getattr(addition, "path_in_repo", None), sha256.hex(), size
            )
            _record_expectation(expectations, expectation)
        return result

    preupload._atomgit_canonical_lfs_preupload_wrapper = True
    return preupload


def _install_payload_wrapper() -> None:
    """Install context-gated wrappers around the locked HF commit boundary."""
    with _PATCH_LOCK:
        current_payload = hf_api._prepare_commit_payload
        if not getattr(current_payload, "_atomgit_canonical_lfs_wrapper", False):
            hf_api._prepare_commit_payload = _canonical_payload_wrapper(current_payload)
        current_preupload = hf_api.HfApi.preupload_lfs_files
        if not getattr(
            current_preupload,
            "_atomgit_canonical_lfs_preupload_wrapper",
            False,
        ):
            hf_api.HfApi.preupload_lfs_files = _preupload_wrapper(current_preupload)


@contextmanager
def canonical_lfs_payloads():
    """Canonicalize LFS payloads and collect exact blobs for verification."""
    _install_payload_wrapper()
    expectations: List[CanonicalLfsPointer] = []
    token = _EXPECTATIONS.set(expectations)
    try:
        yield expectations
    finally:
        _EXPECTATIONS.reset(token)


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        raise urllib.error.HTTPError(
            request.full_url,
            code,
            "unexpected AtomGit API redirect",
            headers,
            file_pointer,
        )


def _open_atomgit_url(request, timeout):
    opener = urllib.request.build_opener(_RejectRedirects())
    return opener.open(request, timeout=timeout)


def _repository_path(repo_id: str) -> str:
    if not isinstance(repo_id, str):
        raise CanonicalLfsPointerError("repository ID is invalid")
    owner, separator, repository = repo_id.partition("/")
    if not separator or not owner or not repository:
        raise CanonicalLfsPointerError("repository ID is invalid")
    return "/repos/{}/{}".format(quote(owner, safe=""), quote(repository, safe=""))


def _pointer_read_failure(error: Exception) -> str:
    if isinstance(error, urllib.error.HTTPError):
        status_code = error.code
        if status_code == 401:
            return "authentication_failed"
        if status_code == 403:
            return "permission_denied"
        if status_code == 404:
            return "pointer_unavailable"
        if status_code == 429:
            return "rate_limited"
        if isinstance(status_code, int) and 500 <= status_code <= 599:
            return "service_unavailable"
        return "request_rejected"
    reason = error.reason if isinstance(error, urllib.error.URLError) else error
    if isinstance(reason, TimeoutError):
        return "request_timeout"
    if isinstance(error, urllib.error.URLError) or isinstance(
        reason,
        (ConnectionError, socket.gaierror, ssl.SSLError, http.client.HTTPException),
    ):
        return "connection_failed"
    return "unknown_read_failure"


def _read_raw_pointer(
    *,
    token: str,
    repo_id: str,
    revision: str,
    expectation: CanonicalLfsPointer,
    timeout: float,
) -> bytes:
    if not token:
        raise CanonicalLfsPointerError("AtomGit credential is unavailable")
    if not isinstance(revision, str) or not revision:
        raise CanonicalLfsPointerError("commit revision is unavailable")
    if (
        not isinstance(timeout, (int, float))
        or isinstance(timeout, bool)
        or timeout <= 0
    ):
        raise CanonicalLfsPointerError("pointer verification timeout is invalid")
    encoded_path = quote(expectation.path_in_repo, safe="/")
    query = urlencode({"ref": revision})
    url = (
        _ATOMGIT_V5_API_BASE
        + _repository_path(repo_id)
        + "/contents/"
        + encoded_path
        + "?"
        + query
    )
    request = urllib.request.Request(
        url,
        headers={
            "PRIVATE-TOKEN": token,
            "Accept": "application/json",
            "User-Agent": "atomgit-cli",
        },
        method="GET",
    )
    try:
        with _open_atomgit_url(request, timeout=timeout) as response:
            payload = response.read(_MAX_POINTER_RESPONSE_BYTES + 1)
    except Exception as error:
        # The transport exception may contain the authenticated repository URL,
        # revision, response text, or other remote details.  Collapse it at this
        # boundary so CLI, SDK, and resumable callers all fail closed under the
        # same credential-safe pointer-verification contract.
        raise CanonicalLfsPointerError._for_confirmation_failure(
            "raw Git LFS pointer could not be retrieved for verification",
            _pointer_read_failure(error),
        ) from None
    if len(payload) > _MAX_POINTER_RESPONSE_BYTES:
        raise CanonicalLfsPointerError._for_confirmation_failure(
            "pointer verification response is too large",
            "response_too_large",
        )
    try:
        document = json.loads(payload.decode("utf-8"))
        if not isinstance(document, dict) or document.get("encoding") != "base64":
            raise ValueError
        raw = base64.b64decode(document["content"], validate=True)
    except (KeyError, TypeError, ValueError, UnicodeError):
        raise CanonicalLfsPointerError._for_confirmation_failure(
            "pointer verification response is malformed",
            "response_malformed",
        ) from None
    return raw


def verify_canonical_lfs_pointers(
    *,
    token: str,
    repo_id: str,
    revision: str,
    expectations: Iterable[CanonicalLfsPointer],
    timeout: float = _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
) -> None:
    """Verify committed raw Git blobs without resolving large LFS objects."""
    if not token:
        raise CanonicalLfsPointerError("AtomGit credential is unavailable")
    _repository_path(repo_id)
    if not isinstance(revision, str) or not revision:
        raise CanonicalLfsPointerError("commit revision is unavailable")
    if (
        not isinstance(timeout, (int, float))
        or isinstance(timeout, bool)
        or timeout <= 0
    ):
        raise CanonicalLfsPointerError("pointer verification timeout is invalid")

    for expectation in expectations:
        for attempt in range(len(_POINTER_VERIFICATION_BACKOFF_SECONDS) + 1):
            try:
                raw = _read_raw_pointer(
                    token=token,
                    repo_id=repo_id,
                    revision=revision,
                    expectation=expectation,
                    timeout=timeout,
                )
                if raw != expectation.content:
                    raise CanonicalLfsPointerError._for_confirmation_failure(
                        "AtomGit generated a noncanonical Git LFS pointer",
                        "content_mismatch",
                    )
            except CanonicalLfsPointerError:
                if attempt == len(_POINTER_VERIFICATION_BACKOFF_SECONDS):
                    raise
                time.sleep(_POINTER_VERIFICATION_BACKOFF_SECONDS[attempt])
            else:
                break


def run_canonical_lfs_upload(
    upload: Callable,
    *,
    token: str,
    repo_id: str,
    timeout: float = _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
):
    """Run one HF upload and verify every LFS blob at its returned commit."""
    with canonical_lfs_payloads() as expectations:
        result = upload()
    if expectations:
        try:
            revision = _validated_commit_revision(getattr(result, "oid", None))
        except CanonicalLfsPointerError as error:
            raise CanonicalLfsPointerError(
                "AtomGit upload did not return a commit for pointer verification"
            ) from error
        try:
            verify_canonical_lfs_pointers(
                token=token,
                repo_id=repo_id,
                revision=revision,
                expectations=expectations,
                timeout=timeout,
            )
        except CanonicalLfsPointerError as error:
            raise CanonicalLfsCommitUnconfirmedError._for_confirmation_failure(
                revision,
                error.confirmation_failure,
            ) from error
    return result
