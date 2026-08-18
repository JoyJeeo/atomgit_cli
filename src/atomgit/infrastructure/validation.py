"""Input validation and bounded error-classification policy."""

import os
import re
import urllib.error
from pathlib import Path
from typing import List, Optional

DEFAULT_CLI_UPLOAD_IGNORE_PATTERNS = (
    "._*",
    "**/._*",
    ".DS_Store",
    "**/.DS_Store",
)

_AUTH_STATUS_PATTERNS = (
    re.compile(
        r"\b(?:http(?:\s+status)?|status(?:\s+code)?)\s*[:=]?\s*(401|403)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(401|403)\s+(?:client\s+error|unauthorized|forbidden)\b",
        re.IGNORECASE,
    ),
)

_REPO_ID_ERROR = "仓库ID格式不正确，应为: username/repo-name"
_REPO_SEGMENT_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-."
)


def _structured_http_status(error: Exception) -> Optional[int]:
    """Read a dependency HTTP status without interpreting arbitrary numbers."""
    response = getattr(error, "response", None)
    for candidate in (
        getattr(response, "status_code", None),
        getattr(response, "status", None),
        getattr(error, "status_code", None),
    ):
        if isinstance(candidate, int) and not isinstance(candidate, bool):
            return candidate
    if isinstance(error, urllib.error.HTTPError):
        return error.code
    return None


def auth_error_kind(error: Exception) -> Optional[str]:
    """Return ``authentication`` or ``permission`` from bounded evidence."""
    status = _structured_http_status(error)
    if status == 401:
        return "authentication"
    if status == 403:
        return "permission"

    message = str(error).lower()
    for pattern in _AUTH_STATUS_PATTERNS:
        match = pattern.search(message)
        if match:
            return "authentication" if match.group(1) == "401" else "permission"
    if any(
        marker in message
        for marker in (
            "unauthorized",
            "authentication failed",
            "invalid token",
            "token expired",
            "expired token",
            "token not found",
            "invalid username or password",
        )
    ):
        return "authentication"
    if any(
        marker in message for marker in ("forbidden", "no scopes", "insufficient scope")
    ):
        return "permission"
    return None


def is_auth_error(error: Exception) -> bool:
    """Compatibility predicate for authentication and permission failures."""
    return auth_error_kind(error) is not None


def is_retryable_download_error(error: Exception) -> bool:
    error_name = type(error).__name__
    message = str(error).lower()
    return error_name in {
        "ChunkedEncodingError",
        "ConnectError",
        "ConnectionError",
        "ReadError",
        "ReadTimeout",
        "RemoteProtocolError",
        "DownloadChecksumMismatchError",
    } or any(
        marker in message
        for marker in (
            "incomplete message body",
            "peer closed connection",
            "connection reset",
            "connection aborted",
            "read timed out",
        )
    )


def run_download_with_retry(operation):
    """Retry once after a retryable connection or integrity failure."""
    try:
        return operation()
    except Exception as error:
        if not is_retryable_download_error(error):
            raise
    return operation()


def sanitized_download_error(error: Exception) -> str:
    """Return an actionable category without exposing remote or signed URLs."""
    if "仓库类型不明确" in str(error):
        return "仓库类型不明确，请使用 --repo-type model 或 dataset"
    if "download manifest is already in use" in str(error):
        return "同一目标目录已有下载任务，请等待完成后重试"
    credential_error = auth_error_kind(error)
    if credential_error == "authentication":
        return "认证失败，请重新登录后重试"
    if credential_error == "permission":
        return "权限不足，请检查仓库访问权限"
    message = str(error).lower()
    if "checksum metadata" in message:
        return "服务未提供受支持的 checksum，无法完成校验"
    if type(error).__name__ == "DownloadChecksumMismatchError":
        return "checksum 校验失败，文件未被替换；请使用 --force 重新下载"
    if is_retryable_download_error(error):
        return "下载连接中断，自动重试后仍失败，请重新执行下载命令"
    if "404" in message or "not found" in message:
        return "仓库、文件或 revision 不存在"
    if "timeout" in message or "timed out" in message:
        return "下载请求超时，请检查网络后重试"
    return f"下载失败（{type(error).__name__}）"


