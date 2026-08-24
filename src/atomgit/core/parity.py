"""Fail-closed registry for CLI/native-SDK capability ownership.

The runtime route registry keeps the parity declarations executable: every
parity-required capability names importable usecase, CLI, and native SDK
symbols, and class-based usecases also declare the methods they own.
"""

import importlib
import inspect
import re
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


@dataclass(frozen=True)
class RuntimeRoute:
    """Importable runtime ownership for one parity capability."""

    usecase: str
    usecase_methods: Tuple[str, ...]
    cli_entries: Tuple[str, ...]
    sdk_entries: Tuple[str, ...]


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


def _route(usecase, usecase_methods, cli_entries, sdk_entries):
    return RuntimeRoute(
        usecase,
        tuple(usecase_methods),
        tuple(cli_entries),
        tuple(sdk_entries),
    )


# This is deliberately separate from the presentation text in
# ``CAPABILITY_REGISTRY``.  The latter remains a compatibility/documentation
# surface; these paths are imported by the executable contract.
RUNTIME_ROUTE_REGISTRY: Dict[str, RuntimeRoute] = {
    "AUTHENTICATION": _route(
        "atomgit.usecases.authentication.AuthenticationUseCase",
        ("login", "logout", "whoami"),
        (
            "atomgit.commands.authentication.login",
            "atomgit.commands.authentication.logout",
            "atomgit.commands.authentication.whoami",
        ),
        (
            "atomgit.interfaces.sdk.client.AtomGitClient.login",
            "atomgit.interfaces.sdk.client.AtomGitClient.logout",
            "atomgit.interfaces.sdk.client.AtomGitClient.whoami",
        ),
    ),
    "REPOSITORIES": _route(
        "atomgit.usecases.repositories.RepositoryUseCase",
        ("create", "list", "set_visibility", "create_branch", "delete"),
        (
            "atomgit.commands.repositories.create",
            "atomgit.commands.repositories.list_repositories",
            "atomgit.commands.repositories.set_repository_visibility",
            "atomgit.commands.repositories.create_branch",
            "atomgit.commands.repositories.delete_repository",
        ),
        (
            "atomgit.interfaces.sdk.client.AtomGitClient.create_repository",
            "atomgit.interfaces.sdk.client.AtomGitClient.list_repositories",
            "atomgit.interfaces.sdk.client.AtomGitClient.set_repository_visibility",
            "atomgit.interfaces.sdk.client.AtomGitClient.create_branch",
            "atomgit.interfaces.sdk.client.AtomGitClient.delete_repository",
        ),
    ),
    "UPLOAD": _route(
        "atomgit.usecases.transfers.UploadUseCase",
        ("file", "folder"),
        ("atomgit.commands.transfers.upload",),
        (
            "atomgit.interfaces.sdk.client.AtomGitClient.upload_file",
            "atomgit.interfaces.sdk.client.AtomGitClient.upload_folder",
        ),
    ),
    "DOWNLOAD": _route(
        "atomgit.usecases.transfers.DownloadUseCase",
        ("snapshot", "file"),
        (
            "atomgit.commands.transfers.download",
            "atomgit.commands.transfers.download_file",
        ),
        (
            "atomgit.interfaces.sdk.client.AtomGitClient.download_snapshot",
            "atomgit.interfaces.sdk.client.AtomGitClient.download_file",
        ),
    ),
    "REVISION": _route(
        "atomgit.usecases.repositories.RepositoryUseCase",
        ("create_branch",),
        (
            "atomgit.commands.repositories.create_branch",
            "atomgit.commands.transfers.upload",
        ),
        (
            "atomgit.interfaces.sdk.client.AtomGitClient.create_branch",
            "atomgit.interfaces.sdk.client.AtomGitClient.upload_file",
            "atomgit.interfaces.sdk.client.AtomGitClient.upload_folder",
        ),
    ),
    "REPO-TYPE": _route(
        "atomgit.domain.repositories.validate_repository_request",
        (),
        (
            "atomgit.commands.repositories.create",
            "atomgit.commands.transfers.upload",
            "atomgit.commands.transfers.download",
        ),
        (
            "atomgit.interfaces.sdk.client.AtomGitClient.create_repository",
            "atomgit.interfaces.sdk.client.AtomGitClient.upload_file",
            "atomgit.interfaces.sdk.client.AtomGitClient.upload_folder",
            "atomgit.interfaces.sdk.client.AtomGitClient.download_snapshot",
            "atomgit.interfaces.sdk.client.AtomGitClient.download_file",
        ),
    ),
    "TOKEN": _route(
        "atomgit.core.policies.resolve_token",
        (),
        (
            "atomgit.commands.authentication.login",
            "atomgit.commands.repositories.create",
            "atomgit.commands.transfers.upload",
            "atomgit.commands.transfers.download",
        ),
        (
            "atomgit.interfaces.sdk.client.AtomGitClient.whoami",
            "atomgit.interfaces.sdk.client.AtomGitClient.create_repository",
            "atomgit.interfaces.sdk.client.AtomGitClient.upload_file",
            "atomgit.interfaces.sdk.client.AtomGitClient.upload_folder",
            "atomgit.interfaces.sdk.client.AtomGitClient.download_snapshot",
            "atomgit.interfaces.sdk.client.AtomGitClient.download_file",
        ),
    ),
    "CHECKSUM": _route(
        "atomgit.usecases.transfers.DownloadUseCase",
        ("snapshot", "file"),
        (
            "atomgit.commands.transfers.download",
            "atomgit.commands.transfers.download_file",
        ),
        (
            "atomgit.interfaces.sdk.client.AtomGitClient.download_snapshot",
            "atomgit.interfaces.sdk.client.AtomGitClient.download_file",
        ),
    ),
    "RESUME": _route(
        "atomgit.usecases.transfers.DownloadUseCase",
        ("snapshot", "file"),
        (
            "atomgit.commands.transfers.upload",
            "atomgit.commands.transfers.download",
            "atomgit.commands.transfers.download_file",
        ),
        (
            "atomgit.interfaces.sdk.client.AtomGitClient.upload_folder",
            "atomgit.interfaces.sdk.client.AtomGitClient.download_snapshot",
            "atomgit.interfaces.sdk.client.AtomGitClient.download_file",
        ),
    ),
    "PRUNE": _route(
        "atomgit.usecases.transfers.DownloadUseCase",
        ("snapshot",),
        ("atomgit.commands.transfers.download",),
        ("atomgit.interfaces.sdk.client.AtomGitClient.download_snapshot",),
    ),
    "LFS": _route(
        "atomgit.usecases.transfers.UploadUseCase",
        ("folder",),
        ("atomgit.commands.transfers.upload",),
        ("atomgit.interfaces.sdk.client.AtomGitClient.upload_folder",),
    ),
    "FINAL_STATE": _route(
        "atomgit.usecases.repositories.RepositoryUseCase",
        ("set_visibility", "create_branch", "delete"),
        (
            "atomgit.commands.repositories.set_repository_visibility",
            "atomgit.commands.repositories.create_branch",
            "atomgit.commands.repositories.delete_repository",
        ),
        (
            "atomgit.interfaces.sdk.client.AtomGitClient.set_repository_visibility",
            "atomgit.interfaces.sdk.client.AtomGitClient.create_branch",
            "atomgit.interfaces.sdk.client.AtomGitClient.delete_repository",
        ),
    ),
}


