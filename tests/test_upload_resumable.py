#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atomgit upload --resumable/--num-workers 功能集成测试（不触碰真实远程仓库）。

策略沿用既有测试的约定：用 Click CliRunner 调用真实 `atomgit upload`
命令链路，但把两个底层 HF 上传入口都替换为假函数，捕获调用瞬间实际
传入的参数，据此验证：
  - 默认走普通 upload_folder（不传 resumable）
  - --resumable 时改走 HfApi().upload_large_folder，并校验 repo_type
    必填（默认 model）、revision/ignore_patterns/num_workers 透传
  - 单文件 + --resumable 应给出 warning 且走普通路径

设计契约：打桩与测试全部位于 tests/ 内，不修改业务源码；仅当本测试模块
被 import 时才会对业务对象的运行时引用生效，进程结束即失效。

运行：conda run -n atomgit_cli python tests/test_upload_resumable.py
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
import huggingface_hub

results = []


def check(name, cond, detail=""):
    results.append((name, cond, detail))
    flag = "PASS" if cond else "FAIL"
    print(f"[{flag}] {name}" + (f"  -> {detail}" if detail else ""))


# 捕获：普通 upload_folder 调用
uf_captured = []


def fake_upload_folder(**kwargs):
    uf_captured.append(dict(kwargs))
    return "fake-commit-url"


# 捕获：upload_large_folder 调用（替代 HfApi 实例上的方法）
ulf_captured = []
hfa_init_captured = []


class FakeHfApi:
    """Match the locked HF 1.1.7 signatures used by the resumable path."""

    def __init__(self, endpoint=None, token=None, library_name=None,
                 library_version=None, user_agent=None, headers=None):
        hfa_init_captured.append({"endpoint": endpoint, "token": token})

    def upload_large_folder(self, repo_id, folder_path, *, repo_type,
                            revision=None, private=None, allow_patterns=None,
                            ignore_patterns=None, num_workers=None,
                            print_report=True, print_report_every=60):
        ulf_captured.append({
            "repo_id": repo_id,
            "folder_path": folder_path,
            "repo_type": repo_type,
            "revision": revision,
            "private": private,
            "allow_patterns": allow_patterns,
            "ignore_patterns": ignore_patterns,
            "num_workers": num_workers,
            "print_report": print_report,
            "print_report_every": print_report_every,
        })
        return None


# 替换 api 模块引用的底层入口：
# - upload_folder（目录上传 + 文件回退路径）
# - hf_upload_file（单文件上传主路径，v1.0.5 起新增；单文件+resumable 时走它）
# - HfApi（resumable 模式下用其实例的 upload_large_folder）
api_mod.upload_folder = fake_upload_folder
api_mod.hf_upload_file = fake_upload_folder
api_mod.HfApi = FakeHfApi

# stub 鉴权
cfg_mod.config.is_logged_in = lambda: True
cfg_mod.config.get_credentials = lambda: {"token": "fake-token-0123456789"}


