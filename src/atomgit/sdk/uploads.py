"""Folder upload behavior for the public Python SDK."""

import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Union

from huggingface_hub import constants as hf_constants
from huggingface_hub import upload_folder as hf_upload_folder

from ..exceptions import AtomGitAuthenticationError, AtomGitUnsupportedError
from ..infrastructure.validation import validate_upload_path_no_symlinks
from ..lfs_pointer import run_canonical_lfs_upload
from .common import _atomgit_repo_type, _get_token, _normalize_repo_id
from .errors import _sdk_error


def upload_folder(
    folder_path: Union[str, Path],
    repo_id: str,
    token: Optional[str] = None,
    repo_type: Optional[str] = None,
    revision: Optional[str] = None,
    commit_message: Optional[str] = None,
    commit_description: Optional[str] = None,
    path_in_repo: str = "./",
    ignore_patterns: Optional[List[str]] = None,
    upload_timeout: float = 300.0,
) -> str:
    """Upload a folder to an AtomGit repository."""
    normalized_repo_id = _normalize_repo_id(repo_id)
    folder_path = Path(folder_path)
    validate_upload_path_no_symlinks(folder_path)

    if not folder_path.exists():
        raise FileNotFoundError(f"文件夹不存在: {folder_path}")
    if not folder_path.is_dir():
        raise NotADirectoryError(f"路径不是目录: {folder_path}")
    if repo_type not in (None, "model", "dataset"):
        raise ValueError("repo_type 仅支持 model 或 dataset")
    if revision not in (None, "", "main"):
        raise AtomGitUnsupportedError(
            "AtomGit 当前仅支持默认 revision main，非默认分支不会被创建"
        )

    if token is None:
        token = _get_token()
        if token is None:
            raise AtomGitAuthenticationError(
                "上传需要认证 token；请先使用 'atomgit login' 登录或提供 token"
            )

    temporary_directory = None
    original_timeout = None
    try:
        if path_in_repo in ("./", ".", ""):
            upload_path = str(folder_path)
        else:
            temporary_directory = tempfile.TemporaryDirectory()
            temp_path = Path(temporary_directory.name)
            target_path = temp_path / path_in_repo.strip("./")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(folder_path, target_path, dirs_exist_ok=True)
            upload_path = str(temp_path)

        original_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT
        hf_constants.DEFAULT_REQUEST_TIMEOUT = upload_timeout

        try:
            upload_kwargs = dict(
                repo_id=normalized_repo_id,
                folder_path=upload_path,
                token=token,
                commit_message=commit_message or f"Upload folder {folder_path.name}",
            )
            if repo_type is not None:
                upload_kwargs["repo_type"] = _atomgit_repo_type(repo_type)
            if revision:
                upload_kwargs["revision"] = revision
            if commit_description is not None:
                upload_kwargs["commit_description"] = commit_description
            if ignore_patterns:
                upload_kwargs["ignore_patterns"] = ignore_patterns
            return run_canonical_lfs_upload(
                lambda: hf_upload_folder(**upload_kwargs),
                token=token,
                repo_id=normalized_repo_id,
                timeout=min(upload_timeout, 15),
            )
        except Exception as error:
            raise _sdk_error(error, "上传目录", repo_id) from error
    finally:
        if original_timeout is not None:
            hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
        if temporary_directory is not None:
            temporary_directory.cleanup()
