#!/usr/bin/env python3
"""Strict offline download contracts across CLI, API, and SDK."""

import contextlib
import inspect
import io
import sys
import tempfile
import warnings
from pathlib import Path

import atomgit  # noqa: F401
import atomgit_hub
from click.testing import CliRunner
from huggingface_hub import hf_hub_download as real_file_download
from huggingface_hub import snapshot_download as real_snapshot_download


api_mod = sys.modules["atomgit.api"]
cli_mod = sys.modules["atomgit.cli"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    original_sdk_snapshot = atomgit_hub.hf_snapshot_download
    original_sdk_file = atomgit_hub.hf_hub_download
    original_get_token = atomgit_hub._get_token
    sdk_snapshot_calls = []
    sdk_file_calls = []

    def strict_snapshot(**kwargs):
        inspect.signature(real_snapshot_download).bind(**kwargs)
        sdk_snapshot_calls.append(kwargs)
        return "/tmp/sdk-snapshot"

    def strict_file(**kwargs):
        inspect.signature(real_file_download).bind(**kwargs)
        sdk_file_calls.append(kwargs)
        return "/tmp/README.md"

    atomgit_hub.hf_snapshot_download = strict_snapshot
    atomgit_hub.hf_hub_download = strict_file
    atomgit_hub._get_token = lambda: "fake-stored-token"
    try:
        result = atomgit_hub.snapshot_download(
            "user/repo",
            revision="main",
            local_dir="/tmp/sdk-local",
            force_download=True,
            allow_patterns=["*.json"],
        )
        check("SDK snapshot result preserved", result == "/tmp/sdk-snapshot")
        call = sdk_snapshot_calls[-1]
        check("SDK snapshot uses stored token", call.get("token") == "fake-stored-token")
        check("SDK snapshot forwards revision", call.get("revision") == "main")
        check("SDK snapshot forwards local directory", call.get("local_dir") == "/tmp/sdk-local")
        check("SDK snapshot forwards force", call.get("force_download") is True)
        check("SDK snapshot forwards patterns", call.get("allow_patterns") == ["*.json"])

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            atomgit_hub.snapshot_download(
                "user/repo",
                token=False,
                local_dir_use_symlinks=False,
                proxies={"https": "http://proxy.invalid"},
                resume_download=True,
            )
        legacy_call = sdk_snapshot_calls[-1]
        check("explicit anonymous token preserved", legacy_call.get("token") is False)
        check(
            "removed legacy options omitted",
            all(
                name not in legacy_call
                for name in ("local_dir_use_symlinks", "proxies", "resume_download")
            ),
        )
        check("non-default legacy options warn", len(caught) == 1 and "ignores" in str(caught[0].message))

        result = atomgit_hub.download_file(
            "user/repo",
            "README.md",
            local_dir="/tmp/sdk-file",
            revision="main",
            token="fake-explicit-token",
            force_download=True,
        )
        check("SDK file result preserved", result == "/tmp/README.md")
        file_call = sdk_file_calls[-1]
        check("SDK file explicit token forwarded", file_call.get("token") == "fake-explicit-token")
        check("SDK file force forwarded", file_call.get("force_download") is True)
    finally:
        atomgit_hub.hf_snapshot_download = original_sdk_snapshot
        atomgit_hub.hf_hub_download = original_sdk_file
        atomgit_hub._get_token = original_get_token

    original_api_snapshot = api_mod.snapshot_download
    original_credentials = api_mod.config.get_credentials
    api_calls = []

    def strict_api_snapshot(**kwargs):
        inspect.signature(real_snapshot_download).bind(**kwargs)
        api_calls.append(kwargs)
        return "/tmp/api-snapshot"

    api_mod.snapshot_download = strict_api_snapshot
    try:
        with tempfile.TemporaryDirectory() as local_dir:
            api_mod.config.get_credentials = lambda: None
            check(
                "API anonymous download succeeds",
                api_mod.api.download_repo("user/repo", Path(local_dir)) is True,
            )
            check("API anonymous call uses no token", api_calls[-1].get("token") is None)

            api_mod.config.get_credentials = lambda: {"token": "fake-stored-token"}
            check(
                "API authenticated download succeeds",
                api_mod.api.download_repo(
                    "user/repo", Path(local_dir), force_download=True
                )
                is True,
            )
            check("API stored token forwarded", api_calls[-1].get("token") == "fake-stored-token")
            check("API force forwarded", api_calls[-1].get("force_download") is True)

            def empty_repo_download(**kwargs):
                inspect.signature(real_snapshot_download).bind(**kwargs)
                raise ValueError("min() iterable argument is empty")

            api_mod.snapshot_download = empty_repo_download
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                empty_ok = api_mod.api.download_repo("user/repo", Path(local_dir)) is True
            empty_output = captured.getvalue()
            check("API empty repo is not a download failure", empty_ok)
            check(
                "API empty repo gives a clear message",
                "仓库为空" in empty_output,
                f"output={empty_output!r}",
            )

            def other_value_error(**kwargs):
                inspect.signature(real_snapshot_download).bind(**kwargs)
                raise ValueError("unrelated value error")

            api_mod.snapshot_download = other_value_error
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                other_failed = api_mod.api.download_repo("user/repo", Path(local_dir)) is False
            other_output = captured.getvalue()
            check("API unrelated ValueError still fails", other_failed)
            check(
                "API unrelated ValueError is reported",
                "unrelated value error" in other_output and "下载" in other_output,
                f"output={other_output!r}",
            )
            api_mod.snapshot_download = strict_api_snapshot
    finally:
        api_mod.snapshot_download = original_api_snapshot
        api_mod.config.get_credentials = original_credentials

    original_cli_download = cli_mod.api.download_repo
    original_logged_in = cli_mod.config.is_logged_in
    cli_calls = []
    cli_mod.config.is_logged_in = lambda: False
    cli_mod.api.download_repo = lambda repo_id, local_path, force_download=False: (
        cli_calls.append((repo_id, Path(local_path), force_download)) or True
    )
    try:
        runner = CliRunner()
        with runner.isolated_filesystem():
            default_result = runner.invoke(cli_mod.cli, ["download", "user/repo"])
            check("CLI default download succeeds", default_result.exit_code == 0)
            check("CLI default directory uses repo name", cli_calls[-1][1].name == "repo")
            explicit_result = runner.invoke(
                cli_mod.cli,
                ["download", "user/repo", "--directory", "target", "--force"],
            )
            check("CLI explicit force succeeds", explicit_result.exit_code == 0)
            check("CLI explicit directory forwarded", cli_calls[-1][1].name == "target")
            check("CLI force forwarded", cli_calls[-1][2] is True)

            cli_mod.api.download_repo = lambda *args, **kwargs: False
            failed = runner.invoke(cli_mod.cli, ["download", "user/repo", "-d", "failed"])
            check("CLI failed download exits nonzero", failed.exit_code == 1)
            check("CLI anonymous failure gives login guidance", "login" in failed.output)
    finally:
        cli_mod.api.download_repo = original_cli_download
        cli_mod.config.is_logged_in = original_logged_in

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
