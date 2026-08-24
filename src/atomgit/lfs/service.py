"""Compatibility alias for the canonical LFS adapter."""

import importlib
import sys

_owner = importlib.import_module("atomgit.adapters.lfs.service")

sys.modules[__name__] = _owner
