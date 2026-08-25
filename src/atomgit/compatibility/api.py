"""Historical API compatibility assembly and patch surface."""

# ruff: noqa: F401 -- historical dependency and monkeypatch surface
import errno  # noqa: F401 -- historical upload patch surface
import hashlib  # noqa: F401 -- historical transfer patch surface
import json
import math
import multiprocessing  # noqa: F401 -- historical upload patch surface
import ntpath  # noqa: F401
import os
import random
import shutil  # noqa: F401 -- historical transfer patch surface
import socket
import ssl  # noqa: F401
import stat  # noqa: F401 -- historical upload patch surface
import sys
import tempfile
import threading
import time
import types
import urllib.error
import urllib.request
from contextlib import ExitStack, contextmanager  # noqa: F401
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path, PurePosixPath, PureWindowsPath  # noqa: F401
from statistics import median
from typing import List, Optional, Set  # noqa: F401
from urllib.parse import quote, urljoin, urlsplit  # noqa: F401

import httpx

try:
    from ..runtime import configure_hf_environment
except ImportError:
    from runtime import configure_hf_environment

configure_hf_environment()

# isort: off -- runtime policy must precede all Hugging Face imports.
try:
    from ..cli_contracts import (  # noqa: F401
        _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
        DEFAULT_UPLOAD_BATCH_SIZE,
    )
except ImportError:
    from cli_contracts import (  # noqa: F401
        _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
        DEFAULT_UPLOAD_BATCH_SIZE,
    )

import huggingface_hub._upload_large_folder as hf_large_folder  # noqa: E402,F401
import huggingface_hub.lfs as hf_lfs  # noqa: E402
from huggingface_hub import HfApi  # noqa: E402
from huggingface_hub import close_session as close_hf_session  # noqa: E402,F401
from huggingface_hub import constants as hf_constants  # noqa: E402,F401
from huggingface_hub import (  # noqa: E402,F401
    create_repo,
    get_hf_file_metadata,
    hf_hub_download,
    snapshot_download,
    upload_folder,
)
from huggingface_hub._local_folder import (  # noqa: E402
    get_local_upload_paths,
    read_upload_metadata,
)
from huggingface_hub.file_download import http_get as hf_http_get  # noqa: E402,F401

try:
    from ..adapters.download import integrity as _download_integrity
    from ..adapters.download import manifest as _download_manifest
    from ..adapters.download import prune as _download_prune
    from ..adapters.download import resume as _download_resume
    from ..adapters.download import service as _download_service
    from ..adapters.download import transport as _download_transport
    from ..adapters.lfs import service as _lfs_service
    from ..adapters.lfs.pointer import (  # noqa: F401
        CanonicalLfsPointerError,
        canonical_lfs_payloads,
        run_canonical_lfs_upload,
        verify_canonical_lfs_pointers,
    )
    from ..adapters.lfs.service import _SlowFlowCoordinator as _LFS_SERVICE_IMPORT
    from ..compatibility import authentication as _authentication_service
    from ..compatibility import repositories as _repository_service
    from ..compatibility.authentication import (  # noqa: F401
        _ATOMGIT_IDENTITY_MAX_JSON_BYTES,
        AuthenticationServiceMixin,
    )
    from ..compatibility.download import DownloadServiceMixin
    from ..compatibility.facade import _delete_legacy_patch, _forward_legacy_patch
    from ..compatibility.repositories import (  # noqa: F401
        _ATOMGIT_V5_API_BASE,
        _ATOMGIT_V5_MAX_JSON_BYTES,
        RepositoryServiceMixin,
        _atomgit_repo_exists,
        _atomgit_repo_type,
        _atomgit_v5_branch_commit_id,
        _atomgit_v5_commit_sha,
        _atomgit_v5_get_json,
        _atomgit_v5_repo_path,
        _atomgit_v5_request_json,
        _classify_create_repo_error,
        _is_definitive_v5_write_error,
        _repo_private_state,
        _sanitized_v5_api_error,
    )
    from ..config import config  # noqa: F401
    from ..utils import (  # noqa: F401
        auth_error_kind,
        is_auth_error,
        is_supported_upload_revision,
        normalize_path_in_repo,
        normalize_repo_id,
        parse_ignore_patterns,
        run_download_with_retry,
        sanitized_download_error,
        validate_upload_path_no_symlinks,
    )
