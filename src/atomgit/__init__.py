#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AtomGit CLI - 基于Transformers和Hugging Face Hub的模型文件上传下载工具

这是一个命令行工具，用于与AtomGit平台交互，
支持模型和数据集的上传、下载等操作。
"""

import os
from importlib import import_module

from .compatibility.root_modules import install_legacy_root_module_finder
from .infrastructure.runtime import configure_hf_environment
from .infrastructure.version import __version__

__author__ = 'JoyJeeo'
__description__ = 'AtomGit模型文件上传下载CLI工具'

install_legacy_root_module_finder()
configure_hf_environment()


_LAZY_EXPORTS = {
    "config": (".config", "config"),
    "api": (".api", "api"),
    "cli": (".cli", "cli"),
    "snapshot_download": (".atomgit_hub", "snapshot_download"),
    "hub_download_url": (".atomgit_hub", "hub_download_url"),
    "download_file": (".atomgit_hub", "download_file"),
    "upload_folder": (".atomgit_hub", "upload_folder"),
    "create_repository": (".atomgit_hub", "create_repository"),
    "AtomGitError": (".atomgit_hub", "AtomGitError"),
    "AtomGitAuthenticationError": (".atomgit_hub", "AtomGitAuthenticationError"),
    "AtomGitRepositoryNotFoundError": (
        ".atomgit_hub",
        "AtomGitRepositoryNotFoundError",
    ),
    "AtomGitRepositoryExistsError": (
        ".atomgit_hub",
        "AtomGitRepositoryExistsError",
    ),
    "AtomGitRevisionNotFoundError": (
        ".atomgit_hub",
        "AtomGitRevisionNotFoundError",
    ),
    "AtomGitTimeoutError": (".atomgit_hub", "AtomGitTimeoutError"),
    "AtomGitNetworkError": (".atomgit_hub", "AtomGitNetworkError"),
    "AtomGitUnsupportedError": (".atomgit_hub", "AtomGitUnsupportedError"),
}


def __getattr__(name):
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = target
    value = getattr(import_module(module_name, __name__), attribute_name)
    globals()[name] = value
    return value


# Click starts a fresh process for every completion request. Preserve the
# established eager package exports for normal callers while keeping that
# high-frequency schema-only path free of business and SDK imports.
if "_ATOMGIT_COMPLETE" not in os.environ:
    try:
        from .compatibility.legacy_packages import install_legacy_package_aliases

        install_legacy_package_aliases()
        import_module(".utils", __name__)
        from .config import config
        from .api import api
        from .cli import cli
        from .atomgit_hub import (
            snapshot_download, hub_download_url, download_file,
            upload_folder, create_repository,
            AtomGitError, AtomGitAuthenticationError,
            AtomGitRepositoryNotFoundError, AtomGitRepositoryExistsError,
            AtomGitRevisionNotFoundError, AtomGitTimeoutError,
            AtomGitNetworkError, AtomGitUnsupportedError,
        )
    except ImportError:
        from compatibility.legacy_packages import install_legacy_package_aliases

        install_legacy_package_aliases()
        import_module("utils")
        from config import config
        from api import api
        from cli import cli
        from atomgit_hub import (
            snapshot_download, hub_download_url, download_file,
            upload_folder, create_repository,
            AtomGitError, AtomGitAuthenticationError,
            AtomGitRepositoryNotFoundError, AtomGitRepositoryExistsError,
            AtomGitRevisionNotFoundError, AtomGitTimeoutError,
            AtomGitNetworkError, AtomGitUnsupportedError,
        )

__all__ = [
    'config', 'api', 'cli',
    'snapshot_download', 'hub_download_url', 'download_file', 
    'upload_folder', 'create_repository',
    'AtomGitError', 'AtomGitAuthenticationError',
    'AtomGitRepositoryNotFoundError', 'AtomGitRepositoryExistsError',
    'AtomGitRevisionNotFoundError', 'AtomGitTimeoutError',
    'AtomGitNetworkError', 'AtomGitUnsupportedError',
]
