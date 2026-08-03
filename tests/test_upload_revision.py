#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atomgit upload --revision 功能集成测试（不触碰真实远程仓库）。

策略沿用既有测试的约定：用 Click CliRunner 调用真实 `atomgit upload`
命令链路，把底层 HF `upload_folder` 替换为假函数，捕获调用瞬间实际传入
的 `revision` / `repo_type` / `path_in_repo` 等参数，据此验证目标分支的
端到端传递，以及与 --repo-type / --path-in-repo 的组合行为。

设计契约：打桩与测试全部位于 tests/ 内，不修改业务源码；仅当本测试模块
被 import 时才会对业务对象的运行时引用生效，进程结束即失效。

运行：conda run -n atomgit_cli python tests/test_upload_revision.py
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
        "repo_type": kwargs.get("repo_type"),
        "revision": kwargs.get("revision"),  # 关键观测点
        "commit_message": kwargs.get("commit_message"),
    })
    return "fake-commit-url"


# 替换 api 模块内导入的两个底层上传入口名字（方法内调用的是模块全局名）：
# - upload_folder（目录上传 + 文件回退路径）
# - hf_upload_file（单文件上传主路径，v1.0.5 起新增）
# 两入口均透传 revision，故共用同一桩函数即可。
api_mod.upload_folder = fake_upload_folder
api_mod.hf_upload_file = fake_upload_folder

# stub 鉴权
cfg_mod.config.is_logged_in = lambda: True
cfg_mod.config.get_credentials = lambda: {"token": "fake-token-0123456789"}


def main():
    with tempfile.TemporaryDirectory() as td:
        tdpath = Path(td)
        # 单文件 + 目录
        (tdpath / "file.bin").write_bytes(b"x" * 100)
        sub = tdpath / "modeldir"
        sub.mkdir()
        (sub / "a.txt").write_text("a")

        runner = CliRunner()
        with runner.isolated_filesystem():
            # --- T1: 文件上传，不指定 revision → HF 默认（不传 revision） ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(tdpath / "file.bin"),
                                    "--repo-id", "user/repo"])
            check("T1 文件-默认 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T1 文件-默认不传 revision",
                      captured[0]["revision"] is None,
                      f"revision={captured[0]['revision']!r}")

            # --- T2: 文件上传，--revision dev ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(tdpath / "file.bin"),
                                    "--repo-id", "user/repo",
                                    "--revision", "dev"])
            check("T2 文件-dev exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T2 文件 revision=dev",
                      captured[0]["revision"] == "dev",
                      f"revision={captured[0]['revision']!r}")

            # --- T3: 文件上传，--revision 带版本号 v1.0 ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(tdpath / "file.bin"),
                                    "--repo-id", "user/repo",
                                    "--revision", "v1.0"])
            check("T3 文件-v1.0 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T3 文件 revision=v1.0",
                      captured[0]["revision"] == "v1.0",
                      f"revision={captured[0]['revision']!r}")

            # --- T4: 目录上传，--revision dev ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(sub),
                                    "--repo-id", "user/repo",
                                    "--revision", "dev"])
            check("T4 目录-dev exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T4 目录 revision=dev",
                      captured[0]["revision"] == "dev",
                      f"revision={captured[0]['revision']!r}")
                check("T4 目录 folder_path=原目录",
                      captured[0]["folder_path"] == str(sub),
                      f"folder_path={captured[0]['folder_path']}")

            # --- T5: --revision 与 --repo-type / --path-in-repo 组合 ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(tdpath / "file.bin"),
                                    "--repo-id", "user/repo",
                                    "--revision", "dev",
                                    "--repo-type", "dataset",
                                    "--path-in-repo", "sub/"])
            check("T5 组合 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T5 revision=dev",
                      captured[0]["revision"] == "dev",
                      f"revision={captured[0]['revision']!r}")
                check("T5 dataset 使用 model 传输路由",
                      captured[0]["repo_type"] == "model",
                      f"repo_type={captured[0]['repo_type']!r}")
                check("T5 path_in_repo='sub/file.bin'",
                      captured[0]["path_in_repo"] == "sub/file.bin",
                      f"path_in_repo={captured[0]['path_in_repo']!r}")

            # --- T6: revision 全特性选项组合（目录 + 全部参数） ---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(sub),
                                    "--repo-id", "user/repo",
                                    "--revision", "feature/x",
                                    "--repo-type", "model",
                                    "--path-in-repo", "weights/",
                                    "-m", "add weights",
                                    "--no-progress-bar",
                                    "-t", "600"])
            check("T6 全参数 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T6 revision=feature/x",
                      captured[0]["revision"] == "feature/x",
                      f"revision={captured[0]['revision']!r}")
                check("T6 repo_type=model",
                      captured[0]["repo_type"] == "model",
                      f"repo_type={captured[0]['repo_type']!r}")
                check("T6 path_in_repo='weights/'",
                      captured[0]["path_in_repo"] == "weights/",
                      f"path_in_repo={captured[0]['path_in_repo']!r}")
                # T6 是目录上传，走 upload_folder，folder_path 应为原目录
                check("T6 folder_path=原目录",
                      captured[0]["folder_path"] == str(sub),
                      f"folder_path={captured[0]['folder_path']}")
                check("T6 commit_message='add weights'",
                      captured[0]["commit_message"] == "add weights",
                      f"msg={captured[0]['commit_message']!r}")

            # --- T7: 临时目录清理（单文件默认走 hf_upload_file，不再产生 .tmp_upload） ---
            leftover = Path.cwd() / ".tmp_upload"
            check("T7 无 .tmp_upload 临时目录", not leftover.exists(), f"exists={leftover.exists()}")

    print("\n" + "=" * 50)
    passed = sum(1 for _, c, _ in results if c)
    print(f"汇总: {passed}/{len(results)} 通过")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