except ImportError:
    from adapters.download import integrity as _download_integrity
    from adapters.download import manifest as _download_manifest
    from adapters.download import prune as _download_prune
    from adapters.download import resume as _download_resume
    from adapters.download import service as _download_service
    from adapters.download import transport as _download_transport
    from adapters.lfs import service as _lfs_service
    from adapters.lfs.pointer import (  # noqa: F401
        CanonicalLfsPointerError,
        canonical_lfs_payloads,
        run_canonical_lfs_upload,
        verify_canonical_lfs_pointers,
    )
    from adapters.lfs.service import _SlowFlowCoordinator as _LFS_SERVICE_IMPORT
    from compatibility import authentication as _authentication_service
    from compatibility import repositories as _repository_service
    from compatibility.authentication import (  # noqa: F401
        _ATOMGIT_IDENTITY_MAX_JSON_BYTES,
        AuthenticationServiceMixin,
    )
    from compatibility.download import DownloadServiceMixin
    from compatibility.facade import _delete_legacy_patch, _forward_legacy_patch
    from compatibility.repositories import (  # noqa: F401
        _ATOMGIT_V5_API_BASE,
        _ATOMGIT_V5_MAX_JSON_BYTES,
        RepositoryServiceMixin,
        _atomgit_repo_exists,
        _atomgit_repo_type,
        _atomgit_v5_branch_commit_id,
        _atomgit_v5_commit_sha,
        _atomgit_v5_get_json,
        _atomgit_v5_repo_path,
        _atomgit_v5_request_json,
        _classify_create_repo_error,
        _is_definitive_v5_write_error,
        _repo_private_state,
        _sanitized_v5_api_error,
    )
    from config import config  # noqa: F401
    from utils import (  # noqa: F401
        auth_error_kind,
        is_auth_error,
        is_supported_upload_revision,
        normalize_path_in_repo,
        normalize_repo_id,
        parse_ignore_patterns,
        run_download_with_retry,
        sanitized_download_error,
        validate_upload_path_no_symlinks,
    )

_v5_adapter = _repository_service._v5_adapter

_DOWNLOAD_OWNER_EXPORTS = {
    "_atomgit_hf_endpoint": _download_transport,
    "_atomgit_resolve_url": _download_transport,
    "DownloadChecksumMismatchError": _download_integrity,
    "DownloadChecksumMetadataError": _download_integrity,
    "_atomgit_file_checksum": _download_integrity,
    "_checksum_from_hf_metadata": _download_integrity,
    "_checksum_from_metadata_values": _download_integrity,
    "_atomgit_file_download_metadata": _download_integrity,
    "_verify_download_checksum": _download_integrity,
    "_resume_cache_root": _download_resume,
    "_DOWNLOAD_MANIFEST_VERSION": _download_manifest,
    "_DOWNLOAD_MANIFEST_MAX_BYTES": _download_manifest,
    "_set_private_file_mode": _download_manifest,
    "_download_manifest_root": _download_manifest,
    "_download_manifest_path": _download_manifest,
    "_load_download_manifest": _download_manifest,
    "_write_download_manifest": _download_manifest,
    "_windows_file_lock_module": _download_manifest,
    "_try_lock_download_manifest_descriptor_windows": _download_manifest,
    "_unlock_download_manifest_descriptor_windows": _download_manifest,
    "_try_lock_download_manifest_descriptor": _download_manifest,
    "_unlock_download_manifest_descriptor": _download_manifest,
    "_download_manifest_lock": _download_manifest,
    "_resume_cache_identity": _download_resume,
    "_process_is_running": _download_resume,
    "_resume_download_lock": _download_resume,
    "_copy_resumed_file_to_destination": _download_resume,
    "_parse_content_range": _download_resume,
    "_atomgit_resume_raw": _download_resume,
    "_download_atomgit_file_resumable": _download_resume,
    "_atomgit_list_repo_files": _download_service,
    "_repository_filename_parts": _download_prune,
    "_safe_download_destination": _download_service,
    "_WindowsFileAPI": _download_prune,
    "_normalized_windows_handle_path": _download_prune,
    "_prune_managed_download_file_windows": _download_prune,
    "_uses_windows_prune": _download_prune,
    "_prune_managed_download_file": _download_prune,
    "_prune_managed_download_files": _download_prune,
    "_atomgit_resolve_url_raw": _download_transport,
    "_download_url_origin": _download_transport,
    "_prepare_download_redirect": _download_transport,
    "_AtomGitRedirectHandler": _download_transport,
    "_atomgit_open_url": _download_transport,
    "_atomgit_raw_http_request": _download_transport,
    "_atomgit_raw_http_get": _download_transport,
    "_atomgit_raw_http_head": _download_transport,
    "_raw_metadata_size": _download_integrity,
    "_atomgit_file_download_metadata_raw": _download_integrity,
    "_copy_exact_http_body": _download_transport,
    "_read_chunk_line": _download_transport,
    "_copy_chunked_http_body": _download_transport,
    "_copy_framed_http_body": _download_transport,
    "_atomgit_download_raw": _download_transport,
    "_download_atomgit_file": _download_transport,
}
for _download_name, _download_owner in _DOWNLOAD_OWNER_EXPORTS.items():
    globals()[_download_name] = getattr(_download_owner, _download_name)

