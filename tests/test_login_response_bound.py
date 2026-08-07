#!/usr/bin/env python3
"""Login identity JSON is bounded before decoding and parsing."""

import contextlib
import io
import sys

import atomgit  # noqa: F401


api_mod = sys.modules["atomgit.api"]
results = []
EXPECTED_LIMIT = 1024 * 1024
TOKEN = "fake-bounded-login-token-never-print"


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


class FakeResponse:
    status = 200

    def __init__(self, body):
        self.body = body
        self.read_sizes = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self, size=-1):
        self.read_sizes.append(size)
        return self.body if size < 0 else self.body[:size]


def capture(operation):
    output = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        result = operation()
    return result, output.getvalue()


def main():
    original_open = api_mod.urllib.request.urlopen
    original_loads = api_mod.json.loads
    original_set_credentials = api_mod.config.set_credentials
    try:
        client = api_mod.HuggingFaceAPI()
        configured_limit = getattr(
            api_mod, "_ATOMGIT_IDENTITY_MAX_JSON_BYTES", None
        )
        check(
            "identity response has a fixed one-MiB limit",
            configured_limit == EXPECTED_LIMIT,
            repr(configured_limit),
        )

        success_response = FakeResponse(b'{"login":"offline-user"}')
        saved = []
        api_mod.urllib.request.urlopen = lambda *args, **kwargs: success_response
        api_mod.config.set_credentials = (
            lambda token, username=None: saved.append((token, username))
        )
        success_result, success_output = capture(lambda: client.login(TOKEN))
        check(
            "successful identity lookup requests only limit plus one byte",
            success_result is True
            and success_response.read_sizes == [EXPECTED_LIMIT + 1]
            and saved == [(TOKEN, "offline-user")],
            repr(success_response.read_sizes),
        )

        oversized_response = FakeResponse(b"x" * (EXPECTED_LIMIT + 1))
        parser_calls = []
        api_mod.urllib.request.urlopen = lambda *args, **kwargs: oversized_response

        def forbidden_parse(payload):
            parser_calls.append(payload)
            raise AssertionError("oversized identity data reached JSON parser")

        api_mod.json.loads = forbidden_parse
        oversized_result, oversized_output = capture(lambda: client.login(TOKEN))
        check(
            "oversized identity body is rejected before JSON parsing",
            oversized_result is False
            and oversized_response.read_sizes == [EXPECTED_LIMIT + 1]
            and not parser_calls,
            f"reads={oversized_response.read_sizes}, parses={len(parser_calls)}",
        )
        check(
            "oversized response uses safe existing diagnostics",
            "响应格式无效" in oversized_output
            and TOKEN not in oversized_output
            and "oversized identity data" not in oversized_output,
            repr(oversized_output),
        )
        check(
            "successful login output still omits the token",
            TOKEN not in success_output,
            repr(success_output),
        )
    finally:
        api_mod.urllib.request.urlopen = original_open
        api_mod.json.loads = original_loads
        api_mod.config.set_credentials = original_set_credentials

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
