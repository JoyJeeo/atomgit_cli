from typing import Optional, Dict, Any, List, Set
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import quote, urljoin, urlsplit
from contextlib import ExitStack, contextmanager
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import errno
import hashlib
import ntpath
import os
import random
import shutil
import json
import socket
import ssl
import stat
import urllib.request
import urllib.error
import multiprocessing
import tempfile
import time

import httpx
import huggingface_hub._upload_large_folder as hf_large_folder


_ATOMGIT_V5_API_BASE = "https://api.atomgit.com/api/v5"
_ATOMGIT_V5_MAX_JSON_BYTES = 10 * 1024 * 1024
_ATOMGIT_IDENTITY_MAX_JSON_BYTES = 1024 * 1024

try:
    from .runtime import configure_hf_environment
except ImportError:
    from runtime import configure_hf_environment

configure_hf_environment()


from huggingface_hub import (
    get_hf_file_metadata, hf_hub_download, upload_folder, create_repo, snapshot_download,
    constants as hf_constants, HfApi, close_session as close_hf_session,
)
from huggingface_hub.file_download import http_get as hf_http_get
from huggingface_hub._local_folder import (
    get_local_upload_paths,
    read_upload_metadata,
)

try:
    from .config import config
    from .utils import (
        auth_error_kind,
        is_auth_error,
        is_supported_upload_revision,
        normalize_repo_id,
        normalize_path_in_repo,
        parse_ignore_patterns,
        run_download_with_retry,
        sanitized_download_error,
        validate_upload_path_no_symlinks,
    )
except ImportError:
    from config import config
    from utils import (
        auth_error_kind,
        is_auth_error,
        is_supported_upload_revision,
        normalize_repo_id,
        normalize_path_in_repo,
        parse_ignore_patterns,
        run_download_with_retry,
        sanitized_download_error,
        validate_upload_path_no_symlinks,
    )

try:
    # 单文件上传专用：直接以 path_or_fileobj 上传，避免本地拷贝
    from huggingface_hub import upload_file as hf_upload_file
except ImportError:  # 老版本兜底
    hf_upload_file = None

try:
    # huggingface_hub >= 0.14 提供的进度条程序化开关
    from huggingface_hub.utils import (
        are_progress_bars_disabled,
        disable_progress_bars,
        enable_progress_bars,
        filter_repo_objects,
    )
    try:
        from huggingface_hub.utils.tqdm import progress_bar_states
    except ImportError:
        progress_bar_states = None
except ImportError:  # 老版本无此 API 时，提供 no-op 回退，保证可用
    progress_bar_states = None

    def are_progress_bars_disabled(*args, **kwargs):
        return False

    def enable_progress_bars(*args, **kwargs):
        pass

    def disable_progress_bars(*args, **kwargs):
        pass

    def filter_repo_objects(items, *, ignore_patterns=None, key=None, **kwargs):
        return items


def _set_progress_bar(enabled: bool) -> None:
    """控制 Hugging Face Hub 上传过程中的进度条显示。

    注意：此为进程级全局状态（HF Hub 的设计）。
    - enabled=True  时显式开启进度条（防御性兜底，覆盖任何先前禁用）；
    - enabled=False 时关闭进度条（适用于日志/CI 等非交互场景）。

    若环境变量 HF_HUB_DISABLE_PROGRESS_BARS=1 在 import 前已设置，则其优先级最高，
    程序化开关将被忽略（HF Hub 既定行为）。
    """
    try:
        if enabled:
            enable_progress_bars()
        else:
            disable_progress_bars()
    except Exception:
        # 进度条控制不应影响上传主流程
        pass


def _capture_progress_bar_state():
    if progress_bar_states is not None:
        return dict(progress_bar_states)
    return are_progress_bars_disabled()


def _restore_progress_bar_state(state) -> None:
    if progress_bar_states is not None and isinstance(state, dict):
        progress_bar_states.clear()
        progress_bar_states.update(state)
        return
    _set_progress_bar(not state)


def _atomgit_repo_type(repo_type: str = None) -> str:
    """Map dataset create/transfer calls to AtomGit's shared model route."""
    return "model" if repo_type == "dataset" else repo_type


def _atomgit_hf_endpoint() -> str:
    """AtomGit HF-compatible endpoint from the shared runtime policy."""
    return os.environ.get("HF_ENDPOINT", "https://hub.atomgit.com")


def _atomgit_resolve_url(repo_id: str, repo_type: str, filename: str) -> str:
    """Build a direct resolve URL that bypasses the missing repo_info route."""
    endpoint = _atomgit_hf_endpoint()
    prefix = "datasets/" if repo_type == "dataset" else ""
    # 文件名必须百分号编码（保留 / 分隔子目录），否则 urllib 发送
    # 请求行时按 ASCII 编码，中文文件名会抛 UnicodeEncodeError。
    encoded_filename = quote(filename, safe="/")
    return f"{endpoint}/{prefix}{repo_id}/resolve/main/{encoded_filename}"


class DownloadChecksumMismatchError(OSError):
    """Downloaded or existing bytes do not match repository metadata."""


class DownloadChecksumMetadataError(ValueError):
    """AtomGit did not provide a supported strong checksum."""


def _atomgit_file_checksum(
    repo_id: str, repo_type: str, filename: str, token: str
) -> tuple:
    """Return (algorithm, digest, size) from AtomGit resolve metadata."""
    checksum, _ = _atomgit_file_download_metadata(
        repo_id, repo_type, filename, token
    )
    return checksum


def _checksum_from_hf_metadata(metadata) -> tuple:
    """Validate one locked HF metadata response as a strong checksum."""
    return _checksum_from_metadata_values(metadata.etag, metadata.size)


def _checksum_from_metadata_values(etag, size) -> tuple:
    """Validate raw metadata values using the shared strong checksum policy."""
    if (
        not isinstance(etag, str)
        or not isinstance(size, int)
        or isinstance(size, bool)
        or size < 0
    ):
        raise DownloadChecksumMetadataError("checksum metadata is unavailable")
    digest = etag.strip().strip('"').lower()
    if not digest or any(character not in "0123456789abcdef" for character in digest):
        raise DownloadChecksumMetadataError("checksum metadata is unsupported")
    if len(digest) == 64:
        algorithm = "sha256"
    elif len(digest) == 40:
        algorithm = "git-sha1"
    else:
        raise DownloadChecksumMetadataError("checksum metadata is unsupported")
    return algorithm, digest, size


def _atomgit_file_download_metadata(
    repo_id: str, repo_type: str, filename: str, token: str
) -> tuple:
    """Return a strong checksum and current credential-safe download URL."""
    resolve_url = _atomgit_resolve_url(repo_id, repo_type, filename)
    try:
        metadata = get_hf_file_metadata(
            resolve_url,
            token=token if token else False,
            timeout=60,
            endpoint=_atomgit_hf_endpoint(),
        )
    except Exception as error:
        if filename.isascii() or not _is_not_found_error(error):
            raise
        return _atomgit_file_download_metadata_raw(
            repo_id, repo_type, filename, token
        )
    checksum = _checksum_from_hf_metadata(metadata)
    location = urljoin(
        resolve_url, getattr(metadata, "location", None) or resolve_url
    )
    _download_url_origin(location)
    return checksum, location


def _verify_download_checksum(path: Path, checksum: tuple) -> bool:
    """Stream-hash one local file using a strong AtomGit checksum contract."""
    algorithm, expected_digest, expected_size = checksum
    try:
        actual_size = path.stat().st_size
    except OSError as error:
        raise DownloadChecksumMismatchError("checksum mismatch") from error
    if actual_size != expected_size:
        raise DownloadChecksumMismatchError("checksum mismatch")

    if algorithm == "sha256":
        digest = hashlib.sha256()
    elif algorithm == "git-sha1":
        digest = hashlib.sha1()
        digest.update(b"blob " + str(actual_size).encode("ascii") + b"\0")
    else:
        raise DownloadChecksumMetadataError("checksum metadata is unsupported")

    bytes_read = 0
    try:
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                bytes_read += len(chunk)
    except OSError as error:
        raise DownloadChecksumMismatchError("checksum mismatch") from error
    if bytes_read != expected_size or digest.hexdigest() != expected_digest:
        raise DownloadChecksumMismatchError("checksum mismatch")
    return True


def _resume_cache_root() -> Path:
    """Return the private cache used only for incomplete CLI downloads."""
    hf_home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "atomgit"))
    root = hf_home / "resume"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    return root


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


def _download_manifest_path(
    repo_id: str, repo_type: str, local_root: Path
) -> Path:
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


def _unlock_download_manifest_descriptor(
    descriptor: int, backend: str
) -> None:
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


def _resume_cache_identity(
    repo_id: str, repo_type: str, filename: str
) -> str:
    identity = "\0".join(
        (_atomgit_hf_endpoint(), repo_id, repo_type, filename)
    ).encode("utf-8")
    return hashlib.sha256(identity).hexdigest()


def _process_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


@contextmanager
def _resume_download_lock(lock_path: Path):
    """Serialize writers while recovering locks left by dead processes."""
    descriptor = None
    for _ in range(2):
        try:
            descriptor = os.open(
                str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600
            )
            try:
                os.write(descriptor, str(os.getpid()).encode("ascii"))
            except Exception:
                os.close(descriptor)
                descriptor = None
                lock_path.unlink(missing_ok=True)
                raise
            break
        except FileExistsError:
            try:
                owner = int(lock_path.read_text(encoding="ascii").strip())
            except (OSError, ValueError):
                try:
                    lock_age = time.time() - lock_path.stat().st_mtime
                except OSError:
                    lock_age = 0
                if lock_age < 60:
                    raise RuntimeError("download resume is already in progress")
                owner = -1
            if _process_is_running(owner):
                raise RuntimeError("download resume is already in progress")
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass
    if descriptor is None:
        raise RuntimeError("unable to acquire download resume lock")
    try:
        yield
    finally:
        os.close(descriptor)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _copy_resumed_file_to_destination(
    partial_path: Path, destination: Path, checksum: tuple
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{destination.name}.",
            suffix=".part",
            dir=destination.parent,
            delete=False,
        ) as output:
            temporary_path = Path(output.name)
            with partial_path.open("rb") as source:
                shutil.copyfileobj(source, output)
        _verify_download_checksum(temporary_path, checksum)
        temporary_path.replace(destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _parse_content_range(value: str, expected_start: int, expected_size: int) -> None:
    try:
        unit, value = value.split(" ", 1)
        byte_range, total = value.split("/", 1)
        start, end = byte_range.split("-", 1)
        start, end, total = int(start), int(end), int(total)
    except (AttributeError, TypeError, ValueError) as error:
        raise urllib.error.URLError("invalid resume Content-Range") from error
    if (
        unit.lower() != "bytes"
        or start != expected_start
        or end < start
        or total != expected_size
    ):
        raise urllib.error.URLError("unexpected resume Content-Range")


def _atomgit_resume_raw(
    url: str,
    partial_stream,
    headers,
    resume_size: int,
    expected_size: int,
    timeout: int = 60,
    max_redirects: int = 5,
) -> None:
    """Resume a raw UTF-8-path response with strict range validation."""
    current_url = url
    current_headers = dict(headers)
    if resume_size:
        current_headers["Range"] = f"bytes={resume_size}-"
    for _ in range(max_redirects + 1):
        parts = urlsplit(current_url)
        host = parts.hostname
        port = parts.port or (443 if parts.scheme == "https" else 80)
        raw_path = (parts.path + (("?" + parts.query) if parts.query else "")).encode("utf-8")
        status, response_headers, body, sock = _atomgit_raw_http_get(
            host, port, parts.scheme, raw_path, current_headers, timeout
        )
        try:
            if status in (301, 302, 303, 307, 308):
                location = response_headers.get("location")
                if not location:
                    raise urllib.error.HTTPError(
                        current_url, status, "Redirect without Location",
                        response_headers, None,
                    )
                current_url, current_headers = _prepare_download_redirect(
                    current_url, location, current_headers
                )
                continue
            if resume_size and status == 206:
                _parse_content_range(
                    response_headers.get("content-range"), resume_size,
                    expected_size,
                )
            elif resume_size and status == 200:
                partial_stream.seek(0)
                partial_stream.truncate()
                resume_size = 0
            elif not 200 <= status < 300:
                raise urllib.error.HTTPError(
                    current_url, status, "HTTP Error", response_headers, None
                )
            _copy_framed_http_body(body, response_headers, partial_stream)
            if partial_stream.tell() != expected_size:
                raise urllib.error.URLError("resumed download size mismatch")
            return
        finally:
            try:
                body.close()
            finally:
                sock.close()
    raise urllib.error.HTTPError(
        current_url, 302, "Too many redirects", {}, None
    )


def _download_atomgit_file_resumable(
    repo_id: str,
    repo_type: str,
    filename: str,
    destination: Path,
    token: str,
) -> None:
    """Persist an interrupted range download and atomically install it."""
    checksum, _ = _atomgit_file_download_metadata(
        repo_id, repo_type, filename, token
    )
    _, expected_digest, expected_size = checksum
    cache_root = _resume_cache_root()
    identity = _resume_cache_identity(repo_id, repo_type, filename)
    partial_path = cache_root / f"{identity}.{expected_digest}.part"
    lock_path = cache_root / f"{identity}.lock"
    headers = {"User-Agent": "atomgit-cli", "Accept": "*/*"}
    resolve_url = _atomgit_resolve_url(repo_id, repo_type, filename)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with _resume_download_lock(lock_path):
        for stale_path in cache_root.glob(f"{identity}.*.part"):
            if stale_path != partial_path:
                stale_path.unlink(missing_ok=True)
        for attempt in range(2):
            partial_path.touch(mode=0o600, exist_ok=True)
            os.chmod(partial_path, 0o600)
            if partial_path.stat().st_size > expected_size:
                partial_path.unlink()
                continue
            try:
                with partial_path.open("ab+") as partial_stream:
                    partial_stream.seek(0, os.SEEK_END)
                    resume_size = partial_stream.tell()
                    if resume_size < expected_size:
                        if filename.isascii():
                            hf_http_get(
                                resolve_url,
                                partial_stream,
                                resume_size=resume_size,
                                headers=headers,
                                expected_size=expected_size,
                                displayed_filename=filename,
                            )
                        else:
                            _atomgit_resume_raw(
                                _atomgit_resolve_url_raw(
                                    repo_id, repo_type, filename
                                ),
                                partial_stream,
                                headers,
                                resume_size,
                                expected_size,
                            )
                _verify_download_checksum(partial_path, checksum)
            except DownloadChecksumMismatchError:
                partial_path.unlink(missing_ok=True)
                if attempt == 0:
                    continue
                raise
            _copy_resumed_file_to_destination(
                partial_path, destination, checksum
            )
            partial_path.unlink(missing_ok=True)
            return
    raise RuntimeError("download resume failed")


def _is_not_found_error(error: Exception) -> bool:
    message = str(error).lower()
    return "404" in message or "not found" in message


def _atomgit_v5_request_json(
    method: str, path: str, token: str, body=None, timeout: int = 15
):
    """Exchange one bounded JSON document with AtomGit's V5 API."""
    if not token:
        raise ValueError("missing AtomGit credential")
    if not path.startswith("/") or "?" in path or "#" in path:
        raise ValueError("invalid AtomGit API path")
    method = method.upper()
    if method not in ("GET", "POST", "PATCH", "DELETE"):
        raise ValueError("unsupported AtomGit API method")
    if method == "DELETE" and body is not None:
        raise ValueError("DELETE request body is unsupported")

    data = None
    headers = {
        "PRIVATE-TOKEN": token,
        "Accept": "application/json",
        "User-Agent": "atomgit-cli",
    }
    if body is not None:
        data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        _ATOMGIT_V5_API_BASE + path,
        data=data,
        headers=headers,
        method=method,
    )
    with _atomgit_open_url(request, timeout=timeout) as response:
        payload = response.read(_ATOMGIT_V5_MAX_JSON_BYTES + 1)
    if len(payload) > _ATOMGIT_V5_MAX_JSON_BYTES:
        raise ValueError("AtomGit API response is too large")
    if not payload:
        return None
    return json.loads(payload.decode("utf-8"))


