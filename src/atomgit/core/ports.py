"""Protocols for outbound integrations.

Ports are intentionally structural: tests can provide strict fakes without
importing Hugging Face or AtomGit V5 into core/domain/usecase modules.
"""

from typing import Any, Dict, List, Optional, Protocol


class AuthenticationPort(Protocol):
    def authenticate(self, token: str) -> Dict[str, Any]: ...

    def clear(self) -> None: ...

    def current_identity(self, token: str) -> Dict[str, Any]: ...


class RepositoryPort(Protocol):
    def create(
        self,
        repo_id: str,
        repo_type: str,
        private: bool,
        exist_ok: bool,
        token: str,
    ) -> Any: ...

    def list(self, token: str) -> List[Dict[str, Any]]: ...

    def set_visibility(self, repo_id: str, private: bool, token: str) -> bool: ...

    def create_branch(
        self, repo_id: str, branch: str, source: str, token: str
    ) -> bool: ...

    def delete(self, repo_id: str, confirmation: str, token: str) -> bool: ...


class TransferPort(Protocol):
    def upload_file(self, **kwargs: Any) -> Any: ...

    def upload_folder(self, **kwargs: Any) -> Any: ...

    def download_snapshot(self, **kwargs: Any) -> Any: ...

    def download_file(self, **kwargs: Any) -> Any: ...


class ConfigPort(Protocol):
    def get_credentials(self) -> Optional[Dict[str, str]]: ...

    def set_credentials(self, token: str, username: Optional[str] = None) -> None: ...

    def clear_credentials(self) -> None: ...
