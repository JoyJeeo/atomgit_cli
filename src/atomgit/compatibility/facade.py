"""Patch forwarding for historical API compatibility surfaces."""

import importlib.util
import sys
import types


class _LegacyCliMainLoader:
    def __init__(self, parent_name, owner):
        self.parent_name = parent_name
        self.owner = owner

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        module.cli = self.owner.cli
        module.__file__ = sys.modules[self.parent_name].__file__

    def get_code(self, fullname):
        source = (
            "from atomgit.compatibility.cli import cli\n"
            'cli(prog_name="python -m atomgit.cli.__main__")\n'
        )
        return compile(source, f"<{fullname}>", "exec")


class _LegacyCliMainFinder:
    def __init__(self, alias_name, loader):
        self.alias_name = alias_name
        self.loader = loader

    def find_spec(self, fullname, path=None, target=None):
        if fullname != self.alias_name:
            return None
        return importlib.util.spec_from_loader(fullname, self.loader)


def _install_legacy_cli_main(parent_name, owner):
    alias_name = f"{parent_name}.__main__"
    sys.modules[parent_name].__path__ = []
    if not any(
        getattr(finder, "alias_name", None) == alias_name for finder in sys.meta_path
    ):
        loader = _LegacyCliMainLoader(parent_name, owner)
        sys.meta_path.insert(0, _LegacyCliMainFinder(alias_name, loader))


def _forward_legacy_patch(module, name, value):
    for target in module._PATCH_TARGETS.get(name, ()):
        setattr(target, name, value)
    types.ModuleType.__setattr__(module, name, value)


def _delete_legacy_patch(module, name):
    for target in module._PATCH_TARGETS.get(name, ()):
        if hasattr(target, name):
            delattr(target, name)
    types.ModuleType.__delattr__(module, name)