def _atomgit_v5_get_json(path: str, token: str, timeout: int = 15):
    """Read one bounded JSON document from AtomGit's authenticated V5 API."""
    return _atomgit_v5_request_json("GET", path, token, timeout=timeout)


def _atomgit_v5_repo_path(repo_id: str) -> str:
    """Build one encoded V5 repository path from the shared logical ID."""
    normalized_repo_id = normalize_repo_id(repo_id)
    owner, separator, repository = normalized_repo_id.partition("/")
    if not separator or not owner or not repository:
        raise ValueError("invalid repository ID")
    return "/repos/{}/{}".format(
        quote(owner, safe=""), quote(repository, safe="")
    )


def _repo_private_state(payload):
    """Read a public/private state from one V5 repository response."""
    if not isinstance(payload, dict):
        return None
    private = payload.get("private")
    if isinstance(private, bool):
        return private
    visibility = payload.get("visibility")
    if isinstance(visibility, str):
        normalized = visibility.strip().lower()
        if normalized == "private":
            return True
        if normalized == "public":
            return False
    return None


def _sanitized_v5_api_error(error: Exception) -> str:
    """Return a credential-safe V5 API error category."""
    if isinstance(error, urllib.error.HTTPError):
        if error.code == 401:
            return "认证失败，请重新登录"
        if error.code == 403:
            return "权限不足"
        if error.code == 404:
            return "接口或资源不存在"
        if error.code == 429:
            return "请求过于频繁，请稍后重试"
        if error.code >= 500:
            return "AtomGit 服务暂时不可用"
        return f"AtomGit API 请求失败（HTTP {error.code}）"
    if isinstance(error, (urllib.error.URLError, socket.timeout, TimeoutError)):
        return "无法连接 AtomGit API，请检查网络后重试"
    if isinstance(error, (json.JSONDecodeError, UnicodeDecodeError, ValueError)):
        return "AtomGit API 响应格式无效"
    return f"AtomGit API 请求失败（{type(error).__name__}）"


def _is_definitive_v5_write_error(error: Exception) -> bool:
    """Return whether a V5 write was definitively rejected by the server."""
    return (
        isinstance(error, urllib.error.HTTPError)
        and 400 <= error.code < 500
    )


def _atomgit_v5_commit_sha(payload: object) -> Optional[str]:
    """Extract the immutable SHA from one V5 commit response."""
    if not isinstance(payload, dict):
        return None
    sha = payload.get("sha")
    if isinstance(sha, str) and sha.strip():
        return sha.strip()
    return None


def _atomgit_v5_branch_commit_id(payload: object) -> Optional[str]:
    """Extract the immutable commit ID from one V5 branch response."""
    if not isinstance(payload, dict):
        return None
    commit = payload.get("commit")
    if not isinstance(commit, dict):
        return None
    commit_id = commit.get("id")
    if isinstance(commit_id, str) and commit_id.strip():
        return commit_id.strip()
    return None


def _atomgit_list_repo_files(repo_id: str, token: str, repo_type: str = None) -> tuple:
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
    if repo_type is not None:
        candidate = None if repo_type == "model" else "dataset"
        files = api.list_repo_files(repo_id, repo_type=candidate)
        return repo_type, list(files)

    successes = {}
    errors = []
    candidates = [("model", None), ("dataset", "dataset")]
    for effective_type, candidate in candidates:
        try:
            files = api.list_repo_files(repo_id, repo_type=candidate)
        except Exception as error:
            errors.append(error)
            continue
        successes[effective_type] = list(files)

    if successes:
        model_files = successes.get("model")
        dataset_files = successes.get("dataset")
        if model_files and dataset_files:
            if set(model_files) != set(dataset_files):
                raise ValueError(
                    "仓库类型不明确，请使用 --repo-type model 或 dataset"
                )
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


def _atomgit_repo_exists(repo_id: str, token: str) -> bool:
    """Probe AtomGit's shared repository tree before non-idempotent create."""
    try:
        HfApi(token=token).list_repo_files(repo_id, repo_type=None)
        return True
    except Exception as error:
        if _is_not_found_error(error):
            return False
        raise


def _repository_filename_parts(filename: str) -> tuple:
    """Validate a repository filename and return its POSIX path parts."""
    if not isinstance(filename, str) or not filename:
        raise ValueError("仓库文件名为空或格式无效")
    if "\\" in filename:
        raise ValueError(f"仓库文件名包含不安全的反斜杠路径: {filename!r}")
    if any(ord(character) < 32 or ord(character) == 127 for character in filename):
        raise ValueError(f"仓库文件名包含控制字符: {filename!r}")

    raw_parts = filename.split("/")
    if any(part in ("", ".", "..") for part in raw_parts):
        raise ValueError(f"仓库文件名包含不安全的路径片段: {filename!r}")

    posix_path = PurePosixPath(filename)
    windows_path = PureWindowsPath(filename)
    if posix_path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        raise ValueError(f"仓库文件名不能是绝对路径: {filename!r}")
    return tuple(raw_parts)


def _safe_download_destination(local_root: Path, filename: str) -> Path:
    """Resolve a repository filename without allowing it to escape local_root."""
    raw_parts = _repository_filename_parts(filename)

    resolved_root = Path(local_root).resolve()
    destination = resolved_root.joinpath(*raw_parts).resolve(strict=False)
    try:
        destination.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(
            f"仓库文件路径超出下载目录: {filename!r}"
        ) from error
    return destination


class _WindowsFileAPI:
    """Minimal Win32 handle API used for race-safe managed-file deletion."""

    FILE_ATTRIBUTE_DIRECTORY = 0x10
    FILE_ATTRIBUTE_REPARSE_POINT = 0x400
    _DELETE = 0x00010000
    _FILE_READ_ATTRIBUTES = 0x00000080
    _FILE_SHARE_READ_WRITE = 0x00000001 | 0x00000002
    _OPEN_EXISTING = 3
    _FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    _FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    _FILE_ATTRIBUTE_TAG_INFO_CLASS = 9
    _FILE_DISPOSITION_INFO_CLASS = 4

    def __init__(self):
        import ctypes
        from ctypes import wintypes

        if os.name != "nt":
            raise RuntimeError("Win32 file API is unavailable")

        class FileAttributeTagInfo(ctypes.Structure):
            _fields_ = [
                ("FileAttributes", wintypes.DWORD),
                ("ReparseTag", wintypes.DWORD),
            ]

        class FileDispositionInfo(ctypes.Structure):
            _fields_ = [("DeleteFile", wintypes.BOOLEAN)]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        kernel32.CreateFileW.restype = wintypes.HANDLE
        kernel32.GetFinalPathNameByHandleW.argtypes = [
            wintypes.HANDLE,
            wintypes.LPWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
        kernel32.GetFileInformationByHandleEx.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.DWORD,
        ]
        kernel32.GetFileInformationByHandleEx.restype = wintypes.BOOL
        kernel32.SetFileInformationByHandle.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.DWORD,
        ]
        kernel32.SetFileInformationByHandle.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        self._ctypes = ctypes
        self._kernel32 = kernel32
        self._attribute_info = FileAttributeTagInfo
        self._disposition_info = FileDispositionInfo
        self._invalid_handle = ctypes.c_void_p(-1).value

    def _error(self, error_code: int, path=None):
        message = self._ctypes.FormatError(error_code).strip()
        return OSError(error_code, message, path)

    def open_path(self, path, delete: bool = False):
        access = self._FILE_READ_ATTRIBUTES
        if delete:
            access |= self._DELETE
        handle = self._kernel32.CreateFileW(
            os.fspath(path),
            access,
            self._FILE_SHARE_READ_WRITE,
            None,
            self._OPEN_EXISTING,
            self._FILE_FLAG_BACKUP_SEMANTICS
            | self._FILE_FLAG_OPEN_REPARSE_POINT,
            None,
        )
        if handle == self._invalid_handle:
            error_code = self._ctypes.get_last_error()
            if error_code in (2, 3):
                raise FileNotFoundError(error_code, "path not found", path)
            raise self._error(error_code, path)
        return handle

    def final_path(self, handle) -> str:
        size = 32768
        buffer = self._ctypes.create_unicode_buffer(size)
        result = self._kernel32.GetFinalPathNameByHandleW(
            handle, buffer, size, 0
        )
        if result == 0:
            raise self._error(self._ctypes.get_last_error())
        if result >= size:
            size = result + 1
            buffer = self._ctypes.create_unicode_buffer(size)
            result = self._kernel32.GetFinalPathNameByHandleW(
                handle, buffer, size, 0
            )
            if result == 0 or result >= size:
                raise self._error(self._ctypes.get_last_error())
        return buffer.value

    def attributes(self, handle) -> int:
        information = self._attribute_info()
        if not self._kernel32.GetFileInformationByHandleEx(
            handle,
            self._FILE_ATTRIBUTE_TAG_INFO_CLASS,
            self._ctypes.byref(information),
            self._ctypes.sizeof(information),
        ):
            raise self._error(self._ctypes.get_last_error())
        return information.FileAttributes

    def mark_delete(self, handle) -> None:
        information = self._disposition_info(True)
        if not self._kernel32.SetFileInformationByHandle(
            handle,
            self._FILE_DISPOSITION_INFO_CLASS,
            self._ctypes.byref(information),
            self._ctypes.sizeof(information),
        ):
            raise self._error(self._ctypes.get_last_error())

    def close(self, handle) -> None:
        if not self._kernel32.CloseHandle(handle):
            raise self._error(self._ctypes.get_last_error())


def _normalized_windows_handle_path(path: str) -> str:
    """Normalize one trusted final Win32 handle path for containment checks."""
    if (
        not isinstance(path, str)
        or not path
        or any(ord(character) < 32 for character in path)
    ):
        raise ValueError("Windows 文件句柄路径无效")
    return ntpath.normcase(ntpath.normpath(path))


