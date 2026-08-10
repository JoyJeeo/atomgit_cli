#!/usr/bin/env python3
"""Offline regressions for AtomGit resumable commit retry policy."""

import httpx
import queue
import sys
import tempfile
from pathlib import Path

import atomgit  # noqa: F401
from huggingface_hub import CommitOperationAdd
from huggingface_hub.errors import HfHubHTTPError


api_mod = sys.modules["atomgit.api"]


def http_error(status, retry_after=None):
    headers = {}
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    request = httpx.Request("POST", "https://hub.atomgit.com/api/models/u/r/commit/main")
    response = httpx.Response(status, headers=headers, request=request)
    return HfHubHTTPError(f"HTTP {status}", response=response)


class FakeOperation:
    def __init__(self, path):
        self.path_in_repo = path


class ScriptedClient:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def create_commit(self, *args, **kwargs):
        operations = list(kwargs["operations"])
        self.calls.append([item.path_in_repo for item in operations])
        outcome = self.outcomes.pop(0) if self.outcomes else None
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class FatalHfApi:
    """Exercise bounded child termination without a remote request."""

    def __init__(self, token=None):
        self.token = token

    def create_commit(self, *args, **kwargs):
        raise http_error(429, retry_after=0)

    def upload_large_folder(self, **kwargs):
        return self.create_commit(
            repo_id=kwargs["repo_id"],
            repo_type=kwargs["repo_type"],
            revision="main",
            operations=[FakeOperation("payload.bin")],
            commit_message="batch",
        )


def make_controller(
    client, sleeps, reconcile=None, max_attempts=3, mark_committed=None
):
    return api_mod._ResumableCommitController(
        client.create_commit,
        token="fake-token-never-print",
        sleep=sleeps.append,
        jitter=lambda delay: 0,
        reconcile=reconcile or (lambda **kwargs: set()),
        max_attempts=max_attempts,
        mark_committed=mark_committed or (lambda operations: None),
    )


