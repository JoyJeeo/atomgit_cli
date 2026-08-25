"""Compatibility alias for historical SDK error conversion."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module("atomgit.adapters.sdk_errors")
