#!/usr/bin/env python3
"""Strict offline contract for verified repository visibility updates."""

import contextlib
import io
import json
import sys

import atomgit  # noqa: F401
from click.testing import CliRunner


api_mod = sys.modules["atomgit.api"]
cli_mod = sys.modules["atomgit.cli"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self, size=-1):
        return self.payload[:size] if size >= 0 else self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def main():
    runner = CliRunner()
    repo_help = runner.invoke(cli_mod.cli, ["repo", "--help"])
    check("repo help advertises visibility", "visibility" in repo_help.output)
    has_api = hasattr(api_mod.api, "set_repo_visibility")
    check("visibility API exists", has_api)
    if not has_api:
        passed = sum(1 for _, condition, _ in results if condition)
        print(f"summary: {passed}/{len(results)} passed")
        return 1

    fake_token = "fake-visibility-credential"
    original_open = api_mod._atomgit_open_url
    original_credentials = api_mod.config.get_credentials
    requests = []
    responses = [
        {"private": False},
        {"full_name": "user/repo", "private": False},
    ]

    def recording_open(request, timeout=None):
        requests.append((request, timeout))
        return FakeResponse(json.dumps(responses.pop(0)).encode("utf-8"))

    api_mod.config.get_credentials = lambda: {"token": fake_token}
    api_mod._atomgit_open_url = recording_open
    try:
        check(
            "public visibility update succeeds after verification",
            api_mod.api.set_repo_visibility("user/repo", private=False) is True,
        )
        check("visibility update performs PATCH then GET", [r[0].get_method() for r in requests] == ["PATCH", "GET"])
        check(
            "visibility endpoint quotes normalized repository path",
            all(
                request.full_url
                == "https://api.atomgit.com/api/v5/repos/user/repo"
                for request, _ in requests
            ),
        )
        patch_request = requests[0][0]
        check("visibility PATCH sends exact JSON", json.loads(patch_request.data.decode("utf-8")) == {"private": False})
        check("visibility PATCH declares JSON", patch_request.get_header("Content-type") == "application/json")
        check("visibility credential stays out of URL and body", all(fake_token not in request.full_url for request, _ in requests) and fake_token not in patch_request.data.decode("utf-8"))
        check("visibility requests use finite timeout", all(timeout == 15 for _, timeout in requests))

        requests.clear()
        responses[:] = [{"private": True}, {"visibility": "private"}]
        check(
            "private visibility string verifies successfully",
            api_mod.api.set_repo_visibility("group/sub/repo", private=True) is True,
        )
        check(
            "multi-level ID uses normalized V5 path",
            requests[-1][0].full_url.endswith("/repos/group-sub/repo"),
            requests[-1][0].full_url,
        )

        requests.clear()
        responses[:] = [{"private": False}, {"private": True}]
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            mismatch = api_mod.api.set_repo_visibility("user/repo", private=False)
        check("visibility mismatch fails", mismatch is False)
        check("visibility mismatch is explained", "验证失败" in captured.getvalue())
        check("visibility mismatch output omits token", fake_token not in captured.getvalue())
    finally:
        api_mod._atomgit_open_url = original_open
        api_mod.config.get_credentials = original_credentials

    original_logged_in = cli_mod.config.is_logged_in
    original_set_visibility = cli_mod.api.set_repo_visibility
    calls = []
    cli_mod.api.set_repo_visibility = lambda repo_id, private: calls.append((repo_id, private)) or True
    try:
        cli_mod.config.is_logged_in = lambda: False
        logged_out = runner.invoke(cli_mod.cli, ["repo", "visibility", "user/repo", "public"])
        check("logged-out visibility exits nonzero", logged_out.exit_code == 1)
        check("logged-out visibility avoids API", not calls)

        cli_mod.config.is_logged_in = lambda: True
        invalid = runner.invoke(cli_mod.cli, ["repo", "visibility", "invalid", "public"])
        check("invalid repository ID exits nonzero", invalid.exit_code == 1)
        check("invalid repository ID avoids API", not calls)

        public = runner.invoke(cli_mod.cli, ["repo", "visibility", "user/repo", "public"])
        private = runner.invoke(cli_mod.cli, ["repo", "visibility", "user/repo", "private"])
        check("CLI public visibility succeeds", public.exit_code == 0)
        check("CLI private visibility succeeds", private.exit_code == 0)
        check("CLI maps visibility to private booleans", calls == [("user/repo", False), ("user/repo", True)])

        cli_mod.api.set_repo_visibility = lambda *args, **kwargs: False
        failed = runner.invoke(cli_mod.cli, ["repo", "visibility", "user/repo", "public"])
        check("visibility API failure exits nonzero", failed.exit_code == 1)
    finally:
        cli_mod.config.is_logged_in = original_logged_in
        cli_mod.api.set_repo_visibility = original_set_visibility

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
