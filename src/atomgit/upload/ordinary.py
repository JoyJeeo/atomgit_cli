"""Compatibility alias for canonical ordinary-upload behavior."""

import importlib
import sys

_owner = importlib.import_module("atomgit.adapters.upload.ordinary")

sys.modules[__name__] = _owner
