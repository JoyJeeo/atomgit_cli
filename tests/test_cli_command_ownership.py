#!/usr/bin/env python3
"""Lock CLI command implementations behind the historical Click module."""

import ast
import importlib
import inspect
import sys
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

TESTS_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = TESTS_DIRECTORY.parent
SRC_DIRECTORY = REPOSITORY_ROOT / "src"
if str(SRC_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SRC_DIRECTORY))
if str(TESTS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TESTS_DIRECTORY))

from cli_baseline_contract import (  # noqa: E402
    EXPECTED_PUBLIC_SCHEMA,
    discover_public_schema,
)

EXPECTED_OWNER_FUNCTIONS = {
    "authentication": ("login", "logout", "whoami", "config_show"),
    "lifecycle": (
        "stable_version_option",
        "update",
        "uninstall",
        "show_completion",
        "install_shell_completion",
        "uninstall_shell_completion",
    ),
    "repositories": (
        "clear_cache",
        "create",
        "list_repositories",
        "set_repository_visibility",
        "delete_repository",
        "create_branch",
    ),
    "transfers": ("upload", "download", "download_file"),
}

EXPECTED_CALLBACK_SIGNATURES = {
    "update": "(target_version, force_reinstall)",
    "uninstall": "(yes)",
    "login": "(token, token_stdin)",
    "logout": "()",
    "whoami": "()",
    "config-show": "()",
    "cache clear": "()",
    "repo create": "(repo_name, repo_type, private, public_repo, exist_ok)",
    "repo list": "()",
    "repo visibility": "(repo_id, visibility)",
    "repo delete": "(repo_id, confirm)",
    "repo branch create": "(repo_id, branch_name, source)",
    "upload": (
        "(path, repo_id, message, timeout_sec, no_progress_bar, path_in_repo, "
        "repo_type, revision, ignore, resumable, num_workers, batch_size, "
        "auto_configure_lfs)"
    ),
    "download": (
        "(repo_id, directory, force, verify_checksum, resume_download, prune, "
        "repo_type)"
    ),
    "download-file": (
        "(repo_id, filename, directory, force, verify_checksum, "
        "resume_download, repo_type)"
    ),
    "completion show": "(shell)",
    "completion install": "(shell)",
    "completion uninstall": "(shell)",
}


results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def _leaf_commands(root):
    leaves = {}

    def visit(command, path=()):
        if hasattr(command, "commands"):
            for name, child in command.commands.items():
                visit(child, path + (name,))
        elif path:
            leaves[" ".join(path)] = command

    visit(root)
    return leaves


def _function_body_is_real(function):
    source = inspect.getsource(function)
    node = ast.parse(source).body[0]
    statements = [
        statement
        for statement in node.body
        if not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        )
    ]
    return bool(statements) and not (
        len(statements) == 1 and isinstance(statements[0], (ast.Pass, ast.Return))
    )


def _context_attributes(source):
    tree = ast.parse(source)
    return {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "context"
    }


