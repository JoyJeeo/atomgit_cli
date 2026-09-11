"""Credential-safe upload and resumable failure policy."""

import errno
import socket
from typing import Optional

import httpx

from ...infrastructure.validation import auth_error_kind
from .projection import ResumableProjectionError

# Program-step 9 LFS exception and validation slots are wired by atomgit.api.
CanonicalLfsCommitUnconfirmedError = None
CanonicalLfsPointerError = None
ResumableUploadModeError = None
ResumableLfsAttributesError = None
ResumableLfsPreuploadError = None
_validated_lfs_patterns = None


class ResumableTargetRevisionError(RuntimeError):
    """A requested resumable upload revision does not exist."""


_RESUMABLE_WORKER_ERROR_MESSAGES = {
    "authentication": "resumable worker authentication failed",
    "permission": "resumable worker permission check failed",
    "repository": "resumable worker repository check failed",
    "revision": "resumable worker revision check failed",
    "request": "resumable worker request validation failed",
    "payload_size": "resumable worker payload is too large",
    "lfs_quota": "resumable worker LFS storage is insufficient",
    "lfs_bandwidth": "resumable worker LFS bandwidth is insufficient",
    "lfs_batch_rejected": "resumable worker LFS batch was rejected",
    "rate_limit": "resumable worker was rate limited",
    "service_unavailable": "resumable worker service is unavailable",
    "timeout": "resumable worker timed out",
    "connection": "resumable worker connection failed",
    "upload_mode": "resumable worker upload mode is unsafe",
    "lfs_attributes": "resumable worker LFS attributes need verification",
    "lfs_pointer": "resumable worker LFS pointer verification failed",
    "remote_commit_unconfirmed": "remote commit was created but remains unconfirmed",
    "client_resource": "resumable worker client resources are insufficient",
    "unknown": "resumable worker failed",
}

_LFS_CONFIRMATION_FAILURE_HINTS = {
    "authentication_failed": "确认请求的登录凭证无效，请重新登录并先核对远端状态。",
    "permission_denied": "当前账号无权读取 pointer，请检查仓库权限并先核对远端状态。",
    "pointer_unavailable": (
        "未找到对应 pointer，这不能证明远端提交不存在，请先核对远端状态。"
    ),
    "rate_limited": "pointer 确认请求受到限流，请稍后核对远端状态。",
    "service_unavailable": "pointer 确认服务暂时不可用，请稍后核对远端状态。",
    "request_timeout": "读取 pointer 超时，请检查网络并先核对远端状态。",
    "connection_failed": "无法连接确认接口，请检查网络并先核对远端状态。",
    "request_rejected": "确认请求被服务拒绝，请核对仓库状态或联系平台支持。",
    "response_too_large": (
        "确认接口返回数据异常过大，未能读取 pointer，请联系平台支持。"
    ),
    "response_malformed": ("确认接口返回格式异常，未能解析 pointer，请联系平台支持。"),
    "content_mismatch": (
        "pointer 内容与本次上传预期不一致，请联系平台支持检查该提交。"
    ),
    "unknown_read_failure": "读取 pointer 时发生未知错误，请先核对远端状态。",
}


def _lfs_confirmation_failure_hint(error: BaseException) -> str:
    reason = getattr(error, "confirmation_failure", None)
    if not isinstance(reason, str):
        reason = "unknown_read_failure"
    return _LFS_CONFIRMATION_FAILURE_HINTS.get(
        reason,
        _LFS_CONFIRMATION_FAILURE_HINTS["unknown_read_failure"],
    )


class ResumableWorkerError(RuntimeError):
    """A credential-safe failure reconstructed from the upload child."""

    def __init__(
        self,
        category: str,
        lfs_patterns=(),
        *,
        commit_revision=None,
        confirmation_failure=None,
    ):
        if category not in _RESUMABLE_WORKER_ERROR_MESSAGES:
            category = "unknown"
        state = None
        if category == "remote_commit_unconfirmed":
            if not isinstance(CanonicalLfsCommitUnconfirmedError, type):
                category = "unknown"
            else:
                try:
                    state = (
                        CanonicalLfsCommitUnconfirmedError._for_confirmation_failure(
                            commit_revision,
                            confirmation_failure,
                        )
                    )
                except Exception:
                    category = "unknown"
        self.category = category
        self.lfs_patterns = (
            _validated_lfs_patterns(lfs_patterns)
            if category in ("upload_mode", "lfs_attributes")
            else ()
        )
        if state is not None:
            self.remote_commit_status = state.remote_commit_status
            self.local_confirmation_status = state.local_confirmation_status
            self.commit_revision = state.commit_revision
            self.confirmation_failure = state.confirmation_failure
        super().__init__(_RESUMABLE_WORKER_ERROR_MESSAGES[category])


