"""Compatibility alias for the canonical CLI repository callbacks."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module(
    "atomgit.interfaces.cli.commands.repositories"
)
