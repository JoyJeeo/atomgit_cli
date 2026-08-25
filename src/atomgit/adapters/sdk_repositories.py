"""Repository creation behavior for the public Python SDK."""

from typing import Dict, List, Optional

from huggingface_hub import create_repo

from ..core.errors import (
    AtomGitAuthenticationError,
    AtomGitRepositoryExistsError,
    AtomGitUnsupportedError,
)
from .sdk_common import _atomgit_repo_type, _get_token, _normalize_repo_id
from .sdk_errors import _sdk_error


def create_repository(
    repo_id: str,
    token: Optional[str] = None,
    private: bool = False,
    repo_type: str = "model",
    exist_ok: bool = False,
    space_sdk: Optional[str] = None,
    space_hardware: Optional[str] = None,
    space_storage: Optional[str] = None,
    space_sleep_time: Optional[int] = None,
    space_secrets: Optional[List[Dict]] = None,
    space_variables: Optional[List[Dict]] = None,
) -> str:
    """Create a repository using AtomGit's verified private-only semantics."""
    normalized_repo_id = _normalize_repo_id(repo_id)
    if not private:
        raise AtomGitUnsupportedError(
            "AtomGit 当前无法可靠验证公开仓库语义；请设置 private=True"
        )
    if repo_type not in ("model", "dataset"):
        raise ValueError("repo_type 仅支持 model 或 dataset")

    space_options = {
        "space_sdk": space_sdk,
        "space_hardware": space_hardware,
        "space_storage": space_storage,
        "space_sleep_time": space_sleep_time,
        "space_secrets": space_secrets,
        "space_variables": space_variables,
    }
    unsupported_space_options = [
        name for name, value in space_options.items() if value is not None
    ]
    if unsupported_space_options:
        raise AtomGitUnsupportedError(
            "AtomGit 不支持 Space 仓库参数: " + ", ".join(unsupported_space_options)
        )

    if token is None:
        token = _get_token()
        if token is None:
            raise AtomGitAuthenticationError(
                "创建仓库需要认证 token；请先使用 'atomgit login' 登录或提供 token"
            )

    try:
        return create_repo(
            repo_id=normalized_repo_id,
            token=token,
            private=private,
            repo_type=_atomgit_repo_type(repo_type),
            exist_ok=exist_ok,
        )
    except Exception as error:
        converted = _sdk_error(error, "创建仓库", repo_id)
        if isinstance(converted, AtomGitRepositoryExistsError) and exist_ok:
            return f"https://atomgit.com/{repo_id}"
        raise converted from error
