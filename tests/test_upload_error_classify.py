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
import errno
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
    case("U2 403 文本 → 权限不足",
         Exception("403 Client Error. Forbidden."),
         "权限不足")

    # --- 仓库不存在 ---
    if _HF_ERR_OK:
        case("U3 RepositoryNotFoundError → 仓库不存在",
             _make_err(RepositoryNotFoundError, "404. Repository Not Found for url ...", 404),
             "仓库不存在")
    case("U4 'Repository Not Found' 文本 → 仓库不存在",
         Exception("Repository Not Found for url: https://hub.atomgit.com/..."),
         "仓库不存在")

    # --- 上传预检 404（HF 1.1.7 对不存在/不可访问仓库返回 preupload 404）---
    case("U21 preupload 404 → 仓库不存在",
         Exception("Client error '404 Not Found' for url "
                   "'https://hub.atomgit.com/api/models/user/repo/preupload/main'"),
         "仓库不存在")
    et, hint = classify(
        Exception("Client error '404 Not Found' for url "
                  "'https://hub.atomgit.com/api/models/user/repo/preupload/main'"),
        repo_id="user/repo",
    )
    check("U22 preupload 404 hint 提示先建仓", "repo create" in hint, f"hint='{hint}'")
    check("U23 preupload 404 hint 不回显远端 URL", "hub.atomgit.com" not in hint, f"hint='{hint}'")

    # --- HF 401 仓库不存在文案（含 gated 通用词，不得误判为受限仓库）---
    case("U24 401+Repository Not Found → 仓库不存在（非受限仓库）",
         Exception("401 Client Error.\nRepository Not Found for url: https://hub.atomgit.com/api/models/user/repo/preupload/main.\nPlease make sure you specified the correct `repo_id` and `repo_type`.\nIf you are trying to access a private or gated repo, make sure you are authenticated. For more details, see https://huggingface.co/docs/huggingface_hub/authentication\nNote: Creating a commit assumes that the repo already exists on the Huggingface Hub. Please use `create_repo` if it's not the case."),
         "仓库不存在")
    et, hint = classify(
        Exception("401 Client Error.\nRepository Not Found for url: https://hub.atomgit.com/api/models/user/repo/preupload/main.\nPlease make sure you specified the correct `repo_id` and `repo_type`.\nIf you are trying to access a private or gated repo, make sure you are authenticated. For more details, see https://huggingface.co/docs/huggingface_hub/authentication\nNote: Creating a commit assumes that the repo already exists on the Huggingface Hub. Please use `create_repo` if it's not the case."),
        repo_id="user/repo",
    )
    check("U25 401 文案含 gated 通用词但非受限仓库", "受限仓库" not in et and "repo create" in hint, f"type='{et}' hint='{hint}'")

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
    case("U10b V5 分支校验失败 → 分支不存在",
         api_mod.ResumableTargetRevisionError("target revision does not exist"),
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

    structured_cases = [
        ("authentication", "认证失败"),
        ("permission", "权限不足"),
        ("repository", "仓库不存在"),
        ("revision", "分支"),
        ("payload_size", "提交过大"),
        ("rate_limit", "请求限流"),
        ("service_unavailable", "服务暂不可用"),
        ("timeout", "请求超时"),
        ("connection", "网络连接失败"),
        ("upload_mode", "上传模式不安全"),
        ("client_resource", "客户端资源不足"),
    ]
    for category, expected in structured_cases:
        case(
            f"structured {category} 保留分类",
            api_mod.ResumableWorkerError(category),
            expected,
        )
    structured_type, structured_hint = classify(
        api_mod.ResumableWorkerError("upload_mode"), repo_id="user/repo"
    )
    check("上传模式错误提示 .gitattributes LFS",
          ".gitattributes" in structured_hint and "LFS" in structured_hint)
    check("结构化子进程错误不包含原始响应或路径",
          "http" not in str(api_mod.ResumableWorkerError("unknown")).lower()
          and "/" not in str(api_mod.ResumableWorkerError("unknown")))
    resource_envelope = api_mod._resumable_failure_envelope(
        OSError(errno.ENOSPC, "disk full", "/private/source/model.bag")
    )
    check("本地资源错误只传递受限类别",
          resource_envelope == {"category": "client_resource"})
    permission_envelope = api_mod._resumable_failure_envelope(
        PermissionError(errno.EACCES, "permission denied", "/private/source")
    )
    check("本地文件权限错误归为客户端资源",
          permission_envelope == {"category": "client_resource"})
    check("受限错误载荷不包含完整路径",
          "/private/source/model.bag" not in repr(resource_envelope))

    commit_revision = "a" * 40
    pointer_cause = api_mod.CanonicalLfsPointerError(
        "pointer failure with fake-secret-response"
    )
    unconfirmed_error = None
    try:
        raise api_mod.CanonicalLfsCommitUnconfirmedError._for_confirmation_failure(
            commit_revision,
            "connection_failed",
        ) from pointer_cause
    except api_mod.CanonicalLfsCommitUnconfirmedError as error:
        unconfirmed_error = error
    unconfirmed_envelope = api_mod._resumable_failure_envelope(unconfirmed_error)
    unconfirmed_worker = api_mod.ResumableWorkerError(
        unconfirmed_envelope["category"],
        commit_revision=unconfirmed_envelope["commit_revision"],
        confirmation_failure=unconfirmed_envelope["confirmation_failure"],
    )
    unconfirmed_type, unconfirmed_hint = classify(unconfirmed_worker)
    check(
        "已创建未确认状态安全穿过 worker envelope",
        unconfirmed_envelope
        == {
            "category": "remote_commit_unconfirmed",
            "commit_revision": commit_revision,
            "confirmation_failure": "connection_failed",
        }
        and unconfirmed_worker.remote_commit_status == "created"
        and unconfirmed_worker.local_confirmation_status == "unconfirmed"
        and unconfirmed_worker.commit_revision == commit_revision,
    )
    check(
        "已创建未确认状态有独立 CLI 分类且不打印 revision",
        unconfirmed_type == "远端提交已创建但未确认"
        and "远端提交状态：已创建" in unconfirmed_hint
        and "本地确认状态：失败" in unconfirmed_hint
        and "无法连接确认接口" in unconfirmed_hint
        and commit_revision not in unconfirmed_hint
        and "fake-secret-response" not in unconfirmed_hint,
    )
    tampered_worker = api_mod.ResumableWorkerError(
        "remote_commit_unconfirmed",
        commit_revision=commit_revision,
        confirmation_failure="unsafe-reason",
    )
    check(
        "非法确认原因降级且保留已创建未确认状态",
        tampered_worker.category == "remote_commit_unconfirmed"
        and tampered_worker.confirmation_failure == "unknown_read_failure"
        and tampered_worker.commit_revision == commit_revision,
    )
    unhashable_worker = api_mod.ResumableWorkerError(
        "remote_commit_unconfirmed",
        commit_revision=commit_revision,
        confirmation_failure=["unsafe-reason"],
    )
    unhashable_error = (
        api_mod.CanonicalLfsCommitUnconfirmedError._for_confirmation_failure(
            commit_revision,
            "connection_failed",
        )
    )
    unhashable_error.confirmation_failure = ["unsafe-reason"]
    unhashable_envelope = api_mod._resumable_failure_envelope(unhashable_error)
    unhashable_type, unhashable_hint = classify(unhashable_error)
    check(
        "不可哈希确认原因安全降级且不破坏状态或 CLI 分类",
        unhashable_worker.category == "remote_commit_unconfirmed"
        and unhashable_worker.confirmation_failure == "unknown_read_failure"
        and unhashable_envelope["confirmation_failure"] == "unknown_read_failure"
        and unhashable_type == "远端提交已创建但未确认"
        and "未知错误" in unhashable_hint,
    )
    confirmation_hints = (
        ("authentication_failed", "重新登录"),
        ("permission_denied", "仓库权限"),
        ("pointer_unavailable", "不能证明远端提交不存在"),
        ("rate_limited", "限流"),
        ("service_unavailable", "暂时不可用"),
        ("request_timeout", "读取 pointer 超时"),
        ("connection_failed", "检查网络"),
        ("request_rejected", "服务拒绝"),
        ("response_too_large", "异常过大"),
        ("response_malformed", "格式异常"),
        ("content_mismatch", "内容与本次上传预期不一致"),
        ("unknown_read_failure", "未知错误"),
    )
    for reason, expected_hint in confirmation_hints:
        reason_error = (
            api_mod.CanonicalLfsCommitUnconfirmedError._for_confirmation_failure(
                commit_revision,
                reason,
            )
        )
        reason_envelope = api_mod._resumable_failure_envelope(reason_error)
        reason_worker = api_mod.ResumableWorkerError(
            reason_envelope["category"],
            commit_revision=reason_envelope["commit_revision"],
            confirmation_failure=reason_envelope["confirmation_failure"],
        )
        reason_type, reason_hint = classify(reason_worker)
        check(
            f"确认失败原因 {reason} 安全穿过 worker 并生成建议",
            reason_envelope["confirmation_failure"] == reason
            and reason_worker.confirmation_failure == reason
            and reason_type == "远端提交已创建但未确认"
            and expected_hint in reason_hint
            and commit_revision not in reason_hint
            and "http" not in reason_hint.lower()
            and "fake-secret" not in reason_hint,
        )

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