class ResumableCommitError(RuntimeError):
    """A resumable commit could not complete under the bounded retry policy."""


def _resumable_error_chain(error: BaseException):
    """Yield a bounded exception chain without serializing exception text."""
    current = error
    seen = set()
    for _ in range(8):
        if not isinstance(current, BaseException) or id(current) in seen:
            return
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def _resumable_error_status(error: BaseException) -> Optional[int]:
    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)
    if isinstance(status_code, int):
        return status_code
    code = getattr(error, "code", None)
    return code if isinstance(code, int) else None


def _resumable_worker_error_category(error: BaseException) -> str:
    """Reduce an arbitrary child failure to one bounded, non-sensitive code."""
    for cause in _resumable_error_chain(error):
        if isinstance(cause, ResumableWorkerError):
            return cause.category
        if isinstance(cause, ResumableUploadModeError):
            return "upload_mode"
        if isinstance(cause, ResumableLfsAttributesError):
            return "lfs_attributes"
        if isinstance(cause, ResumableLfsPreuploadError):
            return cause.category
        if isinstance(cause, CanonicalLfsCommitUnconfirmedError):
            return "remote_commit_unconfirmed"
        if isinstance(cause, CanonicalLfsPointerError):
            return "lfs_pointer"

        name = type(cause).__name__
        if name == "RevisionNotFoundError":
            return "revision"
        if name == "RepositoryNotFoundError":
            return "repository"
        if name in ("GatedRepoError", "DisabledRepoError"):
            return "permission"

        credential_error = auth_error_kind(cause)
        if credential_error in ("authentication", "permission"):
            return credential_error

        status_code = _resumable_error_status(cause)
        if status_code == 401:
            return "authentication"
        if status_code == 403:
            return "permission"
        if status_code == 404:
            return "repository"
        if status_code == 413:
            return "payload_size"
        if status_code == 429:
            return "rate_limit"
        if status_code in (500, 502, 503, 504):
            return "service_unavailable"
        if status_code == 400 or name == "BadRequestError":
            return "request"

        if isinstance(
            cause,
            (httpx.TimeoutException, TimeoutError, socket.timeout),
        ):
            return "timeout"
        if isinstance(
            cause,
            (httpx.NetworkError, ConnectionError),
        ):
            return "connection"
        if isinstance(cause, MemoryError):
            return "client_resource"
        if isinstance(cause, OSError) and cause.errno in (
            errno.EACCES,
            errno.EPERM,
            errno.EFBIG,
            errno.EMFILE,
            errno.ENFILE,
            errno.ENOMEM,
            errno.ENOSPC,
            errno.EROFS,
        ):
            return "client_resource"
    return "unknown"


def _resumable_failure_envelope(error: BaseException) -> dict:
    """Build the only error payload allowed across the process boundary."""
    category = _resumable_worker_error_category(error)
    envelope = {"category": category}
    if category == "remote_commit_unconfirmed":
        for cause in _resumable_error_chain(error):
            if isinstance(cause, CanonicalLfsCommitUnconfirmedError):
                envelope["commit_revision"] = cause.commit_revision
                reason = cause.confirmation_failure
                envelope["confirmation_failure"] = (
                    reason
                    if isinstance(reason, str)
                    and reason in _LFS_CONFIRMATION_FAILURE_HINTS
                    else "unknown_read_failure"
                )
                break
    if category in ("upload_mode", "lfs_attributes"):
        for cause in _resumable_error_chain(error):
            patterns = _validated_lfs_patterns(getattr(cause, "lfs_patterns", ()))
            if patterns:
                envelope["lfs_patterns"] = list(patterns)
                break
    return envelope


