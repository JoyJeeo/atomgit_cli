"""Compatibility alias for the canonical historical-SDK upload adapter."""

import importlib
import sys

_owner = importlib.import_module("atomgit.adapters.sdk_uploads")

sys.modules[__name__] = _owner
