#!/usr/bin/env python3
"""Lock timeout and progress restoration across CLI, SDK, and subprocesses."""

import subprocess
import sys
import tempfile
from pathlib import Path

from click.testing import CliRunner
from huggingface_hub import constants as hf_constants
from huggingface_hub.utils import (
    are_progress_bars_disabled,
    disable_progress_bars,
    enable_progress_bars,
)

import atomgit  # noqa: F401
import atomgit_hub


api_module = sys.modules["atomgit.api"]
cli_module = sys.modules["atomgit.cli"]
config_module = sys.modules["atomgit.config"]
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def main():
    original_cli_upload = api_module.hf_upload_file
    original_sdk_upload = atomgit_hub.hf_upload_folder
    original_logged_in = config_module.config.is_logged_in
    original_credentials = config_module.config.get_credentials
    suite_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT
    suite_progress = are_progress_bars_disabled()
    try:
        config_module.config.is_logged_in = lambda: True
        config_module.config.get_credentials = lambda: {"token": "offline-token"}
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "payload.bin"
            source_file.write_bytes(b"payload")
            source_folder = Path(temp_dir) / "folder"
            source_folder.mkdir()
            (source_folder / "payload.bin").write_bytes(b"payload")
            runner = CliRunner()

            hf_constants.DEFAULT_REQUEST_TIMEOUT = 31
            enable_progress_bars()
            observed = []

            def successful_cli_upload(**kwargs):
                observed.append(
                    (hf_constants.DEFAULT_REQUEST_TIMEOUT, are_progress_bars_disabled())
                )
                return "commit"

            api_module.hf_upload_file = successful_cli_upload
            success = runner.invoke(
                cli_module.cli,
                [
                    "upload",
                    str(source_file),
                    "--repo-id",
                    "user/repo",
                    "--timeout",
                    "7",
                    "--no-progress-bar",
                ],
                prog_name="atomgit",
            )
            check(
                "CLI success applies requested global state only during the call",
                success.exit_code == 0 and observed == [(7.0, True)],
                repr((success.exit_code, observed, success.output[-200:])),
            )
            check(
                "CLI success restores timeout and progress state",
                hf_constants.DEFAULT_REQUEST_TIMEOUT == 31
                and are_progress_bars_disabled() is False,
            )

            disable_progress_bars()
            observed.clear()

            def failing_cli_upload(**kwargs):
                observed.append(
                    (hf_constants.DEFAULT_REQUEST_TIMEOUT, are_progress_bars_disabled())
                )
                raise RuntimeError("offline failure")

            api_module.hf_upload_file = failing_cli_upload
            failure = runner.invoke(
                cli_module.cli,
                [
                    "upload",
                    str(source_file),
                    "--repo-id",
                    "user/repo",
                    "--timeout",
                    "11",
                ],
                prog_name="atomgit",
            )
            check(
                "CLI handled failure applies the requested temporary state",
                failure.exit_code == 1 and observed == [(11.0, False)],
                repr((failure.exit_code, observed, failure.output[-200:])),
            )
            check(
                "CLI handled failure restores the caller's disabled progress state",
                hf_constants.DEFAULT_REQUEST_TIMEOUT == 31
                and are_progress_bars_disabled() is True,
            )

            sdk_observed = []

            def successful_sdk_upload(**kwargs):
                sdk_observed.append(hf_constants.DEFAULT_REQUEST_TIMEOUT)
                return "sdk-commit"

            atomgit_hub.hf_upload_folder = successful_sdk_upload
            sdk_result = atomgit_hub.upload_folder(
                source_folder,
                "user/repo",
                token="offline-token",
                upload_timeout=13,
            )
            check(
                "SDK success restores timeout without changing progress state",
                sdk_result == "sdk-commit"
                and sdk_observed == [13]
                and hf_constants.DEFAULT_REQUEST_TIMEOUT == 31
                and are_progress_bars_disabled() is True,
                repr(sdk_observed),
            )

            def failing_sdk_upload(**kwargs):
                sdk_observed.append(hf_constants.DEFAULT_REQUEST_TIMEOUT)
                raise RuntimeError("offline SDK failure")

            atomgit_hub.hf_upload_folder = failing_sdk_upload
            try:
                atomgit_hub.upload_folder(
                    source_folder,
                    "user/repo",
                    token="offline-token",
                    upload_timeout=17,
                )
            except atomgit_hub.AtomGitError as error:
                sdk_failure = error.__cause__ is not None
            else:
                sdk_failure = False
            check(
                "SDK propagated failure restores timeout and preserves its cause",
                sdk_failure
                and sdk_observed[-1] == 17
                and hf_constants.DEFAULT_REQUEST_TIMEOUT == 31
                and are_progress_bars_disabled() is True,
            )

            parent_state = (
                hf_constants.DEFAULT_REQUEST_TIMEOUT,
                are_progress_bars_disabled(),
            )
            child = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from huggingface_hub import constants; "
                        "from huggingface_hub.utils import disable_progress_bars; "
                        "constants.DEFAULT_REQUEST_TIMEOUT=99; disable_progress_bars(); "
                        "print(constants.DEFAULT_REQUEST_TIMEOUT)"
                    ),
                ],
                cwd=str(REPOSITORY_ROOT),
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            check(
                "child-process global mutations do not leak into the parent",
                child.returncode == 0
                and child.stdout.strip() == "99"
                and parent_state
                == (
                    hf_constants.DEFAULT_REQUEST_TIMEOUT,
                    are_progress_bars_disabled(),
                ),
                child.stderr.strip(),
            )
    finally:
        api_module.hf_upload_file = original_cli_upload
        atomgit_hub.hf_upload_folder = original_sdk_upload
        config_module.config.is_logged_in = original_logged_in
        config_module.config.get_credentials = original_credentials
        hf_constants.DEFAULT_REQUEST_TIMEOUT = suite_timeout
        if suite_progress:
            disable_progress_bars()
        else:
            enable_progress_bars()

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
