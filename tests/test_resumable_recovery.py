#!/usr/bin/env python3
"""Regression tests for bounded and cancellable resumable uploads."""

import os
import sys
import tempfile
import time
from pathlib import Path

results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    original_home = os.environ.get("HOME")
    try:
        with tempfile.TemporaryDirectory() as td:
            os.environ["HOME"] = td
            import atomgit  # noqa: F401
            import sys
            api_module = sys.modules["atomgit.api"]
            config = sys.modules["atomgit.config"].config

            source = Path(td) / "source"
            source.mkdir()
            (source / "payload.bin").write_bytes(b"resumable-test")
            config.get_credentials = lambda: {"token": "fake-token-never-print"}

            original_hf_api = api_module.HfApi
            original_progress = api_module._set_progress_bar
            calls = []

            class SlowHfApi:
                def __init__(self, token=None):
                    calls.append(("init", token))

                def list_repo_tree(self, repo_id, path_in_repo=None, *,
                                   recursive=False, expand=False,
                                   revision=None, repo_type=None, token=None):
                    calls.append(("validate", repo_id))
                    return []

                def upload_large_folder(self, **kwargs):
                    calls.append(("upload", kwargs))
                    time.sleep(0.25)

            class FastHfApi:
                def __init__(self, token=None):
                    calls.append(("init-fast", token))

                def list_repo_tree(self, repo_id, path_in_repo=None, *,
                                   recursive=False, expand=False,
                                   revision=None, repo_type=None, token=None):
                    calls.append(("validate-fast", repo_id))
                    return []

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
                check("T1 timeout returns failure", result is False)
                check("T2 timeout is bounded", elapsed < 0.20, f"elapsed={elapsed:.3f}s")
                check("T3 timeout worker is terminated", True)
            finally:
                api_module.HfApi = original_hf_api
                api_module._set_progress_bar = original_progress

            calls.clear()
            api_module.HfApi = FastHfApi
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
