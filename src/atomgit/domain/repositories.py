"""Repository invariants shared by CLI and native SDK boundaries."""

from ..core.contracts import RepositoryRequest, Visibility
from ..core.policies import normalize_repo_id, normalize_repo_type, normalize_revision


def validate_visibility(private: bool) -> Visibility:
    if not isinstance(private, bool):
        raise ValueError("private 必须是布尔值")
    return Visibility.PRIVATE if private else Visibility.PUBLIC


def validate_repository_request(request: RepositoryRequest) -> RepositoryRequest:
    return RepositoryRequest(
        repo_id=normalize_repo_id(request.repo_id),
        repo_type=normalize_repo_type(request.repo_type),
        visibility=request.visibility,
        revision=normalize_revision(request.revision),
        token=request.token,
        exist_ok=bool(request.exist_ok),
    )


def require_supported_branch(branch: str) -> str:
    value = normalize_revision(branch)
    if value == "main":
        raise ValueError("branch 必须是显式的非 main 分支")
    return value
