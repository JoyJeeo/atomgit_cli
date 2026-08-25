"""Compatibility alias for historical repository API methods."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module("atomgit.compatibility.repositories")
