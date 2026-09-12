"""Isolated resumable upload orchestration and commit reconciliation."""

import hashlib
import json
import multiprocessing
import os
import queue
import random
import re
import socket
import stat
import tempfile
import time
import urllib.error
from contextlib import contextmanager
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path, PurePosixPath
from typing import Optional, Set
from urllib.parse import quote

import httpx
import huggingface_hub._upload_large_folder as hf_large_folder
from huggingface_hub import HfApi
from huggingface_hub import close_session as close_hf_session
from huggingface_hub import constants as hf_constants
from huggingface_hub._local_folder import get_local_upload_paths, read_upload_metadata

from ..download.integrity import _atomgit_file_checksum
from ..download.transport import _atomgit_hf_endpoint
from ..lfs.pointer import (
    CanonicalLfsCommitUnconfirmedError,
    CanonicalLfsPointer,
    CanonicalLfsPointerError,
    _validated_commit_revision,
    canonical_lfs_payloads,
    canonical_lfs_pointer,
    verify_canonical_lfs_pointers,
)
from ..lfs.service import _dispatch_upload_observation, set_upload_observer
from .contracts import _RESUMABLE_DEFAULT_REQUEST_TIMEOUT
from .errors import (
    ResumableCommitConflictError,
    ResumableCommitError,
    ResumableRecoveryStateError,
    ResumableTargetRevisionError,
    ResumableWorkerError,
    _resumable_failure_envelope,
)

# Program-step 9 LFS policy slots are wired by atomgit.api.
_atomgit_v5_get_json = None
_atomgit_v5_repo_path = None
_atomgit_v5_commit_sha = None
ResumableUploadModeError = None
ResumableLfsAttributesError = None
_ResumableLfsAttributesPolicy = None
_ResumableLfsPreuploadController = None
_SlowFlowCoordinator = None
_print_resumable_lfs_preupload_event = None
_print_resumable_slow_flow_event = None
_refresh_unsafe_resumable_upload_modes = None
_resumable_projection_lfs_patterns = None
_scoped_resumable_lfs_recovery = None
_validate_resumable_commit_operations = None
_validate_resumable_upload_mode_items = None

_RESUMABLE_COMMIT_MAX_ATTEMPTS = 5

_RESUMABLE_COMMIT_BACKOFF_BASE = 30.0

_RESUMABLE_COMMIT_BACKOFF_CAP = 300.0

_RESUMABLE_COMMIT_BATCH_SIZES = (20, 10, 5, 2, 1)

_PENDING_COMMIT_VERSION = 1

_PENDING_COMMIT_MAX_BYTES = 64 * 1024

_PENDING_COMMIT_MAX_OPERATIONS = 20

_UPLOAD_OBSERVATION_QUEUE_SIZE = 256

_UPLOAD_OBSERVATION_MAX_BYTES = 16 * 1024

_UPLOAD_OBSERVATION_FIELDS = {"version", "type", "sequence", "flow_key", "payload"}

_PENDING_COMMIT_DIRECTORY = Path(".cache/huggingface/atomgit")

_PENDING_COMMIT_FILENAME = "pending-commit-v1.json"

_PENDING_COMMIT_LOCK_FILENAME = "pending-commit-v1.lock"

_SHA1_PATTERN = re.compile(r"[0-9a-f]{40}")

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class _UploadObservationSender:
    """Best-effort child sender for versioned observation messages."""

    def __init__(self, observation_queue):
        self._queue = observation_queue
        self._sequence = 0

    def send(self, message) -> None:
        if (
            self._queue is None
            or not isinstance(message, dict)
            or set(message) != {"type", "flow_key", "payload"}
            or message.get("type") not in ("flow_state", "flow_event")
            or not isinstance(message.get("flow_key"), int)
            or isinstance(message.get("flow_key"), bool)
            or message["flow_key"] <= 0
            or not isinstance(message.get("payload"), dict)
        ):
            return
        self._sequence += 1
        envelope = {
            "version": 1,
            "type": message["type"],
            "sequence": self._sequence,
            "flow_key": message["flow_key"],
            "payload": message["payload"],
        }
        try:
            encoded = json.dumps(
                envelope,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            ).encode("utf-8")
            if len(encoded) > _UPLOAD_OBSERVATION_MAX_BYTES:
                return
            self._queue.put_nowait(encoded)
        except Exception:
            pass


def _decode_upload_observation(value) -> Optional[dict]:
    """Decode one bounded v1 envelope; malformed observations are discarded."""
    if not isinstance(value, bytes) or len(value) > _UPLOAD_OBSERVATION_MAX_BYTES:
        return None
    try:
        envelope = json.loads(value.decode("utf-8"))
    except (UnicodeError, ValueError, TypeError):
        return None
    if (
        not isinstance(envelope, dict)
        or set(envelope) != _UPLOAD_OBSERVATION_FIELDS
        or envelope.get("version") != 1
        or envelope.get("type") not in ("flow_state", "flow_event")
        or not isinstance(envelope.get("sequence"), int)
        or isinstance(envelope.get("sequence"), bool)
        or envelope["sequence"] <= 0
        or not isinstance(envelope.get("flow_key"), int)
        or isinstance(envelope.get("flow_key"), bool)
        or envelope["flow_key"] <= 0
        or not isinstance(envelope.get("payload"), dict)
    ):
        return None
    return envelope


def _drain_upload_observations(observation_queue, source_id) -> None:
    while True:
        try:
            value = observation_queue.get_nowait()
        except (queue.Empty, AttributeError, EOFError, OSError, ValueError):
            return
        envelope = _decode_upload_observation(value)
        if envelope is not None:
            _dispatch_upload_observation(source_id, envelope=envelope)


