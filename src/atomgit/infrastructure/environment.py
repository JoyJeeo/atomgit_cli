"""Environment identity and installation-origin policy."""

import importlib.metadata
import json
import os
import sys
from pathlib import Path

from .managed_paths import UninstallError


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


def is_source_or_editable_install():
    """Return whether AtomGit runs from a source or editable installation."""
    try:
        distribution = importlib.metadata.distribution("atomgit")
    except importlib.metadata.PackageNotFoundError:
        distribution = None
    try:
        import atomgit

        package_path = Path(atomgit.__file__).resolve().parent
    except (ImportError, AttributeError):
        package_path = None
    if package_path and (package_path / "setup.py").exists():
        return True
    if distribution is not None:
        direct_url = distribution.read_text("direct_url.json")
        if direct_url:
            try:
                if json.loads(direct_url).get("dir_info", {}).get("editable"):
                    return True
            except json.JSONDecodeError:
                return True
    return False
