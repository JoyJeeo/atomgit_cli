"""Hugging Face 1.1.7 boundary used by the shared transfer usecases.

The default adapter delegates to the already verified SDK owners.  Keeping
that bridge in an outbound adapter means new interfaces share request/result
contracts while historical functions retain their exact signatures and patch
seams during the migration.
"""

from pathlib import Path


class HuggingFaceAdapter:
    def __init__(self, *, sdk_module=None, api_module=None):
        if sdk_module is None:
            from .. import sdk as sdk_module
        self.sdk = sdk_module
        if api_module is None:
            from ..api import api as api_module
        self.api = api_module

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
    ):
        from huggingface_hub import upload_file

        from ..lfs_pointer import run_canonical_lfs_upload

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
            "commit_message": f"Upload file {Path(source).name}",
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
        auto_configure_lfs=False,
    ):
        if resumable:
            # The existing CLI owner contains the projection/LFS policy.  It
            # remains the adapter bridge for resumable transfers; ordinary
            # SDK uploads below use the explicit token directly.
            from ..upload.service import scoped_upload_token

            with scoped_upload_token(token):
                return self.api.upload_directory(
                    Path(source),
                    repo_id,
                    repo_type=repo_type,
                    revision=revision,
                    path_in_repo=path_in_repo,
                    ignore_patterns=ignore_patterns,
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
        from ..download.service import scoped_download_token

        with scoped_download_token(token):
            return self.api.download_repo(
                repo_id,
                local_path=Path(local_dir) if local_dir else None,
                force_download=force,
                repo_type=repo_type,
                verify_checksum=checksum,
                resume_download=resume,
                prune=prune,
            )

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
        from ..download.service import scoped_download_token

        with scoped_download_token(token):
            return self.api.download_file(
                repo_id,
                filename,
                local_path=Path(local_dir) if local_dir else None,
                force_download=force,
                repo_type=repo_type,
                verify_checksum=checksum,
                resume_download=resume,
            )


__all__ = ["HuggingFaceAdapter"]