# These exact aliases are consumed by unextracted upload/LFS code below and
# keep its historical static resolution explicit.
_atomgit_file_checksum = _download_integrity._atomgit_file_checksum
_atomgit_hf_endpoint = _download_transport._atomgit_hf_endpoint
_atomgit_open_url = _download_transport._atomgit_open_url
_atomgit_resolve_url = _download_transport._atomgit_resolve_url

# Shared repository policy remains the historical canonical old-path object.
_is_not_found_error = _repository_service._is_not_found_error
# isort: on

try:
    # 单文件上传专用：直接以 path_or_fileobj 上传，避免本地拷贝
    from huggingface_hub import upload_file as hf_upload_file
except ImportError:  # 老版本兜底
    hf_upload_file = None

try:
    # huggingface_hub >= 0.14 提供的进度条程序化开关
    from huggingface_hub.utils import (
        are_progress_bars_disabled,
        disable_progress_bars,
        enable_progress_bars,
        filter_repo_objects,
    )

    try:
        from huggingface_hub.utils.tqdm import progress_bar_states
    except ImportError:
        progress_bar_states = None
except ImportError:  # 老版本无此 API 时，提供 no-op 回退，保证可用
    progress_bar_states = None

    def are_progress_bars_disabled(*args, **kwargs):
        return False

    def enable_progress_bars(*args, **kwargs):
        pass

    def disable_progress_bars(*args, **kwargs):
        pass

    def filter_repo_objects(items, *, ignore_patterns=None, key=None, **kwargs):
        return items


try:
    from ..adapters.upload import errors as _upload_errors
    from ..adapters.upload import ordinary as _upload_ordinary
    from ..adapters.upload import projection as _upload_projection
    from ..adapters.upload import resumable as _upload_resumable
    from ..adapters.upload import service as _upload_service
    from ..adapters.upload.service import UploadServiceMixin
except ImportError:
    from adapters.upload import errors as _upload_errors
    from adapters.upload import ordinary as _upload_ordinary
    from adapters.upload import projection as _upload_projection
    from adapters.upload import resumable as _upload_resumable
    from adapters.upload import service as _upload_service
    from adapters.upload.service import UploadServiceMixin

