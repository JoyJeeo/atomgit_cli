#!/usr/bin/env python3
"""Verify bounded download retry and signed-URL redaction."""

import contextlib
import io
import sys
import tempfile
import traceback
from pathlib import Path

import atomgit
import atomgit_hub


api_mod = sys.modules["atomgit.api"]
cfg_mod = sys.modules["atomgit.config"]
results = []


class RemoteProtocolError(Exception):
    pass


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" +
          (f" -> {detail}" if detail else ""))


def interrupted_then_success(counter, result):
    def operation(**kwargs):
        counter.append(dict(kwargs))
        if len(counter) == 1:
            raise RemoteProtocolError(
                "peer closed connection without sending complete message body "
                "https://lfs.example/file?certificate=signed-secret"
            )
        return result
    return operation


def diagnostic_and_rate_limit_checks():
    import urllib.error
    from unittest.mock import patch

    from huggingface_hub import HfApi

    from atomgit.adapters.download import integrity, service, transport
    from atomgit.infrastructure import validation
    from atomgit.interfaces.sdk import AtomGitClient

    class Config:
        def get_credentials(self):
            return None

    def failure(status=429, retry_after="2"):
        return urllib.error.HTTPError(
            "https://fixture.invalid/?token=FAKE_SECRET",
            status,
            "remote FAKE_SECRET",
            {"Retry-After": retry_after},
            None,
        )

    for delay, expected_calls, expected_wait in (
        ("2", 2, [2]),
        ("invalid", 2, [1]),
        ("31", 1, []),
        ("-1", 2, [1]),
    ):
        calls = []

        def limited():
            calls.append(True)
            if len(calls) == 1:
                raise failure(retry_after=delay)
            return "ok"

        with patch("time.sleep") as sleep:
            try:
                validation.run_download_with_retry(limited)
            except urllib.error.HTTPError:
                pass
        check(
            "429 wait is bounded and respects Retry-After",
            len(calls) == expected_calls
            and [call.args[0] for call in sleep.call_args_list] == expected_wait,
        )

    for status in (401, 403, 404, 429):
        with (
            patch("time.sleep"),
            patch.object(
                HfApi, "list_repo_files", side_effect=failure(status, "0")
            ) as listing,
        ):
            with tempfile.TemporaryDirectory() as directory:
                result = AtomGitClient(config=Config()).download_file(
                    "fake/repo", "file.bin", repo_type="model", local_dir=directory
                )
        diagnostic = result.metadata.get("download_diagnostic", {})
        check(
            "native listing failure has safe structured diagnostics",
            not result.ok
            and diagnostic
            == {
                "stage": "listing",
                "error_type": "HTTPError",
                "status_code": status,
            }
            and "FAKE_SECRET" not in str(result),
        )
        check(
            "only throttled listing gets one additional attempt",
            listing.call_count == (2 if status == 429 else 1),
        )

    from email.utils import formatdate

    import httpx
    from huggingface_hub.errors import BadRequestError

    for header, expected in ((formatdate(105, usegmt=True), 5), ("", 1)):
        with patch("time.time", return_value=100), patch("time.sleep") as sleep:
            operation = iter([failure(retry_after=header), "ok"])

            def invoke():
                value = next(operation)
                if isinstance(value, Exception):
                    raise value
                return value

            check(
                "HTTP-date and missing Retry-After are bounded",
                validation.run_download_with_retry(invoke) == "ok"
                and sleep.call_args.args == (expected,),
            )
    with patch.object(
        HfApi,
        "list_repo_files",
        side_effect=BadRequestError(
            "https://fixture.invalid/?token=FAKE_SECRET",
            response=httpx.Response(
                400, request=httpx.Request("GET", "https://fixture.invalid")
            ),
        ),
    ):
        with tempfile.TemporaryDirectory() as directory:
            result = AtomGitClient(config=Config()).download_file(
                "fake/repo", "file.bin", repo_type="model", local_dir=directory
            )
            check(
                "remote ValueError cannot escape safe download boundary",
                not result.ok
                and result.metadata["download_diagnostic"]["error_type"]
                == "BadRequestError"
                and "FAKE_SECRET" not in str(result),
            )
    with patch.object(HfApi, "list_repo_files", side_effect=failure(403)):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            ok = api_mod.api.download_file("fake/repo", "file.bin", repo_type="model")
        check(
            "CLI-facing errors include safe stage and HTTP status",
            not ok
            and "stage=listing" in output.getvalue()
            and "status_code=403" in output.getvalue()
            and "FAKE_SECRET" not in output.getvalue(),
        )

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        cases = (
            (
                "metadata",
                lambda: integrity._atomgit_file_checksum(
                    "fake/repo", "model", "file.bin", None
                ),
                patch.object(
                    integrity, "get_hf_file_metadata", side_effect=failure(403)
                ),
            ),
            (
                "content",
                lambda: transport._download_atomgit_file(
                    "fake/repo", "model", "file.bin", root / "file.bin", None
                ),
                patch.object(transport, "_atomgit_open_url", side_effect=failure(403)),
            ),
            (
                "checksum",
                lambda: integrity._verify_download_checksum(
                    root / "absent", ("sha256", "0" * 64, 1)
                ),
                contextlib.nullcontext(),
            ),
        )
        for stage, operation, injected in cases:
            with injected:
                try:
                    operation()
                except Exception as error:
                    message = validation.sanitized_download_error(error)
                    check(
                        "download stage is preserved without remote secrets",
                        getattr(error, "_atomgit_download_stage", None) == stage
                        and stage in message
                        and "FAKE_SECRET" not in message,
                    )
                else:
                    check("injected stage fails", False)

    with patch.object(
        HfApi, "list_repo_files", side_effect=[failure(), ["file.bin"]]
    ) as listing:
        with patch("time.sleep"):
            check(
                "listing recovers from one throttle",
                service._atomgit_list_repo_files("fake/repo", None, "model")
                == ("model", ["file.bin"])
                and listing.call_count == 2,
            )


