"""Authentication orchestration for both user-facing interfaces."""

from typing import Any, Dict

from ..core.contracts import OperationResult
from ..core.ports import AuthenticationPort, ConfigPort
from ..domain.authentication import validate_login_token


class AuthenticationUseCase:
    def __init__(self, authentication: AuthenticationPort, config: ConfigPort):
        self.authentication = authentication
        self.config = config

    def login(self, token: str) -> OperationResult[Dict[str, Any]]:
        token = validate_login_token(token)
        identity = self.authentication.authenticate(token)
        self.config.set_credentials(token, username=identity.get("login"))
        return OperationResult("login", True, value=identity)

    def logout(self) -> OperationResult[bool]:
        self.config.clear_credentials()
        return OperationResult("logout", True, value=True)

    def whoami(self, token: str) -> OperationResult[Dict[str, Any]]:
        identity = self.authentication.current_identity(token)
        return OperationResult("whoami", True, value=identity)
