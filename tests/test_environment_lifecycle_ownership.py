#!/usr/bin/env python3
"""Fail closed on infrastructure lifecycle ownership and historical seams."""

import ast
import importlib
import inspect
import sys
from pathlib import Path
from unittest.mock import patch

TESTS_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = TESTS_DIRECTORY.parent
if str(TESTS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TESTS_DIRECTORY))

from structure_contract import (  # noqa: E402
    LEGACY_FACADE_DEBT,
    LEGACY_FORBIDDEN_EDGES,
    PRODUCTION_MODULE_OWNERS,
    discover_internal_edges,
    discover_source_texts,
    validate_structure,
)

LIFECYCLE_MODULES = (
    "lifecycle.__init__",
    "lifecycle.completion",
    "lifecycle.environment",
    "lifecycle.managed_paths",
    "lifecycle.uninstall",
)
INFRASTRUCTURE_LIFECYCLE_MODULES = (
    "infrastructure.completion",
    "infrastructure.environment",
    "infrastructure.managed_paths",
    "infrastructure.uninstall",
)

HISTORICAL_COMPLETION_SYMBOLS = (
    "os",
    "shlex",
    "stat",
    "sys",
    "tempfile",
    "Path",
    "get_completion_class",
    "SUPPORTED_SHELLS",
    "CompletionConfigError",
    "completion_script",
    "_completion_path",
    "_active_conda_prefix",
    "_ensure_managed_directory",
    "_activation_hook",
    "_deactivation_hook",
    "_zshrc_path",
    "_ensure_directory",
    "_file_fingerprint",
    "_read_snapshot",
    "_atomic_write",
    "_write_backup_once",
    "_remove_if_unchanged",
    "_split_managed_block",
    "_managed_block",
    "legacy_completion_present",
    "_remove_legacy_completion",
    "install_completion",
    "uninstall_completion",
)

HISTORICAL_UNINSTALLER_SYMBOLS = (
    "importlib",
    "os",
    "stat",
    "subprocess",
    "sys",
    "Path",
    "MANAGED_COMPLETION_RELATIVE_PATHS",
    "UninstallError",
    "_is_source_or_editable_install",
    "_resolved_directory",
    "active_conda_prefix",
    "managed_completion_paths",
    "_fingerprint",
    "_managed_parent_exists",
    "remove_managed_completion",
    "build_uninstall_plan",
    "run_uninstall",
)


results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def _top_level_definitions(source):
    tree = ast.parse(source)
    return tuple(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    )