def main():
    cli_module = importlib.import_module("atomgit.cli")
    owner_modules = {}
    import_errors = []
    for owner_name in EXPECTED_OWNER_FUNCTIONS:
        try:
            owner_modules[owner_name] = importlib.import_module(
                f"atomgit.commands.{owner_name}"
            )
        except ImportError as error:
            import_errors.append(f"{owner_name}: {error}")

    check(
        "all real CLI command owner modules exist",
        set(owner_modules) == set(EXPECTED_OWNER_FUNCTIONS),
        repr(import_errors),
    )
    if import_errors:
        return 1

    provenance_errors = []
    for owner_name, function_names in EXPECTED_OWNER_FUNCTIONS.items():
        owner_module = owner_modules[owner_name]
        for function_name in function_names:
            function = getattr(owner_module, function_name, None)
            if not inspect.isfunction(function):
                provenance_errors.append(f"{owner_name}.{function_name}: missing")
                continue
            if function.__module__ != owner_module.__name__:
                provenance_errors.append(
                    f"{owner_name}.{function_name}: {function.__module__}"
                )
            if not _function_body_is_real(function):
                provenance_errors.append(
                    f"{owner_name}.{function_name}: placeholder/wrapper"
                )
    check(
        "every command implementation has one non-placeholder owner",
        not provenance_errors,
        repr(provenance_errors),
    )

    check(
        "the historical module still owns the exact Click schema",
        discover_public_schema(cli_module.cli) == EXPECTED_PUBLIC_SCHEMA,
        repr(discover_public_schema(cli_module.cli)),
    )

    leaf_commands = _leaf_commands(cli_module.cli)
    callback_signatures = {
        name: str(inspect.signature(command.callback))
        for name, command in leaf_commands.items()
    }
    check(
        "all historical command callback signatures remain exact",
        callback_signatures == EXPECTED_CALLBACK_SIGNATURES,
        repr(callback_signatures),
    )

    wrapper_errors = []
    expected_calls = {
        "update": ("lifecycle", "update"),
        "uninstall": ("lifecycle", "uninstall"),
        "login": ("authentication", "login"),
        "logout": ("authentication", "logout"),
        "whoami": ("authentication", "whoami"),
        "config-show": ("authentication", "config_show"),
        "cache clear": ("repositories", "clear_cache"),
        "repo create": ("repositories", "create"),
        "repo list": ("repositories", "list_repositories"),
        "repo visibility": ("repositories", "set_repository_visibility"),
        "repo delete": ("repositories", "delete_repository"),
        "repo branch create": ("repositories", "create_branch"),
        "upload": ("transfers", "upload"),
        "download": ("transfers", "download"),
        "download-file": ("transfers", "download_file"),
        "completion show": ("lifecycle", "show_completion"),
        "completion install": ("lifecycle", "install_shell_completion"),
        "completion uninstall": ("lifecycle", "uninstall_shell_completion"),
    }
    for command_name, (owner_name, function_name) in expected_calls.items():
        callback = leaf_commands[command_name].callback
        source = inspect.getsource(callback)
        if f"_{owner_name}_commands.{function_name}(" not in source:
            wrapper_errors.append(f"{command_name}: {source.strip()}")
        if "_COMMAND_CONTEXT" not in source:
            wrapper_errors.append(f"{command_name}: missing historical context")
    check(
        "historical schema callbacks delegate once to exact owners",
        not wrapper_errors,
        repr(wrapper_errors),
    )

    owner_sources = {
        name: inspect.getsource(module) for name, module in owner_modules.items()
    }
    check(
        "owners resolve former runtime dependencies only through context",
        all("_COMMAND_CONTEXT" not in source for source in owner_sources.values())
        and all("from atomgit." not in source for source in owner_sources.values()),
        repr(owner_sources),
    )

    missing_historical_names = {
        owner_name: sorted(
            name
            for name in _context_attributes(source)
            if not hasattr(cli_module, name)
        )
        for owner_name, source in owner_sources.items()
    }
    missing_historical_names = {
        owner_name: names
        for owner_name, names in missing_historical_names.items()
        if names
    }
    check(
        "every owner runtime lookup remains on the historical module",
        not missing_historical_names,
        repr(missing_historical_names),
    )

    runner = CliRunner()
    original_config = cli_module.config
    original_print_warning = cli_module.print_warning
    authentication_calls = []

    class LoggedOutConfig:
        config_file = Path("/tmp/fake-atomgit-config.json")

        @staticmethod
        def is_logged_in():
            return False

    cli_module.config = LoggedOutConfig()
    cli_module.print_warning = authentication_calls.append
    authentication_result = runner.invoke(cli_module.cli, ["config-show"])
    del cli_module.print_warning
    deleted_authentication_result = runner.invoke(cli_module.cli, ["config-show"])
    cli_module.config = original_config
    cli_module.print_warning = original_print_warning
    check(
        "authentication owner honors historical assignment and deletion",
        authentication_result.exit_code == 0
        and authentication_calls == ["当前未登录"]
        and deleted_authentication_result.exit_code == 1
        and cli_module.config is original_config
        and cli_module.print_warning is original_print_warning,
        repr(
            {
                "assigned": authentication_result.exit_code,
                "deleted": deleted_authentication_result.exit_code,
                "calls": authentication_calls,
            }
        ),
    )

    original_clear_cache = cli_module.clear_atomgit_cache
    cache_calls = []
    cli_module.clear_atomgit_cache = lambda: cache_calls.append("clear") or 3
    assigned_result = runner.invoke(cli_module.cli, ["cache", "clear"])
    del cli_module.clear_atomgit_cache
    deleted_result = runner.invoke(cli_module.cli, ["cache", "clear"])
    cli_module.clear_atomgit_cache = original_clear_cache
    check(
        "repository owner honors historical assignment and deletion",
        assigned_result.exit_code == 0
        and cache_calls == ["clear"]
        and "移除 3 项" in assigned_result.output
        and deleted_result.exit_code == 1
        and "清理 AtomGit 缓存失败" in deleted_result.output
        and cli_module.clear_atomgit_cache is original_clear_cache,
        repr(
            {
                "assigned": assigned_result.exit_code,
                "deleted": deleted_result.exit_code,
                "calls": cache_calls,
                "restored": cli_module.clear_atomgit_cache is original_clear_cache,
            }
        ),
    )

    original_validate_repo_name = cli_module.validate_repo_name
    transfer_calls = []
    cli_module.validate_repo_name = (
        lambda repo_id: transfer_calls.append(repo_id) or False
    )
    transfer_result = runner.invoke(cli_module.cli, ["download", "invalid/repository"])
    del cli_module.validate_repo_name
    deleted_transfer_result = runner.invoke(
        cli_module.cli, ["download", "invalid/repository"]
    )
    cli_module.validate_repo_name = original_validate_repo_name
    check(
        "transfer owner honors historical assignment and deletion",
        transfer_result.exit_code == 1
        and transfer_calls == ["invalid/repository"]
        and "仓库ID格式不正确" in transfer_result.output
        and deleted_transfer_result.exit_code == 1
        and cli_module.validate_repo_name is original_validate_repo_name,
        repr(
            {
                "assigned": transfer_result.exit_code,
                "deleted": deleted_transfer_result.exit_code,
                "calls": transfer_calls,
            }
        ),
    )

    lifecycle_calls = []
    with patch.object(
        cli_module,
        "run_update",
        lambda **kwargs: lifecycle_calls.append(kwargs)
        or {
            "status": "skipped",
            "version": "1.1.1",
        },
    ):
        patched_result = runner.invoke(cli_module.cli, ["update"])
    check(
        "patch.object on the historical lifecycle seam reaches its owner",
        patched_result.exit_code == 0
        and lifecycle_calls
        and lifecycle_calls[0]["python"] == sys.executable
        and cli_module.run_update is not None,
        repr(
            {
                "exit": patched_result.exit_code,
                "calls": lifecycle_calls,
            }
        ),
    )

    original_run_update = cli_module.run_update
    cli_module.run_update = lambda **kwargs: {
        "status": "skipped",
        "version": "1.1.1",
    }
    lifecycle_assignment_result = runner.invoke(cli_module.cli, ["update"])
    del cli_module.run_update
    deleted_lifecycle_result = runner.invoke(cli_module.cli, ["update"])
    cli_module.run_update = original_run_update
    check(
        "lifecycle owner honors historical assignment and deletion",
        lifecycle_assignment_result.exit_code == 0
        and deleted_lifecycle_result.exit_code == 1
        and cli_module.run_update is original_run_update,
        repr(
            {
                "assigned": lifecycle_assignment_result.exit_code,
                "deleted": deleted_lifecycle_result.exit_code,
            }
        ),
    )

    cli_source = inspect.getsource(cli_module)
    check(
        "API and CLI facade conversion remain later work",
        (SRC_DIRECTORY / "atomgit" / "api" / "__init__.py").is_file()
        and (SRC_DIRECTORY / "atomgit" / "cli.py").is_file()
        and not (SRC_DIRECTORY / "atomgit" / "cli").exists()
        and 'api = _LazyObject("api", "api")' in cli_source,
    )

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
