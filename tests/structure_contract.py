"""Declarative ownership and dependency contract for structural refactors."""

import ast
from collections import defaultdict
from pathlib import Path

PRODUCTION_MODULE_OWNERS = {
    "__init__": "facade",
    "__main__": "cli",
    "api.__init__": "facade",
    "atomgit_hub": "sdk",
    "cli": "cli",
    "cli_contracts": "cli",
    "completion": "lifecycle",
    "config": "infrastructure",
    "commands.__init__": "cli",
    "commands.authentication": "cli",
    "commands.lifecycle": "cli",
    "commands.repositories": "cli",
    "commands.transfers": "cli",
    "download.__init__": "transfers",
    "download.integrity": "transfers",
    "download.manifest": "transfers",
    "download.prune": "transfers",
    "download.resume": "transfers",
    "download.service": "transfers",
    "download.transport": "transfers",
    "upload.__init__": "transfers",
    "upload.contracts": "transfers",
    "upload.errors": "transfers",
    "upload.ordinary": "transfers",
    "upload.projection": "transfers",
    "upload.resumable": "transfers",
    "upload.service": "transfers",
    "exceptions": "infrastructure",
    "lfs_pointer": "lfs",
    "release": "distribution",
    "runtime": "infrastructure",
    "uninstaller": "lifecycle",
    "utils": "infrastructure",
    "version": "infrastructure",
    "infrastructure.__init__": "infrastructure",
    "infrastructure.cache": "infrastructure",
    "infrastructure.config": "infrastructure",
    "infrastructure.filesystem": "infrastructure",
    "infrastructure.git_credentials": "infrastructure",
    "infrastructure.output": "infrastructure",
    "infrastructure.runtime": "infrastructure",
    "infrastructure.utils": "infrastructure",
    "infrastructure.validation": "infrastructure",
    "lifecycle.__init__": "lifecycle",
    "lifecycle.completion": "lifecycle",
    "lifecycle.environment": "lifecycle",
    "lifecycle.managed_paths": "lifecycle",
    "lifecycle.uninstall": "lifecycle",
    "lfs.__init__": "lfs",
    "lfs.service": "lfs",
    "sdk.__init__": "sdk",
    "sdk.common": "sdk",
    "sdk.datasets": "sdk",
    "sdk.downloads": "sdk",
    "sdk.errors": "sdk",
    "sdk.repositories": "sdk",
    "sdk.uploads": "sdk",
    "services.__init__": "services",
    "services.authentication": "services",
    "services.repositories": "services",
}

DOMAIN_DEPENDENCIES = {
    "facade": {
        "cli",
        "sdk",
        "services",
        "transfers",
        "lifecycle",
        "distribution",
        "infrastructure",
        "lfs",
    },
    "cli": {
        "services",
        "transfers",
        "lifecycle",
        "distribution",
        "infrastructure",
        "lfs",
    },
    "sdk": {"services", "transfers", "infrastructure", "lfs"},
    "services": {"infrastructure"},
    "transfers": {"infrastructure", "lfs"},
    "lifecycle": {"infrastructure"},
    "distribution": {"lifecycle", "infrastructure"},
    "infrastructure": set(),
    "lfs": {"infrastructure"},
}

# These edges are existing 1.1.1 debt. They may disappear but must never grow.
LEGACY_FORBIDDEN_EDGES = {
    ("cli", "api.__init__"),
}

