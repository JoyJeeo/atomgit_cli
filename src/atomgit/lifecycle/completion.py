"""Compatibility alias for infrastructure completion management."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module("atomgit.infrastructure.completion")
