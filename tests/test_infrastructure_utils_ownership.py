#!/usr/bin/env python3
"""Fail closed on infrastructure ownership and historical utility seams."""

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

HISTORICAL_UTILS_DEFINITIONS = (
    "_structured_http_status",
    "auth_error_kind",
    "is_auth_error",
    "is_retryable_download_error",
    "run_download_with_retry",
    "sanitized_download_error",
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "_repo_id_parts",
    "validate_repo_name",
    "validate_repo_type",
    "is_supported_upload_revision",
    "normalize_repo_id",
    "normalize_path_in_repo",
    "parse_ignore_patterns",
    "effective_cli_upload_ignore_patterns",
    "is_macos_metadata_file",
    "validate_upload_path_no_symlinks",
    "get_file_size",
    "format_file_size",
    "_is_resumable_metadata",
    "get_directory_size",
    "count_files_in_directory",
    "get_upload_file_stats",
    "clear_atomgit_cache",
    "confirm_action",
    "is_valid_path",
    "ensure_directory",
    "get_relative_path",
    "_git_helper_key",
    "_git_helper_command",
    "_get_global_git_values",
    "get_atomgit_git_helper_status",
    "_set_global_git_values",
    "_restore_global_git_values",
    "_write_bytes_atomic",
    "_write_helper_state",
    "_load_helper_state",
    "_legacy_cleanup_values",
    "setup_git_credentials",
    "clear_git_credentials",
    "check_git_available",
    "get_git_user_info",
)

results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def main():
    utility = importlib.import_module("atomgit.utils")
    config = importlib.import_module("atomgit.config")
    runtime = importlib.import_module("atomgit.runtime")
    owners = {
        "normalize_repo_id": "atomgit.infrastructure.validation",
        "print_success": "atomgit.infrastructure.output",
        "get_file_size": "atomgit.infrastructure.filesystem",
        "clear_atomgit_cache": "atomgit.infrastructure.cache",
        "setup_git_credentials": "atomgit.infrastructure.git_credentials",
    }
    check(
        "historical utility callables resolve to their exact infrastructure owners",
        all(
            getattr(utility, name).__module__ == owner for name, owner in owners.items()
        ),
        repr({name: getattr(utility, name).__module__ for name in owners}),
    )
    check(
        "historical utility definitions and constants remain available",
        all(hasattr(utility, name) for name in HISTORICAL_UTILS_DEFINITIONS)
        and all(
            hasattr(utility, name)
            for name in (
                "_GIT_CREDENTIAL_HOSTS",
                "_GIT_HELPER_STATE_VERSION",
                "_GIT_HELPER_STATE_FILENAME",
                "DEFAULT_CLI_UPLOAD_IGNORE_PATTERNS",
                "_AUTH_STATUS_PATTERNS",
                "_REPO_ID_ERROR",
                "_REPO_SEGMENT_CHARS",
            )
        ),
    )

    config_owner = importlib.import_module("atomgit.infrastructure.config")
    runtime_owner = importlib.import_module("atomgit.infrastructure.runtime")
    check(
        "historical config preserves the class and shared singleton identities",
        config.Config is config_owner.Config and config.config is config_owner.config,
    )
    check(
        "historical runtime preserves constants and callable identity",
        runtime.configure_hf_environment is runtime_owner.configure_hf_environment
        and runtime.ATOMGIT_HF_ENDPOINT == runtime_owner.ATOMGIT_HF_ENDPOINT,
    )

    validation_owner = importlib.import_module("atomgit.infrastructure.validation")
    original_walk = utility.os.walk
    replacement = object()
    utility.os.walk = replacement
    try:
        check(
            "patching historical utility os.walk reaches validation owner",
            validation_owner.os.walk is replacement,
        )
    finally:
        utility.os.walk = original_walk

    git_owner = importlib.import_module("atomgit.infrastructure.git_credentials")
    original_run = utility.subprocess.run
    replacement = object()
    utility.subprocess.run = replacement
    try:
        check(
            "patching historical utility subprocess reaches Git owner",
            git_owner.subprocess.run is replacement,
        )
    finally:
        utility.subprocess.run = original_run

    with patch.object(utility, "print_error", lambda message: message):
        check(
            "patching historical utility output reaches Git owner",
            git_owner.print_error is utility.print_error,
        )
    with patch.object(utility, "_get_global_git_values", lambda key: []):
        check(
            "patching historical private Git helper reaches owner",
            git_owner._get_global_git_values is utility._get_global_git_values,
        )
    original_os = utility.os
    replacement_os = object()
    with patch.object(utility, "os", replacement_os):
        check(
            "patching historical utility os module reaches owners",
            validation_owner.os is replacement_os
            and importlib.import_module("atomgit.infrastructure.filesystem").os
            is replacement_os,
        )
    check("historical utility os module is restored", utility.os is original_os)

    check(
        "historical private Git helpers retain owner identity",
        utility._git_helper_command is git_owner._git_helper_command
        and utility._legacy_cleanup_values is git_owner._legacy_cleanup_values,
    )

    source_texts = discover_source_texts(REPOSITORY_ROOT)
    check(
        "every delivered nested module has exact infrastructure ownership",
        all(
            PRODUCTION_MODULE_OWNERS[name] == "infrastructure"
            for name in source_texts
            if name.startswith("infrastructure.")
        ),
    )
    check(
        "historical facades contain no owned functions or classes",
        all(
            LEGACY_FACADE_DEBT[name]["max_functions"] == 0
            and LEGACY_FACADE_DEBT[name]["max_classes"] == 0
            for name in ("config", "runtime", "utils")
        ),
    )

    regrown = dict(source_texts)
    regrown["utils"] += "\n\ndef future_utility_behavior():\n    return None\n"
    errors = validate_structure(regrown)
    check(
        "historical utility facade regrowth fails closed",
        any(
            "legacy facade debt contract is stale in utils" in error for error in errors
        ),
        repr(errors),
    )

    unowned = dict(source_texts)
    unowned["infrastructure.future"] = "VALUE = 1\n"
    errors = validate_structure(unowned)
    check(
        "an unowned infrastructure implementation fails closed",
        any(
            "infrastructure.future" in error and "unowned" in error for error in errors
        ),
        repr(errors),
    )

    placeholder = dict(source_texts)
    placeholder["infrastructure.cache"] = '"""Placeholder."""\npass\n'
    errors = validate_structure(placeholder)
    check(
        "an infrastructure placeholder fails closed",
        any("empty placeholder" in error for error in errors),
        repr(errors),
    )

    signature_errors = []
    for name in owners:
        if inspect.signature(getattr(utility, name)) != inspect.signature(
            getattr(importlib.import_module(owners[name]), name)
        ):
            signature_errors.append(name)
    check(
        "historical utility signatures match their exact owners",
        not signature_errors,
        repr(signature_errors),
    )

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