CURRENT_INTERNAL_EDGES = {
    ("__init__", "api.__init__"),
    ("__init__", "atomgit_hub"),
    ("__init__", "cli"),
    ("__init__", "config"),
    ("__init__", "runtime"),
    ("__init__", "version"),
    ("__main__", "cli"),
    ("api.__init__", "cli_contracts"),
    ("api.__init__", "config"),
    ("api.__init__", "download.__init__"),
    ("api.__init__", "download.service"),
    ("api.__init__", "lfs.service"),
    ("api.__init__", "lfs.__init__"),
    ("api.__init__", "lfs_pointer"),
    ("api.__init__", "runtime"),
    ("api.__init__", "services.authentication"),
    ("api.__init__", "services.__init__"),
    ("api.__init__", "services.repositories"),
    ("api.__init__", "upload.service"),
    ("api.__init__", "upload.__init__"),
    ("api.__init__", "utils"),
    ("atomgit_hub", "exceptions"),
    ("atomgit_hub", "runtime"),
    ("atomgit_hub", "sdk.datasets"),
    ("atomgit_hub", "sdk.downloads"),
    ("atomgit_hub", "sdk.repositories"),
    ("atomgit_hub", "sdk.uploads"),
    ("atomgit_hub", "sdk.datasets"),
    ("atomgit_hub", "sdk.downloads"),
    ("atomgit_hub", "sdk.repositories"),
    ("atomgit_hub", "sdk.uploads"),
    ("cli", "api.__init__"),
    ("cli", "cli_contracts"),
    ("cli", "completion"),
    ("cli", "config"),
    ("cli", "release"),
    ("cli", "runtime"),
    ("cli", "uninstaller"),
    ("cli", "utils"),
    ("cli", "version"),
    ("cli", "commands.__init__"),
    ("commands.__init__", "commands.authentication"),
    ("commands.__init__", "commands.lifecycle"),
    ("commands.__init__", "commands.repositories"),
    ("commands.__init__", "commands.transfers"),
    ("completion", "lifecycle.completion"),
    ("completion", "lifecycle.__init__"),
    ("lifecycle.completion", "lifecycle.environment"),
    ("lifecycle.completion", "lifecycle.managed_paths"),
    ("lifecycle.environment", "lifecycle.managed_paths"),
    ("lifecycle.uninstall", "lifecycle.environment"),
    ("lifecycle.uninstall", "lifecycle.managed_paths"),
    ("release", "lifecycle.environment"),
    ("services.authentication", "infrastructure.config"),
    ("services.authentication", "services.repositories"),
    ("services.repositories", "infrastructure.config"),
    ("services.repositories", "infrastructure.validation"),
    ("config", "infrastructure.config"),
    ("config", "infrastructure.__init__"),
    ("download.__init__", "download.service"),
    ("download.integrity", "download.transport"),
    ("download.manifest", "download.prune"),
    ("download.manifest", "download.transport"),
    ("download.resume", "download.integrity"),
    ("download.resume", "download.transport"),
    ("download.service", "download.integrity"),
    ("download.service", "download.manifest"),
    ("download.service", "download.prune"),
    ("download.service", "download.resume"),
    ("download.service", "download.transport"),
    ("download.service", "infrastructure.config"),
    ("download.service", "infrastructure.validation"),
    ("download.transport", "infrastructure.validation"),
    ("upload.errors", "infrastructure.validation"),
    ("upload.errors", "upload.projection"),
    ("upload.projection", "download.transport"),
    ("upload.resumable", "download.integrity"),
    ("upload.resumable", "download.transport"),
    ("upload.resumable", "lfs_pointer"),
    ("upload.resumable", "upload.errors"),
    ("upload.resumable", "upload.contracts"),
    ("upload.service", "infrastructure.config"),
    ("upload.service", "infrastructure.validation"),
    ("upload.service", "lfs_pointer"),
    ("upload.service", "upload.errors"),
    ("upload.service", "upload.contracts"),
    ("upload.service", "upload.ordinary"),
    ("upload.service", "upload.projection"),
    ("upload.service", "upload.resumable"),
    ("infrastructure.git_credentials", "infrastructure.output"),
    ("infrastructure.utils", "infrastructure.cache"),
    ("infrastructure.utils", "infrastructure.filesystem"),
    ("infrastructure.utils", "infrastructure.git_credentials"),
    ("infrastructure.utils", "infrastructure.output"),
    ("infrastructure.utils", "infrastructure.validation"),
    ("runtime", "infrastructure.runtime"),
    ("runtime", "infrastructure.__init__"),
    ("sdk.__init__", "sdk.datasets"),
    ("sdk.__init__", "sdk.downloads"),
    ("sdk.__init__", "sdk.repositories"),
    ("sdk.__init__", "sdk.uploads"),
    ("sdk.common", "infrastructure.config"),
    ("sdk.common", "infrastructure.validation"),
    ("sdk.datasets", "infrastructure.utils"),
    ("sdk.datasets", "sdk.common"),
    ("sdk.datasets", "sdk.errors"),
    ("sdk.downloads", "infrastructure.utils"),
    ("sdk.downloads", "sdk.common"),
    ("sdk.downloads", "sdk.errors"),
    ("sdk.errors", "exceptions"),
    ("sdk.errors", "infrastructure.utils"),
    ("sdk.errors", "lfs_pointer"),
    ("sdk.repositories", "exceptions"),
    ("sdk.repositories", "sdk.common"),
    ("sdk.repositories", "sdk.errors"),
    ("sdk.uploads", "exceptions"),
    ("sdk.uploads", "infrastructure.validation"),
    ("sdk.uploads", "lfs_pointer"),
    ("sdk.uploads", "sdk.common"),
    ("sdk.uploads", "sdk.errors"),
    ("uninstaller", "lifecycle.uninstall"),
    ("uninstaller", "lifecycle.__init__"),
    ("utils", "infrastructure.utils"),
    ("utils", "infrastructure.__init__"),
    ("cli_contracts", "upload.contracts"),
}

