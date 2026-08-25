#!/usr/bin/env python3
"""Fail closed on packaging metadata, discovery, and tool-policy drift."""

import copy
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

TESTS_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = TESTS_DIRECTORY.parent
if str(TESTS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TESTS_DIRECTORY))

from packaging_contract import (  # noqa: E402
    BUILD_SYSTEM,
    CLEAN_POLICY_FILES,
    LEGACY_TOOL_DEBT,
    PYTEST_POLICY,
    SETUPTOOLS_LAYOUT,
    TOOL_POLICY,
    black_debt,
    clean_policy_errors,
    isort_debt,
    load_pyproject,
    ruff_debt,
    setup_layout,
    validate_metadata,
)

PINNED_TOOLS = {
    "black": "24.10.0",
    "isort": "5.13.2",
    "ruff": "0.12.12",
}
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def main():
    pyproject = load_pyproject(REPOSITORY_ROOT / "pyproject.toml")
    setup_mapping = setup_layout(REPOSITORY_ROOT / "setup.py")
    metadata_errors = validate_metadata(pyproject, setup_mapping)
    check(
        "build backend, discovery, pytest, and Python 3.9 tool policy are exact",
        not metadata_errors,
        repr(metadata_errors),
    )
    check(
        "the build backend and root package mapping are explicit",
        pyproject["build-system"] == BUILD_SYSTEM
        and pyproject["tool"]["atomgit"]["packaging"] == SETUPTOOLS_LAYOUT,
        repr(pyproject),
    )
    check(
        "setuptools receives the same src package and module mapping",
        pyproject["tool"]["setuptools"] == SETUPTOOLS_LAYOUT,
        repr(pyproject.get("tool", {}).get("setuptools")),
    )
    check(
        "pytest collection remains exact after configuration consolidation",
        pyproject["tool"]["pytest"]["ini_options"] == PYTEST_POLICY
        and not (REPOSITORY_ROOT / "pytest.ini").exists(),
    )
    check(
        "Black, isort, and Ruff share the Python 3.9 target",
        pyproject["tool"]["black"] == TOOL_POLICY["black"]
        and pyproject["tool"]["isort"] == TOOL_POLICY["isort"]
        and pyproject["tool"]["ruff"]["target-version"] == "py39",
    )

    installed_versions = {}
    for tool in PINNED_TOOLS:
        try:
            installed_versions[tool] = version(tool)
        except PackageNotFoundError:
            installed_versions[tool] = None
    check(
        "executable tool versions match the bounded development contract",
        installed_versions == PINNED_TOOLS,
        repr(installed_versions),
    )

    actual_debt = {
        "black": black_debt(REPOSITORY_ROOT),
        "isort": isort_debt(REPOSITORY_ROOT),
        "ruff": ruff_debt(REPOSITORY_ROOT),
    }
    check(
        "legacy formatting and lint debt is exact and cannot grow silently",
        actual_debt == LEGACY_TOOL_DEBT,
        repr(actual_debt),
    )
    policy_errors = clean_policy_errors(REPOSITORY_ROOT)
    check(
        "new packaging contract files satisfy the clean tool policy",
        not policy_errors,
        repr(policy_errors),
    )
    check(
        "clean policy coverage names only immediate Issue-owned files",
        CLEAN_POLICY_FILES
        == {
            "src/atomgit/adapters/__init__.py",
            "src/atomgit/adapters/atomgit_v5.py",
            "src/atomgit/adapters/config.py",
            "src/atomgit/adapters/download/__init__.py",
            "src/atomgit/adapters/download/integrity.py",
            "src/atomgit/adapters/download/manifest.py",
            "src/atomgit/adapters/download/prune.py",
            "src/atomgit/adapters/download/resume.py",
            "src/atomgit/adapters/download/service.py",
            "src/atomgit/adapters/download/transport.py",
            "src/atomgit/adapters/huggingface.py",
            "src/atomgit/adapters/lfs/__init__.py",
            "src/atomgit/adapters/lfs/pointer.py",
            "src/atomgit/adapters/lfs/service.py",
            "src/atomgit/adapters/sdk_common.py",
            "src/atomgit/adapters/sdk_datasets.py",
            "src/atomgit/adapters/sdk_downloads.py",
            "src/atomgit/adapters/sdk_errors.py",
            "src/atomgit/adapters/sdk_repositories.py",
            "src/atomgit/adapters/sdk_uploads.py",
            "src/atomgit/adapters/upload/__init__.py",
            "src/atomgit/adapters/upload/contracts.py",
            "src/atomgit/adapters/upload/errors.py",
            "src/atomgit/adapters/upload/ordinary.py",
            "src/atomgit/adapters/upload/projection.py",
            "src/atomgit/adapters/upload/resumable.py",
            "src/atomgit/adapters/upload/service.py",
            "src/atomgit/api.py",
            "src/atomgit/cli.py",
            "setup.py",
            "src/atomgit/completion.py",
            "src/atomgit/compatibility/__init__.py",
            "src/atomgit/compatibility/authentication.py",
            "src/atomgit/compatibility/api.py",
            "src/atomgit/compatibility/cli.py",
            "src/atomgit/compatibility/download.py",
            "src/atomgit/compatibility/facade.py",
            "src/atomgit/compatibility/legacy_packages.py",
            "src/atomgit/compatibility/registry.py",
            "src/atomgit/compatibility/repositories.py",
            "src/atomgit/cli_contracts.py",
            "src/atomgit/config.py",
            "src/atomgit/core/__init__.py",
            "src/atomgit/core/contracts.py",
            "src/atomgit/core/errors.py",
            "src/atomgit/core/parity.py",
            "src/atomgit/core/policies.py",
            "src/atomgit/core/ports.py",
            "src/atomgit/infrastructure/__init__.py",
            "src/atomgit/infrastructure/cache.py",
            "src/atomgit/infrastructure/completion.py",
            "src/atomgit/infrastructure/environment.py",
            "src/atomgit/infrastructure/filesystem.py",
            "src/atomgit/infrastructure/managed_paths.py",
            "src/atomgit/infrastructure/output.py",
            "src/atomgit/infrastructure/release.py",
            "src/atomgit/infrastructure/uninstall.py",
            "src/atomgit/release.py",
            "src/atomgit/infrastructure/utils.py",
            "src/atomgit/infrastructure/validation.py",
            "src/atomgit/domain/__init__.py",
            "src/atomgit/domain/authentication.py",
            "src/atomgit/domain/repositories.py",
            "src/atomgit/domain/transfers.py",
            "src/atomgit/interfaces/__init__.py",
            "src/atomgit/interfaces/cli/__init__.py",
            "src/atomgit/interfaces/cli/runner.py",
            "src/atomgit/interfaces/cli/schema.py",
            "src/atomgit/interfaces/cli/commands/__init__.py",
            "src/atomgit/interfaces/cli/commands/authentication.py",
            "src/atomgit/interfaces/cli/commands/lifecycle.py",
            "src/atomgit/interfaces/cli/commands/repositories.py",
            "src/atomgit/interfaces/cli/commands/transfers.py",
            "src/atomgit/interfaces/sdk/__init__.py",
            "src/atomgit/interfaces/sdk/client.py",
            "src/atomgit/runtime.py",
            "src/atomgit/uninstaller.py",
            "src/atomgit/utils.py",
            "src/atomgit_hub.py",
            "src/atomgit/usecases/__init__.py",
            "src/atomgit/usecases/authentication.py",
            "src/atomgit/usecases/repositories.py",
            "src/atomgit/usecases/transfers.py",
            "tests/packaging_contract.py",
            "tests/test_infrastructure_utils_ownership.py",
            "tests/test_src_layout_migration.py",
            "tests/test_packaging_metadata.py",
            "tests/test_environment_lifecycle_ownership.py",
            "tests/test_download_domain_ownership.py",
            "tests/test_auth_repository_services_ownership.py",
            "tests/test_upload_domain_ownership.py",
            "tests/test_lfs_domain_ownership.py",
            "tests/test_sdk_domain_ownership.py",
            "tests/test_cli_command_ownership.py",
            "tests/test_api_facade_conversion.py",
            "tests/test_cli_facade_conversion.py",
            "tests/test_architecture_parity.py",
        },
        repr(CLEAN_POLICY_FILES),
    )

    changed_backend = copy.deepcopy(pyproject)
    changed_backend["build-system"]["build-backend"] = "legacy.backend"
    check(
        "build backend drift fails closed",
        "build-system contract mismatch"
        in validate_metadata(changed_backend, setup_mapping),
    )

    accidental_discovery = copy.deepcopy(pyproject)
    accidental_discovery["tool"]["atomgit"]["packaging"]["packages"].append("tests")
    check(
        "accidental package discovery fails closed",
        "package discovery contract mismatch"
        in validate_metadata(accidental_discovery, setup_mapping),
    )

    changed_setup = copy.deepcopy(setup_mapping)
    changed_setup["py-modules"] = []
    check(
        "setup.py and pyproject discovery drift fails closed",
        "setup.py and pyproject layout mismatch"
        in validate_metadata(pyproject, changed_setup),
    )

    changed_target = copy.deepcopy(pyproject)
    changed_target["tool"]["ruff"]["target-version"] = "py310"
    check(
        "a newer-only tool target fails closed",
        "Python 3.9 tool policy contract mismatch"
        in validate_metadata(changed_target, setup_mapping),
    )

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
