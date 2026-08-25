"""Hugging Face 1.1.7 boundary used by the shared transfer usecases.

Uploads and downloads delegate directly to their canonical adapter owners.
The historical API is loaded only when an explicitly injected compatibility
seam requires it.
"""

from pathlib import Path


class _LegacySdkProxy:
    """Resolve historical SDK adapter functions at each call site."""

    @staticmethod
    def create_repository(*args, **kwargs):
        from .sdk_repositories import create_repository

        return create_repository(*args, **kwargs)

    @staticmethod
    def upload_folder(*args, **kwargs):
        from .sdk_uploads import upload_folder

        return upload_folder(*args, **kwargs)


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
        from huggingface_hub import upload_file

        from .lfs.pointer import run_canonical_lfs_upload

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
        return run_canonical_lfs_upload(
            lambda: upload_file(**kwargs),
            token=token,
            repo_id=repo_id,
            timeout=min(timeout, 15),
        )

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
            from .upload.service import scoped_upload_token

            with scoped_upload_token(token):
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
