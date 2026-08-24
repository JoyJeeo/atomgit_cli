"""Stable error hierarchy owned by the dependency-free core."""


class AtomGitError(Exception):
    """Base class for failures reported by AtomGit interfaces."""


class AtomGitAuthenticationError(AtomGitError):
    """Authentication failed or the token lacks permission."""


class AtomGitRepositoryNotFoundError(AtomGitError):
    """The requested repository or file is unavailable."""


class AtomGitRepositoryExistsError(AtomGitError):
    """Repository creation conflicts with an existing repository."""


class AtomGitRevisionNotFoundError(AtomGitError):
    """The requested revision is unavailable."""


class AtomGitTimeoutError(AtomGitError, TimeoutError):
    """An AtomGit operation exceeded its timeout."""


class AtomGitNetworkError(AtomGitError, ConnectionError):
    """An AtomGit operation failed because of network transport."""


class AtomGitUnsupportedError(AtomGitError, ValueError):
    """The requested behavior is not supported by AtomGit."""


def classify_remote_error(
    error: Exception, operation: str, repo_id=None
) -> AtomGitError:
    """Classify a remote failure without importing a concrete transport."""
    message = str(error).lower()
    target = f"：{repo_id}" if repo_id else ""
    if any(
        marker in message for marker in ("403", "401", "permission", "unauthorized")
    ):
        return AtomGitAuthenticationError(
            f"{operation}认证或权限失败{target}；请重新登录后重试"
        )
    if "revision" in message and ("404" in message or "not found" in message):
        return AtomGitRevisionNotFoundError(f"{operation}的 revision 不存在{target}")
    if "404" in message or "not found" in message:
        return AtomGitRepositoryNotFoundError(f"{operation}的仓库或文件不存在{target}")
    if "409" in message or "already exists" in message:
        return AtomGitRepositoryExistsError(f"仓库已存在{target}")
    if "timeout" in message or "timed out" in message:
        return AtomGitTimeoutError(f"{operation}超时{target}；请检查网络或增大超时")
    if "connection" in message or "network" in message:
        return AtomGitNetworkError(f"{operation}网络连接失败{target}；请稍后重试")
    return AtomGitError(f"{operation}失败{target}（{type(error).__name__}）")


__all__ = [
    "AtomGitError",
    "AtomGitAuthenticationError",
    "AtomGitNetworkError",
    "AtomGitRepositoryExistsError",
    "AtomGitRepositoryNotFoundError",
    "AtomGitRevisionNotFoundError",
    "AtomGitTimeoutError",
    "AtomGitUnsupportedError",
    "classify_remote_error",
]
