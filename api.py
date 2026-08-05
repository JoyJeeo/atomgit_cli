from typing import Optional, Dict, Any
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import quote, urljoin, urlsplit
import os
import shutil
import json
import socket
import ssl
import urllib.request
import urllib.error
import multiprocessing

try:
    from .runtime import configure_hf_environment
except ImportError:
    from runtime import configure_hf_environment

configure_hf_environment()


from huggingface_hub import (
    hf_hub_download, upload_folder, create_repo, snapshot_download,
    constants as hf_constants, HfApi,
)

try:
    from .config import config
    from .utils import (
        is_auth_error,
        is_supported_upload_revision,
        normalize_repo_id,
        normalize_path_in_repo,
        parse_ignore_patterns,
        run_download_with_retry,
        sanitized_download_error,
    )
except ImportError:
    from config import config
    from utils import (
        is_auth_error,
        is_supported_upload_revision,
        normalize_repo_id,
        normalize_path_in_repo,
        parse_ignore_patterns,
        run_download_with_retry,
        sanitized_download_error,
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


def _is_not_found_error(error: Exception) -> bool:
    message = str(error).lower()
    return "404" in message or "not found" in message


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

    api = HfApi(token=token)
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


def _safe_download_destination(local_root: Path, filename: str) -> Path:
    """Resolve a repository filename without allowing it to escape local_root."""
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

    resolved_root = Path(local_root).resolve()
    destination = resolved_root.joinpath(*raw_parts).resolve(strict=False)
    try:
        destination.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(
            f"仓库文件路径超出下载目录: {filename!r}"
        ) from error
    return destination


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
            if key.lower() != "authorization"
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
        if not any(
            key.lower() == "authorization" for key in redirected_headers
        ):
            redirected.remove_header("Authorization")
            redirected.unredirected_hdrs.pop("Authorization", None)
        return redirected


def _atomgit_open_url(request, timeout=60):
    """Open a direct download with the credential-safe redirect handler."""
    opener = urllib.request.build_opener(_AtomGitRedirectHandler())
    return opener.open(request, timeout=timeout)


def _atomgit_raw_http_get(host, port, scheme, raw_path, headers, timeout):
    """Send a raw-socket GET and return (status, headers, body, socket)."""
    context = ssl.create_default_context()
    sock = socket.create_connection((host, port), timeout=timeout)
    try:
        if scheme == "https":
            sock = context.wrap_socket(sock, server_hostname=host)
        sock.settimeout(timeout)
        sock.sendall(b"GET " + raw_path + b" HTTP/1.1\r\n")
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


def _atomgit_download_raw(url: str, dest: Path, headers, timeout: int = 60, max_redirects: int = 5) -> None:
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
    tmp = dest.with_name(dest.name + ".part")
    tmp.unlink(missing_ok=True)
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
                with open(tmp, "wb") as out:
                    _copy_framed_http_body(body, response_headers, out)
                tmp.replace(dest)
                return
            finally:
                try:
                    body.close()
                finally:
                    sock.close()
        raise urllib.error.HTTPError(current_url, 302, "Too many redirects", {}, None)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def _download_atomgit_file(repo_id: str, repo_type: str, filename: str, dest: Path, token: str) -> None:
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
            _atomgit_download_raw(url, dest, headers, timeout=60)
            return
        tmp = dest.with_name(dest.name + ".part")
        req = urllib.request.Request(url, headers=headers)
        with _atomgit_open_url(req, timeout=60) as resp, open(tmp, "wb") as out:
            shutil.copyfileobj(resp, out)
        tmp.replace(dest)

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


def _run_resumable_upload(token, kwargs, result_queue):
    """Run HF's resumable uploader in an isolated child process.

    The child is deliberately short-lived so a timed-out transfer can be
    terminated without leaving worker threads running in the CLI process.
    """
    try:
        HfApi(token=token).upload_large_folder(**kwargs)
        result_queue.put((True, None))
    except BaseException as exc:
        result_queue.put((False, (type(exc).__name__, str(exc))))


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

    # 请求参数错误
    if ename == "BadRequestError" or "400" in msg and "client error" in msg.lower():
        return "请求参数错误", "请求参数不合法。请检查 repo_id、repo_type、path_in_repo 等参数。"

    # 认证失败（401/403 且不属于上述仓库类错误）
    if "401" in msg or "403" in msg or "unauthorized" in msg.lower() or "forbidden" in msg.lower():
        return "认证失败", "认证失败或权限不足。请使用 'atomgit login' 重新登录获取有效 token。"

    # 超时
    if "timeout" in msg.lower() or "timed out" in msg.lower() or ename == "TimeoutError":
        return "请求超时", "请求超时。可使用 -t/--timeout 增大超时时间后重试。"

    # 网络连接
    if "connection" in msg.lower() or "connectionerror" in ename.lower() or "resolve" in msg.lower():
        return "网络连接失败", "无法连接到服务器。请检查网络或代理设置后重试。"

    # 其他
    return "未知错误", f"{type(e).__name__}: {msg}"


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

    # 认证失败：401/403 或 token 无效/无权限
    if (
        "401" in msg
        or "403" in msg
        or "unauthorized" in msg.lower()
        or "forbidden" in msg.lower()
        or "token not found" in msg.lower()
        or "no scopes" in msg.lower()
    ):
        return (
            "认证失败",
            "登录凭证无效或已过期。请使用 'atomgit login' 重新登录获取有效 token，再重试创建。",
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
    return "未知错误", f"{type(e).__name__}: {msg}"


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
        user_info = self._get_login_user_by_token(token)
        if not user_info:
            print("❌ 获取用户信息失败")
            return False
        config.set_credentials(token)
        print("✅ Token已保存")
        return True
    
    def _get_login_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
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
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    login = data.get('login')
                    if login and login.strip():
                        return {
                            'login': login,
                            'name': data.get('name'),
                            'email': data.get('email')
                        }
            return None
        except Exception as e:
            return None

    def get_login_user(self):
        credentials = config.get_credentials()
        if not credentials:
            print("❌ 未找到登录凭证")
            return None
        return self._get_login_user_by_token(credentials['token'])
    
    def create_repo(self, 
                    repo_name: str,
                    repo_type: str = "model", 
                    private: bool = False) -> bool:
        """创建仓库；dataset 通过 AtomGit 的共享 model 兼容路由创建。"""
        try:
            if not private:
                print("AtomGit 当前无法可靠验证公开仓库语义；请使用 --private 创建私有仓库")
                return False
            credentials = config.get_credentials()
            if not credentials:
                print("❌ 未找到登录凭证")
                return False
            # 使用Hugging Face Hub SDK创建仓库
            create_repo(
                repo_id=self._normalize_repo_id(repo_name),
                token=credentials['token'],
                repo_type=_atomgit_repo_type(repo_type),
                private=private,
                exist_ok=True
            )
            return True
        except Exception as e:
            err_type, hint = _classify_create_repo_error(e)
            print(f"创建仓库失败[{err_type}]: {e}")
            print(f"💡 建议: {hint}")
            return False
    
    def upload_folder(self, file_path: Path, repo_id: str,
                   remote_path: str = None, message: str = None,
                   upload_timeout: float = 300.0,
                   progress_bar: bool = True,
                   path_in_repo: str = None,
                   repo_type: str = None,
                   revision: str = None,
                   ignore_patterns=None) -> bool:
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
            print("AtomGit 当前仅支持默认 revision main，已拒绝上传")
            return False
        try:
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
            hf_constants.DEFAULT_REQUEST_TIMEOUT = upload_timeout

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
                _restore_progress_bar_state(original_progress_state)
        except Exception as e:
            err_type, hint = _classify_upload_error(e, repo_id=repo_id)
            print(f"上传文件失败[{err_type}]: {e}")
            print(f"💡 建议: {hint}")
            return False

    def upload_directory(self, dir_path: Path, repo_id: str,
                        message: str = None, progress_callback=None,
                        upload_timeout: float = 300.0,
                        progress_bar: bool = True,
                        path_in_repo: str = None,
                        repo_type: str = None,
                        revision: str = None,
                        ignore_patterns=None,
                        resumable: bool = False,
                        num_workers: int = None) -> bool:
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
                大目录。注意该模式下的限制（HF 既定）：
                (1) ``path_in_repo`` 不生效（需本地自行组织目录结构）；
                (2) ``message`` / ``commit_message`` 不生效（会产生多次提交）；
                (3) ``repo_type`` 必须有值（HF 要求），为空时默认 ``model``。
            num_workers: 仅 ``resumable=True`` 生效，并发 worker 数；为空时
                由 HF 默认决定。
        """
        if not is_supported_upload_revision(revision):
            print("AtomGit 当前仅支持默认 revision main，已拒绝上传")
            return False
        try:
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
                hf_constants.DEFAULT_REQUEST_TIMEOUT = upload_timeout

                if resumable:
                    # 断点续传/分块上传：走 upload_large_folder
                    eff_repo_type = _atomgit_repo_type(repo_type) or "model"
                    lf_kwargs = dict(
                        repo_id=self._normalize_repo_id(repo_id),
                        folder_path=str(dir_path),
                        repo_type=eff_repo_type,
                    )
                    if revision is not None:
                        lf_kwargs['revision'] = revision
                    if ignore_patterns:
                        lf_kwargs['ignore_patterns'] = ignore_patterns
                    if num_workers is not None:
                        lf_kwargs['num_workers'] = num_workers
                    if pipr:
                        # upload_large_folder 不支持 path_in_repo，显式提示
                        print("⚠ 注意：resumable 模式不支持 path_in_repo，"
                              "如需子目录请本地自行组织目录结构")
                    # 在隔离进程中运行，超时后可终止 HF 内部 worker，避免
                    # upload_large_folder 阻塞 CLI 或错误返回成功。
                    methods = multiprocessing.get_all_start_methods()
                    ctx = multiprocessing.get_context(
                        "fork" if "fork" in methods else "spawn"
                    )
                    result_queue = ctx.Queue()
                    process = ctx.Process(
                        target=_run_resumable_upload,
                        args=(credentials['token'], lf_kwargs, result_queue),
                    )
                    process.daemon = True
                    process.start()
                    process.join(upload_timeout)
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
                        name, message = error
                        raise RuntimeError(f"{name}: {message}")
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
                    if ignore_patterns:
                        upload_kwargs['ignore_patterns'] = ignore_patterns
                    upload_folder(**upload_kwargs)

                return True
            finally:
                hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
                _restore_progress_bar_state(original_progress_state)

        except Exception as e:
            err_type, hint = _classify_upload_error(e, repo_id=repo_id)
            print(f"上传目录失败[{err_type}]: {e}")
            print(f"💡 建议: {hint}")
            return False
    
    def download_repo(self, repo_id: str, local_path: Path = None, force_download: bool = False, repo_type: str = None) -> bool:
        """下载仓库到本地目录（公开仓库无需token）。

        绕过 huggingface_hub 的 snapshot_download：AtomGit hub 未实现
        repo_info 路由（GET /api/models/{repo} 返回 404），SDK 会在任何
        下载前中止；这里改为 list_repo_files + resolve 逐文件下载。
        """
        try:
            normalized_repo_id = self._normalize_repo_id(repo_id)

            if local_path is None:
                local_path = Path.cwd() / repo_id.split('/')[-1]

            local_path.mkdir(parents=True, exist_ok=True)

            credentials = config.get_credentials()
            token = credentials['token'] if credentials and 'token' in credentials else None

            effective_type, files = _atomgit_list_repo_files(normalized_repo_id, token, repo_type)
            if not files:
                print("ℹ 仓库为空，没有可下载的文件；本地目录已创建")
                return True

            destinations = [
                (filename, _safe_download_destination(local_path, filename))
                for filename in files
            ]
            for filename, dest in destinations:
                if dest.exists() and not force_download:
                    print(f"⏭ 已存在，跳过: {filename}")
                    continue
                _download_atomgit_file(normalized_repo_id, effective_type, filename, dest, token)
                print(f"✓ 已下载: {filename}")
            print("✅ 仓库下载成功")
            return True
        except Exception as e:
            print(f"仓库下载失败: {sanitized_download_error(e)}")
            return False

    def download_file(self, repo_id: str, filename: str, local_path: Path = None, force_download: bool = False, repo_type: str = None) -> bool:
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
                print(f"⏭ 文件已存在，跳过: {filename}（--force 可覆盖）")
                return True
            _download_atomgit_file(normalized_repo_id, effective_type, filename, dest, token)
            print("✅ 文件下载成功")
            return True
        except Exception as e:
            print(f"文件下载失败: {sanitized_download_error(e)}")
            return False


    def get_repo_info(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """获取仓库信息 - 此功能需要Hugging Face Hub SDK支持"""
        try:
            # 目前Hugging Face Hub SDK可能不直接支持获取仓库信息
            # 这里返回基础信息
            return {
                "repo_id": repo_id,
                "status": "需要Hugging Face Hub SDK支持"
            }
            
        except Exception as e:
            print(f"获取仓库信息失败: {e}")
            return None


# 全局API实例
api = HuggingFaceAPI()
