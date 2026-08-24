"""Historical repository compatibility methods.

The V5 transport, response validation, and Hugging Face boundary are owned by
``adapters.atomgit_v5``. These wrappers preserve the old API's signatures,
messages, return conventions, and patchable helper names.
"""

import json  # noqa: F401 -- historical API patch surface
import socket  # noqa: F401 -- historical API patch surface
import sys
import urllib.error  # noqa: F401 -- historical API patch surface
import urllib.request  # noqa: F401 -- historical API patch surface
from typing import Any, Dict, Optional
from urllib.parse import quote  # noqa: F401 -- historical API patch surface

from huggingface_hub import HfApi  # noqa: F401 -- historical API patch surface

from ..adapters.atomgit_v5 import (
    _ATOMGIT_V5_API_BASE,
    _ATOMGIT_V5_MAX_JSON_BYTES,
    AtomGitV5Adapter,
    RepositoryExistsError,
    _atomgit_repo_exists,
    _atomgit_repo_type,
    _atomgit_v5_branch_commit_id,
    _atomgit_v5_commit_sha,
    _atomgit_v5_get_json,
    _atomgit_v5_repo_path,
    _atomgit_v5_request_json,
    _classify_create_repo_error,
    _is_definitive_v5_write_error,
    _is_not_found_error,
    _repo_private_state,
    _sanitized_v5_api_error,
)
from ..infrastructure.config import config
from ..infrastructure.validation import normalize_repo_id

_v5_adapter = sys.modules[AtomGitV5Adapter.__module__]
create_repo = _v5_adapter.create_repo


class RepositoryServiceMixin:
    """Repository-management methods retained by the historical API client."""

    def _normalize_repo_id(self, repo_id: str) -> str:
        return normalize_repo_id(repo_id)

    def list_repos(self):
        try:
            credentials = config.get_credentials()
            if not credentials or not credentials.get("token"):
                print("❌ 未找到登录凭证")
                return None
            return AtomGitV5Adapter().list(credentials["token"])
        except Exception as error:
            print(f"获取仓库列表失败: {_sanitized_v5_api_error(error)}")
            return None

    def set_repo_visibility(self, repo_id: str, private: bool) -> bool:
        try:
            credentials = config.get_credentials()
            if not credentials or not credentials.get("token"):
                print("❌ 未找到登录凭证")
                return False
            if not isinstance(private, bool):
                raise ValueError("private must be a boolean")
            result = AtomGitV5Adapter().set_visibility(
                repo_id, private, credentials["token"]
            )
            if not result:
                print("仓库可见性验证失败：远端状态与请求不一致")
            return result
        except RuntimeError as error:
            if str(error) == "repository visibility write state is unknown":
                print("仓库可见性写请求状态未知：远端当前状态与请求不一致")
                return False
            if str(error) == "repository visibility state is unavailable":
                print("仓库可见性修改状态未知：无法验证远端状态")
                return False
            print(f"修改仓库可见性失败: {_sanitized_v5_api_error(error)}")
            return False
        except Exception as error:
            print(f"修改仓库可见性失败: {_sanitized_v5_api_error(error)}")
            return False

    def delete_repo(self, repo_id: str, confirmation: str) -> bool:
        try:
            if confirmation != repo_id:
                print("删除仓库失败: 确认仓库 ID 与目标不一致")
                return False
            credentials = config.get_credentials()
            if not credentials or not credentials.get("token"):
                print("❌ 未找到登录凭证")
                return False
            result = AtomGitV5Adapter().delete(
                repo_id, confirmation, credentials["token"]
            )
            if not result:
                print("仓库删除验证失败：远端仓库仍存在")
            return result
        except RuntimeError as error:
            if str(error) == "repository deletion state is unknown":
                print("仓库删除请求状态未知：无法验证远端仓库是否仍存在")
                return False
            print(f"删除仓库失败: {_sanitized_v5_api_error(error)}")
            return False
        except Exception as error:
            print(f"删除仓库失败: {_sanitized_v5_api_error(error)}")
            return False

    def create_branch(
        self, repo_id: str, branch_name: str, source: str = "main"
    ) -> bool:
        try:
            credentials = config.get_credentials()
            if not credentials or not credentials.get("token"):
                print("❌ 未找到登录凭证")
                return False
            adapter = AtomGitV5Adapter()
            result = adapter.create_branch(
                repo_id, branch_name, source, credentials["token"]
            )
            if not result:
                print("创建分支验证失败：远端分支名称或来源提交与请求不一致")
            return result
        except ValueError as error:
            if str(error) == "source revision commit is unavailable":
                print("创建分支失败: 无法解析来源 revision 的提交")
                return False
            print(f"创建分支失败: {_sanitized_v5_api_error(error)}")
            return False
        except RuntimeError as error:
            if str(error) == "branch creation state is unknown":
                print("分支创建状态未知：无法验证远端状态")
                return False
            print(f"创建分支失败: {_sanitized_v5_api_error(error)}")
            return False
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
        try:
            credentials = config.get_credentials()
            if not credentials:
                print("❌ 未找到登录凭证")
                return False
            normalized_repo_id = self._normalize_repo_id(repo_name)
            AtomGitV5Adapter().create(
                normalized_repo_id,
                repo_type,
                private,
                exist_ok,
                credentials["token"],
                visibility_callback=lambda _repo_id, requested_private: self.set_repo_visibility(
                    repo_name, requested_private
                ),
            )
            return True
        except RepositoryExistsError:
            print("创建仓库失败[仓库已存在]")
            print("💡 建议: 如需幂等创建，请显式使用 --exist-ok")
            return False
        except RuntimeError as error:
            if str(error) == "repository visibility could not be verified":
                requested_visibility = "私有" if private else "公开"
                print(
                    f"{requested_visibility}仓库创建未验证完成；"
                    "远端可能未达到目标可见性，"
                    "请立即使用 repo visibility 检查并设置目标状态"
                )
                return False
            error_type, hint = _classify_create_repo_error(error)
            print(f"创建仓库失败[{error_type}]")
            print(f"💡 建议: {hint}")
            return False
        except Exception as error:
            error_type, hint = _classify_create_repo_error(error)
            print(f"创建仓库失败[{error_type}]")
            print(f"💡 建议: {hint}")
            return False

    def get_repo_info(self, repo_id: str) -> Optional[Dict[str, Any]]:
        print("获取仓库信息失败: 当前版本暂不支持仓库信息查询")
        return None


__all__ = [
    "RepositoryServiceMixin",
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
