"""CLI bridge that maps shared results to the historical presentation layer.

The adapters in this module deliberately preserve the historical ``context``
patch seams while the request still travels through the native client and its
shared usecases.  R3 can replace these legacy-backed adapters without another
CLI presentation migration.
"""

from pathlib import Path

from ...adapters import AtomGitDownloadAdapter
from ...adapters.download.service import RemoteDownloadFileNotFoundError
from ...infrastructure.validation import sanitized_download_error
from ..sdk import AtomGitClient


class _ContextManagedCredential(str):
    """Non-secret marker used only by historical write adapters."""


_CONTEXT_MANAGED_CREDENTIAL = _ContextManagedCredential("context-managed-credential")


class _CliConfigPort:
    def __init__(self, context):
        self.context = context

    def get_credentials(self):
        credentials = self.context.config.get_credentials()
        if credentials:
            return credentials
        # Click tests and callers may patch is_logged_in without installing a
        # real config file.  The legacy API remains the credential owner for
        # this bridge, so a non-secret sentinel only satisfies the core write
        # policy and is never sent to a remote adapter.
        if self.context.config.is_logged_in():
            return {"token": _CONTEXT_MANAGED_CREDENTIAL}
        return None

    def set_credentials(self, token, username=None):
        return self.context.config.set_credentials(token, username=username)

    def clear_credentials(self):
        return self.context.config.clear_credentials()


class _CliAuthenticationPort:
    def __init__(self, context):
        self.context = context

    def authenticate(self, token):
        if not self.context.api.login(token):
            raise RuntimeError("登录失败")
        username = None
        get_value = getattr(self.context.config, "get_value", None)
        if get_value is not None:
            username = get_value("username")
        return {"login": username} if username else {}

    def current_identity(self, token):
        identity = self.context.api.get_login_user()
        if not identity:
            raise RuntimeError("无法确认当前登录用户")
        return identity


class _CliRepositoryPort:
    def __init__(self, context):
        self.context = context

    def create(self, repo_id, repo_type, private, exist_ok, token):
        value = self.context.api.create_repo(
            repo_id, repo_type, private, exist_ok=exist_ok
        )
        if not value:
            raise RuntimeError("仓库创建失败")
        return value

    def list(self, token):
        value = self.context.api.list_repos()
        if value is None:
            raise RuntimeError("获取仓库列表失败")
        return value

    def set_visibility(self, repo_id, private, token):
        value = self.context.api.set_repo_visibility(repo_id, private=private)
        if not value:
            raise RuntimeError("仓库可见性修改失败")
        return True

    def create_branch(self, repo_id, branch, source, token):
        value = self.context.api.create_branch(repo_id, branch, source=source)
        if not value:
            raise RuntimeError("分支创建失败")
        return True

    def delete(self, repo_id, confirmation, token):
        value = self.context.api.delete_repo(repo_id, confirmation=confirmation)
        if not value:
            raise RuntimeError("仓库删除失败")
        return True


