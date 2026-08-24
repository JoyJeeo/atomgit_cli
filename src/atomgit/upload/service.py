"""Compatibility alias for the canonical upload adapter."""

import importlib
import sys

_owner = importlib.import_module("atomgit.adapters.upload.service")

sys.modules[__name__] = _owner
