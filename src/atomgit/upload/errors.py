"""Compatibility alias for canonical upload error policy."""

import importlib
import sys

_owner = importlib.import_module("atomgit.adapters.upload.errors")

sys.modules[__name__] = _owner
