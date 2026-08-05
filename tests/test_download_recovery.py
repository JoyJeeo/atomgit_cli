#!/usr/bin/env python3
"""Verify bounded download retry and signed-URL redaction."""

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


def main():
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
