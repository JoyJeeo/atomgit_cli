"""Generate and safely manage AtomGit's Zsh completion adapter."""

import os
import shlex
import stat
import tempfile
from pathlib import Path

from click.shell_completion import get_completion_class


SUPPORTED_SHELLS = ("zsh",)
_COMPLETE_VAR = "_ATOMGIT_COMPLETE"
_PROGRAM_NAME = "atomgit"
_START_MARKER = "# >>> atomgit completion >>>"
_END_MARKER = "# <<< atomgit completion <<<"
_FINAL_NEWLINE_MARKER = "# atomgit-original-final-newline:"
_UNSET = object()


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


def _rollback_install(
    script_path,
    prior_script_snapshot,
    installed_script_snapshot,
    backup_path,
    created_backup_snapshot,
):
    errors = []
    if installed_script_snapshot is not None:
        try:
            if prior_script_snapshot is None:
                _remove_if_unchanged(
                    script_path,
                    installed_script_snapshot,
                    "补全脚本",
                )
            else:
                _atomic_write(
                    script_path,
                    prior_script_snapshot[0],
                    prior_script_snapshot[1],
                    enforce_private_parent=True,
                    expected_snapshot=installed_script_snapshot,
                )
        except CompletionConfigError as error:
            errors.append(str(error))
    if created_backup_snapshot is not None:
        try:
            _remove_if_unchanged(
                backup_path,
                created_backup_snapshot,
                "Zsh 配置备份",
            )
        except CompletionConfigError as error:
            errors.append(str(error))
    return errors


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


def install_completion(command, shell="zsh"):
    """Install one managed Zsh adapter and startup-file block."""
    script = completion_script(command, shell)
    script_path = _completion_path()
    zshrc_path = _zshrc_path()
    zshrc_snapshot = _read_snapshot(zshrc_path, "Zsh 配置")
    original = zshrc_snapshot[0] if zshrc_snapshot is not None else ""
    unmanaged, prior_final_newline = _split_managed_block(original)
    had_final_newline = (
        prior_final_newline
        if prior_final_newline is not None
        else original.endswith("\n")
    )
    separator = "" if not unmanaged or unmanaged.endswith("\n") else "\n"
    updated = unmanaged + separator + _managed_block(script_path, had_final_newline)

    zshrc_mode = zshrc_snapshot[1] if zshrc_snapshot is not None else 0o600
    backup_path = zshrc_path.with_name(zshrc_path.name + ".atomgit.bak")
    prior_script_snapshot = _read_snapshot(script_path, "补全脚本")

    _ensure_directory(script_path.parent.parent, enforce_private=True)
    _ensure_directory(script_path.parent, enforce_private=True)
    created_backup_snapshot = None
    if zshrc_snapshot is not None:
        created_backup_snapshot = _write_backup_once(backup_path, zshrc_snapshot)
    installed_script_snapshot = None
    try:
        installed_script_snapshot = _atomic_write(
            script_path,
            script,
            0o600,
            enforce_private_parent=True,
            expected_snapshot=prior_script_snapshot,
        )
        _atomic_write(
            zshrc_path,
            updated,
            zshrc_mode,
            expected_snapshot=zshrc_snapshot,
        )
    except CompletionConfigError as error:
        rollback_errors = _rollback_install(
            script_path,
            prior_script_snapshot,
            installed_script_snapshot,
            backup_path,
            created_backup_snapshot,
        )
        if rollback_errors:
            detail = "; ".join(rollback_errors)
            raise CompletionConfigError(f"{error}; 安装回滚不完整: {detail}") from error
        raise
    return script_path, zshrc_path


def uninstall_completion(shell="zsh"):
    """Remove only AtomGit-managed Zsh completion content."""
    if shell not in SUPPORTED_SHELLS:
        raise CompletionConfigError(f"不支持的 shell: {shell}")
    script_path = _completion_path()
    zshrc_path = _zshrc_path()
    zshrc_snapshot = _read_snapshot(zshrc_path, "Zsh 配置")
    if zshrc_snapshot is not None:
        original = zshrc_snapshot[0]
        updated, had_final_newline = _split_managed_block(original)
        if had_final_newline is not None:
            if had_final_newline and updated and not updated.endswith("\n"):
                updated += "\n"
            _atomic_write(
                zshrc_path,
                updated,
                zshrc_snapshot[1],
                expected_snapshot=zshrc_snapshot,
            )
    if script_path.is_symlink():
        raise CompletionConfigError(f"拒绝删除符号链接补全脚本: {script_path}")
    if script_path.exists():
        if not script_path.is_file():
            raise CompletionConfigError(f"补全脚本不是普通文件: {script_path}")
        try:
            script_path.unlink()
        except OSError as error:
            raise CompletionConfigError(f"无法删除补全脚本 {script_path}: {error}") from error
    return script_path, zshrc_path