_UPLOAD_OWNER_EXPORTS = {
    "_set_progress_bar": _upload_ordinary,
    "_capture_progress_bar_state": _upload_ordinary,
    "_restore_progress_bar_state": _upload_ordinary,
    "_upload_folder_with_workers": _upload_ordinary,
    "_RESUMABLE_WORKER_ERROR_MESSAGES": _upload_errors,
    "ResumableTargetRevisionError": _upload_errors,
    "ResumableWorkerError": _upload_errors,
    "ResumableCommitError": _upload_errors,
    "_resumable_error_chain": _upload_errors,
    "_resumable_error_status": _upload_errors,
    "_resumable_worker_error_category": _upload_errors,
    "_resumable_failure_envelope": _upload_errors,
    "_classify_upload_error": _upload_errors,
    "ResumableProjectionError": _upload_projection,
    "_resumable_projection_cache_root": _upload_projection,
    "_ensure_projection_directory": _upload_projection,
    "_source_projection_files": _upload_projection,
    "_projection_file_is_current": _upload_projection,
    "_is_projection_hf_metadata": _upload_projection,
    "_sync_resumable_projection": _upload_projection,
    "_prepare_resumable_upload_projection": _upload_projection,
    "_collect_resumable_upload_files": _upload_projection,
    "_resumable_committed_file_count": _upload_projection,
    "_RESUMABLE_COMMIT_MAX_ATTEMPTS": _upload_resumable,
    "_RESUMABLE_COMMIT_BACKOFF_BASE": _upload_resumable,
    "_RESUMABLE_COMMIT_BACKOFF_CAP": _upload_resumable,
    "_RESUMABLE_COMMIT_BATCH_SIZES": _upload_resumable,
    "_commit_error_status": _upload_resumable,
    "_commit_retry_after": _upload_resumable,
    "_is_ambiguous_commit_error": _upload_resumable,
    "_is_retryable_commit_error": _upload_resumable,
    "_is_reducible_commit_error": _upload_resumable,
    "_operation_git_sha1": _upload_resumable,
    "_reconcile_resumable_commit_operations": _upload_resumable,
    "_next_resumable_commit_batch_size": _upload_resumable,
    "_mark_resumable_operations_committed": _upload_resumable,
    "_ResumableCommitController": _upload_resumable,
    "_print_resumable_commit_event": _upload_resumable,
    "_run_resumable_upload": _upload_resumable,
    "_print_upload_batch_plan": _upload_resumable,
    "_print_upload_batch_summary": _upload_resumable,
    "_execute_resumable_upload_process": _upload_resumable,
    "_validate_resumable_upload_target": _upload_resumable,
    "_prefix_resumable_ignore_patterns": _upload_resumable,
}
for _upload_name, _upload_owner in _UPLOAD_OWNER_EXPORTS.items():
    globals()[_upload_name] = getattr(_upload_owner, _upload_name)

_UPLOAD_OWNER_CONSUMERS = {
    "_set_progress_bar": (_upload_ordinary, _upload_service),
    "_capture_progress_bar_state": (_upload_ordinary, _upload_service),
    "_restore_progress_bar_state": (_upload_ordinary, _upload_service),
    "_upload_folder_with_workers": (_upload_ordinary, _upload_service),
    "ResumableTargetRevisionError": (_upload_errors, _upload_resumable),
    "ResumableWorkerError": (
        _upload_errors,
        _upload_resumable,
        _upload_service,
    ),
    "ResumableCommitError": (_upload_errors, _upload_resumable),
    "_resumable_failure_envelope": (_upload_errors, _upload_resumable),
    "_classify_upload_error": (_upload_errors, _upload_service),
    "ResumableProjectionError": (_upload_errors, _upload_projection),
    "_prepare_resumable_upload_projection": (
        _upload_projection,
        _upload_service,
    ),
    "_collect_resumable_upload_files": (_upload_projection, _upload_service),
    "_resumable_committed_file_count": (
        _upload_projection,
        _upload_service,
    ),
    "_print_upload_batch_plan": (_upload_resumable, _upload_service),
    "_print_upload_batch_summary": (_upload_resumable, _upload_service),
    "_execute_resumable_upload_process": (_upload_resumable, _upload_service),
    "_validate_resumable_upload_target": (_upload_resumable, _upload_service),
    "_prefix_resumable_ignore_patterns": (_upload_resumable, _upload_service),
}

