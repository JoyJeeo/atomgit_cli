#!/usr/bin/env python3
"""Lock exact SDK owners behind both historical compatibility paths."""

import ast
import importlib
import inspect
import sys
from pathlib import Path
from unittest.mock import patch

TESTS_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = TESTS_DIRECTORY.parent
SOURCE_ROOT = REPOSITORY_ROOT / "src"
for import_path in (str(TESTS_DIRECTORY), str(SOURCE_ROOT)):
    if import_path not in sys.path:
        sys.path.insert(0, import_path)

from structure_contract import (  # noqa: E402
    LEGACY_FACADE_DEBT,
    PRODUCTION_MODULE_OWNERS,
    discover_source_texts,
    validate_structure,
)

SDK_MODULES = (
    "sdk.__init__",
    "sdk.common",
    "sdk.datasets",
    "sdk.downloads",
    "sdk.errors",
    "sdk.repositories",
    "sdk.uploads",
)

SDK_OWNER_MODULES = (
    "adapters.sdk_datasets",
    "adapters.sdk_downloads",
    "adapters.sdk_common",
    "adapters.sdk_errors",
    "adapters.sdk_repositories",
    "adapters.sdk_uploads",
)

PUBLIC_OWNERS = {
    "snapshot_download": "adapters.sdk_downloads",
    "hub_download_url": "adapters.sdk_downloads",
    "download_file": "adapters.sdk_downloads",
    "upload_folder": "adapters.sdk_uploads",
    "create_repository": "adapters.sdk_repositories",
    "load_dataset": "adapters.sdk_datasets",
}

PRIVATE_OWNERS = {
    "_get_token": "adapters.sdk_common",
    "_normalize_repo_id": "adapters.sdk_common",
    "_atomgit_repo_type": "adapters.sdk_common",
    "_sdk_error": "adapters.sdk_errors",
}

HISTORICAL_PATCH_NAMES = {
    *PUBLIC_OWNERS,
    *PRIVATE_OWNERS,
    "hf_snapshot_download",
    "hf_hub_download",
    "hf_upload_folder",
    "create_repo",
    "ds_load_dataset",
    "DATASET_SUPPORT",
    "HF_DATASETS_CACHE",
    "Path",
    "os",
    "warnings",
    "config",
    "normalize_repo_id",
    "auth_error_kind",
    "is_retryable_download_error",
    "CanonicalLfsPointerError",
    "run_download_with_retry",
    "validate_upload_path_no_symlinks",
    "run_canonical_lfs_upload",
    "AtomGitError",
    "AtomGitAuthenticationError",
    "AtomGitNetworkError",
    "AtomGitRepositoryExistsError",
    "AtomGitRepositoryNotFoundError",
    "AtomGitRevisionNotFoundError",
    "AtomGitTimeoutError",
    "AtomGitUnsupportedError",
}

PUBLIC_SIGNATURES = {
    "snapshot_download": "(repo_id: str, revision: Optional[str] = None, cache_dir: Union[str, pathlib.Path, NoneType] = None, local_dir: Union[str, pathlib.Path, NoneType] = None, local_dir_use_symlinks: Union[bool, str] = 'auto', library_name: Optional[str] = None, library_version: Optional[str] = None, user_agent: Union[str, Dict[str, str], NoneType] = None, proxies: Optional[Dict[str, str]] = None, etag_timeout: float = 10, resume_download: bool = False, force_download: bool = False, token: Union[bool, str, NoneType] = None, local_files_only: bool = False, allow_patterns: Union[List[str], str, NoneType] = None, ignore_patterns: Union[List[str], str, NoneType] = None, max_workers: int = 8, tqdm_class: Optional[Any] = None) -> str",
    "hub_download_url": "(repo_id: str, filename: str, revision: Optional[str] = None, repo_type: Optional[str] = None) -> str",
    "download_file": "(repo_id: str, filename: str, local_dir: Union[str, pathlib.Path, NoneType] = None, revision: Optional[str] = None, token: Optional[str] = None, force_download: bool = False) -> str",
    "upload_folder": "(folder_path: Union[str, pathlib.Path], repo_id: str, token: Optional[str] = None, repo_type: Optional[str] = None, revision: Optional[str] = None, commit_message: Optional[str] = None, commit_description: Optional[str] = None, path_in_repo: str = './', ignore_patterns: Optional[List[str]] = None, upload_timeout: float = 300.0) -> str",
    "create_repository": "(repo_id: str, token: Optional[str] = None, private: bool = False, repo_type: str = 'model', exist_ok: bool = False, space_sdk: Optional[str] = None, space_hardware: Optional[str] = None, space_storage: Optional[str] = None, space_sleep_time: Optional[int] = None, space_secrets: Optional[List[Dict]] = None, space_variables: Optional[List[Dict]] = None) -> str",
}

