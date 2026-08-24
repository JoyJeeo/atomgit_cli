"""Fail-closed registry for CLI/native-SDK capability ownership."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple


class CapabilityClass(str, Enum):
    PARITY_REQUIRED = "parity-required"
    CLI_ONLY = "cli-only"
    SDK_ONLY = "sdk-only"


@dataclass(frozen=True)
class CapabilitySpec:
    capability_id: str
    classification: CapabilityClass
    shared_usecase: Optional[str]
    cli_entry: Optional[str]
    sdk_entry: Optional[str]
    result_contract: str
    tests: Tuple[str, ...]


def _spec(
    capability_id: str,
    classification: CapabilityClass,
    shared_usecase: Optional[str],
    cli_entry: Optional[str],
    sdk_entry: Optional[str],
    result_contract: str,
    *tests: str,
) -> CapabilitySpec:
    return CapabilitySpec(
        capability_id,
        classification,
        shared_usecase,
        cli_entry,
        sdk_entry,
        result_contract,
        tuple(tests),
    )


CAPABILITY_REGISTRY: Dict[str, CapabilitySpec] = {
    "AUTHENTICATION": _spec(
        "AUTHENTICATION",
        CapabilityClass.PARITY_REQUIRED,
        "atomgit.usecases.authentication.AuthenticationUseCase",
        "atomgit login/logout/whoami",
        "AtomGitClient.login/logout/whoami",
        "OperationResult[dict]",
        "test_architecture_parity.py",
    ),
    "REPOSITORIES": _spec(
        "REPOSITORIES",
        CapabilityClass.PARITY_REQUIRED,
        "atomgit.usecases.repositories.RepositoryUseCase",
        "atomgit repo *",
        "AtomGitClient repository methods",
        "OperationResult",
        "test_architecture_parity.py",
    ),
    "UPLOAD": _spec(
        "UPLOAD",
        CapabilityClass.PARITY_REQUIRED,
        "atomgit.usecases.transfers.UploadUseCase",
        "atomgit upload",
        "AtomGitClient.upload_file/upload_folder",
        "OperationResult",
        "test_architecture_parity.py",
    ),
    "DOWNLOAD": _spec(
        "DOWNLOAD",
        CapabilityClass.PARITY_REQUIRED,
        "atomgit.usecases.transfers.DownloadUseCase",
        "atomgit download*",
        "AtomGitClient.download_snapshot/download_file",
        "OperationResult",
        "test_architecture_parity.py",
    ),
    "REVISION": _spec(
        "REVISION",
        CapabilityClass.PARITY_REQUIRED,
        "atomgit.usecases.repositories.RepositoryUseCase",
        "repo branch/upload --revision",
        "AtomGitClient revision parameters",
        "OperationResult",
        "test_architecture_parity.py",
    ),
    "REPO-TYPE": _spec(
        "REPO-TYPE",
        CapabilityClass.PARITY_REQUIRED,
        "atomgit.domain.repositories",
        "CLI repo/upload/download types",
        "AtomGitClient repo_type parameters",
        "shared policy",
        "test_architecture_parity.py",
    ),
    "TOKEN": _spec(
        "TOKEN",
        CapabilityClass.PARITY_REQUIRED,
        "atomgit.core.policies.resolve_token",
        "all remote CLI entries",
        "all AtomGitClient remote entries",
        "shared token policy",
        "test_architecture_parity.py",
    ),
    "CHECKSUM": _spec(
        "CHECKSUM",
        CapabilityClass.PARITY_REQUIRED,
        "atomgit.usecases.transfers.DownloadUseCase",
        "download --verify-checksum",
        "AtomGitClient.download_* checksum",
        "OperationResult.checksum",
        "test_architecture_parity.py",
    ),
    "RESUME": _spec(
        "RESUME",
        CapabilityClass.PARITY_REQUIRED,
        "atomgit.usecases.transfers.DownloadUseCase",
        "download --resume/upload resumable",
        "AtomGitClient resume parameters",
        "OperationResult.metadata",
        "test_architecture_parity.py",
    ),
    "PRUNE": _spec(
        "PRUNE",
        CapabilityClass.PARITY_REQUIRED,
        "atomgit.usecases.transfers.DownloadUseCase",
        "download --prune",
        "AtomGitClient.download_snapshot(prune=True)",
        "OperationResult.metadata",
        "test_architecture_parity.py",
    ),
    "LFS": _spec(
        "LFS",
        CapabilityClass.PARITY_REQUIRED,
        "atomgit.usecases.transfers.UploadUseCase",
        "atomgit upload --auto-configure-lfs",
        "AtomGitClient.upload_folder(auto_configure_lfs=True)",
        "OperationResult.metadata",
        "test_architecture_parity.py",
    ),
    "FINAL_STATE": _spec(
        "FINAL_STATE",
        CapabilityClass.PARITY_REQUIRED,
        "atomgit.usecases.repositories.RepositoryUseCase",
        "repo visibility/delete/branch",
        "AtomGitClient repository methods",
        "OperationResult.ok",
        "test_architecture_parity.py",
    ),
    "PRESENTATION": _spec(
        "PRESENTATION",
        CapabilityClass.CLI_ONLY,
        None,
        "atomgit Click output/prompts/progress/exits",
        None,
        "CLI presentation",
        "test_architecture_parity.py",
    ),
    "LIFECYCLE": _spec(
        "LIFECYCLE",
        CapabilityClass.CLI_ONLY,
        None,
        "atomgit update/uninstall",
        None,
        "CLI lifecycle",
        "test_architecture_parity.py",
    ),
    "SHELL_HOOKS": _spec(
        "SHELL_HOOKS",
        CapabilityClass.CLI_ONLY,
        None,
        "atomgit completion *",
        None,
        "CLI completion",
        "test_architecture_parity.py",
    ),
    "CONFIG_DISPLAY": _spec(
        "CONFIG_DISPLAY",
        CapabilityClass.CLI_ONLY,
        None,
        "atomgit config-show",
        None,
        "CLI output",
        "test_architecture_parity.py",
    ),
}


def validate_parity_registry(registry: Optional[Dict[str, CapabilitySpec]] = None):
    """Return errors instead of silently accepting one-sided capabilities."""
    registry = CAPABILITY_REGISTRY if registry is None else registry
    errors = []
    for key, spec in registry.items():
        if key != spec.capability_id:
            errors.append(f"registry key mismatch: {key} != {spec.capability_id}")
        if not spec.result_contract or not spec.tests:
            errors.append(f"{key} is missing result/tests contract")
        parity = spec.classification == CapabilityClass.PARITY_REQUIRED
        if parity and (
            not spec.shared_usecase or not spec.cli_entry or not spec.sdk_entry
        ):
            errors.append(f"{key} parity capability is one-sided")
        if (
            not parity
            and spec.classification == CapabilityClass.CLI_ONLY
            and spec.sdk_entry
        ):
            errors.append(f"{key} CLI-only capability has an SDK entry")
    return tuple(errors)


__all__ = [
    "CAPABILITY_REGISTRY",
    "CapabilityClass",
    "CapabilitySpec",
    "validate_parity_registry",
]
