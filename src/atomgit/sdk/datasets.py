"""Compatibility alias for the historical SDK dataset adapter."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module("atomgit.adapters.sdk_datasets")