def _close_upload_observation_queue(observation_queue) -> None:
    for method_name in ("close", "join_thread"):
        try:
            method = getattr(observation_queue, method_name, None)
            if callable(method):
                method()
        except Exception:
            pass


def _pending_commit_paths(folder_path: Path):
    directory = Path(folder_path) / _PENDING_COMMIT_DIRECTORY
    return (
        directory,
        directory / _PENDING_COMMIT_FILENAME,
        directory / _PENDING_COMMIT_LOCK_FILENAME,
    )


def _ensure_pending_commit_directory(directory: Path) -> None:
    if directory.exists() and (not directory.is_dir() or directory.is_symlink()):
        raise ResumableRecoveryStateError("pending commit directory is unsafe")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(directory, 0o700)


def _validated_pending_commit_operation(value) -> dict:
    keys = {"path", "size", "sha256", "upload_mode", "git_sha1"}
    if not isinstance(value, dict) or set(value) != keys:
        raise ResumableRecoveryStateError("pending commit operation is malformed")
    path = value["path"]
    parsed = PurePosixPath(path) if isinstance(path, str) else None
    if (
        parsed is None
        or not path
        or "\\" in path
        or parsed.is_absolute()
        or parsed.as_posix() != path
        or any(part in ("", ".", "..") for part in parsed.parts)
    ):
        raise ResumableRecoveryStateError("pending commit path is invalid")
    size = value["size"]
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise ResumableRecoveryStateError("pending commit size is invalid")
    sha256 = value["sha256"]
    if not isinstance(sha256, str) or _SHA256_PATTERN.fullmatch(sha256) is None:
        raise ResumableRecoveryStateError("pending commit digest is invalid")
    upload_mode = value["upload_mode"]
    if upload_mode not in ("regular", "lfs"):
        raise ResumableRecoveryStateError("pending commit mode is invalid")
    git_sha1 = value["git_sha1"]
    if upload_mode == "regular":
        if not isinstance(git_sha1, str) or _SHA1_PATTERN.fullmatch(git_sha1) is None:
            raise ResumableRecoveryStateError("pending commit blob digest is invalid")
    elif git_sha1 is not None:
        raise ResumableRecoveryStateError("pending LFS blob digest is invalid")
    return dict(value)


def _validated_pending_commit(value) -> dict:
    keys = {"version", "state", "base_revision", "commit_revision", "operations"}
    if not isinstance(value, dict) or set(value) != keys:
        raise ResumableRecoveryStateError("pending commit state is malformed")
    if value["version"] != _PENDING_COMMIT_VERSION:
        raise ResumableRecoveryStateError("pending commit version is unsupported")
    state = value["state"]
    if state not in ("attempting", "created_unconfirmed"):
        raise ResumableRecoveryStateError("pending commit status is invalid")
    base_revision = value["base_revision"]
    if base_revision is not None:
        try:
            base_revision = _validated_commit_revision(base_revision)
        except CanonicalLfsPointerError as error:
            raise ResumableRecoveryStateError(
                "pending commit base revision is invalid"
            ) from error
    commit_revision = value["commit_revision"]
    if state == "attempting" and commit_revision is not None:
        raise ResumableRecoveryStateError("attempting commit revision is invalid")
    if state == "created_unconfirmed":
        try:
            commit_revision = _validated_commit_revision(commit_revision)
        except CanonicalLfsPointerError as error:
            raise ResumableRecoveryStateError(
                "pending commit revision is invalid"
            ) from error
    operations = value["operations"]
    if (
        not isinstance(operations, list)
        or not operations
        or len(operations) > _PENDING_COMMIT_MAX_OPERATIONS
    ):
        raise ResumableRecoveryStateError("pending commit operation count is invalid")
    validated = [_validated_pending_commit_operation(item) for item in operations]
    paths = [item["path"] for item in validated]
    if len(paths) != len(set(paths)):
        raise ResumableRecoveryStateError("pending commit paths are duplicated")
    return {
        "version": _PENDING_COMMIT_VERSION,
        "state": state,
        "base_revision": base_revision,
        "commit_revision": commit_revision,
        "operations": validated,
    }


def _read_pending_commit(folder_path: Path) -> Optional[dict]:
    directory, pending_path, _ = _pending_commit_paths(folder_path)
    if not pending_path.exists():
        return None
    if pending_path.is_symlink() or not pending_path.is_file():
        raise ResumableRecoveryStateError("pending commit file is unsafe")
    if os.name != "nt":
        if stat.S_IMODE(directory.stat().st_mode) & 0o077:
            raise ResumableRecoveryStateError(
                "pending commit directory permissions are unsafe"
            )
        if stat.S_IMODE(pending_path.stat().st_mode) & 0o077:
            raise ResumableRecoveryStateError(
                "pending commit file permissions are unsafe"
            )
    with pending_path.open("rb") as stream:
        payload = stream.read(_PENDING_COMMIT_MAX_BYTES + 1)
    if len(payload) > _PENDING_COMMIT_MAX_BYTES:
        raise ResumableRecoveryStateError("pending commit file is too large")
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ResumableRecoveryStateError("pending commit file is malformed") from error
    return _validated_pending_commit(value)


