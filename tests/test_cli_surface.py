#!/usr/bin/env python3
"""Offline coverage for every advertised AtomGit CLI command surface."""

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import atomgit  # noqa: F401
from click.testing import CliRunner


cli_mod = sys.modules["atomgit.cli"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    runner = CliRunner()

    root_help = runner.invoke(cli_mod.cli, ["--help"])
    check("root help succeeds", root_help.exit_code == 0)
    for command in (
        "login",
        "logout",
        "whoami",
        "repo",
        "upload",
        "download",
        "download-file",
        "config-show",
    ):
        check(f"root help lists {command}", command in root_help.output)

    version = runner.invoke(cli_mod.cli, ["--version"])
    check(
        "version succeeds",
        version.exit_code == 0 and "1.0.6" in version.output,
    )

    for command in (
        "login", "logout", "whoami", "repo", "upload", "download",
        "download-file", "config-show",
    ):
        result = runner.invoke(cli_mod.cli, [command, "--help"])
        check(f"{command} help succeeds", result.exit_code == 0, result.output[-200:])
        if command == "whoami":
            check("whoami help describes the command", "显示当前登录用户" in result.output)
    create_help = runner.invoke(cli_mod.cli, ["repo", "create", "--help"])
    check("repo create help succeeds", create_help.exit_code == 0)

    original_login = cli_mod.api.login
    original_git_available = cli_mod.check_git_available
    original_setup = cli_mod.setup_git_credentials
    token = "fake-cli-surface-token"
    try:
        supplied_tokens = []
        cli_mod.api.login = lambda supplied: supplied_tokens.append(supplied) or True
        cli_mod.check_git_available = lambda: False
        stdin_login = runner.invoke(
            cli_mod.cli, ["login", "--token-stdin"], input=token + "\n"
        )
        check("login token stdin succeeds", stdin_login.exit_code == 0)
        check("login token stdin forwards exact token", supplied_tokens == [token])
        check("login token stdin does not echo token", token not in stdin_login.output)

        supplied_tokens.clear()
        conflicting = runner.invoke(
            cli_mod.cli,
            ["login", "--token", token, "--token-stdin"],
            input="ignored-token\n",
        )
        check("login token modes are mutually exclusive", conflicting.exit_code == 2)
        check("conflicting login makes no API call", supplied_tokens == [])

        empty_stdin = runner.invoke(cli_mod.cli, ["login", "--token-stdin"], input="\n")
        check("empty token stdin is a usage error", empty_stdin.exit_code == 2)
        check("empty token stdin makes no API call", supplied_tokens == [])

        cli_mod.api.login = lambda supplied: False
        failed = runner.invoke(cli_mod.cli, ["login", "--token", token])
        check("login authentication failure exits nonzero", failed.exit_code == 1)
        check("failed login does not print token", token not in failed.output)

        cli_mod.api.login = lambda supplied: supplied == token
        cli_mod.check_git_available = lambda: False
        no_git = runner.invoke(cli_mod.cli, ["login", "--token", token])
        check("login succeeds without Git", no_git.exit_code == 0)
        check("successful login does not print token", token not in no_git.output)
        check("login explains skipped Git integration", "跳过" in no_git.output)

        setup_tokens = []
        cli_mod.check_git_available = lambda: True
        cli_mod.setup_git_credentials = lambda supplied: setup_tokens.append(supplied) or False
        helper_failed = runner.invoke(cli_mod.cli, ["login", "--token", token])
        check("helper setup failure is nonfatal", helper_failed.exit_code == 0)
        check("helper setup failure is reported", "配置失败" in helper_failed.output)
        check("helper receives authenticated token", setup_tokens == [token])
        check("helper failure output omits token", token not in helper_failed.output)

        cli_mod.setup_git_credentials = lambda supplied: supplied == token
        helper_ok = runner.invoke(cli_mod.cli, ["login", "--token", token])
        check(
            "login reports enabled Git integration",
            helper_ok.exit_code == 0 and "Git凭证已配置" in helper_ok.output,
        )
    finally:
        cli_mod.api.login = original_login
        cli_mod.check_git_available = original_git_available
        cli_mod.setup_git_credentials = original_setup

    original_logged_in = cli_mod.config.is_logged_in
    original_user = cli_mod.api.get_login_user
    try:
        user_calls = []
        cli_mod.config.is_logged_in = lambda: False
        cli_mod.api.get_login_user = lambda: user_calls.append(True)
        logged_out = runner.invoke(cli_mod.cli, ["whoami"])
        check("whoami logged-out exits nonzero", logged_out.exit_code == 1)
        check("whoami logged-out avoids API", not user_calls)

        cli_mod.config.is_logged_in = lambda: True
        cli_mod.api.get_login_user = lambda: {"login": "offline-user"}
        known_user = runner.invoke(cli_mod.cli, ["whoami"])
        check(
            "whoami reports current user",
            known_user.exit_code == 0 and "offline-user" in known_user.output,
        )

        cli_mod.api.get_login_user = lambda: None
        unknown_user = runner.invoke(cli_mod.cli, ["whoami"])
        check("whoami API failure exits nonzero", unknown_user.exit_code == 1)
    finally:
        cli_mod.config.is_logged_in = original_logged_in
        cli_mod.api.get_login_user = original_user

    original_logged_in = cli_mod.config.is_logged_in
    original_credentials = cli_mod.config.get_credentials
    original_git_available = cli_mod.check_git_available
    try:
        cli_mod.config.is_logged_in = lambda: False
        logged_out = runner.invoke(cli_mod.cli, ["config-show"])
        check(
            "config-show reports logged-out state",
            logged_out.exit_code == 0 and "当前未登录" in logged_out.output,
        )

        cli_mod.config.is_logged_in = lambda: True
        cli_mod.config.get_credentials = lambda: {"token": token}
        cli_mod.check_git_available = lambda: False
        no_git = runner.invoke(cli_mod.cli, ["config-show"])
        check("config-show reports logged-in state", "登录状态: 已登录" in no_git.output)
        check("config-show never prints token", token not in no_git.output)

        cli_mod.check_git_available = lambda: True

        def configured_helper(command, **kwargs):
            helper = "!/tmp/git-credential-atomgit"
            return subprocess.CompletedProcess(command, 0, stdout=helper, stderr="")

        with patch("subprocess.run", side_effect=configured_helper):
            configured = runner.invoke(cli_mod.cli, ["config-show"])
        check(
            "config-show detects both owned helpers",
            "Git集成: 已启用（2/2 域名）" in configured.output,
        )

        def partial_helper(command, **kwargs):
            if "credential.https://atomgit.com.helper" in command:
                return subprocess.CompletedProcess(
                    command, 0, stdout="!/tmp/git-credential-atomgit\n", stderr=""
                )
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="")

        with patch("subprocess.run", side_effect=partial_helper):
            partial = runner.invoke(cli_mod.cli, ["config-show"])
        check("config-show detects partial helper", "Git集成: 部分启用" in partial.output)
        check(
            "config-show names configured and missing hosts",
            "atomgit.com" in partial.output and "hub.atomgit.com" in partial.output,
        )

        def missing_helper(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="")

        with patch("subprocess.run", side_effect=missing_helper):
            missing = runner.invoke(cli_mod.cli, ["config-show"])
        check("config-show reports missing helper", "Git集成: 未启用" in missing.output)

        with patch("subprocess.run", side_effect=OSError("offline failure")):
            broken = runner.invoke(cli_mod.cli, ["config-show"])
        check("config-show handles Git inspection failure", "Git集成: 检查失败" in broken.output)
    finally:
        cli_mod.config.is_logged_in = original_logged_in
        cli_mod.config.get_credentials = original_credentials
        cli_mod.check_git_available = original_git_available

    original_logged_in = cli_mod.config.is_logged_in
    original_git_available = cli_mod.check_git_available
    try:
        with tempfile.TemporaryDirectory() as home_name, patch(
            "pathlib.Path.home", return_value=Path(home_name)
        ):
            cli_mod.config.is_logged_in = lambda: False
            cli_mod.check_git_available = lambda: True
            logout = runner.invoke(cli_mod.cli, ["logout"])
        check(
            "logout is idempotent when already logged out",
            logout.exit_code == 0 and "当前未登录" in logout.output,
        )
    finally:
        cli_mod.config.is_logged_in = original_logged_in
        cli_mod.check_git_available = original_git_available

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