def _resolve_symbol(path: str):
    """Resolve a dotted module/symbol path without importing broad facades."""
    parts = path.split(".")
    for index in range(len(parts) - 1, 0, -1):
        module_name = ".".join(parts[:index])
        try:
            value = importlib.import_module(module_name)
        except ModuleNotFoundError as error:
            if error.name != module_name and not error.name.startswith(
                module_name + "."
            ):
                raise
            continue
        for attribute in parts[index:]:
            value = getattr(value, attribute)
        return value
    raise ImportError(f"runtime route is not dotted: {path}")


_CLI_ROUTE_OPERATIONS = {
    "atomgit.commands.authentication.login": ("login",),
    "atomgit.commands.authentication.logout": ("logout",),
    "atomgit.commands.authentication.whoami": ("whoami",),
    "atomgit.commands.repositories.create": ("create_repository",),
    "atomgit.commands.repositories.list_repositories": ("list_repositories",),
    "atomgit.commands.repositories.set_repository_visibility": (
        "set_repository_visibility",
    ),
    "atomgit.commands.repositories.create_branch": ("create_branch",),
    "atomgit.commands.repositories.delete_repository": ("delete_repository",),
    "atomgit.commands.transfers.upload": ("upload_file", "upload_folder"),
    "atomgit.commands.transfers.download": ("download_snapshot",),
    "atomgit.commands.transfers.download_file": ("download_file",),
}