LEGACY_FACADE_DEBT = {
    "api.__init__": {"max_lines": 774, "max_functions": 0, "max_classes": 1},
    "atomgit_hub": {"max_lines": 158, "max_functions": 2, "max_classes": 0},
    "cli": {"max_lines": 452, "max_functions": 26, "max_classes": 1},
    "completion": {"max_lines": 92, "max_functions": 0, "max_classes": 0},
    "config": {"max_lines": 10, "max_functions": 0, "max_classes": 0},
    "runtime": {"max_lines": 6, "max_functions": 0, "max_classes": 0},
    "uninstaller": {"max_lines": 55, "max_functions": 0, "max_classes": 0},
    "utils": {"max_lines": 130, "max_functions": 0, "max_classes": 0},
}

PUBLIC_IMPORTS = (
    "atomgit",
    "atomgit.api",
    "atomgit.cli",
    "atomgit.completion",
    "atomgit.uninstaller",
    "atomgit.utils",
    "atomgit_hub",
)

PUBLIC_SYMBOLS = {
    "atomgit": (
        "__version__",
        "config",
        "api",
        "cli",
        "snapshot_download",
        "hub_download_url",
        "download_file",
        "upload_folder",
        "create_repository",
        "AtomGitError",
        "AtomGitAuthenticationError",
        "AtomGitRepositoryNotFoundError",
        "AtomGitRepositoryExistsError",
        "AtomGitRevisionNotFoundError",
        "AtomGitTimeoutError",
        "AtomGitNetworkError",
        "AtomGitUnsupportedError",
    ),
    "atomgit.api": ("HuggingFaceAPI", "api"),
    "atomgit.cli": ("cli",),
    "atomgit.completion": (
        "CompletionConfigError",
        "completion_script",
        "install_completion",
        "legacy_completion_present",
        "uninstall_completion",
    ),
    "atomgit.uninstaller": (
        "UninstallError",
        "active_conda_prefix",
        "build_uninstall_plan",
        "managed_completion_paths",
        "remove_managed_completion",
        "run_uninstall",
    ),
    "atomgit_hub": (
        "snapshot_download",
        "hub_download_url",
        "download_file",
        "upload_folder",
        "create_repository",
        "AtomGitError",
        "AtomGitAuthenticationError",
        "AtomGitRepositoryNotFoundError",
        "AtomGitRepositoryExistsError",
        "AtomGitRevisionNotFoundError",
        "AtomGitTimeoutError",
        "AtomGitNetworkError",
        "AtomGitUnsupportedError",
    ),
}

PACKAGE_ALL = tuple(
    symbol for symbol in PUBLIC_SYMBOLS["atomgit"] if symbol != "__version__"
)

PUBLIC_SIGNATURES = {
    "snapshot_download": "(repo_id: str, revision: Optional[str] = None, cache_dir: Union[str, pathlib.Path, NoneType] = None, local_dir: Union[str, pathlib.Path, NoneType] = None, local_dir_use_symlinks: Union[bool, str] = 'auto', library_name: Optional[str] = None, library_version: Optional[str] = None, user_agent: Union[str, Dict[str, str], NoneType] = None, proxies: Optional[Dict[str, str]] = None, etag_timeout: float = 10, resume_download: bool = False, force_download: bool = False, token: Union[bool, str, NoneType] = None, local_files_only: bool = False, allow_patterns: Union[List[str], str, NoneType] = None, ignore_patterns: Union[List[str], str, NoneType] = None, max_workers: int = 8, tqdm_class: Optional[Any] = None) -> str",
    "hub_download_url": "(repo_id: str, filename: str, revision: Optional[str] = None, repo_type: Optional[str] = None) -> str",
    "download_file": "(repo_id: str, filename: str, local_dir: Union[str, pathlib.Path, NoneType] = None, revision: Optional[str] = None, token: Optional[str] = None, force_download: bool = False) -> str",
    "upload_folder": "(folder_path: Union[str, pathlib.Path], repo_id: str, token: Optional[str] = None, repo_type: Optional[str] = None, revision: Optional[str] = None, commit_message: Optional[str] = None, commit_description: Optional[str] = None, path_in_repo: str = './', ignore_patterns: Optional[List[str]] = None, upload_timeout: float = 300.0) -> str",
    "create_repository": "(repo_id: str, token: Optional[str] = None, private: bool = False, repo_type: str = 'model', exist_ok: bool = False, space_sdk: Optional[str] = None, space_hardware: Optional[str] = None, space_storage: Optional[str] = None, space_sleep_time: Optional[int] = None, space_secrets: Optional[List[Dict]] = None, space_variables: Optional[List[Dict]] = None) -> str",
}

