"""Compatibility alias for canonical resumable projections."""

import importlib
import sys

_owner = importlib.import_module("atomgit.adapters.upload.projection")

sys.modules[__name__] = _owner
