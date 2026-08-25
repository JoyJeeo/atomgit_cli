#!/usr/bin/env python3
"""Lock historical CLI paths to one canonical compatibility facade."""

import ast
import importlib
import inspect
import os
import subprocess
import sys
from pathlib import Path

TESTS_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = TESTS_DIRECTORY.parent
SRC_DIRECTORY = REPOSITORY_ROOT / "src"
PACKAGE_DIRECTORY = SRC_DIRECTORY / "atomgit"
if str(SRC_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SRC_DIRECTORY))
if str(TESTS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TESTS_DIRECTORY))

from cli_baseline_contract import (  # noqa: E402
    EXPECTED_PUBLIC_SCHEMA,
    discover_public_schema,
)

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
EXPECTED_COMMAND_EXPORTS = {
    "update",
    "uninstall",
    "completion",
    "show_completion",
    "install_shell_completion",
    "uninstall_shell_completion",
    "login",
    "logout",
    "whoami",
    "repo",
    "cache",
    "clear_cache",
    "create",
    "list_repositories",
    "set_repository_visibility",
    "delete_repository",
    "branch_commands",
    "create_branch",
    "upload",
    "download",
    "download_file",
    "config_show",
}
FORBIDDEN_FACADE_CALLS = {
    "open",
    "urlopen",
    "request",
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "sleep",
    "run",
    "Popen",
    "mkdtemp",
    "TemporaryDirectory",
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


def _module_help(module_name):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SRC_DIRECTORY)
    environment.pop("_ATOMGIT_COMPLETE", None)
    return subprocess.run(
        [sys.executable, "-m", module_name, "--help"],
        cwd=REPOSITORY_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def main():
    flat_path = PACKAGE_DIRECTORY / "cli.py"
    facade_path = PACKAGE_DIRECTORY / "cli" / "__init__.py"
    executable_path = PACKAGE_DIRECTORY / "cli" / "__main__.py"
    owner_path = PACKAGE_DIRECTORY / "compatibility" / "cli.py"
    check(
        "root CLI shim and canonical facade replace the historical package",
        not facade_path.exists()
        and not executable_path.exists()
        and flat_path.is_file()
        and owner_path.is_file(),
        repr(
            {
                "flat": flat_path.exists(),
                "facade": facade_path.is_file(),
                "executable": executable_path.is_file(),
                "owner": owner_path.is_file(),
            }
        ),
    )
    if not owner_path.is_file() or not flat_path.is_file():
        return 1

    source = owner_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(owner_path))
    cli_module = importlib.import_module("atomgit.cli")
    owner_module = importlib.import_module("atomgit.compatibility.cli")
    atomgit_package = importlib.import_module("atomgit")
    schema_module = importlib.import_module("atomgit.interfaces.cli.schema")
    executable_module = importlib.import_module("atomgit.cli.__main__")

    check(
        "historical CLI import forwards through the root shim",
        cli_module.__name__ == "atomgit.cli"
        and Path(cli_module.__file__).resolve() == flat_path.resolve()
        and cli_module.__package__ == "atomgit"
        and tuple(cli_module.__path__) == ()
        and executable_module.__name__ == "atomgit.cli.__main__"
        and executable_module.cli is owner_module.cli,
        repr(
            {
                "name": cli_module.__name__,
                "file": cli_module.__file__,
                "package": cli_module.__package__,
            }
        ),
    )

    leaves = _leaf_commands(cli_module.cli)
    callback_signatures = {
        name: str(inspect.signature(command.callback))
        for name, command in leaves.items()
    }
    check(
        "the facade preserves the exact Click tree callbacks and package export",
        discover_public_schema(cli_module.cli) == EXPECTED_PUBLIC_SCHEMA
        and callback_signatures == EXPECTED_CALLBACK_SIGNATURES
        and all(
            command.callback.__module__ == "atomgit.compatibility.cli"
            for command in leaves.values()
        )
        and atomgit_package.cli is cli_module.cli,
        repr(callback_signatures),
    )

    check(
        "lazy runtime resolution targets the parent package and historical context",
        cli_module._COMMAND_CONTEXT is owner_module
        and cli_module._import_runtime_module("api").__name__
        == "atomgit.compatibility.api"
        and cli_module._import_runtime_module("utils").__name__ == "atomgit.utils"
        and cli_module.api._resolve() is importlib.import_module("atomgit.api").api,
    )

    top_level_definitions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    check(
        "the CLI facade contains schema assembly rather than command business work",
        "_LazyObject" in top_level_definitions
        and {"cli", "_LazyObject", "_import_runtime_module"} <= top_level_definitions
        and not (called_names & FORBIDDEN_FACADE_CALLS),
        repr(
            {
                "definitions": sorted(top_level_definitions),
                "forbidden_calls": sorted(called_names & FORBIDDEN_FACADE_CALLS),
            }
        ),
    )

    check(
        "the Click schema has one canonical interface owner",
        cli_module.cli is not None
        and schema_module.build_cli.__module__ == "atomgit.interfaces.cli.schema"
        and all(
            command.callback.__module__ == "atomgit.compatibility.cli"
            for command in leaves.values()
        ),
    )
    check(
        "historical command objects remain importable from atomgit.cli",
        all(hasattr(cli_module, name) for name in EXPECTED_COMMAND_EXPORTS)
        and cli_module.login is leaves["login"]
        and cli_module.upload is leaves["upload"]
        and cli_module.repo is cli_module.cli.commands["repo"],
    )

    module_results = {
        module_name: _module_help(module_name)
        for module_name in ("atomgit", "atomgit.cli", "atomgit.cli.__main__")
    }
    check(
        "both historical Python module entry paths retain executable help",
        all(result.returncode == 0 for result in module_results.values())
        and all("Usage:" in result.stdout for result in module_results.values())
        and "RuntimeWarning" not in module_results["atomgit.cli.__main__"].stderr,
        repr(
            {
                name: (result.returncode, result.stdout, result.stderr)
                for name, result in module_results.items()
            }
        ),
    )

    api_facade = PACKAGE_DIRECTORY / "compatibility" / "api.py"
    check(
        "the completed API facade remains outside the CLI migration",
        api_facade.is_file()
        and (PACKAGE_DIRECTORY / "api.py").is_file()
        and importlib.import_module("atomgit.api").__file__ == str(api_facade),
    )

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
