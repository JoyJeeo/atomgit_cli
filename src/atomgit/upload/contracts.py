"""Compatibility alias for canonical upload adapter defaults."""

import importlib
import sys

_owner = importlib.import_module("atomgit.adapters.upload.contracts")

sys.modules[__name__] = _owner
