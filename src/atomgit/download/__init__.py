"""Compatibility package for historical download import paths."""

import importlib
import sys

_OWNERS = {
    "integrity": "atomgit.adapters.download.integrity",
    "manifest": "atomgit.adapters.download.manifest",
    "prune": "atomgit.adapters.download.prune",
    "resume": "atomgit.adapters.download.resume",
    "service": "atomgit.compatibility.download",
    "transport": "atomgit.adapters.download.transport",
}
for _name, _owner_name in _OWNERS.items():
    _module = importlib.import_module(_owner_name)
    sys.modules[f"{__name__}.{_name}"] = _module
    globals()[_name] = _module

DownloadServiceMixin = globals()["service"].DownloadServiceMixin

__all__ = ("DownloadServiceMixin",)
