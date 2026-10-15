#!/usr/bin/env python3
"""Ensure CLI-facing operation failures never echo dependency secrets."""

import contextlib
import importlib
import io
import logging
import multiprocessing
import sys
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

import httpx

import atomgit  # noqa: F401

api_mod = sys.modules["atomgit.api"]
results = []
SECRET = "never-print-this-token"
SENSITIVE_ERROR = RuntimeError(
    f"Authorization: Bearer {SECRET} https://signed.example/file?token={SECRET}"
)


def fork_output_probe(result_queue):
    from atomgit.adapters.upload.errors import _scoped_upload_output

    with _scoped_upload_output():
        result_queue.put(True)


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))


def safe_output(name, operation):
    output = io.StringIO()
    logger = logging.getLogger("huggingface_hub.utils._http")
    handler = logging.StreamHandler(output)
    logger.addHandler(handler)
    escaped = None
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = operation()
    except Exception as error:
        result = None
        escaped = error
    finally:
        logger.removeHandler(handler)
    text = output.getvalue()
    check(f"{name} contains exception", escaped is None, repr(escaped))
    check(
        f"{name} redacts credentials",
        SECRET not in text and "https://signed.example" not in text and "Authorization:" not in text,
        repr(text),
    )
    check(f"{name} reports failure", result in (False, None), repr(result))
    return text


def upload_logging_checks():
    errors = importlib.import_module("atomgit.adapters.upload.errors")
    scope = getattr(errors, "_scoped_upload_output", None)
    check("upload output has a scoped dependency-log boundary", scope is not None)
    if scope is None:
        return
    before_factory = logging.getLogRecordFactory()
    before_hook = threading.excepthook
    output = io.StringIO()
    late_logger = logging.getLogger("huggingface_hub.upload_late_logger")
    handler = logging.StreamHandler(output)
    late_logger.addHandler(handler)
    try:
        with contextlib.redirect_stderr(output), scope():
            with scope():
                late_logger.warning(
                    "%s",
                    SENSITIVE_ERROR,
                    exc_info=(RuntimeError, SENSITIVE_ERROR, None),
                )
            late_logger.error("response body: %s", SECRET)

            def crash():
                raise SENSITIVE_ERROR

            thread = threading.Thread(target=crash)
            thread.start()
            thread.join(2)
            from huggingface_hub.utils import _http

            def timeout(request):
                raise httpx.WriteTimeout(str(SENSITIVE_ERROR), request=request)

            retry_logger = logging.getLogger("huggingface_hub.utils._http")
            retry_logger.addHandler(handler)
            try:
                with httpx.Client(transport=httpx.MockTransport(timeout)) as client:
                    with patch.object(_http, "get_session", return_value=client):
                        try:
                            _http.http_backoff(
                                "PUT",
                                "https://signed.example/file?token=" + SECRET,
                                max_retries=1,
                                base_wait_time=0,
                                max_wait_time=0,
                            )
                        except httpx.WriteTimeout:
                            pass
            finally:
                retry_logger.removeHandler(handler)
        text = output.getvalue()
        check(
            "dependency and background failures contain no raw details",
            SECRET not in text
            and "signed.example" not in text
            and "Authorization:" not in text
            and "response body" not in text,
        )
        check("background failure retains a safe error type", "RuntimeError" in text)
        check(
            "nested upload scopes restore logging and thread hooks",
            logging.getLogRecordFactory() is before_factory
            and threading.excepthook is before_hook,
        )
    finally:
        late_logger.removeHandler(handler)

    first_ready, second_ready = threading.Event(), threading.Event()
    first_release, second_release = threading.Event(), threading.Event()

    def hold_scope(ready, release):
        with scope():
            ready.set()
            release.wait(5)

    first = threading.Thread(target=hold_scope, args=(first_ready, first_release))
    second = threading.Thread(target=hold_scope, args=(second_ready, second_release))
    try:
        first.start()
        first_started = first_ready.wait(2)
        second.start()
        second_started = second_ready.wait(2)
        first_release.set()
        first.join(2)
        record = logging.getLogger("httpcore.late_transport").makeRecord(
            "httpcore.late_transport",
            logging.ERROR,
            "test",
            1,
            str(SENSITIVE_ERROR),
            (),
            None,
        )
        check(
            "overlapping uploads stay protected when the first exits",
            first_started and second_started and SECRET not in record.getMessage(),
        )
    finally:
        first_release.set()
        second_release.set()
        first.join(2)
        second.join(2)
    check(
        "overlapping uploads restore process hooks after the last exit",
        logging.getLogRecordFactory() is before_factory
        and threading.excepthook is before_hook,
    )
    if "fork" in multiprocessing.get_all_start_methods():
        ready, release = threading.Event(), threading.Event()

        def hold_lock():
            with errors._UPLOAD_OUTPUT_LOCK:
                ready.set()
                release.wait(10)

        holder = threading.Thread(target=hold_lock)
        context = multiprocessing.get_context("fork")
        result_queue = context.Queue()
        child = context.Process(target=fork_output_probe, args=(result_queue,))
        try:
            holder.start()
            assert ready.wait(2)
            child.start()
            child.join(3)
            check(
                "fork upload does not inherit a locked output guard",
                not child.is_alive() and child.exitcode == 0,
            )
        finally:
            release.set()
            holder.join(2)
            if child.is_alive():
                child.kill()
                child.join(2)
            child.close()
            result_queue.close()
            result_queue.join_thread()