_LFS_OWNER_EXPORTS = {
    name: _lfs_service
    for name in (
        "_RESUMABLE_LFS_PREUPLOAD_MAX_ATTEMPTS",
        "_RESUMABLE_LFS_PREUPLOAD_BACKOFF_BASE",
        "_RESUMABLE_LFS_PREUPLOAD_WAIT_CAP",
        "_RESUMABLE_LFS_ERROR_BODY_MAX_BYTES",
        "_SLOW_FLOW_SAMPLE_SECONDS",
        "_SLOW_FLOW_WINDOW_SECONDS",
        "_SLOW_FLOW_REQUIRED_WINDOWS",
        "_SLOW_FLOW_MAX_REPLACEMENTS",
        "_SLOW_FLOW_REPLACEMENT_COOLDOWNS",
        "_SLOW_FLOW_STREAM_CHUNK_BYTES",
        "_RESUMABLE_REGULAR_FILE_MAX_BYTES",
        "_RESUMABLE_LFS_PATTERN_MAX_COUNT",
        "_RESUMABLE_LFS_PATTERN_MAX_EXTENSION",
        "_LFS_GITATTRIBUTES_MAX_BYTES",
        "_LFS_GITATTRIBUTES_MAX_ATTEMPTS",
        "_LFS_GITATTRIBUTES_PATH",
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
    )
}
for _lfs_name, _lfs_owner in _LFS_OWNER_EXPORTS.items():
    globals()[_lfs_name] = getattr(_lfs_owner, _lfs_name)

_LFS_PATCH_TARGETS = {
    name: (_lfs_service, _upload_errors, _upload_resumable, _upload_service)
    for name in _LFS_OWNER_EXPORTS
}


class HuggingFaceAPI(
    AuthenticationServiceMixin,
    RepositoryServiceMixin,
    DownloadServiceMixin,
    UploadServiceMixin,
):
    """AtomGit API client with historical identity and owned service methods."""

    def __init__(self):
        pass


_repository_service._atomgit_open_url = _atomgit_open_url
_repository_service._is_not_found_error = _is_not_found_error
_v5_adapter._atomgit_open_url = _atomgit_open_url
_v5_adapter._is_not_found_error = _is_not_found_error
_authentication_service._sanitized_v5_api_error = _sanitized_v5_api_error
_download_service._is_not_found_error = _is_not_found_error
_download_integrity._is_not_found_error = _is_not_found_error
_download_transport._is_not_found_error = _is_not_found_error
_download_integrity._atomgit_open_url = _atomgit_open_url
_download_transport._atomgit_open_url = _atomgit_open_url

_UPLOAD_PATCH_TARGETS = {
    "HfApi": (_upload_ordinary, _upload_resumable),
    "upload_folder": (_upload_ordinary, _upload_service),
    "hf_upload_file": (_upload_service,),
    "are_progress_bars_disabled": (_upload_ordinary,),
    "disable_progress_bars": (_upload_ordinary,),
    "enable_progress_bars": (_upload_ordinary,),
    "progress_bar_states": (_upload_ordinary,),
    "errno": (_upload_errors,),
    "httpx": (_upload_errors, _upload_resumable),
    "socket": (_upload_errors, _upload_resumable),
    "auth_error_kind": (_upload_errors,),
    "CanonicalLfsPointerError": (_upload_errors,),
    "ResumableUploadModeError": (_upload_errors, _upload_resumable),
    "ResumableLfsAttributesError": (_upload_errors, _upload_resumable),
    "ResumableLfsPreuploadError": (_upload_errors,),
    "_validated_lfs_patterns": (_upload_errors, _upload_service),
    "hashlib": (_upload_projection, _upload_resumable),
    "os": (_upload_projection, _upload_resumable),
    "shutil": (_upload_projection, _upload_service),
    "stat": (_upload_projection,),
    "filter_repo_objects": (_upload_projection,),
    "read_upload_metadata": (_upload_projection, _upload_resumable),
    "_atomgit_hf_endpoint": (_upload_projection, _upload_resumable),
    "multiprocessing": (_upload_resumable,),
    "random": (_upload_resumable,),
    "time": (_upload_resumable, _upload_service),
    "urllib": (_upload_resumable,),
    "datetime": (_upload_resumable,),
    "timezone": (_upload_resumable,),
    "parsedate_to_datetime": (_upload_resumable,),
    "quote": (_upload_resumable,),
    "hf_large_folder": (_upload_resumable,),
    "hf_constants": (_upload_resumable, _upload_service),
    "close_hf_session": (_upload_resumable, _upload_service),
    "get_local_upload_paths": (_upload_resumable,),
    "_atomgit_file_checksum": (_upload_resumable,),
    "_atomgit_v5_get_json": (_upload_resumable,),
    "_atomgit_v5_repo_path": (_upload_resumable,),
    "canonical_lfs_payloads": (_upload_resumable,),
    "verify_canonical_lfs_pointers": (_upload_resumable,),
    "_ResumableLfsAttributesPolicy": (_upload_resumable,),
    "_ResumableLfsPreuploadController": (_upload_resumable,),
    "_SlowFlowCoordinator": (_upload_resumable,),
    "_print_resumable_lfs_preupload_event": (_upload_resumable,),
    "_print_resumable_slow_flow_event": (_upload_resumable,),
    "_refresh_unsafe_resumable_upload_modes": (_upload_resumable,),
    "_resumable_projection_lfs_patterns": (_upload_resumable,),
    "_scoped_resumable_lfs_recovery": (_upload_resumable,),
    "_validate_resumable_commit_operations": (_upload_resumable,),
    "_validate_resumable_upload_mode_items": (_upload_resumable,),
    "_RESUMABLE_DEFAULT_REQUEST_TIMEOUT": (_upload_resumable, _upload_service),
    "config": (_upload_service,),
    "is_supported_upload_revision": (_upload_service,),
    "normalize_path_in_repo": (_upload_service,),
    "validate_upload_path_no_symlinks": (_upload_service,),
    "run_canonical_lfs_upload": (_upload_service,),
    "_atomgit_repo_type": (_upload_service,),
    "DEFAULT_UPLOAD_BATCH_SIZE": (_upload_service,),
    "_RESUMABLE_LFS_PATTERN_MAX_COUNT": (_upload_service,),
    "_configure_remote_lfs_attributes": (_upload_service,),
    **{
        name: _UPLOAD_OWNER_CONSUMERS.get(name, (owner,))
        for name, owner in _UPLOAD_OWNER_EXPORTS.items()
    },
}

