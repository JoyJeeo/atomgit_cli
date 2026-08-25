"""Snapshot, file, and URL download behavior for the public Python SDK."""

import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from huggingface_hub import hf_hub_download
from huggingface_hub import snapshot_download as hf_snapshot_download

from ..infrastructure.utils import run_download_with_retry
from .sdk_common import _get_token, _normalize_repo_id
from .sdk_errors import _sdk_error


def snapshot_download(
    repo_id: str,
    revision: Optional[str] = None,
    cache_dir: Optional[Union[str, Path]] = None,
    local_dir: Optional[Union[str, Path]] = None,
    local_dir_use_symlinks: Union[bool, str] = "auto",
    library_name: Optional[str] = None,
    library_version: Optional[str] = None,
    user_agent: Optional[Union[str, Dict[str, str]]] = None,
    proxies: Optional[Dict[str, str]] = None,
    etag_timeout: float = 10,
    resume_download: bool = False,
    force_download: bool = False,
    token: Optional[Union[str, bool]] = None,
    local_files_only: bool = False,
    allow_patterns: Optional[Union[List[str], str]] = None,
    ignore_patterns: Optional[Union[List[str], str]] = None,
    max_workers: int = 8,
    tqdm_class: Optional[Any] = None,
) -> str:
    """Download a complete AtomGit repository snapshot."""
    normalized_repo_id = _normalize_repo_id(repo_id)
    if token is None:
        token = _get_token()

    kwargs = {"repo_id": normalized_repo_id}
    if revision is not None:
        kwargs["revision"] = revision
    if cache_dir is not None:
        kwargs["cache_dir"] = str(cache_dir)
    if local_dir is not None:
        kwargs["local_dir"] = str(local_dir)
    if token is not None:
        kwargs["token"] = token

    legacy_options = []
    if local_dir_use_symlinks != "auto":
        legacy_options.append("local_dir_use_symlinks")
    if proxies is not None:
        legacy_options.append("proxies")
    if resume_download:
        legacy_options.append("resume_download")
    if legacy_options:
        warnings.warn(
            "huggingface-hub 1.1.7 no longer accepts and AtomGit ignores: "
            + ", ".join(legacy_options),
            FutureWarning,
            stacklevel=2,
        )

    kwargs.update(
        {
            "library_name": library_name or "atomgit_hub",
            "library_version": library_version,
            "user_agent": user_agent,
            "etag_timeout": etag_timeout,
            "force_download": force_download,
            "local_files_only": local_files_only,
            "allow_patterns": allow_patterns,
            "ignore_patterns": ignore_patterns,
            "max_workers": max_workers,
            "tqdm_class": tqdm_class,
        }
    )

    try:
        return run_download_with_retry(
            lambda: hf_snapshot_download(
                **{key: value for key, value in kwargs.items() if value is not None}
            )
        )
    except Exception as error:
        raise _sdk_error(error, "下载仓库", repo_id) from error


def hub_download_url(
    repo_id: str,
    filename: str,
    revision: Optional[str] = None,
    repo_type: Optional[str] = None,
) -> str:
    """Return the AtomGit Hub resolve URL for a repository file."""
    normalized_repo_id = _normalize_repo_id(repo_id)
    if revision is None:
        revision = "main"
    if repo_type is None:
        repo_type = "model"
    return f"https://hub.atomgit.com/{normalized_repo_id}/resolve/{revision}/{filename}"


def download_file(
    repo_id: str,
    filename: str,
    local_dir: Optional[Union[str, Path]] = None,
    revision: Optional[str] = None,
    token: Optional[str] = None,
    force_download: bool = False,
) -> str:
    """Download one file from an AtomGit repository."""
    normalized_repo_id = _normalize_repo_id(repo_id)
    if token is None:
        token = _get_token()

    kwargs = {"repo_id": normalized_repo_id, "filename": filename}
    if local_dir is not None:
        kwargs["local_dir"] = str(local_dir)
    if revision is not None:
        kwargs["revision"] = revision
    if token is not None:
        kwargs["token"] = token
    if force_download:
        kwargs["force_download"] = force_download

    try:
        return run_download_with_retry(
            lambda: hf_hub_download(
                **{key: value for key, value in kwargs.items() if value is not None}
            )
        )
    except Exception as error:
        raise _sdk_error(error, "下载文件", repo_id) from error
