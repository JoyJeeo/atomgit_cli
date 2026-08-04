#!/usr/bin/env python3
"""Single-file fallback uploads use unique, automatically cleaned temp trees."""

import tempfile
from pathlib import Path

import atomgit  # noqa: F401
import sys


api_mod = sys.modules["atomgit.api"]
cfg = sys.modules["atomgit.config"].config
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    original_upload = api_mod.upload_folder
    original_credentials = cfg.get_credentials
    captured_paths = []
    cfg.get_credentials = lambda: {"token": "fake-token"}
    try:
        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as work_dir:
            source = Path(source_dir) / "weights.bin"
            source.write_bytes(b"weights")
            work_path = Path(work_dir)

            def successful_upload(**kwargs):
                upload_path = Path(kwargs["folder_path"])
                captured_paths.append(upload_path)
                check("fallback directory exists during call", upload_path.is_dir())
                check("fallback is outside working directory", upload_path.parent != work_path)
                check(
                    "fallback preserves repository layout",
                    (upload_path / "models" / source.name).read_bytes() == b"weights",
                )
                return "commit-url"

            api_mod.upload_folder = successful_upload
            previous_cwd = Path.cwd()
            try:
                import os

                os.chdir(work_path)
                first = api_mod.api.upload_folder(
                    source,
                    "user/repo",
                    path_in_repo="models",
                    ignore_patterns=["*.tmp"],
                )
                second = api_mod.api.upload_folder(
                    source,
                    "user/repo",
                    path_in_repo="models",
                    ignore_patterns=["*.tmp"],
                )
            finally:
                os.chdir(previous_cwd)

            check("successful fallbacks return success", first is True and second is True)
            check(
                "fallback directories are unique",
                len(captured_paths) == 2 and captured_paths[0] != captured_paths[1],
            )
            check(
                "successful fallback directories are removed",
                all(not path.exists() for path in captured_paths),
            )
            check("working tree has no shared fallback", not (work_path / ".tmp_upload").exists())

            def failing_upload(**kwargs):
                upload_path = Path(kwargs["folder_path"])
                captured_paths.append(upload_path)
                raise RuntimeError("offline fallback failure")

            api_mod.upload_folder = failing_upload
            failed = api_mod.api.upload_folder(
                source,
                "user/repo",
                ignore_patterns=["*.tmp"],
            )
            check("failed fallback reports failure", failed is False)
            check("failed fallback directory is removed", not captured_paths[-1].exists())
    finally:
        api_mod.upload_folder = original_upload
        cfg.get_credentials = original_credentials

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
