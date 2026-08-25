"""Compatibility alias for the canonical CLI authentication callbacks."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module(
    "atomgit.interfaces.cli.commands.authentication"
)
