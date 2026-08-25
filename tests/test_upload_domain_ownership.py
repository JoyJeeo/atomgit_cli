#!/usr/bin/env python3
"""Lock exact upload owners behind the historical API compatibility path."""

import ast
import importlib
import inspect
import sys
from pathlib import Path

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

UPLOAD_OWNER_MODULES = (
    "adapters.upload.__init__",
    "adapters.upload.contracts",
    "adapters.upload.errors",
    "adapters.upload.ordinary",
    "adapters.upload.projection",
    "adapters.upload.resumable",
    "adapters.upload.service",
)
UPLOAD_COMPATIBILITY_MODULES = (
    "upload.__init__",
    "upload.contracts",
    "upload.errors",
    "upload.ordinary",
    "upload.projection",
    "upload.resumable",
    "upload.service",
)

HISTORICAL_HELPER_OWNERS = {
    "_set_progress_bar": "adapters.upload.ordinary",
    "_capture_progress_bar_state": "adapters.upload.ordinary",
    "_restore_progress_bar_state": "adapters.upload.ordinary",
    "_upload_folder_with_workers": "adapters.upload.ordinary",
    "ResumableProjectionError": "adapters.upload.projection",
    "_resumable_projection_cache_root": "adapters.upload.projection",
    "_prepare_resumable_upload_projection": "adapters.upload.projection",
    "_collect_resumable_upload_files": "adapters.upload.projection",
    "_resumable_committed_file_count": "adapters.upload.projection",
    "ResumableTargetRevisionError": "adapters.upload.errors",
    "ResumableWorkerError": "adapters.upload.errors",
    "ResumableCommitError": "adapters.upload.errors",
    "_classify_upload_error": "adapters.upload.errors",
    "_run_resumable_upload": "adapters.upload.resumable",
    "_execute_resumable_upload_process": "adapters.upload.resumable",
    "_validate_resumable_upload_target": "adapters.upload.resumable",
}

LFS_BOUNDARY_DEFINITIONS = {
    "_SlowFlowCoordinator",
    "_ResumableLfsTransferController",
    "_scoped_resumable_lfs_recovery",
    "ResumableUploadModeError",
    "ResumableLfsAttributesError",
    "ResumableLfsPreuploadError",
    "_ResumableLfsAttributesPolicy",
    "_ResumableLfsPreuploadController",
    "_configure_remote_lfs_attributes",
    "_print_resumable_lfs_preupload_event",
    "_print_resumable_slow_flow_event",
}