def main():
    original_create = api_mod.create_repo
    original_exists = api_mod._atomgit_repo_exists
    original_upload_file = api_mod.hf_upload_file
    original_upload_folder = api_mod.upload_folder
    original_credentials = api_mod.config.get_credentials
    original_set_credentials = api_mod.config.set_credentials
    original_login_lookup = api_mod.api._get_login_user_by_token
    try:
        api_mod.config.get_credentials = lambda: {"token": "fake-stored-token"}
        api_mod._atomgit_repo_exists = lambda repo_id, token: False

        def fail(*args, **kwargs):
            raise SENSITIVE_ERROR

        def noisy_upload(*args, **kwargs):
            logging.getLogger("huggingface_hub.utils._http").warning(
                "%s", SENSITIVE_ERROR
            )
            raise SENSITIVE_ERROR

        api_mod.create_repo = fail
        create_text = safe_output(
            "create", lambda: api_mod.api.create_repo("user/repo", private=True)
        )
        check("create retains categorized guidance", "未知错误" in create_text and "建议" in create_text)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "file.bin"
            source.write_bytes(b"data")
            api_mod.hf_upload_file = noisy_upload
            file_text = safe_output(
                "file upload", lambda: api_mod.api.upload_folder(source, "user/repo")
            )
            check("file upload retains categorized guidance", "未知错误" in file_text and "建议" in file_text)

            upload_root = root / "folder"
            upload_root.mkdir()
            (upload_root / "data.bin").write_bytes(b"data")
            api_mod.upload_folder = noisy_upload
            directory_text = safe_output(
                "directory upload",
                lambda: api_mod.api.upload_directory(upload_root, "user/repo"),
            )
            check("directory upload retains categorized guidance", "未知错误" in directory_text and "建议" in directory_text)

        api_mod.api._get_login_user_by_token = lambda token: {"login": "tester"}
        api_mod.config.set_credentials = fail
        login_text = safe_output("login", lambda: api_mod.api.login("x" * 20))
        check("login has safe actionable message", "保存" in login_text or "登录" in login_text)

        api_mod.config.get_credentials = fail
        whoami_text = safe_output("whoami", api_mod.api.get_login_user)
        check("whoami has safe actionable message", "凭证" in whoami_text or "用户" in whoami_text)
    finally:
        api_mod.create_repo = original_create
        api_mod._atomgit_repo_exists = original_exists
        api_mod.hf_upload_file = original_upload_file
        api_mod.upload_folder = original_upload_folder
        api_mod.config.get_credentials = original_credentials
        api_mod.config.set_credentials = original_set_credentials
        api_mod.api._get_login_user_by_token = original_login_lookup

    upload_logging_checks()
    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
