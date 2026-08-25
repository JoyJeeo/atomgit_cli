"""Historical facade for the owned Python SDK implementation."""

import sys
import types

from .runtime import configure_hf_environment

configure_hf_environment()


from .adapters.sdk_datasets import (  # noqa: E402,F401
    DATASET_SUPPORT,
    HF_DATASETS_CACHE,
    ds_load_dataset,
    load_dataset,
)
from .adapters.sdk_downloads import (  # noqa: E402,F401
    download_file,
    hf_hub_download,
    hf_snapshot_download,
    hub_download_url,
    snapshot_download,
)
from .adapters.sdk_repositories import create_repo, create_repository  # noqa: E402,F401
from .adapters.sdk_uploads import hf_upload_folder, upload_folder  # noqa: E402,F401
from .exceptions import (  # noqa: E402
    AtomGitAuthenticationError,
    AtomGitError,
    AtomGitNetworkError,
    AtomGitRepositoryExistsError,
    AtomGitRepositoryNotFoundError,
    AtomGitRevisionNotFoundError,
    AtomGitTimeoutError,
    AtomGitUnsupportedError,
)

_sdk_datasets = sys.modules[load_dataset.__module__]
_sdk_downloads = sys.modules[snapshot_download.__module__]
_sdk_repositories = sys.modules[create_repository.__module__]
_sdk_uploads = sys.modules[upload_folder.__module__]
_sdk_common = sys.modules[_sdk_downloads._get_token.__module__]
_sdk_errors = sys.modules[_sdk_downloads._sdk_error.__module__]
_get_token = _sdk_common._get_token
_normalize_repo_id = _sdk_common._normalize_repo_id
_atomgit_repo_type = _sdk_common._atomgit_repo_type
_sdk_error = _sdk_errors._sdk_error
Path = _sdk_downloads.Path
os = _sdk_datasets.os
warnings = _sdk_downloads.warnings
config = _sdk_common.config
normalize_repo_id = _sdk_common.normalize_repo_id
auth_error_kind = _sdk_errors.auth_error_kind
is_retryable_download_error = _sdk_errors.is_retryable_download_error
CanonicalLfsPointerError = _sdk_errors.CanonicalLfsPointerError
run_download_with_retry = _sdk_downloads.run_download_with_retry
validate_upload_path_no_symlinks = _sdk_uploads.validate_upload_path_no_symlinks
run_canonical_lfs_upload = _sdk_uploads.run_canonical_lfs_upload

_SDK_PATCH_TARGETS = {
    "snapshot_download": (_sdk_downloads,),
    "hub_download_url": (_sdk_downloads,),
    "download_file": (_sdk_downloads,),
    "upload_folder": (_sdk_uploads,),
    "create_repository": (_sdk_repositories,),
    "load_dataset": (_sdk_datasets,),
    "_get_token": (
        _sdk_datasets,
        _sdk_downloads,
        _sdk_repositories,
        _sdk_uploads,
    ),
    "_normalize_repo_id": (
        _sdk_datasets,
        _sdk_downloads,
        _sdk_repositories,
        _sdk_uploads,
    ),
    "_atomgit_repo_type": (_sdk_repositories, _sdk_uploads),
    "_sdk_error": (
        _sdk_datasets,
        _sdk_downloads,
        _sdk_repositories,
        _sdk_uploads,
    ),
    "hf_snapshot_download": (_sdk_datasets, _sdk_downloads),
    "hf_hub_download": (_sdk_downloads,),
    "hf_upload_folder": (_sdk_uploads,),
    "create_repo": (_sdk_repositories,),
    "ds_load_dataset": (_sdk_datasets,),
    "DATASET_SUPPORT": (_sdk_datasets,),
    "HF_DATASETS_CACHE": (_sdk_datasets,),
    "Path": (_sdk_datasets, _sdk_downloads, _sdk_uploads),
    "os": (_sdk_datasets,),
    "warnings": (_sdk_downloads,),
    "config": (_sdk_common, _sdk_uploads),
    "normalize_repo_id": (_sdk_common, _sdk_uploads),
    "auth_error_kind": (_sdk_errors,),
    "is_retryable_download_error": (_sdk_errors,),
    "CanonicalLfsPointerError": (_sdk_errors,),
    "run_download_with_retry": (_sdk_datasets, _sdk_downloads),
    "validate_upload_path_no_symlinks": (_sdk_uploads,),
    "run_canonical_lfs_upload": (_sdk_uploads,),
    "AtomGitError": (_sdk_errors,),
    "AtomGitAuthenticationError": (
        _sdk_errors,
        _sdk_repositories,
        _sdk_uploads,
    ),
    "AtomGitNetworkError": (_sdk_errors,),
    "AtomGitRepositoryExistsError": (_sdk_errors, _sdk_repositories),
    "AtomGitRepositoryNotFoundError": (_sdk_errors,),
    "AtomGitRevisionNotFoundError": (_sdk_errors,),
    "AtomGitTimeoutError": (_sdk_errors,),
    "AtomGitUnsupportedError": (
        _sdk_errors,
        _sdk_repositories,
        _sdk_uploads,
    ),
}

# Seed every adapter resolution point from the historical owner. This keeps
# private helper identity and monkeypatch propagation stable while the adapter
# remains free of an eager import cycle through ``sdk.__init__``.
for _patch_name, _patch_targets in _SDK_PATCH_TARGETS.items():
    if not hasattr(sys.modules[__name__], _patch_name):
        continue
    _patch_value = globals()[_patch_name]
    for _patch_target in _patch_targets:
        setattr(_patch_target, _patch_name, _patch_value)


def _forward_sdk_patch(module, name, value):
    for target in module._SDK_PATCH_TARGETS.get(name, ()):
        setattr(target, name, value)
    types.ModuleType.__setattr__(module, name, value)


def _delete_sdk_patch(module, name):
    for target in module._SDK_PATCH_TARGETS.get(name, ()):
        if hasattr(target, name):
            delattr(target, name)
    types.ModuleType.__delattr__(module, name)


_FacadeModule = type(
    "_FacadeModule",
    (types.ModuleType,),
    {"__setattr__": _forward_sdk_patch, "__delattr__": _delete_sdk_patch},
)
sys.modules[__name__].__class__ = _FacadeModule


__all__ = [
    "AtomGitError",
    "AtomGitAuthenticationError",
    "AtomGitRepositoryNotFoundError",
    "AtomGitRepositoryExistsError",
    "AtomGitRevisionNotFoundError",
    "AtomGitTimeoutError",
    "AtomGitNetworkError",
    "AtomGitUnsupportedError",
    "snapshot_download",
    "hub_download_url",
    "download_file",
    "upload_folder",
    "create_repository",
    "load_dataset",
]
