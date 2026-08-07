#!/usr/bin/env python3
"""Offline validation tests for upload timeout and worker options."""
import tempfile
from pathlib import Path
from click.testing import CliRunner
import atomgit  # noqa: F401
from atomgit.cli import cli
import sys

api_mod = sys.modules["atomgit.api"]
cfg_mod = sys.modules["atomgit.config"]
cfg_mod.config.is_logged_in = lambda: True


def main():
    with tempfile.TemporaryDirectory() as td:
        folder = Path(td) / "folder"
        folder.mkdir()
        (folder / "file.txt").write_text("x")
        file_path = Path(td) / "single.txt"
        file_path.write_text("x")
        runner = CliRunner()
        original = api_mod.api.upload_directory
        calls = []
        api_mod.api.upload_directory = lambda *a, **kw: calls.append(kw) or True
        try:
            cases = [
                ([str(folder), "--repo-id", "user/repo", "--timeout", "0"], "超时时间"),
                ([str(folder), "--repo-id", "user/repo", "--timeout", "-1"], "超时时间"),
                ([str(folder), "--repo-id", "user/repo", "--resumable", "--num-workers", "0"], "worker"),
                ([str(folder), "--repo-id", "user/repo", "--resumable", "--num-workers", "-2"], "worker"),
                ([str(folder), "--repo-id", "user/repo", "--no-resumable", "--num-workers", "2"], "worker"),
                ([str(folder), "--repo-id", "user/repo", "--resumable", "--message", "release"], "message"),
                ([str(file_path), "--repo-id", "user/repo", "--num-workers", "2"], "worker"),
            ]
            passed = 0
            for args, marker in cases:
                result = runner.invoke(cli, ["upload", *args])
                ok = result.exit_code == 2 and marker in result.output.lower()
                print(f"[{'PASS' if ok else 'FAIL'}] {' '.join(args)}")
                passed += ok
            valid = runner.invoke(
                cli,
                ["upload", str(folder), "--repo-id", "user/repo", "--timeout", "1",
                 "--num-workers", "1", "--path-in-repo", "sub/"],
            )
            ok = (
                valid.exit_code == 0
                and len(calls) == 1
                and calls[0]["resumable"] is True
                and calls[0]["path_in_repo"] == "sub/"
            )
            print(f"[{'PASS' if ok else 'FAIL'}] default resumable options accepted")
            passed += ok
            explicit = runner.invoke(
                cli,
                ["upload", str(folder), "--repo-id", "user/repo", "--timeout", "1",
                 "--resumable", "--num-workers", "1"],
            )
            ok = explicit.exit_code == 0 and len(calls) == 2
            print(f"[{'PASS' if ok else 'FAIL'}] explicit resumable remains accepted")
            passed += ok
            cfg_mod.config.is_logged_in = lambda: False
            unauthenticated_conflict = runner.invoke(
                cli,
                ["upload", str(folder), "--repo-id", "user/repo",
                 "--no-resumable", "--num-workers", "2"],
            )
            ok = (
                unauthenticated_conflict.exit_code == 2
                and "worker" in unauthenticated_conflict.output.lower()
                and len(calls) == 2
            )
            print(f"[{'PASS' if ok else 'FAIL'}] conflicts precede authentication")
            passed += ok
            print(f"summary: {passed}/10 passed")
            return 0 if passed == 10 else 1
        finally:
            api_mod.api.upload_directory = original


if __name__ == "__main__":
    raise SystemExit(main())