def _write_pending_commit(folder_path: Path, value: dict) -> None:
    value = _validated_pending_commit(value)
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(payload) > _PENDING_COMMIT_MAX_BYTES:
        raise ResumableRecoveryStateError("pending commit file is too large")
    directory, pending_path, _ = _pending_commit_paths(folder_path)
    _ensure_pending_commit_directory(directory)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".pending-", dir=directory)
    try:
        if callable(getattr(os, "fchmod", None)):
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, pending_path)
        os.chmod(pending_path, 0o600)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            Path(temporary_name).unlink()
        except FileNotFoundError:
            pass


def _delete_pending_commit(folder_path: Path) -> None:
    _, pending_path, _ = _pending_commit_paths(folder_path)
    pending_path.unlink(missing_ok=True)


@contextmanager
def _resumable_projection_lock(folder_path: Path):
    """Serialize one stable projection across local upload processes."""
    directory, _, lock_path = _pending_commit_paths(folder_path)
    _ensure_pending_commit_directory(directory)
    if lock_path.is_symlink() or (lock_path.exists() and not lock_path.is_file()):
        raise ResumableRecoveryStateError("pending commit lock file is unsafe")
    with lock_path.open("a+b") as stream:
        os.chmod(lock_path, 0o600)
        if os.name == "nt":
            import msvcrt

            if stream.seek(0, os.SEEK_END) == 0:
                stream.write(b"\0")
                stream.flush()
            stream.seek(0)
            while True:
                try:
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _commit_error_status(error: BaseException) -> Optional[int]:
    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)
    return status_code if isinstance(status_code, int) else None


def _resolve_resumable_revision(
    *, token: str, repo_id: str, revision: str, request_timeout: float
) -> str:
    path = _atomgit_v5_repo_path(repo_id)
    path += "/commits/" + quote(revision or "main", safe="")
    payload = _atomgit_v5_get_json(path, token, timeout=request_timeout)
    commit_sha = _atomgit_v5_commit_sha(payload)
    try:
        return _validated_commit_revision(commit_sha)
    except CanonicalLfsPointerError as error:
        raise ResumableRecoveryStateError(
            "target revision could not be resolved"
        ) from error


def _operation_pending_record(operation) -> dict:
    path = getattr(operation, "path_in_repo", None)
    upload_info = getattr(operation, "upload_info", None)
    size = getattr(upload_info, "size", None)
    sha256 = getattr(upload_info, "sha256", None)
    upload_mode = getattr(operation, "_upload_mode", None)
    record = {
        "path": path,
        "size": size,
        "sha256": sha256.hex() if isinstance(sha256, bytes) else None,
        "upload_mode": upload_mode,
        "git_sha1": (
            _operation_git_sha1(operation) if upload_mode == "regular" else None
        ),
    }
    return _validated_pending_commit_operation(record)


def _pending_commit_value(
    *, state: str, base_revision: str, commit_revision, operations
) -> dict:
    return _validated_pending_commit(
        {
            "version": _PENDING_COMMIT_VERSION,
            "state": state,
            "base_revision": base_revision,
            "commit_revision": commit_revision,
            "operations": [_operation_pending_record(item) for item in operations],
        }
    )


def _local_pending_record_matches(folder_path: Path, record: dict) -> bool:
    candidate = Path(folder_path).joinpath(*PurePosixPath(record["path"]).parts)
    try:
        if candidate.is_symlink() or not candidate.is_file():
            return False
        digest = hashlib.sha256()
        with candidate.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        if candidate.stat().st_size != record["size"]:
            return False
        if digest.hexdigest() != record["sha256"]:
            return False
        if record["upload_mode"] == "regular":
            operation = type(
                "_PendingOperation",
                (),
                {
                    "path_or_fileobj": candidate,
                    "upload_info": type("_UploadInfo", (), {"size": record["size"]})(),
                },
            )()
            return _operation_git_sha1(operation) == record["git_sha1"]
        return True
    except OSError:
        return False


def _mark_pending_records_committed(folder_path: Path, records) -> None:
    for record in records:
        paths = get_local_upload_paths(Path(folder_path), record["path"])
        metadata = read_upload_metadata(Path(folder_path), record["path"])
        if (
            metadata.sha256 != record["sha256"]
            or metadata.size != record["size"]
            or metadata.upload_mode != record["upload_mode"]
        ):
            raise ResumableRecoveryStateError(
                "resumable metadata changed before recovery"
            )
        metadata.is_committed = True
        metadata.save(paths)


def _remote_pending_record_matches(
    *,
    record: dict,
    repo_id: str,
    repo_type: str,
    revision: str,
    token: str,
    request_timeout: float,
) -> bool:
    try:
        algorithm, digest, size = _atomgit_file_checksum(
            repo_id,
            repo_type,
            record["path"],
            token,
            revision,
        )
    except Exception as error:
        if _commit_error_status(error) == 404 or getattr(error, "code", None) == 404:
            return False
        raise ResumableRecoveryStateError(
            "remote pending commit state could not be read"
        ) from error
    if size != record["size"]:
        return False
    if record["upload_mode"] == "regular":
        return algorithm == "git-sha1" and digest == record["git_sha1"]
    if algorithm != "sha256" or digest != record["sha256"]:
        return False
    expectation = CanonicalLfsPointer(
        path_in_repo=record["path"],
        oid=record["sha256"],
        size=record["size"],
        content=canonical_lfs_pointer(record["sha256"], record["size"]),
    )
    try:
        verify_canonical_lfs_pointers(
            token=token,
            repo_id=repo_id,
            revision=revision,
            expectations=[expectation],
            timeout=request_timeout,
        )
    except CanonicalLfsPointerError as error:
        raise ResumableRecoveryStateError(
            "remote LFS pointer could not be confirmed"
        ) from error
    return True