results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def _class_methods(source, class_name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    return set()


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
    missing = tuple(
        name
        for name in (*UPLOAD_OWNER_MODULES, *UPLOAD_COMPATIBILITY_MODULES)
        if name not in source_texts
    )
    check("all canonical and compatibility upload modules exist", not missing)
    if missing:
        print(f"summary: 0/{len(results)} passed")
        return 1

    api_module = importlib.import_module("atomgit.api")
    upload_service = importlib.import_module("atomgit.adapters.upload.service")
    owner_modules = {
        name: importlib.import_module(f"atomgit.{name}")
        for name in UPLOAD_OWNER_MODULES
        if name != "adapters.upload.__init__"
    }

    check(
        "historical concrete API class and singleton remain at the old path",
        api_module.HuggingFaceAPI.__module__ == "atomgit.compatibility.api"
        and type(api_module.api) is api_module.HuggingFaceAPI,
    )
    check(
        "historical upload methods resolve to the service owner",
        api_module.HuggingFaceAPI.upload_folder
        is upload_service.UploadServiceMixin.upload_folder
        and api_module.HuggingFaceAPI.upload_directory
        is upload_service.UploadServiceMixin.upload_directory,
    )
    check(
        "historical upload method signatures are unchanged",
        str(inspect.signature(api_module.HuggingFaceAPI.upload_folder))
        == "(self, file_path: pathlib.Path, repo_id: str, remote_path: str = None, message: str = None, upload_timeout: Optional[float] = None, progress_bar: bool = True, path_in_repo: str = None, repo_type: str = None, revision: str = None, ignore_patterns=None, num_workers: int = 5) -> bool"
        and str(inspect.signature(api_module.HuggingFaceAPI.upload_directory))
        == "(self, dir_path: pathlib.Path, repo_id: str, message: str = None, progress_callback=None, upload_timeout: Optional[float] = None, progress_bar: bool = True, path_in_repo: str = None, repo_type: str = None, revision: str = None, ignore_patterns=None, resumable: bool = False, num_workers: int = 5, auto_configure_lfs: bool = False, batch_size: int = 20) -> bool",
    )
    check(
        "historical upload helpers remain exact owner identities",
        all(
            getattr(api_module, helper) is getattr(owner_modules[owner], helper)
            for helper, owner in HISTORICAL_HELPER_OWNERS.items()
        ),
    )

    upload_runtime_modules = {
        module
        for name, module in owner_modules.items()
        if name not in {"adapters.upload.contracts", "adapters.upload.__init__"}
    }
    missing_consumers = {}
    for name in api_module._UPLOAD_OWNER_EXPORTS:
        expected = {
            module
            for module in upload_runtime_modules
            if name
            in _loaded_names(source_texts[module.__name__.removeprefix("atomgit.")])
        }
        registered = set(api_module._UPLOAD_PATCH_TARGETS.get(name, ()))
        if not expected <= registered:
            missing_consumers[name] = sorted(
                module.__name__ for module in expected - registered
            )
    check(
        "every moved upload symbol registers all new resolution sites",
        not missing_consumers,
        repr(missing_consumers),
    )

    initial_mismatches = []
    assignment_mismatches = []
    deletion_mismatches = []
    restoration_mismatches = []
    for name, targets in api_module._UPLOAD_PATCH_TARGETS.items():
        original = getattr(api_module, name)
        if any(getattr(target, name, object()) is not original for target in targets):
            initial_mismatches.append(name)

        replacement = object()
        setattr(api_module, name, replacement)
        try:
            if any(
                getattr(target, name, object()) is not replacement for target in targets
            ):
                assignment_mismatches.append(name)
            delattr(api_module, name)
            if hasattr(api_module, name) or any(
                hasattr(target, name) for target in targets
            ):
                deletion_mismatches.append(name)
        finally:
            setattr(api_module, name, original)

        if getattr(api_module, name, object()) is not original or any(
            getattr(target, name, object()) is not original for target in targets
        ):
            restoration_mismatches.append(name)

    check(
        "every registered old upload seam starts with exact shared identity",
        not initial_mismatches,
        repr(initial_mismatches),
    )
    check(
        "assigning every old upload seam reaches all former resolution sites",
        not assignment_mismatches,
        repr(assignment_mismatches),
    )
    check(
        "deleting every old upload seam removes all former resolution sites",
        not deletion_mismatches,
        repr(deletion_mismatches),
    )
    check(
        "restoring every old upload seam restores exact shared identity",
        not restoration_mismatches,
        repr(restoration_mismatches),
    )

    check(
        "the historical API class contains no moved upload method definitions",
        not (
            _class_methods(source_texts["compatibility.api"], "HuggingFaceAPI")
            & {"upload_folder", "upload_directory"}
        ),
    )
    check(
        "canonical upload modules have adapter ownership and old paths are compatibility",
        all(
            PRODUCTION_MODULE_OWNERS[name] == "adapters"
            for name in UPLOAD_OWNER_MODULES
        )
        and all(
            PRODUCTION_MODULE_OWNERS[name] == "compatibility"
            for name in UPLOAD_COMPATIBILITY_MODULES
        ),
    )
    check(
        "the API facade debt ceiling tightens with moved implementation",
        LEGACY_FACADE_DEBT["compatibility.api"]["max_lines"] < 3715
        and LEGACY_FACADE_DEBT["compatibility.api"]["max_functions"] < 60
        and LEGACY_FACADE_DEBT["compatibility.api"]["max_classes"] < 17,
    )

    placeholder = dict(source_texts)
    placeholder["adapters.upload.resumable"] = '"""Placeholder."""\npass\n'
    errors = validate_structure(placeholder)
    check(
        "an upload placeholder replacement fails closed",
        any("empty placeholder" in error for error in errors),
        repr(errors),
    )
    unowned = dict(source_texts)
    unowned["adapters.upload.future"] = "VALUE = 1\n"
    errors = validate_structure(unowned)
    check(
        "an unowned upload implementation fails closed",
        any(
            "adapters.upload.future" in error and "unowned" in error for error in errors
        ),
        repr(errors),
    )

    lfs_definitions = _top_level_definitions(source_texts["adapters.lfs.service"])
    upload_definitions = set().union(
        *(_top_level_definitions(source_texts[name]) for name in UPLOAD_OWNER_MODULES)
    )
    sdk_upload_definitions = _top_level_definitions(
        source_texts["adapters.sdk_uploads"]
    )
    check(
        "LFS and SDK ownership remain outside the upload package",
        LFS_BOUNDARY_DEFINITIONS <= lfs_definitions
        and not (LFS_BOUNDARY_DEFINITIONS & upload_definitions)
        and "upload_folder" in sdk_upload_definitions
        and "upload_folder" not in upload_definitions,
    )
    check(
        "historical upload paths contain no business definitions or dependency calls",
        all(
            not _top_level_definitions(source_texts[name])
            and "huggingface_hub" not in source_texts[name]
            for name in UPLOAD_COMPATIBILITY_MODULES
        ),
    )

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