EXPECTED_WHEEL_FILES = {
    "atomgit/__init__.py",
    "atomgit/__main__.py",
    "atomgit/api/__init__.py",
    "atomgit/atomgit_hub.py",
    "atomgit/cli.py",
    "atomgit/cli_contracts.py",
    "atomgit/completion.py",
    "atomgit/config.py",
    "atomgit/commands/__init__.py",
    "atomgit/commands/authentication.py",
    "atomgit/commands/lifecycle.py",
    "atomgit/commands/repositories.py",
    "atomgit/commands/transfers.py",
    "atomgit/download/__init__.py",
    "atomgit/download/integrity.py",
    "atomgit/download/manifest.py",
    "atomgit/download/prune.py",
    "atomgit/download/resume.py",
    "atomgit/download/service.py",
    "atomgit/download/transport.py",
    "atomgit/upload/__init__.py",
    "atomgit/upload/contracts.py",
    "atomgit/upload/errors.py",
    "atomgit/upload/ordinary.py",
    "atomgit/upload/projection.py",
    "atomgit/upload/resumable.py",
    "atomgit/upload/service.py",
    "atomgit/lfs/__init__.py",
    "atomgit/lfs/service.py",
    "atomgit/sdk/__init__.py",
    "atomgit/sdk/common.py",
    "atomgit/sdk/datasets.py",
    "atomgit/sdk/downloads.py",
    "atomgit/sdk/errors.py",
    "atomgit/sdk/repositories.py",
    "atomgit/sdk/uploads.py",
    "atomgit/exceptions.py",
    "atomgit/lfs_pointer.py",
    "atomgit/release.py",
    "atomgit/runtime.py",
    "atomgit/uninstaller.py",
    "atomgit/utils.py",
    "atomgit/version.py",
    "atomgit_hub.py",
    "atomgit/infrastructure/__init__.py",
    "atomgit/infrastructure/cache.py",
    "atomgit/infrastructure/config.py",
    "atomgit/infrastructure/filesystem.py",
    "atomgit/infrastructure/git_credentials.py",
    "atomgit/infrastructure/output.py",
    "atomgit/infrastructure/runtime.py",
    "atomgit/infrastructure/utils.py",
    "atomgit/infrastructure/validation.py",
    "atomgit/lifecycle/__init__.py",
    "atomgit/lifecycle/completion.py",
    "atomgit/lifecycle/environment.py",
    "atomgit/lifecycle/managed_paths.py",
    "atomgit/lifecycle/uninstall.py",
    "atomgit/services/__init__.py",
    "atomgit/services/authentication.py",
    "atomgit/services/repositories.py",
}

