# ruff: noqa: F401 -- historical private import surface
"""Historical download API methods backed by canonical adapters."""

from pathlib import Path

from ..adapters.download.service import (
    AtomGitDownloadAdapter,
    RemoteDownloadFileNotFoundError,
    _atomgit_list_repo_files,
    _revision_kwargs,
    _safe_download_destination,
)
from ..infrastructure.config import config
from ..infrastructure.validation import sanitized_download_error


class DownloadServiceMixin:
    """Preserve historical signatures, boolean results, and saved-token use."""

    @staticmethod
    def _download_token():
        credentials = config.get_credentials()
        return credentials.get("token") if credentials else None

    def download_repo(
        self,
        repo_id: str,
        local_path: Path = None,
        force_download: bool = False,
        repo_type: str = None,
        verify_checksum: bool = False,
        resume_download: bool = False,
        prune: bool = False,
    ) -> bool:
        try:
            return AtomGitDownloadAdapter(emit=print).download_snapshot(
                repo_id=repo_id,
                repo_type=repo_type,
                revision="main",
                token=self._download_token(),
                local_dir=local_path,
                force=force_download,
                checksum=verify_checksum,
                resume=resume_download,
                prune=prune,
                allow_patterns=None,
                ignore_patterns=None,
            )
        except Exception as error:
            print(f"仓库下载失败: {sanitized_download_error(error)}")
            return False

    def download_file(
        self,
        repo_id: str,
        filename: str,
        local_path: Path = None,
        force_download: bool = False,
        repo_type: str = None,
        verify_checksum: bool = False,
        resume_download: bool = False,
    ) -> bool:
        try:
            return AtomGitDownloadAdapter(emit=print).download_file(
                repo_id=repo_id,
                filename=filename,
                repo_type=repo_type,
                revision="main",
                token=self._download_token(),
                local_dir=local_path,
                force=force_download,
                checksum=verify_checksum,
                resume=resume_download,
            )
        except RemoteDownloadFileNotFoundError:
            print(f"✗ 文件不存在: {filename}")
            return False
        except Exception as error:
            print(f"文件下载失败: {sanitized_download_error(error)}")
            return False


__all__ = ["DownloadServiceMixin"]
