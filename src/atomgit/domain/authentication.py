"""Authentication rules independent of persistence and transport."""

from ..core.errors import AtomGitAuthenticationError


def validate_login_token(token: str) -> str:
    if not isinstance(token, str) or len(token.strip()) < 10:
        raise AtomGitAuthenticationError("Token 格式不正确")
    if any(ord(character) < 32 or ord(character) == 127 for character in token):
        raise AtomGitAuthenticationError("Token 格式不正确")
    return token.strip()
