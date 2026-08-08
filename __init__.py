#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AtomGit CLI - 基于Transformers和Hugging Face Hub的模型文件上传下载工具

这是一个命令行工具，用于与AtomGit平台交互，
支持模型和数据集的上传、下载等操作。
"""

__version__ = '1.0.6'
__author__ = 'JoyJeeo'
__description__ = 'AtomGit模型文件上传下载CLI工具'

try:
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
