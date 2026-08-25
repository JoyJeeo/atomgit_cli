"""Stable, credential-safe error conversion for historical SDK adapters."""

from ..adapters.lfs.pointer import CanonicalLfsPointerError
from ..core.errors import (
    AtomGitAuthenticationError,
    AtomGitError,
    AtomGitNetworkError,
    AtomGitRepositoryExistsError,
    AtomGitRepositoryNotFoundError,
    AtomGitRevisionNotFoundError,
    AtomGitTimeoutError,
    AtomGitUnsupportedError,
)
from ..infrastructure.utils import auth_error_kind, is_retryable_download_error


def _sdk_error(error: Exception, operation: str, repo_id: str = None) -> AtomGitError:
    """Classify a dependency failure without echoing remote or signed URLs."""
    name = type(error).__name__
    message = str(error).lower()
    credential_error = auth_error_kind(error)
    retryable_failure = is_retryable_download_error(error)
    if any(
        marker in message
        for marker in (
            "http://",
            "https://",
            "token",
            "secret",
            "signature",
            "certificate",
        )
    ):
        error.args = (f"{name} details redacted",)
    target = f"：{repo_id}" if repo_id else ""
    if isinstance(error, CanonicalLfsPointerError):
        return AtomGitError(
            f"{operation}的 Git LFS pointer 验证失败{target}；"
            "AtomGit 服务未返回可确认的规范原始 blob，请联系平台支持"
        )
    if credential_error == "authentication":
        return AtomGitAuthenticationError(
            f"{operation}认证失败{target}；请重新登录后重试"
        )
    if credential_error == "permission":
        return AtomGitAuthenticationError(
            f"{operation}权限不足{target}；请检查仓库或命名空间权限"
        )
    if name == "RevisionNotFoundError" or (
        "revision" in message and ("not found" in message or "404" in message)
    ):
        return AtomGitRevisionNotFoundError(f"{operation}的 revision 不存在{target}")
    if (
        "409" in message
        or "already exists" in message
        or name == "RepositoryExistsError"
    ):
        return AtomGitRepositoryExistsError(f"仓库已存在{target}")
    if name in ("RepositoryNotFoundError", "EntryNotFoundError") or (
        "404" in message or "not found" in message
    ):
        return AtomGitRepositoryNotFoundError(f"{operation}的仓库或文件不存在{target}")
    if name == "TimeoutError" or "timeout" in message or "timed out" in message:
        return AtomGitTimeoutError(f"{operation}超时{target}；请检查网络或增大超时")
    if retryable_failure:
        return AtomGitNetworkError(f"{operation}网络连接失败{target}；请稍后重试")
    if "unsupported" in message or "not supported" in message:
        return AtomGitUnsupportedError(f"AtomGit 不支持请求的{operation}行为{target}")
    return AtomGitError(f"{operation}失败{target}（{name}）")
