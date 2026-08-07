#!/usr/bin/env python3
"""Credential failures use status semantics without numeric false positives."""

import sys
import urllib.error

import atomgit  # noqa: F401


api_mod = sys.modules["atomgit.api"]
hub_mod = sys.modules["atomgit.atomgit_hub"]
utils_mod = sys.modules["atomgit.utils"]
results = []


def check(name, condition):
    results.append((name, condition))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")


class Response:
    def __init__(self, status_code):
        self.status_code = status_code


class StructuredError(Exception):
    def __init__(self, status_code, message="dependency failure"):
        super().__init__(message)
        self.response = Response(status_code)


def main():
    classify = getattr(utils_mod, "auth_error_kind", lambda error: None)
    auth_401 = StructuredError(401)
    permission_403 = StructuredError(403)

    check("structured 401 is authentication", classify(auth_401) == "authentication")
    check("structured 403 is permission", classify(permission_403) == "permission")
    check(
        "urllib 403 is permission",
        classify(
            urllib.error.HTTPError(
                "https://example.invalid", 403, "Denied", {}, None
            )
        )
        == "permission",
    )
    check(
        "explicit 401 text fallback is authentication",
        classify(RuntimeError("401 Client Error. Unauthorized."))
        == "authentication",
    )
    check(
        "explicit 403 text fallback is permission",
        classify(RuntimeError("HTTP 403: Forbidden.")) == "permission",
    )
    check(
        "incidental 403 filename is not credential failure",
        classify(RuntimeError("checksum mismatch for artifact403.bin")) is None
        and not utils_mod.is_auth_error(
            RuntimeError("checksum mismatch for artifact403.bin")
        ),
    )
    check(
        "incidental 401 count is not credential failure",
        not utils_mod.is_auth_error(RuntimeError("401 files processed")),
    )
    check(
        "local filesystem denial is not repository permission",
        classify(PermissionError(13, "Permission denied", "/tmp/model")) is None,
    )
    check("combined predicate keeps 401", utils_mod.is_auth_error(auth_401))
    check("combined predicate keeps 403", utils_mod.is_auth_error(permission_403))

    auth_download = utils_mod.sanitized_download_error(auth_401)
    permission_download = utils_mod.sanitized_download_error(permission_403)
    check(
        "download 401 recommends login",
        "认证失败" in auth_download and "重新登录" in auth_download,
    )
    check(
        "download 403 recommends repository permission",
        "权限不足" in permission_download
        and "仓库访问权限" in permission_download
        and "重新登录" not in permission_download,
    )

    upload_type, upload_hint = api_mod._classify_upload_error(permission_403)
    create_type, create_hint = api_mod._classify_create_repo_error(permission_403)
    check(
        "upload 403 is permission, not authentication",
        upload_type == "权限不足"
        and "仓库权限" in upload_hint
        and "重新登录" not in upload_hint,
    )
    check(
        "create 403 is permission, not authentication",
        create_type == "权限不足"
        and "创建权限" in create_hint
        and "重新登录" not in create_hint,
    )

    sdk_error = hub_mod._sdk_error(
        StructuredError(403, "forbidden token=secret"),
        "下载仓库",
        "user/repo",
    )
    check(
        "SDK keeps compatible type with permission message",
        isinstance(sdk_error, hub_mod.AtomGitAuthenticationError)
        and "权限不足" in str(sdk_error)
        and "token" not in str(sdk_error)
        and "secret" not in str(sdk_error),
    )

    passed = sum(condition for _, condition in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