_DOWNLOAD_PATCH_TARGETS = {
    "errno": (_download_manifest,),
    "hashlib": (_download_integrity, _download_manifest, _download_resume),
    "json": (_download_manifest,),
    "ntpath": (_download_prune,),
    "os": (_download_manifest, _download_prune, _download_resume, _download_transport),
    "shutil": (_download_resume, _download_transport),
    "socket": (_download_transport,),
    "ssl": (_download_transport,),
    "stat": (_download_manifest, _download_prune),
    "tempfile": (_download_manifest, _download_resume, _download_transport),
    "time": (_download_resume,),
    "urllib": (
        _download_integrity,
        _download_manifest,
        _download_resume,
        _download_transport,
    ),
    "ExitStack": (_download_service,),
    "contextmanager": (_download_manifest, _download_resume),
    "Path": (
        _download_integrity,
        _download_manifest,
        _download_prune,
        _download_resume,
        _download_service,
        _download_transport,
    ),
    "PurePosixPath": (_download_prune,),
    "PureWindowsPath": (_download_prune,),
    "quote": (_download_transport,),
    "urljoin": (_download_integrity, _download_transport),
    "urlsplit": (_download_integrity, _download_resume, _download_transport),
    "config": (_download_service,),
    "HfApi": (_download_service,),
    "get_hf_file_metadata": (_download_integrity,),
    "hf_http_get": (_download_resume,),
    "is_auth_error": (_download_service,),
    "run_download_with_retry": (_download_transport,),
    "sanitized_download_error": (_download_service,),
    "DownloadChecksumMetadataError": (_download_integrity,),
    "DownloadChecksumMismatchError": (_download_integrity, _download_resume),
    "_DOWNLOAD_MANIFEST_VERSION": (_download_manifest,),
    "_DOWNLOAD_MANIFEST_MAX_BYTES": (_download_manifest,),
    "_atomgit_hf_endpoint": (
        _download_integrity,
        _download_manifest,
        _download_resume,
        _download_transport,
    ),
    "_atomgit_resolve_url": (
        _download_integrity,
        _download_resume,
        _download_transport,
    ),
    "_atomgit_resolve_url_raw": (
        _download_integrity,
        _download_resume,
        _download_transport,
    ),
    "_atomgit_file_checksum": (_download_integrity, _download_service),
    "_checksum_from_hf_metadata": (_download_integrity,),
    "_checksum_from_metadata_values": (_download_integrity,),
    "_atomgit_file_download_metadata": (_download_integrity, _download_resume),
    "_verify_download_checksum": (
        _download_integrity,
        _download_resume,
        _download_service,
        _download_transport,
    ),
    "_raw_metadata_size": (_download_integrity,),
    "_atomgit_file_download_metadata_raw": (_download_integrity,),
    "_set_private_file_mode": (_download_manifest,),
    "_download_manifest_root": (_download_manifest,),
    "_download_manifest_path": (_download_manifest, _download_service),
    "_load_download_manifest": (_download_manifest, _download_service),
    "_write_download_manifest": (_download_manifest, _download_service),
    "_windows_file_lock_module": (_download_manifest,),
    "_try_lock_download_manifest_descriptor_windows": (_download_manifest,),
    "_unlock_download_manifest_descriptor_windows": (_download_manifest,),
    "_try_lock_download_manifest_descriptor": (_download_manifest,),
    "_unlock_download_manifest_descriptor": (_download_manifest,),
    "_download_manifest_lock": (_download_manifest, _download_service),
    "_resume_cache_root": (_download_resume,),
    "_resume_cache_identity": (_download_resume,),
    "_process_is_running": (_download_resume,),
    "_resume_download_lock": (_download_resume,),
    "_copy_resumed_file_to_destination": (_download_resume,),
    "_parse_content_range": (_download_resume,),
    "_atomgit_resume_raw": (_download_resume,),
    "_download_atomgit_file_resumable": (_download_resume, _download_service),
    "_is_not_found_error": (
        _download_integrity,
        _download_service,
        _download_transport,
    ),
    "_atomgit_list_repo_files": (_download_service,),
    "_repository_filename_parts": (
        _download_manifest,
        _download_prune,
        _download_service,
    ),
    "_safe_download_destination": (_download_service,),
    "_WindowsFileAPI": (_download_prune,),
    "_normalized_windows_handle_path": (_download_prune,),
    "_prune_managed_download_file_windows": (_download_prune,),
    "_uses_windows_prune": (_download_prune,),
    "_prune_managed_download_file": (_download_prune,),
    "_prune_managed_download_files": (_download_prune, _download_service),
    "_download_url_origin": (_download_integrity, _download_transport),
    "_prepare_download_redirect": (
        _download_integrity,
        _download_resume,
        _download_transport,
    ),
    "_AtomGitRedirectHandler": (_download_transport,),
    "_atomgit_open_url": (_download_integrity, _download_transport),
    "_atomgit_raw_http_request": (_download_transport,),
    "_atomgit_raw_http_get": (
        _download_integrity,
        _download_resume,
        _download_transport,
    ),
    "_atomgit_raw_http_head": (_download_integrity,),
    "_copy_exact_http_body": (_download_transport,),
    "_read_chunk_line": (_download_transport,),
    "_copy_chunked_http_body": (_download_transport,),
    "_copy_framed_http_body": (_download_resume, _download_transport),
    "_atomgit_download_raw": (_download_transport,),
    "_download_atomgit_file": (_download_service, _download_transport),
}

