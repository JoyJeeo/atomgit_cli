#!/usr/bin/env python3
"""Offline regressions for bounded resumable LFS preupload failures."""

import json
import errno
import queue
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import httpx
import atomgit  # noqa: F401
from huggingface_hub.errors import HfHubHTTPError


api_mod = sys.modules["atomgit.api"]


def http_error(status, payload=None, retry_after=None):
    headers = {}
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    request = httpx.Request(
        "POST",
        "https://hub.atomgit.com/user/repo.git/info/lfs/objects/batch",
        headers={"Authorization": "Bearer fake-token-never-print"},
    )
    content = json.dumps(payload).encode() if payload is not None else b""
    response = httpx.Response(
        status,
        headers=headers,
        content=content,
        request=request,
    )
    return HfHubHTTPError(
        "remote failure https://signed.invalid/path?token=secret",
        response=response,
    )


class ScriptedPreupload:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0) if self.outcomes else None
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class FatalPreuploadApi:
    def __init__(self, endpoint=None, token=None):
        self.endpoint = endpoint
        self.token = token

    def create_commit(self, *args, **kwargs):
        return None

    def upload_large_folder(self, **kwargs):
        api_mod.hf_large_folder._preupload_lfs(
            [], api=self, repo_id=kwargs["repo_id"],
            repo_type=kwargs["repo_type"], revision="main",
        )

    def preupload_lfs_files(self, **kwargs):
        raise http_error(413, {
            "error_code_name": "UN_KNOW",
            "error_message": "Insufficient LFS space: quota exceeded",
        })


def make_controller(outcomes, *, deadline=None, monotonic=None):
    call = ScriptedPreupload(outcomes)
    sleeps = []
    events = []
    fatal = []
    controller = api_mod._ResumableLfsPreuploadController(
        call,
        sleep=sleeps.append,
        jitter=lambda delay: 0,
        monotonic=monotonic or (lambda: 0.0),
        deadline=deadline,
        fatal_callback=fatal.append,
        event_callback=events.append,
    )
    return controller, call, sleeps, events, fatal