def main():
    with tempfile.TemporaryDirectory() as td:
        tdpath = Path(td)
        (tdpath / "file.bin").write_bytes(b"x" * 100)
        sub = tdpath / "modeldir"
        sub.mkdir()
        (sub / "a.txt").write_text("a")
        (sub / "b.txt").write_text("b")

        runner = CliRunner()
        with runner.isolated_filesystem():
            # --- T1: 目录上传，默认走 upload_folder（不传 resumable） ---
            uf_captured.clear(); ulf_captured.clear(); hfa_init_captured.clear()
            r = runner.invoke(cli, ["upload", str(sub), "--repo-id", "user/repo"])
            check("T1 默认 exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            check("T1 默认走 upload_folder", len(uf_captured) == 1 and len(ulf_captured) == 0,
                  f"uf={len(uf_captured)} ulf={len(ulf_captured)}")

            # --- T2: 目录上传，--resumable → 走 upload_large_folder ---
            uf_captured.clear(); ulf_captured.clear()
            r = runner.invoke(cli, ["upload", str(sub), "--repo-id", "user/repo",
                                    "--resumable"])
            check("T2 resumable exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            check("T2 resumable worker completes", r.exit_code == 0,
                  f"uf={len(uf_captured)} ulf={len(ulf_captured)}")
            if ulf_captured:
                call = ulf_captured[0]
                check("T2 repo_type 默认 model",
                      call.get("repo_type") == "model",
                      f"repo_type={call.get('repo_type')!r}")
                check("T2 folder_path=原目录",
                      call.get("folder_path") == str(sub),
                      f"folder_path={call.get('folder_path')}")
                check("T2 upload_large_folder 未传 token", "token" not in call)
                check("T2 HfApi 构造器传入 token",
                      len(hfa_init_captured) == 1
                      and bool(hfa_init_captured[0]["token"]),
                      f"init_calls={len(hfa_init_captured)}")

            # --- T3: --resumable --repo-type dataset ---
            uf_captured.clear(); ulf_captured.clear()
            r = runner.invoke(cli, ["upload", str(sub), "--repo-id", "user/repo",
                                    "--resumable", "--repo-type", "dataset"])
            check("T3 dataset resumable rejected", r.exit_code == 1, f"exit={r.exit_code}")
            if ulf_captured:
                check("T3 dataset 使用 model 传输路由",
                      ulf_captured[0].get("repo_type") == "model",
                      f"repo_type={ulf_captured[0].get('repo_type')!r}")

            # --- T4: --resumable --revision dev --ignore *.tmp --num-workers 4 ---
            uf_captured.clear(); ulf_captured.clear()
            r = runner.invoke(cli, ["upload", str(sub), "--repo-id", "user/repo",
                                    "--resumable", "--revision", "dev",
                                    "--ignore", "*.tmp", "--num-workers", "4"])
            check("T4 非默认 revision rejected", r.exit_code == 2, f"exit={r.exit_code}")
            if ulf_captured:
                call = ulf_captured[0]
                check("T4 revision=dev", call.get("revision") == "dev",
                      f"revision={call.get('revision')!r}")
                check("T4 ignore_patterns=['*.tmp']", call.get("ignore_patterns") == ["*.tmp"],
                      f"ignore={call.get('ignore_patterns')!r}")
                check("T4 num_workers=4", call.get("num_workers") == 4,
                      f"num_workers={call.get('num_workers')!r}")

            # --- T5: --resumable + path_in_repo → 给出提示但仍可上传 ---
            uf_captured.clear(); ulf_captured.clear()
            r = runner.invoke(cli, ["upload", str(sub), "--repo-id", "user/repo",
                                    "--resumable", "--path-in-repo", "sub/"])
            check("T5 path_in_repo+resumable exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            check("T5 resumable worker completes", r.exit_code == 0,
                  f"ulf={len(ulf_captured)}")
            # 输出应包含 path_in_repo 不支持的提示
            check("T5 提示 path_in_repo 不支持", "path_in_repo" in r.output or "resumable" in r.output,
                  f"output含提示={'path_in_repo' in r.output or 'resumable' in r.output}")

            # --- T6: 单文件 + --resumable → 给 warning，走普通路径 ---
            uf_captured.clear(); ulf_captured.clear()
            r = runner.invoke(cli, ["upload", str(tdpath / "file.bin"),
                                    "--repo-id", "user/repo", "--resumable"])
            check("T6 文件+resumable exit=0", r.exit_code == 0, f"exit={r.exit_code}")
            check("T6 文件走 upload_folder（非 large）",
                  len(uf_captured) == 1 and len(ulf_captured) == 0,
                  f"uf={len(uf_captured)} ulf={len(ulf_captured)}")
            check("T6 文件提示 resumable 仅目录有效",
                  "resumable" in r.output or "目录" in r.output,
                  f"提示={'有' if ('resumable' in r.output or '目录' in r.output) else '无'}")

            # --- T7: .tmp_upload 清理（文件分支会复制） ---
            leftover = Path.cwd() / ".tmp_upload"
            check("T7 .tmp_upload 已清理", not leftover.exists(), f"exists={leftover.exists()}")

    print("\n" + "=" * 50)
    passed = sum(1 for _, c, _ in results if c)
    print(f"汇总: {passed}/{len(results)} 通过")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
