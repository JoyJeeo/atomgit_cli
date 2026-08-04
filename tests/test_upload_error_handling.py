#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atomgit upload 错误处理端到端集成测试（不触碰真实远程仓库）。

验证 ``api.upload_folder`` / ``api.upload_directory`` 在底层 HF 抛异常时，
是否走 ``_classify_upload_error`` 给出语义化错误类型 + 可执行建议，而非
旧的笼统 "上传文件失败: <e>"。

策略：让桩 HF 上传入口抛出特定异常，检查 CLI/方法输出与返回值。
沿用既有测试约定：打桩全部位于 tests/ 内，不修改业务源码；仅当本测试
模块被 import 时对业务对象运行时引用生效，进程结束即失效。

运行：conda run -n atomgit_cli python tests/test_upload_error_handling.py
"""
import sys
import tempfile
from pathlib import Path

import atomgit  # noqa: F401
api_mod = sys.modules["atomgit.api"]
cfg_mod = sys.modules["atomgit.config"]

results = []


def check(name, cond, detail=""):
    results.append((name, cond, detail))
    flag = "PASS" if cond else "FAIL"
    print(f"[{flag}] {name}" + (f"  -> {detail}" if detail else ""))


# stub 鉴权
cfg_mod.config.is_logged_in = lambda: True
cfg_mod.config.get_credentials = lambda: {"token": "fake-token-0123456789"}


def make_raising(exc):
    def _f(**kwargs):
        raise exc
    return _f


def run_case(name, exc, expect_type_kw, expect_hint_kw, target="file"):
    """target: 'file' 走 upload_folder 单文件路径；'dir' 走 upload_directory。"""
    import contextlib
    import io
    # 桩两个入口，确保目标方法会调用到并抛异常
    api_mod.hf_upload_file = make_raising(exc)
    api_mod.upload_folder = make_raising(exc)
    output = io.StringIO()
    with tempfile.TemporaryDirectory() as td:
        tdpath = Path(td)
        if target == "file":
            fp = tdpath / "a.bin"
            fp.write_bytes(b"x" * 10)
            with contextlib.redirect_stdout(output):
                ok = api_mod.api.upload_folder(fp, "user/repo")
        else:
            dp = tdpath / "d"
            dp.mkdir()
            (dp / "a.txt").write_text("a")
            with contextlib.redirect_stdout(output):
                ok = api_mod.api.upload_directory(dp, "user/repo")
    text = output.getvalue()
    check(f"{name} 返回False", ok is False, f"ok={ok}")
    check(f"{name} 输出含错误类型", expect_type_kw in text, f"found={expect_type_kw in text}")
    check(f"{name} 输出含建议", expect_hint_kw in text, f"found={expect_hint_kw in text}")


def main():
    # --- 1. 仓库不存在 ---
    try:
        from huggingface_hub.errors import RepositoryNotFoundError
        import httpx
        resp = httpx.Response(404, request=httpx.Request("GET", "https://x"))
        exc_rnf = RepositoryNotFoundError("Repository Not Found", response=resp)
    except Exception:
        exc_rnf = Exception("404 Client Error. Repository Not Found for url ...")
    run_case("E1 文件-仓库不存在", exc_rnf, "仓库不存在", "repo_id")

    # --- 2. 认证失败 ---
    exc_401 = Exception("401 Client Error. Unauthorized. Invalid username or password.")
    run_case("E2 文件-认证失败", exc_401, "认证失败", "login")

    # --- 3. 超时 ---
    exc_timeout = TimeoutError("Connection timed out after 300s")
    run_case("E3 目录-请求超时", exc_timeout, "请求超时", "timeout", target="dir")

    # --- 4. 网络连接失败 ---
    exc_conn = ConnectionError("Failed to establish a connection")
    run_case("E4 目录-网络连接失败", exc_conn, "网络连接失败", "网络", target="dir")

    # --- 5. 仓库已禁用（含403，验证优先级） ---
    try:
        from huggingface_hub.errors import DisabledRepoError
        import httpx
        resp = httpx.Response(403, request=httpx.Request("GET", "https://x"))
        exc_disabled = DisabledRepoError("403. repo disabled.", response=resp)
    except Exception:
        exc_disabled = Exception("This repo is disabled by the author.")
    run_case("E5 文件-仓库已禁用", exc_disabled, "仓库已禁用", "禁用")

    # --- 6. 未知错误 ---
    exc_unknown = RuntimeError("totally unexpected boom")
    run_case("E6 目录-未知错误", exc_unknown, "未知错误", "", target="dir")

    # --- 7. 上传预检 404（HF 1.1.7 对不存在仓库返回 preupload 404）---
    exc_preupload = Exception(
        "Client error '404 Not Found' for url "
        "'https://hub.atomgit.com/api/models/weixin_52273949/test_model/preupload/main'"
    )
    run_case("E7 文件-preupload 404 仓库不存在", exc_preupload, "仓库不存在", "repo create")

    print("\n" + "=" * 50)
    passed = sum(1 for _, c, _ in results if c)
    print(f"汇总: {passed}/{len(results)} 通过")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
