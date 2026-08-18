"""Internal aggregation surface for infrastructure utility owners."""

# ruff: noqa: F401

import types

from .cache import clear_atomgit_cache
from .filesystem import (
    count_files_in_directory,
    ensure_directory,
    format_file_size,
    get_directory_size,
    get_file_size,
    get_relative_path,
    get_upload_file_stats,
    is_valid_path,
)
from .git_credentials import (
    check_git_available,
    clear_git_credentials,
    get_atomgit_git_helper_status,
    get_git_user_info,
    setup_git_credentials,
)
from .output import (
    confirm_action,
    print_error,
    print_info,
    print_success,
    print_warning,
)
from .validation import (
    DEFAULT_CLI_UPLOAD_IGNORE_PATTERNS,
    auth_error_kind,
    effective_cli_upload_ignore_patterns,
    is_auth_error,
    is_macos_metadata_file,
    is_retryable_download_error,
    is_supported_upload_revision,
    normalize_path_in_repo,
    normalize_repo_id,
    parse_ignore_patterns,
    run_download_with_retry,
    sanitized_download_error,
    validate_repo_name,
    validate_repo_type,
    validate_upload_path_no_symlinks,
)


def _forward_legacy_patch(module, name, value):
    for target in module._PATCH_TARGETS.get(name, ()):
        setattr(target, name, value)
    types.ModuleType.__setattr__(module, name, value)


def _delete_legacy_patch(module, name):
    for target in module._PATCH_TARGETS.get(name, ()):
        if hasattr(target, name):
            delattr(target, name)
    types.ModuleType.__delattr__(module, name)


__all__ = tuple(name for name in globals() if not name.startswith("_"))
