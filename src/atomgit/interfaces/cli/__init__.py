"""Lightweight CLI interface package.

Command schema imports must not load SDK or Hugging Face dependencies.  The
shared-usecase runner is resolved only when a leaf command executes.
"""


def run(*args, **kwargs):
    from .runner import run as execute

    return execute(*args, **kwargs)


__all__ = ["run"]
