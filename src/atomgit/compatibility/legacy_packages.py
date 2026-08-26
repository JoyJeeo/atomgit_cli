"""Install historical package aliases after their physical directories disappear."""

import importlib
import sys
import types

LEGACY_PACKAGE_TARGETS = {
    "commands": {
        "authentication": "atomgit.interfaces.cli.commands.authentication",
        "lifecycle": "atomgit.interfaces.cli.commands.lifecycle",
        "repositories": "atomgit.interfaces.cli.commands.repositories",
        "transfers": "atomgit.interfaces.cli.commands.transfers",
        "monitor": "atomgit.interfaces.cli.commands.monitor",
    },
    "download": {
        "integrity": "atomgit.adapters.download.integrity",
        "manifest": "atomgit.adapters.download.manifest",
        "prune": "atomgit.adapters.download.prune",
        "resume": "atomgit.adapters.download.resume",
        "service": "atomgit.compatibility.download",
        "transport": "atomgit.adapters.download.transport",
    },
    "lfs": {"service": "atomgit.adapters.lfs.service"},
    "lifecycle": {
        "completion": "atomgit.infrastructure.completion",
        "environment": "atomgit.infrastructure.environment",
        "managed_paths": "atomgit.infrastructure.managed_paths",
        "uninstall": "atomgit.infrastructure.uninstall",
    },
    "sdk": {
        "common": "atomgit.adapters.sdk_common",
        "datasets": "atomgit.adapters.sdk_datasets",
        "downloads": "atomgit.adapters.sdk_downloads",
        "errors": "atomgit.adapters.sdk_errors",
        "repositories": "atomgit.adapters.sdk_repositories",
        "uploads": "atomgit.adapters.sdk_uploads",
    },
    "services": {
        "authentication": "atomgit.compatibility.authentication",
        "repositories": "atomgit.compatibility.repositories",
    },
    "upload": {
        "contracts": "atomgit.adapters.upload.contracts",
        "errors": "atomgit.adapters.upload.errors",
        "ordinary": "atomgit.adapters.upload.ordinary",
        "projection": "atomgit.adapters.upload.projection",
        "resumable": "atomgit.adapters.upload.resumable",
        "service": "atomgit.adapters.upload.service",
    },
}


def _legacy_package(fullname, children):
    package = types.ModuleType(fullname)
    package.__package__ = fullname
    package.__path__ = []
    package.__all__ = tuple(children)
    for child_name, target_name in children.items():
        owner = importlib.import_module(target_name)
        sys.modules[f"{fullname}.{child_name}"] = owner
        setattr(package, child_name, owner)
    return package


def install_legacy_package_aliases():
    """Register every deletion-pending package path against canonical owners."""
    atomgit_package = sys.modules["atomgit"]
    for package_name, children in LEGACY_PACKAGE_TARGETS.items():
        fullname = f"atomgit.{package_name}"
        package = _legacy_package(fullname, children)
        if package_name == "download":
            package.DownloadServiceMixin = package.service.DownloadServiceMixin
        elif package_name == "sdk":
            for name in (
                "snapshot_download",
                "hub_download_url",
                "download_file",
                "upload_folder",
                "create_repository",
                "load_dataset",
            ):
                for owner in children.values():
                    module = importlib.import_module(owner)
                    if hasattr(module, name):
                        setattr(package, name, getattr(module, name))
                        break
            package.__all__ = (
                "snapshot_download",
                "hub_download_url",
                "download_file",
                "upload_folder",
                "create_repository",
                "load_dataset",
            )
        sys.modules[fullname] = package
        setattr(atomgit_package, package_name, package)
