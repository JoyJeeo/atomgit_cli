"""Canonical AtomGit V5 and identity adapter.

This module owns the transport and Hugging Face boundary used by the shared
authentication and repository usecases. Historical ``services`` modules
delegate here so their public methods and patch seams remain compatible.
"""

import json
import socket
import urllib.error
import urllib.request
from typing import Any, Dict, Optional
from urllib.parse import quote

from huggingface_hub import HfApi, create_repo

from ..infrastructure.config import config
from ..infrastructure.validation import (
    auth_error_kind,
    is_supported_upload_revision,
    normalize_repo_id,
)

_ATOMGIT_IDENTITY_MAX_JSON_BYTES = 1024 * 1024
_ATOMGIT_V5_API_BASE = "https://api.atomgit.com/api/v5"
_ATOMGIT_V5_MAX_JSON_BYTES = 10 * 1024 * 1024


class RepositoryExistsError(RuntimeError):
    """Raised when non-idempotent creation finds an existing repository."""


def _atomgit_open_url(request, timeout=60):
    return urllib.request.urlopen(request, timeout=timeout)


def _atomgit_repo_type(repo_type: str = None) -> str:
    return "model" if repo_type == "dataset" else repo_type


def _atomgit_v5_request_json(
    method: str, path: str, token: str, body=None, timeout: int = 15
):
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
    return _atomgit_v5_request_json("GET", path, token, timeout=timeout)


def _atomgit_v5_repo_path(repo_id: str) -> str:
    normalized_repo_id = normalize_repo_id(repo_id)
    owner, separator, repository = normalized_repo_id.partition("/")
    if not separator or not owner or not repository:
        raise ValueError("invalid repository ID")
    return "/repos/{}/{}".format(quote(owner, safe=""), quote(repository, safe=""))


def _repo_private_state(payload):
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
    return isinstance(error, urllib.error.HTTPError) and 400 <= error.code < 500


def _atomgit_v5_commit_sha(payload: object) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    sha = payload.get("sha")
    return sha.strip() if isinstance(sha, str) and sha.strip() else None


def _atomgit_v5_branch_commit_id(payload: object) -> Optional[str]:
    if not isinstance(payload, dict) or not isinstance(payload.get("commit"), dict):
        return None
    commit_id = payload["commit"].get("id")
    return (
        commit_id.strip() if isinstance(commit_id, str) and commit_id.strip() else None
    )


def _is_not_found_error(error: Exception) -> bool:
    message = str(error).lower()
    return "404" in message or "not found" in message


def _atomgit_repo_exists(repo_id: str, token: str) -> bool:
    try:
        HfApi(token=token).list_repo_files(repo_id, repo_type=None)
        return True
    except Exception as error:
        if _is_not_found_error(error):
            return False
        raise


def _classify_create_repo_error(error: Exception) -> tuple:
    message = str(error)
    error_name = type(error).__name__
    credential_error = auth_error_kind(error)
    if isinstance(error, RepositoryExistsError) or "already exists" in message.lower():
        return "仓库已存在", "如需幂等创建，请显式使用 --exist-ok。"
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
    if error_name == "BadRequestError" or (
        "400" in message and "client error" in message.lower()
    ):
        return (
            "请求参数错误",
            "仓库参数不合法。请检查 repo_name 格式（username/repo-name）与 --type 取值。",
        )
    if (
        "timeout" in message.lower()
        or "timed out" in message.lower()
        or error_name == "TimeoutError"
    ):
        return "请求超时", "请求超时。请检查网络后重试。"
    if (
        "connection" in message.lower()
        or "connectionerror" in error_name.lower()
        or "resolve" in message.lower()
    ):
        return "网络连接失败", "无法连接到服务器。请检查网络或代理设置后重试。"
    return "未知错误", "服务返回了未识别的错误；请稍后重试，仍失败时联系平台支持。"