def _prune_managed_download_file_windows(
    local_root, parts, windows_api=None
) -> bool:
    """Delete one managed Windows file by verified handle, never by path."""
    if windows_api is None:
        windows_api = _WindowsFileAPI()
    root_handle = windows_api.open_path(local_root)
    directory_handles = [root_handle]
    target_handle = None
    try:
        root_attributes = windows_api.attributes(root_handle)
        if (
            not root_attributes & windows_api.FILE_ATTRIBUTE_DIRECTORY
            or root_attributes & windows_api.FILE_ATTRIBUTE_REPARSE_POINT
        ):
            raise ValueError("下载根目录不是安全的普通目录")

        root_final = _normalized_windows_handle_path(
            windows_api.final_path(root_handle)
        )
        current_path = os.fspath(local_root)
        for part in parts[:-1]:
            current_path = ntpath.join(current_path, part)
            try:
                directory_handle = windows_api.open_path(current_path)
            except FileNotFoundError:
                return False
            directory_handles.append(directory_handle)
            attributes = windows_api.attributes(directory_handle)
            if (
                not attributes & windows_api.FILE_ATTRIBUTE_DIRECTORY
                or attributes & windows_api.FILE_ATTRIBUTE_REPARSE_POINT
            ):
                raise ValueError("受管理路径包含不安全的父目录")
            directory_final = _normalized_windows_handle_path(
                windows_api.final_path(directory_handle)
            )
            try:
                inside_root = (
                    ntpath.commonpath((root_final, directory_final))
                    == root_final
                )
            except ValueError:
                inside_root = False
            if not inside_root:
                raise ValueError("受管理路径超出下载目录，已拒绝清理")

        target_path = ntpath.join(current_path, parts[-1])
        try:
            target_handle = windows_api.open_path(target_path, delete=True)
        except FileNotFoundError:
            return False

        target_attributes = windows_api.attributes(target_handle)
        if target_attributes & (
            windows_api.FILE_ATTRIBUTE_DIRECTORY
            | windows_api.FILE_ATTRIBUTE_REPARSE_POINT
        ):
            raise ValueError("受管理路径不再是普通文件，已拒绝清理")

        target_final = _normalized_windows_handle_path(
            windows_api.final_path(target_handle)
        )
        try:
            inside_root = (
                ntpath.commonpath((root_final, target_final)) == root_final
                and target_final != root_final
            )
        except ValueError:
            inside_root = False
        if not inside_root:
            raise ValueError("受管理路径超出下载目录，已拒绝清理")

        windows_api.mark_delete(target_handle)
        return True
    finally:
        try:
            if target_handle is not None:
                windows_api.close(target_handle)
        finally:
            close_error = None
            for directory_handle in reversed(directory_handles):
                try:
                    windows_api.close(directory_handle)
                except Exception as error:
                    if close_error is None:
                        close_error = error
            if close_error is not None:
                raise close_error


def _uses_windows_prune() -> bool:
    return os.name == "nt"


def _prune_managed_download_file(local_root: Path, filename: str) -> bool:
    """Delete one managed regular file without following directory symlinks."""
    parts = _repository_filename_parts(filename)
    if _uses_windows_prune():
        return _prune_managed_download_file_windows(
            Path(local_root).resolve(), parts
        )
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise RuntimeError("当前平台不支持安全的下载文件清理")
    directory_flags = os.O_RDONLY
    directory_flags |= os.O_DIRECTORY | os.O_NOFOLLOW

    descriptor = os.open(str(Path(local_root).resolve()), directory_flags)
    try:
        for part in parts[:-1]:
            try:
                next_descriptor = os.open(
                    part, directory_flags, dir_fd=descriptor
                )
            except FileNotFoundError:
                return False
            os.close(descriptor)
            descriptor = next_descriptor
        try:
            file_status = os.stat(
                parts[-1], dir_fd=descriptor, follow_symlinks=False
            )
        except FileNotFoundError:
            return False
        if not stat.S_ISREG(file_status.st_mode):
            raise ValueError(
                f"受管理路径不再是普通文件，已拒绝清理: {filename!r}"
            )
        os.unlink(parts[-1], dir_fd=descriptor)
        return True
    finally:
        os.close(descriptor)


def _prune_managed_download_files(local_root: Path, filenames) -> int:
    """Delete only previously managed regular files and leave directories."""
    removed = 0
    for filename in sorted(filenames):
        if _prune_managed_download_file(local_root, filename):
            removed += 1
    return removed


def _atomgit_resolve_url_raw(repo_id: str, repo_type: str, filename: str) -> str:
    """Build a resolve URL that keeps the raw UTF-8 filename bytes.

    AtomGit resolve cannot match percent-encoded nested paths with non-ASCII
    filenames, but serves the same file when the raw UTF-8 bytes are sent in
    the request target. urllib refuses to send raw non-ASCII paths, so this
    variant is consumed by _atomgit_download_raw below.
    """
    endpoint = _atomgit_hf_endpoint()
    prefix = "datasets/" if repo_type == "dataset" else ""
    return f"{endpoint}/{prefix}{repo_id}/resolve/main/{filename}"


def _download_url_origin(url: str) -> tuple:
    """Return a normalized origin after validating a download URL."""
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as error:
        raise urllib.error.URLError(f"invalid download URL: {error}") from error
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        raise urllib.error.URLError(
            f"unsupported download redirect scheme: {scheme or '(empty)'}"
        )
    if not parts.hostname:
        raise urllib.error.URLError("download redirect has no hostname")
    if parts.username is not None or parts.password is not None:
        raise urllib.error.URLError("download redirect must not contain credentials")
    effective_port = port or (443 if scheme == "https" else 80)
    return scheme, parts.hostname.rstrip(".").lower(), effective_port


def _prepare_download_redirect(current_url: str, location: str, headers) -> tuple:
    """Validate a redirect and remove credentials when its origin changes."""
    target_url = urljoin(current_url, location)
    current_origin = _download_url_origin(current_url)
    target_origin = _download_url_origin(target_url)
    if current_origin[0] == "https" and target_origin[0] != "https":
        raise urllib.error.URLError("refusing HTTPS-to-HTTP download redirect")

    redirected_headers = dict(headers)
    if current_origin != target_origin:
        redirected_headers = {
            key: value
            for key, value in redirected_headers.items()
            if key.lower() not in ("authorization", "private-token")
        }
    return target_url, redirected_headers


class _AtomGitRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Apply AtomGit credential isolation to urllib redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target_url, redirected_headers = _prepare_download_redirect(
            req.full_url, newurl, req.header_items()
        )
        redirected = super().redirect_request(
            req, fp, code, msg, headers, target_url
        )
        if redirected is None:
            return None
        for header_name in ("Authorization", "Private-token"):
            if not any(
                key.lower() == header_name.lower()
                for key in redirected_headers
            ):
                redirected.remove_header(header_name)
                redirected.unredirected_hdrs.pop(header_name, None)
        return redirected


def _atomgit_open_url(request, timeout=60):
    """Open a direct download with the credential-safe redirect handler."""
    opener = urllib.request.build_opener(_AtomGitRedirectHandler())
    return opener.open(request, timeout=timeout)


def _atomgit_raw_http_request(
    method, host, port, scheme, raw_path, headers, timeout
):
    """Send one bounded raw-socket request and return its response streams."""
    if method not in (b"GET", b"HEAD"):
        raise ValueError("unsupported raw HTTP method")
    context = ssl.create_default_context()
    sock = socket.create_connection((host, port), timeout=timeout)
    try:
        if scheme == "https":
            sock = context.wrap_socket(sock, server_hostname=host)
        sock.settimeout(timeout)
        sock.sendall(method + b" " + raw_path + b" HTTP/1.1\r\n")
        sock.sendall(b"Host: " + host.encode("ascii") + b"\r\n")
        for key, value in headers.items():
            if any(character in str(key) for character in "\r\n:"):
                raise urllib.error.URLError("invalid HTTP request header name")
            if any(character in str(value) for character in "\r\n"):
                raise urllib.error.URLError("invalid HTTP request header value")
            sock.sendall(key.encode("latin-1") + b": " + str(value).encode("utf-8") + b"\r\n")
        sock.sendall(b"Connection: close\r\n\r\n")
        body = sock.makefile("rb")
        status_line = body.readline(65537)
        if len(status_line) > 65536:
            raise urllib.error.URLError("HTTP status line is too long")
        if not status_line:
            raise urllib.error.URLError("empty response from " + str(host))
        try:
            status = int(status_line.decode("latin-1").split(" ", 2)[1])
        except (IndexError, ValueError) as error:
            raise urllib.error.URLError("malformed HTTP status line") from error
        response_headers = {}
        header_bytes = 0
        header_count = 0
        while True:
            line = body.readline(65537)
            if len(line) > 65536:
                raise urllib.error.URLError("HTTP response header line is too long")
            if line in (b"\r\n", b"\n", b""):
                break
            header_bytes += len(line)
            header_count += 1
            if header_bytes > 65536 or header_count > 200:
                raise urllib.error.URLError("HTTP response headers are too large")
            key, _, value = line.decode("latin-1").partition(":")
            if not key.strip() or not _:
                raise urllib.error.URLError("malformed HTTP response header")
            normalized_key = key.strip().lower()
            normalized_value = value.strip()
            if normalized_key in response_headers:
                response_headers[normalized_key] += "," + normalized_value
            else:
                response_headers[normalized_key] = normalized_value
        return status, response_headers, body, sock
    except Exception:
        sock.close()
        raise


def _atomgit_raw_http_get(host, port, scheme, raw_path, headers, timeout):
    """Send a raw-socket GET and return (status, headers, body, socket)."""
    return _atomgit_raw_http_request(
        b"GET", host, port, scheme, raw_path, headers, timeout
    )


def _atomgit_raw_http_head(host, port, scheme, raw_path, headers, timeout):
    """Send a raw-socket HEAD and return (status, headers, body, socket)."""
    return _atomgit_raw_http_request(
        b"HEAD", host, port, scheme, raw_path, headers, timeout
    )


def _raw_metadata_size(response_headers) -> int:
    """Read one unambiguous nonnegative file size from metadata headers."""
    values = []
    for name in ("x-linked-size", "content-length"):
        value = response_headers.get(name)
        if value is None:
            continue
        if not value or any(
            character not in "0123456789" for character in value
        ):
            raise DownloadChecksumMetadataError(
                "checksum metadata is unavailable"
            )
        values.append(int(value, 10))
    if not values or len(set(values)) != 1:
        raise DownloadChecksumMetadataError("checksum metadata is unavailable")
    return values[0]


def _atomgit_file_download_metadata_raw(
    repo_id: str,
    repo_type: str,
    filename: str,
    token: str,
    timeout: int = 60,
    max_redirects: int = 5,
) -> tuple:
    """Read strong metadata with a raw UTF-8 request target after a 404."""
    current_url = _atomgit_resolve_url_raw(repo_id, repo_type, filename)
    current_headers = {
        "User-Agent": "atomgit-cli",
        "Accept": "*/*",
        "Accept-Encoding": "identity",
    }
    if token:
        current_headers["Authorization"] = f"Bearer {token}"

    for _ in range(max_redirects + 1):
        parts = urlsplit(current_url)
        _download_url_origin(current_url)
        host = parts.hostname
        port = parts.port or (443 if parts.scheme == "https" else 80)
        raw_path = (
            parts.path + (("?" + parts.query) if parts.query else "")
        ).encode("utf-8")
        status, response_headers, body, sock = _atomgit_raw_http_head(
            host,
            port,
            parts.scheme,
            raw_path,
            current_headers,
            timeout,
        )
        try:
            if status in (301, 302, 303, 307, 308):
                location = response_headers.get("location")
                if not location:
                    raise urllib.error.HTTPError(
                        current_url,
                        status,
                        "Redirect without Location",
                        response_headers,
                        None,
                    )
                current_url, current_headers = _prepare_download_redirect(
                    current_url, location, current_headers
                )
                continue
            if not 200 <= status < 300:
                raise urllib.error.HTTPError(
                    current_url,
                    status,
                    "HTTP Error",
                    response_headers,
                    None,
                )
            checksum = _checksum_from_metadata_values(
                response_headers.get("x-linked-etag")
                or response_headers.get("etag"),
                _raw_metadata_size(response_headers),
            )
            return checksum, current_url
        finally:
            try:
                body.close()
            finally:
                sock.close()
    raise urllib.error.HTTPError(
        current_url, 302, "Too many redirects", {}, None
    )


def _copy_exact_http_body(body, output, size: int) -> None:
    """Copy exactly size bytes or fail without accepting a truncated body."""
    remaining = size
    while remaining:
        chunk = body.read(min(1024 * 1024, remaining))
        if not chunk:
            raise urllib.error.URLError(
                f"truncated HTTP response body: {remaining} bytes missing"
            )
        output.write(chunk)
        remaining -= len(chunk)


def _read_chunk_line(body, description: str) -> bytes:
    line = body.readline(65537)
    if len(line) > 65536:
        raise urllib.error.URLError(f"{description} is too long")
    if not line.endswith(b"\r\n"):
        raise urllib.error.URLError(f"malformed {description}")
    return line[:-2]


def _copy_chunked_http_body(body, output) -> None:
    """Decode an HTTP/1.1 chunked response body while streaming to output."""
    while True:
        size_line = _read_chunk_line(body, "HTTP chunk-size line")
        size_token = size_line.split(b";", 1)[0].strip()
        if not size_token:
            raise urllib.error.URLError("empty HTTP chunk size")
        if any(character not in b"0123456789abcdefABCDEF" for character in size_token):
            raise urllib.error.URLError("invalid HTTP chunk size")
        try:
            chunk_size = int(size_token, 16)
        except ValueError as error:
            raise urllib.error.URLError("invalid HTTP chunk size") from error
        if chunk_size < 0:
            raise urllib.error.URLError("negative HTTP chunk size")
        if chunk_size == 0:
            trailer_bytes = 0
            trailer_count = 0
            while True:
                trailer = _read_chunk_line(body, "HTTP chunk trailer")
                if not trailer:
                    return
                trailer_bytes += len(trailer) + 2
                trailer_count += 1
                if trailer_bytes > 65536 or trailer_count > 200:
                    raise urllib.error.URLError("HTTP chunk trailers are too large")
                if b":" not in trailer:
                    raise urllib.error.URLError("malformed HTTP chunk trailer")
        _copy_exact_http_body(body, output, chunk_size)
        if body.read(2) != b"\r\n":
            raise urllib.error.URLError("HTTP chunk is missing its terminator")


