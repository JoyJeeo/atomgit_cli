"""Strong download metadata and checksum verification."""

import hashlib
import urllib.error
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from huggingface_hub import get_hf_file_metadata

from . import transport as _transport
from .transport import (
    _atomgit_hf_endpoint,
    _atomgit_raw_http_head,
    _atomgit_resolve_url,
    _atomgit_resolve_url_raw,
    _download_url_origin,
    _prepare_download_redirect,
)


def _is_not_found_error(error: Exception) -> bool:
    """Fallback until the historical API facade wires shared policy."""
    message = str(error).lower()
    return "404" in message or "not found" in message


class DownloadChecksumMismatchError(OSError):
    """Downloaded or existing bytes do not match repository metadata."""


class DownloadChecksumMetadataError(ValueError):
    """AtomGit did not provide a supported strong checksum."""


def _atomgit_file_checksum(
    repo_id: str, repo_type: str, filename: str, token: str
) -> tuple:
    """Return (algorithm, digest, size) from AtomGit resolve metadata."""
    checksum, _ = _atomgit_file_download_metadata(repo_id, repo_type, filename, token)
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
        return _atomgit_file_download_metadata_raw(repo_id, repo_type, filename, token)
    checksum = _checksum_from_hf_metadata(metadata)
    location = urljoin(resolve_url, getattr(metadata, "location", None) or resolve_url)
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


_transport._verify_download_checksum = _verify_download_checksum


def _raw_metadata_size(response_headers) -> int:
    """Read one unambiguous nonnegative file size from metadata headers."""
    values = []
    for name in ("x-linked-size", "content-length"):
        value = response_headers.get(name)
        if value is None:
            continue
        if not value or any(character not in "0123456789" for character in value):
            raise DownloadChecksumMetadataError("checksum metadata is unavailable")
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
        raw_path = (parts.path + (("?" + parts.query) if parts.query else "")).encode(
            "utf-8"
        )
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
                response_headers.get("x-linked-etag") or response_headers.get("etag"),
                _raw_metadata_size(response_headers),
            )
            return checksum, current_url
        finally:
            try:
                body.close()
            finally:
                sock.close()
    raise urllib.error.HTTPError(current_url, 302, "Too many redirects", {}, None)
