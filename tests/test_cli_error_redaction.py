#!/usr/bin/env python3
"""Ensure CLI-facing operation failures never echo dependency secrets."""

import contextlib
import io
import sys
import tempfile
from pathlib import Path

import atomgit  # noqa: F401


api_mod = sys.modules["atomgit.api"]
results = []
SECRET = "never-print-this-token"
SENSITIVE_ERROR = RuntimeError(
    f"Authorization: Bearer {SECRET} https://signed.example/file?token={SECRET}"
)


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))


def safe_output(name, operation):
    output = io.StringIO()
    escaped = None
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = operation()
    except Exception as error:
        result = None
        escaped = error
    text = output.getvalue()
    check(f"{name} contains exception", escaped is None, repr(escaped))
    check(
        f"{name} redacts credentials",
        SECRET not in text and "https://signed.example" not in text and "Authorization:" not in text,
        repr(text),
    )
    check(f"{name} reports failure", result in (False, None), repr(result))
    return text


def main():
    original_create = api_mod.create_repo
    original_exists = api_mod._atomgit_repo_exists
    original_upload_file = api_mod.hf_upload_file
    original_upload_folder = api_mod.upload_folder
    original_credentials = api_mod.config.get_credentials
    original_set_credentials = api_mod.config.set_credentials
    original_login_lookup = api_mod.api._get_login_user_by_token
    try:
        api_mod.config.get_credentials = lambda: {"token": "fake-stored-token"}
        api_mod._atomgit_repo_exists = lambda repo_id, token: False

        def fail(*args, **kwargs):
            raise SENSITIVE_ERROR

        api_mod.create_repo = fail
        create_text = safe_output(
            "create", lambda: api_mod.api.create_repo("user/repo", private=True)
        )
        check("create retains categorized guidance", "未知错误" in create_text and "建议" in create_text)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "file.bin"
            source.write_bytes(b"data")
            api_mod.hf_upload_file = fail
            file_text = safe_output(
                "file upload", lambda: api_mod.api.upload_folder(source, "user/repo")
            )
            check("file upload retains categorized guidance", "未知错误" in file_text and "建议" in file_text)

            upload_root = root / "folder"
            upload_root.mkdir()
            (upload_root / "data.bin").write_bytes(b"data")
            api_mod.upload_folder = fail
            directory_text = safe_output(
                "directory upload",
                lambda: api_mod.api.upload_directory(upload_root, "user/repo"),
            )
            check("directory upload retains categorized guidance", "未知错误" in directory_text and "建议" in directory_text)

        api_mod.api._get_login_user_by_token = lambda token: {"login": "tester"}
        api_mod.config.set_credentials = fail
        login_text = safe_output("login", lambda: api_mod.api.login("x" * 20))
        check("login has safe actionable message", "保存" in login_text or "登录" in login_text)

        api_mod.config.get_credentials = fail
        whoami_text = safe_output("whoami", api_mod.api.get_login_user)
        check("whoami has safe actionable message", "凭证" in whoami_text or "用户" in whoami_text)
    finally:
        api_mod.create_repo = original_create
        api_mod._atomgit_repo_exists = original_exists
        api_mod.hf_upload_file = original_upload_file
        api_mod.upload_folder = original_upload_folder
        api_mod.config.get_credentials = original_credentials
        api_mod.config.set_credentials = original_set_credentials
        api_mod.api._get_login_user_by_token = original_login_lookup

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
