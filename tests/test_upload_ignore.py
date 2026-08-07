#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atomgit upload --ignore 功能集成测试（不触碰真实远程仓库）。

策略沿用既有测试的约定：用 Click CliRunner 调用真实 `atomgit upload`
命令链路，把底层 HF `upload_folder` 替换为假函数，捕获调用瞬间实际传入
的 `ignore_patterns` / `path_in_repo` 等参数，据此验证忽略模式的解析与
端到端传递，以及与 --path-in-repo / --repo-type 的组合行为。

设计契约：打桩与测试全部位于 tests/ 内，不修改业务源码；仅当本测试模块
被 import 时才会对业务对象的运行时引用生效，进程结束即失效。

运行：conda run -n atomgit_cli python tests/test_upload_ignore.py
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
from atomgit.utils import parse_ignore_patterns

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
        "repo_type": kwargs.get("repo_type"),
        "revision": kwargs.get("revision"),
        "ignore_patterns": kwargs.get("ignore_patterns"),  # 关键观测点
        "commit_message": kwargs.get("commit_message"),
    })
    return "fake-commit-url"


api_mod.upload_folder = fake_upload_folder

# stub 鉴权
cfg_mod.config.is_logged_in = lambda: True
cfg_mod.config.get_credentials = lambda: {"token": "fake-token-0123456789"}


def main():
    # --- 纯函数单测：parse_ignore_patterns ---
    check("U1 None → None", parse_ignore_patterns(None) is None,
          f"got={parse_ignore_patterns(None)!r}")
    check("U2 空串 → None", parse_ignore_patterns("") is None,
          f"got={parse_ignore_patterns('')!r}")
    check("U3 单模式", parse_ignore_patterns("*.tmp") == ["*.tmp"],
          f"got={parse_ignore_patterns('*.tmp')}")
    check("U4 多模式去空白", parse_ignore_patterns(" *.tmp , logs/ , .DS_Store ") == ["*.tmp", "logs/", ".DS_Store"],
          f"got={parse_ignore_patterns(' *.tmp , logs/ , .DS_Store ')}")
    check("U5 去空片段", parse_ignore_patterns(",*.tmp,,") == ["*.tmp"],
          f"got={parse_ignore_patterns(',*.tmp,,')}")
    check("U6 去重保序", parse_ignore_patterns("*.tmp,*.tmp,logs/") == ["*.tmp", "logs/"],
          f"got={parse_ignore_patterns('*.tmp,*.tmp,logs/')}")
    check("U7 全空白 → None", parse_ignore_patterns(" , , ") is None,
          f"got={parse_ignore_patterns(' , , ')}")

    # --- CLI 端到端 ---
    with tempfile.TemporaryDirectory() as td:
        tdpath = Path(td)
        (tdpath / "file.bin").write_bytes(b"x" * 100)
        sub = tdpath / "modeldir"
        sub.mkdir()
        (sub / "a.txt").write_text("a")
        (sub / "b.tmp").write_text("b")

        runner = CliRunner()
        with runner.isolated_filesystem():
            # --- T1: 目录上传，不指定 --ignore → 不传 ignore_patterns ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(sub), "--repo-id", "user/repo",
                                    "--no-resumable"])
            check("T1 目录-默认 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T1 目录-默认不传 ignore_patterns",
                      captured[0]["ignore_patterns"] is None,
                      f"ignore={captured[0]['ignore_patterns']!r}")

            # --- T2: 目录上传，--ignore 单模式 *.tmp ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(sub), "--repo-id", "user/repo",
                                    "--ignore", "*.tmp", "--no-resumable"])
            check("T2 目录-单模式 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T2 ignore_patterns=['*.tmp']",
                      captured[0]["ignore_patterns"] == ["*.tmp"],
                      f"ignore={captured[0]['ignore_patterns']!r}")

            # --- T3: 目录上传，--ignore 多模式（逗号分隔+空白） ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(sub), "--repo-id", "user/repo",
                                    "--ignore", " *.tmp , logs/ , .DS_Store ",
                                    "--no-resumable"])
            check("T3 目录-多模式 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T3 ignore_patterns 规整为 ['*.tmp','logs/','.DS_Store']",
                      captured[0]["ignore_patterns"] == ["*.tmp", "logs/", ".DS_Store"],
                      f"ignore={captured[0]['ignore_patterns']!r}")

            # --- T4: -i 短选项别名 ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(sub), "--repo-id", "user/repo",
                                    "-i", "*.tmp", "--no-resumable"])
            check("T4 -i短选项 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T4 -i 等价 --ignore",
                      captured[0]["ignore_patterns"] == ["*.tmp"],
                      f"ignore={captured[0]['ignore_patterns']!r}")

            # --- T5: --ignore 与 --path-in-repo / --repo-type 组合 ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(sub), "--repo-id", "user/repo",
                                    "--ignore", "*.tmp,*.log",
                                    "--path-in-repo", "weights/",
                                    "--repo-type", "model", "--no-resumable"])
            check("T5 组合 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T5 ignore_patterns=['*.tmp','*.log']",
                      captured[0]["ignore_patterns"] == ["*.tmp", "*.log"],
                      f"ignore={captured[0]['ignore_patterns']!r}")
                check("T5 path_in_repo='weights/'",
                      captured[0]["path_in_repo"] == "weights/",
                      f"path_in_repo={captured[0]['path_in_repo']!r}")
                check("T5 repo_type='model'",
                      captured[0]["repo_type"] == "model",
                      f"repo_type={captured[0]['repo_type']!r}")

            # --- T6: 单文件上传 + --ignore（拒绝歧义组合） ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(tdpath / "file.bin"),
                                    "--repo-id", "user/repo",
                                    "--ignore", "*.tmp"])
            check("T6 文件+ignore exit=2", r.exit_code == 2, f"exit={r.exit_code}")
            check("T6 文件+ignore 不调用上传", not captured)

            # --- T7: 临时目录清理 ---
            leftover = Path.cwd() / ".tmp_upload"
            check("T7 .tmp_upload 已清理", not leftover.exists(), f"exists={leftover.exists()}")

    print("\n" + "=" * 50)
    passed = sum(1 for _, c, _ in results if c)
    print(f"汇总: {passed}/{len(results)} 通过")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
