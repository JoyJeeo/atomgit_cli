"""Stable public exception hierarchy for the AtomGit Python SDK."""


class AtomGitError(Exception):
    """Base class for failures reported by the AtomGit SDK."""


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
