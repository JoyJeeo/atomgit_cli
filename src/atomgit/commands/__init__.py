"""Compatibility package for the historical CLI command import path."""

import importlib
import sys

_owner = importlib.import_module("atomgit.interfaces.cli.commands")
for _name in ("authentication", "lifecycle", "repositories", "transfers"):
    _module = importlib.import_module(f"{_owner.__name__}.{_name}")
    sys.modules[f"{__name__}.{_name}"] = _module
    globals()[_name] = _module

__all__ = ("authentication", "lifecycle", "repositories", "transfers")