def main():
    diagnostic_and_rate_limit_checks()
    cfg_mod.config.get_credentials = lambda: {"token": "fake-token-never-print"}
    original_cli_snapshot = api_mod.snapshot_download
    original_cli_file = api_mod.hf_hub_download
    original_sdk_snapshot = atomgit_hub.hf_snapshot_download
    original_sdk_file = atomgit_hub.hf_hub_download
    original_sdk_loader = atomgit_hub.ds_load_dataset
    try:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            class FakeHttpResponse:
                def __init__(self, data):
                    self._data = data

                def read(self, size=-1):
                    if size is None or size < 0:
                        data, self._data = self._data, b""
                        return data
                    chunk, self._data = self._data[:size], self._data[size:]
                    return chunk

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

            original_api_list = api_mod._atomgit_list_repo_files
            original_urlopen = api_mod._atomgit_open_url
            api_mod._atomgit_list_repo_files = lambda repo_id, token, repo_type=None: ("model", ["config.json"])
            urlopen_calls = []

            def interrupted_urlopen(req, timeout=None):
                urlopen_calls.append(str(req.full_url))
                if len(urlopen_calls) == 1:
                    raise RemoteProtocolError(
                        "peer closed connection without sending complete message body "
                        "https://lfs.example/file?certificate=signed-secret"
                    )
                return FakeHttpResponse(b"content")

            api_mod._atomgit_open_url = interrupted_urlopen
            try:
                check("T1 CLI repo retries interrupted response",
                      api_mod.api.download_repo("user/repo", root / "repo"))
                check("T2 CLI repo retries exactly once", len(urlopen_calls) == 2,
                      str(len(urlopen_calls)))
            finally:
                api_mod._atomgit_list_repo_files = original_api_list
                api_mod._atomgit_open_url = original_urlopen

            sdk_snapshot_calls = []
            atomgit_hub.hf_snapshot_download = interrupted_then_success(
                sdk_snapshot_calls, str(root / "sdk-repo")
            )
            result = atomgit_hub.snapshot_download("user/repo")
            check("T3 SDK snapshot retry succeeds", result.endswith("sdk-repo"))
            check("T4 SDK snapshot retries exactly once",
                  len(sdk_snapshot_calls) == 2)

            sdk_file_calls = []
            atomgit_hub.hf_hub_download = interrupted_then_success(
                sdk_file_calls, str(root / "file.bin")
            )
            result = atomgit_hub.download_file("user/repo", "file.bin")
            check("T5 SDK file retry succeeds", result.endswith("file.bin"))
            check("T6 SDK file retries exactly once", len(sdk_file_calls) == 2)

            always_fail_calls = []
            def always_fail(**kwargs):
                always_fail_calls.append(dict(kwargs))
                raise RemoteProtocolError(
                    "peer closed connection https://lfs.example/file?certificate=signed-secret"
                )
            atomgit_hub.hf_hub_download = always_fail
            try:
                atomgit_hub.download_file("user/repo", "file.bin")
                exposed_error = ""
            except Exception as error:
                exposed_error = str(error)
                exposed_traceback = "".join(traceback.format_exception(error))
            check("T7 exhausted retry is bounded", len(always_fail_calls) == 2)
            check("T8 signed URL is redacted",
                  "signed-secret" not in exposed_error
                  and "https://" not in exposed_error
                  and "signed-secret" not in exposed_traceback
                  and "https://" not in exposed_traceback,
                  exposed_error)

            auth_calls = []
            def auth_failure(**kwargs):
                auth_calls.append(dict(kwargs))
                raise RuntimeError("403 Forbidden https://signed.example?token=secret")
            atomgit_hub.hf_hub_download = auth_failure
            try:
                atomgit_hub.download_file("user/repo", "file.bin")
            except Exception as error:
                auth_error = str(error)
            check("T9 deterministic auth failure is not retried", len(auth_calls) == 1)
            check("T10 auth error is redacted",
                  "secret" not in auth_error and "https://" not in auth_error,
                  auth_error)

            dataset_snapshot_calls = []
            atomgit_hub.hf_snapshot_download = interrupted_then_success(
                dataset_snapshot_calls, str(root / "dataset-snapshot")
            )
            atomgit_hub.ds_load_dataset = lambda **kwargs: {"loaded": True}
            result = atomgit_hub.load_dataset(
                "user/dataset", data_files="data.csv",
                token="fake-token-never-print",
            )
            check("T11 dataset snapshot retries interrupted response",
                  result == {"loaded": True})
            check("T12 dataset snapshot retries exactly once",
                  len(dataset_snapshot_calls) == 2)
    finally:
        api_mod.snapshot_download = original_cli_snapshot
        api_mod.hf_hub_download = original_cli_file
        atomgit_hub.hf_snapshot_download = original_sdk_snapshot
        atomgit_hub.hf_hub_download = original_sdk_file
        atomgit_hub.ds_load_dataset = original_sdk_loader

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
