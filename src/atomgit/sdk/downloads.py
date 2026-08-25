"""Compatibility alias for the historical SDK download adapter."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module("atomgit.adapters.sdk_downloads")
