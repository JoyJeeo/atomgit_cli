"""Historical public path for the core-owned AtomGit error hierarchy."""

from .core.errors import (
    AtomGitAuthenticationError,
    AtomGitError,
    AtomGitNetworkError,
    AtomGitRepositoryExistsError,
    AtomGitRepositoryNotFoundError,
    AtomGitRevisionNotFoundError,
    AtomGitTimeoutError,
    AtomGitUnsupportedError,
)

__all__ = [
    "AtomGitError",
    "AtomGitAuthenticationError",
    "AtomGitRepositoryNotFoundError",
    "AtomGitRepositoryExistsError",
    "AtomGitRevisionNotFoundError",
    "AtomGitTimeoutError",
    "AtomGitNetworkError",
    "AtomGitUnsupportedError",
]
