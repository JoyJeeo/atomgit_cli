"""Whole-repository and single-file CLI API download service."""

from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from fnmatch import fnmatch
from pathlib import Path

from huggingface_hub import HfApi

from ..infrastructure.config import config
from ..infrastructure.validation import is_auth_error, sanitized_download_error
from .integrity import _atomgit_file_checksum, _verify_download_checksum
from .manifest import (
    _download_manifest_lock,
    _download_manifest_path,
    _load_download_manifest,
    _write_download_manifest,
)
from .prune import _prune_managed_download_files, _repository_filename_parts
from .resume import _download_atomgit_file_resumable
from .transport import _download_atomgit_file

_DOWNLOAD_TOKEN_UNSET = object()
_DOWNLOAD_TOKEN_OVERRIDE = ContextVar(
    "atomgit_download_token_override", default=_DOWNLOAD_TOKEN_UNSET
)
_DOWNLOAD_REVISION_OVERRIDE = ContextVar(
    "atomgit_download_revision_override", default=None
)
_DOWNLOAD_FILTER_OVERRIDE = ContextVar(
    "atomgit_download_filter_override", default=(None, None)
)


@contextmanager
def scoped_download_token(token):
    """Use an explicit SDK token without mutating saved credentials."""
    marker = _DOWNLOAD_TOKEN_OVERRIDE.set(token)
    try:
        yield
    finally:
        _DOWNLOAD_TOKEN_OVERRIDE.reset(marker)


@contextmanager
def scoped_download_revision(revision):
    """Pass a native-SDK revision without changing the legacy API signature."""
    marker = _DOWNLOAD_REVISION_OVERRIDE.set(revision)
    try:
        yield
    finally:
        _DOWNLOAD_REVISION_OVERRIDE.reset(marker)


@contextmanager
def scoped_download_filters(allow_patterns=None, ignore_patterns=None):
    """Pass native-SDK selection policies without growing the legacy facade."""
    marker = _DOWNLOAD_FILTER_OVERRIDE.set((allow_patterns, ignore_patterns))
    try:
        yield
    finally:
        _DOWNLOAD_FILTER_OVERRIDE.reset(marker)


def _revision_kwargs(revision):
    return {} if revision in (None, "", "main") else {"revision": revision}


def _is_not_found_error(error: Exception) -> bool:
    message = str(error).lower()
    return "404" in message or "not found" in message


def _atomgit_list_repo_files(
    repo_id: str,
    token: str,
    repo_type: str = None,
    revision: str = "main",
) -> tuple:
    """List repo files without calling repo_info.

    huggingface_hub 的 snapshot_download/hf_hub_download 第一步都会调用
    repo_info（GET /api/models/{repo}），AtomGit hub 未实现该路由（404），
    SDK 会在任何下载前中止。tree/list 与 resolve 路由已实现，因此在这里
    列文件、再对每个文件直接走 resolve 下载。未显式指定类型时同时探测
    model/dataset；若兼容路由返回不同内容，则要求调用方明确选择类型。

    返回 (effective_repo_type, files)；所有候选都失败时抛出最后一次错误。
    """
    if repo_type not in (None, "model", "dataset"):
        raise ValueError("repo_type 仅支持 model 或 dataset")

    # HF Hub treats None as "use the ambient Hugging Face token". AtomGit
    # anonymous requests must opt out explicitly so an unrelated credential is
    # never attached after HF_ENDPOINT is redirected to hub.atomgit.com.
    api = HfApi(token=token if token else False)
    list_kwargs = _revision_kwargs(revision)
    if repo_type is not None:
        candidate = None if repo_type == "model" else "dataset"
        files = api.list_repo_files(repo_id, repo_type=candidate, **list_kwargs)
        return repo_type, list(files)

    successes = {}
    errors = []
    candidates = [("model", None), ("dataset", "dataset")]
    for effective_type, candidate in candidates:
        try:
            files = api.list_repo_files(repo_id, repo_type=candidate, **list_kwargs)
        except Exception as error:
            errors.append(error)
            continue
        successes[effective_type] = list(files)

    if successes:
        model_files = successes.get("model")
        dataset_files = successes.get("dataset")
        if model_files and dataset_files:
            if set(model_files) != set(dataset_files):
                raise ValueError("仓库类型不明确，请使用 --repo-type model 或 dataset")
            return "model", model_files
        if model_files:
            return "model", model_files
        if dataset_files:
            return "dataset", dataset_files
        if model_files is not None:
            return "model", model_files
        return "dataset", dataset_files or []

    for error in errors:
        if is_auth_error(error):
            raise error
    for error in errors:
        if not _is_not_found_error(error):
            raise error
    if errors:
        raise errors[-1]
    return "model", []


