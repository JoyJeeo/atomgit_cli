"""Compatibility package for historical lifecycle import paths."""

import importlib
import sys

for _name in ("completion", "environment", "managed_paths", "uninstall"):
    _module = importlib.import_module(f"atomgit.infrastructure.{_name}")
    sys.modules[f"{__name__}.{_name}"] = _module
    globals()[_name] = _module

__all__ = ("completion", "environment", "managed_paths", "uninstall")
