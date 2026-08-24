"""Native SDK client assembled from shared usecases and outbound ports."""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from ...adapters import AtomGitV5Adapter, HuggingFaceAdapter
from ...core.contracts import (
    DownloadRequest,
    OperationResult,
    RepositoryRequest,
    UploadRequest,
    Visibility,
)
from ...core.errors import AtomGitError, classify_remote_error
from ...core.policies import normalize_revision, resolve_token
from ...infrastructure.config import config as default_config
from ...usecases.authentication import AuthenticationUseCase
from ...usecases.repositories import RepositoryUseCase
from ...usecases.transfers import DownloadUseCase, UploadUseCase


class AtomGitClient:
    """A parity-oriented native SDK client.

    The legacy HF-style functions remain available in ``atomgit_hub``.  This
    client exposes the broader general remote surface through typed request
    mapping and redacted :class:`OperationResult` values.
    """

    def __init__(
        self,
        token: Optional[Union[str, bool]] = None,
        *,
        config=default_config,
        transfer=None,
        repository=None,
        authentication=None,
    ):
        self.config = config
        self._explicit_token = token
        self.transfer = transfer or HuggingFaceAdapter()
        self.repository = repository or AtomGitV5Adapter()
        self.authentication = authentication or AtomGitV5Adapter()
        self._auth = AuthenticationUseCase(self.authentication, config)
        self._repos = RepositoryUseCase(self.repository)
        self._uploads = UploadUseCase(self.transfer, config)
        self._downloads = DownloadUseCase(self.transfer, config)

    def _saved_token(self):
        credentials = self.config.get_credentials()
        return credentials.get("token") if credentials else None

    def _token(self, explicit=None, *, write=False):
        value = self._explicit_token if explicit is None else explicit
        return resolve_token(value, self._saved_token(), write=write)

    @staticmethod
    def _execute(operation, callback, repo_id=None):
        """Return structured remote failures while preserving local errors."""
        try:
            return callback()
        except (ValueError, FileNotFoundError, NotADirectoryError, TypeError):
            raise
        except AtomGitError:
            raise
        except Exception as error:
            return OperationResult(
                operation,
                False,
                repo_id=repo_id,
                error=classify_remote_error(error, operation, repo_id),
            )

    def login(self, token: str) -> OperationResult[Dict[str, Any]]:
        return self._execute("登录", lambda: self._auth.login(token))

    def logout(self) -> OperationResult[bool]:
        return self._execute("退出登录", self._auth.logout)

    def whoami(
        self, token: Optional[Union[str, bool]] = None
    ) -> OperationResult[Dict[str, Any]]:
        selected = self._token(token, write=True)
        return self._execute("获取用户信息", lambda: self._auth.whoami(selected))

    def create_repository(
        self,
        repo_id: str,
        *,
        token: Optional[Union[str, bool]] = None,
        private: bool = False,
        repo_type: str = "model",
        exist_ok: bool = False,
    ) -> OperationResult[Any]:
        selected_token = self._token(token, write=True)
        request = RepositoryRequest(
            repo_id=repo_id,
            repo_type=repo_type,
            visibility=Visibility.PRIVATE if private else Visibility.PUBLIC,
            token=selected_token,
            exist_ok=exist_ok,
        )
        return self._execute(
            "创建仓库",
            lambda: self._repos.create(request, self._saved_token()),
            repo_id,
        )

    def list_repositories(self, *, token: Optional[Union[str, bool]] = None):
        return self._execute(
            "列出仓库", lambda: self._repos.list(self._token(token, write=True))
        )

    def set_repository_visibility(self, repo_id: str, private: bool, *, token=None):
        return self._execute(
            "修改仓库可见性",
            lambda: self._repos.set_visibility(
                repo_id, private, self._token(token, write=True)
            ),
            repo_id,
        )

    def create_branch(
        self, repo_id: str, branch: str, *, source: str = "main", token=None
    ):
        return self._execute(
            "创建分支",
            lambda: self._repos.create_branch(
                repo_id, branch, source, self._token(token, write=True)
            ),
            repo_id,
        )

    def delete_repository(self, repo_id: str, *, confirmation: str, token=None):
        return self._execute(
            "删除仓库",
            lambda: self._repos.delete(
                repo_id, confirmation, self._token(token, write=True)
            ),
            repo_id,
        )

    def upload_file(
        self,
        source: Union[str, Path],
        repo_id: str,
        *,
        token=None,
        repo_type: str = "model",
        revision: Optional[str] = None,
        message: Optional[str] = None,
        path_in_repo: str = "./",
        ignore_patterns=None,
        timeout: float = 300.0,
        progress: bool = True,
        num_workers: int = 5,
    ):
        request = UploadRequest(
            source=source,
            repo_id=repo_id,
            repo_type=repo_type,
            revision=normalize_revision(revision),
            token=token,
            path_in_repo=path_in_repo,
            ignore_patterns=tuple(ignore_patterns or ()),
            message=message,
            timeout=timeout,
            progress=progress,
            num_workers=num_workers,
        )
        return self._execute("上传文件", lambda: self._uploads.file(request), repo_id)

    def upload_folder(
        self,
        source: Union[str, Path],
        repo_id: str,
        *,
        token=None,
        repo_type: str = "model",
        revision: Optional[str] = None,
        message: Optional[str] = None,
        path_in_repo: str = "./",
        ignore_patterns=None,
        resumable: bool = False,
        num_workers: int = 5,
        batch_size: int = 20,
        timeout: float = 300.0,
        progress: bool = True,
        auto_configure_lfs: bool = False,
    ):
        request = UploadRequest(
            source=source,
            repo_id=repo_id,
            repo_type=repo_type,
            revision=normalize_revision(revision),
            token=token,
            path_in_repo=path_in_repo,
            ignore_patterns=tuple(ignore_patterns or ()),
            message=message,
            resumable=resumable,
            num_workers=num_workers,
            batch_size=batch_size,
            timeout=timeout,
            progress=progress,
            auto_configure_lfs=auto_configure_lfs,
        )
        return self._execute("上传目录", lambda: self._uploads.folder(request), repo_id)

    def download_snapshot(
        self,
        repo_id: str,
        *,
        token=None,
        repo_type=None,
        revision: Optional[str] = None,
        local_dir=None,
        force: bool = False,
        checksum: bool = False,
        resume: bool = False,
        prune: bool = False,
        allow_patterns=None,
        ignore_patterns=None,
    ):
        request = DownloadRequest(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=normalize_revision(revision),
            token=token,
            local_dir=local_dir,
            force=force,
            checksum=checksum,
            resume=resume,
            prune=prune,
            allow_patterns=tuple(allow_patterns) if allow_patterns else None,
            ignore_patterns=tuple(ignore_patterns) if ignore_patterns else None,
        )
        return self._execute(
            "下载仓库", lambda: self._downloads.snapshot(request), repo_id
        )

    def download_file(
        self,
        repo_id: str,
        filename: str,
        *,
        token=None,
        repo_type=None,
        revision: Optional[str] = None,
        local_dir=None,
        force: bool = False,
        checksum: bool = False,
        resume: bool = False,
    ):
        request = DownloadRequest(
            repo_id=repo_id,
            filename=filename,
            repo_type=repo_type,
            revision=normalize_revision(revision),
            token=token,
            local_dir=local_dir,
            force=force,
            checksum=checksum,
            resume=resume,
        )
        return self._execute("下载文件", lambda: self._downloads.file(request), repo_id)


__all__ = ["AtomGitClient"]
