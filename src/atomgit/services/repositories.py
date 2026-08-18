"""AtomGit V5 repository management and final-state verification."""

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

_ATOMGIT_V5_API_BASE = "https://api.atomgit.com/api/v5"
_ATOMGIT_V5_MAX_JSON_BYTES = 10 * 1024 * 1024


def _atomgit_open_url(request, timeout=60):
    """Fallback used only when the historical API module has not wired its opener."""
    return urllib.request.urlopen(request, timeout=timeout)


def _atomgit_repo_type(repo_type: str = None) -> str:
    """Map dataset create/transfer calls to AtomGit's shared model route."""
    return "model" if repo_type == "dataset" else repo_type


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
    return "/repos/{}/{}".format(quote(owner, safe=""), quote(repository, safe=""))


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
    return isinstance(error, urllib.error.HTTPError) and 400 <= error.code < 500


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


def _atomgit_repo_exists(repo_id: str, token: str) -> bool:
    """Probe AtomGit's shared repository tree before non-idempotent create."""
    try:
        HfApi(token=token).list_repo_files(repo_id, repo_type=None)
        return True
    except Exception as error:
        if _is_not_found_error(error):
            return False
        raise


def _is_not_found_error(error: Exception) -> bool:
    message = str(error).lower()
    return "404" in message or "not found" in message


def _classify_create_repo_error(error: Exception) -> tuple:
    """Classify one HF repository-creation failure into actionable output."""
    message = str(error)
    error_name = type(error).__name__

    credential_error = auth_error_kind(error)
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


class RepositoryServiceMixin:
    """Repository-management methods retained by the historical API client."""

    def _normalize_repo_id(self, repo_id: str) -> str:
        """标准化仓库 ID，兼容保留原有内部方法。"""
        return normalize_repo_id(repo_id)

    def list_repos(self):
        """List repositories available to the stored AtomGit credential."""
        try:
            credentials = config.get_credentials()
            if not credentials or not credentials.get("token"):
                print("❌ 未找到登录凭证")
                return None
            payload = _atomgit_v5_get_json("/user/repos", credentials["token"])
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
            if not credentials or not credentials.get("token"):
                print("❌ 未找到登录凭证")
                return False
            if not isinstance(private, bool):
                raise ValueError("private must be a boolean")
            path = _atomgit_v5_repo_path(repo_id)
            write_error = None
            try:
                _atomgit_v5_request_json(
                    "PATCH", path, credentials["token"], {"private": private}
                )
            except Exception as error:
                if _is_definitive_v5_write_error(error):
                    print("修改仓库可见性失败: " + _sanitized_v5_api_error(error))
                    return False
                write_error = error
            try:
                repository = _atomgit_v5_get_json(path, credentials["token"])
            except Exception:
                print("仓库可见性修改状态未知：无法验证远端状态")
                return False
            if _repo_private_state(repository) is not private:
                if write_error is None:
                    print("仓库可见性验证失败：远端状态与请求不一致")
                else:
                    print("仓库可见性写请求状态未知：远端当前状态与请求不一致")
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
            if not credentials or not credentials.get("token"):
                print("❌ 未找到登录凭证")
                return False
            token = credentials["token"]
            path = _atomgit_v5_repo_path(repo_id)
            repository = _atomgit_v5_get_json(path, token)
            if not isinstance(repository, dict):
                raise ValueError("repository response is malformed")

            delete_error = None
            try:
                _atomgit_v5_request_json("DELETE", path, token)
            except urllib.error.HTTPError as error:
                if 400 <= error.code < 500:
                    print(f"删除仓库失败: {_sanitized_v5_api_error(error)}")
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
                print(f"删除仓库失败: {_sanitized_v5_api_error(delete_error)}")
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
            if not credentials or not credentials.get("token"):
                print("❌ 未找到登录凭证")
                return False
            if not branch_name or not is_supported_upload_revision(branch_name):
                raise ValueError("invalid branch name")
            if not source or not is_supported_upload_revision(source):
                raise ValueError("invalid source revision")
            repo_path = _atomgit_v5_repo_path(repo_id)
            source_path = repo_path + "/commits/" + quote(source, safe="")
            source_payload = _atomgit_v5_get_json(source_path, credentials["token"])
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
                    credentials["token"],
                    {"branch_name": branch_name, "refs": source},
                )
            except Exception as error:
                if _is_definitive_v5_write_error(error):
                    print("创建分支失败: " + _sanitized_v5_api_error(error))
                    return False
                write_error = error
            branch_path = base_path + "/" + quote(branch_name, safe="")
            try:
                payload = _atomgit_v5_get_json(branch_path, credentials["token"])
            except Exception:
                print("分支创建状态未知：无法验证远端状态")
                return False
            name = payload.get("name") if isinstance(payload, dict) else None
            target_commit = _atomgit_v5_branch_commit_id(payload)
            if name != branch_name or target_commit != source_commit:
                if write_error is None:
                    print("分支创建验证失败：远端分支名称或来源提交与请求不一致")
                else:
                    print("分支创建写请求状态未知：远端分支名称或来源提交与请求不一致")
                return False
            return True
        except Exception as error:
            print(f"创建分支失败: {_sanitized_v5_api_error(error)}")
            return False

    def create_repo(
        self,
        repo_name: str,
        repo_type: str = "model",
        private: bool = False,
        exist_ok: bool = False,
    ) -> bool:
        """创建仓库；dataset 通过 AtomGit 的共享 model 兼容路由创建。"""
        try:
            credentials = config.get_credentials()
            if not credentials:
                print("❌ 未找到登录凭证")
                return False
            normalized_repo_id = self._normalize_repo_id(repo_name)
            if not exist_ok and _atomgit_repo_exists(
                normalized_repo_id, credentials["token"]
            ):
                print("创建仓库失败[仓库已存在]")
                print("💡 建议: 如需幂等创建，请显式使用 --exist-ok")
                return False
            create_repo(
                repo_id=normalized_repo_id,
                token=credentials["token"],
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
        except Exception as error:
            error_type, hint = _classify_create_repo_error(error)
            print(f"创建仓库失败[{error_type}]")
            print(f"💡 建议: {hint}")
            return False

    def get_repo_info(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Report the unsupported detail lookup without fabricating data."""
        print("获取仓库信息失败: 当前版本暂不支持仓库信息查询")
        return None
