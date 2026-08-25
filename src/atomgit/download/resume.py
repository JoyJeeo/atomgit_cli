"""Compatibility alias for canonical download resume helpers."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module("atomgit.adapters.download.resume")