def main():
    results = []

    def check(name, condition, detail=""):
        results.append(bool(condition))
        print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))

    operations = [FakeOperation(f"file-{index:02d}.bin") for index in range(20)]

    sleeps = []
    timeout_client = ScriptedClient([httpx.ReadTimeout("response timed out")])
    reconciled = {item.path_in_repo for item in operations}
    controller = make_controller(
        timeout_client,
        sleeps,
        reconcile=lambda **kwargs: reconciled,
    )
    result = controller.create_commit(
        repo_id="user/repo",
        repo_type="model",
        revision="main",
        operations=operations,
        commit_message="batch",
    )
    check("ambiguous timeout reconciles remote success", result is None)
    check("reconciled timeout is not submitted twice", len(timeout_client.calls) == 1)

    sleeps = []
    partial_client = ScriptedClient([httpx.ReadTimeout("response timed out"), "partial-ok"])
    partial_paths = {item.path_in_repo for item in operations[:10]}
    controller = make_controller(
        partial_client,
        sleeps,
        reconcile=lambda **kwargs: partial_paths,
    )
    result = controller.create_commit(
        repo_id="user/repo",
        repo_type="model",
        revision="main",
        operations=operations,
        commit_message="batch",
    )
    check("partial reconciliation commits only missing paths", result == "partial-ok")
    check("partial reconciliation reduces retry set", [len(call) for call in partial_client.calls] == [20, 10])

    marked_paths = []
    partial_split = ScriptedClient([
        httpx.ReadTimeout("initial timeout"),
        "first-half-ok",
        httpx.ReadTimeout("second-half timeout"),
        httpx.ReadTimeout("smaller timeout"),
        httpx.ReadTimeout("single timeout"),
        httpx.ReadTimeout("terminal timeout"),
    ])
    controller = make_controller(
        partial_split,
        [],
        max_attempts=1,
        mark_committed=lambda items: marked_paths.extend(
            item.path_in_repo for item in items
        ),
    )
    try:
        controller.create_commit(
            repo_id="user/repo",
            repo_type="model",
            revision="main",
            operations=operations,
            commit_message="batch",
        )
    except api_mod.ResumableCommitError:
        split_failure = True
    else:
        split_failure = False
    check("partial split failure remains a failure", split_failure)
    check(
        "successful split is persisted before a later split fails",
        marked_paths == [item.path_in_repo for item in operations[:10]],
        repr(marked_paths),
    )

    sleeps = []
    limited_client = ScriptedClient([http_error(429, retry_after=7), "ok"])
    controller = make_controller(limited_client, sleeps)
    result = controller.create_commit(
        repo_id="user/repo",
        repo_type="model",
        revision="main",
        operations=operations,
        commit_message="batch",
    )
    check("429 retry eventually returns commit result", result == "ok")
    check("429 honors Retry-After", sleeps == [7.0], repr(sleeps))
    check("429 retries the same batch", [len(call) for call in limited_client.calls] == [20, 20])

    long_retry_sleeps = []
    long_retry_client = ScriptedClient([http_error(429, retry_after=600), "ok"])
    controller = make_controller(long_retry_client, long_retry_sleeps)
    controller.create_commit(
        repo_id="user/repo",
        repo_type="model",
        revision="main",
        operations=operations,
        commit_message="batch",
    )
    check("Retry-After is not shortened", long_retry_sleeps == [600.0], repr(long_retry_sleeps))

    sleeps = []
    unavailable_client = ScriptedClient([http_error(503), "recovered"])
    controller = make_controller(unavailable_client, sleeps)
    result = controller.create_commit(
        repo_id="user/repo",
        repo_type="model",
        revision="main",
        operations=operations,
        commit_message="batch",
    )
    check("503 uses bounded retry and recovers", result == "recovered")
    check("503 uses exponential backoff base", sleeps == [30.0], repr(sleeps))

    oversized_client = ScriptedClient([http_error(413), "first-ok", "second-ok"])
    controller = make_controller(oversized_client, [])
    result = controller.create_commit(
        repo_id="user/repo",
        repo_type="model",
        revision="main",
        operations=operations,
        commit_message="batch",
    )
    check("413 reduces immediately and completes", result == "second-ok")
    check("413 reduces twenty to two tens", [len(call) for call in oversized_client.calls] == [20, 10, 10], repr(oversized_client.calls))

    sleeps = []
    persistent_limit = ScriptedClient([http_error(429), http_error(429)])
    controller = make_controller(persistent_limit, sleeps, max_attempts=2)
    try:
        controller.create_commit(
            repo_id="user/repo",
            repo_type="model",
            revision="main",
            operations=operations,
            commit_message="batch",
        )
    except api_mod.ResumableCommitError:
        limited_failure = True
    else:
        limited_failure = False
    check("persistent 429 fails after bounded attempts", limited_failure)
    check("persistent 429 never reduces batch", [len(call) for call in persistent_limit.calls] == [20, 20])

    sleeps = []
    persistent_timeout = ScriptedClient(
        [httpx.ReadTimeout("response timed out") for _ in range(8)]
    )
    controller = make_controller(persistent_timeout, sleeps, max_attempts=1)
    try:
        controller.create_commit(
            repo_id="user/repo",
            repo_type="model",
            revision="main",
            operations=operations,
            commit_message="batch",
        )
    except api_mod.ResumableCommitError:
        timeout_failure = True
    else:
        timeout_failure = False
    sizes = [len(call) for call in persistent_timeout.calls]
    check("persistent timeout fails safely", timeout_failure)
    check("persistent timeout really reduces below twenty", sizes[:5] == [20, 10, 5, 2, 1], repr(sizes))

    disconnected_client = ScriptedClient([httpx.ConnectError("offline")])
    controller = make_controller(disconnected_client, [], max_attempts=1)
    try:
        controller.create_commit(
            repo_id="user/repo",
            repo_type="model",
            revision="main",
            operations=operations,
            commit_message="batch",
        )
    except api_mod.ResumableCommitError:
        disconnected_failure = True
    else:
        disconnected_failure = False
    check("persistent connection failure exits safely", disconnected_failure)
    check("connection failure does not reduce batch", [len(call) for call in disconnected_client.calls] == [20])

    forbidden_client = ScriptedClient([http_error(403)])
    controller = make_controller(forbidden_client, [])
    try:
        controller.create_commit(
            repo_id="user/repo",
            repo_type="model",
            revision="main",
            operations=operations,
            commit_message="batch",
        )
    except api_mod.ResumableCommitError:
        forbidden_failure = True
    else:
        forbidden_failure = False
    check("non-retryable 403 fails immediately", forbidden_failure)
    check("non-retryable 403 is attempted once", len(forbidden_client.calls) == 1)

    payload_type, payload_hint = api_mod._classify_upload_error(
        api_mod.ResumableCommitError(
            "resumable commit failed for 1 file(s): HTTP 413"
        )
    )
    check("single-file 413 has an actionable category", payload_type == "提交过大", payload_type)
    check("single-file 413 explains the remaining limit", "单文件" in payload_hint, payload_hint)

    rate_type, rate_hint = api_mod._classify_upload_error(
        api_mod.ResumableCommitError(
            "resumable commit failed for 20 file(s): HTTP 429"
        )
    )
    check("exhausted 429 has an actionable category", rate_type == "请求限流", rate_type)
    check("exhausted 429 explains resumable progress", "断点" in rate_hint, rate_hint)

    service_type, service_hint = api_mod._classify_upload_error(
        api_mod.ResumableCommitError(
            "resumable commit failed for 1 file(s): HTTP 503"
        )
    )
    check("exhausted 503 has an actionable category", service_type == "服务暂不可用", service_type)
    check("exhausted 503 suggests retrying later", "稍后" in service_hint, service_hint)

    original_checksum = api_mod._atomgit_file_checksum
    try:
        with tempfile.TemporaryDirectory(prefix="atomgit-reconcile-") as td:
            payload = Path(td) / "payload.bin"
            payload.write_bytes(b"content")
            operation = CommitOperationAdd(
                path_in_repo="prefix/payload.bin",
                path_or_fileobj=payload,
            )
            api_mod._atomgit_file_checksum = lambda *args: (
                "sha256",
                operation.upload_info.sha256.hex(),
                operation.upload_info.size,
            )
            matched = api_mod._reconcile_resumable_commit_operations(
                repo_id="user/repo",
                repo_type="model",
                revision="main",
                operations=[operation],
                token="fake-token-never-print",
            )
            check("remote reconciliation compares LFS object identity", matched == {"prefix/payload.bin"})

            projection = Path(td) / "projection"
            projected_file = projection / "prefix" / "payload.bin"
            projected_file.parent.mkdir(parents=True)
            projected_file.write_bytes(b"content")
            projected_operation = CommitOperationAdd(
                path_in_repo="prefix/payload.bin",
                path_or_fileobj=projected_file,
            )
            paths = api_mod.get_local_upload_paths(
                projection, "prefix/payload.bin"
            )
            metadata = api_mod.read_upload_metadata(
                projection, "prefix/payload.bin"
            )
            metadata.sha256 = projected_operation.upload_info.sha256.hex()
            metadata.upload_mode = "lfs"
            metadata.is_uploaded = True
            metadata.save(paths)
            api_mod._mark_resumable_operations_committed(
                projection, [projected_operation]
            )
            persisted = api_mod.read_upload_metadata(
                projection, "prefix/payload.bin"
            )
            check("successful sub-commit persists locked HF metadata", persisted.is_committed)
    finally:
        api_mod._atomgit_file_checksum = original_checksum

    original_api = api_mod.HfApi
    original_close = api_mod.close_hf_session
    original_timeout = api_mod.hf_constants.DEFAULT_REQUEST_TIMEOUT
    captured = []

    class TimeoutAwareApi:
        def __init__(self, token=None):
            captured.append(api_mod.hf_constants.DEFAULT_REQUEST_TIMEOUT)

        def create_commit(self, *args, **kwargs):
            return None

        def upload_large_folder(self, **kwargs):
            return None

    api_mod.HfApi = TimeoutAwareApi
    api_mod.close_hf_session = lambda: captured.append("closed")
    result_queue = queue.Queue()
    try:
        api_mod._run_resumable_upload(
            "fake-token-never-print",
            {"repo_id": "user/repo", "folder_path": ".", "repo_type": "model"},
            result_queue,
            300.0,
        )
        check("child reports successful upload", result_queue.get_nowait() == (True, None))
        check("child constructs HF client with 300 second timeout", 300.0 in captured, repr(captured))
        check("child closes cached HTTP sessions before and after", captured.count("closed") == 2, repr(captured))
        check("child restores process-global timeout", api_mod.hf_constants.DEFAULT_REQUEST_TIMEOUT == original_timeout)
    finally:
        api_mod.HfApi = original_api
        api_mod.close_hf_session = original_close
        api_mod.hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout

    methods = api_mod.multiprocessing.get_all_start_methods()
    if "fork" in methods:
        original_api = api_mod.HfApi
        api_mod.HfApi = FatalHfApi
        process = None
        try:
            context = api_mod.multiprocessing.get_context("fork")
            result_queue = context.Queue()
            process = context.Process(
                target=api_mod._run_resumable_upload,
                args=(
                    "fake-token-never-print",
                    {
                        "repo_id": "user/repo",
                        "folder_path": ".",
                        "repo_type": "model",
                    },
                    result_queue,
                    300.0,
                ),
            )
            process.start()
            process.join(5)
            child_result = result_queue.get(timeout=1)
            check("persistent child failure terminates promptly", not process.is_alive())
            check("persistent child failure returns resumable error", child_result[0] is False and child_result[1][0] == "ResumableCommitError", repr(child_result))
        finally:
            if process is not None and process.is_alive():
                process.terminate()
                process.join(2)
            api_mod.HfApi = original_api
    else:
        check("persistent child failure test requires fork", True)

    passed = sum(results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
