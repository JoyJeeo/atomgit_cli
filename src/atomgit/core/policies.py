"""Shared input and credential policies with no network dependencies."""

from typing import Optional, Union

from .errors import AtomGitAuthenticationError, AtomGitUnsupportedError


def normalize_repo_id(repo_id: str) -> str:
    if not isinstance(repo_id, str) or not repo_id.strip():
        raise ValueError("repo_id 不能为空")
    value = repo_id.strip().strip("/")
    parts = value.split("/")
    if len(parts) < 2 or any(not part or part in (".", "..") for part in parts):
        raise ValueError("repo_id 必须是 owner/repository")
    if any(character in value for character in ("\\", "\x00")):
        raise ValueError("repo_id 包含不支持的字符")
    return "/".join(part.strip() for part in parts)


def normalize_repo_type(repo_type: Optional[str]) -> str:
    value = "model" if repo_type in (None, "") else str(repo_type).strip().lower()
    if value not in {"model", "dataset"}:
        raise ValueError("repo_type 仅支持 model 或 dataset")
    return value


def normalize_revision(revision: Optional[str]) -> str:
    value = "main" if revision in (None, "") else str(revision).strip()
    if not value or any(character in value for character in ("\\", "\x00")):
        raise ValueError("revision 名称不合法")
    return value


def resolve_token(
    explicit: Optional[Union[str, bool]],
    saved: Optional[str],
    *,
    write: bool,
) -> Optional[str]:
    """Apply the one shared token-priority policy.

    An explicit non-empty token wins; ``False`` explicitly requests anonymous
    access; otherwise a saved token is used.  Writes fail closed without a
    credential, while reads may remain anonymous.
    """

    if isinstance(explicit, str) and explicit:
        return explicit
    if explicit is False:
        selected = None
    else:
        selected = saved or None
    if write and not selected:
        raise AtomGitAuthenticationError("该操作需要认证 token；请先登录或提供 token")
    return selected


def require_private_visibility(private: bool) -> None:
    if private is not True:
        raise AtomGitUnsupportedError(
            "AtomGit 当前无法可靠验证公开仓库语义；请设置 private=True"
        )
