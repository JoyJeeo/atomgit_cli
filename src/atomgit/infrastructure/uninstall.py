"""Plan and execute safe package removal for the current interpreter."""

import importlib.metadata
import subprocess
import sys
from pathlib import Path

from .environment import active_conda_prefix, is_source_or_editable_install
from .managed_paths import (
    UninstallError,
    managed_completion_paths,
    remove_managed_completion,
)

_is_source_or_editable_install = is_source_or_editable_install


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
        "managed_paths": (
            tuple(str(path) for path in managed_completion_paths(prefix))
            if prefix
            else ()
        ),
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
