#!/usr/bin/env python3
"""Prevent silent writes to main when AtomGit ignores non-default revisions."""
import tempfile
from pathlib import Path
from click.testing import CliRunner
import atomgit  # noqa: F401
from atomgit.cli import cli
import sys


def main():
    cfg = sys.modules["atomgit.config"].config
    cfg.is_logged_in = lambda: True
    api = sys.modules["atomgit.api"].api
    original = api.upload_folder
    original_file = sys.modules["atomgit.api"].hf_upload_file
    calls = []
    api.upload_folder = lambda *a, **kw: calls.append(kw) or True
    sys.modules["atomgit.api"].hf_upload_file = lambda *a, **kw: calls.append(kw) or True
    try:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "file.txt"
            path.write_text("x")
            runner = CliRunner()
            rejected = runner.invoke(cli, ["upload", str(path), "--repo-id", "user/repo", "--revision", "dev"])
            rejected_calls = len(calls)
            accepted = runner.invoke(cli, ["upload", str(path), "--repo-id", "user/repo", "--revision", "main"])
        ok = rejected.exit_code == 2 and rejected_calls == 0 and accepted.exit_code == 0 and len(calls) == 1
        print(f"[{'PASS' if ok else 'FAIL'}] non-default rejected; main accepted")
        return 0 if ok else 1
    finally:
        api.upload_folder = original
        sys.modules["atomgit.api"].hf_upload_file = original_file


if __name__ == "__main__":
    raise SystemExit(main())
