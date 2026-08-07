#!/usr/bin/env python3
"""Reject upload symlinks before credentials or transfer code can run."""

import contextlib
import io
import sys
import tempfile
from pathlib import Path

import atomgit  # noqa: F401
from click.testing import CliRunner
from huggingface_hub import HfApi


api_mod = sys.modules["atomgit.api"]
cli_mod = sys.modules["atomgit.cli"]
sdk_mod = sys.modules["atomgit.atomgit_hub"]
utils_mod = sys.modules["atomgit.utils"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    original_credentials = api_mod.config.get_credentials
    original_logged_in = cli_mod.config.is_logged_in
    original_file_upload = api_mod.hf_upload_file
    original_folder_upload = api_mod.upload_folder
    original_get_context = api_mod.multiprocessing.get_context
    original_sdk_upload = sdk_mod.hf_upload_folder
    original_sdk_token = sdk_mod._get_token
    original_walk = utils_mod.os.walk

    credential_calls = []
    transfer_calls = []
    sdk_token_calls = []
    login_state_calls = []

    def credentials():
        credential_calls.append(True)
        return {"token": "fake-symlink-safety-token"}

    def transfer(**kwargs):
        transfer_calls.append(kwargs)
        return "offline-result"

    def get_context(method):
        transfer_calls.append({"multiprocessing": method})
        raise AssertionError("resumable worker must not be created")

    api_mod.config.get_credentials = credentials
    cli_mod.config.is_logged_in = lambda: login_state_calls.append(True) or True
    api_mod.hf_upload_file = transfer
    api_mod.upload_folder = transfer
    api_mod.multiprocessing.get_context = get_context
    sdk_mod.hf_upload_folder = transfer
    sdk_mod._get_token = lambda: sdk_token_calls.append(True) or "fake-token"

    try:
        with tempfile.TemporaryDirectory(prefix="atomgit-upload-symlink-") as temp:
            sandbox = Path(temp)
            outside_file = sandbox / "outside.txt"
            outside_file.write_text("outside-sentinel", encoding="utf-8")
            outside_directory = sandbox / "outside-directory"
            outside_directory.mkdir()
            (outside_directory / "secret.txt").write_text(
                "directory-sentinel", encoding="utf-8"
            )

            regular_directory = sandbox / "regular"
            regular_directory.mkdir()
            (regular_directory / "regular.txt").write_text(
                "regular", encoding="utf-8"
            )

            root_file_link = sandbox / "root-file-link.txt"
            root_directory_link = sandbox / "root-directory-link"
            nested_file_directory = sandbox / "nested-file"
            nested_directory_directory = sandbox / "nested-directory"
            broken_directory = sandbox / "broken"
            for directory in (
                nested_file_directory,
                nested_directory_directory,
                broken_directory,
            ):
                directory.mkdir()

            try:
                root_file_link.symlink_to(outside_file)
                root_directory_link.symlink_to(
                    outside_directory, target_is_directory=True
                )
                (nested_file_directory / "linked.txt").symlink_to(outside_file)
                (nested_directory_directory / "linked-dir").symlink_to(
                    outside_directory, target_is_directory=True
                )
                (broken_directory / "broken.txt").symlink_to(
                    sandbox / "missing-target"
                )
            except (OSError, NotImplementedError) as error:
                check("symlink fixtures unavailable", True, type(error).__name__)
                passed = sum(1 for _, condition, _ in results if condition)
                print(f"summary: {passed}/{len(results)} passed")
                return 0

            dependency_operations = HfApi(token=False)._prepare_upload_folder_additions(
                nested_file_directory, path_in_repo="."
            )
            selected_source = Path(dependency_operations[0].path_or_fileobj)
            check(
                "locked HF dependency selects an escaping file symlink",
                len(dependency_operations) == 1
                and selected_source.is_symlink()
                and selected_source.resolve() == outside_file.resolve(),
            )
            check(
                "locked HF dependency would read outside content",
                selected_source.read_text(encoding="utf-8") == "outside-sentinel",
            )

            cases = (
                (
                    "single-file root symlink",
                    lambda: api_mod.api.upload_folder(
                        root_file_link, "user/repo"
                    ),
                ),
                (
                    "directory root symlink",
                    lambda: api_mod.api.upload_directory(
                        root_directory_link, "user/repo"
                    ),
                ),
                (
                    "nested file symlink",
                    lambda: api_mod.api.upload_directory(
                        nested_file_directory, "user/repo"
                    ),
                ),
                (
                    "nested directory symlink",
                    lambda: api_mod.api.upload_directory(
                        nested_directory_directory, "user/repo"
                    ),
                ),
                (
                    "nested broken symlink",
                    lambda: api_mod.api.upload_directory(
                        broken_directory, "user/repo"
                    ),
                ),
                (
                    "resumable nested symlink",
                    lambda: api_mod.api.upload_directory(
                        nested_file_directory, "user/repo", resumable=True
                    ),
                ),
                (
                    "ignored nested symlink",
                    lambda: api_mod.api.upload_directory(
                        nested_file_directory,
                        "user/repo",
                        ignore_patterns=["linked.txt"],
                    ),
                ),
            )
            for name, operation in cases:
                credential_calls.clear()
                transfer_calls.clear()
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    result = operation()
                check(f"{name} is rejected", result is False, output.getvalue())
                check(
                    f"{name} explains symlink policy",
                    "符号链接" in output.getvalue(),
                    output.getvalue(),
                )
                check(
                    f"{name} stops before credentials and transfer",
                    not credential_calls and not transfer_calls,
                )

            sdk_token_calls.clear()
            transfer_calls.clear()
            try:
                sdk_mod.upload_folder(nested_file_directory, "user/repo")
                sdk_error = None
            except Exception as error:
                sdk_error = error
            check("SDK rejects nested symlink with ValueError", isinstance(sdk_error, ValueError))
            check(
                "SDK symlink error is actionable and credential-safe",
                "符号链接" in str(sdk_error)
                and "fake-symlink-safety-token" not in str(sdk_error),
                str(sdk_error),
            )
            check(
                "SDK rejects before token and transfer access",
                not sdk_token_calls and not transfer_calls,
            )

            credential_calls.clear()
            transfer_calls.clear()
            login_state_calls.clear()
            cli_result = CliRunner().invoke(
                cli_mod.cli,
                [
                    "upload",
                    str(nested_file_directory),
                    "--repo-id",
                    "user/repo",
                ],
            )
            check("CLI symlink upload exits nonzero", cli_result.exit_code == 1)
            check("CLI symlink output is actionable", "符号链接" in cli_result.output)
            check(
                "CLI rejection avoids login state, credentials, and transfer",
                not login_state_calls
                and not credential_calls
                and not transfer_calls,
            )

            credential_calls.clear()
            transfer_calls.clear()

            def failed_walk(*args, **kwargs):
                kwargs["onerror"](PermissionError("offline traversal failure"))
                return ()

            utils_mod.os.walk = failed_walk
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                traversal_result = api_mod.api.upload_directory(
                    regular_directory, "user/repo"
                )
            check("upload traversal error fails closed", traversal_result is False)
            check(
                "traversal failure avoids credentials and transfer",
                not credential_calls and not transfer_calls,
            )
            check(
                "traversal failure has safe guidance",
                "安全检查" in output.getvalue()
                and "fake-symlink-safety-token" not in output.getvalue(),
                output.getvalue(),
            )
            utils_mod.os.walk = original_walk

            credential_calls.clear()
            transfer_calls.clear()
            regular = api_mod.api.upload_directory(
                regular_directory, "user/repo"
            )
            check("regular directory remains accepted", regular is True)
            check(
                "regular directory reaches credentials and one transfer",
                len(credential_calls) == 1 and len(transfer_calls) == 1,
            )
    finally:
        api_mod.config.get_credentials = original_credentials
        cli_mod.config.is_logged_in = original_logged_in
        api_mod.hf_upload_file = original_file_upload
        api_mod.upload_folder = original_folder_upload
        api_mod.multiprocessing.get_context = original_get_context
        sdk_mod.hf_upload_folder = original_sdk_upload
        sdk_mod._get_token = original_sdk_token
        utils_mod.os.walk = original_walk

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
