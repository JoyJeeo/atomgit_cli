"""Compatibility package for historical service import paths."""

import importlib
import sys

for _name in ("authentication", "repositories"):
    _module = importlib.import_module(f"atomgit.compatibility.{_name}")
    sys.modules[f"{__name__}.{_name}"] = _module
    globals()[_name] = _module

__all__ = ("authentication", "repositories")
