#!/usr/bin/env python3
"""Reject repository filenames that escape the selected download root."""

import os
import sys
import tempfile
from pathlib import Path

import atomgit  # noqa: F401


api_mod = sys.modules["atomgit.api"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    original_list = api_mod._atomgit_list_repo_files
    original_fetch = api_mod._download_atomgit_file
    original_credentials = api_mod.config.get_credentials
    calls = []

    def fake_fetch(repo_id, repo_type, filename, dest, token):
        calls.append(Path(dest))
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        Path(dest).write_bytes(b"content")

    api_mod.config.get_credentials = lambda: None
    api_mod._download_atomgit_file = fake_fetch
    try:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir) / "download"
            malicious_names = [
                "../escape.bin",
                "sub/../../escape.bin",
                "/tmp/absolute.bin",
                "C:/windows-drive.bin",
                r"C:\windows-drive.bin",
                r"..\windows-escape.bin",
                r"\\server\share\file.bin",
                "sub//empty-segment.bin",
                "sub/./dot-segment.bin",
                "sub/control\nname.bin",
                "sub/nul\x00name.bin",
            ]
            for filename in malicious_names:
                calls.clear()
                api_mod._atomgit_list_repo_files = (
                    lambda repo_id, token, repo_type=None, name=filename:
                    ("model", [name])
                )
                result = api_mod.api.download_repo("user/repo", root, True)
                check(
                    f"reject unsafe remote filename {filename!r}",
                    result is False and not calls,
                    f"result={result} calls={calls!r}",
                )

            outside = Path(temporary_dir) / "outside"
            outside.mkdir()
            link = root / "linked"
            root.mkdir(parents=True, exist_ok=True)
            try:
                os.symlink(outside, link, target_is_directory=True)
                symlink_supported = True
            except (OSError, NotImplementedError):
                symlink_supported = False

            if symlink_supported:
                calls.clear()
                api_mod._atomgit_list_repo_files = (
                    lambda repo_id, token, repo_type=None:
                    ("model", ["linked/escape.bin"])
                )
                result = api_mod.api.download_repo("user/repo", root, True)
                check(
                    "reject existing symlink escape",
                    result is False and not calls and not (outside / "escape.bin").exists(),
                    f"result={result} calls={calls!r}",
                )
            else:
                check("symlink escape test unavailable on platform", True)

            calls.clear()
            api_mod._atomgit_list_repo_files = (
                lambda repo_id, token, repo_type=None:
                ("model", ["嵌套/安全文件.bin"])
            )
            result = api_mod.api.download_repo("user/repo", root, True)
            expected = root.resolve() / "嵌套" / "安全文件.bin"
            check(
                "normal nested non-ASCII filename stays inside root",
                result is True and calls == [expected] and expected.is_file(),
                f"result={result} calls={calls!r}",
            )

            calls.clear()
            api_mod._atomgit_list_repo_files = (
                lambda repo_id, token, repo_type=None:
                ("model", ["../single.bin"])
            )
            result = api_mod.api.download_file(
                "user/repo", "../single.bin", root, True
            )
            check(
                "single-file download also rejects traversal",
                result is False and not calls,
                f"result={result} calls={calls!r}",
            )

            calls.clear()
            api_mod._atomgit_list_repo_files = (
                lambda repo_id, token, repo_type=None:
                ("model", ["safe-first.bin", "../unsafe-second.bin"])
            )
            result = api_mod.api.download_repo("user/repo", root, True)
            check(
                "entire file list is validated before the first download",
                result is False and not calls and not (root / "safe-first.bin").exists(),
                f"result={result} calls={calls!r}",
            )
    finally:
        api_mod._atomgit_list_repo_files = original_list
        api_mod._download_atomgit_file = original_fetch
        api_mod.config.get_credentials = original_credentials

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
