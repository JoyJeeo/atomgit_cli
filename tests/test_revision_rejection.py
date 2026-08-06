#!/usr/bin/env python3
"""Forward safe explicit revisions and reject malformed Git refs."""
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
            accepted_dev = runner.invoke(cli, ["upload", str(path), "--repo-id", "user/repo", "--revision", "dev"])
            dev_calls = len(calls)
            rejected = runner.invoke(cli, ["upload", str(path), "--repo-id", "user/repo", "--revision", "bad..ref"])
            accepted = runner.invoke(cli, ["upload", str(path), "--repo-id", "user/repo", "--revision", "main"])
        ok = accepted_dev.exit_code == 0 and dev_calls == 1 and rejected.exit_code == 2 and accepted.exit_code == 0 and len(calls) == 2 and calls[0]["revision"] == "dev"
        print(f"[{'PASS' if ok else 'FAIL'}] safe non-main forwarded; malformed rejected")
        return 0 if ok else 1
    finally:
        api.upload_folder = original
        sys.modules["atomgit.api"].hf_upload_file = original_file


if __name__ == "__main__":
    raise SystemExit(main())