def _recover_pending_commit(
    *,
    folder_path: Path,
    token: str,
    repo_id: str,
    repo_type: str,
    revision: str,
    request_timeout: float,
) -> dict:
    pending = _read_pending_commit(folder_path)
    if pending is None:
        return {"confirmed": 0, "remaining": 0, "confirmed_paths": ()}
    for record in pending["operations"]:
        if not _local_pending_record_matches(folder_path, record):
            raise ResumableRecoveryStateError(
                "local content changed while a commit remains pending",
                confirmed=0,
                remaining=len(pending["operations"]),
            )
    first_revision = _resolve_resumable_revision(
        token=token,
        repo_id=repo_id,
        revision=revision,
        request_timeout=request_timeout,
    )
    matched = [
        record
        for record in pending["operations"]
        if _remote_pending_record_matches(
            record=record,
            repo_id=repo_id,
            repo_type=repo_type,
            revision=first_revision,
            token=token,
            request_timeout=request_timeout,
        )
    ]
    second_revision = _resolve_resumable_revision(
        token=token,
        repo_id=repo_id,
        revision=revision,
        request_timeout=request_timeout,
    )
    if first_revision != second_revision:
        raise ResumableCommitConflictError(
            "target revision changed during resumable recovery",
            confirmed=0,
            remaining=len(pending["operations"]),
        )
    remaining = [item for item in pending["operations"] if item not in matched]
    if matched:
        _mark_pending_records_committed(folder_path, matched)
    if not remaining:
        _delete_pending_commit(folder_path)
    else:
        pending["operations"] = remaining
        _write_pending_commit(folder_path, pending)
        if first_revision != pending["base_revision"]:
            raise ResumableCommitConflictError(
                "pending commit conflicts with the target revision",
                confirmed=len(matched),
                remaining=len(remaining),
            )
    return {
        "confirmed": len(matched),
        "remaining": len(remaining),
        "confirmed_paths": tuple(item["path"] for item in matched),
    }


def _commit_retry_after(error: BaseException) -> Optional[float]:
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    value = headers.get("Retry-After") if headers is not None else None
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        try:
            retry_at = parsedate_to_datetime(value)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(
                0.0,
                (retry_at - datetime.now(timezone.utc)).total_seconds(),
            )
        except (TypeError, ValueError, OverflowError):
            return None


def _is_ambiguous_commit_error(error: BaseException) -> bool:
    status_code = _commit_error_status(error)
    if status_code in (502, 503, 504):
        return True
    return isinstance(
        error,
        (
            httpx.TimeoutException,
            httpx.NetworkError,
            TimeoutError,
            ConnectionError,
            socket.timeout,
        ),
    )


def _is_retryable_commit_error(error: BaseException) -> bool:
    status_code = _commit_error_status(error)
    if status_code in (429, 502, 503, 504):
        return True
    return isinstance(
        error,
        (
            httpx.TimeoutException,
            httpx.NetworkError,
            TimeoutError,
            ConnectionError,
            socket.timeout,
        ),
    )


def _is_reducible_commit_error(error: BaseException) -> bool:
    status_code = _commit_error_status(error)
    if status_code in (413, 502, 503, 504):
        return True
    return isinstance(
        error,
        (httpx.ReadTimeout, httpx.WriteTimeout, TimeoutError, socket.timeout),
    )


def _operation_git_sha1(operation) -> Optional[str]:
    upload_info = getattr(operation, "upload_info", None)
    size = getattr(upload_info, "size", None)
    source = getattr(operation, "path_or_fileobj", None)
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        return None
    digest = hashlib.sha1()
    digest.update(b"blob " + str(size).encode("ascii") + b"\0")
    try:
        if isinstance(source, bytes):
            digest.update(source)
        elif isinstance(source, (str, Path)):
            with Path(source).open("rb") as stream:
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
        elif hasattr(source, "read"):
            position = source.tell()
            try:
                source.seek(0)
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
            finally:
                source.seek(position)
        else:
            return None
    except (OSError, ValueError, AttributeError):
        return None
    return digest.hexdigest()


def _reconcile_resumable_commit_operations(
    *, repo_id: str, repo_type: str, revision: str, operations, token: str
) -> Set[str]:
    """Return paths whose remote object identity matches the commit operation."""
    if revision not in (None, "main"):
        return set()
    matched = set()
    for operation in operations:
        path_in_repo = getattr(operation, "path_in_repo", None)
        upload_info = getattr(operation, "upload_info", None)
        if not isinstance(path_in_repo, str) or upload_info is None:
            continue
        try:
            algorithm, remote_digest, remote_size = _atomgit_file_checksum(
                repo_id, repo_type, path_in_repo, token
            )
        except Exception:
            continue
        local_size = getattr(upload_info, "size", None)
        if remote_size != local_size:
            continue
        if algorithm == "sha256":
            local_sha256 = getattr(upload_info, "sha256", None)
            if isinstance(local_sha256, bytes) and local_sha256.hex() == remote_digest:
                matched.add(path_in_repo)
        elif algorithm == "git-sha1":
            if _operation_git_sha1(operation) == remote_digest:
                matched.add(path_in_repo)
    return matched


def _next_resumable_commit_batch_size(item_count: int) -> int:
    for batch_size in _RESUMABLE_COMMIT_BATCH_SIZES:
        if batch_size < item_count:
            return batch_size
    return 1


