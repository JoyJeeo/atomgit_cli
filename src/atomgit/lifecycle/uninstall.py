"""Compatibility alias for infrastructure uninstall behavior."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module("atomgit.infrastructure.uninstall")