# Preserve historical module-object patching while service methods resolve
# their dependencies in the new owner modules. The API module itself remains a
# partial implementation until the later transfer and facade program steps.
_PATCH_TARGETS = {
    "urllib": (_authentication_service, _repository_service, _v5_adapter),
    "json": (_authentication_service, _repository_service, _v5_adapter),
    "socket": (_repository_service, _v5_adapter),
    "config": (_authentication_service, _repository_service, _v5_adapter),
    "create_repo": (_repository_service, _v5_adapter),
    "HfApi": (_repository_service, _v5_adapter),
    "quote": (_repository_service, _v5_adapter),
    "auth_error_kind": (_repository_service, _v5_adapter),
    "is_supported_upload_revision": (_repository_service, _v5_adapter),
    "normalize_repo_id": (_repository_service, _v5_adapter),
    "_atomgit_open_url": (_repository_service, _v5_adapter),
    "_is_not_found_error": (_repository_service, _v5_adapter),
    "_ATOMGIT_IDENTITY_MAX_JSON_BYTES": (_authentication_service, _v5_adapter),
    "_ATOMGIT_V5_API_BASE": (_repository_service, _v5_adapter),
    "_ATOMGIT_V5_MAX_JSON_BYTES": (_repository_service, _v5_adapter),
    **{
        name: (_repository_service, _v5_adapter)
        for name in (
            "_atomgit_repo_type",
            "_atomgit_repo_exists",
            "_atomgit_v5_branch_commit_id",
            "_atomgit_v5_commit_sha",
            "_atomgit_v5_get_json",
            "_atomgit_v5_repo_path",
            "_atomgit_v5_request_json",
            "_classify_create_repo_error",
            "_is_definitive_v5_write_error",
            "_repo_private_state",
        )
    },
    "_sanitized_v5_api_error": (
        _authentication_service,
        _repository_service,
        _v5_adapter,
    ),
}

