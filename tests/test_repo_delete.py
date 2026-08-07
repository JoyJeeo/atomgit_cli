#!/usr/bin/env python3
"""Strict offline contract for confirmed and verified repository deletion."""

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
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" +
          (f" -> {detail}" if detail else ""))


class FakeResponse:
    def __init__(self, payload=b""):
        self.payload = payload

    def read(self, size=-1):
        return self.payload[:size] if size >= 0 else self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def not_found(request):
    raise api_mod.urllib.error.HTTPError(
        request.full_url, 404, "Not Found", {}, None
    )


def main():
    runner = CliRunner()
    repo_help = runner.invoke(cli_mod.cli, ["repo", "--help"])
    check(
        "repo help advertises delete",
        repo_help.exit_code == 0 and "delete" in repo_help.output,
        repo_help.output,
    )
    has_api = hasattr(api_mod.api, "delete_repo")
    check("repository delete API exists", has_api)
    if not has_api:
        passed = sum(1 for _, condition, _ in results if condition)
        print(f"summary: {passed}/{len(results)} passed")
        return 1

    def delete_api(repo_id):
        return api_mod.api.delete_repo(repo_id, confirmation=repo_id)

    fake_token = "fake-repository-delete-credential"
    original_open_url = api_mod._atomgit_open_url
    original_credentials = api_mod.config.get_credentials
    requests = []

    def successful_delete(request, timeout=None):
        requests.append((request, timeout))
        methods = [item[0].get_method() for item in requests]
        if methods[-1] == "DELETE":
            return FakeResponse()
        if methods.count("GET") == 1:
            return FakeResponse(
                json.dumps({"full_name": "user/repo"}).encode("utf-8")
            )
        return not_found(request)

    api_mod.config.get_credentials = lambda: {"token": fake_token}
    api_mod._atomgit_open_url = successful_delete
    try:
        check(
            "verified repository deletion succeeds",
            delete_api("user/repo") is True,
        )
        check(
            "delete performs preflight, DELETE, then verification",
            [request.get_method() for request, _ in requests]
            == ["GET", "DELETE", "GET"],
            repr([request.get_method() for request, _ in requests]),
        )
        check(
            "delete uses the official V5 repository endpoint",
            all(
                request.full_url
                == "https://api.atomgit.com/api/v5/repos/user/repo"
                for request, _ in requests
            ),
        )
        delete_request = requests[1][0]
        check("DELETE request has no body", delete_request.data is None)
        check(
            "DELETE request does not declare a JSON body",
            delete_request.get_header("Content-type") is None,
        )
        check(
            "delete credential stays only in the private-token header",
            all(
                request.get_header("Private-token") == fake_token
                and fake_token not in request.full_url
                and (request.data is None or fake_token not in request.data.decode("utf-8"))
                for request, _ in requests
            ),
        )
        check(
            "all repository delete requests use finite timeouts",
            all(timeout == 15 for _, timeout in requests),
        )

        requests.clear()

        def successful_multilevel_delete(request, timeout=None):
            requests.append((request, timeout))
            if request.get_method() == "DELETE":
                return FakeResponse()
            if len(requests) == 1:
                return FakeResponse(
                    json.dumps({"full_name": "group-sub/repo"}).encode("utf-8")
                )
            return not_found(request)

        api_mod._atomgit_open_url = successful_multilevel_delete
        check(
            "multi-level repository deletion succeeds",
            delete_api("group/sub/repo") is True,
        )
        check(
            "multi-level delete uses the shared normalized V5 path",
            all(
                request.full_url.endswith("/repos/group-sub/repo")
                for request, _ in requests
            ),
            repr([request.full_url for request, _ in requests]),
        )

        requests.clear()

        def ambiguous_but_deleted(request, timeout=None):
            requests.append((request, timeout))
            if request.get_method() == "DELETE":
                raise api_mod.urllib.error.URLError("offline response lost")
            if len(requests) == 1:
                return FakeResponse(b'{"full_name":"user/repo"}')
            return not_found(request)

        api_mod._atomgit_open_url = ambiguous_but_deleted
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            recovered = delete_api("user/repo")
        check("ambiguous DELETE is recovered only after GET 404", recovered)
        check("recovered success omits transport details", "offline" not in captured.getvalue())
        check("recovered success omits credential", fake_token not in captured.getvalue())

        requests.clear()

        def still_present(request, timeout=None):
            requests.append((request, timeout))
            if request.get_method() == "DELETE":
                return FakeResponse()
            return FakeResponse(b'{"full_name":"user/repo"}')

        api_mod._atomgit_open_url = still_present
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            present_result = delete_api("user/repo")
        check("DELETE response alone is not reported as success", present_result is False)
        check("still-present state is explained", "仍存在" in captured.getvalue(), captured.getvalue())
        check("still-present output omits credential", fake_token not in captured.getvalue())

        requests.clear()

        def unknown_state(request, timeout=None):
            requests.append((request, timeout))
            if len(requests) == 1:
                return FakeResponse(b'{"full_name":"user/repo"}')
            if request.get_method() == "DELETE":
                return FakeResponse()
            raise api_mod.urllib.error.URLError("offline verification failure")

        api_mod._atomgit_open_url = unknown_state
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            unknown_result = delete_api("user/repo")
        check("unverifiable deletion returns failure", unknown_result is False)
        check("unverifiable deletion reports unknown state", "状态未知" in captured.getvalue(), captured.getvalue())
        check("unknown-state output omits credential and transport detail", fake_token not in captured.getvalue() and "offline" not in captured.getvalue())

        requests.clear()

        def forbidden_delete(request, timeout=None):
            requests.append((request, timeout))
            if len(requests) == 1:
                return FakeResponse(b'{"full_name":"user/repo"}')
            if request.get_method() == "DELETE":
                raise api_mod.urllib.error.HTTPError(
                    request.full_url, 403, "Forbidden", {}, None
                )
            return FakeResponse(b'{"full_name":"user/repo"}')

        api_mod._atomgit_open_url = forbidden_delete
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            forbidden_result = delete_api("user/repo")
        check("permission failure leaves deletion unsuccessful", forbidden_result is False)
        check("permission failure is actionable", "权限不足" in captured.getvalue(), captured.getvalue())
        check("permission output omits credential", fake_token not in captured.getvalue())
        check(
            "deterministic permission failure is not recovered by GET",
            [item[0].get_method() for item in requests] == ["GET", "DELETE"],
            repr([item[0].get_method() for item in requests]),
        )

        requests.clear()
        api_mod._atomgit_open_url = lambda request, timeout=None: (
            requests.append((request, timeout))
            or FakeResponse(b"[]")
        )
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            malformed = delete_api("user/repo")
        check("malformed preflight fails before DELETE", malformed is False)
        check("malformed preflight sends GET only", [item[0].get_method() for item in requests] == ["GET"])
        check("malformed response is sanitized", "响应格式无效" in captured.getvalue(), captured.getvalue())

        requests.clear()

        def missing_preflight(request, timeout=None):
            requests.append((request, timeout))
            return not_found(request)

        api_mod._atomgit_open_url = missing_preflight
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            missing = delete_api("user/repo")
        check("missing repository fails before DELETE", missing is False)
        check("missing preflight sends GET only", [item[0].get_method() for item in requests] == ["GET"])
        check("missing repository output is sanitized", "不存在" in captured.getvalue(), captured.getvalue())

        api_mod.config.get_credentials = lambda: None
        requests.clear()
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            logged_out_api = delete_api("user/repo")
        check("API without credentials refuses deletion", logged_out_api is False)
        check("API without credentials sends no request", not requests)

        api_mod.config.get_credentials = lambda: {"token": fake_token}
        requests.clear()
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            mismatched_api = api_mod.api.delete_repo(
                "user/repo", confirmation="user/other"
            )
        check("API mismatched confirmation refuses deletion", mismatched_api is False)
        check("API mismatched confirmation sends no request", not requests)
        check("API mismatch output omits credential", fake_token not in captured.getvalue())
    finally:
        api_mod._atomgit_open_url = original_open_url
        api_mod.config.get_credentials = original_credentials

    original_logged_in = cli_mod.config.is_logged_in
    original_cli_delete = cli_mod.api.delete_repo
    cli_calls = []
    cli_mod.api.delete_repo = lambda repo_id, confirmation: (
        cli_calls.append((repo_id, confirmation)) or True
    )
    try:
        cli_mod.config.is_logged_in = lambda: False
        logged_out = runner.invoke(
            cli_mod.cli,
            ["repo", "delete", "user/repo", "--confirm", "user/repo"],
        )
        check("logged-out CLI delete exits nonzero", logged_out.exit_code == 1)
        check("logged-out CLI delete avoids API", not cli_calls)

        cli_mod.config.is_logged_in = lambda: True
        missing_confirmation = runner.invoke(
            cli_mod.cli, ["repo", "delete", "user/repo"]
        )
        check("missing confirmation is a usage error", missing_confirmation.exit_code == 2)
        check("missing confirmation avoids API", not cli_calls)

        invalid = runner.invoke(
            cli_mod.cli,
            ["repo", "delete", "invalid", "--confirm", "invalid"],
        )
        check("invalid repository ID exits nonzero", invalid.exit_code == 1)
        check("invalid repository ID avoids API", not cli_calls)

        mismatch = runner.invoke(
            cli_mod.cli,
            ["repo", "delete", "user/repo", "--confirm", "user/other"],
        )
        check("mismatched confirmation is a usage error", mismatch.exit_code == 2)
        check("mismatched confirmation avoids API", not cli_calls)

        deleted = runner.invoke(
            cli_mod.cli,
            ["repo", "delete", "user/repo", "--confirm", "user/repo"],
        )
        check("confirmed CLI deletion succeeds", deleted.exit_code == 0, deleted.output)
        check(
            "confirmed CLI deletion forwards target and confirmation",
            cli_calls == [("user/repo", "user/repo")],
            repr(cli_calls),
        )

        multilevel = runner.invoke(
            cli_mod.cli,
            [
                "repo", "delete", "group/sub/repo",
                "--confirm", "group/sub/repo",
            ],
        )
        check("multi-level literal confirmation succeeds", multilevel.exit_code == 0)
        check(
            "multi-level ID and confirmation reach API unchanged",
            cli_calls[-1]
            == ("group/sub/repo", "group/sub/repo"),
        )

        cli_mod.api.delete_repo = lambda *args, **kwargs: False
        failed = runner.invoke(
            cli_mod.cli,
            ["repo", "delete", "user/repo", "--confirm", "user/repo"],
        )
        check("API deletion failure exits nonzero", failed.exit_code == 1)
    finally:
        cli_mod.config.is_logged_in = original_logged_in
        cli_mod.api.delete_repo = original_cli_delete

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
