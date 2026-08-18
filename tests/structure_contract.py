"""Declarative ownership and dependency contract for structural refactors."""

import ast
from collections import defaultdict
from pathlib import Path


PRODUCTION_MODULE_OWNERS = {
    "__init__": "facade",
    "__main__": "cli",
    "api": "facade",
    "atomgit_hub": "sdk",
    "cli": "cli",
    "cli_contracts": "cli",
    "completion": "lifecycle",
    "config": "infrastructure",
    "exceptions": "infrastructure",
    "lfs_pointer": "lfs",
    "release": "distribution",
    "runtime": "infrastructure",
    "uninstaller": "lifecycle",
    "utils": "infrastructure",
    "version": "infrastructure",
}

DOMAIN_DEPENDENCIES = {
    "facade": {
        "cli", "sdk", "services", "transfers", "lifecycle", "distribution",
        "infrastructure", "lfs",
    },
    "cli": {
        "services", "transfers", "lifecycle", "distribution",
        "infrastructure", "lfs",
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
    ("cli", "api"),
    ("uninstaller", "release"),
}

CURRENT_INTERNAL_EDGES = {
    ("__init__", "api"),
    ("__init__", "atomgit_hub"),
    ("__init__", "cli"),
    ("__init__", "config"),
    ("__init__", "runtime"),
    ("__init__", "version"),
    ("__main__", "cli"),
    ("api", "cli_contracts"),
    ("api", "config"),
    ("api", "lfs_pointer"),
    ("api", "runtime"),
    ("api", "utils"),
    ("atomgit_hub", "config"),
    ("atomgit_hub", "exceptions"),
    ("atomgit_hub", "lfs_pointer"),
    ("atomgit_hub", "runtime"),
    ("atomgit_hub", "utils"),
    ("cli", "api"),
    ("cli", "cli_contracts"),
    ("cli", "completion"),
    ("cli", "config"),
    ("cli", "release"),
    ("cli", "runtime"),
    ("cli", "uninstaller"),
    ("cli", "utils"),
    ("cli", "version"),
    ("completion", "uninstaller"),
    ("uninstaller", "release"),
}

LEGACY_FACADE_DEBT = {
    "api": {"max_lines": 5496, "max_functions": 121, "max_classes": 21},
    "atomgit_hub": {"max_lines": 734, "max_functions": 10, "max_classes": 0},
    "cli": {"max_lines": 908, "max_functions": 26, "max_classes": 1},
    "utils": {"max_lines": 861, "max_functions": 45, "max_classes": 0},
}

PUBLIC_IMPORTS = (
    "atomgit",
    "atomgit.api",
    "atomgit.cli",
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
    "atomgit/api.py",
    "atomgit/atomgit_hub.py",
    "atomgit/cli.py",
    "atomgit/cli_contracts.py",
    "atomgit/completion.py",
    "atomgit/config.py",
    "atomgit/exceptions.py",
    "atomgit/lfs_pointer.py",
    "atomgit/release.py",
    "atomgit/runtime.py",
    "atomgit/uninstaller.py",
    "atomgit/utils.py",
    "atomgit/version.py",
    "atomgit_hub.py",
}

EXPECTED_SDIST_FILES = {
    "__init__.py",
    "__main__.py",
    "api.py",
    "atomgit_hub.py",
    "cli.py",
    "cli_contracts.py",
    "completion.py",
    "config.py",
    "exceptions.py",
    "lfs_pointer.py",
    "release.py",
    "runtime.py",
    "uninstaller.py",
    "utils.py",
    "version.py",
}


def _module_name(path):
    return path.stem


def discover_source_texts(repository_root):
    return {
        _module_name(path): path.read_text(encoding="utf-8")
        for path in sorted(Path(repository_root).glob("*.py"))
        if path.name != "setup.py"
    }


def discover_internal_edges(source_texts):
    module_names = set(source_texts)
    edges = set()
    for module_name, source in source_texts.items():
        tree = ast.parse(source, filename=f"{module_name}.py")
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                candidates = (
                    [node.module.split(".")[0]]
                    if node.module
                    else [alias.name.split(".")[0] for alias in node.names]
                )
                edges.update(
                    (module_name, candidate)
                    for candidate in candidates
                    if candidate in module_names
                )
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"_LazyObject", "_import_runtime_module"}
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value in module_names
            ):
                edges.add((module_name, node.args[0].value))
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
    expected_package_files = {f"atomgit/{module}.py" for module in owners}
    expected_wheel = expected_package_files | {"atomgit_hub.py"}
    expected_sdist = {f"{module}.py" for module in owners}
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
                (isinstance(node, ast.Import) and any(a.name == "click" for a in node.names))
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
        if source_domain is None or target_domain is None or source_domain == target_domain:
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