def _classify_upload_error(e: Exception, repo_id: str = None) -> tuple:
    """把 HF Hub 上传异常归类为 (error_type, hint) 二元组，供上层给出语义化提示。

    覆盖以下典型情形（基于 huggingface_hub 错误类型与文本特征）：
      - 认证失败 (401/403, 无有效 token)
      - 仓库不存在 (RepositoryNotFoundError)
      - 仓库已禁用 (DisabledRepoError)
      - 分支不存在 (RevisionNotFoundError)
      - 请求参数错误 (BadRequestError / 400)
      - 超时 / 网络连接 (timeout / connection)
      - 其他未知错误

    返回 (error_type, hint)，其中 hint 是给用户的可执行建议。
    """
    if isinstance(e, ResumableWorkerError):
        structured_errors = {
            "authentication": (
                "认证失败",
                "登录凭证无效或已过期。请使用 'atomgit login' 重新登录后重试。",
            ),
            "permission": (
                "权限不足",
                "当前登录凭证无权上传到目标仓库。请检查仓库权限或目标命名空间。",
            ),
            "repository": (
                "仓库不存在",
                f"目标仓库 {repo_id or ''} 不存在或不可访问。请先使用 "
                "'atomgit repo create' 创建仓库，或检查 repo_id / repo_type。",
            ),
            "revision": (
                "分支/版本不存在",
                "目标分支不存在且无法自动创建。请检查 revision 是否正确。",
            ),
            "request": (
                "请求参数错误",
                "请求参数不合法。请检查 repo_id、repo_type、path_in_repo 等参数。",
            ),
            "payload_size": (
                "提交过大",
                "提交已降至单文件仍超过服务端限制；断点状态已保留，请联系平台支持。",
            ),
            "lfs_quota": (
                "LFS 存储空间不足",
                "请增加仓库或账号的 LFS 配额，或删除无用对象并完成服务端 LFS GC；"
                "断点状态已保留，释放空间后可重新执行同一命令。",
            ),
            "lfs_bandwidth": (
                "LFS 带宽额度不足",
                "请等待带宽额度重置或联系平台支持；断点状态已保留，"
                "条件恢复后可重新执行同一命令。",
            ),
            "lfs_batch_rejected": (
                "LFS 协商请求被拒绝",
                "Git LFS Batch 请求被服务端拒绝；断点状态已保留，"
                "请在平台支持解决后重新执行同一命令。",
            ),
            "rate_limit": (
                "请求限流",
                "服务端持续限流，上传已停止且断点状态已保留；请稍后重新执行同一命令。",
            ),
            "service_unavailable": (
                "服务暂不可用",
                "服务端暂时不可用，上传断点状态已保留；请稍后重新执行同一命令。",
            ),
            "timeout": (
                "请求超时",
                "请求超时。可使用 -t/--timeout 增大超时时间后重试。",
            ),
            "connection": (
                "网络连接失败",
                "无法连接到服务器。请检查网络或代理设置后重试。",
            ),
            "upload_mode": (
                "上传模式不安全",
                "服务端将超大文件判定为 regular；请在仓库 .gitattributes "
                "中为该文件类型配置 Git LFS 后重试；如允许 CLI 提交该配置，"
                "可加 --auto-configure-lfs 重新执行同一命令。断点状态已保留。",
            ),
            "lfs_pointer": (
                "LFS 指针验证失败",
                "AtomGit 服务生成的 Git LFS pointer 不符合规范或无法按原始 "
                "Git blob 确认；本次上传未确认成功，请保留断点并联系平台支持。",
            ),
            "remote_commit_unconfirmed": (
                "远端提交已创建但未确认",
                "远端提交状态：已创建；本地确认状态：失败。"
                "请先确认远端状态再决定是否重试，断点状态已保留。",
            ),
            "client_resource": (
                "客户端资源不足",
                "本机内存、磁盘空间或文件句柄不足；释放资源后重新执行同一命令。",
            ),
            "unknown": (
                "未知错误",
                "上传子进程失败且未能安全识别原因；断点状态已保留，请稍后重试。",
            ),
        }
        error_type, hint = structured_errors[e.category]
        if e.category == "remote_commit_unconfirmed":
            hint += _lfs_confirmation_failure_hint(e)
        return error_type, hint

    if isinstance(e, ResumableUploadModeError):
        return (
            "上传模式不安全",
            "服务端将超大文件判定为 regular；请在仓库 .gitattributes "
            "中为该文件类型配置 Git LFS 后重试；如允许 CLI 提交该配置，"
            "可加 --auto-configure-lfs 重新执行同一命令。断点状态已保留。",
        )

    if isinstance(e, CanonicalLfsCommitUnconfirmedError):
        return (
            "远端提交已创建但未确认",
            "远端提交状态：已创建；本地确认状态：失败。"
            + _lfs_confirmation_failure_hint(e),
        )

    if isinstance(e, CanonicalLfsPointerError):
        return (
            "LFS 指针验证失败",
            "AtomGit 服务生成的 Git LFS pointer 不符合规范或无法按原始 "
            "Git blob 确认；本次上传未确认成功，请联系平台支持。",
        )

    if isinstance(e, ResumableTargetRevisionError):
        return (
            "分支/版本不存在",
            "目标分支不存在且无法自动创建。请检查 revision 是否正确。",
        )

    msg = str(e)
    ename = type(e).__name__

    # 仓库已禁用（需放在 RepositoryNotFoundError 之前，避免被 403 误吞）
    if (
        ename == "DisabledRepoError"
        or "disabled" in msg.lower()
        and "repo" in msg.lower()
    ):
        return "仓库已禁用", "该仓库已被作者禁用，无法上传。请联系仓库所有者。"

    # 分支/版本不存在
    if (
        ename == "RevisionNotFoundError"
        or "revision" in msg.lower()
        and ("not found" in msg.lower() or "404" in msg)
    ):
        return (
            "分支/版本不存在",
            "目标分支不存在且无法自动创建。请检查 revision 是否正确。",
        )

    # 受限仓库的可靠特征。HF 401 通用文案（"If you are trying to access a
    # private or gated repo..."）也含 "gated" 一词，不能仅凭该词判定。
    gated_markers = (
        "cannot access gated repo" in msg.lower()
        or "you are not on the authorized list" in msg.lower()
        or "you are not in the authorized list" in msg.lower()
        or "repo is gated" in msg.lower()
        or "is gated" in msg.lower()
    )

    # 仓库不存在（HF 既定：404/401 或 "Repository Not Found"、"创建提交前仓库
    # 必须已存在 / 检查 repo_id 与 repo_type" 等特征；preupload 预检对不存在
    # 或不可访问的仓库返回 404/401）
    if (
        ename in ("RepositoryNotFoundError", "GatedRepoError")
        or "repository not found" in msg.lower()
        or ("404" in msg and "not found" in msg.lower())
        or "creating a commit assumes that the repo already exists" in msg.lower()
        or "please make sure you specified the correct `repo_id` and `repo_type`"
        in msg.lower()
    ):
        if ename == "GatedRepoError" or gated_markers:
            return (
                "受限仓库",
                "该仓库为受限仓库(gated)，您未在授权名单内。请在平台申请访问权限。",
            )
        if "preupload" in msg.lower():
            return (
                "仓库不存在",
                f"目标仓库 {repo_id or ''} 不存在或为私有且无访问权限。"
                "请先使用 'atomgit repo create' 创建仓库，或检查 repo_id / repo_type。",
            )
        return (
            "仓库不存在",
            f"仓库 {repo_id or ''} 不存在或为私有且无访问权限。请检查 repo_id/repo_type，或先 atomgit login。",
        )

    # 受限仓库（文本特征兜底：仅限明确的 gated 语义）
    if gated_markers:
        return (
            "受限仓库",
            "该仓库为受限仓库(gated)，您未在授权名单内。请在平台申请访问权限。",
        )

    if isinstance(e, ResumableProjectionError):
        return "本地投影失败", msg

    if "429" in msg or "too many requests" in msg.lower():
        return (
            "请求限流",
            "服务端持续限流，上传已停止且断点状态已保留；请稍后重新执行同一命令。",
        )

    if "413" in msg:
        return (
            "提交过大",
            "提交已降至单文件仍超过服务端限制；断点状态已保留，请联系平台支持。",
        )

    if any(code in msg for code in ("502", "503", "504")):
        return (
            "服务暂不可用",
            "服务端暂时不可用，上传断点状态已保留；请稍后重新执行同一命令。",
        )

    # 请求参数错误
    if ename == "BadRequestError" or "400" in msg and "client error" in msg.lower():
        return (
            "请求参数错误",
            "请求参数不合法。请检查 repo_id、repo_type、path_in_repo 等参数。",
        )

    # 认证/权限失败（且不属于上述仓库类错误）
    credential_error = auth_error_kind(e)
    if credential_error == "authentication":
        return (
            "认证失败",
            "登录凭证无效或已过期。请使用 'atomgit login' 重新登录后重试。",
        )
    if credential_error == "permission":
        return (
            "权限不足",
            "当前登录凭证无权上传到目标仓库。请检查仓库权限或目标命名空间。",
        )

    # 超时
    if (
        "timeout" in msg.lower()
        or "timed out" in msg.lower()
        or ename == "TimeoutError"
    ):
        return "请求超时", "请求超时。可使用 -t/--timeout 增大超时时间后重试。"

    # 网络连接
    if (
        "connection" in msg.lower()
        or "connectionerror" in ename.lower()
        or "resolve" in msg.lower()
    ):
        return "网络连接失败", "无法连接到服务器。请检查网络或代理设置后重试。"

    # 其他
    return "未知错误", "服务返回了未识别的错误；请稍后重试，仍失败时联系平台支持。"
