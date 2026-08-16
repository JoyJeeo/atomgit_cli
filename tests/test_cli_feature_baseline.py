#!/usr/bin/env python3
"""Executable baseline for every public AtomGit CLI command and option."""

import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import click
import atomgit  # noqa: F401
from click.testing import CliRunner

from cli_baseline_contract import (
    BASELINE_LEAF_COMMAND_COUNT,
    BASELINE_PUBLIC_COMMAND_COUNT,
    BASELINE_PUBLIC_PARAMETER_COUNT,
    BASELINE_TEST_SCRIPT_COUNT,
    BASELINE_TEST_GROUPS,
    EXPECTED_PUBLIC_SCHEMA,
    LEAF_DISPATCH_PATHS,
    discover_public_schema,
    validate_leaf_dispatches,
    validate_public_schema,
    validate_test_entrypoints,
    validate_test_registry,
)


cli_mod = sys.modules["atomgit.cli"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def command_at(path):
    command = cli_mod.cli
    for name in path:
        if not isinstance(command, click.Group) or name not in command.commands:
            return None
        command = command.commands[name]
    return command


def main():
    results.clear()
    runner = CliRunner()

    actual_schema = discover_public_schema(cli_mod.cli)
    schema_errors = validate_public_schema(actual_schema)
    check(
        "public CLI schema exactly matches the registered baseline",
        not schema_errors,
        repr(schema_errors),
    )

    for path, expected_spec in EXPECTED_PUBLIC_SCHEMA.items():
        command = command_at(path)
        label = " ".join(path) if path else "<root>"
        actual_spec = actual_schema.get(path)
        check(
            f"exact command schema remains stable: {label}",
            actual_spec == expected_spec,
            f"expected={expected_spec!r}, actual={actual_spec!r}",
        )
        if command is None:
            continue
        help_args = [*path, "--help"] if path else ["--help"]
        help_result = runner.invoke(cli_mod.cli, help_args)
        check(
            f"help remains usable: {label}",
            help_result.exit_code == 0 and "--help" in help_result.output,
            f"exit={help_result.exit_code}",
        )

    tests_directory = Path(__file__).resolve().parent
    discovered_tests = {
        path.name for path in tests_directory.glob("test_*.py")
    }
    registry_errors = validate_test_registry(discovered_tests)
    check(
        "every offline regression script is registered exactly once",
        not registry_errors,
        repr(registry_errors),
    )

    entrypoint_errors = validate_test_entrypoints(
        {
            path.name: path.read_text(encoding="utf-8")
            for path in tests_directory.glob("test_*.py")
        }
    )
    check(
        "every offline regression script has an executable main entrypoint",
        not entrypoint_errors,
        repr(entrypoint_errors),
    )

    dispatch_errors = validate_leaf_dispatches(
        LEAF_DISPATCH_PATHS,
        actual_schema,
    )
    check(
        "baseline dispatch registry exactly covers every leaf command",
        not dispatch_errors,
        repr(dispatch_errors),
    )

    calls = []
    logged_in = {"value": True}
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        home = root / "home"
        home.mkdir()
        upload_file = root / "file.bin"
        upload_file.write_bytes(b"baseline")
        upload_directory = root / "folder"
        upload_directory.mkdir()
        (upload_directory / "data.txt").write_text(
            "baseline", encoding="utf-8"
        )

        with ExitStack() as stack:
            stack.enter_context(patch("pathlib.Path.home", return_value=home))
            stack.enter_context(
                patch.object(
                    cli_mod.config,
                    "is_logged_in",
                    side_effect=lambda: logged_in["value"],
                )
            )
            stack.enter_context(
                patch.object(cli_mod.config, "clear_credentials")
            )
            stack.enter_context(
                patch.object(cli_mod, "check_git_available", return_value=False)
            )
            stack.enter_context(
                patch.object(
                    cli_mod,
                    "completion_script",
                    side_effect=lambda command, shell: (
                        calls.append(("completion-show", command, shell))
                        or "#compdef atomgit\n"
                    ),
                )
            )
            stack.enter_context(
                patch.object(
                    cli_mod,
                    "install_completion",
                    side_effect=lambda command, shell: (
                        calls.append(("completion-install", command, shell))
                        or (root / "atomgit.zsh", home / ".zshrc")
                    ),
                )
            )
            stack.enter_context(
                patch.object(
                    cli_mod,
                    "uninstall_completion",
                    side_effect=lambda shell: calls.append(
                        ("completion-uninstall", shell)
                    ),
                )
            )

            stack.enter_context(
                patch.object(
                    cli_mod.api,
                    "login",
                    side_effect=lambda token: calls.append(("login", token)) or True,
                )
            )
            stack.enter_context(
                patch.object(
                    cli_mod.api,
                    "get_login_user",
                    return_value={"login": "offline-user"},
                )
            )
            stack.enter_context(
                patch.object(
                    cli_mod.api,
                    "create_repo",
                    side_effect=lambda name, repo_type, private, exist_ok=False: (
                        calls.append(
                            ("repo-create", name, repo_type, private, exist_ok)
                        )
                        or True
                    ),
                )
            )
            stack.enter_context(
                patch.object(
                    cli_mod.api,
                    "list_repos",
                    return_value=[
                        {"full_name": "user/repo", "private": True}
                    ],
                )
            )
            stack.enter_context(
                patch.object(
                    cli_mod.api,
                    "set_repo_visibility",
                    side_effect=lambda repo_id, private: calls.append(
                        ("repo-visibility", repo_id, private)
                    )
                    or True,
                )
            )
            stack.enter_context(
                patch.object(
                    cli_mod.api,
                    "delete_repo",
                    side_effect=lambda repo_id, confirmation: calls.append(
                        ("repo-delete", repo_id, confirmation)
                    )
                    or True,
                )
            )
            stack.enter_context(
                patch.object(
                    cli_mod.api,
                    "create_branch",
                    side_effect=lambda repo_id, branch_name, source="main": (
                        calls.append(
                            ("branch-create", repo_id, branch_name, source)
                        )
                        or True
                    ),
                )
            )
            stack.enter_context(
                patch.object(
                    cli_mod.api,
                    "upload_folder",
                    side_effect=lambda path, repo_id, **kwargs: calls.append(
                        ("upload-file", Path(path), repo_id, kwargs)
                    )
                    or True,
                )
            )
            stack.enter_context(
                patch.object(
                    cli_mod.api,
                    "upload_directory",
                    side_effect=lambda path, repo_id, **kwargs: calls.append(
                        ("upload-directory", Path(path), repo_id, kwargs)
                    )
                    or True,
                )
            )
            stack.enter_context(
                patch.object(
                    cli_mod.api,
                    "download_repo",
                    side_effect=lambda repo_id, path, **kwargs: calls.append(
                        ("download", repo_id, Path(path), kwargs)
                    )
                    or True,
                )
            )
            stack.enter_context(
                patch.object(
                    cli_mod.api,
                    "download_file",
                    side_effect=lambda repo_id, filename, path, **kwargs: (
                        calls.append(
                            ("download-file", repo_id, filename, Path(path), kwargs)
                        )
                        or True
                    ),
                )
            )

            token = "fake-cli-baseline-token-never-print"
            login_result = runner.invoke(
                cli_mod.cli, ["login", "--token", token]
            )
            check(
                "login baseline dispatches safely",
                login_result.exit_code == 0
                and ("login", token) in calls
                and token not in login_result.output,
                f"exit={login_result.exit_code}",
            )

            logout_result = runner.invoke(cli_mod.cli, ["logout"])
            check(
                "logout baseline clears local credentials",
                logout_result.exit_code == 0
                and cli_mod.config.clear_credentials.call_count == 1,
                f"exit={logout_result.exit_code}",
            )

            whoami_result = runner.invoke(cli_mod.cli, ["whoami"])
            check(
                "whoami baseline reports identity",
                whoami_result.exit_code == 0
                and "offline-user" in whoami_result.output,
                f"exit={whoami_result.exit_code}",
            )

            config_result = runner.invoke(cli_mod.cli, ["config-show"])
            check(
                "config-show baseline reports login state",
                config_result.exit_code == 0
                and "已登录" in config_result.output,
                f"exit={config_result.exit_code}",
            )

            completion_show = runner.invoke(
                cli_mod.cli, ["completion", "show", "zsh"]
            )
            check(
                "completion show baseline dispatches the live command tree",
                completion_show.exit_code == 0
                and ("completion-show", cli_mod.cli, "zsh") in calls
                and "#compdef atomgit" in completion_show.output,
                f"exit={completion_show.exit_code}",
            )
            completion_install = runner.invoke(
                cli_mod.cli, ["completion", "install", "--shell", "zsh"]
            )
            check(
                "completion install baseline dispatches managed Zsh setup",
                completion_install.exit_code == 0
                and ("completion-install", cli_mod.cli, "zsh") in calls,
                f"exit={completion_install.exit_code}",
            )
            completion_uninstall = runner.invoke(
                cli_mod.cli, ["completion", "uninstall", "--shell", "zsh"]
            )
            check(
                "completion uninstall baseline dispatches managed removal",
                completion_uninstall.exit_code == 0
                and ("completion-uninstall", "zsh") in calls,
                f"exit={completion_uninstall.exit_code}",
            )

            create_result = runner.invoke(
                cli_mod.cli,
                [
                    "repo", "create", "user/repo", "--type", "model",
                    "--private",
                ],
            )
            check(
                "repo create baseline forwards visibility and type",
                create_result.exit_code == 0
                and (
                    "repo-create", "user/repo", "model", True, False
                )
                in calls,
                f"exit={create_result.exit_code}",
            )

            list_result = runner.invoke(cli_mod.cli, ["repo", "list"])
            check(
                "repo list baseline renders repository identity",
                list_result.exit_code == 0
                and "private" in list_result.output
                and "user/repo" in list_result.output,
                f"exit={list_result.exit_code}",
            )

            visibility_result = runner.invoke(
                cli_mod.cli,
                ["repo", "visibility", "user/repo", "public"],
            )
            check(
                "repo visibility baseline forwards public state",
                visibility_result.exit_code == 0
                and ("repo-visibility", "user/repo", False) in calls,
                f"exit={visibility_result.exit_code}",
            )

            delete_result = runner.invoke(
                cli_mod.cli,
                [
                    "repo", "delete", "user/repo", "--confirm", "user/repo",
                ],
            )
            check(
                "repo delete baseline preserves exact confirmation",
                delete_result.exit_code == 0
                and ("repo-delete", "user/repo", "user/repo") in calls,
                f"exit={delete_result.exit_code}",
            )

            branch_result = runner.invoke(
                cli_mod.cli,
                [
                    "repo", "branch", "create", "user/repo", "dev",
                    "--from", "main",
                ],
            )
            check(
                "branch create baseline forwards source revision",
                branch_result.exit_code == 0
                and ("branch-create", "user/repo", "dev", "main") in calls,
                f"exit={branch_result.exit_code}",
            )

            upload_file_result = runner.invoke(
                cli_mod.cli,
                [
                    "upload", str(upload_file), "--repo-id", "user/repo",
                    "--path-in-repo", "weights", "--repo-type", "model",
                ],
            )
            file_call = next(call for call in calls if call[0] == "upload-file")
            check(
                "single-file upload baseline forwards destination options",
                upload_file_result.exit_code == 0
                and file_call[1] == upload_file
                and file_call[2] == "user/repo"
                and file_call[3]["path_in_repo"] == "weights"
                and file_call[3]["repo_type"] == "model",
                f"exit={upload_file_result.exit_code}",
            )

            upload_directory_result = runner.invoke(
                cli_mod.cli,
                [
                    "upload", str(upload_directory), "--repo-id", "user/repo",
                    "--ignore", "*.tmp", "--repo-type", "dataset",
                    "--batch-size", "10", "--path-in-repo", "weights",
                    "--revision", "dev", "--num-workers", "3",
                    "--timeout", "9", "--resumable",
                ],
            )
            directory_call = next(
                call for call in calls if call[0] == "upload-directory"
            )
            check(
                "directory upload baseline forwards ignore and repository type",
                upload_directory_result.exit_code == 0
                and directory_call[1] == upload_directory
                and directory_call[3]["ignore_patterns"]
                == [
                    "._*", "**/._*", ".DS_Store", "**/.DS_Store", "*.tmp",
                ]
                and directory_call[3]["repo_type"] == "dataset"
                and directory_call[3]["resumable"] is True
                and directory_call[3]["batch_size"] == 10
                and directory_call[3]["path_in_repo"] == "weights"
                and directory_call[3]["revision"] == "dev"
                and directory_call[3]["num_workers"] == 3
                and directory_call[3]["upload_timeout"] == 9.0,
                f"exit={upload_directory_result.exit_code}",
            )

            default_batch_result = runner.invoke(
                cli_mod.cli,
                [
                    "upload", str(upload_directory), "--repo-id", "user/repo",
                    "--no-resumable",
                ],
            )
            default_batch_call = [
                call for call in calls if call[0] == "upload-directory"
            ][-1]
            check(
                "directory upload defaults outer batch size to 20",
                default_batch_result.exit_code == 0
                and default_batch_call[3]["batch_size"] == 20,
                f"exit={default_batch_result.exit_code}",
            )

            logged_in["value"] = False
            download_target = root / "repository-download"
            download_result = runner.invoke(
                cli_mod.cli,
                [
                    "download", "user/repo", "--directory",
                    str(download_target), "--verify-checksum", "--resume",
                    "--repo-type", "model",
                ],
            )
            download_call = next(call for call in calls if call[0] == "download")
            check(
                "repository download baseline supports anonymous verified resume",
                download_result.exit_code == 0
                and download_call[1] == "user/repo"
                and download_call[2] == download_target
                and download_call[3]
                == {
                    "force_download": False,
                    "repo_type": "model",
                    "verify_checksum": True,
                    "resume_download": True,
                },
                f"exit={download_result.exit_code}",
            )

            file_target = root / "file-download"
            download_file_result = runner.invoke(
                cli_mod.cli,
                [
                    "download-file", "user/repo", "weights/model.bin",
                    "--directory", str(file_target), "--force",
                    "--verify-checksum", "--repo-type", "dataset",
                ],
            )
            download_file_call = next(
                call for call in calls if call[0] == "download-file"
            )
            check(
                "single-file download baseline forwards file and safety options",
                download_file_result.exit_code == 0
                and download_file_call[1:4]
                == ("user/repo", "weights/model.bin", file_target)
                and download_file_call[4]
                == {
                    "force_download": True,
                    "repo_type": "dataset",
                    "verify_checksum": True,
                },
                f"exit={download_file_result.exit_code}",
            )

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