def _mark_resumable_operations_committed(folder_path: Path, operations) -> None:
    """Persist successful sub-commits before the outer HF batch completes."""
    folder_path = Path(folder_path)
    for operation in operations:
        path_in_repo = getattr(operation, "path_in_repo", None)
        upload_info = getattr(operation, "upload_info", None)
        local_sha256 = getattr(upload_info, "sha256", None)
        if not isinstance(path_in_repo, str) or not isinstance(local_sha256, bytes):
            raise ResumableCommitError("resumable commit metadata is unavailable")
        paths = get_local_upload_paths(folder_path, path_in_repo)
        metadata = read_upload_metadata(folder_path, path_in_repo)
        if metadata.sha256 != local_sha256.hex():
            raise ResumableCommitError(
                "resumable commit metadata changed during upload"
            )
        metadata.is_committed = True
        metadata.save(paths)


class _ResumableCommitController:
    """Apply AtomGit-specific retry and reconciliation to HF commit calls."""

    def __init__(
        self,
        create_commit,
        *,
        token: str,
        sleep=time.sleep,
        jitter=None,
        reconcile=_reconcile_resumable_commit_operations,
        max_attempts: int = _RESUMABLE_COMMIT_MAX_ATTEMPTS,
        mark_committed=None,
        canonical_payloads=canonical_lfs_payloads,
        verify_committed=None,
        fatal_callback=None,
        event_callback=None,
        lfs_attributes_policy=None,
        folder_path=None,
        request_timeout: float = _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
    ):
        self._create_commit = create_commit
        self._token = token
        self._sleep = sleep
        self._jitter = jitter or (
            lambda delay: random.uniform(0.0, min(1.0, delay * 0.1))
        )
        self._reconcile = reconcile
        self._max_attempts = max_attempts
        self._mark_committed = mark_committed or (lambda operations: None)
        self._canonical_payloads = canonical_payloads
        self._verify_committed = verify_committed or (
            lambda expectations, repo_id, revision: None
        )
        self._fatal_callback = fatal_callback
        self._event_callback = event_callback
        self._lfs_attributes_policy = lfs_attributes_policy
        self._folder_path = Path(folder_path) if folder_path is not None else None
        self._request_timeout = request_timeout

    def _recover_pending(self, kwargs, operations):
        if self._folder_path is None:
            return list(operations)
        try:
            recovery = _recover_pending_commit(
                folder_path=self._folder_path,
                token=self._token,
                repo_id=kwargs.get("repo_id"),
                repo_type=kwargs.get("repo_type") or "model",
                revision=kwargs.get("revision") or "main",
                request_timeout=self._request_timeout,
            )
        except (ResumableCommitConflictError, ResumableRecoveryStateError) as error:
            self._raise_fatal(error, len(operations))
        confirmed = set(recovery["confirmed_paths"])
        if recovery["confirmed"]:
            self._emit(
                "recovery_result",
                confirmed=recovery["confirmed"],
                remaining=recovery["remaining"],
            )
        return [
            operation
            for operation in operations
            if getattr(operation, "path_in_repo", None) not in confirmed
        ]

    def _write_attempt(self, kwargs, operations) -> str:
        base_revision = _resolve_resumable_revision(
            token=self._token,
            repo_id=kwargs.get("repo_id"),
            revision=kwargs.get("revision") or "main",
            request_timeout=self._request_timeout,
        )
        _write_pending_commit(
            self._folder_path,
            _pending_commit_value(
                state="attempting",
                base_revision=base_revision,
                commit_revision=None,
                operations=operations,
            ),
        )
        return base_revision

    def _write_created(self, base_revision, commit_revision, operations) -> None:
        _write_pending_commit(
            self._folder_path,
            _pending_commit_value(
                state="created_unconfirmed",
                base_revision=base_revision,
                commit_revision=commit_revision,
                operations=operations,
            ),
        )

    def _emit(self, kind: str, **details) -> None:
        if self._event_callback is None:
            return
        try:
            self._event_callback({"kind": kind, **details})
        except Exception:
            # Observability must never change upload or retry semantics.
            pass

    def _raise_fatal(self, error: BaseException, item_count: int):
        status_code = _commit_error_status(error)
        if status_code is not None:
            detail = f"HTTP {status_code}"
        else:
            detail = type(error).__name__
        wrapped = ResumableCommitError(
            f"resumable commit failed for {item_count} file(s): {detail}"
        )
        if self._fatal_callback is not None:
            self._fatal_callback(error)
        raise wrapped from error

    def _retry_delay(self, error: BaseException, attempt: int) -> float:
        retry_after = _commit_retry_after(error)
        if retry_after is not None:
            return retry_after
        delay = min(
            _RESUMABLE_COMMIT_BACKOFF_BASE * (2 ** (attempt - 1)),
            _RESUMABLE_COMMIT_BACKOFF_CAP,
        )
        return delay + self._jitter(delay)

    def _commit_group(self, args, kwargs, operations):
        operations = list(operations)
        attempts = 0
        last_error = None
        while operations and attempts < self._max_attempts:
            operations = self._recover_pending(kwargs, operations)
            if not operations:
                return None
            attempts += 1
            call_kwargs = dict(kwargs)
            call_kwargs["operations"] = operations
            expectations = []
            base_revision = None
            try:
                if self._folder_path is not None:
                    base_revision = self._write_attempt(call_kwargs, operations)
                    call_kwargs["parent_commit"] = base_revision
                with self._canonical_payloads() as expectations:
                    result = self._create_commit(*args, **call_kwargs)
                if self._folder_path is not None:
                    try:
                        commit_revision = _validated_commit_revision(
                            getattr(result, "oid", None)
                        )
                    except CanonicalLfsPointerError as error:
                        raise ResumableRecoveryStateError(
                            "resumable commit revision is unavailable"
                        ) from error
                    self._write_created(base_revision, commit_revision, operations)
                if expectations:
                    if self._folder_path is None:
                        try:
                            commit_revision = _validated_commit_revision(
                                getattr(result, "oid", None)
                            )
                        except CanonicalLfsPointerError as error:
                            raise RuntimeError(
                                "resumable commit revision is unavailable"
                            ) from error
                    try:
                        self._verify_committed(
                            expectations,
                            call_kwargs.get("repo_id"),
                            commit_revision,
                        )
                    except CanonicalLfsPointerError as error:
                        raise CanonicalLfsCommitUnconfirmedError._for_confirmation_failure(
                            commit_revision,
                            error.confirmation_failure,
                        ) from error
                self._mark_committed(operations)
                if self._folder_path is not None:
                    _delete_pending_commit(self._folder_path)
                return result
            except Exception as error:
                last_error = error
                status_code = _commit_error_status(error)
                if status_code in (409, 412):
                    self._raise_fatal(
                        ResumableCommitConflictError(
                            "target revision changed before commit",
                            confirmed=0,
                            remaining=len(operations),
                        ),
                        len(operations),
                    )
                if _is_ambiguous_commit_error(error):
                    self._emit(
                        "reconcile_start",
                        item_count=len(operations),
                        attempt=attempts,
                    )
                    if self._folder_path is not None:
                        recovered_operations = self._recover_pending(
                            call_kwargs, operations
                        )
                        matched = {
                            getattr(operation, "path_in_repo", None)
                            for operation in operations
                            if operation not in recovered_operations
                        }
                    else:
                        matched = self._reconcile(
                            repo_id=call_kwargs.get("repo_id"),
                            repo_type=call_kwargs.get("repo_type") or "model",
                            revision=call_kwargs.get("revision") or "main",
                            operations=operations,
                            token=self._token,
                        )
                    matched_operations = [
                        operation
                        for operation in operations
                        if getattr(operation, "path_in_repo", None) in matched
                    ]
                    if matched_operations:
                        matched_expectations = [
                            expectation
                            for expectation in expectations
                            if expectation.path_in_repo in matched
                        ]
                        try:
                            if matched_expectations and self._folder_path is None:
                                self._verify_committed(
                                    matched_expectations,
                                    call_kwargs.get("repo_id"),
                                    call_kwargs.get("revision") or "main",
                                )
                            if self._folder_path is None:
                                self._mark_committed(matched_operations)
                        except Exception as metadata_error:
                            self._raise_fatal(metadata_error, len(matched_operations))
                    operations = [
                        operation
                        for operation in operations
                        if getattr(operation, "path_in_repo", None) not in matched
                    ]
                    self._emit(
                        "reconcile_result",
                        confirmed=len(matched_operations),
                        remaining=len(operations),
                        attempt=attempts,
                    )
                    if not operations:
                        return None
                if status_code == 413:
                    if self._folder_path is not None:
                        _delete_pending_commit(self._folder_path)
                    break
                if self._folder_path is not None and status_code in (
                    400,
                    401,
                    403,
                    404,
                    422,
                    429,
                ):
                    _delete_pending_commit(self._folder_path)
                if not _is_retryable_commit_error(error):
                    self._raise_fatal(error, len(operations))
                if attempts < self._max_attempts:
                    delay = self._retry_delay(error, attempts)
                    if status_code == 429:
                        self._emit(
                            "rate_limit_wait",
                            delay=delay,
                            attempt=attempts,
                            item_count=len(operations),
                        )
                    self._emit(
                        "retry",
                        attempt=attempts + 1,
                        max_attempts=self._max_attempts,
                        item_count=len(operations),
                        status_code=status_code,
                        error_type=type(error).__name__,
                    )
                    self._sleep(delay)

        if not operations:
            return None
        if len(operations) == 1 or not _is_reducible_commit_error(last_error):
            self._raise_fatal(last_error, len(operations))

        batch_size = _next_resumable_commit_batch_size(len(operations))
        self._emit(
            "reduce",
            from_size=len(operations),
            to_size=batch_size,
        )
        result = None
        for index in range(0, len(operations), batch_size):
            result = self._commit_group(
                args,
                kwargs,
                operations[index : index + batch_size],
            )
        return result

    def create_commit(self, *args, **kwargs):
        operations = list(kwargs.get("operations", ()))
        if not operations:
            return self._create_commit(*args, **kwargs)
        try:
            if self._lfs_attributes_policy is not None:
                self._lfs_attributes_policy.validate_operations(operations)
            _validate_resumable_commit_operations(operations)
        except (ResumableUploadModeError, ResumableLfsAttributesError) as error:
            if self._fatal_callback is not None:
                self._fatal_callback(error)
            raise
        return self._commit_group(args, kwargs, operations)


