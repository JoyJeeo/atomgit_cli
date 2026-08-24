"""Canonical private resumable download state and transfer adapter."""

import hashlib
import os
import shutil
import tempfile
import time
import urllib.error
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

from huggingface_hub.file_download import http_get as hf_http_get

from .integrity import (
    DownloadChecksumMismatchError,
    _atomgit_file_download_metadata,
    _verify_download_checksum,
)
from .transport import (
    _atomgit_hf_endpoint,
    _atomgit_raw_http_get,
    _atomgit_resolve_url,
    _atomgit_resolve_url_raw,
    _copy_framed_http_body,
    _prepare_download_redirect,
)


def _resume_cache_root() -> Path:
    """Return the private cache used only for incomplete CLI downloads."""
    hf_home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "atomgit"))
    root = hf_home / "resume"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    return root


def _resume_cache_identity(
    repo_id: str,
    repo_type: str,
    filename: str,
    revision: str = "main",
) -> str:
    identity = "\0".join(
        (_atomgit_hf_endpoint(), repo_id, repo_type, revision or "main", filename)
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
        raw_path = (parts.path + (("?" + parts.query) if parts.query else "")).encode(
            "utf-8"
        )
        status, response_headers, body, sock = _atomgit_raw_http_get(
            host, port, parts.scheme, raw_path, current_headers, timeout
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
            if resume_size and status == 206:
                _parse_content_range(
                    response_headers.get("content-range"),
                    resume_size,
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
    raise urllib.error.HTTPError(current_url, 302, "Too many redirects", {}, None)


def _download_atomgit_file_resumable(
    repo_id: str,
    repo_type: str,
    filename: str,
    destination: Path,
    token: str,
    revision: str = "main",
) -> None:
    """Persist an interrupted range download and atomically install it."""
    checksum, _ = _atomgit_file_download_metadata(
        repo_id, repo_type, filename, token, revision
    )
    _, expected_digest, expected_size = checksum
    cache_root = _resume_cache_root()
    identity = _resume_cache_identity(repo_id, repo_type, filename, revision)
    partial_path = cache_root / f"{identity}.{expected_digest}.part"
    lock_path = cache_root / f"{identity}.lock"
    headers = {"User-Agent": "atomgit-cli", "Accept": "*/*"}
    resolve_url = _atomgit_resolve_url(repo_id, repo_type, filename, revision)
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
                                    repo_id, repo_type, filename, revision
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
            _copy_resumed_file_to_destination(partial_path, destination, checksum)
            partial_path.unlink(missing_ok=True)
            return
    raise RuntimeError("download resume failed")
