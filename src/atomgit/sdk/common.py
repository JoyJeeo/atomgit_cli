"""Shared authentication and repository policy for the public Python SDK."""

from typing import Optional

from ..infrastructure.config import config
from ..infrastructure.validation import normalize_repo_id


def _normalize_repo_id(repo_id: str) -> str:
    """Normalize a repository ID while preserving the historical helper."""
    return normalize_repo_id(repo_id)


def _atomgit_repo_type(repo_type: Optional[str]) -> Optional[str]:
    """Map dataset create and transfer calls to AtomGit's shared model route."""
    return "model" if repo_type == "dataset" else repo_type


def _get_token() -> Optional[str]:
    """Return the saved authentication token, if available."""
    try:
        credentials = config.get_credentials()
        if credentials and "token" in credentials:
            return credentials["token"]
    except Exception:
        pass
    return None