results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def _top_level_definitions(source):
    return {
        node.name
        for node in ast.parse(source).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def _loaded_names(source):
    return {
        node.id
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }


def main():
    results.clear()
    source_texts = discover_source_texts(REPOSITORY_ROOT)
    missing = tuple(name for name in SDK_OWNER_MODULES if name not in source_texts)
    check("all approved SDK canonical owners contain real implementation", not missing)
    if missing:
        print(f"summary: 0/{len(results)} passed")
        return 1

    package_facade = importlib.import_module("atomgit.atomgit_hub")
    top_level_facade = importlib.import_module("atomgit_hub")
    package = importlib.import_module("atomgit")
    owner_modules = {
        name: importlib.import_module(f"atomgit.{name}") for name in SDK_OWNER_MODULES
    }
    historical_modules = {
        name: importlib.import_module(f"atomgit.{name}")
        for name in SDK_MODULES
        if name != "sdk.__init__"
    }

    check(
        "historical SDK modules alias canonical owners",
        historical_modules["sdk.common"] is owner_modules["adapters.sdk_common"]
        and historical_modules["sdk.errors"] is owner_modules["adapters.sdk_errors"]
        and historical_modules["sdk.datasets"] is owner_modules["adapters.sdk_datasets"]
        and historical_modules["sdk.downloads"]
        is owner_modules["adapters.sdk_downloads"]
        and historical_modules["sdk.repositories"]
        is owner_modules["adapters.sdk_repositories"]
        and historical_modules["sdk.uploads"] is owner_modules["adapters.sdk_uploads"],
    )

    check(
        "historical public SDK functions remain exact owner identities",
        all(
            getattr(package_facade, name) is getattr(owner_modules[owner], name)
            and getattr(top_level_facade, name) is getattr(owner_modules[owner], name)
            for name, owner in PUBLIC_OWNERS.items()
        ),
    )
    check(
        "package exports remain exact historical SDK identities",
        all(
            getattr(package, name) is getattr(package_facade, name)
            for name in PUBLIC_OWNERS
            if name != "load_dataset"
        ),
    )
    check(
        "historical private SDK helpers remain exact owner identities",
        all(
            getattr(package_facade, name) is getattr(owner_modules[owner], name)
            and getattr(top_level_facade, name) is getattr(owner_modules[owner], name)
            for name, owner in PRIVATE_OWNERS.items()
        ),
    )
    check(
        "historical public SDK signatures remain unchanged",
        all(
            str(inspect.signature(getattr(package_facade, name))) == signature
            for name, signature in PUBLIC_SIGNATURES.items()
        ),
    )
    check(
        "historical SDK patch registry is exhaustive and exact",
        set(package_facade._SDK_PATCH_TARGETS) == HISTORICAL_PATCH_NAMES,
        repr(sorted(set(package_facade._SDK_PATCH_TARGETS) ^ HISTORICAL_PATCH_NAMES)),
    )

    runtime_modules = set(owner_modules.values())
    missing_consumers = {}
    for name, targets in package_facade._SDK_PATCH_TARGETS.items():
        expected = {
            module
            for module in runtime_modules
            if name
            in _loaded_names(source_texts[module.__name__.removeprefix("atomgit.")])
        }
        registered = set(targets)
        if not expected <= registered:
            missing_consumers[name] = sorted(
                module.__name__ for module in expected - registered
            )
    check(
        "every moved SDK symbol registers all new resolution sites",
        not missing_consumers,
        repr(missing_consumers),
    )

    initial_mismatches = []
    assignment_mismatches = []
    deletion_mismatches = []
    restoration_mismatches = []
    for name, targets in package_facade._SDK_PATCH_TARGETS.items():
        original = getattr(package_facade, name)
        if any(getattr(target, name, object()) is not original for target in targets):
            initial_mismatches.append(name)

        replacement = object()
        setattr(top_level_facade, name, replacement)
        try:
            if getattr(package_facade, name, object()) is not replacement or any(
                getattr(target, name, object()) is not replacement for target in targets
            ):
                assignment_mismatches.append(name)
            delattr(top_level_facade, name)
            if hasattr(package_facade, name) or any(
                hasattr(target, name) for target in targets
            ):
                deletion_mismatches.append(name)
        finally:
            setattr(top_level_facade, name, original)

        if getattr(package_facade, name, object()) is not original or any(
            getattr(target, name, object()) is not original for target in targets
        ):
            restoration_mismatches.append(name)

    check(
        "every registered SDK seam starts with exact shared identity",
        not initial_mismatches,
        repr(initial_mismatches),
    )
    check(
        "assigning every top-level SDK seam reaches former resolution sites",
        not assignment_mismatches,
        repr(assignment_mismatches),
    )
    check(
        "deleting every top-level SDK seam removes former resolution sites",
        not deletion_mismatches,
        repr(deletion_mismatches),
    )
    check(
        "restoring every top-level SDK seam restores exact shared identity",
        not restoration_mismatches,
        repr(restoration_mismatches),
    )

    sentinel = object()
    with patch.object(top_level_facade, "hf_upload_folder", sentinel):
        check(
            "patch.object on the top-level facade reaches the upload owner",
            owner_modules["adapters.sdk_uploads"].hf_upload_folder is sentinel,
        )

    facade_definitions = _top_level_definitions(source_texts["atomgit_hub"])
    check(
        "the package SDK facade contains no moved implementation definitions",
        not (set(PUBLIC_OWNERS) | set(PRIVATE_OWNERS)) & facade_definitions,
    )
    check(
        "canonical SDK owners replace physically absent historical aliases",
        all(PRODUCTION_MODULE_OWNERS[name] == "adapters" for name in SDK_OWNER_MODULES)
        and all(name not in source_texts for name in SDK_MODULES),
    )
    check(
        "the historical SDK facade debt ceiling tightens with moved implementation",
        LEGACY_FACADE_DEBT["atomgit_hub"]["max_lines"] < 734
        and LEGACY_FACADE_DEBT["atomgit_hub"]["max_functions"] < 10,
    )

    placeholder = dict(source_texts)
    placeholder["adapters.sdk_downloads"] = '"""Placeholder."""\npass\n'
    errors = validate_structure(placeholder)
    check(
        "an SDK placeholder replacement fails closed",
        any("empty placeholder" in error for error in errors),
        repr(errors),
    )
    unowned = dict(source_texts)
    unowned["adapters.sdk_future"] = "VALUE = 1\n"
    errors = validate_structure(unowned)
    check(
        "an unowned SDK implementation fails closed",
        any("sdk_future" in error and "unowned" in error for error in errors),
        repr(errors),
    )

    check(
        "CLI API and LFS implementation remain outside the SDK package",
        "class HuggingFaceAPI(" in source_texts["compatibility.api"]
        and "def _configure_remote_lfs_attributes("
        in source_texts["adapters.lfs.service"]
        and "def cli(" in source_texts["compatibility.cli"],
    )
    check(
        "historical SDK paths contain no physical source modules",
        all(name not in source_texts for name in SDK_MODULES),
    )

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
