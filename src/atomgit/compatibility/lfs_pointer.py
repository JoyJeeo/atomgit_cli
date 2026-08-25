"""Compatibility alias for the canonical LFS pointer adapter."""

import importlib
import sys

_owner = importlib.import_module("atomgit.adapters.lfs.pointer")

sys.modules[__name__] = _owner