def _copy_framed_http_body(body, response_headers, output) -> None:
    """Copy a response body according to unambiguous HTTP/1.1 framing."""
    transfer_encoding = response_headers.get("transfer-encoding")
    content_length = response_headers.get("content-length")
    if transfer_encoding and content_length:
        raise urllib.error.URLError(
            "ambiguous HTTP response framing: both Transfer-Encoding and Content-Length"
        )
    if transfer_encoding:
        codings = [item.strip().lower() for item in transfer_encoding.split(",")]
        if codings != ["chunked"]:
            raise urllib.error.URLError(
                f"unsupported HTTP transfer coding: {transfer_encoding}"
            )
        _copy_chunked_http_body(body, output)
        return
    if content_length is not None:
        values = [item.strip() for item in content_length.split(",")]
        if not values or len(set(values)) != 1:
            raise urllib.error.URLError("conflicting HTTP Content-Length values")
        if not values[0] or any(
            character not in "0123456789" for character in values[0]
        ):
            raise urllib.error.URLError("invalid HTTP Content-Length")
        try:
            size = int(values[0], 10)
        except ValueError as error:
            raise urllib.error.URLError("invalid HTTP Content-Length") from error
        if size < 0:
            raise urllib.error.URLError("negative HTTP Content-Length")
        _copy_exact_http_body(body, output, size)
        return
    shutil.copyfileobj(body, output)


