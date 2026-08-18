"""Compatibility proxy for the historical top-level ``atomgit_hub`` module."""

import sys
import types

from atomgit import atomgit_hub as _implementation

__all__ = _implementation.__all__


def __getattr__(name):
    return getattr(_implementation, name)


def _forward_setattr(module, name, value):
    if name in {"_implementation", "__all__"} or name.startswith("__"):
        types.ModuleType.__setattr__(module, name, value)
    else:
        setattr(_implementation, name, value)


def _forward_delattr(module, name):
    if name in {"_implementation", "__all__"} or name.startswith("__"):
        types.ModuleType.__delattr__(module, name)
    else:
        delattr(_implementation, name)


_module = sys.modules[__name__]
_module.__class__ = type(
    "_AtomGitHubCompatibilityModule",
    (types.ModuleType,),
    {"__setattr__": _forward_setattr, "__delattr__": _forward_delattr},
)