def main():
    results = []

    def check(name, condition, detail=""):
        results.append(bool(condition))
        label = "PASS" if condition else "FAIL"
        print(f"[{label}] {name}" + (f" -> {detail}" if detail else ""))

    quota_payload = {
        "error_code_name": "UN_KNOW",
        "error_message": "Insufficient LFS space: current usage exceeds quota",
        "trace_id": "trace-secret",
    }
    terminal_cases = [
        ("structured 413 quota", http_error(413, quota_payload), "lfs_quota"),
        ("generic 413", http_error(413, {"message": "too large"}), "lfs_batch_rejected"),
        ("protocol 507", http_error(507), "lfs_quota"),
        ("protocol 509", http_error(509), "lfs_bandwidth"),
        ("authentication", http_error(401), "authentication"),
        ("permission", http_error(403), "permission"),
        ("repository", http_error(404), "repository"),
        ("unprocessable batch", http_error(422), "lfs_batch_rejected"),
        ("unknown 4xx", http_error(418), "lfs_batch_rejected"),
        ("malformed batch", ValueError("Malformed response from server"), "lfs_batch_rejected"),
    ]
    for name, error, category in terminal_cases:
        controller, call, sleeps, _, fatal = make_controller([error])
        try:
            controller.preupload_lfs(items=[], api=None, repo_id="u/r", repo_type="model", revision="main")
        except api_mod.ResumableLfsPreuploadError as caught:
            actual = api_mod._resumable_worker_error_category(caught)
        else:
            actual = "no-error"
        check(f"{name} terminates once", call.calls == 1 and not sleeps)
        check(f"{name} category", actual == category, actual)
        check(f"{name} invokes child fatal path", len(fatal) == 1)

    local_resource = OSError(errno.ENOSPC, "disk full", "/private/source.bin")
    controller, call, sleeps, _, fatal = make_controller([local_resource])
    try:
        controller.preupload_lfs([], None, "u/r", "model", "main")
    except api_mod.ResumableLfsPreuploadError as error:
        resource_category = error.category
    else:
        resource_category = "no-error"
    check("local resource failure terminates once", call.calls == 1 and not sleeps)
    check("local resource failure keeps safe category", resource_category == "client_resource")
    check("local resource failure invokes child fatal path", len(fatal) == 1)

    stable_quota = http_error(413, {"error_code_name": "INSUFFICIENT_LFS_SPACE"})
    controller, call, _, _, _ = make_controller([stable_quota])
    try:
        controller.preupload_lfs([], None, "u/r", "model", "main")
    except api_mod.ResumableLfsPreuploadError as error:
        stable_category = error.category
    else:
        stable_category = "no-error"
    check("stable quota code is accepted", stable_category == "lfs_quota")

    misleading = http_error(413, {"error_message": "Insufficient LFS spaceship"})
    controller, _, _, _, _ = make_controller([misleading])
    try:
        controller.preupload_lfs([], None, "u/r", "model", "main")
    except api_mod.ResumableLfsPreuploadError as error:
        misleading_category = error.category
    else:
        misleading_category = "no-error"
    check("quota compatibility marker is narrowly anchored", misleading_category == "lfs_batch_rejected")

    retry_cases = [
        (429, "rate_limit"),
        (500, "service_unavailable"),
        (502, "service_unavailable"),
        (503, "service_unavailable"),
        (504, "service_unavailable"),
    ]
    for status, category in retry_cases:
        errors = [http_error(status), http_error(status), "ok"]
        controller, call, sleeps, events, fatal = make_controller(errors)
        result = controller.preupload_lfs([], None, "u/r", "model", "main")
        check(f"HTTP {status} succeeds within bound", result == "ok" and call.calls == 3)
        check(f"HTTP {status} deterministic backoff", sleeps == [2.0, 4.0], repr(sleeps))
        check(f"HTTP {status} emits sanitized retries", [event["category"] for event in events] == [category, category])
        check(f"HTTP {status} does not invoke fatal on recovery", not fatal)

    for error in (httpx.ReadTimeout("secret path"), httpx.ConnectError("secret host")):
        controller, call, sleeps, _, _ = make_controller([error, error, "ok"])
        check(
            f"{type(error).__name__} retries exactly",
            controller.preupload_lfs([], None, "u/r", "model", "main") == "ok"
            and call.calls == 3
            and sleeps == [2.0, 4.0],
        )

    exhausted = [http_error(503), http_error(503), http_error(503), "must-not-run"]
    controller, call, sleeps, exhausted_events, fatal = make_controller(exhausted)
    try:
        controller.preupload_lfs([], None, "u/r", "model", "main")
    except api_mod.ResumableLfsPreuploadError as error:
        exhausted_category = error.category
    else:
        exhausted_category = "no-error"
    check("transient retries never exceed three attempts", call.calls == 3)
    check("retry exhaustion keeps semantic category", exhausted_category == "service_unavailable")
    check("retry exhaustion sleeps only between attempts", sleeps == [2.0, 4.0])
    check("retry exhaustion invokes fatal once", len(fatal) == 1)
    check(
        "retry exhaustion emits bounded attempt count",
        exhausted_events[-1] == {
            "kind": "lfs_preupload_exhausted",
            "category": "service_unavailable",
            "attempts": 3,
        },
        repr(exhausted_events),
    )

    controller, call, sleeps, _, _ = make_controller([
        http_error(429, retry_after=7),
        "ok",
    ])
    controller.preupload_lfs([], None, "u/r", "model", "main")
    check("valid Retry-After is honored", call.calls == 2 and sleeps == [7.0])

    controller, _, sleeps, _, _ = make_controller([
        http_error(429, retry_after=9999),
        "ok",
    ])
    controller.preupload_lfs([], None, "u/r", "model", "main")
    check("Retry-After is capped", sleeps == [api_mod._RESUMABLE_LFS_PREUPLOAD_WAIT_CAP])

    for invalid_retry_after in ("-1", "nan", "not-a-delay"):
        controller, _, sleeps, _, _ = make_controller([
            http_error(429, retry_after=invalid_retry_after),
            "ok",
        ])
        controller.preupload_lfs([], None, "u/r", "model", "main")
        check(
            f"invalid Retry-After {invalid_retry_after!r} uses backoff",
            sleeps == [2.0],
            repr(sleeps),
        )

    clock = iter([9.0, 9.0])
    controller, call, sleeps, _, fatal = make_controller(
        [http_error(503), "must-not-run"],
        deadline=10.0,
        monotonic=lambda: next(clock),
    )
    try:
        controller.preupload_lfs([], None, "u/r", "model", "main")
    except api_mod.ResumableLfsPreuploadError as error:
        deadline_category = error.category
    else:
        deadline_category = "no-error"
    check("deadline prevents overlong retry wait", call.calls == 1 and not sleeps)
    check("deadline failure is timeout", deadline_category == "timeout")
    check("deadline invokes fatal path", len(fatal) == 1)

    envelope = api_mod._resumable_failure_envelope(
        api_mod.ResumableLfsPreuploadError("lfs_quota")
    )
    serialized = repr(envelope)
    check("LFS envelope is category-only", envelope == {"category": "lfs_quota"})
    check(
        "LFS envelope contains no sensitive detail",
        all(secret not in serialized for secret in (
            "fake-token", "signed.invalid", "trace-secret", "oid", "/private/",
        )),
    )

    structured = [
        ("lfs_quota", "LFS 存储空间不足"),
        ("lfs_bandwidth", "LFS 带宽额度不足"),
        ("lfs_batch_rejected", "LFS 协商请求被拒绝"),
    ]
    for category, expected in structured:
        error_type, hint = api_mod._classify_upload_error(
            api_mod.ResumableWorkerError(category), repo_id="u/r"
        )
        check(f"CLI maps {category}", expected in error_type)
        check(f"CLI {category} preserves breakpoint", "断点" in hint)
        check(f"CLI {category} is not commit-size guidance", "提交已降至单文件" not in hint)

    with tempfile.TemporaryDirectory(prefix="atomgit-lfs-preupload-") as td:
        projection = Path(td)
        pending_file = projection / "pending.bin"
        pending_file.write_bytes(b"pending")
        pending_paths = api_mod.get_local_upload_paths(projection, "pending.bin")
        pending = api_mod.read_upload_metadata(projection, "pending.bin")
        pending.sha256 = "12" * 32
        pending.upload_mode = "lfs"
        pending.should_ignore = False
        pending.save(pending_paths)

        committed_file = projection / "committed.bin"
        committed_file.write_bytes(b"committed")
        committed_paths = api_mod.get_local_upload_paths(projection, "committed.bin")
        committed = api_mod.read_upload_metadata(projection, "committed.bin")
        committed.sha256 = "34" * 32
        committed.upload_mode = "lfs"
        committed.is_uploaded = True
        committed.is_committed = True
        committed.save(committed_paths)

        class MetadataApi:
            def __init__(self, outcomes):
                self.outcomes = list(outcomes)
                self.calls = 0

            def preupload_lfs_files(self, **kwargs):
                self.calls += 1
                outcome = self.outcomes.pop(0)
                if isinstance(outcome, BaseException):
                    raise outcome

        item = (pending_paths, pending)
        metadata_api = MetadataApi([http_error(507)])
        metadata_controller = api_mod._ResumableLfsPreuploadController(
            api_mod.hf_large_folder._preupload_lfs,
            jitter=lambda delay: 0,
        )
        try:
            metadata_controller.preupload_lfs(
                [item], api=metadata_api, repo_id="u/r",
                repo_type="model", revision="main",
            )
        except api_mod.ResumableLfsPreuploadError:
            pass
        failed = api_mod.read_upload_metadata(projection, "pending.bin")
        preserved = api_mod.read_upload_metadata(projection, "committed.bin")
        check(
            "failed LFS metadata preserves reusable identity",
            failed.sha256 == "12" * 32
            and failed.upload_mode == "lfs"
            and not failed.is_uploaded
            and not failed.is_committed,
        )
        check(
            "prior committed metadata remains committed",
            preserved.sha256 == "34" * 32
            and preserved.is_uploaded
            and preserved.is_committed,
        )

        metadata_api.outcomes.append(None)
        metadata_controller.preupload_lfs(
            [item], api=metadata_api, repo_id="u/r",
            repo_type="model", revision="main",
        )
        resumed = api_mod.read_upload_metadata(projection, "pending.bin")
        check(
            "later success reuses metadata and marks only upload",
            metadata_api.calls == 2
            and resumed.sha256 == "12" * 32
            and resumed.upload_mode == "lfs"
            and resumed.is_uploaded
            and not resumed.is_committed,
        )

    original_api = api_mod.HfApi
    original_preupload = api_mod.hf_large_folder._preupload_lfs
    original_timeout = api_mod.hf_constants.DEFAULT_REQUEST_TIMEOUT
    original_close = api_mod.close_hf_session
    try:
        api_mod.HfApi = FatalPreuploadApi
        api_mod.close_hf_session = lambda: None
        inline_queue = queue.Queue()
        api_mod._run_resumable_upload(
            "fake-token-never-print",
            {"repo_id": "u/r", "folder_path": ".", "repo_type": "model"},
            inline_queue,
            300.0,
            (1, 1),
            None,
        )
        check(
            "inline terminal failure returns bounded category",
            inline_queue.get_nowait() == (False, {"category": "lfs_quota"}),
        )
        check(
            "inline failure restores dependency preupload global",
            api_mod.hf_large_folder._preupload_lfs is original_preupload,
        )
        methods = api_mod.multiprocessing.get_all_start_methods()
        if "fork" in methods:
            context = api_mod.multiprocessing.get_context("fork")
            result_queue = context.Queue()
            process = context.Process(
                target=api_mod._run_resumable_upload,
                args=(
                    "fake-token-never-print",
                    {"repo_id": "u/r", "folder_path": ".", "repo_type": "model"},
                    result_queue,
                    300.0,
                    (1, 1),
                    None,
                ),
            )
            process.start()
            process.join(5)
            child_result = result_queue.get(timeout=1)
            check("terminal LFS child exits promptly", not process.is_alive())
            check(
                "terminal LFS child returns bounded category",
                child_result == (False, {"category": "lfs_quota"}),
                repr(child_result),
            )
        else:
            check("terminal LFS child test requires fork", True)
    finally:
        api_mod.HfApi = original_api
        api_mod.close_hf_session = original_close
        api_mod.hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
    check(
        "dependency preupload global remains unchanged in parent",
        api_mod.hf_large_folder._preupload_lfs is original_preupload,
    )

    print("\n" + "=" * 50)
    passed = sum(results)
    print(f"汇总: {passed}/{len(results)} 通过")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