_SDK_USECASE_DELEGATIONS = {
    "login": "self._auth.login",
    "logout": "self._auth.logout",
    "whoami": "self._auth.whoami",
    "create_repository": "self._repos.create",
    "list_repositories": "self._repos.list",
    "set_repository_visibility": "self._repos.set_visibility",
    "create_branch": "self._repos.create_branch",
    "delete_repository": "self._repos.delete",
    "upload_file": "self._uploads.file",
    "upload_folder": "self._uploads.folder",
    "download_snapshot": "self._downloads.snapshot",
    "download_file": "self._downloads.file",
}


def validate_runtime_routes(
    registry: Optional[Dict[str, CapabilitySpec]] = None,
    routes: Optional[Dict[str, RuntimeRoute]] = None,
):
    """Return errors for missing or non-importable parity runtime routes."""
    registry = CAPABILITY_REGISTRY if registry is None else registry
    routes = RUNTIME_ROUTE_REGISTRY if routes is None else routes
    errors = []
    for key, spec in registry.items():
        if spec.classification != CapabilityClass.PARITY_REQUIRED:
            if key in routes:
                errors.append(f"{key} non-parity capability has runtime route")
            continue
        route = routes.get(key)
        if route is None:
            errors.append(f"{key} is missing runtime route")
            continue
        try:
            usecase = _resolve_symbol(route.usecase)
        except (ImportError, AttributeError) as error:
            errors.append(f"{key} usecase cannot be resolved: {error}")
            continue
        for method in route.usecase_methods:
            if not callable(getattr(usecase, method, None)):
                errors.append(
                    f"{key} usecase method is missing: {route.usecase}.{method}"
                )
        for surface, entries in (
            ("CLI", route.cli_entries),
            ("SDK", route.sdk_entries),
        ):
            if not entries:
                errors.append(f"{key} has no {surface} runtime entries")
            for entry in entries:
                try:
                    target = _resolve_symbol(entry)
                except (ImportError, AttributeError) as error:
                    errors.append(f"{key} {surface} route cannot be resolved: {error}")
                    continue
                if not callable(target):
                    errors.append(f"{key} {surface} route is not callable: {entry}")
                source = inspect.getsource(target)
                if surface == "CLI":
                    operations = _CLI_ROUTE_OPERATIONS.get(entry, ())
                    if not operations:
                        errors.append(
                            f"{key} CLI route has no operation contract: {entry}"
                        )
                    for operation in operations:
                        pattern = rf"context\.run_usecase\(\s*['\"]{re.escape(operation)}['\"]"
                        if not re.search(pattern, source):
                            errors.append(
                                f"{key} CLI route bypasses shared usecase {operation}: {entry}"
                            )
                else:
                    method_name = entry.rsplit(".", 1)[-1]
                    delegation = _SDK_USECASE_DELEGATIONS.get(method_name)
                    if delegation and delegation not in source:
                        errors.append(
                            f"{key} SDK route bypasses shared usecase {delegation}: {entry}"
                        )
    for key in routes:
        if key not in registry:
            errors.append(f"runtime route is unregistered: {key}")
    return tuple(errors)


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
    errors.extend(validate_runtime_routes(registry))
    return tuple(errors)


__all__ = [
    "CAPABILITY_REGISTRY",
    "CapabilityClass",
    "CapabilitySpec",
    "RuntimeRoute",
    "RUNTIME_ROUTE_REGISTRY",
    "validate_runtime_routes",
    "validate_parity_registry",
]