def _print_resumable_commit_event(event, batch_context) -> None:
    """Print one credential-safe child event with its outer batch identity."""
    if not batch_context:
        return
    current, total = batch_context
    prefix = f"[批次 {current}/{total}]"
    kind = event.get("kind")
    if kind == "rate_limit_wait":
        print(
            f"{prefix} 请求限流，等待 {event['delay']:g} 秒后重试",
            flush=True,
        )
    elif kind == "retry":
        reason = (
            f"HTTP {event['status_code']}"
            if event.get("status_code") is not None
            else event.get("error_type", "网络错误")
        )
        print(
            f"{prefix} 重试 {event['attempt']}/{event['max_attempts']}"
            f"（{reason}，{event['item_count']} 个文件）",
            flush=True,
        )
    elif kind == "reconcile_start":
        print(
            f"{prefix} 提交结果不明确，正在核对远端状态"
            f"（{event['item_count']} 个文件）",
            flush=True,
        )
    elif kind == "reconcile_result":
        print(
            f"{prefix} 远端核对完成: 确认 {event['confirmed']}，"
            f"仍待提交 {event['remaining']}",
            flush=True,
        )
    elif kind == "recovery_result":
        print(
            f"{prefix} 待对账提交已核对: 确认复用 {event['confirmed']}，"
            f"仍待提交 {event['remaining']}",
            flush=True,
        )
    elif kind == "reduce":
        print(
            f"{prefix} 降低提交批量: {event['from_size']} -> " f"{event['to_size']}",
            flush=True,
        )


