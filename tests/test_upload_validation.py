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
        original_file = api_mod.api.upload_folder
        original_credentials = cfg_mod.config.get_credentials
        calls = []
        api_mod.api.upload_directory = lambda *a, **kw: calls.append(kw) or True
        api_mod.api.upload_folder = lambda *a, **kw: calls.append(kw) or True
        try:
            cases = [
                ([str(folder), "--repo-id", "user/repo", "--timeout", "0"], "超时时间"),
                ([str(folder), "--repo-id", "user/repo", "--timeout", "-1"], "超时时间"),
                ([str(folder), "--repo-id", "user/repo", "--resumable", "--num-workers", "0"], "worker"),
                ([str(folder), "--repo-id", "user/repo", "--resumable", "--num-workers", "-2"], "worker"),
                ([str(folder), "--repo-id", "user/repo", "--resumable", "--message", "release"], "message"),
                ([str(folder), "--repo-id", "user/repo", "--batch-size", "0"], "batch-size"),
                ([str(folder), "--repo-id", "user/repo", "--batch-size", "-1"], "batch-size"),
                ([str(folder), "--repo-id", "user/repo", "--batch-size", "21"], "batch-size"),
                ([str(folder), "--repo-id", "user/repo", "--batch-size", "two"], "batch-size"),
            ]
            passed = 0
            cfg_mod.config.is_logged_in = lambda: (_ for _ in ()).throw(
                AssertionError("invalid options must fail before authentication")
            )
            for args, marker in cases:
                result = runner.invoke(cli, ["upload", *args])
                ok = result.exit_code == 2 and marker in result.output.lower()
                print(f"[{'PASS' if ok else 'FAIL'}] {' '.join(args)}")
                passed += ok
            help_result = runner.invoke(cli, ["upload", "--help"])
            ok = (
                help_result.exit_code == 0
                and "默认网络请求等待超时" in help_result.output
                and "部分请求阶段有独立等待上限" not in help_result.output
            )
            print(f"[{'PASS' if ok else 'FAIL'}] timeout help has one request contract")
            passed += ok
            cfg_mod.config.is_logged_in = lambda: True
            valid = runner.invoke(
                cli,
                ["upload", str(folder), "--repo-id", "user/repo", "--timeout", "1",
                 "--num-workers", "1", "--path-in-repo", "sub/",
                 "--batch-size", "2"],
            )
            ok = (
                valid.exit_code == 0
                and len(calls) == 1
                and calls[0]["resumable"] is True
                and calls[0]["path_in_repo"] == "sub/"
                and calls[0]["batch_size"] == 2
            )
            print(f"[{'PASS' if ok else 'FAIL'}] default resumable options accepted")
            passed += ok
            ordinary = runner.invoke(
                cli,
                ["upload", str(folder), "--repo-id", "user/repo",
                 "--no-resumable", "--num-workers", "2"],
            )
            ok = ordinary.exit_code == 0 and calls[-1].get("num_workers") == 2
            print(f"[{'PASS' if ok else 'FAIL'}] ordinary mode accepts workers")
            passed += ok
            single = runner.invoke(
                cli,
                ["upload", str(file_path), "--repo-id", "user/repo",
                 "--num-workers", "2", "--batch-size", "2"],
            )
            ok = (
                single.exit_code == 0
                and calls[-1].get("num_workers") == 2
                and "batch_size" not in calls[-1]
            )
            print(f"[{'PASS' if ok else 'FAIL'}] file mode accepts workers")
            passed += ok
            explicit = runner.invoke(
                cli,
                ["upload", str(folder), "--repo-id", "user/repo", "--timeout", "1",
                 "--resumable", "--num-workers", "1"],
            )
            ok = explicit.exit_code == 0 and len(calls) == 4
            print(f"[{'PASS' if ok else 'FAIL'}] explicit resumable remains accepted")
            passed += ok
            cfg_mod.config.is_logged_in = lambda: False
            unauthenticated_conflict = runner.invoke(
                cli,
                ["upload", str(folder), "--repo-id", "user/repo",
                 "--no-resumable", "--num-workers", "2"],
            )
            ok = unauthenticated_conflict.exit_code == 1 and "登录" in unauthenticated_conflict.output
            print(f"[{'PASS' if ok else 'FAIL'}] authentication follows valid worker option")
            passed += ok
            direct_before = len(calls)
            cfg_mod.config.get_credentials = lambda: (_ for _ in ()).throw(
                AssertionError("invalid API values must fail before credentials")
            )
            try:
                direct_results = [
                    original(folder, "user/repo", batch_size=value)
                    for value in (0, -1, 21, 1.5, True, "2")
                ]
            finally:
                cfg_mod.config.get_credentials = original_credentials
            ok = all(result is False for result in direct_results) and len(calls) == direct_before
            print(f"[{'PASS' if ok else 'FAIL'}] direct API rejects invalid batch sizes")
            passed += ok
            print(f"summary: {passed}/16 passed")
            return 0 if passed == 16 else 1
        finally:
            api_mod.api.upload_directory = original
            api_mod.api.upload_folder = original_file
            cfg_mod.config.get_credentials = original_credentials


if __name__ == "__main__":
    raise SystemExit(main())
