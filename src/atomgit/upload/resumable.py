"""Compatibility alias for canonical resumable-upload behavior."""

import importlib
import sys

_owner = importlib.import_module("atomgit.adapters.upload.resumable")

sys.modules[__name__] = _owner
