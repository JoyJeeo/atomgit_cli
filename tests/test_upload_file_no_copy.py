#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atomgit upload 单文件上传「无本地拷贝」优化集成测试（不触碰真实远程仓库）。

优化目标：单文件上传不再先 copy 到 ``.tmp_upload`` 临时目录，而是直接
用 HF ``upload_file(path_or_fileobj=<原路径>)`` 上传，省去一次本地磁盘
拷贝开销。仅在 HF 版本过旧无 ``upload_file``，或用户显式传了
``--ignore``（单文件下意义不大但保留语义）时，回退到旧的临时目录拷贝
路径。

策略沿用既有测试的约定：用 Click CliRunner 调用真实 ``atomgit upload``
命令链路，把两个底层 HF 上传入口（``upload_file``、``upload_folder``）
都替换为假函数，并 monkey-patch ``Path.copy2`` 不可行——改为直接
检测是否产生了 ``.tmp_upload`` 临时目录，以及实际调用的是哪个入口、
传入的 ``path_or_fileobj`` 是否为原文件路径。

设计契约：打桩与测试全部位于 tests/ 内，不修改业务源码；仅当本测试模块
被 import 时才会对业务对象的运行时引用生效，进程结束即失效。

运行：conda run -n atomgit_cli python tests/test_upload_file_no_copy.py
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


# 捕获：upload_file 调用（新路径）
uf_captured = []


def fake_upload_file(**kwargs):
    uf_captured.append(dict(kwargs))
    return "fake-commit-url"


# 捕获：upload_folder 调用（回退路径）
ufold_captured = []


def fake_upload_folder(**kwargs):
    ufold_captured.append(dict(kwargs))
    return "fake-commit-url"


# 替换 api 模块引用的两个底层入口
api_mod.hf_upload_file = fake_upload_file
api_mod.upload_folder = fake_upload_folder

# stub 鉴权
cfg_mod.config.is_logged_in = lambda: True
cfg_mod.config.get_credentials = lambda: {"token": "fake-token-0123456789"}


def main():
    with tempfile.TemporaryDirectory() as td:
        tdpath = Path(td)
        fpath = tdpath / "weights.bin"
        fpath.write_bytes(b"x" * 100)  # 100 字节「大」文件

        runner = CliRunner()
        with runner.isolated_filesystem():
            # --- T1: 单文件默认上传 → 走 upload_file，path_or_fileobj=原路径 ---
            uf_captured.clear(); ufold_captured.clear()
            r = runner.invoke(cli, ["upload", str(fpath), "--repo-id", "user/repo"])
            check("T1 文件默认 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            check("T1 走 upload_file（非 upload_folder）",
                  len(uf_captured) == 1 and len(ufold_captured) == 0,
                  f"upload_file={len(uf_captured)} upload_folder={len(ufold_captured)}")
            if uf_captured:
                call = uf_captured[0]
                check("T1 path_or_fileobj=原文件路径",
                      call.get("path_or_fileobj") == str(fpath),
                      f"path_or_fileobj={call.get('path_or_fileobj')}")
                check("T1 path_in_repo=文件名",
                      call.get("path_in_repo") == "weights.bin",
                      f"path_in_repo={call.get('path_in_repo')!r}")
                check("T1 传了 token", bool(call.get("token")),
                      f"token={'有' if call.get('token') else '无'}")

            # --- T2: 单文件 + --path-in-repo sub/ → path_in_repo='sub/weights.bin' ---
            uf_captured.clear(); ufold_captured.clear()
            r = runner.invoke(cli, ["upload", str(fpath), "--repo-id", "user/repo",
                                   "--path-in-repo", "sub/"])
            check("T2 sub/ exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if uf_captured:
                check("T2 path_in_repo='sub/weights.bin'",
                      uf_captured[0].get("path_in_repo") == "sub/weights.bin",
                      f"path_in_repo={uf_captured[0].get('path_in_repo')!r}")

            # --- T3: 单文件 + --repo-type dataset + --revision dev ---
            uf_captured.clear(); ufold_captured.clear()
            r = runner.invoke(cli, ["upload", str(fpath), "--repo-id", "user/repo",
                                   "--repo-type", "dataset", "--revision", "dev"])
            check("T3 dataset+dev accepted", r.exit_code == 0, f"exit={r.exit_code}")
            if uf_captured:
                check("T3 dataset 使用 model 传输路由",
                      uf_captured[0].get("repo_type") == "model",
                      f"repo_type={uf_captured[0].get('repo_type')!r}")
                check("T3 revision=dev",
                      uf_captured[0].get("revision") == "dev",
                      f"revision={uf_captured[0].get('revision')!r}")

            # --- T4: 无本地拷贝：.tmp_upload 不应被创建 ---
            leftover = Path.cwd() / ".tmp_upload"
            check("T4 无 .tmp_upload 临时目录", not leftover.exists(),
                  f"exists={leftover.exists()}")

            # --- T5: 单文件 + --ignore（CLI 拒绝歧义组合） ---
            uf_captured.clear(); ufold_captured.clear()
            # 先确保 .tmp_upload 不存在
            tp = Path.cwd() / ".tmp_upload"
            if tp.exists():
                import shutil as _sh
                _sh.rmtree(tp)
            r = runner.invoke(cli, ["upload", str(fpath), "--repo-id", "user/repo",
                                   "--ignore", "*.tmp"])
            check("T5 ignore rejected exit=2", r.exit_code == 2, f"exit={r.exit_code}")
            check("T5 ignore 不调用上传",
                  len(ufold_captured) == 0 and len(uf_captured) == 0,
                  f"upload_file={len(uf_captured)} upload_folder={len(ufold_captured)}")
            # 回退路径会在执行中创建 .tmp_upload，结束后清理
            check("T5 回退后 .tmp_upload 已清理", not tp.exists(), f"exists={tp.exists()}")

            # --- T6: 单文件 + message → commit_message 透传 ---
            uf_captured.clear(); ufold_captured.clear()
            r = runner.invoke(cli, ["upload", str(fpath), "--repo-id", "user/repo",
                                   "-m", "add weights"])
            check("T6 message exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            if uf_captured:
                check("T6 commit_message='add weights'",
                      uf_captured[0].get("commit_message") == "add weights",
                      f"msg={uf_captured[0].get('commit_message')!r}")

    print("\n" + "=" * 50)
    passed = sum(1 for _, c, _ in results if c)
    print(f"汇总: {passed}/{len(results)} 通过")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
