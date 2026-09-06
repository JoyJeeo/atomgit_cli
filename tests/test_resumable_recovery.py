#!/usr/bin/env python3
"""Regression tests for request timeouts and cancellable resumable uploads."""

import importlib
import io
import multiprocessing
import os
import sys
import tempfile
import time
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx

results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def offline_child(result_queue, outcome, ready):
    if outcome == "cancel":
        ready.set()
        time.sleep(30)
    elif outcome == "crash":
        os._exit(3)
    elif outcome == "empty":
        return
    elif outcome == "failure":
        result_queue.put((False, {"category": "timeout"}))
    elif outcome == "success-crash":
        result_queue.put((True, None))
        result_queue.close()
        result_queue.join_thread()
        os._exit(3)
    elif outcome == "invalid":
        result_queue.put(("yes", None))
    else:
        result_queue.put((True, None))


def process_lifecycle_checks():
    resumable = importlib.import_module("atomgit.adapters.upload.resumable")
    for method in multiprocessing.get_all_start_methods():
        context = multiprocessing.get_context(method)
        for outcome in (
            "success",
            "failure",
            "empty",
            "crash",
            "success-crash",
            "invalid",
            "cancel",
        ):
            ready = context.Event()
            children = []

            def process_factory(target, args):
                child = context.Process(
                    target=offline_child, args=(args[2], outcome, ready)
                )
                children.append(child)
                if outcome == "cancel":
                    real_join = child.join
                    interrupted = False

                    def interrupt_join(timeout=None):
                        nonlocal interrupted
                        if not interrupted:
                            interrupted = True
                            assert ready.wait(5), "upload child did not start"
                            raise KeyboardInterrupt
                        return real_join(timeout)

                    class InterruptibleProcess:
                        def __getattr__(self, name):
                            return getattr(child, name)

                        def join(self, timeout=None):
                            return interrupt_join(timeout)

                    child.daemon = True
                    return InterruptibleProcess()
                return child

            adapter = SimpleNamespace(
                get_all_start_methods=lambda: [method],
                get_context=lambda selected: SimpleNamespace(
                    Process=process_factory, Queue=context.Queue
                ),
            )
            error = None
            try:
                with patch.object(resumable, "multiprocessing", adapter):
                    resumable._execute_resumable_upload_process(
                        token="fake-token-never-print",
                        upload_kwargs={},
                        request_timeout=0.01,
                        batch_context=(1, 1),
                    )
            except BaseException as exc:
                error = exc
            try:
                expected = (
                    error is None
                    if outcome == "success"
                    else (
                        isinstance(error, KeyboardInterrupt)
                        if outcome == "cancel"
                        else (
                            isinstance(error, resumable.ResumableWorkerError)
                            and error.category == "timeout"
                            if outcome == "failure"
                            else isinstance(error, RuntimeError)
                        )
                    )
                )
                check(f"{method} {outcome} result classified", expected)
                check(
                    f"{method} {outcome} child reaped",
                    len(children) == 1
                    and not children[0].is_alive()
                    and children[0].exitcode is not None,
                )
            finally:
                for child in children:
                    if child.is_alive():
                        child.kill()
                        child.join()
                    child.close()


def main():
    original_home = os.environ.get("HOME")
    try:
        with tempfile.TemporaryDirectory() as td:
            os.environ["HOME"] = td
            import sys

            import atomgit  # noqa: F401

            api_module = sys.modules["atomgit.api"]
            config = sys.modules["atomgit.config"].config

            source = Path(td) / "source"
            source.mkdir()
            (source / "payload.bin").write_bytes(b"resumable-test")
            config.get_credentials = lambda: {"token": "fake-token-never-print"}

            original_hf_api = api_module.HfApi
            original_progress = api_module._set_progress_bar
            original_v5_get = api_module._atomgit_v5_get_json
            calls = []

            api_module._atomgit_v5_get_json = lambda *args, **kwargs: {
                "full_name": "user/repo",
                "default_branch": "main",
            }

            class SlowHfApi:
                def __init__(self, endpoint=None, token=None):
                    calls.append(("init", endpoint, token))

                def upload_large_folder(self, **kwargs):
                    calls.append(("upload", kwargs))
                    time.sleep(0.25)

            class FastHfApi:
                def __init__(self, endpoint=None, token=None):
                    calls.append(("init-fast", endpoint, token))

                def upload_large_folder(self, **kwargs):
                    calls.append(("upload-fast", kwargs))

            api_module.HfApi = SlowHfApi
            api_module._set_progress_bar = lambda enabled: None
            try:
                started = time.monotonic()
                result = api_module.api.upload_directory(
                    source,
                    "user/repo",
                    upload_timeout=0.05,
                    progress_bar=False,
                    resumable=True,
                    num_workers=1,
                )
                elapsed = time.monotonic() - started
                check("T1 request timeout does not cap upload lifetime", result is True)
                check(
                    "T2 healthy worker finishes beyond request timeout",
                    elapsed >= 0.25,
                    f"elapsed={elapsed:.3f}s",
                )
                check(
                    "T3 no upload child is left alive",
                    not api_module.multiprocessing.active_children(),
                )
            finally:
                api_module.HfApi = original_hf_api
                api_module._atomgit_v5_get_json = original_v5_get
                api_module._set_progress_bar = original_progress

            from huggingface_hub import constants as hf_constants
            from huggingface_hub.utils import _http

            before = hf_constants.DEFAULT_REQUEST_TIMEOUT
            for timeout_error in (httpx.ReadTimeout, httpx.WriteTimeout):

                class FailedHfApi:
                    def __init__(self, endpoint=None, token=None):
                        pass

                    def upload_large_folder(self, **kwargs):
                        with _http.default_client_factory() as client:
                            assert client.timeout.read == 0.05
                            assert client.timeout.connect == 0.05
                            assert client.timeout.pool == 0.05
                            assert client.timeout.write == 60.0
                        raise timeout_error("offline request timeout")

                output = io.StringIO()
                with (
                    redirect_stdout(output),
                    patch.object(api_module, "HfApi", FailedHfApi),
                    patch.object(
                        api_module, "_atomgit_v5_get_json", lambda *a, **kw: {}
                    ),
                ):
                    failed = api_module.api.upload_directory(
                        source,
                        "user/repo",
                        upload_timeout=0.05,
                        resumable=True,
                        progress_bar=False,
                    )
                check(
                    f"{timeout_error.__name__} fails through upload service",
                    failed is False and "上传目录失败[请求超时]" in output.getvalue(),
                )
                check(
                    "request timeout restored after failure",
                    hf_constants.DEFAULT_REQUEST_TIMEOUT == before,
                )

            process_lifecycle_checks()

            calls.clear()
            api_module.HfApi = FastHfApi
            api_module._atomgit_v5_get_json = lambda *args, **kwargs: {
                "full_name": "user/repo",
                "default_branch": "main",
            }
            try:
                result = api_module.api.upload_directory(
                    source,
                    "user/repo",
                    upload_timeout=1,
                    progress_bar=False,
                    resumable=True,
                    num_workers=1,
                )
                check("T4 successful child returns success", result is True)
                check("T5 successful worker completes within timeout", result is True)
            finally:
                api_module.HfApi = original_hf_api
                api_module._atomgit_v5_get_json = original_v5_get

    finally:
        if original_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = original_home

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