def main():
    results.clear()
    source_texts = discover_source_texts(REPOSITORY_ROOT)
    missing = tuple(
        name for name in INFRASTRUCTURE_LIFECYCLE_MODULES if name not in source_texts
    )
    check(
        "all approved infrastructure lifecycle owners contain real implementation",
        not missing,
        repr(missing),
    )
    if missing:
        print(f"summary: 0/{len(results)} passed")
        return 1

    completion = importlib.import_module("atomgit.completion")
    uninstaller = importlib.import_module("atomgit.uninstaller")
    completion_owner = importlib.import_module("atomgit.infrastructure.completion")
    environment_owner = importlib.import_module("atomgit.infrastructure.environment")
    managed_paths_owner = importlib.import_module(
        "atomgit.infrastructure.managed_paths"
    )
    uninstall_owner = importlib.import_module("atomgit.infrastructure.uninstall")
    historical_owners = tuple(
        (
            importlib.import_module(f"atomgit.{name.rsplit('.', 1)[0]}")
            if name.endswith(".__init__")
            else importlib.import_module(f"atomgit.{name}")
        )
        for name in LIFECYCLE_MODULES
    )
    release = importlib.import_module("atomgit.release")
    release_owner = importlib.import_module("atomgit.infrastructure.release")

    check(
        "historical lifecycle modules alias infrastructure owners",
        historical_owners[1] is completion_owner
        and historical_owners[2] is environment_owner
        and historical_owners[3] is managed_paths_owner
        and historical_owners[4] is uninstall_owner,
    )
    check(
        "historical completion symbols remain exact owner identities",
        all(hasattr(completion, name) for name in HISTORICAL_COMPLETION_SYMBOLS)
        and all(
            getattr(completion, name) is getattr(completion_owner, name)
            for name in HISTORICAL_COMPLETION_SYMBOLS
            if hasattr(completion_owner, name)
        ),
    )
    check(
        "historical uninstaller symbols remain exact owner identities",
        all(hasattr(uninstaller, name) for name in HISTORICAL_UNINSTALLER_SYMBOLS)
        and uninstaller.UninstallError is managed_paths_owner.UninstallError
        and uninstaller.active_conda_prefix is environment_owner.active_conda_prefix
        and uninstaller.managed_completion_paths
        is managed_paths_owner.managed_completion_paths
        and uninstaller.remove_managed_completion
        is managed_paths_owner.remove_managed_completion
        and uninstaller.build_uninstall_plan is uninstall_owner.build_uninstall_plan
        and uninstaller.run_uninstall is uninstall_owner.run_uninstall,
    )
    check(
        "historical signatures are unchanged at their owner paths",
        all(
            inspect.signature(getattr(completion, name))
            == inspect.signature(getattr(completion_owner, name))
            for name in (
                "completion_script",
                "install_completion",
                "uninstall_completion",
            )
        )
        and all(
            inspect.signature(getattr(uninstaller, name))
            == inspect.signature(getattr(owner, name))
            for name, owner in (
                ("active_conda_prefix", environment_owner),
                ("managed_completion_paths", managed_paths_owner),
                ("remove_managed_completion", managed_paths_owner),
                ("build_uninstall_plan", uninstall_owner),
                ("run_uninstall", uninstall_owner),
            )
        ),
    )
    check(
        "source and editable install policy has one lifecycle identity",
        uninstaller._is_source_or_editable_install
        is environment_owner.is_source_or_editable_install
        and release._is_source_or_editable_install
        is environment_owner.is_source_or_editable_install,
    )
    check(
        "release facade forwards implementation identities",
        release.is_stable_version is release_owner.is_stable_version
        and release.validate_release_assets is release_owner.validate_release_assets
        and release._main is release_owner._main
        and release._is_source_or_editable_install
        is release_owner._is_source_or_editable_install,
    )
    check(
        "managed completion manifest has one lifecycle identity",
        uninstaller.MANAGED_COMPLETION_RELATIVE_PATHS
        is managed_paths_owner.MANAGED_COMPLETION_RELATIVE_PATHS,
    )

    replacement = object()
    with patch.object(release, "MAX_RESPONSE_BYTES", replacement):
        check(
            "patching historical release seam reaches infrastructure owner",
            release_owner.MAX_RESPONSE_BYTES is replacement,
        )
    with patch.object(completion, "_active_conda_prefix", replacement):
        check(
            "patching historical completion environment seam reaches its owner",
            completion_owner._active_conda_prefix is replacement,
        )
    with patch.object(completion, "_atomic_write", replacement):
        check(
            "patching historical completion private seam reaches its owner",
            completion_owner._atomic_write is replacement,
        )
    with patch.object(completion, "legacy_completion_present", replacement):
        check(
            "patching historical completion callable seam reaches its owner",
            completion_owner.legacy_completion_present is replacement,
        )
    with patch.object(completion, "Path", replacement):
        check(
            "patching historical completion Path reaches its owner",
            completion_owner.Path is replacement,
        )
    with patch.object(uninstaller, "active_conda_prefix", replacement):
        check(
            "patching historical uninstall environment seam reaches only its call site",
            uninstall_owner.active_conda_prefix is replacement
            and environment_owner.active_conda_prefix is not replacement,
        )
    environment_had_private_origin = hasattr(
        environment_owner, "_is_source_or_editable_install"
    )
    with patch.object(uninstaller, "_is_source_or_editable_install", replacement):
        check(
            "patching historical install-origin seam reaches uninstall owner",
            uninstall_owner._is_source_or_editable_install is replacement,
        )
    check(
        "historical install-origin patch cleanup does not grow the environment owner",
        hasattr(environment_owner, "_is_source_or_editable_install")
        is environment_had_private_origin,
    )
    with patch.object(uninstaller, "Path", replacement):
        check(
            "patching historical uninstall Path reaches every former call site",
            environment_owner.Path is replacement
            and managed_paths_owner.Path is replacement
            and uninstall_owner.Path is replacement,
        )
    with patch.object(uninstaller, "os", replacement):
        check(
            "patching historical uninstall os reaches environment policy",
            environment_owner.os is replacement,
        )
    with patch.object(uninstaller, "stat", replacement):
        check(
            "patching historical uninstall stat reaches managed paths",
            managed_paths_owner.stat is replacement,
        )
    with patch.object(uninstaller, "subprocess", replacement):
        check(
            "patching historical uninstall subprocess reaches its owner",
            uninstall_owner.subprocess is replacement,
        )

    check(
        "historical lifecycle facades contain no owned definitions",
        not _top_level_definitions(source_texts["completion"])
        and not _top_level_definitions(source_texts["uninstaller"])
        and LEGACY_FACADE_DEBT["completion"]["max_functions"] == 0
        and LEGACY_FACADE_DEBT["completion"]["max_classes"] == 0
        and LEGACY_FACADE_DEBT["uninstaller"]["max_functions"] == 0
        and LEGACY_FACADE_DEBT["uninstaller"]["max_classes"] == 0,
    )
    check(
        "infrastructure owners replace physically absent lifecycle aliases",
        all(
            PRODUCTION_MODULE_OWNERS[name] == "infrastructure"
            for name in INFRASTRUCTURE_LIFECYCLE_MODULES
        )
        and all(name not in source_texts for name in LIFECYCLE_MODULES),
    )
    check(
        "the legacy uninstaller-to-release edge is removed exactly",
        ("uninstaller", "release") not in LEGACY_FORBIDDEN_EDGES
        and ("uninstaller", "release") not in discover_internal_edges(source_texts),
    )

    regrown = dict(source_texts)
    regrown["completion"] += "\n\ndef future_completion_behavior():\n    return None\n"
    errors = validate_structure(regrown)
    check(
        "historical lifecycle facade regrowth fails closed",
        any(
            "legacy facade debt contract is stale in completion" in error
            for error in errors
        ),
        repr(errors),
    )
    placeholder = dict(source_texts)
    placeholder["infrastructure.environment"] = '"""Placeholder."""\npass\n'
    errors = validate_structure(placeholder)
    check(
        "lifecycle placeholder replacement fails closed",
        any("empty placeholder" in error for error in errors),
        repr(errors),
    )

    shell = (REPOSITORY_ROOT / "uninstall.sh").read_text(encoding="utf-8")
    check(
        "package-absent Shell fallback carries the exact Python manifest",
        all(
            str(relative) in shell
            for relative in uninstaller.MANAGED_COMPLETION_RELATIVE_PATHS
        )
        and "config.json" not in shell
        and "git-credential-atomgit" not in shell,
    )

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
