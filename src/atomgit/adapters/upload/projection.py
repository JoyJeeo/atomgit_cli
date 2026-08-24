"""Stable private projections for resumable uploads."""

import hashlib
import os
import shutil
import stat
from pathlib import Path
from typing import Optional, Set

from huggingface_hub._local_folder import read_upload_metadata
from huggingface_hub.utils import filter_repo_objects

from ..download.transport import _atomgit_hf_endpoint


class ResumableProjectionError(ValueError):
    """A local resumable projection cannot be prepared safely."""


def _resumable_projection_cache_root() -> Path:
    """Return the private cache for stable path-in-repo upload projections."""
    hf_home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "atomgit"))
    root = hf_home / "upload-projections"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise ResumableProjectionError("断点续传投影缓存目录不安全")
    os.chmod(root, 0o700)
    return root


def _ensure_projection_directory(path: Path, projection_root: Path) -> None:
    """Create an internal projection directory without following symlinks."""
    relative = path.relative_to(projection_root)
    current = projection_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ResumableProjectionError("断点续传投影缓存包含符号链接")
        if current.exists() and not current.is_dir():
            current.unlink()
        current.mkdir(mode=0o700, exist_ok=True)


def _source_projection_files(source: Path):
    """Yield regular source files while excluding HF's local resume metadata."""
    for root_name, directory_names, filenames in os.walk(
        str(source), topdown=True, followlinks=False
    ):
        root = Path(root_name)
        relative_root = root.relative_to(source)
        if tuple(part.casefold() for part in relative_root.parts[:2]) == (
            ".cache",
            "huggingface",
        ):
            directory_names[:] = []
            continue

        retained_directories = []
        for name in directory_names:
            candidate = root / name
            if candidate.is_symlink():
                raise ValueError("上传路径包含符号链接，已拒绝上传")
            if name == ".git":
                continue
            relative = candidate.relative_to(source)
            if tuple(part.casefold() for part in relative.parts[:2]) != (
                ".cache",
                "huggingface",
            ):
                retained_directories.append(name)
        directory_names[:] = retained_directories

        for name in filenames:
            candidate = root / name
            if candidate.is_symlink():
                raise ValueError("上传路径包含符号链接，已拒绝上传")
            try:
                file_stat = candidate.stat()
            except OSError as error:
                raise ValueError("无法读取上传目录，已拒绝上传") from error
            if stat.S_ISREG(file_stat.st_mode):
                yield candidate.relative_to(source), candidate, file_stat


def _projection_file_is_current(source: Path, destination: Path, source_stat) -> bool:
    if destination.is_symlink():
        try:
            return os.path.samefile(source, destination)
        except OSError:
            return False
    if not destination.is_file():
        return False
    try:
        if os.path.samefile(source, destination):
            return True
        destination_stat = destination.stat()
    except OSError:
        return False
    return (
        destination_stat.st_size == source_stat.st_size
        and destination_stat.st_mtime_ns == source_stat.st_mtime_ns
    )


def _is_projection_hf_metadata(path: Path, projection: Path) -> bool:
    relative = path.relative_to(projection)
    return tuple(part.casefold() for part in relative.parts[:2]) == (
        ".cache",
        "huggingface",
    )