EXPECTED_SDIST_FILES = {
    "src/atomgit/__init__.py",
    "src/atomgit/__main__.py",
    "src/atomgit/api/__init__.py",
    "src/atomgit/atomgit_hub.py",
    "src/atomgit/cli.py",
    "src/atomgit/cli_contracts.py",
    "src/atomgit/completion.py",
    "src/atomgit/config.py",
    "src/atomgit/commands/__init__.py",
    "src/atomgit/commands/authentication.py",
    "src/atomgit/commands/lifecycle.py",
    "src/atomgit/commands/repositories.py",
    "src/atomgit/commands/transfers.py",
    "src/atomgit/download/__init__.py",
    "src/atomgit/download/integrity.py",
    "src/atomgit/download/manifest.py",
    "src/atomgit/download/prune.py",
    "src/atomgit/download/resume.py",
    "src/atomgit/download/service.py",
    "src/atomgit/download/transport.py",
    "src/atomgit/upload/__init__.py",
    "src/atomgit/upload/contracts.py",
    "src/atomgit/upload/errors.py",
    "src/atomgit/upload/ordinary.py",
    "src/atomgit/upload/projection.py",
    "src/atomgit/upload/resumable.py",
    "src/atomgit/upload/service.py",
    "src/atomgit/lfs/__init__.py",
    "src/atomgit/lfs/service.py",
    "src/atomgit/sdk/__init__.py",
    "src/atomgit/sdk/common.py",
    "src/atomgit/sdk/datasets.py",
    "src/atomgit/sdk/downloads.py",
    "src/atomgit/sdk/errors.py",
    "src/atomgit/sdk/repositories.py",
    "src/atomgit/sdk/uploads.py",
    "src/atomgit/exceptions.py",
    "src/atomgit/lfs_pointer.py",
    "src/atomgit/release.py",
    "src/atomgit/runtime.py",
    "src/atomgit/uninstaller.py",
    "src/atomgit/utils.py",
    "src/atomgit/version.py",
    "src/atomgit_hub.py",
    "src/atomgit/infrastructure/__init__.py",
    "src/atomgit/infrastructure/cache.py",
    "src/atomgit/infrastructure/config.py",
    "src/atomgit/infrastructure/filesystem.py",
    "src/atomgit/infrastructure/git_credentials.py",
    "src/atomgit/infrastructure/output.py",
    "src/atomgit/infrastructure/runtime.py",
    "src/atomgit/infrastructure/utils.py",
    "src/atomgit/infrastructure/validation.py",
    "src/atomgit/lifecycle/__init__.py",
    "src/atomgit/lifecycle/completion.py",
    "src/atomgit/lifecycle/environment.py",
    "src/atomgit/lifecycle/managed_paths.py",
    "src/atomgit/lifecycle/uninstall.py",
    "src/atomgit/services/__init__.py",
    "src/atomgit/services/authentication.py",
    "src/atomgit/services/repositories.py",
}


def _module_name(path):
    return path.with_suffix("").as_posix().replace("/", ".")


def discover_source_texts(repository_root):
    package_root = Path(repository_root) / "src" / "atomgit"
    return {
        _module_name(path.relative_to(package_root)): path.read_text(encoding="utf-8")
        for path in sorted(package_root.rglob("*.py"))
    }


def discover_internal_edges(source_texts):
    module_names = set(source_texts)

    def resolve_module(candidate):
        if candidate in module_names:
            return candidate
        package_candidate = f"{candidate}.__init__"
        return package_candidate if package_candidate in module_names else None

    edges = set()
    for module_name, source in source_texts.items():
        tree = ast.parse(source, filename=f"{module_name}.py")
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                package = module_name.rsplit(".", 1)[0] if "." in module_name else ""
                base_parts = package.split(".") if package else []
                if node.level > 1:
                    base_parts = base_parts[: -(node.level - 1)]
                base = ".".join(base_parts)
                imported = f"{base}.{node.module}".strip(".") if node.module else base
                candidates = (
                    [imported]
                    if node.module
                    else [f"{base}.{alias.name}".strip(".") for alias in node.names]
                )
                edges.update(
                    (module_name, resolved)
                    for candidate in candidates
                    if (resolved := resolve_module(candidate)) is not None
                )
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"_LazyObject", "_import_runtime_module"}
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and resolve_module(node.args[0].value) is not None
            ):
                resolved = resolve_module(node.args[0].value)
                if resolved is not None:
                    edges.add((module_name, resolved))
        if module_name == "cli" and "_lazy_utility(" in source:
            edges.add(("cli", "utils"))
    return edges


def _top_level_counts(source):
    tree = ast.parse(source)
    return {
        "max_lines": len(source.splitlines()),
        "max_functions": sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            for node in tree.body
        ),
        "max_classes": sum(isinstance(node, ast.ClassDef) for node in tree.body),
    }


