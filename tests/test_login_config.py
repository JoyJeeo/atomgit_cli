#!/usr/bin/env python3
"""Offline login and configuration lifecycle coverage."""

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import atomgit  # noqa: F401
from click.testing import CliRunner


api_mod = sys.modules["atomgit.api"]
cli_mod = sys.modules["atomgit.cli"]
config_mod = sys.modules["atomgit.config"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    with tempfile.TemporaryDirectory() as home_dir:
        home = Path(home_dir)
        with patch("pathlib.Path.home", return_value=home):
            config = config_mod.Config()
            check("fresh config is logged out", not config.is_logged_in())
            config.set_credentials("fake-persisted-token")
            reloaded = config_mod.Config()
            check(
                "saved token reloads",
                reloaded.get_credentials() == {"token": "fake-persisted-token"},
            )
            reloaded.clear_credentials()
            check("logout state persists", not config_mod.Config().is_logged_in())

            config_file = home / ".atomgit" / "config.json"
            config_file.write_text("{broken-json", encoding="utf-8")
            corrupt = config_mod.Config()
            check("corrupt config loads logged out", not corrupt.is_logged_in())
            corrupt.set_credentials("fake-repaired-token")
            repaired = json.loads(config_file.read_text(encoding="utf-8"))
            check("later save repairs corrupt JSON", repaired["token"] == "fake-repaired-token")

    api = api_mod.HuggingFaceAPI()
    original_set = api_mod.config.set_credentials
    saved_tokens = []
    api_mod.config.set_credentials = saved_tokens.append
    try:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            short_result = api.login("short")
        check("short token rejected", short_result is False and not saved_tokens)

        api._get_login_user_by_token = lambda token: None
        with contextlib.redirect_stdout(output):
            identity_result = api.login("fake-token-long-enough")
        check("identity failure is not persisted", identity_result is False and not saved_tokens)

        api._get_login_user_by_token = lambda token: {"login": "offline-user"}
        with contextlib.redirect_stdout(output):
            valid_result = api.login("fake-token-long-enough")
        check(
            "verified token is persisted once",
            valid_result is True and saved_tokens == ["fake-token-long-enough"],
        )
        check("token is absent from login output", "fake-token-long-enough" not in output.getvalue())
    finally:
        api_mod.config.set_credentials = original_set

    original_logged_in = cli_mod.config.is_logged_in
    original_clear = cli_mod.config.clear_credentials
    original_git = cli_mod.check_git_available
    cleared = []
    cli_mod.config.is_logged_in = lambda: True
    cli_mod.config.clear_credentials = lambda: cleared.append(True)
    cli_mod.check_git_available = lambda: False
    try:
        result = CliRunner().invoke(cli_mod.cli, ["logout"])
        check("CLI logout succeeds without Git", result.exit_code == 0)
        check("CLI logout clears credentials", cleared == [True])
    finally:
        cli_mod.config.is_logged_in = original_logged_in
        cli_mod.config.clear_credentials = original_clear
        cli_mod.check_git_available = original_git

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