def _atomgit_download_raw(
    url: str,
    dest: Path,
    headers,
    timeout: int = 60,
    max_redirects: int = 5,
    checksum: tuple = None,
) -> None:
    """Download over HTTPS keeping non-ASCII path bytes raw.

    AtomGit resolve cannot match percent-encoded nested paths with non-ASCII
    filenames, but serves the same file when the raw UTF-8 bytes are sent in
    the request target. This helper speaks HTTPS directly, follows redirects
    within a bounded limit, and streams the body to dest.
    """
    current_url = url
    current_headers = dict(headers)
    _download_url_origin(current_url)
    parts = urlsplit(current_url)
    host = parts.hostname
    port = parts.port or (443 if parts.scheme == "https" else 80)
    raw_path = (parts.path + (("?" + parts.query) if parts.query else "")).encode("utf-8")
    temporary_path = None
    try:
        for _ in range(max_redirects + 1):
            status, response_headers, body, sock = _atomgit_raw_http_get(
                host, port, parts.scheme, raw_path, current_headers, timeout
            )
            try:
                if status in (301, 302, 303, 307, 308):
                    location = response_headers.get("location")
                    if not location:
                        raise urllib.error.HTTPError(current_url, status, "Redirect without Location", response_headers, None)
                    current_url, current_headers = _prepare_download_redirect(
                        current_url, location, current_headers
                    )
                    parts = urlsplit(current_url)
                    host = parts.hostname
                    port = parts.port or (443 if parts.scheme == "https" else 80)
                    raw_path = (parts.path + (("?" + parts.query) if parts.query else "")).encode("utf-8")
                    continue
                if status == 404:
                    raise urllib.error.HTTPError(current_url, 404, "Not Found", response_headers, None)
                if not 200 <= status < 300:
                    raise urllib.error.HTTPError(current_url, status, "HTTP Error", response_headers, None)
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    prefix=f".{dest.name}.",
                    suffix=".part",
                    dir=dest.parent,
                    delete=False,
                ) as out:
                    temporary_path = Path(out.name)
                    _copy_framed_http_body(body, response_headers, out)
                if checksum is not None:
                    _verify_download_checksum(temporary_path, checksum)
                temporary_path.replace(dest)
                temporary_path = None
                return
            finally:
                try:
                    body.close()
                finally:
                    sock.close()
        raise urllib.error.HTTPError(current_url, 302, "Too many redirects", {}, None)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _download_atomgit_file(
    repo_id: str,
    repo_type: str,
    filename: str,
    dest: Path,
    token: str,
    checksum: tuple = None,
) -> None:
    """Download one file from the already-selected repository type.

    Standard percent-encoded URLs are tried first (HF Hub compatible). When the
    filename contains non-ASCII characters, raw UTF-8 byte URLs are tried after
    a 404, which works around the AtomGit resolve route failing to decode
    nested paths with non-ASCII filenames.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "atomgit-cli", "Accept": "*/*"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    def fetch_once(url: str, raw: bool = False) -> None:
        if raw:
            if checksum is None:
                _atomgit_download_raw(url, dest, headers, timeout=60)
            else:
                _atomgit_download_raw(
                    url, dest, headers, timeout=60, checksum=checksum
                )
            return
        temporary_path = None
        try:
            req = urllib.request.Request(url, headers=headers)
            with _atomgit_open_url(req, timeout=60) as resp:
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    prefix=f".{dest.name}.",
                    suffix=".part",
                    dir=dest.parent,
                    delete=False,
                ) as out:
                    temporary_path = Path(out.name)
                    shutil.copyfileobj(resp, out)
            if checksum is not None:
                _verify_download_checksum(temporary_path, checksum)
            temporary_path.replace(dest)
            temporary_path = None
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    url_specs = [
        (_atomgit_resolve_url(repo_id, repo_type, filename), False),
    ]
    if not filename.isascii():
        url_specs.append((_atomgit_resolve_url_raw(repo_id, repo_type, filename), True))
    last_error = None
    for url, raw in url_specs:
        try:
            run_download_with_retry(lambda: fetch_once(url, raw))
            return
        except Exception as error:
            if _is_not_found_error(error):
                last_error = error
                continue
            raise
    raise last_error


_RESUMABLE_DEFAULT_REQUEST_TIMEOUT = 300.0
_RESUMABLE_COMMIT_MAX_ATTEMPTS = 5
_RESUMABLE_COMMIT_BACKOFF_BASE = 30.0
_RESUMABLE_COMMIT_BACKOFF_CAP = 300.0
_RESUMABLE_COMMIT_BATCH_SIZES = (20, 10, 5, 2, 1)
# HF Hub 1.1.7 documents a 1 GB regular-file commit payload limit. Files above
# it must be selected as LFS by the repository policy before commit encoding.
_RESUMABLE_REGULAR_FILE_MAX_BYTES = 1_000_000_000


class ResumableUploadModeError(RuntimeError):
    """A server-selected resumable upload mode is unsafe for the file size."""


_RESUMABLE_WORKER_ERROR_MESSAGES = {
    "authentication": "resumable worker authentication failed",
    "permission": "resumable worker permission check failed",
    "repository": "resumable worker repository check failed",
    "revision": "resumable worker revision check failed",
    "request": "resumable worker request validation failed",
    "payload_size": "resumable worker payload is too large",
    "rate_limit": "resumable worker was rate limited",
    "service_unavailable": "resumable worker service is unavailable",
    "timeout": "resumable worker timed out",
    "connection": "resumable worker connection failed",
    "upload_mode": "resumable worker upload mode is unsafe",
    "client_resource": "resumable worker client resources are insufficient",
    "unknown": "resumable worker failed",
}


class ResumableWorkerError(RuntimeError):
    """A credential-safe failure reconstructed from the upload child."""

    def __init__(self, category: str):
        if category not in _RESUMABLE_WORKER_ERROR_MESSAGES:
            category = "unknown"
        self.category = category
        super().__init__(_RESUMABLE_WORKER_ERROR_MESSAGES[category])


class ResumableCommitError(RuntimeError):
    """A resumable commit could not complete under the bounded retry policy."""


def _resumable_error_chain(error: BaseException):
    """Yield a bounded exception chain without serializing exception text."""
    current = error
    seen = set()
    for _ in range(8):
        if not isinstance(current, BaseException) or id(current) in seen:
            return
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def _resumable_error_status(error: BaseException) -> Optional[int]:
    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)
    if isinstance(status_code, int):
        return status_code
    code = getattr(error, "code", None)
    return code if isinstance(code, int) else None


def _resumable_worker_error_category(error: BaseException) -> str:
    """Reduce an arbitrary child failure to one bounded, non-sensitive code."""
    for cause in _resumable_error_chain(error):
        if isinstance(cause, ResumableWorkerError):
            return cause.category
        if isinstance(cause, ResumableUploadModeError):
            return "upload_mode"

        name = type(cause).__name__
        if name == "RevisionNotFoundError":
            return "revision"
        if name == "RepositoryNotFoundError":
            return "repository"
        if name in ("GatedRepoError", "DisabledRepoError"):
            return "permission"

        credential_error = auth_error_kind(cause)
        if credential_error in ("authentication", "permission"):
            return credential_error

        status_code = _resumable_error_status(cause)
        if status_code == 401:
            return "authentication"
        if status_code == 403:
            return "permission"
        if status_code == 404:
            return "repository"
        if status_code == 413:
            return "payload_size"
        if status_code == 429:
            return "rate_limit"
        if status_code in (502, 503, 504):
            return "service_unavailable"
        if status_code == 400 or name == "BadRequestError":
            return "request"

        if isinstance(
            cause,
            (httpx.TimeoutException, TimeoutError, socket.timeout),
        ):
            return "timeout"
        if isinstance(
            cause,
            (httpx.NetworkError, ConnectionError),
        ):
            return "connection"
        if isinstance(cause, MemoryError):
            return "client_resource"
        if isinstance(cause, OSError) and cause.errno in (
            errno.EACCES,
            errno.EPERM,
            errno.EFBIG,
            errno.EMFILE,
            errno.ENFILE,
            errno.ENOMEM,
            errno.ENOSPC,
            errno.EROFS,
        ):
            return "client_resource"
    return "unknown"


def _resumable_failure_envelope(error: BaseException) -> dict:
    """Build the only error payload allowed across the process boundary."""
    return {"category": _resumable_worker_error_category(error)}


def _validate_resumable_commit_operations(operations) -> None:
    """Reject unsafe regular blobs before commit serialization reads them."""
    for operation in operations:
        upload_info = getattr(operation, "upload_info", None)
        size = getattr(upload_info, "size", None)
        upload_mode = getattr(operation, "_upload_mode", None)
        if (
            upload_mode == "regular"
            and isinstance(size, int)
            and not isinstance(size, bool)
            and size > _RESUMABLE_REGULAR_FILE_MAX_BYTES
        ):
            raise ResumableUploadModeError(
                "服务端将超大文件判定为 regular；请在仓库 .gitattributes "
                "中为该文件类型配置 Git LFS 后重试。"
            )


def _validate_resumable_upload_mode_items(items) -> None:
    """Apply the regular-file size policy immediately after preupload mode."""
    for _, metadata in items:
        if (
            metadata.upload_mode == "regular"
            and metadata.size > _RESUMABLE_REGULAR_FILE_MAX_BYTES
        ):
            raise ResumableUploadModeError(
                "服务端将超大文件判定为 regular；请在仓库 .gitattributes "
                "中为该文件类型配置 Git LFS 后重试。"
            )


def _refresh_unsafe_resumable_upload_modes(folder_path: Path) -> int:
    """Refresh only unsafe uncommitted policy fields in locked HF metadata."""
    folder_path = Path(folder_path)
    if not (folder_path / ".cache" / "huggingface" / "upload").is_dir():
        return 0
    refreshed = 0
    for file_path in folder_path.rglob("*"):
        if not file_path.is_file():
            continue
        relative_path = file_path.relative_to(folder_path).as_posix()
        if relative_path.startswith(".cache/huggingface/"):
            continue
        paths = get_local_upload_paths(folder_path, relative_path)
        if not paths.metadata_path.is_file():
            continue
        metadata = read_upload_metadata(folder_path, relative_path)
        if (
            not metadata.is_committed
            and metadata.upload_mode == "regular"
            and metadata.size > _RESUMABLE_REGULAR_FILE_MAX_BYTES
        ):
            metadata.upload_mode = None
            metadata.should_ignore = None
            metadata.remote_oid = None
            metadata.save(paths)
            refreshed += 1
    return refreshed


def _commit_error_status(error: BaseException) -> Optional[int]:
    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)
    return status_code if isinstance(status_code, int) else None


def _commit_retry_after(error: BaseException) -> Optional[float]:
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    value = headers.get("Retry-After") if headers is not None else None
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        try:
            retry_at = parsedate_to_datetime(value)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(
                0.0,
                (retry_at - datetime.now(timezone.utc)).total_seconds(),
            )
        except (TypeError, ValueError, OverflowError):
            return None


def _is_ambiguous_commit_error(error: BaseException) -> bool:
    status_code = _commit_error_status(error)
    if status_code in (502, 503, 504):
        return True
    return isinstance(
        error,
        (
            httpx.TimeoutException,
            httpx.NetworkError,
            TimeoutError,
            ConnectionError,
            socket.timeout,
        ),
    )


def _is_retryable_commit_error(error: BaseException) -> bool:
    status_code = _commit_error_status(error)
    if status_code in (429, 502, 503, 504):
        return True
    return isinstance(
        error,
        (
            httpx.TimeoutException,
            httpx.NetworkError,
            TimeoutError,
            ConnectionError,
            socket.timeout,
        ),
    )


def _is_reducible_commit_error(error: BaseException) -> bool:
    status_code = _commit_error_status(error)
    if status_code in (413, 502, 503, 504):
        return True
    return isinstance(
        error,
        (httpx.ReadTimeout, httpx.WriteTimeout, TimeoutError, socket.timeout),
    )


def _operation_git_sha1(operation) -> Optional[str]:
    upload_info = getattr(operation, "upload_info", None)
    size = getattr(upload_info, "size", None)
    source = getattr(operation, "path_or_fileobj", None)
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        return None
    digest = hashlib.sha1()
    digest.update(b"blob " + str(size).encode("ascii") + b"\0")
    try:
        if isinstance(source, bytes):
            digest.update(source)
        elif isinstance(source, (str, Path)):
            with Path(source).open("rb") as stream:
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
        elif hasattr(source, "read"):
            position = source.tell()
            try:
                source.seek(0)
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
            finally:
                source.seek(position)
        else:
            return None
    except (OSError, ValueError, AttributeError):
        return None
    return digest.hexdigest()


def _reconcile_resumable_commit_operations(
    *, repo_id: str, repo_type: str, revision: str, operations, token: str
) -> Set[str]:
    """Return paths whose remote object identity matches the commit operation."""
    if revision not in (None, "main"):
        return set()
    matched = set()
    for operation in operations:
        path_in_repo = getattr(operation, "path_in_repo", None)
        upload_info = getattr(operation, "upload_info", None)
        if not isinstance(path_in_repo, str) or upload_info is None:
            continue
        try:
            algorithm, remote_digest, remote_size = _atomgit_file_checksum(
                repo_id, repo_type, path_in_repo, token
            )
        except Exception:
            continue
        local_size = getattr(upload_info, "size", None)
        if remote_size != local_size:
            continue
        if algorithm == "sha256":
            local_sha256 = getattr(upload_info, "sha256", None)
            if isinstance(local_sha256, bytes) and local_sha256.hex() == remote_digest:
                matched.add(path_in_repo)
        elif algorithm == "git-sha1":
            if _operation_git_sha1(operation) == remote_digest:
                matched.add(path_in_repo)
    return matched


def _next_resumable_commit_batch_size(item_count: int) -> int:
    for batch_size in _RESUMABLE_COMMIT_BATCH_SIZES:
        if batch_size < item_count:
            return batch_size
    return 1


def _mark_resumable_operations_committed(
    folder_path: Path, operations
) -> None:
    """Persist successful sub-commits before the outer HF batch completes."""
    folder_path = Path(folder_path)
    for operation in operations:
        path_in_repo = getattr(operation, "path_in_repo", None)
        upload_info = getattr(operation, "upload_info", None)
        local_sha256 = getattr(upload_info, "sha256", None)
        if not isinstance(path_in_repo, str) or not isinstance(local_sha256, bytes):
            raise ResumableCommitError(
                "resumable commit metadata is unavailable"
            )
        paths = get_local_upload_paths(folder_path, path_in_repo)
        metadata = read_upload_metadata(folder_path, path_in_repo)
        if metadata.sha256 != local_sha256.hex():
            raise ResumableCommitError(
                "resumable commit metadata changed during upload"
            )
        metadata.is_committed = True
        metadata.save(paths)


class _ResumableCommitController:
    """Apply AtomGit-specific retry and reconciliation to HF commit calls."""

    def __init__(
        self,
        create_commit,
        *,
        token: str,
        sleep=time.sleep,
        jitter=None,
        reconcile=_reconcile_resumable_commit_operations,
        max_attempts: int = _RESUMABLE_COMMIT_MAX_ATTEMPTS,
        mark_committed=None,
        fatal_callback=None,
        event_callback=None,
    ):
        self._create_commit = create_commit
        self._token = token
        self._sleep = sleep
        self._jitter = jitter or (
            lambda delay: random.uniform(0.0, min(1.0, delay * 0.1))
        )
        self._reconcile = reconcile
        self._max_attempts = max_attempts
        self._mark_committed = mark_committed or (lambda operations: None)
        self._fatal_callback = fatal_callback
        self._event_callback = event_callback

    def _emit(self, kind: str, **details) -> None:
        if self._event_callback is None:
            return
        try:
            self._event_callback({"kind": kind, **details})
        except Exception:
            # Observability must never change upload or retry semantics.
            pass

    def _raise_fatal(self, error: BaseException, item_count: int):
        status_code = _commit_error_status(error)
        if status_code is not None:
            detail = f"HTTP {status_code}"
        else:
            detail = type(error).__name__
        wrapped = ResumableCommitError(
            f"resumable commit failed for {item_count} file(s): {detail}"
        )
        if self._fatal_callback is not None:
            self._fatal_callback(error)
        raise wrapped from error

    def _retry_delay(self, error: BaseException, attempt: int) -> float:
        retry_after = _commit_retry_after(error)
        if retry_after is not None:
            return retry_after
        delay = min(
            _RESUMABLE_COMMIT_BACKOFF_BASE * (2 ** (attempt - 1)),
            _RESUMABLE_COMMIT_BACKOFF_CAP,
        )
        return delay + self._jitter(delay)

    def _commit_group(self, args, kwargs, operations):
        operations = list(operations)
        attempts = 0
        last_error = None
        while operations and attempts < self._max_attempts:
            attempts += 1
            call_kwargs = dict(kwargs)
            call_kwargs["operations"] = operations
            try:
                result = self._create_commit(*args, **call_kwargs)
                self._mark_committed(operations)
                return result
            except Exception as error:
                last_error = error
                if _is_ambiguous_commit_error(error):
                    self._emit(
                        "reconcile_start",
                        item_count=len(operations),
                        attempt=attempts,
                    )
                    matched = self._reconcile(
                        repo_id=call_kwargs.get("repo_id"),
                        repo_type=call_kwargs.get("repo_type") or "model",
                        revision=call_kwargs.get("revision") or "main",
                        operations=operations,
                        token=self._token,
                    )
                    matched_operations = [
                        operation for operation in operations
                        if getattr(operation, "path_in_repo", None) in matched
                    ]
                    if matched_operations:
                        try:
                            self._mark_committed(matched_operations)
                        except Exception as metadata_error:
                            self._raise_fatal(
                                metadata_error, len(matched_operations)
                            )
                    operations = [
                        operation for operation in operations
                        if getattr(operation, "path_in_repo", None) not in matched
                    ]
                    self._emit(
                        "reconcile_result",
                        confirmed=len(matched_operations),
                        remaining=len(operations),
                        attempt=attempts,
                    )
                    if not operations:
                        return None
                if _commit_error_status(error) == 413:
                    break
                if not _is_retryable_commit_error(error):
                    self._raise_fatal(error, len(operations))
                if attempts < self._max_attempts:
                    delay = self._retry_delay(error, attempts)
                    status_code = _commit_error_status(error)
                    if status_code == 429:
                        self._emit(
                            "rate_limit_wait",
                            delay=delay,
                            attempt=attempts,
                            item_count=len(operations),
                        )
                    self._emit(
                        "retry",
                        attempt=attempts + 1,
                        max_attempts=self._max_attempts,
                        item_count=len(operations),
                        status_code=status_code,
                        error_type=type(error).__name__,
                    )
                    self._sleep(delay)

        if not operations:
            return None
        if (
            len(operations) == 1
            or not _is_reducible_commit_error(last_error)
        ):
            self._raise_fatal(last_error, len(operations))

        batch_size = _next_resumable_commit_batch_size(len(operations))
        self._emit(
            "reduce",
            from_size=len(operations),
            to_size=batch_size,
        )
        result = None
        for index in range(0, len(operations), batch_size):
            result = self._commit_group(
                args,
                kwargs,
                operations[index:index + batch_size],
            )
        return result

    def create_commit(self, *args, **kwargs):
        operations = list(kwargs.get("operations", ()))
        if not operations:
            return self._create_commit(*args, **kwargs)
        try:
            _validate_resumable_commit_operations(operations)
        except ResumableUploadModeError as error:
            if self._fatal_callback is not None:
                self._fatal_callback(error)
            raise
        return self._commit_group(args, kwargs, operations)


def _print_resumable_commit_event(event, batch_context) -> None:
    """Print one credential-safe child event with its outer batch identity."""
    if not batch_context:
        return
    current, total = batch_context
    prefix = f"[批次 {current}/{total}]"
    kind = event.get("kind")
    if kind == "rate_limit_wait":
        print(
            f"{prefix} 请求限流，等待 {event['delay']:g} 秒后重试",
            flush=True,
        )
    elif kind == "retry":
        reason = (
            f"HTTP {event['status_code']}"
            if event.get("status_code") is not None
            else event.get("error_type", "网络错误")
        )
        print(
            f"{prefix} 重试 {event['attempt']}/{event['max_attempts']}"
            f"（{reason}，{event['item_count']} 个文件）",
            flush=True,
        )
    elif kind == "reconcile_start":
        print(
            f"{prefix} 提交结果不明确，正在核对远端状态"
            f"（{event['item_count']} 个文件）",
            flush=True,
        )
    elif kind == "reconcile_result":
        print(
            f"{prefix} 远端核对完成: 确认 {event['confirmed']}，"
            f"仍待提交 {event['remaining']}",
            flush=True,
        )
    elif kind == "reduce":
        print(
            f"{prefix} 降低提交批量: {event['from_size']} -> "
            f"{event['to_size']}",
            flush=True,
        )


def _run_resumable_upload(
    token, kwargs, result_queue,
    request_timeout: float = _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
    batch_context=None,
):
    """Run HF's resumable uploader in an isolated child process.

    The child is deliberately short-lived so a timed-out transfer can be
    terminated without leaving worker threads running in the CLI process.
    """
    original_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT
    original_get_upload_mode = hf_large_folder._get_upload_mode
    result_sent = False

    def send_failure(error):
        nonlocal result_sent
        if not result_sent:
            result_queue.put((False, _resumable_failure_envelope(error)))
            result_sent = True

    def fatal_exit(error):
        if multiprocessing.current_process().name == "MainProcess":
            return
        send_failure(error)
        if hasattr(result_queue, "close"):
            result_queue.close()
        if hasattr(result_queue, "join_thread"):
            result_queue.join_thread()
        os._exit(1)

    def get_upload_mode_with_policy(*args, **kwargs):
        result = original_get_upload_mode(*args, **kwargs)
        items = kwargs.get("items")
        if items is None and args:
            items = args[0]
        try:
            _validate_resumable_upload_mode_items(items or [])
        except ResumableUploadModeError as error:
            fatal_exit(error)
            raise
        return result

    try:
        hf_constants.DEFAULT_REQUEST_TIMEOUT = request_timeout
        close_hf_session()
        client = HfApi(token=token)
        _refresh_unsafe_resumable_upload_modes(Path(kwargs["folder_path"]))

        def existing_repo(repo_id, *, private=None, repo_type=None,
                          exist_ok=False):
            """Satisfy HF 1.1.7 setup after the parent validated the target."""
            return type("_ExistingRepo", (), {"repo_id": repo_id})()

        # HF 1.1.7 otherwise sends create_repo(exist_ok=True) before metadata
        # recovery. AtomGit upload targets are required to pre-exist.
        client.create_repo = existing_repo
        hf_large_folder._get_upload_mode = get_upload_mode_with_policy
        create_commit = getattr(client, "create_commit", None)
        if callable(create_commit):
            controller = _ResumableCommitController(
                create_commit,
                token=token,
                mark_committed=lambda operations: (
                    _mark_resumable_operations_committed(
                        Path(kwargs["folder_path"]), operations
                    )
                ),
                fatal_callback=fatal_exit,
                event_callback=lambda event: _print_resumable_commit_event(
                    event, batch_context
                ),
            )
            client.create_commit = controller.create_commit
        client.upload_large_folder(**kwargs)
        result_queue.put((True, None))
        result_sent = True
    except BaseException as exc:
        send_failure(exc)
    finally:
        hf_large_folder._get_upload_mode = original_get_upload_mode
        hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
        close_hf_session()


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
            ".cache", "huggingface"
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
                ".cache", "huggingface"
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


def _projection_file_is_current(
    source: Path, destination: Path, source_stat
) -> bool:
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
        ".cache", "huggingface"
    )


def _sync_resumable_projection(
    source: Path,
    projection: Path,
    prefix: str = None,
    ignore_patterns=None,
    selected_paths: Optional[Set[Path]] = None,
) -> None:
    """Mirror source files below prefix while retaining HF metadata at root."""
    payload_root = (
        projection.joinpath(*prefix.split("/")) if prefix else projection
    )
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
        folded_parts[index:index + 2] == [".cache", "huggingface"]
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


def _print_upload_batch_plan(file_count: int, batch_count: int) -> None:
    print(
        f"上传批次计划: 共 {file_count} 个文件，{batch_count} 个批次，"
        "每批最多 20 个文件",
        flush=True,
    )


def _print_upload_batch_summary(
    planned: int, submitted: int, skipped: int, completed: int
) -> None:
    print(
        f"上传批次汇总: 计划 {planned}，新增提交 {submitted}，"
        f"续传跳过 {skipped}，确认完成 {completed}",
        flush=True,
    )


def _execute_resumable_upload_process(
    *, token: str, upload_kwargs: dict, request_timeout: float,
    upload_deadline, upload_timeout, batch_context,
) -> None:
    """Run one outer resumable batch and require an explicit child result."""
    methods = multiprocessing.get_all_start_methods()
    context = multiprocessing.get_context(
        "fork" if "fork" in methods else "spawn"
    )
    result_queue = context.Queue()
    process = context.Process(
        target=_run_resumable_upload,
        args=(
            token,
            upload_kwargs,
            result_queue,
            request_timeout,
            batch_context,
        ),
    )
    process.daemon = True
    remaining_timeout = None
    if upload_deadline is not None:
        remaining_timeout = upload_deadline - time.monotonic()
    if remaining_timeout is not None and remaining_timeout <= 0:
        raise TimeoutError(
            f"resumable upload timed out after {upload_timeout}s"
        )
    process.start()
    process.join(remaining_timeout)
    if process.is_alive():
        process.terminate()
        process.join(2)
        raise TimeoutError(
            f"resumable upload timed out after {upload_timeout}s"
        )
    try:
        ok, error = result_queue.get(timeout=1)
    except Exception as exc:
        raise RuntimeError(
            "resumable upload worker exited without a result"
        ) from exc
    if not ok:
        category = error.get("category") if isinstance(error, dict) else None
        raise ResumableWorkerError(category or "unknown")


def _validate_resumable_upload_target(
    *, token: str, repo_id: str, repo_type: str, revision: str = None
) -> None:
    """Perform one read-only repository/revision check before local hashing."""
    client = HfApi(token=token)
    list_repo_type = None if repo_type == "model" else repo_type
    tree = client.list_repo_tree(
        repo_id=repo_id,
        recursive=False,
        revision=revision,
        repo_type=list_repo_type,
    )
    next(iter(tree), None)


def _upload_folder_with_workers(upload_kwargs: dict, num_workers: int = 5):
    """Call HF upload_folder while honoring the requested commit thread count."""
    if num_workers == 5:
        return upload_folder(**upload_kwargs)
    kwargs = dict(upload_kwargs)
    token = kwargs.pop("token", None)
    client = HfApi(token=token)
    original_create_commit = client.create_commit

    def create_commit_with_workers(*args, **call_kwargs):
        call_kwargs["num_threads"] = num_workers
        return original_create_commit(*args, **call_kwargs)

    client.create_commit = create_commit_with_workers
    return client.upload_folder(**kwargs)


def _prefix_resumable_ignore_patterns(path_in_repo: str, ignore_patterns):
    """Apply source-relative ignore patterns to a projected remote prefix."""
    if not path_in_repo or not ignore_patterns:
        return ignore_patterns
    return [
        f"{path_in_repo}/{pattern.lstrip('/')}" for pattern in ignore_patterns
    ]


def _classify_upload_error(e: Exception, repo_id: str = None) -> tuple:
    """把 HF Hub 上传异常归类为 (error_type, hint) 二元组，供上层给出语义化提示。

    覆盖以下典型情形（基于 huggingface_hub 错误类型与文本特征）：
      - 认证失败 (401/403, 无有效 token)
      - 仓库不存在 (RepositoryNotFoundError)
      - 仓库已禁用 (DisabledRepoError)
      - 分支不存在 (RevisionNotFoundError)
      - 请求参数错误 (BadRequestError / 400)
      - 超时 / 网络连接 (timeout / connection)
      - 其他未知错误

    返回 (error_type, hint)，其中 hint 是给用户的可执行建议。
    """
    if isinstance(e, ResumableWorkerError):
        structured_errors = {
            "authentication": (
                "认证失败",
                "登录凭证无效或已过期。请使用 'atomgit login' 重新登录后重试。",
            ),
            "permission": (
                "权限不足",
                "当前登录凭证无权上传到目标仓库。请检查仓库权限或目标命名空间。",
            ),
            "repository": (
                "仓库不存在",
                f"目标仓库 {repo_id or ''} 不存在或不可访问。请先使用 "
                "'atomgit repo create' 创建仓库，或检查 repo_id / repo_type。",
            ),
            "revision": (
                "分支/版本不存在",
                "目标分支不存在且无法自动创建。请检查 revision 是否正确。",
            ),
            "request": (
                "请求参数错误",
                "请求参数不合法。请检查 repo_id、repo_type、path_in_repo 等参数。",
            ),
            "payload_size": (
                "提交过大",
                "提交已降至单文件仍超过服务端限制；断点状态已保留，请联系平台支持。",
            ),
            "rate_limit": (
                "请求限流",
                "服务端持续限流，上传已停止且断点状态已保留；请稍后重新执行同一命令。",
            ),
            "service_unavailable": (
                "服务暂不可用",
                "服务端暂时不可用，上传断点状态已保留；请稍后重新执行同一命令。",
            ),
            "timeout": (
                "请求超时",
                "请求超时。可使用 -t/--timeout 增大超时时间后重试。",
            ),
            "connection": (
                "网络连接失败",
                "无法连接到服务器。请检查网络或代理设置后重试。",
            ),
            "upload_mode": (
                "上传模式不安全",
                "服务端将超大文件判定为 regular；请在仓库 .gitattributes "
                "中为该文件类型配置 Git LFS 后重试。断点状态已保留。",
            ),
            "client_resource": (
                "客户端资源不足",
                "本机内存、磁盘空间或文件句柄不足；释放资源后重新执行同一命令。",
            ),
            "unknown": (
                "未知错误",
                "上传子进程失败且未能安全识别原因；断点状态已保留，请稍后重试。",
            ),
        }
        return structured_errors[e.category]

    if isinstance(e, ResumableUploadModeError):
        return (
            "上传模式不安全",
            "服务端将超大文件判定为 regular；请在仓库 .gitattributes "
            "中为该文件类型配置 Git LFS 后重试。断点状态已保留。",
        )

    msg = str(e)
    ename = type(e).__name__

    # 仓库已禁用（需放在 RepositoryNotFoundError 之前，避免被 403 误吞）
    if ename == "DisabledRepoError" or "disabled" in msg.lower() and "repo" in msg.lower():
        return "仓库已禁用", "该仓库已被作者禁用，无法上传。请联系仓库所有者。"

    # 分支/版本不存在
    if ename == "RevisionNotFoundError" or "revision" in msg.lower() and ("not found" in msg.lower() or "404" in msg):
        return "分支/版本不存在", f"目标分支不存在且无法自动创建。请检查 revision 是否正确。"

    # 受限仓库的可靠特征。HF 401 通用文案（"If you are trying to access a
    # private or gated repo..."）也含 "gated" 一词，不能仅凭该词判定。
    gated_markers = (
        "cannot access gated repo" in msg.lower()
        or "you are not on the authorized list" in msg.lower()
        or "you are not in the authorized list" in msg.lower()
        or "repo is gated" in msg.lower()
        or "is gated" in msg.lower()
    )

    # 仓库不存在（HF 既定：404/401 或 "Repository Not Found"、"创建提交前仓库
    # 必须已存在 / 检查 repo_id 与 repo_type" 等特征；preupload 预检对不存在
    # 或不可访问的仓库返回 404/401）
    if (
        ename in ("RepositoryNotFoundError", "GatedRepoError")
        or "repository not found" in msg.lower()
        or ("404" in msg and "not found" in msg.lower())
        or "creating a commit assumes that the repo already exists" in msg.lower()
        or "please make sure you specified the correct `repo_id` and `repo_type`" in msg.lower()
    ):
        if ename == "GatedRepoError" or gated_markers:
            return "受限仓库", "该仓库为受限仓库(gated)，您未在授权名单内。请在平台申请访问权限。"
        if "preupload" in msg.lower():
            return (
                "仓库不存在",
                f"目标仓库 {repo_id or ''} 不存在或为私有且无访问权限。"
                "请先使用 'atomgit repo create' 创建仓库，或检查 repo_id / repo_type。",
            )
        return "仓库不存在", f"仓库 {repo_id or ''} 不存在或为私有且无访问权限。请检查 repo_id/repo_type，或先 atomgit login。"

    # 受限仓库（文本特征兜底：仅限明确的 gated 语义）
    if gated_markers:
        return "受限仓库", "该仓库为受限仓库(gated)，您未在授权名单内。请在平台申请访问权限。"

    if isinstance(e, ResumableProjectionError):
        return "本地投影失败", msg

    if "429" in msg or "too many requests" in msg.lower():
        return (
            "请求限流",
            "服务端持续限流，上传已停止且断点状态已保留；请稍后重新执行同一命令。",
        )

    if "413" in msg:
        return (
            "提交过大",
            "提交已降至单文件仍超过服务端限制；断点状态已保留，请联系平台支持。",
        )

    if any(code in msg for code in ("502", "503", "504")):
        return (
            "服务暂不可用",
            "服务端暂时不可用，上传断点状态已保留；请稍后重新执行同一命令。",
        )

    # 请求参数错误
    if ename == "BadRequestError" or "400" in msg and "client error" in msg.lower():
        return "请求参数错误", "请求参数不合法。请检查 repo_id、repo_type、path_in_repo 等参数。"

    # 认证/权限失败（且不属于上述仓库类错误）
    credential_error = auth_error_kind(e)
    if credential_error == "authentication":
        return (
            "认证失败",
            "登录凭证无效或已过期。请使用 'atomgit login' 重新登录后重试。",
        )
    if credential_error == "permission":
        return (
            "权限不足",
            "当前登录凭证无权上传到目标仓库。请检查仓库权限或目标命名空间。",
        )

    # 超时
    if "timeout" in msg.lower() or "timed out" in msg.lower() or ename == "TimeoutError":
        return "请求超时", "请求超时。可使用 -t/--timeout 增大超时时间后重试。"

    # 网络连接
    if "connection" in msg.lower() or "connectionerror" in ename.lower() or "resolve" in msg.lower():
        return "网络连接失败", "无法连接到服务器。请检查网络或代理设置后重试。"

    # 其他
    return "未知错误", "服务返回了未识别的错误；请稍后重试，仍失败时联系平台支持。"


def _classify_create_repo_error(e: Exception) -> tuple:
    """把 HF Hub 建仓异常归类为 (error_type, hint) 二元组，供上层给出语义化提示。

    覆盖以下典型情形（基于 huggingface_hub 错误类型与文本特征）：
      - 认证失败 (401/403, 无效 token 或权限不足)
      - 请求参数错误 (BadRequestError / 400)
      - 超时 / 网络连接
      - 其他未知错误

    返回 (error_type, hint)，其中 hint 是给用户的可执行建议。
    """
    msg = str(e)
    ename = type(e).__name__

    credential_error = auth_error_kind(e)
    if credential_error == "authentication":
        return (
            "认证失败",
            "登录凭证无效或已过期。请使用 'atomgit login' 重新登录获取有效 token，再重试创建。",
        )
    if credential_error == "permission":
        return (
            "权限不足",
            "当前登录凭证缺少目标命名空间的仓库创建权限。请检查组织或命名空间权限。",
        )

    # 请求参数错误
    if ename == "BadRequestError" or "400" in msg and "client error" in msg.lower():
        return (
            "请求参数错误",
            "仓库参数不合法。请检查 repo_name 格式（username/repo-name）与 --type 取值。",
        )

    # 超时
    if "timeout" in msg.lower() or "timed out" in msg.lower() or ename == "TimeoutError":
        return "请求超时", "请求超时。请检查网络后重试。"

    # 网络连接
    if "connection" in msg.lower() or "connectionerror" in ename.lower() or "resolve" in msg.lower():
        return "网络连接失败", "无法连接到服务器。请检查网络或代理设置后重试。"

    # 其他
    return "未知错误", "服务返回了未识别的错误；请稍后重试，仍失败时联系平台支持。"


class HuggingFaceAPI:
    """AtomGit API 客户端，完全基于Hugging Face Hub SDK"""
    
    def __init__(self):
        pass
    
    def _normalize_repo_id(self, repo_id: str) -> str:
        """标准化仓库 ID，兼容保留原有内部方法。"""
        return normalize_repo_id(repo_id)
    
    def login(self, token: str) -> bool:
        """登录验证"""
        if not token or len(token) < 10:
            print("❌ Token格式不正确")
            return False
        try:
            user_info = self._get_login_user_by_token(token)
        except Exception as error:
            print(f"❌ 登录验证失败: {_sanitized_v5_api_error(error)}")
            return False
        if not user_info:
            print("❌ 登录验证失败: AtomGit API 响应格式无效")
            return False
        try:
            config.set_credentials(token, username=user_info['login'])
        except Exception:
            print("❌ 登录凭证保存失败，请检查配置目录权限后重试")
            return False
        print("✅ Token已保存")
        return True
    
    def _get_login_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        if not token:
            print("❌ 未找到登录凭证")
            return None
        api_url = 'https://atomgit.com/api/v5/user'
        req = urllib.request.Request(
            api_url,
            headers={
                'Authorization': token,
                'User-Agent': 'atomgit-cli',
                'Accept': 'application/json'
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                raise urllib.error.HTTPError(
                    api_url,
                    response.status,
                    "unexpected AtomGit identity response",
                    getattr(response, "headers", {}),
                    None,
                )
            payload = response.read(_ATOMGIT_IDENTITY_MAX_JSON_BYTES + 1)
        if len(payload) > _ATOMGIT_IDENTITY_MAX_JSON_BYTES:
            raise ValueError("identity response is too large")
        data = json.loads(payload.decode('utf-8'))
        if not isinstance(data, dict):
            raise ValueError("identity response is malformed")
        login = data.get('login')
        if not isinstance(login, str) or not login.strip():
            raise ValueError("identity response is missing login")
        return {
            'login': login,
            'name': data.get('name'),
            'email': data.get('email')
        }

    def get_login_user(self):
        try:
            credentials = config.get_credentials()
        except Exception:
            print("❌ 登录凭证读取失败，请检查配置文件和目录权限")
            return None
        if not credentials:
            print("❌ 未找到登录凭证")
            return None
        try:
            user_info = self._get_login_user_by_token(credentials['token'])
        except Exception as error:
            print(f"❌ 获取用户信息失败: {_sanitized_v5_api_error(error)}")
            return None
        if not user_info:
            print("❌ 获取用户信息失败: AtomGit API 响应格式无效")
            return None
        return user_info

    def list_repos(self):
        """List repositories available to the stored AtomGit credential."""
        try:
            credentials = config.get_credentials()
            if not credentials or not credentials.get('token'):
                print("❌ 未找到登录凭证")
                return None
            payload = _atomgit_v5_get_json(
                "/user/repos", credentials['token']
            )
            if isinstance(payload, dict):
                for key in ("data", "repositories"):
                    if isinstance(payload.get(key), list):
                        payload = payload[key]
                        break
            if not isinstance(payload, list) or not all(
                isinstance(repository, dict) for repository in payload
            ):
                raise ValueError("repository collection is malformed")
            return payload
        except Exception as error:
            print(f"获取仓库列表失败: {_sanitized_v5_api_error(error)}")
            return None

    def set_repo_visibility(self, repo_id: str, private: bool) -> bool:
        """Update and verify one repository's public/private state."""
        try:
            credentials = config.get_credentials()
            if not credentials or not credentials.get('token'):
                print("❌ 未找到登录凭证")
                return False
            if not isinstance(private, bool):
                raise ValueError("private must be a boolean")
            path = _atomgit_v5_repo_path(repo_id)
            write_error = None
            try:
                _atomgit_v5_request_json(
                    "PATCH", path, credentials['token'], {"private": private}
                )
            except Exception as error:
                if _is_definitive_v5_write_error(error):
                    print(
                        "修改仓库可见性失败: "
                        + _sanitized_v5_api_error(error)
                    )
                    return False
                write_error = error
            try:
                repository = _atomgit_v5_get_json(
                    path, credentials['token']
                )
            except Exception:
                print("仓库可见性修改状态未知：无法验证远端状态")
                return False
            if _repo_private_state(repository) is not private:
                if write_error is None:
                    print("仓库可见性验证失败：远端状态与请求不一致")
                else:
                    print(
                        "仓库可见性写请求状态未知："
                        "远端当前状态与请求不一致"
                    )
                return False
            return True
        except Exception as error:
            print(f"修改仓库可见性失败: {_sanitized_v5_api_error(error)}")
            return False

    def delete_repo(self, repo_id: str, confirmation: str) -> bool:
        """Delete one V5 repository and require verified remote absence."""
        try:
            if confirmation != repo_id:
                print("删除仓库失败: 确认仓库 ID 与目标不一致")
                return False
            credentials = config.get_credentials()
            if not credentials or not credentials.get('token'):
                print("❌ 未找到登录凭证")
                return False
            token = credentials['token']
            path = _atomgit_v5_repo_path(repo_id)
            repository = _atomgit_v5_get_json(path, token)
            if not isinstance(repository, dict):
                raise ValueError("repository response is malformed")

            delete_error = None
            try:
                _atomgit_v5_request_json("DELETE", path, token)
            except urllib.error.HTTPError as error:
                if 400 <= error.code < 500:
                    print(
                        f"删除仓库失败: {_sanitized_v5_api_error(error)}"
                    )
                    return False
                delete_error = error
            except Exception as error:
                delete_error = error

            try:
                _atomgit_v5_get_json(path, token)
            except urllib.error.HTTPError as error:
                if error.code == 404:
                    return True
                print("仓库删除请求状态未知：无法验证远端仓库是否仍存在")
                return False
            except Exception:
                print("仓库删除请求状态未知：无法验证远端仓库是否仍存在")
                return False

            if delete_error is not None:
                print(
                    f"删除仓库失败: {_sanitized_v5_api_error(delete_error)}"
                )
            else:
                print("仓库删除验证失败：远端仓库仍存在")
            return False
        except Exception as error:
            print(f"删除仓库失败: {_sanitized_v5_api_error(error)}")
            return False

    def create_branch(
        self, repo_id: str, branch_name: str, source: str = "main"
    ) -> bool:
        """Create one explicit branch and verify it through AtomGit V5."""
        try:
            credentials = config.get_credentials()
            if not credentials or not credentials.get('token'):
                print("❌ 未找到登录凭证")
                return False
            if not branch_name or not is_supported_upload_revision(branch_name):
                raise ValueError("invalid branch name")
            if not source or not is_supported_upload_revision(source):
                raise ValueError("invalid source revision")
            repo_path = _atomgit_v5_repo_path(repo_id)
            source_path = repo_path + "/commits/" + quote(source, safe="")
            source_payload = _atomgit_v5_get_json(
                source_path, credentials['token']
            )
            source_commit = _atomgit_v5_commit_sha(source_payload)
            if source_commit is None:
                print("创建分支失败: 无法解析来源 revision 的提交")
                return False
            base_path = repo_path + "/branches"
            write_error = None
            try:
                _atomgit_v5_request_json(
                    "POST",
                    base_path,
                    credentials['token'],
                    {"branch_name": branch_name, "refs": source},
                )
            except Exception as error:
                if _is_definitive_v5_write_error(error):
                    print(
                        "创建分支失败: " + _sanitized_v5_api_error(error)
                    )
                    return False
                write_error = error
            branch_path = base_path + "/" + quote(branch_name, safe="")
            try:
                payload = _atomgit_v5_get_json(
                    branch_path, credentials['token']
                )
            except Exception:
                print("分支创建状态未知：无法验证远端状态")
                return False
            name = payload.get("name") if isinstance(payload, dict) else None
            target_commit = _atomgit_v5_branch_commit_id(payload)
            if name != branch_name or target_commit != source_commit:
                if write_error is None:
                    print(
                        "分支创建验证失败：远端分支名称或来源提交"
                        "与请求不一致"
                    )
                else:
                    print(
                        "分支创建写请求状态未知：远端分支名称或"
                        "来源提交与请求不一致"
                    )
                return False
            return True
        except Exception as error:
            print(f"创建分支失败: {_sanitized_v5_api_error(error)}")
            return False
    
    def create_repo(self, 
                    repo_name: str,
                    repo_type: str = "model", 
                    private: bool = False,
                    exist_ok: bool = False) -> bool:
        """创建仓库；dataset 通过 AtomGit 的共享 model 兼容路由创建。"""
        try:
            credentials = config.get_credentials()
            if not credentials:
                print("❌ 未找到登录凭证")
                return False
            normalized_repo_id = self._normalize_repo_id(repo_name)
            if not exist_ok and _atomgit_repo_exists(
                normalized_repo_id, credentials['token']
            ):
                print("创建仓库失败[仓库已存在]")
                print("💡 建议: 如需幂等创建，请显式使用 --exist-ok")
                return False
            # 使用Hugging Face Hub SDK创建仓库
            # HF public creation can report success while AtomGit keeps the
            # repository private. Always create safely as private, then use the
            # V5 settings API and verify the explicitly requested visibility.
            create_repo(
                repo_id=normalized_repo_id,
                token=credentials['token'],
                repo_type=_atomgit_repo_type(repo_type),
                private=True,
                exist_ok=exist_ok,
            )
            if not self.set_repo_visibility(repo_name, private=private):
                requested_visibility = "私有" if private else "公开"
                print(
                    f"{requested_visibility}仓库创建未验证完成；"
                    "远端可能未达到目标可见性，"
                    "请立即使用 repo visibility 检查并设置目标状态"
                )
                return False
            return True
        except Exception as e:
            err_type, hint = _classify_create_repo_error(e)
            print(f"创建仓库失败[{err_type}]")
            print(f"💡 建议: {hint}")
            return False
    
    def upload_folder(self, file_path: Path, repo_id: str,
                   remote_path: str = None, message: str = None,
                   upload_timeout: Optional[float] = None,
                   progress_bar: bool = True,
                   path_in_repo: str = None,
                   repo_type: str = None,
                   revision: str = None,
                   ignore_patterns=None,
                   num_workers: int = 5) -> bool:
        """上传单个文件 - 使用Hugging Face Hub SDK

        优先使用 HF ``upload_file`` 直接以文件路径上传，避免旧实现中
        "先复制再上传"的额外本地拷贝开销；仅在 HF 版本过旧（无
        ``upload_file``）时回退到 ``upload_folder`` + 唯一系统临时目录。

        Args:
            path_in_repo: 仓库内目标目录前缀。为空/``./`` 时上传到仓库根目录；
                否则文件会被放到该前缀下（如 ``sub/`` → ``sub/<文件名>``）。
            repo_type: 仓库类型，``model`` 或 ``dataset``。为空时由 HF
                默认按 ``model`` 处理（保持既有行为）。
            revision: 上传目标 revision。AtomGit 当前仅支持空值或 ``main``；
                CLI 会在调用本方法前拒绝其他值。
            ignore_patterns: 单文件上传路径下该参数仅会匹配 ``file_path.name``，
                几乎不生效——主要对目录上传有意义。新实现（``upload_file``）
                不支持该参数，传入时若非空会回退到 ``upload_folder`` 旧路径
                以保留语义。
        """
        if not is_supported_upload_revision(revision):
            print("上传 revision 名称不合法，已拒绝上传")
            return False
        try:
            try:
                validate_upload_path_no_symlinks(file_path)
            except ValueError as error:
                print(str(error))
                return False
            if not file_path.exists():
                print(f"文件不存在: {file_path}")
                return False

            credentials = config.get_credentials()
            if not credentials:
                print("未找到登录凭证")
                return False

            # 规范化 path_in_repo（remote_path 为旧别名，向后兼容）
            try:
                pipr = normalize_path_in_repo(path_in_repo if path_in_repo is not None else remote_path)
            except ValueError as e:
                print(f"上传路径不合法: {e}")
                return False

            original_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT
            original_progress_state = _capture_progress_bar_state()
            _set_progress_bar(progress_bar)

            commit_message = message or "Upload folder using atomgit client"
            normalized_repo_id = self._normalize_repo_id(repo_id)
            # 使用 Monkey Patch 方式临时修改 huggingface_hub 的默认超时配置
            request_timeout = (
                upload_timeout
                if upload_timeout is not None
                else _RESUMABLE_DEFAULT_REQUEST_TIMEOUT
            )
            hf_constants.DEFAULT_REQUEST_TIMEOUT = request_timeout
            close_hf_session()

            try:
                # 路径2（推荐）：直接 upload_file，无本地拷贝
                if hf_upload_file is not None and not ignore_patterns:
                    # upload_file 需要完整的 path_in_repo（含文件名）
                    remote_file_path = f"{pipr}/{file_path.name}" if pipr else file_path.name
                    file_kwargs = dict(
                        path_or_fileobj=str(file_path),
                        path_in_repo=remote_file_path,
                        repo_id=normalized_repo_id,
                        token=credentials['token'],
                        commit_message=commit_message,
                    )
                    upload_repo_type = _atomgit_repo_type(repo_type)
                    if upload_repo_type is not None:
                        file_kwargs['repo_type'] = upload_repo_type
                    if revision is not None:
                        file_kwargs['revision'] = revision
                    hf_upload_file(**file_kwargs)
                    return True

                # 路径1（回退）：upload_folder + 临时目录拷贝（旧实现）
                # 触发条件：HF 版本过旧无 upload_file，或用户传了 ignore_patterns
                import tempfile
                with tempfile.TemporaryDirectory(prefix="atomgit-upload-") as temp_name:
                    temp_dir = Path(temp_name)
                    if pipr:
                        target_file = temp_dir / pipr / file_path.name
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        upload_path_in_repo = f"{pipr}/"
                    else:
                        target_file = temp_dir / file_path.name
                        upload_path_in_repo = "./"
                    import shutil
                    shutil.copy2(file_path, target_file)
                    upload_kwargs = dict(
                        repo_id=normalized_repo_id,
                        folder_path=str(temp_dir),
                        path_in_repo=upload_path_in_repo,
                        token=credentials['token'],
                        commit_message=commit_message,
                    )
                    upload_repo_type = _atomgit_repo_type(repo_type)
                    if upload_repo_type is not None:
                        upload_kwargs['repo_type'] = upload_repo_type
                    if revision is not None:
                        upload_kwargs['revision'] = revision
                    if ignore_patterns:
                        upload_kwargs['ignore_patterns'] = ignore_patterns
                    upload_folder(**upload_kwargs)
                    return True
            finally:
                hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
                close_hf_session()
                _restore_progress_bar_state(original_progress_state)
        except Exception as e:
            err_type, hint = _classify_upload_error(e, repo_id=repo_id)
            print(f"上传文件失败[{err_type}]")
            print(f"💡 建议: {hint}")
            return False

    def upload_directory(self, dir_path: Path, repo_id: str,
                        message: str = None, progress_callback=None,
                        upload_timeout: Optional[float] = None,
                        progress_bar: bool = True,
                        path_in_repo: str = None,
                        repo_type: str = None,
                        revision: str = None,
                        ignore_patterns=None,
                        resumable: bool = False,
                        num_workers: int = 5) -> bool:
        """上传目录 - 使用Hugging Face Hub SDK

        Args:
            path_in_repo: 仓库内目标目录前缀。为空/``./`` 时上传到仓库根目录；
                否则目录内容会被放到该前缀下。
            repo_type: 仓库类型，``model`` 或 ``dataset``。为空时由 HF
                默认按 ``model`` 处理（保持既有行为）。
            revision: 上传目标 revision。AtomGit 当前仅支持空值或 ``main``；
                CLI 会在调用本方法前拒绝其他值。
            ignore_patterns: 忽略的文件模式列表（fnmatch/glob 风格，如
                ``*.tmp``、``logs/``、``**/.DS_Store``）。为 None 时不忽略。
            resumable: 是否启用可断点续传/分块上传模式。为 True 时改用 HF
                ``upload_large_folder``：进程级元数据写入目录下
                ``.cache/.huggingface/``，中断后再次执行可自动续传；适合
                大目录。CLI 使用按上传身份隔离的私有持久投影；
                ``path_in_repo`` 非空时将源目录内容放到对应远端前缀下，同时
                保留 HF 元数据。该模式不支持单一
                ``message`` / ``commit_message``（会产生多次提交），且 HF
                要求 ``repo_type`` 必填，为空时默认 ``model``。
            num_workers: 上传 worker 数，默认为 5；适用于断点续传和普通目录上传。
        """
        if not is_supported_upload_revision(revision):
            print("上传 revision 名称不合法，已拒绝上传")
            return False
        try:
            try:
                validate_upload_path_no_symlinks(dir_path)
            except ValueError as error:
                print(str(error))
                return False
            if not dir_path.exists() or not dir_path.is_dir():
                print(f"目录不存在: {dir_path}")
                return False

            credentials = config.get_credentials()
            if not credentials:
                print("未找到登录凭证")
                return False

            # 规范化 path_in_repo
            try:
                pipr = normalize_path_in_repo(path_in_repo)
            except ValueError as e:
                print(f"上传路径不合法: {e}")
                return False

            original_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT
            original_progress_state = _capture_progress_bar_state()
            _set_progress_bar(progress_bar)

            try:
                commit_message = message or "Upload folder using atomgit client"
                request_timeout = (
                    upload_timeout
                    if upload_timeout is not None
                    else _RESUMABLE_DEFAULT_REQUEST_TIMEOUT
                )
                hf_constants.DEFAULT_REQUEST_TIMEOUT = request_timeout
                close_hf_session()

                selected_files = _collect_resumable_upload_files(
                    dir_path, ignore_patterns
                )
                batches = [
                    selected_files[index:index + 20]
                    for index in range(0, len(selected_files), 20)
                ] or [[]]
                batch_count = len(batches)
                total_files = len(selected_files)
                submitted_files = 0
                skipped_files = 0
                completed_files = 0
                _print_upload_batch_plan(total_files, batch_count)

                if resumable:
                    # 断点续传/分块上传：走 upload_large_folder
                    eff_repo_type = _atomgit_repo_type(repo_type) or "model"
                    normalized_repo_id = self._normalize_repo_id(repo_id)
                    upload_deadline = (
                        None
                        if upload_timeout is None
                        else time.monotonic() + upload_timeout
                    )
                    _validate_resumable_upload_target(
                        token=credentials['token'],
                        repo_id=normalized_repo_id,
                        repo_type=eff_repo_type,
                        revision=revision,
                    )
                    for batch_index, batch in enumerate(batches):
                        batch_number = batch_index + 1
                        batch_size = len(batch)
                        print(
                            f"[批次 {batch_number}/{batch_count}] 开始: "
                            f"{batch_size} 个文件",
                            flush=True,
                        )
                        selected_paths = {item[0] for item in batch}
                        upload_root = None
                        batch_skipped = 0
                        try:
                            upload_root = _prepare_resumable_upload_projection(
                                dir_path,
                                normalized_repo_id,
                                eff_repo_type,
                                revision,
                                pipr,
                                ignore_patterns=None,
                                selected_paths=selected_paths,
                                batch_key=str(batch_index),
                            )
                            batch_skipped = _resumable_committed_file_count(
                                upload_root, selected_paths, pipr
                            )
                            if batch_skipped:
                                print(
                                    f"[批次 {batch_number}/{batch_count}] "
                                    f"续传跳过: {batch_skipped} 个已确认完成文件",
                                    flush=True,
                                )

                            lf_kwargs = dict(
                                repo_id=normalized_repo_id,
                                folder_path=str(upload_root),
                                repo_type=eff_repo_type,
                                num_workers=num_workers or 5,
                            )
                            if revision is not None:
                                lf_kwargs['revision'] = revision
                            if ignore_patterns:
                                lf_kwargs['ignore_patterns'] = (
                                    _prefix_resumable_ignore_patterns(
                                        pipr, ignore_patterns
                                    )
                                )
                            # Even a fully committed projection must enter HF so
                            # repository existence and authorization are checked.
                            _execute_resumable_upload_process(
                                token=credentials['token'],
                                upload_kwargs=lf_kwargs,
                                request_timeout=request_timeout,
                                upload_deadline=upload_deadline,
                                upload_timeout=upload_timeout,
                                batch_context=(batch_number, batch_count),
                            )
                        except Exception:
                            confirmed_in_batch = batch_skipped
                            if upload_root is not None:
                                confirmed_in_batch = max(
                                    confirmed_in_batch,
                                    _resumable_committed_file_count(
                                        upload_root, selected_paths, pipr
                                    ),
                                )
                            skipped_files += batch_skipped
                            submitted_files += max(
                                0, confirmed_in_batch - batch_skipped
                            )
                            completed_files += confirmed_in_batch
                            remaining_files = total_files - completed_files
                            print(
                                f"[批次 {batch_number}/{batch_count}] 失败: "
                                f"累计确认完成 {completed_files}/{total_files}，"
                                f"剩余 {remaining_files}",
                                flush=True,
                            )
                            print(
                                "断点元数据已保留；修复问题后重新执行同一命令可继续上传",
                                flush=True,
                            )
                            _print_upload_batch_summary(
                                total_files,
                                submitted_files,
                                skipped_files,
                                completed_files,
                            )
                            raise

                        skipped_files += batch_skipped
                        newly_submitted = batch_size - batch_skipped
                        submitted_files += newly_submitted
                        completed_files += batch_size
                        print(
                            f"[批次 {batch_number}/{batch_count}] 成功: "
                            f"新增提交 {newly_submitted}，续传跳过 {batch_skipped}，"
                            f"累计完成 {completed_files}/{total_files}",
                            flush=True,
                        )
                else:
                    # 仓库内目标前缀：空 → "./"（根目录）
                    upload_path_in_repo = pipr + "/" if pipr else "./"
                    upload_kwargs = dict(
                        repo_id=self._normalize_repo_id(repo_id),
                        folder_path=str(dir_path),
                        path_in_repo=upload_path_in_repo,
                        token=credentials['token'],
                        commit_message=commit_message,
                    )
                    upload_repo_type = _atomgit_repo_type(repo_type)
                    if upload_repo_type is not None:
                        upload_kwargs['repo_type'] = upload_repo_type
                    if revision is not None:
                        upload_kwargs['revision'] = revision
                    for batch_index, batch in enumerate(batches):
                        batch_number = batch_index + 1
                        batch_size = len(batch)
                        print(
                            f"[批次 {batch_number}/{batch_count}] 开始: "
                            f"{batch_size} 个文件",
                            flush=True,
                        )
                        try:
                            if batch:
                                upload_kwargs['allow_patterns'] = [
                                    item[0].as_posix() for item in batch
                                ]
                            if ignore_patterns:
                                upload_kwargs['ignore_patterns'] = ignore_patterns
                            _upload_folder_with_workers(
                                upload_kwargs, num_workers or 5
                            )
                        except Exception:
                            remaining_files = total_files - completed_files
                            print(
                                f"[批次 {batch_number}/{batch_count}] 失败: "
                                f"累计确认完成 {completed_files}/{total_files}，"
                                f"剩余 {remaining_files}",
                                flush=True,
                            )
                            _print_upload_batch_summary(
                                total_files,
                                submitted_files,
                                skipped_files,
                                completed_files,
                            )
                            raise
                        submitted_files += batch_size
                        completed_files += batch_size
                        print(
                            f"[批次 {batch_number}/{batch_count}] 成功: "
                            f"新增提交 {batch_size}，续传跳过 0，"
                            f"累计完成 {completed_files}/{total_files}",
                            flush=True,
                        )

                _print_upload_batch_summary(
                    total_files,
                    submitted_files,
                    skipped_files,
                    completed_files,
                )

                return True
            finally:
                hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
                close_hf_session()
                _restore_progress_bar_state(original_progress_state)

        except Exception as e:
            err_type, hint = _classify_upload_error(e, repo_id=repo_id)
            print(f"上传目录失败[{err_type}]")
            print(f"💡 建议: {hint}")
            return False
    
    def download_repo(
        self,
        repo_id: str,
        local_path: Path = None,
        force_download: bool = False,
        repo_type: str = None,
        verify_checksum: bool = False,
        resume_download: bool = False,
        prune: bool = False,
    ) -> bool:
        """下载仓库到本地目录（公开仓库无需token）。

        绕过 huggingface_hub 的 snapshot_download：AtomGit hub 未实现
        repo_info 路由（GET /api/models/{repo} 返回 404），SDK 会在任何
        下载前中止；这里改为 list_repo_files + resolve 逐文件下载。
        """
        manifest_locks = ExitStack()
        try:
            normalized_repo_id = self._normalize_repo_id(repo_id)

            if local_path is None:
                local_path = Path.cwd() / repo_id.split('/')[-1]

            local_path.mkdir(parents=True, exist_ok=True)

            credentials = config.get_credentials()
            token = credentials['token'] if credentials and 'token' in credentials else None

            effective_type, files = _atomgit_list_repo_files(normalized_repo_id, token, repo_type)

            destinations = [
                (filename, _safe_download_destination(local_path, filename))
                for filename in files
            ]
            remote_files = set(files)
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
                print(
                    "⚠ 下载 manifest 不可用；本次下载文件不会纳入后续清理"
                )
            else:
                manifest_locks.enter_context(
                    _download_manifest_lock(manifest_path)
                )
                try:
                    manifest_exists, previously_managed = (
                        _load_download_manifest(manifest_path)
                    )
                except Exception:
                    manifest_locks.close()
                    if prune:
                        raise
                    manifest_available = False
                    manifest_exists, previously_managed = False, set()
                    print(
                        "⚠ 下载 manifest 不可用；本次下载文件不会纳入后续清理"
                    )
            downloaded_files = set()
            if not files:
                print("ℹ 仓库为空，没有可下载的文件；本地目录已创建")
            for filename, dest in destinations:
                if dest.exists() and not force_download:
                    if verify_checksum:
                        checksum = _atomgit_file_checksum(
                            normalized_repo_id, effective_type, filename, token
                        )
                        _verify_download_checksum(dest, checksum)
                        print(f"✓ checksum 校验通过: {filename}")
                        continue
                    print(f"⏭ 已存在，跳过（未校验内容；--force 可覆盖）: {filename}")
                    continue
                if resume_download:
                    _download_atomgit_file_resumable(
                        normalized_repo_id, effective_type, filename, dest, token
                    )
                    print(f"✓ 可续传下载完成并通过 checksum 校验: {filename}")
                    downloaded_files.add(filename)
                    continue
                checksum = None
                if verify_checksum:
                    checksum = _atomgit_file_checksum(
                        normalized_repo_id, effective_type, filename, token
                    )
                if checksum is None:
                    _download_atomgit_file(
                        normalized_repo_id, effective_type, filename, dest, token
                    )
                    print(f"✓ 已下载: {filename}")
                else:
                    _download_atomgit_file(
                        normalized_repo_id,
                        effective_type,
                        filename,
                        dest,
                        token,
                        checksum=checksum,
                    )
                    print(f"✓ 已下载并通过 checksum 校验: {filename}")
                downloaded_files.add(filename)
            if prune:
                if not manifest_exists:
                    print("ℹ 未找到历史下载 manifest；未删除未受管理的本地文件")
                removed = _prune_managed_download_files(
                    local_path, previously_managed - remote_files
                )
                managed_files = (
                    (previously_managed & remote_files) | downloaded_files
                )
                print(f"✓ 已清理受管理的本地多余文件: {removed}")
            else:
                managed_files = previously_managed | downloaded_files
            if prune:
                _write_download_manifest(manifest_path, managed_files)
            elif manifest_available:
                try:
                    _write_download_manifest(manifest_path, managed_files)
                except Exception:
                    print(
                        "⚠ 下载 manifest 写入失败；本次下载文件不会纳入后续清理"
                    )
            print("✅ 仓库下载成功")
            return True
        except Exception as e:
            print(f"仓库下载失败: {sanitized_download_error(e)}")
            return False
        finally:
            manifest_locks.close()

    def download_file(
        self,
        repo_id: str,
        filename: str,
        local_path: Path = None,
        force_download: bool = False,
        repo_type: str = None,
        verify_checksum: bool = False,
        resume_download: bool = False,
    ) -> bool:
        """下载单个文件到本地目录（公开仓库无需token）。"""
        try:
            normalized_repo_id = self._normalize_repo_id(repo_id)

            if local_path is None:
                local_path = Path.cwd()

            local_path.mkdir(parents=True, exist_ok=True)

            credentials = config.get_credentials()
            token = credentials['token'] if credentials and 'token' in credentials else None

            effective_type, files = _atomgit_list_repo_files(normalized_repo_id, token, repo_type)
            if filename not in files:
                print(f"✗ 文件不存在: {filename}")
                return False

            dest = _safe_download_destination(local_path, filename)
            if dest.exists() and not force_download:
                if verify_checksum:
                    checksum = _atomgit_file_checksum(
                        normalized_repo_id, effective_type, filename, token
                    )
                    _verify_download_checksum(dest, checksum)
                    print(f"✅ 文件 checksum 校验通过: {filename}")
                    return True
                print(f"⏭ 文件已存在，跳过: {filename}（未校验内容；--force 可覆盖）")
                return True
            if resume_download:
                _download_atomgit_file_resumable(
                    normalized_repo_id, effective_type, filename, dest, token
                )
                print("✅ 文件可续传下载完成，checksum 校验通过")
                return True
            checksum = None
            if verify_checksum:
                checksum = _atomgit_file_checksum(
                    normalized_repo_id, effective_type, filename, token
                )
            if checksum is None:
                _download_atomgit_file(
                    normalized_repo_id, effective_type, filename, dest, token
                )
                print("✅ 文件下载成功")
            else:
                _download_atomgit_file(
                    normalized_repo_id,
                    effective_type,
                    filename,
                    dest,
                    token,
                    checksum=checksum,
                )
                print("✅ 文件下载成功，checksum 校验通过")
            return True
        except Exception as e:
            print(f"文件下载失败: {sanitized_download_error(e)}")
            return False


    def get_repo_info(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Report the unsupported detail lookup without fabricating data."""
        print("获取仓库信息失败: 当前版本暂不支持仓库信息查询")
        return None


# 全局API实例
api = HuggingFaceAPI()
