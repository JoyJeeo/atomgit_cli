"""Compatibility alias for the canonical CLI transfer callbacks."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module(
    "atomgit.interfaces.cli.commands.transfers"
)
