#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atomgit upload --path-in-repo 功能集成测试（不触碰真实远程仓库）。

策略沿用 test_upload_progress.py 的约定：用 Click CliRunner 调用真实
`atomgit upload` 命令链路，把底层 HF `upload_folder` 替换为假函数，
捕获调用瞬间实际传入的 `path_in_repo` / `folder_path` 等参数，据此验证
仓库内路径前缀的规范化与传递逻辑。

设计契约：打桩与测试全部位于 tests/ 内，不修改业务源码；仅当本测试模块
被 import 时才会对业务对象的运行时引用生效，进程结束即失效。

运行：conda run -n atomgit_cli python tests/test_upload_path_in_repo.py
"""
import sys
import tempfile
from pathlib import Path
from click.testing import CliRunner

import atomgit  # noqa: F401  触发包初始化
# atomgit/__init__.py 的 `from .api import api` 会把包级 api 名字
# 覆盖为 HuggingFaceAPI 实例，故用 sys.modules 取真正的 api 模块。
api_mod = sys.modules["atomgit.api"]
cfg_mod = sys.modules["atomgit.config"]
from atomgit.cli import cli

results = []


def check(name, cond, detail=""):
    results.append((name, cond, detail))
    flag = "PASS" if cond else "FAIL"
    print(f"[{flag}] {name}" + (f"  -> {detail}" if detail else ""))


# 假的 HF upload_folder：捕获调用参数
captured = []


def fake_upload_folder(**kwargs):
    captured.append({
        "repo_id": kwargs.get("repo_id"),
        "folder_path": kwargs.get("folder_path"),
        "path_in_repo": kwargs.get("path_in_repo"),
        "commit_message": kwargs.get("commit_message"),
    })
    return "fake-commit-url"


api_mod.upload_folder = fake_upload_folder

# stub 鉴权
cfg_mod.config.is_logged_in = lambda: True
cfg_mod.config.get_credentials = lambda: {"token": "fake-token-0123456789"}


def main():
    with tempfile.TemporaryDirectory() as td:
        tdpath = Path(td)
        # 单文件
        (tdpath / "file.bin").write_bytes(b"x" * 100)
        # 目录（含子目录，验证目录上传的 path_in_repo 透传）
        sub = tdpath / "modeldir"
        sub.mkdir()
        (sub / "a.txt").write_text("a")
        (sub / "b.txt").write_text("b")

        runner = CliRunner()
        with runner.isolated_filesystem():
            # --- T1: 文件上传，不指定 path_in_repo → 根目录 "./" ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(tdpath / "file.bin"),
                                    "--repo-id", "user/repo"])
            check("T1 文件-默认 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T1 文件-默认 path_in_repo='./'",
                      captured[0]["path_in_repo"] == "./",
                      f"path_in_repo={captured[0]['path_in_repo']!r}")

            # --- T2: 文件上传，--path-in-repo sub/ ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(tdpath / "file.bin"),
                                    "--repo-id", "user/repo",
                                    "--path-in-repo", "sub/"])
            check("T2 文件-sub exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T2 文件 path_in_repo 规范为 'sub/'",
                      captured[0]["path_in_repo"] == "sub/",
                      f"path_in_repo={captured[0]['path_in_repo']!r}")

            # --- T3: 文件上传，--path-in-repo 多层 a/b/c ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(tdpath / "file.bin"),
                                    "--repo-id", "user/repo",
                                    "--path-in-repo", "a/b/c"])
            check("T3 文件-多层 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T3 文件 path_in_repo 规范为 'a/b/c/'",
                      captured[0]["path_in_repo"] == "a/b/c/",
                      f"path_in_repo={captured[0]['path_in_repo']!r}")

            # --- T4: 文件上传，--path-in-repo ./extra/（带 ./ 前缀，应被规整） ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(tdpath / "file.bin"),
                                    "--repo-id", "user/repo",
                                    "--path-in-repo", "./extra/"])
            check("T4 文件-带./ exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T4 './extra/' 规范为 'extra/'",
                      captured[0]["path_in_repo"] == "extra/",
                      f"path_in_repo={captured[0]['path_in_repo']!r}")

            # --- T5: 文件上传，--path-in-repo ../ （路径穿越，应被拒绝） ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(tdpath / "file.bin"),
                                    "--repo-id", "user/repo",
                                    "--path-in-repo", "../evil"])
            check("T5 路径穿越被拒绝(非0退出)", r.exit_code != 0, f"exit={r.exit_code}")
            check("T5 未调用 HF上传", len(captured) == 0, f"calls={len(captured)}")

            # --- T6: 目录上传，--path-in-repo sub/ ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(sub),
                                    "--repo-id", "user/repo",
                                    "--path-in-repo", "sub/"])
            check("T6 目录-sub exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T6 目录 path_in_repo='sub/'",
                      captured[0]["path_in_repo"] == "sub/",
                      f"path_in_repo={captured[0]['path_in_repo']!r}")
                # 目录上传应直接用原目录（不再复制到 .tmp_upload）
                check("T6 目录 folder_path=原目录",
                      captured[0]["folder_path"] == str(sub),
                      f"folder_path={captured[0]['folder_path']}")

            # --- T7: 目录上传，不指定 → 根目录 "./" ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(sub), "--repo-id", "user/repo"])
            check("T7 目录-默认 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T7 目录-默认 path_in_repo='./'",
                      captured[0]["path_in_repo"] == "./",
                      f"path_in_repo={captured[0]['path_in_repo']!r}")

            # --- T8: -p 短选项别名 ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(tdpath / "file.bin"),
                                    "--repo-id", "user/repo",
                                    "-p", "short/"])
            check("T8 -p短选项 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T8 -p 等价 --path-in-repo",
                      captured[0]["path_in_repo"] == "short/",
                      f"path_in_repo={captured[0]['path_in_repo']!r}")

            # --- T9: 临时目录清理（文件上传分支会复制到 .tmp_upload）---
            leftover = Path.cwd() / ".tmp_upload"
            check("T9 .tmp_upload 已清理", not leftover.exists(), f"exists={leftover.exists()}")

    print("\n" + "=" * 50)
    passed = sum(1 for _, c, _ in results if c)
    print(f"汇总: {passed}/{len(results)} 通过")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
