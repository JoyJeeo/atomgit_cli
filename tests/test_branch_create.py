#!/usr/bin/env python3
"""Offline V5 contract for explicit branch creation."""
import contextlib
import io
import json
import sys
import urllib.error
import atomgit  # noqa: F401
from click.testing import CliRunner

api_mod = sys.modules["atomgit.api"]
cli_mod = sys.modules["atomgit.cli"]
results = []

def check(name, condition):
    results.append((name, condition))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")

class Response:
    def __init__(self, payload): self.payload = payload
    def read(self, size=-1): return self.payload[:size]
    def __enter__(self): return self
    def __exit__(self, *args): return False

def main():
    original_open = api_mod._atomgit_open_url
    original_credentials = api_mod.config.get_credentials
    requests = []
    payloads = [{"name": "feature/x"}, {"name": "feature/x"}]
    def open_url(request, timeout=None):
        requests.append(request)
        return Response(json.dumps(payloads.pop(0)).encode())
    api_mod._atomgit_open_url = open_url
    api_mod.config.get_credentials = lambda: {"token": "fake-branch-token"}
    try:
        check("API creates and verifies branch", api_mod.api.create_branch("user/repo", "feature/x", "main"))
        check("API uses POST then GET", [r.get_method() for r in requests] == ["POST", "GET"])
        check("API sends exact branch JSON", json.loads(requests[0].data) == {"branch_name": "feature/x", "refs": "main"})
        check("branch verification path is encoded", requests[1].full_url.endswith("/branches/feature%2Fx"))
        check("unsafe branch is rejected", not api_mod.api.create_branch("user/repo", "bad..ref"))

        requests.clear()

        def ambiguous_success(request, timeout=None):
            requests.append(request)
            if request.get_method() == "POST":
                raise urllib.error.URLError("offline after write")
            return Response(json.dumps({"name": "feature/x"}).encode())

        api_mod._atomgit_open_url = ambiguous_success
        check(
            "ambiguous branch write recovers from matching GET",
            api_mod.api.create_branch("user/repo", "feature/x", "main"),
        )
        check(
            "ambiguous branch recovery performs POST then GET",
            [request.get_method() for request in requests] == ["POST", "GET"],
        )

        requests.clear()

        def ambiguous_mismatch(request, timeout=None):
            requests.append(request)
            if request.get_method() == "POST":
                raise urllib.error.URLError("offline after write")
            return Response(json.dumps({"name": "different"}).encode())

        api_mod._atomgit_open_url = ambiguous_mismatch
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            mismatched_write = api_mod.api.create_branch(
                "user/repo", "feature/x", "main"
            )
        check("ambiguous mismatched branch fails", mismatched_write is False)
        check(
            "ambiguous branch mismatch reports unknown write status",
            "状态未知" in captured.getvalue()
            and "fake-branch-token" not in captured.getvalue(),
        )

        requests.clear()

        def ambiguous_unknown(request, timeout=None):
            requests.append(request)
            raise urllib.error.URLError("offline transport detail")

        api_mod._atomgit_open_url = ambiguous_unknown
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            unknown = api_mod.api.create_branch(
                "user/repo", "feature/x", "main"
            )
        check("unverifiable branch write fails", unknown is False)
        check(
            "unverifiable branch reports sanitized unknown state",
            "状态未知" in captured.getvalue()
            and "offline" not in captured.getvalue()
            and "fake-branch-token" not in captured.getvalue(),
        )

        requests.clear()

        def forbidden_write(request, timeout=None):
            requests.append(request)
            raise urllib.error.HTTPError(
                request.full_url, 403, "Forbidden", {}, None
            )

        api_mod._atomgit_open_url = forbidden_write
        check(
            "branch 4xx remains failure",
            not api_mod.api.create_branch("user/repo", "feature/x", "main"),
        )
        check("branch 4xx skips recovery GET", len(requests) == 1)
    finally:
        api_mod._atomgit_open_url = original_open
        api_mod.config.get_credentials = original_credentials

    runner = CliRunner()
    original_login = cli_mod.config.is_logged_in
    original_create = cli_mod.api.create_branch
    calls = []
    cli_mod.config.is_logged_in = lambda: True
    cli_mod.api.create_branch = lambda repo_id, branch, source="main": calls.append((repo_id, branch, source)) or True
    try:
        result = runner.invoke(cli_mod.cli, ["repo", "branch", "create", "user/repo", "dev", "--from", "main"])
        check("CLI branch create succeeds", result.exit_code == 0)
        check("CLI forwards branch source", calls == [("user/repo", "dev", "main")])
        invalid = runner.invoke(cli_mod.cli, ["repo", "branch", "create", "user/repo", "bad..ref"])
        check("CLI rejects malformed branch", invalid.exit_code == 2 and len(calls) == 1)
    finally:
        cli_mod.config.is_logged_in = original_login
        cli_mod.api.create_branch = original_create
    passed = sum(ok for _, ok in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1

if __name__ == "__main__": raise SystemExit(main())
