"""Canonical repository and single-file download adapter."""

from contextlib import ExitStack
from fnmatch import fnmatch
from pathlib import Path

from huggingface_hub import HfApi

from ...infrastructure.validation import is_auth_error, normalize_repo_id
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


class RemoteDownloadFileNotFoundError(RuntimeError):
    """The requested remote repository file is absent."""


class AtomGitDownloadAdapter:
    def __init__(self, *, emit=None):
        self._emit_callback = emit

    def _emit(self, message):
        if self._emit_callback is not None:
            self._emit_callback(message)

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
    ) -> bool:
        """Download a repository through the canonical shared adapter.

        绕过 huggingface_hub 的 snapshot_download：AtomGit hub 未实现
        repo_info 路由（GET /api/models/{repo} 返回 404），SDK 会在任何
        下载前中止；这里改为 list_repo_files + resolve 逐文件下载。
        """
        revision = revision or "main"
        local_path = Path(local_dir) if local_dir else None
        manifest_locks = ExitStack()
        try:
            normalized_repo_id = normalize_repo_id(repo_id)

            if local_path is None:
                local_path = Path.cwd() / repo_id.split("/")[-1]

            local_path.mkdir(parents=True, exist_ok=True)

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
                self._emit("⚠ 下载 manifest 不可用；本次下载文件不会纳入后续清理")
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
                    self._emit("⚠ 下载 manifest 不可用；本次下载文件不会纳入后续清理")
            downloaded_files = set()
            if not files:
                self._emit("ℹ 仓库为空，没有可下载的文件；本地目录已创建")
            for filename, dest in destinations:
                if dest.exists() and not force:
                    if checksum:
                        expected_checksum = _atomgit_file_checksum(
                            normalized_repo_id,
                            effective_type,
                            filename,
                            token,
                            **_revision_kwargs(revision),
                        )
                        _verify_download_checksum(dest, expected_checksum)
                        self._emit(f"✓ checksum 校验通过: {filename}")
                        continue
                    self._emit(
                        f"⏭ 已存在，跳过（未校验内容；--force 可覆盖）: {filename}"
                    )
                    continue
                if resume:
                    _download_atomgit_file_resumable(
                        normalized_repo_id,
                        effective_type,
                        filename,
                        dest,
                        token,
                        **_revision_kwargs(revision),
                    )
                    self._emit(f"✓ 可续传下载完成并通过 checksum 校验: {filename}")
                    downloaded_files.add(filename)
                    continue
                expected_checksum = None
                if checksum:
                    expected_checksum = _atomgit_file_checksum(
                        normalized_repo_id,
                        effective_type,
                        filename,
                        token,
                        **_revision_kwargs(revision),
                    )
                if expected_checksum is None:
                    _download_atomgit_file(
                        normalized_repo_id, effective_type, filename, dest, token
                    )
                    self._emit(f"✓ 已下载: {filename}")
                else:
                    _download_atomgit_file(
                        normalized_repo_id,
                        effective_type,
                        filename,
                        dest,
                        token,
                        checksum=expected_checksum,
                        **_revision_kwargs(revision),
                    )
                    self._emit(f"✓ 已下载并通过 checksum 校验: {filename}")
                downloaded_files.add(filename)
            if prune:
                if not manifest_exists:
                    self._emit("ℹ 未找到历史下载 manifest；未删除未受管理的本地文件")
                removed = _prune_managed_download_files(
                    local_path, previously_managed - remote_files
                )
                managed_files = (previously_managed & remote_files) | downloaded_files
                self._emit(f"✓ 已清理受管理的本地多余文件: {removed}")
            else:
                managed_files = previously_managed | downloaded_files
            if prune:
                _write_download_manifest(manifest_path, managed_files)
            elif manifest_available:
                try:
                    _write_download_manifest(manifest_path, managed_files)
                except Exception:
                    self._emit("⚠ 下载 manifest 写入失败；本次下载文件不会纳入后续清理")
            self._emit("✅ 仓库下载成功")
            return True
        finally:
            manifest_locks.close()

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
    ) -> bool:
        """Download one file through the canonical shared adapter."""
        revision = revision or "main"
        local_path = Path(local_dir) if local_dir else None
        normalized_repo_id = normalize_repo_id(repo_id)

        if local_path is None:
            local_path = Path.cwd()

        local_path.mkdir(parents=True, exist_ok=True)

        if revision in (None, "", "main"):
            effective_type, files = _atomgit_list_repo_files(
                normalized_repo_id, token, repo_type
            )
        else:
            effective_type, files = _atomgit_list_repo_files(
                normalized_repo_id, token, repo_type, revision
            )
        if filename not in files:
            raise RemoteDownloadFileNotFoundError(f"404 文件不存在: {filename}")

        dest = _safe_download_destination(local_path, filename)
        if dest.exists() and not force:
            if checksum:
                expected_checksum = _atomgit_file_checksum(
                    normalized_repo_id,
                    effective_type,
                    filename,
                    token,
                    **_revision_kwargs(revision),
                )
                _verify_download_checksum(dest, expected_checksum)
                self._emit(f"✅ 文件 checksum 校验通过: {filename}")
                return True
            self._emit(f"⏭ 文件已存在，跳过: {filename}（未校验内容；--force 可覆盖）")
            return True
        if resume:
            _download_atomgit_file_resumable(
                normalized_repo_id,
                effective_type,
                filename,
                dest,
                token,
                **_revision_kwargs(revision),
            )
            self._emit("✅ 文件可续传下载完成，checksum 校验通过")
            return True
        expected_checksum = None
        if checksum:
            expected_checksum = _atomgit_file_checksum(
                normalized_repo_id,
                effective_type,
                filename,
                token,
                **_revision_kwargs(revision),
            )
        if expected_checksum is None:
            _download_atomgit_file(
                normalized_repo_id, effective_type, filename, dest, token
            )
            self._emit("✅ 文件下载成功")
        else:
            _download_atomgit_file(
                normalized_repo_id,
                effective_type,
                filename,
                dest,
                token,
                checksum=expected_checksum,
                **_revision_kwargs(revision),
            )
            self._emit("✅ 文件下载成功，checksum 校验通过")
        return True


__all__ = [
    "AtomGitDownloadAdapter",
    "RemoteDownloadFileNotFoundError",
    "_atomgit_list_repo_files",
    "_revision_kwargs",
    "_safe_download_destination",
]
