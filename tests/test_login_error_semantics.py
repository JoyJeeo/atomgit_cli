#!/usr/bin/env python3
"""Login failures retain safe, actionable categories without token leakage."""

import contextlib
import io
import socket
import sys
import urllib.error

import atomgit  # noqa: F401
from click.testing import CliRunner


api_mod = sys.modules["atomgit.api"]
cli_mod = sys.modules["atomgit.cli"]
results = []
TOKEN = "fake-login-token-never-print"
RAW_SECRET = "raw-network-detail-never-print"


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


class FakeResponse:
    status = 200

    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self, size=-1):
        return self.body if size < 0 else self.body[:size]


def capture(operation):
    output = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        result = operation()
    return result, output.getvalue()


def main():
    original_open = api_mod.urllib.request.urlopen
    original_credentials = api_mod.config.get_credentials
    original_set_credentials = api_mod.config.set_credentials
    original_cli_login = cli_mod.api.login
    try:
        client = api_mod.HuggingFaceAPI()

        requests = []
        saved_credentials = []

        def succeed(request, timeout):
            requests.append(
                (
                    request.full_url,
                    request.get_header("Authorization"),
                    request.get_header("User-agent"),
                    request.get_header("Accept"),
                    timeout,
                )
            )
            return FakeResponse(b'{"login":"offline-user"}')

        api_mod.urllib.request.urlopen = succeed
        api_mod.config.set_credentials = (
            lambda token, username=None: saved_credentials.append((token, username))
        )
        success_result, success_output = capture(lambda: client.login(TOKEN))
        check(
            "successful login preserves request and persistence contract",
            success_result is True
            and requests
            == [
                (
                    "https://atomgit.com/api/v5/user",
                    TOKEN,
                    "atomgit-cli",
                    "application/json",
                    10,
                )
            ]
            and saved_credentials == [(TOKEN, "offline-user")],
            f"requests={len(requests)}, saves={len(saved_credentials)}",
        )

        def fail_401(*args, **kwargs):
            raise urllib.error.HTTPError(
                "https://atomgit.invalid/user", 401, RAW_SECRET, {}, None
            )

        api_mod.urllib.request.urlopen = fail_401
        auth_result, auth_output = capture(lambda: client.login(TOKEN))
        check(
            "401 login is categorized as authentication failure",
            auth_result is False
            and "认证失败" in auth_output
            and "重新登录" in auth_output,
            repr(auth_output),
        )

        def fail_403(*args, **kwargs):
            raise urllib.error.HTTPError(
                "https://atomgit.invalid/user", 403, RAW_SECRET, {}, None
            )

        api_mod.urllib.request.urlopen = fail_403
        permission_result, permission_output = capture(lambda: client.login(TOKEN))
        check(
            "403 login is categorized as permission failure",
            permission_result is False and "权限不足" in permission_output,
            repr(permission_output),
        )

        status_outputs = []
        for status, expected in (
            (429, "请求过于频繁"),
            (503, "服务暂时不可用"),
        ):
            def fail_status(*args, status=status, **kwargs):
                raise urllib.error.HTTPError(
                    "https://atomgit.invalid/user",
                    status,
                    RAW_SECRET,
                    {},
                    None,
                )

            api_mod.urllib.request.urlopen = fail_status
            status_result, status_output = capture(lambda: client.login(TOKEN))
            status_outputs.append(status_output)
            check(
                f"HTTP {status} login failure is actionable",
                status_result is False and expected in status_output,
                repr(status_output),
            )

        def fail_network(*args, **kwargs):
            raise urllib.error.URLError(RAW_SECRET)

        api_mod.urllib.request.urlopen = fail_network
        network_result, network_output = capture(lambda: client.login(TOKEN))
        check(
            "network failure is not reported as an invalid token",
            network_result is False
            and "无法连接" in network_output
            and "Token格式" not in network_output,
            repr(network_output),
        )

        def fail_timeout(*args, **kwargs):
            raise socket.timeout(RAW_SECRET)

        api_mod.urllib.request.urlopen = fail_timeout
        timeout_result, timeout_output = capture(lambda: client.login(TOKEN))
        check(
            "timeout failure retains actionable network guidance",
            timeout_result is False and "检查网络" in timeout_output,
            repr(timeout_output),
        )

        api_mod.urllib.request.urlopen = lambda *args, **kwargs: FakeResponse(
            b"{invalid-json"
        )
        malformed_result, malformed_output = capture(lambda: client.login(TOKEN))
        check(
            "malformed identity response is categorized",
            malformed_result is False and "响应格式无效" in malformed_output,
            repr(malformed_output),
        )

        api_mod.config.get_credentials = lambda: {"token": TOKEN}
        api_mod.urllib.request.urlopen = fail_network
        whoami_result, whoami_output = capture(client.get_login_user)
        check(
            "whoami retains the network failure category",
            whoami_result is None and "无法连接" in whoami_output,
            repr(whoami_output),
        )

        cli_mod.api.login = lambda token: False
        cli_result = CliRunner().invoke(cli_mod.cli, ["login", "--token", TOKEN])
        check(
            "CLI summary does not assume the token is invalid",
            cli_result.exit_code == 1
            and "令牌是否正确" not in cli_result.output
            and "上方提示" in cli_result.output,
            repr(cli_result.output),
        )

        combined_output = "".join(
            (
                auth_output,
                success_output,
                permission_output,
                *status_outputs,
                network_output,
                timeout_output,
                malformed_output,
                whoami_output,
                cli_result.output,
            )
        )
        check(
            "login diagnostics redact credentials and raw exception details",
            TOKEN not in combined_output and RAW_SECRET not in combined_output,
            repr(combined_output),
        )
    finally:
        api_mod.urllib.request.urlopen = original_open
        api_mod.config.get_credentials = original_credentials
        api_mod.config.set_credentials = original_set_credentials
        cli_mod.api.login = original_cli_login

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
