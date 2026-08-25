"""Compatibility alias for infrastructure environment policy."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module("atomgit.infrastructure.environment")