def _repo_id_parts(repo_id: str) -> List[str]:
    """Parse one unambiguous repository ID or raise a public-safe error."""
    if not isinstance(repo_id, str):
        raise ValueError(_REPO_ID_ERROR)
    if any(ord(character) < 32 or ord(character) == 127 for character in repo_id):
        raise ValueError(_REPO_ID_ERROR)
    if "%" in repo_id or "\\" in repo_id:
        raise ValueError(_REPO_ID_ERROR)
    parts = repo_id.split("/")
    if len(parts) < 2 or any(
        not part
        or part in (".", "..")
        or any(character not in _REPO_SEGMENT_CHARS for character in part)
        for part in parts
    ):
        raise ValueError(_REPO_ID_ERROR)
    return parts


def validate_repo_name(repo_name: str) -> bool:
    """Return whether a repository ID has one safe, literal interpretation."""
    try:
        _repo_id_parts(repo_name)
    except ValueError:
        return False
    return True


def validate_repo_type(repo_type: str) -> bool:
    """验证仓库类型"""
    return repo_type in ["model", "dataset"]


def is_supported_upload_revision(revision: Optional[str]) -> bool:
    """Return whether a revision has one safe Git-ref interpretation."""
    if revision in (None, ""):
        return True
    if not isinstance(revision, str) or revision == "@":
        return False
    if (
        revision.startswith(("/", "."))
        or revision.endswith(("/", ".", ".lock"))
        or ".." in revision
        or "@{" in revision
        or "//" in revision
        or any(character in revision for character in " ~^:?*[\\")
        or any(ord(character) < 32 or ord(character) == 127 for character in revision)
    ):
        return False
    return all(part and not part.startswith(".") for part in revision.split("/"))


def normalize_repo_id(repo_id: str) -> str:
    """Map AtomGit multi-level names to its HF-compatible repository ID."""
    parts = _repo_id_parts(repo_id)
    if len(parts) < 3:
        return repo_id
    return f"{parts[0]}-{parts[1]}/{'/'.join(parts[2:])}"


def normalize_path_in_repo(path_in_repo: Optional[str]) -> Optional[str]:
    """Normalize a safe upload repository prefix."""
    if not path_in_repo:
        return None
    parts = [
        part
        for part in path_in_repo.replace("\\", "/").split("/")
        if part and part != "."
    ]
    if ".." in parts:
        raise ValueError("path_in_repo 不能包含 '..'（禁止路径穿越）")
    return "/".join(parts) if parts else None


def parse_ignore_patterns(raw: Optional[str]) -> Optional[List[str]]:
    """Parse the CLI comma-separated ignore option."""
    if not raw:
        return None
    seen = set()
    patterns = []
    for pattern in raw.split(","):
        pattern = pattern.strip()
        if pattern and pattern not in seen:
            seen.add(pattern)
            patterns.append(pattern)
    return patterns or None


def effective_cli_upload_ignore_patterns(user_patterns=None) -> List[str]:
    """Return CLI directory-upload defaults plus user patterns, in order."""
    seen = set()
    patterns = []
    for pattern in (*DEFAULT_CLI_UPLOAD_IGNORE_PATTERNS, *(user_patterns or ())):
        if pattern not in seen:
            seen.add(pattern)
            patterns.append(pattern)
    return patterns


def is_macos_metadata_file(path) -> bool:
    """Return whether one selected file is AppleDouble or Finder metadata."""
    name = Path(path).name
    return name == ".DS_Store" or name.startswith("._")


def validate_upload_path_no_symlinks(upload_path: Path) -> None:
    """Reject an upload root or tree containing any symbolic link."""
    upload_path = Path(upload_path)
    if upload_path.is_symlink():
        raise ValueError("上传路径包含符号链接，已拒绝上传: .")
    if not upload_path.is_dir():
        return

    def raise_walk_error(error):
        raise error

    try:
        for root, directory_names, filenames in os.walk(
            str(upload_path),
            topdown=True,
            onerror=raise_walk_error,
            followlinks=False,
        ):
            root_path = Path(root)
            for name in directory_names + filenames:
                candidate = root_path / name
                if candidate.is_symlink():
                    relative = candidate.relative_to(upload_path).as_posix()
                    raise ValueError(f"上传路径包含符号链接，已拒绝上传: {relative}")
    except OSError as error:
        raise ValueError("无法安全检查上传路径，已拒绝上传") from error
