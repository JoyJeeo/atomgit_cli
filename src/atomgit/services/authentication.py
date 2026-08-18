"""Bounded AtomGit authentication and stored-identity service."""

import json
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from ..infrastructure.config import config

_ATOMGIT_IDENTITY_MAX_JSON_BYTES = 1024 * 1024


class AuthenticationServiceMixin:
    """Authentication methods retained by the historical API client."""

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
            config.set_credentials(token, username=user_info["login"])
        except Exception:
            print("❌ 登录凭证保存失败，请检查配置目录权限后重试")
            return False
        print("✅ Token已保存")
        return True

    def _get_login_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        if not token:
            print("❌ 未找到登录凭证")
            return None
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
        return {
            "login": login,
            "name": data.get("name"),
            "email": data.get("email"),
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
            user_info = self._get_login_user_by_token(credentials["token"])
        except Exception as error:
            print(f"❌ 获取用户信息失败: {_sanitized_v5_api_error(error)}")
            return None
        if not user_info:
            print("❌ 获取用户信息失败: AtomGit API 响应格式无效")
            return None
        return user_info


# Wired to the repository owner by atomgit.api after both owners load. Keeping
# this as a module global preserves the former direct old-path patch seam.
def _sanitized_v5_api_error(error: Exception) -> str:
    from .repositories import _sanitized_v5_api_error as implementation

    return implementation(error)