def _run_resumable_upload(
    token,
    kwargs,
    result_queue,
    request_timeout: float = _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
    batch_context=None,
    auto_configure_lfs=False,
    configured_lfs_patterns=(),
    observation_queue=None,
):
    """Run HF's resumable uploader in an isolated child process.

    Isolation lets cancellation stop all upload worker threads together.
    Request timeouts do not limit the lifetime of this process.
    """
    if multiprocessing.current_process().name != "MainProcess":
        set_upload_observer(None)
    original_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT
    original_get_upload_mode = hf_large_folder._get_upload_mode
    original_preupload_lfs = hf_large_folder._preupload_lfs
    lfs_attributes_policy = (
        _ResumableLfsAttributesPolicy(configured_lfs_patterns)
        if auto_configure_lfs
        else None
    )
    observation_sender = _UploadObservationSender(observation_queue)
    slow_flow_coordinator = _SlowFlowCoordinator(
        event_callback=lambda event: _print_resumable_slow_flow_event(
            event, batch_context
        ),
        observation_callback=observation_sender.send,
    )
    result_sent = False

    def send_failure(error):
        nonlocal result_sent
        if not result_sent:
            result_queue.put((False, _resumable_failure_envelope(error)))
            result_sent = True

    def fatal_exit(error):
        if multiprocessing.current_process().name == "MainProcess":
            return
        send_failure(error)
        if hasattr(result_queue, "close"):
            result_queue.close()
        if hasattr(result_queue, "join_thread"):
            result_queue.join_thread()
        os._exit(1)

    def get_upload_mode_with_policy(*args, **kwargs):
        result = original_get_upload_mode(*args, **kwargs)
        items = kwargs.get("items")
        if items is None and args:
            items = args[0]
        try:
            _validate_resumable_upload_mode_items(items or [])
            if lfs_attributes_policy is not None:
                lfs_attributes_policy.validate_items(items or [])
        except (ResumableUploadModeError, ResumableLfsAttributesError) as error:
            fatal_exit(error)
            raise
        return result

    try:
        hf_constants.DEFAULT_REQUEST_TIMEOUT = request_timeout
        close_hf_session()
        client = HfApi(endpoint=_atomgit_hf_endpoint(), token=token)
        recovery = _recover_pending_commit(
            folder_path=Path(kwargs["folder_path"]),
            token=token,
            repo_id=kwargs["repo_id"],
            repo_type=kwargs.get("repo_type") or "model",
            revision=kwargs.get("revision") or "main",
            request_timeout=request_timeout,
        )
        if recovery["confirmed"]:
            _print_resumable_commit_event(
                {
                    "kind": "recovery_result",
                    "confirmed": recovery["confirmed"],
                    "remaining": recovery["remaining"],
                },
                batch_context,
            )
        _refresh_unsafe_resumable_upload_modes(Path(kwargs["folder_path"]))
        if lfs_attributes_policy is not None:
            cached_patterns = _resumable_projection_lfs_patterns(
                Path(kwargs["folder_path"])
            )
            if cached_patterns:
                try:
                    lfs_attributes_policy.validate_patterns(cached_patterns)
                except ResumableLfsAttributesError as error:
                    fatal_exit(error)
                    raise

        def existing_repo(repo_id, *, private=None, repo_type=None, exist_ok=False):
            """Satisfy HF 1.1.7 setup after the parent validated the target."""
            return type("_ExistingRepo", (), {"repo_id": repo_id})()

        # HF 1.1.7 otherwise sends create_repo(exist_ok=True) before metadata
        # recovery. AtomGit upload targets are required to pre-exist.
        client.create_repo = existing_repo
        hf_large_folder._get_upload_mode = get_upload_mode_with_policy
        preupload_controller = _ResumableLfsPreuploadController(
            original_preupload_lfs,
            fatal_callback=fatal_exit,
            event_callback=lambda event: _print_resumable_lfs_preupload_event(
                event, batch_context
            ),
            lfs_attributes_policy=lfs_attributes_policy,
        )
        hf_large_folder._preupload_lfs = preupload_controller.preupload_lfs
        create_commit = getattr(client, "create_commit", None)
        if callable(create_commit):
            controller = _ResumableCommitController(
                create_commit,
                token=token,
                mark_committed=lambda operations: (
                    _mark_resumable_operations_committed(
                        Path(kwargs["folder_path"]), operations
                    )
                ),
                verify_committed=lambda expectations, repo_id, revision: (
                    verify_canonical_lfs_pointers(
                        token=token,
                        repo_id=repo_id,
                        revision=revision,
                        expectations=expectations,
                        timeout=request_timeout,
                    )
                ),
                fatal_callback=fatal_exit,
                event_callback=lambda event: _print_resumable_commit_event(
                    event, batch_context
                ),
                lfs_attributes_policy=lfs_attributes_policy,
                folder_path=Path(kwargs["folder_path"]),
                request_timeout=request_timeout,
            )
            client.create_commit = controller.create_commit
        with _scoped_resumable_lfs_recovery(slow_flow_coordinator):
            client.upload_large_folder(**kwargs)
        result_queue.put((True, {"recovered": recovery["confirmed"]}))
        result_sent = True
    except BaseException as exc:
        send_failure(exc)
    finally:
        hf_large_folder._get_upload_mode = original_get_upload_mode
        hf_large_folder._preupload_lfs = original_preupload_lfs
        hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
        close_hf_session()
        _close_upload_observation_queue(observation_queue)


