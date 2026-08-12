"""Canonical Git LFS pointer payloads for AtomGit's HF-compatible API."""

import base64
import json
import re
import threading
import urllib.error
import urllib.request
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional
from urllib.parse import quote, urlencode

import huggingface_hub.hf_api as hf_api


_ATOMGIT_V5_API_BASE = "https://api.atomgit.com/api/v5"
_MAX_POINTER_RESPONSE_BYTES = 64 * 1024
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_PATCH_LOCK = threading.Lock()
_EXPECTATIONS: ContextVar[Optional[List["CanonicalLfsPointer"]]] = ContextVar(
    "atomgit_canonical_lfs_expectations", default=None
)


class CanonicalLfsPointerError(RuntimeError):
    """AtomGit could not produce or verify a canonical Git LFS pointer."""


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
            if (
                getattr(addition, "_upload_mode", None) != "lfs"
                or getattr(addition, "_should_ignore", False)
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
            hf_api._prepare_commit_payload = _canonical_payload_wrapper(
                current_payload
            )
        current_preupload = hf_api.HfApi.preupload_lfs_files
        if not getattr(
            current_preupload,
            "_atomgit_canonical_lfs_preupload_wrapper",
            False,
        ):
            hf_api.HfApi.preupload_lfs_files = _preupload_wrapper(
                current_preupload
            )


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
            request.full_url, code, "unexpected AtomGit API redirect", headers, file_pointer
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
    return "/repos/{}/{}".format(
        quote(owner, safe=""), quote(repository, safe="")
    )


def _read_raw_pointer(
    *, token: str, repo_id: str, revision: str,
    expectation: CanonicalLfsPointer, timeout: float,
) -> bytes:
    if not token:
        raise CanonicalLfsPointerError("AtomGit credential is unavailable")
    if not isinstance(revision, str) or not revision:
        raise CanonicalLfsPointerError("commit revision is unavailable")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
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
    except Exception:
        # The transport exception may contain the authenticated repository URL,
        # revision, response text, or other remote details.  Collapse it at this
        # boundary so CLI, SDK, and resumable callers all fail closed under the
        # same credential-safe pointer-verification contract.
        raise CanonicalLfsPointerError(
            "raw Git LFS pointer could not be retrieved for verification"
        ) from None
    if len(payload) > _MAX_POINTER_RESPONSE_BYTES:
        raise CanonicalLfsPointerError("pointer verification response is too large")
    try:
        document = json.loads(payload.decode("utf-8"))
        if not isinstance(document, dict) or document.get("encoding") != "base64":
            raise ValueError
        raw = base64.b64decode(document["content"], validate=True)
    except (KeyError, TypeError, ValueError, UnicodeError) as error:
        raise CanonicalLfsPointerError(
            "pointer verification response is malformed"
        ) from error
    return raw


def verify_canonical_lfs_pointers(
    *, token: str, repo_id: str, revision: str,
    expectations: Iterable[CanonicalLfsPointer], timeout: float = 15,
) -> None:
    """Verify committed raw Git blobs without resolving large LFS objects."""
    for expectation in expectations:
        raw = _read_raw_pointer(
            token=token,
            repo_id=repo_id,
            revision=revision,
            expectation=expectation,
            timeout=timeout,
        )
        if raw != expectation.content:
            raise CanonicalLfsPointerError(
                "AtomGit generated a noncanonical Git LFS pointer for "
                + repr(expectation.path_in_repo)
            )


def run_canonical_lfs_upload(
    upload: Callable,
    *,
    token: str,
    repo_id: str,
    timeout: float = 15,
):
    """Run one HF upload and verify every LFS blob at its returned commit."""
    with canonical_lfs_payloads() as expectations:
        result = upload()
    if expectations:
        revision = getattr(result, "oid", None)
        if not isinstance(revision, str) or not revision:
            raise CanonicalLfsPointerError(
                "AtomGit upload did not return a commit for pointer verification"
            )
        verify_canonical_lfs_pointers(
            token=token,
            repo_id=repo_id,
            revision=revision,
            expectations=expectations,
            timeout=timeout,
        )
    return result
