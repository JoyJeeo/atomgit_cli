"""Credential-safe AtomGit resolve transport and HTTP framing."""

import os
import shutil
import socket
import ssl
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit

from ..infrastructure.validation import run_download_with_retry

_verify_download_checksum = None


def _is_not_found_error(error: Exception) -> bool:
    """Fallback until the historical API facade wires shared policy."""
    message = str(error).lower()
    return "404" in message or "not found" in message


def _atomgit_hf_endpoint() -> str:
    """AtomGit HF-compatible endpoint from the shared runtime policy."""
    return os.environ.get("HF_ENDPOINT", "https://hub.atomgit.com")


def _atomgit_resolve_url(
    repo_id: str, repo_type: str, filename: str, revision: str = "main"
) -> str:
    """Build a direct resolve URL that bypasses the missing repo_info route."""
    endpoint = _atomgit_hf_endpoint()
    prefix = "datasets/" if repo_type == "dataset" else ""
    # 文件名必须百分号编码（保留 / 分隔子目录），否则 urllib 发送
    # 请求行时按 ASCII 编码，中文文件名会抛 UnicodeEncodeError。
    encoded_filename = quote(filename, safe="/")
    encoded_revision = quote(revision or "main", safe="")
    return (
        f"{endpoint}/{prefix}{repo_id}/resolve/"
        f"{encoded_revision}/{encoded_filename}"
    )


def _atomgit_resolve_url_raw(
    repo_id: str, repo_type: str, filename: str, revision: str = "main"
) -> str:
    """Build a resolve URL that keeps the raw UTF-8 filename bytes.

    AtomGit resolve cannot match percent-encoded nested paths with non-ASCII
    filenames, but serves the same file when the raw UTF-8 bytes are sent in
    the request target. urllib refuses to send raw non-ASCII paths, so this
    variant is consumed by _atomgit_download_raw below.
    """
    endpoint = _atomgit_hf_endpoint()
    prefix = "datasets/" if repo_type == "dataset" else ""
    encoded_revision = quote(revision or "main", safe="")
    return f"{endpoint}/{prefix}{repo_id}/resolve/{encoded_revision}/{filename}"


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
        redirected = super().redirect_request(req, fp, code, msg, headers, target_url)
        if redirected is None:
            return None
        for header_name in ("Authorization", "Private-token"):
            if not any(
                key.lower() == header_name.lower() for key in redirected_headers
            ):
                redirected.remove_header(header_name)
                redirected.unredirected_hdrs.pop(header_name, None)
        return redirected


def _atomgit_open_url(request, timeout=60):
    """Open a direct download with the credential-safe redirect handler."""
    opener = urllib.request.build_opener(_AtomGitRedirectHandler())
    return opener.open(request, timeout=timeout)


def _atomgit_raw_http_request(method, host, port, scheme, raw_path, headers, timeout):
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
            sock.sendall(
                key.encode("latin-1") + b": " + str(value).encode("utf-8") + b"\r\n"
            )
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
    raw_path = (parts.path + (("?" + parts.query) if parts.query else "")).encode(
        "utf-8"
    )
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
                    parts = urlsplit(current_url)
                    host = parts.hostname
                    port = parts.port or (443 if parts.scheme == "https" else 80)
                    raw_path = (
                        parts.path + (("?" + parts.query) if parts.query else "")
                    ).encode("utf-8")
                    continue
                if status == 404:
                    raise urllib.error.HTTPError(
                        current_url, 404, "Not Found", response_headers, None
                    )
                if not 200 <= status < 300:
                    raise urllib.error.HTTPError(
                        current_url, status, "HTTP Error", response_headers, None
                    )
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
                _atomgit_download_raw(url, dest, headers, timeout=60, checksum=checksum)
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


_RESUMABLE_LFS_PREUPLOAD_MAX_ATTEMPTS = 3
