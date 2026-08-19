#!/usr/bin/env python3
"""Lock LFS ownership behind the historical API compatibility path."""

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
    PRODUCTION_MODULE_OWNERS,
    discover_source_texts,
    validate_structure,
)

LFS_MODULES = ("lfs.__init__", "lfs.service")
LFS_DEFINITIONS = {
    "_slow_flow_stable_baseline",
    "_slow_flow_peer_baseline",
    "_SlowFlowDecision",
    "_SlowFlowState",
    "_SlowFlowCoordinator",
    "_SlowFlowReconnect",
    "_SlowFlowPayload",
    "_lfs_source_identity",
    "_lfs_object_key",
    "_ResumableLfsTransferController",
    "_scoped_resumable_lfs_recovery",
    "_validated_lfs_patterns",
    "_lfs_pattern_from_repo_path",
    "_unsafe_resumable_lfs_patterns",
    "_resumable_lfs_patterns",
    "ResumableUploadModeError",
    "ResumableLfsAttributesError",
    "ResumableLfsPreuploadError",
    "_ResumableLfsAttributesPolicy",
    "_validate_resumable_commit_operations",
    "_validate_resumable_upload_mode_items",
    "_refresh_unsafe_resumable_upload_modes",
    "_resumable_projection_lfs_patterns",
    "_lfs_config_cache_root",
    "_lfs_gitattributes_line",
    "_merge_lfs_gitattributes",
    "_gitattributes_contains_lfs_patterns",
    "_remote_revision_commit_sha",
    "_download_remote_gitattributes",
    "_configure_remote_lfs_attributes",
    "_bounded_lfs_retry_after",
    "_bounded_lfs_error_payload",
    "_is_atomgit_lfs_quota_error",
    "_lfs_preupload_error_category",
    "_ResumableLfsPreuploadController",
    "_print_resumable_lfs_preupload_event",
    "_print_resumable_slow_flow_event",
}


def _top_level_definitions(source):
    return {
        node.name
        for node in ast.parse(source).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def main():
    results = []

    def check(name, condition, detail=""):
        results.append(bool(condition))
        label = "PASS" if condition else "FAIL"
        suffix = f" -> {detail}" if detail and not condition else ""
        print(f"[{label}] {name}{suffix}")

    source_texts = discover_source_texts(REPOSITORY_ROOT)
    missing = tuple(name for name in LFS_MODULES if name not in source_texts)
    check(
        "all LFS owner modules contain real implementation", not missing, repr(missing)
    )
    if missing:
        print(f"summary: {sum(results)}/{len(results)} passed")
        return 1

    api_module = sys.modules.get("atomgit.api") or importlib.import_module(
        "atomgit.api"
    )
    lfs_service = importlib.import_module("atomgit.lfs.service")
    check(
        "historical API class and singleton remain concrete and unchanged",
        api_module.HuggingFaceAPI.__module__ == "atomgit.api"
        and type(api_module.api) is api_module.HuggingFaceAPI,
    )
    check(
        "every moved LFS definition has the exact service owner",
        all(
            getattr(api_module, name) is getattr(lfs_service, name)
            for name in api_module._LFS_OWNER_EXPORTS
        ),
    )
    check(
        "representative LFS signatures remain unchanged",
        str(inspect.signature(lfs_service._configure_remote_lfs_attributes))
        == "(*, token: str, repo_id: str, repo_type: str, revision: str, patterns, request_timeout: float) -> dict"
        and str(inspect.signature(lfs_service._scoped_resumable_lfs_recovery))
        == "(coordinator: atomgit.lfs.service._SlowFlowCoordinator)",
    )

    initial_mismatches = []
    assignment_mismatches = []
    deletion_mismatches = []
    restoration_mismatches = []
    for name, targets in api_module._LFS_PATCH_TARGETS.items():
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
        "LFS seams start with exact shared identity",
        not initial_mismatches,
        repr(initial_mismatches),
    )
    check(
        "assigning an old LFS seam reaches every consumer",
        not assignment_mismatches,
        repr(assignment_mismatches),
    )
    check(
        "deleting an old LFS seam removes every consumer",
        not deletion_mismatches,
        repr(deletion_mismatches),
    )
    check(
        "restoring an old LFS seam restores exact identity",
        not restoration_mismatches,
        repr(restoration_mismatches),
    )

    api_definitions = _top_level_definitions(source_texts["api.__init__"])
    lfs_definitions = _top_level_definitions(source_texts["lfs.service"])
    upload_definitions = set().union(
        *(
            _top_level_definitions(source_texts[name])
            for name in source_texts
            if name.startswith("upload.")
        )
    )
    check(
        "all moved definitions live in the LFS service",
        LFS_DEFINITIONS <= lfs_definitions and not (LFS_DEFINITIONS & api_definitions),
    )
    check(
        "upload modules do not regain LFS implementation",
        not (LFS_DEFINITIONS & upload_definitions),
    )
    check(
        "LFS modules have exact domain ownership",
        all(
            PRODUCTION_MODULE_OWNERS[name.removeprefix("atomgit.")] == "lfs"
            for name in LFS_MODULES
        ),
    )
    errors = validate_structure(source_texts)
    check("structure contract accepts the LFS domain", not errors, repr(errors))
    check(
        "SDK implementation remains outside the LFS domain",
        "upload_folder" in _top_level_definitions(source_texts["sdk.uploads"])
        and "upload_folder" not in lfs_definitions,
    )

    passed = sum(results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