class _CliTransferPort:
    def __init__(self, context, *, repo_type_explicit=True, progress_callback=None):
        self.context = context
        self.repo_type_explicit = repo_type_explicit
        self.progress_callback = progress_callback

    def _legacy_repo_type(self, repo_type):
        return repo_type if self.repo_type_explicit else None

    @staticmethod
    def _download_token(token):
        if token is _CONTEXT_MANAGED_CREDENTIAL:
            return None
        return token

    def _download_error(self, label, error):
        detail = sanitized_download_error(error)
        print(f"{label}: {detail}")

    def _patched_legacy_download(self, name):
        """Return an explicitly patched old API seam, never the default owner."""
        resolver = getattr(self.context.api, "_resolve", None)
        api = resolver() if callable(resolver) else self.context.api
        if name not in getattr(api, "__dict__", {}):
            return None
        return getattr(api, name)

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
        value = self.context.api.upload_folder(
            Path(source),
            repo_id,
            upload_timeout=timeout,
            progress_bar=progress,
            path_in_repo=path_in_repo,
            repo_type=self._legacy_repo_type(repo_type),
            revision=revision,
            ignore_patterns=ignore_patterns,
            message=message,
            num_workers=num_workers,
        )
        if not value:
            raise RuntimeError("文件上传失败")
        return value

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
        if Path(source).is_file():
            value = self.context.api.upload_folder(
                Path(source),
                repo_id,
                upload_timeout=timeout,
                progress_bar=progress,
                path_in_repo=path_in_repo,
                repo_type=self._legacy_repo_type(repo_type),
                revision=revision,
                ignore_patterns=ignore_patterns,
                message=message,
                num_workers=num_workers,
            )
        else:
            value = self.context.api.upload_directory(
                Path(source),
                repo_id,
                upload_timeout=timeout,
                progress_bar=progress,
                path_in_repo=path_in_repo,
                repo_type=self._legacy_repo_type(repo_type),
                revision=revision,
                ignore_patterns=ignore_patterns,
                message=message,
                resumable=resumable,
                num_workers=num_workers,
                batch_size=batch_size,
                auto_configure_lfs=auto_configure_lfs,
                progress_callback=(self.progress_callback if resumable else None),
            )
        if not value:
            raise RuntimeError("目录上传失败")
        return value

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
        legacy = self._patched_legacy_download("download_repo")
        if legacy is not None:
            options = {
                "force_download": force,
                "repo_type": self._legacy_repo_type(repo_type),
            }
            if checksum:
                options["verify_checksum"] = True
            if resume:
                options["resume_download"] = True
            if prune:
                options["prune"] = True
            value = legacy(repo_id, Path(local_dir) if local_dir else None, **options)
        else:
            try:
                value = AtomGitDownloadAdapter(emit=print).download_snapshot(
                    repo_id=repo_id,
                    repo_type=self._legacy_repo_type(repo_type),
                    revision=revision,
                    token=self._download_token(token),
                    local_dir=local_dir,
                    force=force,
                    checksum=checksum,
                    resume=resume,
                    prune=prune,
                    allow_patterns=allow_patterns,
                    ignore_patterns=ignore_patterns,
                )
            except Exception as error:
                self._download_error("仓库下载失败", error)
                raise
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
        legacy = self._patched_legacy_download("download_file")
        if legacy is not None:
            options = {
                "force_download": force,
                "repo_type": self._legacy_repo_type(repo_type),
            }
            if checksum:
                options["verify_checksum"] = True
            if resume:
                options["resume_download"] = True
            value = legacy(
                repo_id, filename, Path(local_dir) if local_dir else None, **options
            )
        else:
            try:
                value = AtomGitDownloadAdapter(emit=print).download_file(
                    repo_id=repo_id,
                    filename=filename,
                    repo_type=self._legacy_repo_type(repo_type),
                    revision=revision,
                    token=self._download_token(token),
                    local_dir=local_dir,
                    force=force,
                    checksum=checksum,
                    resume=resume,
                )
            except RemoteDownloadFileNotFoundError:
                print(f"✗ 文件不存在: {filename}")
                raise
            except Exception as error:
                self._download_error("文件下载失败", error)
                raise
        if not value:
            raise RuntimeError("文件下载失败")
        return value


def run(context, operation, *args, **kwargs):
    """Execute a shared usecase with historical CLI adapters."""
    repo_type_explicit = kwargs.pop("_cli_repo_type_explicit", True)
    progress_callback = kwargs.pop("_cli_progress_callback", None)
    config = _CliConfigPort(context)
    client = AtomGitClient(
        config=config,
        transfer=_CliTransferPort(
            context,
            repo_type_explicit=repo_type_explicit,
            progress_callback=progress_callback,
        ),
        repository=_CliRepositoryPort(context),
        authentication=_CliAuthenticationPort(context),
    )
    return getattr(client, operation)(*args, **kwargs)


__all__ = ["run"]
