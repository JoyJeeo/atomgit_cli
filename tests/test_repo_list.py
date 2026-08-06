#!/usr/bin/env python3
"""Strict offline contract for authenticated repository listing."""

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
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def read(self, size=-1):
        return self.payload[:size] if size >= 0 else self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def main():
    runner = CliRunner()
    repo_help = runner.invoke(cli_mod.cli, ["repo", "--help"])
    check(
        "repo help advertises list",
        repo_help.exit_code == 0 and "list" in repo_help.output,
    )
    has_api = hasattr(api_mod.api, "list_repos")
    check("repository list API exists", has_api)
    if not has_api:
        passed = sum(1 for _, condition, _ in results if condition)
        print(f"summary: {passed}/{len(results)} passed")
        return 1

    fake_token = "fake-repository-list-credential"
    original_open_url = api_mod._atomgit_open_url
    original_credentials = api_mod.config.get_credentials
    original_logged_in = cli_mod.config.is_logged_in
    original_cli_list = cli_mod.api.list_repos
    requests = []

    def successful_urlopen(request, timeout=None):
        requests.append((request, timeout))
        payload = json.dumps(
            [
                {"full_name": "user/private-repo", "private": True},
                {"owner": {"login": "user"}, "name": "public-repo", "private": False},
                {"path_with_namespace": "org/internal", "visibility": "internal"},
                {"name": "name-only"},
            ]
        ).encode("utf-8")
        return FakeResponse(payload)

    api_mod.config.get_credentials = lambda: {"token": fake_token}
    api_mod._atomgit_open_url = successful_urlopen
    try:
        repositories = api_mod.api.list_repos()
        check("API returns repository dictionaries", len(repositories or []) == 4)
        request, timeout = requests[-1]
        check(
            "API uses documented endpoint",
            request.full_url == "https://api.atomgit.com/api/v5/user/repos",
            request.full_url,
        )
        check("API uses GET", request.get_method() == "GET")
        check("API applies finite timeout", timeout == 15)
        check(
            "API authenticates in a private-token header",
            request.get_header("Private-token") == fake_token,
        )
        check("credential is absent from URL", fake_token not in request.full_url)
        check("API requests JSON", request.get_header("Accept") == "application/json")

        cli_mod.config.is_logged_in = lambda: True
        listed = runner.invoke(cli_mod.cli, ["repo", "list"])
        check("CLI repository list succeeds", listed.exit_code == 0, listed.output)
        check(
            "CLI prints standard and fallback repository IDs",
            all(
                name in listed.output
                for name in (
                    "user/private-repo",
                    "user/public-repo",
                    "org/internal",
                    "name-only",
                )
            ),
        )
        check(
            "CLI prints visibility without token",
            all(value in listed.output for value in ("private", "public", "internal", "unknown"))
            and fake_token not in listed.output,
        )

        api_mod._atomgit_open_url = lambda request, timeout=None: FakeResponse(
            json.dumps({"data": []}).encode("utf-8")
        )
        check("API accepts defensive data wrapper", api_mod.api.list_repos() == [])
        empty = runner.invoke(cli_mod.cli, ["repo", "list"])
        check(
            "CLI explains an empty repository list",
            empty.exit_code == 0 and "没有可显示的仓库" in empty.output,
        )

        api_mod._atomgit_open_url = lambda request, timeout=None: FakeResponse(
            b'{"unexpected": true}'
        )
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            malformed = api_mod.api.list_repos()
        check("API rejects malformed collection JSON", malformed is None)
        check(
            "malformed response is sanitized",
            "响应格式无效" in captured.getvalue() and fake_token not in captured.getvalue(),
            captured.getvalue(),
        )

        def unauthorized(request, timeout=None):
            raise api_mod.urllib.error.HTTPError(
                request.full_url, 401, "Unauthorized", {}, None
            )

        api_mod._atomgit_open_url = unauthorized
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            unauthorized_result = api_mod.api.list_repos()
        check("HTTP authentication failure returns no collection", unauthorized_result is None)
        check(
            "HTTP authentication failure is sanitized",
            "认证失败" in captured.getvalue() and fake_token not in captured.getvalue(),
            captured.getvalue(),
        )

        api_mod._atomgit_open_url = lambda request, timeout=None: (_ for _ in ()).throw(
            api_mod.urllib.error.URLError("offline network failure")
        )
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            network_result = api_mod.api.list_repos()
        check("network failure returns no collection", network_result is None)
        check(
            "network failure is sanitized",
            "无法连接" in captured.getvalue() and fake_token not in captured.getvalue(),
            captured.getvalue(),
        )

        _, redirected_headers = api_mod._prepare_download_redirect(
            "https://api.atomgit.com/api/v5/user/repos",
            "https://objects.example.invalid/repos",
            {"Private-token": fake_token, "Accept": "application/json"},
        )
        check(
            "cross-origin API redirect strips private token",
            all(key.lower() != "private-token" for key in redirected_headers),
        )
    finally:
        api_mod._atomgit_open_url = original_open_url
        api_mod.config.get_credentials = original_credentials

    calls = []
    cli_mod.config.is_logged_in = lambda: False
    cli_mod.api.list_repos = lambda: calls.append(True)
    try:
        logged_out = runner.invoke(cli_mod.cli, ["repo", "list"])
        check("logged-out list exits nonzero", logged_out.exit_code == 1)
        check("logged-out list avoids API access", not calls)

        cli_mod.config.is_logged_in = lambda: True
        cli_mod.api.list_repos = lambda: None
        failed = runner.invoke(cli_mod.cli, ["repo", "list"])
        check("API list failure exits nonzero", failed.exit_code == 1)
    finally:
        cli_mod.config.is_logged_in = original_logged_in
        cli_mod.api.list_repos = original_cli_list

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
