#!/usr/bin/env python3
"""Strict offline repository creation contracts for API and CLI."""

import contextlib
import inspect
import io
import sys

import atomgit  # noqa: F401
from click.testing import CliRunner
from huggingface_hub import create_repo as real_create_repo


api_mod = sys.modules["atomgit.api"]
cli_mod = sys.modules["atomgit.cli"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    original_create = api_mod.create_repo
    original_credentials = api_mod.config.get_credentials
    calls = []

    def strict_create(**kwargs):
        inspect.signature(real_create_repo).bind(**kwargs)
        calls.append(kwargs)
        return "https://atomgit.com/user/repo"

    api_mod.create_repo = strict_create
    api_mod.config.get_credentials = lambda: {"token": "fake-stored-token"}
    try:
        for repo_type in ("model", "dataset"):
            result = api_mod.api.create_repo(
                f"user/{repo_type}-repo",
                repo_type=repo_type,
                private=True,
            )
            check(f"API private {repo_type} succeeds", result is True)
            call = calls[-1]
            expected_type = "model" if repo_type == "dataset" else repo_type
            check(
                f"API private {repo_type} uses compatible create route",
                call["repo_type"] == expected_type,
            )
            check(f"API private {repo_type} privacy forwarded", call["private"] is True)
            check(f"API private {repo_type} token forwarded", call["token"] == "fake-stored-token")
            check(f"API private {repo_type} is idempotent", call["exist_ok"] is True)

        before = len(calls)
        api_mod.config.get_credentials = lambda: None
        check(
            "API missing credentials fails",
            api_mod.api.create_repo("user/repo", private=True) is False,
        )
        check("API missing credentials makes no HF call", len(calls) == before)

        api_mod.config.get_credentials = lambda: {"token": "fake-stored-token"}

        def failing_create(**kwargs):
            inspect.signature(real_create_repo).bind(**kwargs)
            raise RuntimeError("offline create failure")

        api_mod.create_repo = failing_create
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            dep_failed = api_mod.api.create_repo("user/repo", private=True) is False
        check("API dependency failure is not false success", dep_failed)
        dep_output = captured.getvalue()
        check(
            "API dependency failure reports a safe category",
            "offline create failure" not in dep_output
            and "创建仓库失败[未知错误]" in dep_output
            and "建议" in dep_output,
            f"output={dep_output!r}",
        )

        def auth_failing_create(**kwargs):
            inspect.signature(real_create_repo).bind(**kwargs)
            raise RuntimeError(
                "401 Client Error. Unauthorized for url: "
                "https://hub.atomgit.com/api/repos/create"
            )

        api_mod.create_repo = auth_failing_create
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            auth_failed = api_mod.api.create_repo("user/repo", private=True) is False
        auth_output = captured.getvalue()
        check("API auth failure is not false success", auth_failed)
        check(
            "API auth failure suggests re-login",
            "认证失败" in auth_output and "atomgit login" in auth_output,
            f"output={auth_output!r}",
        )
    finally:
        api_mod.create_repo = original_create
        api_mod.config.get_credentials = original_credentials

    original_logged_in = cli_mod.config.is_logged_in
    original_api_create = cli_mod.api.create_repo
    cli_calls = []
    runner = CliRunner()
    try:
        cli_mod.config.is_logged_in = lambda: False
        result = runner.invoke(
            cli_mod.cli,
            ["repo", "create", "user/repo", "--type", "model", "--private"],
        )
        check("CLI requires login", result.exit_code == 1 and "登录" in result.output)

        cli_mod.config.is_logged_in = lambda: True
        cli_mod.api.create_repo = lambda name, repo_type, private: (
            cli_calls.append((name, repo_type, private)) or private
        )
        invalid_name = runner.invoke(
            cli_mod.cli,
            ["repo", "create", "invalid", "--type", "model", "--private"],
        )
        check("CLI invalid name exits nonzero", invalid_name.exit_code == 1)
        check("CLI invalid name makes no API call", not cli_calls)

        invalid_type = runner.invoke(
            cli_mod.cli,
            ["repo", "create", "user/repo", "--type", "space", "--private"],
        )
        check("CLI invalid type is a Click usage error", invalid_type.exit_code == 2)

        public = runner.invoke(
            cli_mod.cli,
            ["repo", "create", "user/repo", "--type", "model"],
        )
        check("CLI public creation reports failure", public.exit_code == 1)
        check("CLI public flag reaches API as false", cli_calls[-1] == ("user/repo", "model", False))

        private = runner.invoke(
            cli_mod.cli,
            ["repo", "create", "user/repo", "--type", "dataset", "--private"],
        )
        check("CLI private dataset succeeds", private.exit_code == 0)
        check("CLI private dataset arguments forwarded", cli_calls[-1] == ("user/repo", "dataset", True))

        cli_mod.api.create_repo = lambda *args, **kwargs: False
        failed = runner.invoke(
            cli_mod.cli,
            ["repo", "create", "user/repo", "--type", "model", "--private"],
        )
        check("CLI API failure exits nonzero", failed.exit_code == 1)
    finally:
        cli_mod.config.is_logged_in = original_logged_in
        cli_mod.api.create_repo = original_api_create

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
