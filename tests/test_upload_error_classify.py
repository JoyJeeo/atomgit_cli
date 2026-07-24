#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atomgit upload 错误分类（_classify_upload_error）单元测试。

不调用 CLI 也不触碰远程，直接构造各类 HF Hub 异常实例，调用
``atomgit.api._classify_upload_error`` 验证其返回的 (error_type, hint)
是否语义正确。覆盖：
  - 认证失败 (401/403 文本特征)
  - 仓库不存在 (RepositoryNotFoundError / Repository Not Found 文本)
  - 受限仓库 (GatedRepoError / gated 文本)
  - 仓库已禁用 (DisabledRepoError / disabled 文本)
  - 分支/版本不存在 (RevisionNotFoundError / revision+404 文本)
  - 请求参数错误 (BadRequestError / 400)
  - 超时 (TimeoutError / timeout 文本)
  - 网络连接失败 (ConnectionError / connection 文本)
  - 未知错误兜底
  - 优先级：DisabledRepoError 在 403 文本下不被误判为认证失败

设计契约：仅做纯函数单测，不修改业务源码；进程结束即失效。

运行：conda run -n atomgit_cli python tests/test_upload_error_classify.py
"""
import sys
import atomgit  # noqa: F401  触发包初始化
api_mod = sys.modules["atomgit.api"]
classify = api_mod._classify_upload_error

# 尽量用 HF 真实异常类构造；不可用则用通用 Exception + 文本特征兜底
try:
    from huggingface_hub.errors import (
        RepositoryNotFoundError, GatedRepoError, DisabledRepoError,
        RevisionNotFoundError, BadRequestError,
    )
    _HF_ERR_OK = True
except Exception:  # 老版本无某些异常类
    _HF_ERR_OK = False
    RepositoryNotFoundError = GatedRepoError = DisabledRepoError = None
    RevisionNotFoundError = BadRequestError = None

# HF 的 HTTP 异常类构造需要 response；用 httpx 伪 response 辅助构造
try:
    import httpx as _httpx

    def _resp(status=404, url="https://hub.atomgit.com/api/models/user/repo"):
        return _httpx.Response(status, request=_httpx.Request("GET", url))
except Exception:
    _httpx = None

    def _resp(status=404, url="https://hub.atomgit.com/api/models/user/repo"):
        return None


def _make_err(cls, message, status=404):
    """构造 HF HTTP 异常实例；response 缺失时回退到普通 Exception。"""
    if cls is None:
        return Exception(message)
    try:
        return cls(message, response=_resp(status))
    except TypeError:
        # 非基于 response 的异常类（如 EntryNotFoundError），直接构造
        return cls(message)

results = []


def check(name, cond, detail=""):
    results.append((name, cond, detail))
    flag = "PASS" if cond else "FAIL"
    print(f"[{flag}] {name}" + (f"  -> {detail}" if detail else ""))


def case(name, exc, exp_type_kw, repo_id="user/repo"):
    et, hint = classify(exc, repo_id=repo_id)
    ok = exp_type_kw in et
    check(name, ok, f"got type='{et}' hint='{hint}'")


def main():
    # --- 认证失败 ---
    case("U1 401 文本 → 认证失败",
         Exception("401 Client Error. Unauthorized. Invalid username or password."),
         "认证失败")
    case("U2 403 文本 → 认证失败",
         Exception("403 Client Error. Forbidden."),
         "认证失败")

    # --- 仓库不存在 ---
    if _HF_ERR_OK:
        case("U3 RepositoryNotFoundError → 仓库不存在",
             _make_err(RepositoryNotFoundError, "404. Repository Not Found for url ...", 404),
             "仓库不存在")
    case("U4 'Repository Not Found' 文本 → 仓库不存在",
         Exception("Repository Not Found for url: https://hub.atomgit.com/..."),
         "仓库不存在")

    # --- 受限仓库 (gated) ---
    if _HF_ERR_OK:
        case("U5 GatedRepoError → 受限仓库",
             _make_err(GatedRepoError, "403. Cannot access gated repo ...", 403),
             "受限仓库")
    case("U6 'gated' 文本 → 受限仓库",
         Exception("Access is gated. You are not in the authorized list."),
         "受限仓库")

    # --- 仓库已禁用 ---
    if _HF_ERR_OK:
        case("U7 DisabledRepoError → 仓库已禁用",
             _make_err(DisabledRepoError, "Repo has been disabled.", 403),
             "仓库已禁用")
    case("U8 'disabled repo' 文本 → 仓库已禁用",
         Exception("This repo is disabled by the author."),
         "仓库已禁用")

    # --- 分支/版本不存在 ---
    if _HF_ERR_OK:
        case("U9 RevisionNotFoundError → 分支不存在",
             _make_err(RevisionNotFoundError, "404. Revision Not Found for rev 'dev'", 404),
             "分支")
    case("U10 revision+404 文本 → 分支不存在",
         Exception("404 Client Error. revision 'dev' not found"),
         "分支")

    # --- 请求参数错误 ---
    if _HF_ERR_OK:
        case("U11 BadRequestError → 请求参数错误",
             _make_err(BadRequestError, "400 Client Error. Bad request.", 400),
             "请求参数错误")
    case("U12 400 文本 → 请求参数错误",
         Exception("400 Client Error. invalid repo_id"),
         "请求参数错误")

    # --- 超时 ---
    case("U13 TimeoutError → 请求超时",
         TimeoutError("Connection timed out after 300s"),
         "请求超时")
    case("U14 'timeout' 文本 → 请求超时",
         Exception("Operation timed out."),
         "请求超时")

    # --- 网络连接失败 ---
    case("U15 ConnectionError → 网络连接失败",
         ConnectionError("Failed to establish a connection"),
         "网络连接失败")
    case("U16 'connection' 文本 → 网络连接失败",
         Exception("Could not resolve host: hub.atomgit.com"),
         "网络连接失败")

    # --- 未知错误兜底 ---
    case("U17 未知异常 → 未知错误",
         RuntimeError("something totally unexpected"),
         "未知错误")

    # --- 优先级：仓库已禁用即便含 403 也不应被误判为认证失败 ---
    # DisabledRepoError 含 403 文本时，应归到"仓库已禁用"
    if _HF_ERR_OK:
        et, _ = classify(_make_err(DisabledRepoError, "403 Client Error. repo disabled.", 403),
                         repo_id="user/repo")
        check("U18 DisabledRepoError 含403 → 仓库已禁用（不被误判为认证失败）",
              "仓库已禁用" in et, f"got type='{et}'")

    # --- hint 非空且包含可执行建议 ---
    et, hint = classify(Exception("401 Unauthorized"), repo_id="u/r")
    check("U19 hint 非空", bool(hint), f"hint='{hint}'")
    check("U20 hint 含 login 建议", "login" in hint, f"hint='{hint}'")

    print("\n" + "=" * 50)
    passed = sum(1 for _, c, _ in results if c)
    print(f"汇总: {passed}/{len(results)} 通过")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
