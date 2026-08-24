"""CLI bridge that maps shared results to the historical presentation layer."""

from ..sdk import AtomGitClient


def run(operation, *args, **kwargs):
    """Execute a native usecase and return its result for Click presentation."""
    return getattr(AtomGitClient(), operation)(*args, **kwargs)


__all__ = ["run"]
