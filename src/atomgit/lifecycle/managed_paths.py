"""Compatibility alias for infrastructure managed paths."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module("atomgit.infrastructure.managed_paths")
