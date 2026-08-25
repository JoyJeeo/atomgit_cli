"""Compatibility alias for the historical API facade."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module("atomgit.compatibility.api")
