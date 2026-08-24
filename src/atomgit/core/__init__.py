"""Stable, dependency-free contracts shared by AtomGit interfaces.

The core package deliberately contains no Click, Hugging Face, AtomGit V5, or
filesystem/network implementation.  Concrete integrations implement the ports
defined here and are assembled by the user-facing interfaces.
"""

from .contracts import (
    DownloadRequest,
    OperationResult,
    RepositoryRequest,
    UploadRequest,
    Visibility,
)
from .parity import CAPABILITY_REGISTRY, CapabilityClass, validate_parity_registry
from .policies import normalize_repo_id, normalize_repo_type, normalize_revision

__all__ = [
    "CapabilityClass",
    "CAPABILITY_REGISTRY",
    "DownloadRequest",
    "OperationResult",
    "RepositoryRequest",
    "UploadRequest",
    "Visibility",
    "normalize_repo_id",
    "normalize_repo_type",
    "normalize_revision",
    "validate_parity_registry",
]
