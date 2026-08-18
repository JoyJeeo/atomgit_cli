"""Generate and safely manage AtomGit's Zsh completion adapter."""

import os
import shlex
import stat
import sys
import tempfile
from pathlib import Path

from click.shell_completion import get_completion_class

from .environment import active_conda_prefix
from .managed_paths import (
    UninstallError,
    managed_completion_paths,
    remove_managed_completion,
)

SUPPORTED_SHELLS = ("zsh",)
_COMPLETE_VAR = "_ATOMGIT_COMPLETE"
_PROGRAM_NAME = "atomgit"
_START_MARKER = "# >>> atomgit completion >>>"
_END_MARKER = "# <<< atomgit completion <<<"
_FINAL_NEWLINE_MARKER = "# atomgit-original-final-newline:"
_UNSET = object()
_ACTIVATION_WARNING = """[AtomGit] 检测到 atomgit 已通过 pip 卸载，但当前环境仍有补全配置。

请执行官方清理命令：
  curl -fsSL https://raw.githubusercontent.com/JoyJeeo/atomgit_cli/yuto/uninstall.sh | sh

当前 shell 中已加载的补全需要重新启动 Zsh：
  exec zsh
"""


class CompletionConfigError(RuntimeError):
    """A shell completion file cannot be managed without risking user data."""


def completion_script(command, shell):
    """Return Click's dynamic adapter for a supported shell."""
    completion_class = get_completion_class(shell)
    if shell not in SUPPORTED_SHELLS or completion_class is None:
        raise CompletionConfigError(f"不支持的 shell: {shell}")
    return completion_class(
        command,
        {},
        _PROGRAM_NAME,
        _COMPLETE_VAR,
    ).source()


def _completion_path():
    return Path.home() / ".atomgit" / "completions" / "atomgit.zsh"


def _active_conda_prefix():
    try:
        prefix = active_conda_prefix(python_prefix=sys.prefix)
    except UninstallError as error:
        raise CompletionConfigError(str(error)) from error
    if prefix is None:
        raise CompletionConfigError(
            "Zsh 补全仅安装到当前 conda 环境；请先激活目标 conda 环境"
        )
    return prefix


def _ensure_managed_directory(prefix, directory):
    try:
        relative = directory.relative_to(prefix)
    except ValueError as error:
        raise CompletionConfigError(
            f"受控目录位于 conda 环境之外: {directory}"
        ) from error
    current = prefix
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise CompletionConfigError(f"拒绝使用符号链接目录: {current}")
        if current.exists():
            if not current.is_dir():
                raise CompletionConfigError(f"受控路径不是目录: {current}")
            continue
        try:
            current.mkdir(mode=0o755)
        except FileExistsError:
            if current.is_symlink() or not current.is_dir():
                raise CompletionConfigError(f"受控路径不是安全目录: {current}")
        except OSError as error:
            raise CompletionConfigError(
                f"无法创建受控目录 {current}: {error}"
            ) from error


def _activation_hook():
    warning = _ACTIVATION_WARNING.rstrip("\n")
    return f"""# Managed by AtomGit CLI. Do not edit.
if [ -x "$CONDA_PREFIX/bin/python" ] && ! "$CONDA_PREFIX/bin/python" -c 'import importlib.metadata as m; m.distribution("atomgit")' >/dev/null 2>&1; then
    cat >&2 <<'ATOMGIT_WARNING'
{warning}
ATOMGIT_WARNING
elif [ -n "${{ZSH_VERSION:-}}" ]; then
    if (( $+functions[_atomgit_completion] )); then
        unfunction _atomgit_completion 2>/dev/null || true
    fi
    if (( $+functions[compdef] )); then
        compdef -d atomgit 2>/dev/null || true
    fi
    autoload -Uz compinit
    (( $+functions[compdef] )) || compinit
    source "$CONDA_PREFIX/share/atomgit/completions/atomgit.zsh"
    export ATOMGIT_COMPLETION_PREFIX="$CONDA_PREFIX"
fi
"""


def _deactivation_hook():
    return """# Managed by AtomGit CLI. Do not edit.
if [ -n "${ZSH_VERSION:-}" ]; then
    if (( $+functions[compdef] )); then
        compdef -d atomgit 2>/dev/null || true
    fi
    if (( $+functions[_atomgit_completion] )); then
        unfunction _atomgit_completion 2>/dev/null || true
    fi
fi
unset ATOMGIT_COMPLETION_PREFIX
"""


def _zshrc_path():
    zdotdir = os.environ.get("ZDOTDIR")
    if not zdotdir:
        return Path.home() / ".zshrc"
    path = Path(zdotdir).expanduser()
    if not path.is_absolute():
        raise CompletionConfigError("ZDOTDIR 必须是绝对路径")
    return path / ".zshrc"


def _ensure_directory(path, enforce_private=False):
    if path.is_symlink():
        raise CompletionConfigError(f"拒绝使用符号链接目录: {path}")
    if path.exists() and not path.is_dir():
        raise CompletionConfigError(f"补全目录不是普通目录: {path}")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if enforce_private:
        path.chmod(0o700)