def _print_upload_batch_plan(
    file_count: int, batch_count: int, batch_size: int
) -> None:
    print(
        f"上传批次计划: 共 {file_count} 个文件，{batch_count} 个批次，"
        f"每批最多 {batch_size} 个文件",
        flush=True,
    )


def _print_upload_batch_summary(
    planned: int, submitted: int, skipped: int, completed: int
) -> None:
    print(
        f"上传批次汇总: 计划 {planned}，新增提交 {submitted}，"
        f"续传跳过 {skipped}，确认完成 {completed}",
        flush=True,
    )


def _execute_resumable_upload_process(
    *,
    token: str,
    upload_kwargs: dict,
    request_timeout: float,
    batch_context,
    auto_configure_lfs: bool = False,
    configured_lfs_patterns=(),
) -> dict:
    """Run one outer resumable batch and require an explicit child result."""
    methods = multiprocessing.get_all_start_methods()
    context = multiprocessing.get_context("fork" if "fork" in methods else "spawn")
    result_queue = context.Queue()
    try:
        observation_queue = context.Queue(maxsize=_UPLOAD_OBSERVATION_QUEUE_SIZE)
    except Exception:
        observation_queue = None
    source_id = object()
    process = context.Process(
        target=_run_resumable_upload,
        args=(
            token,
            upload_kwargs,
            result_queue,
            request_timeout,
            batch_context,
            auto_configure_lfs,
            configured_lfs_patterns,
            observation_queue,
        ),
    )
    process.daemon = True
    terminal = "failed"
    try:
        process.start()
        while process.is_alive():
            process.join(0.1)
            _drain_upload_observations(observation_queue, source_id)
        process.join()
        _drain_upload_observations(observation_queue, source_id)
        try:
            ok, error = result_queue.get(timeout=1)
        except Exception as exc:
            raise RuntimeError(
                "resumable upload worker exited without a result"
            ) from exc
        if ok is False:
            category = error.get("category") if isinstance(error, dict) else None
            patterns = error.get("lfs_patterns", ()) if isinstance(error, dict) else ()
            commit_revision = (
                error.get("commit_revision") if isinstance(error, dict) else None
            )
            confirmation_failure = (
                error.get("confirmation_failure") if isinstance(error, dict) else None
            )
            confirmed = error.get("confirmed") if isinstance(error, dict) else None
            remaining = error.get("remaining") if isinstance(error, dict) else None
            raise ResumableWorkerError(
                category or "unknown",
                patterns,
                commit_revision=commit_revision,
                confirmation_failure=confirmation_failure,
                confirmed=confirmed,
                remaining=remaining,
            )
        if (
            ok is not True
            or not isinstance(error, dict)
            or set(error) != {"recovered"}
            or not isinstance(error["recovered"], int)
            or isinstance(error["recovered"], bool)
            or not 0 <= error["recovered"] <= _PENDING_COMMIT_MAX_OPERATIONS
            or getattr(process, "exitcode", 0) != 0
        ):
            raise RuntimeError("resumable upload worker returned an invalid result")
        terminal = "completed"
        return error
    except KeyboardInterrupt:
        terminal = "interrupted"
        raise
    finally:
        if process.is_alive():
            process.terminate()
            process.join(2)
            if process.is_alive():
                process.kill()
                process.join()
        _drain_upload_observations(observation_queue, source_id)
        _dispatch_upload_observation(source_id, terminal=terminal)
        if hasattr(result_queue, "close"):
            result_queue.close()
            result_queue.join_thread()
        _close_upload_observation_queue(observation_queue)


def _validate_resumable_upload_target(
    *,
    token: str,
    repo_id: str,
    revision: str = None,
    request_timeout: float = _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
) -> None:
    """Perform one read-only repository/revision check before local hashing."""
    repo_path = _atomgit_v5_repo_path(repo_id)
    repository = _atomgit_v5_get_json(repo_path, token, timeout=request_timeout)
    if not isinstance(repository, dict):
        raise ValueError("repository response is malformed")
    if revision in (None, "main"):
        return

    branch_path = repo_path + "/branches/" + quote(revision, safe="")
    try:
        branch = _atomgit_v5_get_json(branch_path, token, timeout=request_timeout)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise ResumableTargetRevisionError(
                "target revision does not exist"
            ) from error
        raise
    if not isinstance(branch, dict) or branch.get("name") != revision:
        raise ResumableTargetRevisionError("target revision could not be verified")


def _prefix_resumable_ignore_patterns(path_in_repo: str, ignore_patterns):
    """Apply source-relative ignore patterns to a projected remote prefix."""
    if not path_in_repo or not ignore_patterns:
        return ignore_patterns
    return [f"{path_in_repo}/{pattern.lstrip('/')}" for pattern in ignore_patterns]
