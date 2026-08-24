"""Repository orchestration and post-write verification."""

from typing import Any, Dict, List

from ..core.contracts import OperationResult, RepositoryRequest
from ..core.policies import resolve_token
from ..core.ports import RepositoryPort
from ..domain.repositories import (
    require_supported_branch,
    validate_repository_request,
    validate_visibility,
)


class RepositoryUseCase:
    def __init__(self, repository: RepositoryPort):
        self.repository = repository

    def create(
        self, request: RepositoryRequest, saved_token: str = None
    ) -> OperationResult[Any]:
        request = validate_repository_request(request)
        token = resolve_token(request.token, saved_token, write=True)
        private = request.visibility is None or request.visibility.value == "private"
        value = self.repository.create(
            request.repo_id, request.repo_type, private, request.exist_ok, token
        )
        return OperationResult(
            "create_repository", True, value=value, repo_id=request.repo_id
        )

    def list(self, token: str) -> OperationResult[List[Dict[str, Any]]]:
        token = resolve_token(token, None, write=True)
        value = self.repository.list(token)
        return OperationResult("list_repositories", True, value=value)

    def set_visibility(
        self, repo_id: str, private: bool, token: str
    ) -> OperationResult[bool]:
        repo_id = validate_repository_request(RepositoryRequest(repo_id)).repo_id
        validate_visibility(private)
        token = resolve_token(token, None, write=True)
        value = self.repository.set_visibility(repo_id, private, token)
        return OperationResult(
            "set_visibility", bool(value), value=bool(value), repo_id=repo_id
        )

    def create_branch(
        self, repo_id: str, branch: str, source: str, token: str
    ) -> OperationResult[bool]:
        repo_id = validate_repository_request(RepositoryRequest(repo_id)).repo_id
        branch = require_supported_branch(branch)
        token = resolve_token(token, None, write=True)
        value = self.repository.create_branch(repo_id, branch, source or "main", token)
        return OperationResult(
            "create_branch",
            bool(value),
            value=bool(value),
            repo_id=repo_id,
            revision=branch,
        )

    def delete(
        self, repo_id: str, confirmation: str, token: str
    ) -> OperationResult[bool]:
        repo_id = validate_repository_request(RepositoryRequest(repo_id)).repo_id
        if confirmation != repo_id:
            raise ValueError("confirmation must exactly match repo_id")
        token = resolve_token(token, None, write=True)
        value = self.repository.delete(repo_id, confirmation, token)
        return OperationResult(
            "delete_repository", bool(value), value=bool(value), repo_id=repo_id
        )
