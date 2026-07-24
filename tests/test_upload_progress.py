#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atomgit upload 进度条功能集成测试（不触碰真实远程仓库）。

策略：用 Click CliRunner 调用真实 `atomgit upload` 命令，但把底层 HF
`upload_folder` 替换为假函数，捕获调用瞬间 HF 进度条的实际禁用状态，
从而验证 `--no-progress-bar` 开关的端到端传递与切换逻辑。

运行：conda run -n atomgit_cli python -m pytest tests/test_upload_progress.py -v
或：  conda run -n atomgit_cli python tests/test_upload_progress.py
"""
import sys
import tempfile
from pathlib import Path
from click.testing import CliRunner

import atomgit  # noqa: F401  触发包初始化
# 注意：atomgit/__init__.py 的 `from .api import api` 会把包级 `api` 名字
# 覆盖为 HuggingFaceAPI 实例，因此必须用 sys.modules 取真正的 api 模块。
api_mod = sys.modules["atomgit.api"]
from atomgit.cli import cli
from huggingface_hub.utils import are_progress_bars_disabled

results = []


def check(name, cond, detail=""):
    results.append((name, cond, detail))
    flag = "PASS" if cond else "FAIL"
    print(f"[{flag}] {name}" + (f"  -> {detail}" if detail else ""))


# 假的 HF upload_folder：捕获调用参数 + 调用瞬间的进度条状态
captured = []


def fake_upload_folder(**kwargs):
    captured.append({
        "repo_id": kwargs.get("repo_id"),
        "folder_path": kwargs.get("folder_path"),
        "commit_message": kwargs.get("commit_message"),
        "pb_disabled_at_call": are_progress_bars_disabled(),
    })
    return "fake-commit-url"


# 替换 api 模块内导入的两个底层上传入口名字（方法内调用的是模块全局名）：
# - upload_folder（目录上传 + 文件回退路径）
# - hf_upload_file（单文件上传主路径，v1.0.5 起新增）
api_mod.upload_folder = fake_upload_folder
api_mod.hf_upload_file = fake_upload_folder

# stub 鉴权，让 upload 通过前置登录校验（同一 Config 单例，cli.py 也用同一对象）
# 同样因 __init__.py 的 `from .config import config` 把子模块名遮蔽为实例，
# 故用 sys.modules 取真正的 config 模块，再访问其中的全局单例 config。
cfg_mod = sys.modules["atomgit.config"]
cfg_mod.config.is_logged_in = lambda: True
cfg_mod.config.get_credentials = lambda: {"token": "fake-token-0123456789"}


def main():
    with tempfile.TemporaryDirectory() as td:
        tdpath = Path(td)
        # 准备一个单文件 + 一个目录
        (tdpath / "file.bin").write_bytes(b"x" * 100)
        sub = tdpath / "modeldir"
        sub.mkdir()
        (sub / "a.txt").write_text("a")
        (sub / "b.txt").write_text("b")

        runner = CliRunner()
        with runner.isolated_filesystem():
            # --- Test 1: 目录上传，默认（应开启进度条）---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(sub), "--repo-id", "user/repo"])
            check("T1 目录上传默认 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            check("T1 调用 HF 1次", len(captured) == 1, f"calls={len(captured)}")
            if captured:
                check("T1 默认进度条=开启", captured[0]["pb_disabled_at_call"] is False,
                      f"disabled={captured[0]['pb_disabled_at_call']}")

            # --- Test 2: 目录上传，--no-progress-bar（应禁用进度条）---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(sub), "--repo-id", "user/repo",
                                    "--no-progress-bar"])
            check("T2 目录上传-noprog exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T2 --no-progress-bar 确实禁用", captured[0]["pb_disabled_at_call"] is True,
                      f"disabled={captured[0]['pb_disabled_at_call']}")

            # --- Test 3: 单文件上传，默认（应开启）---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(tdpath / "file.bin"),
                                    "--repo-id", "user/repo"])
            check("T3 文件上传默认 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T3 文件默认进度条=开启", captured[0]["pb_disabled_at_call"] is False,
                      f"disabled={captured[0]['pb_disabled_at_call']}")

            # --- Test 4: 单文件上传，--no-progress-bar（应禁用）---
            captured.clear()
            r = runner.invoke(cli, ["upload", str(tdpath / "file.bin"),
                                    "--repo-id", "user/repo", "--no-progress-bar"])
            check("T4 文件上传-noprog exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if captured:
                check("T4 文件 --no-progress-bar 确实禁用", captured[0]["pb_disabled_at_call"] is True,
                      f"disabled={captured[0]['pb_disabled_at_call']}")

            # --- Test 5: 上传结束后进度条应恢复默认开启（不污染进程后续调用）---
            check("T5 上传后进度条恢复开启", are_progress_bars_disabled() is False,
                  f"disabled={are_progress_bars_disabled()}")

            # --- Test 6: .tmp_upload 临时目录已被清理 ---
            leftover = Path.cwd() / ".tmp_upload"
            check("T6 .tmp_upload 已清理", not leftover.exists(), f"exists={leftover.exists()}")

    print("\n" + "=" * 50)
    passed = sum(1 for _, c, _ in results if c)
    print(f"汇总: {passed}/{len(results)} 通过")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
