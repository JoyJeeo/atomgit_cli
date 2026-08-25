"""Historical API import shim."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module("atomgit.compatibility.api")
