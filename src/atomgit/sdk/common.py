"""Compatibility alias for historical SDK common policy."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module("atomgit.adapters.sdk_common")
