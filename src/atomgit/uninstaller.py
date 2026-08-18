"""Safe removal of AtomGit package-owned environment state."""

import importlib.metadata
import os
import stat
import subprocess
import sys
from pathlib import Path

try:
    from .release import _is_source_or_editable_install
except ImportError:
    from release import _is_source_or_editable_install


MANAGED_COMPLETION_RELATIVE_PATHS = (
    Path("share/atomgit/completions/atomgit.zsh"),
    Path("etc/conda/activate.d/atomgit-completion.sh"),
    Path("etc/conda/deactivate.d/atomgit-completion.sh"),
)


class UninstallError(RuntimeError):
    """The requested uninstall cannot proceed without risking user data."""


def _resolved_directory(path, description):
    path = Path(path).expanduser()
    if not path.is_absolute():
        raise UninstallError(f"{description}必须是绝对路径: {path}")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise UninstallError(f"无法解析{description} {path}: {error}") from error
    if not resolved.is_dir():
        raise UninstallError(f"{description}不是目录: {resolved}")
    return resolved


def active_conda_prefix(*, python_prefix=None):
    """Return the active matching conda prefix, or None outside conda."""
    raw_prefix = os.environ.get("CONDA_PREFIX")
    if not raw_prefix:
        return None
    conda_prefix = _resolved_directory(raw_prefix, "CONDA_PREFIX")
    runtime_prefix = _resolved_directory(
        python_prefix if python_prefix is not None else sys.prefix,
        "Python 环境根目录",
    )
    if conda_prefix != runtime_prefix:
        raise UninstallError(
            "CONDA_PREFIX 与当前 Python 环境不匹配；请激活目标环境后重试"
        )
    return conda_prefix


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


def build_uninstall_plan():
    """Inspect the current interpreter without mutating package or user state."""
    if _is_source_or_editable_install():
        raise UninstallError(
            "检测到 Git/可编辑源码安装；请在源码环境中使用 python -m pip uninstall atomgit，"
            "并由 Git 管理源码"
        )
    try:
        version = importlib.metadata.version("atomgit")
    except importlib.metadata.PackageNotFoundError as error:
        raise UninstallError("当前 Python 中未安装 AtomGit CLI") from error
    prefix = active_conda_prefix()
    return {
        "python": sys.executable,
        "prefix": str(Path(sys.prefix).resolve()),
        "version": version,
        "managed_paths": tuple(str(path) for path in managed_completion_paths(prefix))
        if prefix
        else (),
    }


def run_uninstall(plan):
    """Apply a previously displayed plan with the same running interpreter."""
    current_plan = build_uninstall_plan()
    if plan != current_plan:
        raise UninstallError("卸载计划已变化，请重新检查并确认")
    prefix = active_conda_prefix()
    expected_paths = (
        tuple(str(path) for path in managed_completion_paths(prefix)) if prefix else ()
    )
    if tuple(plan["managed_paths"]) != expected_paths:
        raise UninstallError("卸载计划中的受控路径已变化，请重新运行命令")
    removed = remove_managed_completion(prefix) if prefix else ()
    result = subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "--yes", "atomgit"],
        check=False,
        text=True,
    )
    if result.returncode:
        raise UninstallError("pip 未能卸载当前 Python 中的 AtomGit CLI")
    return {"removed": tuple(str(path) for path in removed)}
