"""Historical authentication compatibility methods.

The transport and identity parsing live in ``adapters.atomgit_v5``. This
module keeps the old API method signatures, output, and patchable names.
"""

import json  # noqa: F401 -- historical API patch surface
import urllib.error  # noqa: F401 -- historical API patch surface
import urllib.request  # noqa: F401 -- historical API patch surface
from typing import Any, Dict, Optional

from ..adapters.atomgit_v5 import (
    _ATOMGIT_IDENTITY_MAX_JSON_BYTES,
    AtomGitV5Adapter,
    _sanitized_v5_api_error,
)
from ..infrastructure.config import config


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
        return AtomGitV5Adapter().authenticate(token)

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


__all__ = [
    "AuthenticationServiceMixin",
    "_ATOMGIT_IDENTITY_MAX_JSON_BYTES",
    "_sanitized_v5_api_error",
]
