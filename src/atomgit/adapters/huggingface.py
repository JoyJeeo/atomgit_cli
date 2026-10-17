"""Hugging Face 1.1.7 boundary used by the shared transfer usecases.

Uploads and downloads delegate directly to their canonical adapter owners.
The historical API is loaded only when an explicitly injected compatibility
seam requires it.
"""

from pathlib import Path

from ..infrastructure.runtime import ATOMGIT_HF_ENDPOINT
from ..infrastructure.validation import (
    normalize_path_in_repo,
    validate_upload_path_no_symlinks,
)
from .upload.errors import _scoped_upload_output, _suppress_hf_model_repo_warning
from .upload.ordinary import _scoped_upload_settings


class _LegacySdkProxy:
    """Resolve historical SDK adapter functions at each call site."""

    @staticmethod
    def create_repository(*args, **kwargs):
        from .sdk_repositories import create_repository

        return create_repository(*args, **kwargs)

    @staticmethod
    def upload_folder(*args, **kwargs):
        from .sdk_uploads import _upload_folder

        return _upload_folder(*args, **kwargs)


class HuggingFaceAdapter:
    def __init__(self, *, sdk_module=None, api_module=None, download_adapter=None):
        if sdk_module is None:
            sdk_module = _LegacySdkProxy()
        self.sdk = sdk_module
        self._api = api_module
        if download_adapter is None:
            from .download import AtomGitDownloadAdapter

            download_adapter = AtomGitDownloadAdapter()
        self.downloads = download_adapter

    @property
    def api(self):
        """Load the historical upload bridge only when an upload needs it."""
        if self._api is None:
            from ..api import api

            self._api = api
        return self._api

    def create_repository(self, repo_id, repo_type, private, exist_ok):
        return self.sdk.create_repository(
            repo_id, private=private, repo_type=repo_type, exist_ok=exist_ok
        )

    @_scoped_upload_output()
    def upload_file(
        self,
        *,
        source,
        repo_id,
        repo_type,
        revision,
        token,
        path_in_repo,
        ignore_patterns,
        timeout,
        progress,
        message=None,
        num_workers=5,
    ):
        from huggingface_hub import HfApi

        from .lfs.pointer import (
            CanonicalLfsCommitUnconfirmedError,
            run_canonical_lfs_upload,
        )
        from .sdk_errors import _sdk_error

        validate_upload_path_no_symlinks(Path(source))
        path_in_repo = normalize_path_in_repo(path_in_repo) or "./"
        if ignore_patterns:
            raise ValueError("单文件 SDK 上传不支持 ignore_patterns")
        remote_path = (
            f"{path_in_repo.rstrip('/')}/{Path(source).name}"
            if path_in_repo not in ("", ".", "./")
            else Path(source).name
        )
        kwargs = {
            "path_or_fileobj": str(source),
            "path_in_repo": remote_path,
            "repo_id": repo_id,
            "token": token,
            "commit_message": message or f"Upload file {Path(source).name}",
        }
        if repo_type:
            kwargs["repo_type"] = "model" if repo_type == "dataset" else repo_type
        if revision:
            kwargs["revision"] = revision

        client = HfApi(endpoint=ATOMGIT_HF_ENDPOINT, token=token)
        original_commit = client.create_commit

        def commit_with_workers(*args, **call_kwargs):
            call_kwargs["num_threads"] = num_workers
            return original_commit(*args, **call_kwargs)

        client.create_commit = commit_with_workers

        def upload():
            with _suppress_hf_model_repo_warning(repo_type == "dataset"):
                return client.upload_file(**kwargs)

        try:
            with _scoped_upload_settings(timeout, progress):
                return run_canonical_lfs_upload(
                    upload,
                    token=token,
                    repo_id=repo_id,
                    timeout=timeout,
                )
        except CanonicalLfsCommitUnconfirmedError:
            raise
        except Exception as error:
            raise _sdk_error(error, "上传文件", repo_id) from None

    def upload_folder(
        self,
        *,
        source,
        repo_id,
        repo_type,
        revision,
        token,
        path_in_repo,
        ignore_patterns,
        timeout,
        progress,
        resumable,
        num_workers,
        batch_size,
        message=None,
        auto_configure_lfs=False,
    ):
        if resumable:
            from .upload.service import propagate_upload_errors, scoped_upload_token

            with scoped_upload_token(token), propagate_upload_errors():
                return self.api.upload_directory(
                    Path(source),
                    repo_id,
                    repo_type=repo_type,
                    revision=revision,
                    path_in_repo=path_in_repo,
                    ignore_patterns=ignore_patterns,
                    message=message,
                    upload_timeout=timeout,
                    progress_bar=progress,
                    resumable=True,
                    num_workers=num_workers,
                    batch_size=batch_size,
                    auto_configure_lfs=auto_configure_lfs,
                )
        if auto_configure_lfs:
            raise ValueError("auto_configure_lfs 仅支持 resumable=True")
        if batch_size != 20:
            raise ValueError(
                "普通 SDK 上传不支持自定义 batch_size，请使用 resumable=True"
            )
        return self.sdk.upload_folder(
            Path(source),
            repo_id,
            token=token,
            repo_type=repo_type,
            revision=revision,
            path_in_repo=path_in_repo,
            ignore_patterns=ignore_patterns,
            commit_message=message,
            upload_timeout=timeout,
            progress=progress,
            num_workers=num_workers,
        )

    def download_snapshot(
        self,
        *,
        repo_id,
        repo_type,
        revision,
        token,
        local_dir,
        force,
        checksum,
        resume,
        prune,
        allow_patterns,
        ignore_patterns,
    ):
        value = self.downloads.download_snapshot(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            token=token,
            local_dir=local_dir,
            force=force,
            checksum=checksum,
            resume=resume,
            prune=prune,
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
        )
        if not value:
            raise RuntimeError("仓库下载失败")
        return value

    def download_file(
        self,
        *,
        repo_id,
        filename,
        repo_type,
        revision,
        token,
        local_dir,
        force,
        checksum,
        resume,
    ):
        value = self.downloads.download_file(
            repo_id=repo_id,
            filename=filename,
            repo_type=repo_type,
            revision=revision,
            token=token,
            local_dir=local_dir,
            force=force,
            checksum=checksum,
            resume=resume,
        )
        if not value:
            raise RuntimeError("文件下载失败")
        return value


__all__ = ["HuggingFaceAdapter"]