def _file_fingerprint(file_stat):
    return (
        file_stat.st_dev,
        file_stat.st_ino,
        file_stat.st_mode,
        file_stat.st_uid,
        file_stat.st_gid,
        file_stat.st_size,
        file_stat.st_mtime_ns,
    )


def _read_snapshot(path, description):
    try:
        before = path.lstat()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise CompletionConfigError(f"无法检查{description} {path}: {error}") from error
    if stat.S_ISLNK(before.st_mode):
        raise CompletionConfigError(f"拒绝使用符号链接{description}: {path}")
    if not stat.S_ISREG(before.st_mode):
        raise CompletionConfigError(f"{description}不是普通文件: {path}")
    try:
        content = path.read_text(encoding="utf-8")
        after = path.lstat()
    except (FileNotFoundError, UnicodeError) as error:
        raise CompletionConfigError(f"读取期间{description}发生变化: {path}") from error
    except OSError as error:
        raise CompletionConfigError(f"无法读取{description} {path}: {error}") from error
    before_fingerprint = _file_fingerprint(before)
    after_fingerprint = _file_fingerprint(after)
    if before_fingerprint != after_fingerprint:
        raise CompletionConfigError(f"读取期间{description}发生变化: {path}")
    return content, stat.S_IMODE(after.st_mode), after_fingerprint


def _atomic_write(
    path,
    content,
    mode,
    enforce_private_parent=False,
    expected_snapshot=_UNSET,
):
    if path.is_symlink():
        raise CompletionConfigError(f"拒绝覆盖符号链接: {path}")
    if path.exists() and not path.is_file():
        raise CompletionConfigError(f"目标不是普通文件: {path}")
    _ensure_directory(path.parent, enforce_private_parent)
    file_descriptor = None
    temporary_path = None
    written_snapshot = None
    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
        )
        temporary_path = Path(temporary_name)
        os.fchmod(file_descriptor, mode)
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="") as file:
            file_descriptor = None
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
            written_stat = os.fstat(file.fileno())
            written_snapshot = (
                content,
                stat.S_IMODE(written_stat.st_mode),
                _file_fingerprint(written_stat),
            )
        if (
            expected_snapshot is not _UNSET
            and _read_snapshot(path, "目标文件") != expected_snapshot
        ):
            raise CompletionConfigError(f"目标文件已被并发修改，未覆盖: {path}")
        os.replace(str(temporary_path), str(path))
        temporary_path = None
    except OSError as error:
        raise CompletionConfigError(f"无法写入 {path}: {error}") from error
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                pass
    return written_snapshot


def _write_backup_once(path, source_snapshot):
    if path.is_symlink():
        raise CompletionConfigError(f"拒绝使用符号链接备份: {path}")
    if path.exists():
        if not path.is_file():
            raise CompletionConfigError(f"Zsh 配置备份不是普通文件: {path}")
        return None

    content, mode, _ = source_snapshot
    file_descriptor = None
    created = False
    backup_snapshot = None
    try:
        file_descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        created = True
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="") as file:
            file_descriptor = None
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
            written_stat = os.fstat(file.fileno())
            backup_snapshot = (
                content,
                stat.S_IMODE(written_stat.st_mode),
                _file_fingerprint(written_stat),
            )
    except FileExistsError:
        if path.is_symlink() or not path.is_file():
            raise CompletionConfigError(f"Zsh 配置备份不是安全的普通文件: {path}")
        return None
    except OSError as error:
        if created:
            try:
                path.unlink()
            except OSError:
                pass
        raise CompletionConfigError(f"无法备份 Zsh 配置 {path}: {error}") from error
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
    return backup_snapshot


def _remove_if_unchanged(path, expected_snapshot, description):
    if _read_snapshot(path, description) != expected_snapshot:
        raise CompletionConfigError(f"{description}已被并发修改，未删除: {path}")
    try:
        path.unlink()
    except OSError as error:
        raise CompletionConfigError(f"无法删除{description} {path}: {error}") from error


def _split_managed_block(content):
    start_count = content.count(_START_MARKER)
    end_count = content.count(_END_MARKER)
    if start_count == end_count == 0:
        return content, None
    if start_count != 1 or end_count != 1:
        raise CompletionConfigError(".zshrc 中的 AtomGit 补全标记不完整或重复")
    start = content.index(_START_MARKER)
    try:
        end = content.index(_END_MARKER, start) + len(_END_MARKER)
    except ValueError as error:
        raise CompletionConfigError(
            ".zshrc 中的 AtomGit 补全结束标记位于开始标记之前"
        ) from error
    if content[end : end + 1] == "\n":
        end += 1
    block = content[start:end]
    prefix = content[:start]
    suffix = content[end:]
    marker_lines = [
        line for line in block.splitlines() if line.startswith(_FINAL_NEWLINE_MARKER)
    ]
    if len(marker_lines) != 1:
        raise CompletionConfigError(".zshrc 中的 AtomGit 补全元数据无效")
    marker_value = marker_lines[0].partition(":")[2].strip()
    if marker_value not in {"0", "1"}:
        raise CompletionConfigError(".zshrc 中的 AtomGit 换行元数据无效")
    if marker_value == "0" and prefix.endswith("\n") and not suffix:
        prefix = prefix[:-1]
    return prefix + suffix, marker_value == "1"


