"""Compatibility alias for historical download API methods."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module("atomgit.compatibility.download")
