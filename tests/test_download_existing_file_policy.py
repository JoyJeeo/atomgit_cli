#!/usr/bin/env python3
"""Verify that existing download files are skipped with accurate guidance."""

import contextlib
import io
import sys
import tempfile
from pathlib import Path

import atomgit  # noqa: F401
from click.testing import CliRunner


api_mod = sys.modules["atomgit.api"]
cli_mod = sys.modules["atomgit.cli"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    original_list = api_mod._atomgit_list_repo_files
    original_fetch = api_mod._download_atomgit_file
    original_credentials = api_mod.config.get_credentials
    original_cli_download = cli_mod.api.download_repo
    original_logged_in = cli_mod.config.is_logged_in
    fetches = []
    try:
        api_mod._atomgit_list_repo_files = lambda *args, **kwargs: (
            "model",
            ["existing.bin"],
        )
        api_mod.config.get_credentials = lambda: None

        def fake_fetch(repo_id, repo_type, filename, destination, token):
            fetches.append(filename)
            destination.write_bytes(b"new")

        api_mod._download_atomgit_file = fake_fetch
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "existing.bin"
            destination.write_bytes(b"old")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                success = api_mod.api.download_repo("user/repo", Path(directory))
            text = output.getvalue()
            check("default existing-file download succeeds", success)
            check("default policy does not fetch", fetches == [])
            check("default policy preserves file", destination.read_bytes() == b"old")
            check("skip output discloses no verification", "未校验" in text, repr(text))
            check("skip output names force override", "--force" in text, repr(text))

            with contextlib.redirect_stdout(io.StringIO()):
                forced = api_mod.api.download_repo(
                    "user/repo", Path(directory), force_download=True
                )
            check("force download succeeds", forced)
            check("force fetches existing file", fetches == ["existing.bin"])
            check("force replaces existing file", destination.read_bytes() == b"new")

        cli_mod.api.download_repo = lambda *args, **kwargs: True
        cli_mod.config.is_logged_in = lambda: True
        with CliRunner().isolated_filesystem():
            target = Path("target")
            target.mkdir()
            (target / "existing.bin").write_bytes(b"old")
            result = CliRunner().invoke(
                cli_mod.cli, ["download", "user/repo", "-d", str(target)]
            )
        check("CLI existing-directory download succeeds", result.exit_code == 0)
        check("CLI does not claim resumable mode", "断点续传" not in result.output)
        check("CLI explains skip policy", "默认跳过" in result.output, repr(result.output))
    finally:
        api_mod._atomgit_list_repo_files = original_list
        api_mod._download_atomgit_file = original_fetch
        api_mod.config.get_credentials = original_credentials
        cli_mod.api.download_repo = original_cli_download
        cli_mod.config.is_logged_in = original_logged_in

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