def _managed_block(script_path, had_final_newline):
    quoted_path = shlex.quote(str(script_path))
    return "\n".join(
        (
            _START_MARKER,
            f"{_FINAL_NEWLINE_MARKER} {1 if had_final_newline else 0}",
            "autoload -Uz compinit",
            "(( $+functions[compdef] )) || compinit",
            f"source {quoted_path}",
            _END_MARKER,
            "",
        )
    )


def legacy_completion_present():
    """Return whether the pre-1.1.1 global completion owns any state."""
    script_path = _completion_path()
    if script_path.is_symlink():
        raise CompletionConfigError(f"拒绝使用符号链接旧补全脚本: {script_path}")
    if script_path.exists():
        if not script_path.is_file():
            raise CompletionConfigError(f"旧补全脚本不是普通文件: {script_path}")
        return True
    snapshot = _read_snapshot(_zshrc_path(), "Zsh 配置")
    if snapshot is None:
        return False
    _, managed = _split_managed_block(snapshot[0])
    return managed is not None


def _remove_legacy_completion():
    script_path = _completion_path()
    zshrc_path = _zshrc_path()
    zshrc_snapshot = _read_snapshot(zshrc_path, "Zsh 配置")
    script_snapshot = _read_snapshot(script_path, "旧补全脚本")
    written_zshrc = None
    try:
        if zshrc_snapshot is not None:
            updated, had_final_newline = _split_managed_block(zshrc_snapshot[0])
            if had_final_newline is not None:
                if had_final_newline and updated and not updated.endswith("\n"):
                    updated += "\n"
                _write_backup_once(
                    zshrc_path.with_name(zshrc_path.name + ".atomgit.bak"),
                    zshrc_snapshot,
                )
                written_zshrc = _atomic_write(
                    zshrc_path,
                    updated,
                    zshrc_snapshot[1],
                    expected_snapshot=zshrc_snapshot,
                )
        if script_snapshot is not None:
            _remove_if_unchanged(script_path, script_snapshot, "旧补全脚本")
    except CompletionConfigError as error:
        if written_zshrc is not None:
            try:
                _atomic_write(
                    zshrc_path,
                    zshrc_snapshot[0],
                    zshrc_snapshot[1],
                    expected_snapshot=written_zshrc,
                )
            except CompletionConfigError as rollback_error:
                raise CompletionConfigError(
                    f"{error}; 旧版 .zshrc 迁移回滚失败: {rollback_error}"
                ) from error
        raise


def install_completion(command, shell="zsh", migrate_legacy=False):
    """Install completion and activation hooks in the active conda environment."""
    if legacy_completion_present() and not migrate_legacy:
        raise CompletionConfigError(
            "检测到旧版全局补全；需要明确确认迁移后才能安装环境级补全"
        )
    prefix = _active_conda_prefix()
    paths = managed_completion_paths(prefix)
    contents = (
        completion_script(command, shell),
        _activation_hook(),
        _deactivation_hook(),
    )
    snapshots = tuple(_read_snapshot(path, "受控补全文件") for path in paths)
    written = []
    try:
        for path, content, prior in zip(paths, contents, snapshots):
            _ensure_managed_directory(prefix, path.parent)
            written_snapshot = _atomic_write(
                path,
                content,
                0o644,
                expected_snapshot=prior,
            )
            written.append((path, prior, written_snapshot))
        if migrate_legacy:
            _remove_legacy_completion()
    except (CompletionConfigError, OSError) as error:
        rollback_errors = []
        for path, prior, current in reversed(written):
            try:
                if prior is None:
                    _remove_if_unchanged(path, current, "受控补全文件")
                else:
                    _atomic_write(
                        path,
                        prior[0],
                        prior[1],
                        expected_snapshot=current,
                    )
            except CompletionConfigError as rollback_error:
                rollback_errors.append(str(rollback_error))
        detail = (
            f"; 安装回滚不完整: {'; '.join(rollback_errors)}" if rollback_errors else ""
        )
        raise CompletionConfigError(f"{error}{detail}") from error
    return paths


def uninstall_completion(shell="zsh"):
    """Remove only active-environment completion files."""
    if shell not in SUPPORTED_SHELLS:
        raise CompletionConfigError(f"不支持的 shell: {shell}")
    prefix = _active_conda_prefix()
    try:
        remove_managed_completion(prefix)
    except UninstallError as error:
        raise CompletionConfigError(str(error)) from error
    return managed_completion_paths(prefix)