class AtomGitV5Adapter:
    """Adapt direct V5 and Hugging Face calls to shared core ports."""

    def create(
        self,
        repo_id: str,
        repo_type: str,
        private: bool,
        exist_ok: bool,
        token: str = None,
        visibility_callback=None,
    ):
        if not token:
            raise ValueError("missing AtomGit credential")
        if not exist_ok and _atomgit_repo_exists(repo_id, token):
            raise RepositoryExistsError("repository already exists")
        result = create_repo(
            repo_id=repo_id,
            token=token,
            private=True,
            repo_type=_atomgit_repo_type(repo_type),
            exist_ok=exist_ok,
        )
        if visibility_callback is None:
            verified = self.set_visibility(repo_id, private, token)
        else:
            verified = visibility_callback(repo_id, private)
        if not verified:
            raise RuntimeError("repository visibility could not be verified")
        return result

    def list(self, token: str):
        payload = _atomgit_v5_get_json("/user/repos", token)
        if isinstance(payload, dict):
            for key in ("data", "repositories"):
                if isinstance(payload.get(key), list):
                    payload = payload[key]
                    break
        if not isinstance(payload, list) or not all(
            isinstance(item, dict) for item in payload
        ):
            raise ValueError("repository collection is malformed")
        return payload

    def set_visibility(self, repo_id: str, private: bool, token: str) -> bool:
        path = _atomgit_v5_repo_path(repo_id)
        write_error = None
        try:
            _atomgit_v5_request_json("PATCH", path, token, {"private": private})
        except Exception as error:
            if _is_definitive_v5_write_error(error):
                raise
            write_error = error
        try:
            payload = _atomgit_v5_get_json(path, token)
        except Exception as error:
            raise RuntimeError("repository visibility state is unavailable") from error
        if _repo_private_state(payload) is not private:
            if write_error is not None:
                raise RuntimeError("repository visibility write state is unknown")
            return False
        return True

    def create_branch(self, repo_id: str, branch: str, source: str, token: str) -> bool:
        if not branch or not is_supported_upload_revision(branch):
            raise ValueError("invalid branch name")
        if not source or not is_supported_upload_revision(source):
            raise ValueError("invalid source revision")
        repo_path = _atomgit_v5_repo_path(repo_id)
        source_payload = _atomgit_v5_get_json(
            repo_path + "/commits/" + quote(source, safe=""), token
        )
        source_commit = _atomgit_v5_commit_sha(source_payload)
        if source_commit is None:
            raise ValueError("source revision commit is unavailable")
        base_path = repo_path + "/branches"
        write_error = None
        try:
            _atomgit_v5_request_json(
                "POST", base_path, token, {"branch_name": branch, "refs": source}
            )
        except Exception as error:
            if _is_definitive_v5_write_error(error):
                raise
            write_error = error
        try:
            payload = _atomgit_v5_get_json(
                base_path + "/" + quote(branch, safe=""), token
            )
        except Exception as error:
            raise RuntimeError("branch creation state is unknown") from error
        verified = (
            isinstance(payload, dict)
            and payload.get("name") == branch
            and _atomgit_v5_branch_commit_id(payload) == source_commit
        )
        if not verified and write_error is not None:
            raise RuntimeError("branch creation state is unknown")
        return verified

    def delete(self, repo_id: str, confirmation: str, token: str) -> bool:
        path = _atomgit_v5_repo_path(repo_id)
        repository = _atomgit_v5_get_json(path, token)
        if not isinstance(repository, dict):
            raise ValueError("repository response is malformed")
        delete_error = None
        try:
            _atomgit_v5_request_json("DELETE", path, token)
        except urllib.error.HTTPError as error:
            if 400 <= error.code < 500:
                raise
            delete_error = error
        except Exception as error:
            delete_error = error
        try:
            _atomgit_v5_get_json(path, token)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return True
            raise RuntimeError("repository deletion state is unknown")
        except Exception as error:
            raise RuntimeError("repository deletion state is unknown") from error
        if delete_error is not None:
            raise RuntimeError("repository deletion state is unknown")
        return False

    def authenticate(self, token: str) -> Dict[str, Any]:
        if not token:
            raise ValueError("missing AtomGit credential")
        api_url = "https://atomgit.com/api/v5/user"
        request = urllib.request.Request(
            api_url,
            headers={
                "Authorization": token,
                "User-Agent": "atomgit-cli",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=10) as response:
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
        data = json.loads(payload.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("identity response is malformed")
        login = data.get("login")
        if not isinstance(login, str) or not login.strip():
            raise ValueError("identity response is missing login")
        return {"login": login, "name": data.get("name"), "email": data.get("email")}

    def current_identity(self, token: str):
        return self.authenticate(token)

    def clear(self):
        config.clear_credentials()


__all__ = [
    "AtomGitV5Adapter",
    "RepositoryExistsError",
    "_ATOMGIT_IDENTITY_MAX_JSON_BYTES",
    "_ATOMGIT_V5_API_BASE",
    "_ATOMGIT_V5_MAX_JSON_BYTES",
    "_atomgit_repo_exists",
    "_atomgit_repo_type",
    "_atomgit_v5_branch_commit_id",
    "_atomgit_v5_commit_sha",
    "_atomgit_v5_get_json",
    "_atomgit_v5_repo_path",
    "_atomgit_v5_request_json",
    "_classify_create_repo_error",
    "_is_definitive_v5_write_error",
    "_is_not_found_error",
    "_repo_private_state",
    "_sanitized_v5_api_error",
]