def _sync_resumable_projection(
    source: Path,
    projection: Path,
    prefix: str = None,
    ignore_patterns=None,
    selected_paths: Optional[Set[Path]] = None,
) -> None:
    """Mirror source files below prefix while retaining HF metadata at root."""
    payload_root = projection.joinpath(*prefix.split("/")) if prefix else projection
    _ensure_projection_directory(payload_root, projection)
    desired_paths = set()

    source_files = filter_repo_objects(
        _source_projection_files(source),
        ignore_patterns=ignore_patterns,
        key=lambda item: item[0].as_posix(),
    )
    for relative, source_file, source_stat in source_files:
        if selected_paths is not None and relative not in selected_paths:
            continue
        desired_paths.add(relative)
        destination = payload_root / relative
        if _is_projection_hf_metadata(destination, projection):
            raise ResumableProjectionError(
                "上传内容与 HF 断点续传元数据路径冲突，请使用 --no-resumable"
            )
        _ensure_projection_directory(destination.parent, projection)
        if destination.is_dir():
            shutil.rmtree(destination)
        elif _projection_file_is_current(source_file, destination, source_stat):
            continue
        elif destination.exists():
            destination.unlink()

        try:
            os.link(source_file, destination)
        except OSError:
            try:
                os.symlink(source_file, destination)
            except OSError as error:
                raise ResumableProjectionError(
                    "无法为断点续传创建无副本投影；请确认缓存目录与源目录支持硬链接或符号链接"
                ) from error

    for root_name, directory_names, filenames in os.walk(
        str(payload_root), topdown=False, followlinks=False
    ):
        root = Path(root_name)
        for name in filenames:
            candidate = root / name
            relative = candidate.relative_to(payload_root)
            if _is_projection_hf_metadata(candidate, projection):
                continue
            if relative not in desired_paths:
                candidate.unlink()
        for name in directory_names:
            candidate = root / name
            if candidate.is_symlink():
                candidate.unlink()
                continue
            relative = candidate.relative_to(payload_root)
            if _is_projection_hf_metadata(candidate, projection):
                continue
            try:
                candidate.rmdir()
            except OSError:
                pass


def _prepare_resumable_upload_projection(
    source: Path,
    repo_id: str,
    repo_type: str,
    revision: str,
    path_in_repo: str = None,
    ignore_patterns=None,
    selected_paths: Optional[Set[Path]] = None,
    batch_key: str = "all",
) -> Path:
    """Build or refresh one stable large-folder projection for a remote prefix."""
    parts = path_in_repo.split("/") if path_in_repo else []
    folded_parts = [part.casefold() for part in parts]
    if ".git" in folded_parts or any(
        folded_parts[index : index + 2] == [".cache", "huggingface"]
        for index in range(len(folded_parts) - 1)
    ):
        raise ResumableProjectionError(
            "断点续传模式不能上传到 HF 保留路径，请使用 --no-resumable"
        )

    source = source.expanduser().resolve(strict=True)
    cache_root = _resumable_projection_cache_root()
    try:
        source.relative_to(cache_root)
    except ValueError:
        pass
    else:
        raise ResumableProjectionError("不能将断点续传投影缓存作为上传源")

    identity = "\0".join(
        (
            _atomgit_hf_endpoint(),
            str(source),
            repo_id,
            repo_type,
            revision or "main",
            path_in_repo or "",
            batch_key,
        )
    )
    projection = cache_root / hashlib.sha256(identity.encode("utf-8")).hexdigest()
    _ensure_projection_directory(projection, cache_root)
    os.chmod(projection, 0o700)
    _sync_resumable_projection(
        source,
        projection,
        path_in_repo,
        ignore_patterns=ignore_patterns,
        selected_paths=selected_paths,
    )
    return projection


def _collect_resumable_upload_files(source: Path, ignore_patterns=None):
    """Return deterministic source-relative files selected for upload."""
    source_files = filter_repo_objects(
        _source_projection_files(source),
        ignore_patterns=ignore_patterns,
        key=lambda item: item[0].as_posix(),
    )
    return sorted(list(source_files), key=lambda item: item[0].as_posix())


def _resumable_committed_file_count(
    projection: Path, selected_paths, path_in_repo: str = None
) -> int:
    """Count current projected files already committed by HF large-folder."""
    prefix = f"{path_in_repo}/" if path_in_repo else ""
    committed = 0
    for relative_path in selected_paths:
        try:
            metadata = read_upload_metadata(
                Path(projection), prefix + relative_path.as_posix()
            )
        except Exception:
            # This helper is observational. HF remains authoritative and will
            # validate or repair its own metadata in the upload process.
            continue
        if metadata.is_committed:
            committed += 1
    return committed
