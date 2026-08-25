"""Historical utility import facade with cross-owner patch forwarding."""

# ruff: noqa: F401

import os
import subprocess
import sys
import types

from atomgit.infrastructure import cache as _cache
from atomgit.infrastructure import filesystem as _filesystem
from atomgit.infrastructure import git_credentials as _git_credentials
from atomgit.infrastructure import output as _output
from atomgit.infrastructure import utils as _implementation
from atomgit.infrastructure import validation as _validation
from atomgit.infrastructure.utils import *  # noqa: F401,F403

_GIT_CREDENTIAL_HOSTS = _git_credentials._GIT_CREDENTIAL_HOSTS
_GIT_HELPER_STATE_VERSION = _git_credentials._GIT_HELPER_STATE_VERSION
_GIT_HELPER_STATE_FILENAME = _git_credentials._GIT_HELPER_STATE_FILENAME
_git_helper_key = _git_credentials._git_helper_key
_git_helper_command = _git_credentials._git_helper_command
_get_global_git_values = _git_credentials._get_global_git_values
_set_global_git_values = _git_credentials._set_global_git_values
_restore_global_git_values = _git_credentials._restore_global_git_values
_write_bytes_atomic = _git_credentials._write_bytes_atomic
_write_helper_state = _git_credentials._write_helper_state
_load_helper_state = _git_credentials._load_helper_state
_legacy_cleanup_values = _git_credentials._legacy_cleanup_values
_structured_http_status = _validation._structured_http_status
_repo_id_parts = _validation._repo_id_parts
_is_resumable_metadata = _filesystem._is_resumable_metadata
_AUTH_STATUS_PATTERNS = _validation._AUTH_STATUS_PATTERNS
_REPO_ID_ERROR = _validation._REPO_ID_ERROR
_REPO_SEGMENT_CHARS = _validation._REPO_SEGMENT_CHARS


_PATCH_TARGETS = {
    "os": (_validation, _filesystem, _cache, _git_credentials),
    "subprocess": (_git_credentials,),
    **{
        name: (_validation, _implementation)
        for name in (
            "DEFAULT_CLI_UPLOAD_IGNORE_PATTERNS",
            "auth_error_kind",
            "effective_cli_upload_ignore_patterns",
            "is_auth_error",
            "is_macos_metadata_file",
            "is_retryable_download_error",
            "is_supported_upload_revision",
            "normalize_path_in_repo",
            "normalize_repo_id",
            "parse_ignore_patterns",
            "run_download_with_retry",
            "sanitized_download_error",
            "validate_repo_name",
            "validate_repo_type",
            "validate_upload_path_no_symlinks",
            "_AUTH_STATUS_PATTERNS",
            "_REPO_ID_ERROR",
            "_REPO_SEGMENT_CHARS",
            "_repo_id_parts",
            "_structured_http_status",
        )
    },
    **{
        name: (_filesystem, _implementation)
        for name in (
            "count_files_in_directory",
            "ensure_directory",
            "format_file_size",
            "get_directory_size",
            "get_file_size",
            "get_relative_path",
            "get_upload_file_stats",
            "is_valid_path",
            "_is_resumable_metadata",
        )
    },
    **{name: (_cache, _implementation) for name in ("clear_atomgit_cache",)},
    **{
        name: (_output, _implementation)
        for name in ("confirm_action", "print_info", "print_warning")
    },
    **{
        name: (_output, _git_credentials, _implementation)
        for name in ("print_error", "print_success")
    },
    **{
        name: (_git_credentials, _implementation)
        for name in (
            "check_git_available",
            "clear_git_credentials",
            "get_atomgit_git_helper_status",
            "get_git_user_info",
            "setup_git_credentials",
            "_GIT_CREDENTIAL_HOSTS",
            "_GIT_HELPER_STATE_VERSION",
            "_GIT_HELPER_STATE_FILENAME",
            "_git_helper_key",
            "_git_helper_command",
            "_get_global_git_values",
            "_set_global_git_values",
            "_restore_global_git_values",
            "_write_bytes_atomic",
            "_write_helper_state",
            "_load_helper_state",
            "_legacy_cleanup_values",
        )
    },
}

_FacadeModule = type(
    "_FacadeModule",
    (types.ModuleType,),
    {
        "__setattr__": _implementation._forward_legacy_patch,
        "__delattr__": _implementation._delete_legacy_patch,
    },
)
sys.modules[__name__].__class__ = _FacadeModule
