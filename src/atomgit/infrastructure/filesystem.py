"""Filesystem validation and upload-statistics helpers."""

import os
from fnmatch import fnmatch
from pathlib import Path
from typing import List, Optional

try:
    from huggingface_hub.utils import filter_repo_objects
except ImportError:

    def filter_repo_objects(items, *, ignore_patterns=None, key=None, **kwargs):
        patterns = tuple(ignore_patterns or ())
        for item in items:
            candidate = key(item) if key is not None else item
            candidate = str(candidate)
            if not any(fnmatch(candidate, pattern) for pattern in patterns):
                yield item


def get_file_size(file_path: Path) -> int:
    """获取文件大小"""
    try:
        return file_path.stat().st_size
    except OSError:
        return 0


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    index = 0
    while size_bytes >= 1024 and index < len(size_names) - 1:
        size_bytes /= 1024.0
        index += 1

    return f"{size_bytes:.1f} {size_names[index]}"


def _is_resumable_metadata(path: Path, root: Path) -> bool:
    """Return whether a file belongs to HF's resumable metadata subtree."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    parts = relative.parts
    return len(parts) >= 2 and parts[0] == ".cache" and parts[1] == "huggingface"


def get_directory_size(dir_path: Path, exclude_resumable_metadata: bool = False) -> int:
    """获取目录大小"""
    total_size = 0
    try:
        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and not (
                exclude_resumable_metadata
                and _is_resumable_metadata(file_path, dir_path)
            ):
                total_size += get_file_size(file_path)
    except OSError:
        pass
    return total_size


def count_files_in_directory(
    dir_path: Path, exclude_resumable_metadata: bool = False
) -> int:
    """统计目录中的文件数量"""
    count = 0
    try:
        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and not (
                exclude_resumable_metadata
                and _is_resumable_metadata(file_path, dir_path)
            ):
                count += 1
    except OSError:
        pass
    return count


def get_upload_file_stats(
    dir_path: Path, ignore_patterns: Optional[List[str]] = None
) -> tuple:
    """Return the file count and bytes HF will consider for a directory upload."""
    dir_path = Path(dir_path)

    def candidates():
        for root_name, directory_names, filenames in os.walk(
            str(dir_path), topdown=True, followlinks=False
        ):
            root = Path(root_name)
            if _is_resumable_metadata(root, dir_path):
                directory_names[:] = []
                continue
            directory_names[:] = [
                name
                for name in directory_names
                if not _is_resumable_metadata(root / name, dir_path) and name != ".git"
            ]
            for name in filenames:
                candidate = root / name
                if candidate.is_symlink() or not candidate.is_file():
                    continue
                yield candidate.relative_to(dir_path), candidate

    filtered = filter_repo_objects(
        candidates(),
        ignore_patterns=ignore_patterns,
        key=lambda item: item[0].as_posix(),
    )
    count = 0
    total_size = 0
    for _, candidate in filtered:
        count += 1
        total_size += get_file_size(candidate)
    return count, total_size


def is_valid_path(path_str: str) -> bool:
    """检查路径是否有效"""
    try:
        Path(path_str)
        return True
    except (ValueError, OSError):
        return False


def ensure_directory(dir_path: Path) -> bool:
    """确保目录存在"""
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False


def get_relative_path(file_path: Path, base_path: Path) -> str:
    """获取相对路径"""
    try:
        return str(file_path.relative_to(base_path))
    except ValueError:
        return str(file_path)
