"""Exact managed-path manifest and safe environment cleanup."""

import stat
from pathlib import Path

MANAGED_COMPLETION_RELATIVE_PATHS = (
    Path("share/atomgit/completions/atomgit.zsh"),
    Path("etc/conda/activate.d/atomgit-completion.sh"),
    Path("etc/conda/deactivate.d/atomgit-completion.sh"),
)


class UninstallError(RuntimeError):
    """The requested uninstall cannot proceed without risking user data."""


def managed_completion_paths(prefix):
    prefix = Path(prefix)
    return tuple(prefix / relative for relative in MANAGED_COMPLETION_RELATIVE_PATHS)


def _fingerprint(file_stat):
    return (
        file_stat.st_dev,
        file_stat.st_ino,
        file_stat.st_mode,
        file_stat.st_size,
        file_stat.st_mtime_ns,
    )


def _managed_parent_exists(prefix, path):
    current = prefix
    for component in path.relative_to(prefix).parts[:-1]:
        current = current / component
        try:
            parent_stat = current.lstat()
        except FileNotFoundError:
            return False
        except OSError as error:
            raise UninstallError(f"无法检查受控父目录 {current}: {error}") from error
        if stat.S_ISLNK(parent_stat.st_mode) or not stat.S_ISDIR(parent_stat.st_mode):
            raise UninstallError(f"拒绝通过非普通受控目录删除文件: {current}")
    return True


def remove_managed_completion(prefix):
    """Remove only exact regular files from the completion manifest."""
    prefix = Path(prefix).resolve()
    snapshots = []
    for path in managed_completion_paths(prefix):
        if not _managed_parent_exists(prefix, path):
            continue
        try:
            file_stat = path.lstat()
        except FileNotFoundError:
            continue
        except OSError as error:
            raise UninstallError(f"无法检查受控文件 {path}: {error}") from error
        if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
            raise UninstallError(f"拒绝删除非普通受控文件: {path}")
        snapshots.append((path, _fingerprint(file_stat)))

    removed = []
    for path, expected in snapshots:
        try:
            if _fingerprint(path.lstat()) != expected:
                raise UninstallError(f"受控文件已被并发修改，未删除: {path}")
            path.unlink()
        except FileNotFoundError as error:
            raise UninstallError(f"受控文件已被并发删除: {path}") from error
        except OSError as error:
            raise UninstallError(f"无法删除受控文件 {path}: {error}") from error
        removed.append(path)
    return tuple(removed)
