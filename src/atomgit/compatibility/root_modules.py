"""Load the finite historical root-module surface from canonical directories."""

import importlib.util
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
LEGACY_ROOT_MODULE_SOURCES = {
    "atomgit.cli_contracts": _PACKAGE_ROOT / "compatibility" / "cli_contracts.py",
    "atomgit.completion": _PACKAGE_ROOT / "compatibility" / "completion.py",
    "atomgit.config": _PACKAGE_ROOT / "compatibility" / "config.py",
    "atomgit.exceptions": _PACKAGE_ROOT / "compatibility" / "exceptions.py",
    "atomgit.lfs_pointer": _PACKAGE_ROOT / "compatibility" / "lfs_pointer.py",
    "atomgit.release": _PACKAGE_ROOT / "compatibility" / "release.py",
    "atomgit.runtime": _PACKAGE_ROOT / "compatibility" / "runtime.py",
    "atomgit.uninstaller": _PACKAGE_ROOT / "compatibility" / "uninstaller.py",
    "atomgit.utils": _PACKAGE_ROOT / "compatibility" / "utils.py",
    "atomgit.version": _PACKAGE_ROOT / "infrastructure" / "version.py",
}


class _LegacyRootModuleFinder:
    route_names = frozenset(LEGACY_ROOT_MODULE_SOURCES)

    def find_spec(self, fullname, path=None, target=None):
        source = LEGACY_ROOT_MODULE_SOURCES.get(fullname)
        if source is None:
            return None
        loader = SourceFileLoader(fullname, str(source))
        return importlib.util.spec_from_file_location(fullname, source, loader=loader)


def install_legacy_root_module_finder():
    """Install one idempotent finder for the ten approved historical names."""

    if not any(
        getattr(finder, "route_names", None) == _LegacyRootModuleFinder.route_names
        for finder in sys.meta_path
    ):
        sys.meta_path.insert(0, _LegacyRootModuleFinder())


__all__ = ("LEGACY_ROOT_MODULE_SOURCES", "install_legacy_root_module_finder")