def _has_owned_content(source):
    tree = ast.parse(source)
    for index, node in enumerate(tree.body):
        if (
            index == 0
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        if not isinstance(node, (ast.Import, ast.ImportFrom, ast.Pass)):
            return True
    return False


def _cycle_errors(edges):
    graph = defaultdict(set)
    for source, target in edges:
        if source != "__init__" and target != "__init__":
            graph[source].add(target)
    errors = []
    visiting = set()
    visited = set()

    def visit(module, trail):
        if module in visiting:
            errors.append("internal dependency cycle: " + " -> ".join((*trail, module)))
            return
        if module in visited:
            return
        visiting.add(module)
        for target in sorted(graph[module]):
            visit(target, (*trail, module))
        visiting.remove(module)
        visited.add(module)

    for module in sorted(graph):
        visit(module, ())
    return errors


def validate_artifact_contract(module_owners=None, wheel_files=None, sdist_files=None):
    owners = PRODUCTION_MODULE_OWNERS if module_owners is None else module_owners
    wheel = EXPECTED_WHEEL_FILES if wheel_files is None else wheel_files
    sdist = EXPECTED_SDIST_FILES if sdist_files is None else sdist_files
    expected_package_files = {
        "atomgit/" + module.replace(".", "/") + ".py" for module in owners
    }
    expected_wheel = expected_package_files | {"atomgit_hub.py"}
    expected_sdist = {
        "src/atomgit/" + module.replace(".", "/") + ".py" for module in owners
    }
    expected_sdist.add("src/atomgit_hub.py")
    errors = []
    if set(wheel) != expected_wheel:
        errors.append(
            "wheel artifact contract mismatch: "
            f"missing={sorted(expected_wheel - set(wheel))}, "
            f"stale={sorted(set(wheel) - expected_wheel)}"
        )
    if set(sdist) != expected_sdist:
        errors.append(
            "sdist artifact contract mismatch: "
            f"missing={sorted(expected_sdist - set(sdist))}, "
            f"stale={sorted(set(sdist) - expected_sdist)}"
        )
    return errors


def validate_structure(source_texts, module_owners=None, legacy_debt=None):
    owners = PRODUCTION_MODULE_OWNERS if module_owners is None else module_owners
    debt = LEGACY_FACADE_DEBT if legacy_debt is None else legacy_debt
    errors = []
    discovered_modules = set(source_texts)
    registered_modules = set(owners)
    if discovered_modules != registered_modules:
        errors.append(
            "production module ownership mismatch: "
            f"unowned={sorted(discovered_modules - registered_modules)}, "
            f"stale={sorted(registered_modules - discovered_modules)}"
        )

    unknown_domains = set(owners.values()) - set(DOMAIN_DEPENDENCIES)
    if unknown_domains:
        errors.append(f"unknown ownership domains: {sorted(unknown_domains)}")

    for module_name, source in source_texts.items():
        try:
            has_content = _has_owned_content(source)
        except SyntaxError as error:
            errors.append(f"invalid Python module {module_name}: {error}")
            continue
        if not has_content:
            errors.append(f"empty placeholder module is forbidden: {module_name}")
        if owners.get(module_name) != "cli":
            tree = ast.parse(source)
            if any(
                (
                    isinstance(node, ast.Import)
                    and any(a.name == "click" for a in node.names)
                )
                or (isinstance(node, ast.ImportFrom) and node.module == "click")
                for node in ast.walk(tree)
            ):
                errors.append(f"non-CLI module imports Click: {module_name}")

    edges = discover_internal_edges(source_texts)
    if edges != CURRENT_INTERNAL_EDGES:
        errors.append(
            "internal dependency contract is stale: "
            f"added={sorted(edges - CURRENT_INTERNAL_EDGES)}, "
            f"removed={sorted(CURRENT_INTERNAL_EDGES - edges)}"
        )
    forbidden_edges = set()
    for source, target in edges:
        source_domain = owners.get(source)
        target_domain = owners.get(target)
        if (
            source_domain is None
            or target_domain is None
            or source_domain == target_domain
        ):
            continue
        if target_domain not in DOMAIN_DEPENDENCIES[source_domain]:
            forbidden_edges.add((source, target))
    if forbidden_edges != LEGACY_FORBIDDEN_EDGES:
        errors.append(
            "legacy dependency debt contract is stale: "
            f"added={sorted(forbidden_edges - LEGACY_FORBIDDEN_EDGES)}, "
            f"removed={sorted(LEGACY_FORBIDDEN_EDGES - forbidden_edges)}"
        )
    errors.extend(_cycle_errors(edges))

    for module_name, limits in debt.items():
        source = source_texts.get(module_name)
        if source is None:
            continue
        actual = _top_level_counts(source)
        mismatch = {
            key: (actual[key], limit)
            for key, limit in limits.items()
            if actual[key] != limit
        }
        if mismatch:
            errors.append(
                f"legacy facade debt contract is stale in {module_name}: {mismatch}"
            )
    errors.extend(validate_artifact_contract(owners))
    return errors