for _patch_name, _download_targets in _DOWNLOAD_PATCH_TARGETS.items():
    _existing_targets = _PATCH_TARGETS.get(_patch_name, ())
    _PATCH_TARGETS[_patch_name] = tuple(
        dict.fromkeys((*_existing_targets, *_download_targets))
    )

    # Initialize every former resolution point from the historical module
    # before its forwarding module type becomes active.
    _patch_value = globals()[_patch_name]
    for _patch_target in _download_targets:
        setattr(_patch_target, _patch_name, _patch_value)

for _patch_name, _upload_targets in _UPLOAD_PATCH_TARGETS.items():
    _existing_targets = _PATCH_TARGETS.get(_patch_name, ())
    _PATCH_TARGETS[_patch_name] = tuple(
        dict.fromkeys((*_existing_targets, *_upload_targets))
    )
    _patch_value = globals()[_patch_name]
    for _patch_target in _upload_targets:
        setattr(_patch_target, _patch_name, _patch_value)

for _patch_name, _lfs_targets in _LFS_PATCH_TARGETS.items():
    _existing_targets = _PATCH_TARGETS.get(_patch_name, ())
    _PATCH_TARGETS[_patch_name] = tuple(
        dict.fromkeys((*_existing_targets, *_lfs_targets))
    )
    _patch_value = globals()[_patch_name]
    for _patch_target in _lfs_targets:
        setattr(_patch_target, _patch_name, _patch_value)

_LFS_DEPENDENCY_TARGETS = {
    "HfApi": (_lfs_service,),
    "json": (_lfs_service,),
    "math": (_lfs_service,),
    "os": (_lfs_service,),
    "random": (_lfs_service,),
    "socket": (_lfs_service,),
    "tempfile": (_lfs_service,),
    "threading": (_lfs_service,),
    "time": (_lfs_service,),
    "urllib": (_lfs_service,),
    "httpx": (_lfs_service,),
    "Path": (_lfs_service,),
    "quote": (_lfs_service,),
    "parsedate_to_datetime": (_lfs_service,),
    "timezone": (_lfs_service,),
    "_atomgit_hf_endpoint": (_lfs_service,),
    "_atomgit_open_url": (_lfs_service,),
    "_atomgit_resolve_url": (_lfs_service,),
    "_atomgit_v5_get_json": (_lfs_service,),
    "_atomgit_v5_repo_path": (_lfs_service,),
    "_atomgit_v5_commit_sha": (_lfs_service,),
    "_resumable_error_chain": (_lfs_service,),
    "_resumable_error_status": (_lfs_service,),
    "_resumable_worker_error_category": (_lfs_service,),
    "_RESUMABLE_WORKER_ERROR_MESSAGES": (_lfs_service,),
}
for _patch_name, _lfs_targets in _LFS_DEPENDENCY_TARGETS.items():
    _existing_targets = _PATCH_TARGETS.get(_patch_name, ())
    _PATCH_TARGETS[_patch_name] = tuple(
        dict.fromkeys((*_existing_targets, *_lfs_targets))
    )
    _patch_value = globals()[_patch_name]
    for _patch_target in _lfs_targets:
        setattr(_patch_target, _patch_name, _patch_value)

_FacadeModule = type(
    "_FacadeModule",
    (types.ModuleType,),
    {"__setattr__": _forward_legacy_patch, "__delattr__": _delete_legacy_patch},
)
sys.modules[__name__].__class__ = _FacadeModule

# 全局API实例
api = HuggingFaceAPI()
