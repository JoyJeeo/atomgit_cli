"""Isolated resumable upload orchestration and commit reconciliation."""

import hashlib
import multiprocessing
import os
import random
import socket
import time
import urllib.error
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
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
from ..lfs.pointer import canonical_lfs_payloads, verify_canonical_lfs_pointers
from .contracts import _RESUMABLE_DEFAULT_REQUEST_TIMEOUT
from .errors import (
    ResumableCommitError,
    ResumableTargetRevisionError,
    ResumableWorkerError,
    _resumable_failure_envelope,
)

# Program-step 9 LFS policy slots are wired by atomgit.api.
_atomgit_v5_get_json = None
_atomgit_v5_repo_path = None
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


def _commit_error_status(error: BaseException) -> Optional[int]:
    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)
    return status_code if isinstance(status_code, int) else None


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
            attempts += 1
            call_kwargs = dict(kwargs)
            call_kwargs["operations"] = operations
            expectations = []
            try:
                with self._canonical_payloads() as expectations:
                    result = self._create_commit(*args, **call_kwargs)
                if expectations:
                    commit_revision = getattr(result, "oid", None)
                    if not isinstance(commit_revision, str) or not commit_revision:
                        raise RuntimeError("resumable commit revision is unavailable")
                    self._verify_committed(
                        expectations,
                        call_kwargs.get("repo_id"),
                        commit_revision,
                    )
                self._mark_committed(operations)
                return result
            except Exception as error:
                last_error = error
                if _is_ambiguous_commit_error(error):
                    self._emit(
                        "reconcile_start",
                        item_count=len(operations),
                        attempt=attempts,
                    )
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
                            if matched_expectations:
                                self._verify_committed(
                                    matched_expectations,
                                    call_kwargs.get("repo_id"),
                                    call_kwargs.get("revision") or "main",
                                )
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
                if _commit_error_status(error) == 413:
                    break
                if not _is_retryable_commit_error(error):
                    self._raise_fatal(error, len(operations))
                if attempts < self._max_attempts:
                    delay = self._retry_delay(error, attempts)
                    status_code = _commit_error_status(error)
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
):
    """Run HF's resumable uploader in an isolated child process.

    Isolation lets cancellation stop all upload worker threads together.
    Request timeouts do not limit the lifetime of this process.
    """
    original_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT
    original_get_upload_mode = hf_large_folder._get_upload_mode
    original_preupload_lfs = hf_large_folder._preupload_lfs
    lfs_attributes_policy = (
        _ResumableLfsAttributesPolicy(configured_lfs_patterns)
        if auto_configure_lfs
        else None
    )
    slow_flow_coordinator = _SlowFlowCoordinator(
        event_callback=lambda event: _print_resumable_slow_flow_event(
            event, batch_context
        ),
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
                        timeout=min(request_timeout, 15),
                    )
                ),
                fatal_callback=fatal_exit,
                event_callback=lambda event: _print_resumable_commit_event(
                    event, batch_context
                ),
                lfs_attributes_policy=lfs_attributes_policy,
            )
            client.create_commit = controller.create_commit
        with _scoped_resumable_lfs_recovery(slow_flow_coordinator):
            client.upload_large_folder(**kwargs)
        result_queue.put((True, None))
        result_sent = True
    except BaseException as exc:
        send_failure(exc)
    finally:
        hf_large_folder._get_upload_mode = original_get_upload_mode
        hf_large_folder._preupload_lfs = original_preupload_lfs
        hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
        close_hf_session()


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
) -> None:
    """Run one outer resumable batch and require an explicit child result."""
    methods = multiprocessing.get_all_start_methods()
    context = multiprocessing.get_context("fork" if "fork" in methods else "spawn")
    result_queue = context.Queue()
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
        ),
    )
    process.daemon = True
    try:
        process.start()
        process.join()
        try:
            ok, error = result_queue.get(timeout=1)
        except Exception as exc:
            raise RuntimeError(
                "resumable upload worker exited without a result"
            ) from exc
        if ok is False:
            category = error.get("category") if isinstance(error, dict) else None
            patterns = error.get("lfs_patterns", ()) if isinstance(error, dict) else ()
            raise ResumableWorkerError(category or "unknown", patterns)
        if ok is not True or error is not None or getattr(process, "exitcode", 0) != 0:
            raise RuntimeError("resumable upload worker returned an invalid result")
    finally:
        if process.is_alive():
            process.terminate()
            process.join(2)
            if process.is_alive():
                process.kill()
                process.join()
        if hasattr(result_queue, "close"):
            result_queue.close()
            result_queue.join_thread()


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
