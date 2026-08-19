#!/usr/bin/env python3
"""Lock exact download owners behind the historical API compatibility path."""

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

DOWNLOAD_MODULES = (
    "download.__init__",
    "download.integrity",
    "download.manifest",
    "download.prune",
    "download.resume",
    "download.service",
    "download.transport",
)

HISTORICAL_HELPER_OWNERS = {
    "_atomgit_hf_endpoint": "download.transport",
    "_atomgit_resolve_url": "download.transport",
    "_atomgit_file_checksum": "download.integrity",
    "_verify_download_checksum": "download.integrity",
    "_download_manifest_path": "download.manifest",
    "_download_manifest_lock": "download.manifest",
    "_safe_download_destination": "download.service",
    "_prune_managed_download_files": "download.prune",
    "_atomgit_download_raw": "download.transport",
    "_download_atomgit_file": "download.transport",
    "_download_atomgit_file_resumable": "download.resume",
    "_atomgit_list_repo_files": "download.service",
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


def main():
    results.clear()
    source_texts = discover_source_texts(REPOSITORY_ROOT)
    missing = tuple(name for name in DOWNLOAD_MODULES if name not in source_texts)
    check(
        "all approved download owner modules contain real implementation", not missing
    )
    if missing:
        print(f"summary: 0/{len(results)} passed")
        return 1

    api_module = importlib.import_module("atomgit.api")
    download_service = importlib.import_module("atomgit.download.service")
    owner_modules = {
        name: importlib.import_module(f"atomgit.{name}")
        for name in DOWNLOAD_MODULES
        if name != "download.__init__"
    }

    check(
        "historical concrete API class and singleton remain at the old path",
        api_module.HuggingFaceAPI.__module__ == "atomgit.api"
        and type(api_module.api) is api_module.HuggingFaceAPI,
    )
    check(
        "historical download methods resolve to the service owner",
        api_module.HuggingFaceAPI.download_repo
        is download_service.DownloadServiceMixin.download_repo
        and api_module.HuggingFaceAPI.download_file
        is download_service.DownloadServiceMixin.download_file,
    )
    check(
        "historical download method signatures are unchanged",
        str(inspect.signature(api_module.HuggingFaceAPI.download_repo))
        == "(self, repo_id: str, local_path: pathlib.Path = None, force_download: bool = False, repo_type: str = None, verify_checksum: bool = False, resume_download: bool = False, prune: bool = False) -> bool"
        and str(inspect.signature(api_module.HuggingFaceAPI.download_file))
        == "(self, repo_id: str, filename: str, local_path: pathlib.Path = None, force_download: bool = False, repo_type: str = None, verify_checksum: bool = False, resume_download: bool = False) -> bool",
    )
    check(
        "historical download helpers remain exact owner identities",
        all(
            getattr(api_module, helper) is getattr(owner_modules[owner], helper)
            for helper, owner in HISTORICAL_HELPER_OWNERS.items()
        ),
    )

    initial_mismatches = []
    assignment_mismatches = []
    deletion_mismatches = []
    restoration_mismatches = []
    for name, targets in api_module._DOWNLOAD_PATCH_TARGETS.items():
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
        "every registered old download seam starts with exact shared identity",
        not initial_mismatches,
        repr(initial_mismatches),
    )
    check(
        "assigning every old download seam reaches all former resolution sites",
        not assignment_mismatches,
        repr(assignment_mismatches),
    )
    check(
        "deleting every old download seam removes all former resolution sites",
        not deletion_mismatches,
        repr(deletion_mismatches),
    )
    check(
        "restoring every old download seam restores exact shared identity",
        not restoration_mismatches,
        repr(restoration_mismatches),
    )

    check(
        "the historical API class contains no moved download method definitions",
        not (
            _class_methods(source_texts["api"], "HuggingFaceAPI")
            & {"download_repo", "download_file"}
        ),
    )
    check(
        "every nested download module has exact transfer ownership",
        all(PRODUCTION_MODULE_OWNERS[name] == "transfers" for name in DOWNLOAD_MODULES),
    )
    check(
        "the API facade debt ceiling tightens with moved implementation",
        LEGACY_FACADE_DEBT["api"]["max_lines"] < 5074
        and LEGACY_FACADE_DEBT["api"]["max_functions"] < 110
        and LEGACY_FACADE_DEBT["api"]["max_classes"] < 21,
    )

    placeholder = dict(source_texts)
    placeholder["download.transport"] = '"""Placeholder."""\npass\n'
    errors = validate_structure(placeholder)
    check(
        "a download placeholder replacement fails closed",
        any("empty placeholder" in error for error in errors),
        repr(errors),
    )
    unowned = dict(source_texts)
    unowned["download.future"] = "VALUE = 1\n"
    errors = validate_structure(unowned)
    check(
        "an unowned download implementation fails closed",
        any("download.future" in error and "unowned" in error for error in errors),
        repr(errors),
    )

    sdk_download_source = source_texts["sdk.downloads"]
    download_definitions = set().union(
        *(_top_level_definitions(source_texts[name]) for name in DOWNLOAD_MODULES)
    )
    lfs_source = source_texts["lfs.service"]
    check(
        "SDK download and LFS helpers remain outside the download package",
        {"snapshot_download", "download_file"}
        <= _top_level_definitions(sdk_download_source)
        and not ({"snapshot_download", "download_file"} & download_definitions)
        and "def _download_remote_gitattributes(" in lfs_source,
    )

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
