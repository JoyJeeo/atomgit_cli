#!/usr/bin/env python3
"""Fail closed on service ownership and historical API seams."""

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
    PRODUCTION_MODULE_OWNERS,
    discover_source_texts,
    validate_structure,
)

SERVICE_MODULES = (
    "services.__init__",
    "services.authentication",
    "services.repositories",
)
AUTHENTICATION_METHODS = (
    "login",
    "_get_login_user_by_token",
    "get_login_user",
)
REPOSITORY_METHODS = (
    "_normalize_repo_id",
    "list_repos",
    "set_repo_visibility",
    "delete_repo",
    "create_branch",
    "create_repo",
    "get_repo_info",
)
HISTORICAL_SERVICE_HELPERS = (
    "_atomgit_repo_type",
    "_atomgit_v5_request_json",
    "_atomgit_v5_get_json",
    "_atomgit_v5_repo_path",
    "_repo_private_state",
    "_sanitized_v5_api_error",
    "_is_definitive_v5_write_error",
    "_atomgit_v5_commit_sha",
    "_atomgit_v5_branch_commit_id",
    "_atomgit_repo_exists",
    "_classify_create_repo_error",
)

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


def main():
    results.clear()
    source_texts = discover_source_texts(REPOSITORY_ROOT)
    missing = tuple(name for name in SERVICE_MODULES if name not in source_texts)
    check("all approved service owner modules contain real implementation", not missing)
    if missing:
        print(f"summary: 0/{len(results)} passed")
        return 1

    api_module = importlib.import_module("atomgit.api")
    authentication = importlib.import_module("atomgit.services.authentication")
    repositories = importlib.import_module("atomgit.services.repositories")

    check(
        "historical concrete API class and singleton remain at the old path",
        api_module.HuggingFaceAPI.__module__ == "atomgit.api"
        and type(api_module.api) is api_module.HuggingFaceAPI,
    )
    check(
        "historical authentication methods resolve to exact service owners",
        all(
            getattr(api_module.HuggingFaceAPI, name)
            is getattr(authentication.AuthenticationServiceMixin, name)
            for name in AUTHENTICATION_METHODS
        ),
    )
    check(
        "historical repository methods resolve to exact service owners",
        all(
            getattr(api_module.HuggingFaceAPI, name)
            is getattr(repositories.RepositoryServiceMixin, name)
            for name in REPOSITORY_METHODS
        ),
    )
    check(
        "historical service helpers remain exact owner identities",
        all(
            getattr(api_module, name) is getattr(repositories, name)
            for name in HISTORICAL_SERVICE_HELPERS
        )
        and authentication._sanitized_v5_api_error
        is repositories._sanitized_v5_api_error,
    )
    check(
        "historical moved method signatures are unchanged",
        str(inspect.signature(api_module.HuggingFaceAPI.login))
        == "(self, token: str) -> bool"
        and str(inspect.signature(api_module.HuggingFaceAPI.create_repo))
        == "(self, repo_name: str, repo_type: str = 'model', private: bool = False, exist_ok: bool = False) -> bool"
        and str(inspect.signature(api_module.HuggingFaceAPI.get_repo_info))
        == "(self, repo_id: str) -> Optional[Dict[str, Any]]",
    )

    replacement = object()
    with patch.object(api_module, "_atomgit_open_url", replacement):
        check(
            "patching the old V5 opener reaches the repository owner",
            repositories._atomgit_open_url is replacement,
        )
    with patch.object(api_module, "_atomgit_v5_get_json", replacement):
        check(
            "patching the old V5 reader reaches service and transfer call sites",
            repositories._atomgit_v5_get_json is replacement
            and api_module._atomgit_v5_get_json is replacement,
        )
    with patch.object(api_module, "_is_not_found_error", replacement):
        check(
            "patching the old not-found policy reaches repository probing",
            repositories._is_not_found_error is replacement,
        )
    with patch.object(api_module, "create_repo", replacement):
        check(
            "patching the old HF create dependency reaches its service owner",
            repositories.create_repo is replacement,
        )
    with patch.object(api_module, "urllib", replacement):
        check(
            "patching the old urllib module reaches both service owners",
            authentication.urllib is replacement and repositories.urllib is replacement,
        )
    with patch.object(api_module, "json", replacement):
        check(
            "patching the old json module reaches both service owners",
            authentication.json is replacement and repositories.json is replacement,
        )
    original_v5_reader = api_module._atomgit_v5_get_json
    del api_module._atomgit_v5_get_json
    try:
        check(
            "deleting an old private helper removes the owner seam",
            not hasattr(repositories, "_atomgit_v5_get_json"),
        )
    finally:
        api_module._atomgit_v5_get_json = original_v5_reader
    check(
        "restoring an old private helper restores the exact owner identity",
        api_module._atomgit_v5_get_json
        is repositories._atomgit_v5_get_json
        is original_v5_reader,
    )

    moved_methods = set(AUTHENTICATION_METHODS) | set(REPOSITORY_METHODS)
    check(
        "the historical API class contains no moved method definitions",
        not (
            _class_methods(source_texts["api.__init__"], "HuggingFaceAPI")
            & moved_methods
        ),
    )
    check(
        "every nested services module has exact services ownership",
        all(PRODUCTION_MODULE_OWNERS[name] == "services" for name in SERVICE_MODULES),
    )
    check(
        "the API facade debt ceiling tightens with moved implementation",
        LEGACY_FACADE_DEBT["api.__init__"]["max_lines"] < 5496
        and LEGACY_FACADE_DEBT["api.__init__"]["max_functions"] < 121
        and LEGACY_FACADE_DEBT["api.__init__"]["max_classes"] <= 21,
    )

    placeholder = dict(source_texts)
    placeholder["services.authentication"] = '"""Placeholder."""\npass\n'
    errors = validate_structure(placeholder)
    check(
        "a service placeholder replacement fails closed",
        any("empty placeholder" in error for error in errors),
        repr(errors),
    )
    unowned = dict(source_texts)
    unowned["services.future"] = "VALUE = 1\n"
    errors = validate_structure(unowned)
    check(
        "an unowned service implementation fails closed",
        any("services.future" in error and "unowned" in error for error in errors),
        repr(errors),
    )

    transfer_definitions = {"upload_folder", "upload_directory"}
    check(
        "upload methods remain outside repository service ownership",
        not (
            _class_methods(source_texts["api.__init__"], "HuggingFaceAPI")
            & transfer_definitions
        )
        and transfer_definitions
        <= _class_methods(source_texts["upload.service"], "UploadServiceMixin")
        and not any(
            transfer_definitions
            & _class_methods(source_texts[name], "RepositoryServiceMixin")
            for name in ("services.authentication", "services.repositories")
        ),
    )

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
