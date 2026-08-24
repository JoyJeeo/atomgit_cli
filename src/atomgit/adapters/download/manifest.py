"""Canonical private managed-checkout manifest adapter."""

import errno
import hashlib
import json
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from .prune import _repository_filename_parts
from .transport import _atomgit_hf_endpoint

_DOWNLOAD_MANIFEST_VERSION = 1
_DOWNLOAD_MANIFEST_MAX_BYTES = 10 * 1024 * 1024


def _set_private_file_mode(file_descriptor: int, path: Path) -> None:
    """Set private mode on Unix and pre-3.13 Windows Python."""
    fchmod = getattr(os, "fchmod", None)
    if callable(fchmod):
        fchmod(file_descriptor, 0o600)
    else:
        os.chmod(path, 0o600)


def _download_manifest_root() -> Path:
    """Return the private state directory for repository download manifests."""
    hf_home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "atomgit"))
    root = hf_home / "download-manifests"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("下载 manifest 缓存目录不安全")
    os.chmod(root, 0o700)
    return root


def _download_manifest_path(repo_id: str, repo_type: str, local_root: Path) -> Path:
    """Return a credential-free opaque manifest path for one local checkout."""
    identity = "\0".join(
        (
            _atomgit_hf_endpoint(),
            repo_id,
            repo_type,
            str(Path(local_root).resolve()),
        )
    ).encode("utf-8")
    return _download_manifest_root() / f"{hashlib.sha256(identity).hexdigest()}.json"


def _load_download_manifest(manifest_path: Path) -> tuple:
    """Load and validate managed repository filenames, failing closed."""
    descriptor = None
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(str(manifest_path), flags)
    except FileNotFoundError:
        return False, set()
    except OSError as error:
        if manifest_path.is_symlink():
            raise ValueError("下载 manifest 不是普通文件") from error
        raise
    try:
        file_status = os.fstat(descriptor)
        if not stat.S_ISREG(file_status.st_mode):
            raise ValueError("下载 manifest 不是普通文件")
        if file_status.st_size > _DOWNLOAD_MANIFEST_MAX_BYTES:
            raise ValueError("下载 manifest 过大，已拒绝清理")
        try:
            with os.fdopen(descriptor, "r", encoding="utf-8") as manifest_file:
                descriptor = None
                payload = json.load(manifest_file)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("下载 manifest 无效，已拒绝清理") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if (
        not isinstance(payload, dict)
        or payload.get("version") != _DOWNLOAD_MANIFEST_VERSION
        or not isinstance(payload.get("files"), list)
    ):
        raise ValueError("下载 manifest 格式不受支持，已拒绝清理")
    managed_files = set()
    for filename in payload["files"]:
        _repository_filename_parts(filename)
        managed_files.add(filename)
    return True, managed_files


def _write_download_manifest(manifest_path: Path, managed_files) -> None:
    """Atomically persist managed filenames with restrictive permissions."""
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=f".{manifest_path.name}.",
            suffix=".tmp",
            dir=manifest_path.parent,
            delete=False,
        ) as manifest_file:
            temporary_path = Path(manifest_file.name)
            _set_private_file_mode(manifest_file.fileno(), temporary_path)
            json.dump(
                {
                    "version": _DOWNLOAD_MANIFEST_VERSION,
                    "files": sorted(managed_files),
                },
                manifest_file,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            manifest_file.write("\n")
            manifest_file.flush()
            os.fsync(manifest_file.fileno())
        temporary_path.replace(manifest_path)
        os.chmod(manifest_path, 0o600)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _windows_file_lock_module():
    """Load the Windows byte-range locking module only on Windows."""
    import msvcrt

    return msvcrt


def _try_lock_download_manifest_descriptor_windows(
    descriptor: int,
) -> bool:
    """Acquire a nonblocking one-byte Windows lock."""
    locking = _windows_file_lock_module()
    if os.fstat(descriptor).st_size == 0:
        os.write(descriptor, b"\0")
    os.lseek(descriptor, 0, os.SEEK_SET)
    try:
        locking.locking(descriptor, locking.LK_NBLCK, 1)
    except OSError as error:
        busy_errors = {errno.EACCES, errno.EAGAIN}
        if hasattr(errno, "EDEADLK"):
            busy_errors.add(errno.EDEADLK)
        if error.errno in busy_errors:
            return False
        raise
    return True


def _unlock_download_manifest_descriptor_windows(descriptor: int) -> None:
    """Release a Windows one-byte manifest lock."""
    locking = _windows_file_lock_module()
    os.lseek(descriptor, 0, os.SEEK_SET)
    locking.locking(descriptor, locking.LK_UNLCK, 1)


def _try_lock_download_manifest_descriptor(
    descriptor: int,
) -> Optional[str]:
    """Acquire one nonblocking OS advisory lock and return its backend."""
    if os.name == "nt":
        if not _try_lock_download_manifest_descriptor_windows(descriptor):
            return None
        return "windows"

    import fcntl

    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        if error.errno in (errno.EACCES, errno.EAGAIN):
            return None
        raise
    return "posix"


def _unlock_download_manifest_descriptor(descriptor: int, backend: str) -> None:
    """Release an advisory manifest lock acquired by the selected backend."""
    if backend == "windows":
        _unlock_download_manifest_descriptor_windows(descriptor)
        return

    import fcntl

    fcntl.flock(descriptor, fcntl.LOCK_UN)


@contextmanager
def _download_manifest_lock(manifest_path: Path):
    """Hold one OS-released transaction lock for an opaque manifest."""
    lock_path = manifest_path.with_name(manifest_path.name + ".lock")
    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(str(lock_path), flags, 0o600)
    backend = None
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("下载 manifest 锁不是普通文件")
        _set_private_file_mode(descriptor, lock_path)
        backend = _try_lock_download_manifest_descriptor(descriptor)
        if backend is None:
            raise RuntimeError("download manifest is already in use")
        yield
    finally:
        try:
            if backend is not None:
                _unlock_download_manifest_descriptor(descriptor, backend)
        finally:
            os.close(descriptor)