def _safe_download_destination(local_root: Path, filename: str) -> Path:
    """Resolve a repository filename without allowing it to escape local_root."""
    raw_parts = _repository_filename_parts(filename)

    resolved_root = Path(local_root).resolve()
    destination = resolved_root.joinpath(*raw_parts).resolve(strict=False)
    try:
        destination.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(f"仓库文件路径超出下载目录: {filename!r}") from error
    return destination


class DownloadServiceMixin:
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
        """下载仓库到本地目录（公开仓库无需token）。

        绕过 huggingface_hub 的 snapshot_download：AtomGit hub 未实现
        repo_info 路由（GET /api/models/{repo} 返回 404），SDK 会在任何
        下载前中止；这里改为 list_repo_files + resolve 逐文件下载。
        """
        revision = _DOWNLOAD_REVISION_OVERRIDE.get() or "main"
        allow_patterns, ignore_patterns = _DOWNLOAD_FILTER_OVERRIDE.get()
        manifest_locks = ExitStack()
        try:
            normalized_repo_id = self._normalize_repo_id(repo_id)

            if local_path is None:
                local_path = Path.cwd() / repo_id.split("/")[-1]

            local_path.mkdir(parents=True, exist_ok=True)

            override_token = _DOWNLOAD_TOKEN_OVERRIDE.get()
            credentials = (
                {"token": override_token}
                if override_token is not _DOWNLOAD_TOKEN_UNSET and override_token
                else (
                    None
                    if override_token is not _DOWNLOAD_TOKEN_UNSET
                    else config.get_credentials()
                )
            )
            token = (
                credentials["token"] if credentials and "token" in credentials else None
            )

            if revision in (None, "", "main"):
                effective_type, files = _atomgit_list_repo_files(
                    normalized_repo_id, token, repo_type
                )
            else:
                effective_type, files = _atomgit_list_repo_files(
                    normalized_repo_id, token, repo_type, revision
                )
            remote_files = set(files)
            if allow_patterns:
                files = [
                    filename
                    for filename in files
                    if any(fnmatch(filename, pattern) for pattern in allow_patterns)
                ]
            if ignore_patterns:
                files = [
                    filename
                    for filename in files
                    if not any(
                        fnmatch(filename, pattern) for pattern in ignore_patterns
                    )
                ]

            destinations = [
                (filename, _safe_download_destination(local_path, filename))
                for filename in files
            ]
            manifest_path = None
            manifest_available = True
            try:
                manifest_path = _download_manifest_path(
                    normalized_repo_id, effective_type, local_path
                )
            except Exception:
                if prune:
                    raise
                manifest_available = False
                manifest_exists, previously_managed = False, set()
                print("⚠ 下载 manifest 不可用；本次下载文件不会纳入后续清理")
            else:
                manifest_locks.enter_context(_download_manifest_lock(manifest_path))
                try:
                    manifest_exists, previously_managed = _load_download_manifest(
                        manifest_path
                    )
                except Exception:
                    manifest_locks.close()
                    if prune:
                        raise
                    manifest_available = False
                    manifest_exists, previously_managed = False, set()
                    print("⚠ 下载 manifest 不可用；本次下载文件不会纳入后续清理")
            downloaded_files = set()
            if not files:
                print("ℹ 仓库为空，没有可下载的文件；本地目录已创建")
            for filename, dest in destinations:
                if dest.exists() and not force_download:
                    if verify_checksum:
                        checksum = _atomgit_file_checksum(
                            normalized_repo_id,
                            effective_type,
                            filename,
                            token,
                            **_revision_kwargs(revision),
                        )
                        _verify_download_checksum(dest, checksum)
                        print(f"✓ checksum 校验通过: {filename}")
                        continue
                    print(f"⏭ 已存在，跳过（未校验内容；--force 可覆盖）: {filename}")
                    continue
                if resume_download:
                    _download_atomgit_file_resumable(
                        normalized_repo_id,
                        effective_type,
                        filename,
                        dest,
                        token,
                        **_revision_kwargs(revision),
                    )
                    print(f"✓ 可续传下载完成并通过 checksum 校验: {filename}")
                    downloaded_files.add(filename)
                    continue
                checksum = None
                if verify_checksum:
                    checksum = _atomgit_file_checksum(
                        normalized_repo_id,
                        effective_type,
                        filename,
                        token,
                        **_revision_kwargs(revision),
                    )
                if checksum is None:
                    _download_atomgit_file(
                        normalized_repo_id, effective_type, filename, dest, token
                    )
                    print(f"✓ 已下载: {filename}")
                else:
                    _download_atomgit_file(
                        normalized_repo_id,
                        effective_type,
                        filename,
                        dest,
                        token,
                        checksum=checksum,
                        **_revision_kwargs(revision),
                    )
                    print(f"✓ 已下载并通过 checksum 校验: {filename}")
                downloaded_files.add(filename)
            if prune:
                if not manifest_exists:
                    print("ℹ 未找到历史下载 manifest；未删除未受管理的本地文件")
                removed = _prune_managed_download_files(
                    local_path, previously_managed - remote_files
                )
                managed_files = (previously_managed & remote_files) | downloaded_files
                print(f"✓ 已清理受管理的本地多余文件: {removed}")
            else:
                managed_files = previously_managed | downloaded_files
            if prune:
                _write_download_manifest(manifest_path, managed_files)
            elif manifest_available:
                try:
                    _write_download_manifest(manifest_path, managed_files)
                except Exception:
                    print("⚠ 下载 manifest 写入失败；本次下载文件不会纳入后续清理")
            print("✅ 仓库下载成功")
            return True
        except Exception as e:
            print(f"仓库下载失败: {sanitized_download_error(e)}")
            return False
        finally:
            manifest_locks.close()

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
        """下载单个文件到本地目录（公开仓库无需token）。"""
        revision = _DOWNLOAD_REVISION_OVERRIDE.get() or "main"
        try:
            normalized_repo_id = self._normalize_repo_id(repo_id)

            if local_path is None:
                local_path = Path.cwd()

            local_path.mkdir(parents=True, exist_ok=True)

            override_token = _DOWNLOAD_TOKEN_OVERRIDE.get()
            credentials = (
                {"token": override_token}
                if override_token is not _DOWNLOAD_TOKEN_UNSET and override_token
                else (
                    None
                    if override_token is not _DOWNLOAD_TOKEN_UNSET
                    else config.get_credentials()
                )
            )
            token = (
                credentials["token"] if credentials and "token" in credentials else None
            )

            if revision in (None, "", "main"):
                effective_type, files = _atomgit_list_repo_files(
                    normalized_repo_id, token, repo_type
                )
            else:
                effective_type, files = _atomgit_list_repo_files(
                    normalized_repo_id, token, repo_type, revision
                )
            if filename not in files:
                print(f"✗ 文件不存在: {filename}")
                return False

            dest = _safe_download_destination(local_path, filename)
            if dest.exists() and not force_download:
                if verify_checksum:
                    checksum = _atomgit_file_checksum(
                        normalized_repo_id,
                        effective_type,
                        filename,
                        token,
                        **_revision_kwargs(revision),
                    )
                    _verify_download_checksum(dest, checksum)
                    print(f"✅ 文件 checksum 校验通过: {filename}")
                    return True
                print(f"⏭ 文件已存在，跳过: {filename}（未校验内容；--force 可覆盖）")
                return True
            if resume_download:
                _download_atomgit_file_resumable(
                    normalized_repo_id,
                    effective_type,
                    filename,
                    dest,
                    token,
                    **_revision_kwargs(revision),
                )
                print("✅ 文件可续传下载完成，checksum 校验通过")
                return True
            checksum = None
            if verify_checksum:
                checksum = _atomgit_file_checksum(
                    normalized_repo_id,
                    effective_type,
                    filename,
                    token,
                    **_revision_kwargs(revision),
                )
            if checksum is None:
                _download_atomgit_file(
                    normalized_repo_id, effective_type, filename, dest, token
                )
                print("✅ 文件下载成功")
            else:
                _download_atomgit_file(
                    normalized_repo_id,
                    effective_type,
                    filename,
                    dest,
                    token,
                    checksum=checksum,
                    **_revision_kwargs(revision),
                )
                print("✅ 文件下载成功，checksum 校验通过")
            return True
        except Exception as e:
            print(f"文件下载失败: {sanitized_download_error(e)}")
            return False
