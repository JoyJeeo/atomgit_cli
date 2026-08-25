"""Declarative ownership and dependency contract for structural refactors."""

import ast
from collections import defaultdict
from pathlib import Path


CANONICAL_FIRST_LEVEL_DIRECTORIES = frozenset(
    {
        "adapters",
        "compatibility",
        "core",
        "domain",
        "infrastructure",
        "interfaces",
        "usecases",
    }
)

# Root modules are intentionally finite: each is either a package entry shim
# or a compatibility surface that cannot live below a responsibility package.
ROOT_COMPATIBILITY_PYTHON_ALLOWLIST = frozenset(
    {
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
)


def validate_physical_layout(repository_root):
    """Return errors when the source tree escapes the seven-layer contract."""

    package_root = Path(repository_root) / "src" / "atomgit"
    directories = {
        path.name
        for path in package_root.iterdir()
        if path.is_dir() and path.name != "__pycache__"
    }
    errors = []
    if directories != set(CANONICAL_FIRST_LEVEL_DIRECTORIES):
        errors.append(
            "first-level directory contract mismatch: "
            f"unexpected={sorted(directories - set(CANONICAL_FIRST_LEVEL_DIRECTORIES))}, "
            f"missing={sorted(set(CANONICAL_FIRST_LEVEL_DIRECTORIES) - directories)}"
        )
    root_python = {path.name for path in package_root.glob("*.py")}
    unexpected_root = root_python - set(ROOT_COMPATIBILITY_PYTHON_ALLOWLIST)
    if unexpected_root:
        errors.append(
            "root compatibility Python allowlist mismatch: "
            f"unexpected={sorted(unexpected_root)}"
        )
    return errors

PRODUCTION_MODULE_OWNERS = {
    "__init__": "facade",
    "__main__": "facade",
    "adapters.__init__": "adapters",
    "adapters.atomgit_v5": "adapters",
    "adapters.config": "adapters",
    "adapters.download.__init__": "adapters",
    "adapters.download.integrity": "adapters",
    "adapters.download.manifest": "adapters",
    "adapters.download.prune": "adapters",
    "adapters.download.resume": "adapters",
    "adapters.download.service": "adapters",
    "adapters.download.transport": "adapters",
    "adapters.huggingface": "adapters",
    "adapters.lfs.__init__": "adapters",
    "adapters.lfs.pointer": "adapters",
    "adapters.lfs.service": "adapters",
    "adapters.sdk_common": "adapters",
    "adapters.sdk_datasets": "adapters",
    "adapters.sdk_downloads": "adapters",
    "adapters.sdk_errors": "adapters",
    "adapters.sdk_repositories": "adapters",
    "adapters.sdk_uploads": "adapters",
    "adapters.upload.__init__": "adapters",
    "adapters.upload.contracts": "adapters",
    "adapters.upload.errors": "adapters",
    "adapters.upload.ordinary": "adapters",
    "adapters.upload.projection": "adapters",
    "adapters.upload.resumable": "adapters",
    "adapters.upload.service": "adapters",
    "api": "facade",
    "api.__init__": "facade",
    "atomgit_hub": "compatibility",
    "cli": "facade",
    "cli.__init__": "facade",
    "cli.__main__": "facade",
    "cli_contracts": "compatibility",
    "compatibility.__init__": "compatibility",
    "compatibility.authentication": "compatibility",
    "compatibility.api": "facade",
    "compatibility.cli": "facade",
    "compatibility.download": "compatibility",
    "compatibility.facade": "compatibility",
    "compatibility.legacy_packages": "compatibility",
    "compatibility.registry": "compatibility",
    "compatibility.repositories": "compatibility",
    "core.__init__": "core",
    "core.contracts": "core",
    "core.errors": "core",
    "core.parity": "core",
    "core.policies": "core",
    "core.ports": "core",
    "domain.__init__": "domain",
    "domain.authentication": "domain",
    "domain.repositories": "domain",
    "domain.transfers": "domain",
    "completion": "compatibility",
    "config": "infrastructure",
    "commands.__init__": "cli",
    "commands.authentication": "cli",
    "commands.lifecycle": "cli",
    "commands.repositories": "cli",
    "commands.transfers": "cli",
    "download.__init__": "compatibility",
    "download.integrity": "compatibility",
    "download.manifest": "compatibility",
    "download.prune": "compatibility",
    "download.resume": "compatibility",
    "download.service": "compatibility",
    "download.transport": "compatibility",
    "upload.__init__": "compatibility",
    "upload.contracts": "compatibility",
    "upload.errors": "compatibility",
    "upload.ordinary": "compatibility",
    "upload.projection": "compatibility",
    "upload.resumable": "compatibility",
    "upload.service": "compatibility",
    "exceptions": "infrastructure",
    "lfs_pointer": "compatibility",
    "release": "compatibility",
    "runtime": "infrastructure",
    "uninstaller": "compatibility",
    "utils": "infrastructure",
    "version": "infrastructure",
    "infrastructure.__init__": "infrastructure",
    "infrastructure.cache": "infrastructure",
    "infrastructure.completion": "infrastructure",
    "infrastructure.config": "infrastructure",
    "infrastructure.environment": "infrastructure",
    "infrastructure.filesystem": "infrastructure",
    "infrastructure.git_credentials": "infrastructure",
    "infrastructure.managed_paths": "infrastructure",
    "infrastructure.output": "infrastructure",
    "infrastructure.release": "distribution",
    "infrastructure.runtime": "infrastructure",
    "infrastructure.uninstall": "infrastructure",
    "infrastructure.utils": "infrastructure",
    "infrastructure.validation": "infrastructure",
    "interfaces.__init__": "interfaces",
    "interfaces.cli.__init__": "interfaces",
    "interfaces.cli.runner": "interfaces",
    "interfaces.cli.schema": "cli",
    "interfaces.cli.commands.__init__": "cli",
    "interfaces.cli.commands.authentication": "cli",
    "interfaces.cli.commands.lifecycle": "cli",
    "interfaces.cli.commands.repositories": "cli",
    "interfaces.cli.commands.transfers": "cli",
    "interfaces.sdk.__init__": "interfaces",
    "interfaces.sdk.client": "interfaces",
    "lifecycle.__init__": "compatibility",
    "lifecycle.completion": "compatibility",
    "lifecycle.environment": "compatibility",
    "lifecycle.managed_paths": "compatibility",
    "lifecycle.uninstall": "compatibility",
    "lfs.__init__": "compatibility",
    "lfs.service": "compatibility",
    "sdk.__init__": "compatibility",
    "sdk.common": "compatibility",
    "sdk.datasets": "compatibility",
    "sdk.downloads": "compatibility",
    "sdk.errors": "compatibility",
    "sdk.repositories": "compatibility",
    "sdk.uploads": "compatibility",
    "services.__init__": "compatibility",
    "services.authentication": "compatibility",
    "services.repositories": "compatibility",
    "usecases.__init__": "usecases",
    "usecases.authentication": "usecases",
    "usecases.repositories": "usecases",
    "usecases.transfers": "usecases",
}

DOMAIN_DEPENDENCIES = {
    "adapters": {
        "facade",
        "core",
        "infrastructure",
        "lfs",
        "transfers",
    },
    "compatibility": {"adapters", "core", "infrastructure", "interfaces", "usecases"},
    "core": set(),
    "facade": {
        "adapters",
        "cli",
        "compatibility",
        "transfers",
        "distribution",
        "infrastructure",
        "interfaces",
        "lfs",
    },
    "cli": {
        "compatibility",
        "interfaces",
        "transfers",
        "distribution",
        "infrastructure",
        "lfs",
    },
    "transfers": {"adapters", "infrastructure", "lfs"},
    "distribution": {"infrastructure"},
    "infrastructure": {"core"},
    "interfaces": {"adapters", "core", "infrastructure", "usecases"},
    "lfs": {"infrastructure"},
    "domain": {"core"},
    "usecases": {"core", "domain"},
}

# These edges are existing 1.1.1 debt. They may disappear but must never grow.
LEGACY_FORBIDDEN_EDGES = set()

CURRENT_INTERNAL_EDGES = {
    ("adapters.atomgit_v5", "infrastructure.config"),
    ("adapters.atomgit_v5", "infrastructure.validation"),
    ("adapters.config", "infrastructure.config"),
    ("adapters.download.__init__", "adapters.download.service"),
    ("adapters.download.integrity", "adapters.download.transport"),
    ("adapters.download.manifest", "adapters.download.prune"),
    ("adapters.download.manifest", "adapters.download.transport"),
    ("adapters.download.resume", "adapters.download.integrity"),
    ("adapters.download.resume", "adapters.download.transport"),
    ("adapters.download.service", "adapters.download.integrity"),
    ("adapters.download.service", "adapters.download.manifest"),
    ("adapters.download.service", "adapters.download.prune"),
    ("adapters.download.service", "adapters.download.resume"),
    ("adapters.download.service", "adapters.download.transport"),
    ("adapters.download.service", "infrastructure.validation"),
    ("adapters.download.transport", "infrastructure.validation"),
    ("adapters.huggingface", "api"),
    ("adapters.huggingface", "adapters.download.__init__"),
    ("adapters.huggingface", "adapters.lfs.pointer"),
    ("adapters.huggingface", "adapters.upload.service"),
    ("adapters.huggingface", "adapters.sdk_repositories"),
    ("adapters.huggingface", "adapters.sdk_uploads"),
    ("adapters.sdk_common", "infrastructure.config"),
    ("adapters.sdk_common", "infrastructure.validation"),
    ("adapters.sdk_datasets", "adapters.sdk_common"),
    ("adapters.sdk_datasets", "adapters.sdk_errors"),
    ("adapters.sdk_datasets", "infrastructure.utils"),
    ("adapters.sdk_downloads", "adapters.sdk_common"),
    ("adapters.sdk_downloads", "adapters.sdk_errors"),
    ("adapters.sdk_downloads", "infrastructure.utils"),
    ("adapters.sdk_errors", "adapters.lfs.pointer"),
    ("adapters.sdk_errors", "exceptions"),
    ("adapters.sdk_errors", "infrastructure.utils"),
    ("adapters.sdk_repositories", "adapters.sdk_common"),
    ("adapters.sdk_repositories", "adapters.sdk_errors"),
    ("adapters.sdk_repositories", "exceptions"),
    ("adapters.sdk_uploads", "adapters.lfs.pointer"),
    ("adapters.sdk_uploads", "exceptions"),
    ("adapters.sdk_uploads", "infrastructure.config"),
    ("adapters.sdk_uploads", "infrastructure.validation"),
    ("adapters.sdk_uploads", "adapters.sdk_errors"),
    ("adapters.upload.contracts", "core.contracts"),
    ("adapters.upload.errors", "adapters.upload.projection"),
    ("adapters.upload.errors", "infrastructure.validation"),
    ("adapters.upload.projection", "adapters.download.transport"),
    ("adapters.upload.resumable", "adapters.download.integrity"),
    ("adapters.upload.resumable", "adapters.download.transport"),
    ("adapters.upload.resumable", "adapters.lfs.pointer"),
    ("adapters.upload.resumable", "adapters.upload.contracts"),
    ("adapters.upload.resumable", "adapters.upload.errors"),
    ("adapters.upload.service", "adapters.lfs.pointer"),
    ("adapters.upload.service", "adapters.upload.contracts"),
    ("adapters.upload.service", "adapters.upload.errors"),
    ("adapters.upload.service", "adapters.upload.ordinary"),
    ("adapters.upload.service", "adapters.upload.projection"),
    ("adapters.upload.service", "adapters.upload.resumable"),
    ("adapters.upload.service", "infrastructure.config"),
    ("adapters.upload.service", "infrastructure.validation"),
    ("__init__", "api"),
    ("__init__", "atomgit_hub"),
    ("__init__", "compatibility.legacy_packages"),
    ("__init__", "cli"),
    ("__init__", "config"),
    ("__init__", "runtime"),
    ("__init__", "version"),
    ("__main__", "cli"),
    ("atomgit_hub", "exceptions"),
    ("atomgit_hub", "runtime"),
    ("atomgit_hub", "adapters.sdk_datasets"),
    ("atomgit_hub", "adapters.sdk_downloads"),
    ("atomgit_hub", "adapters.sdk_repositories"),
    ("atomgit_hub", "adapters.sdk_uploads"),
    ("cli.__init__", "compatibility.__init__"),
    ("cli.__init__", "compatibility.facade"),
    ("cli", "compatibility.__init__"),
    ("cli", "compatibility.facade"),
    ("cli.__main__", "compatibility.cli"),
    ("interfaces.cli.__init__", "interfaces.cli.runner"),
    ("interfaces.cli.runner", "adapters.__init__"),
    ("interfaces.cli.runner", "adapters.download.service"),
    ("interfaces.cli.runner", "infrastructure.validation"),
    ("interfaces.cli.runner", "interfaces.sdk.__init__"),
    ("interfaces.cli.schema", "cli_contracts"),
    ("interfaces.cli.schema", "interfaces.cli.commands.__init__"),
    ("interfaces.cli.commands.__init__", "interfaces.cli.commands.authentication"),
    ("interfaces.cli.commands.__init__", "interfaces.cli.commands.lifecycle"),
    ("interfaces.cli.commands.__init__", "interfaces.cli.commands.repositories"),
    ("interfaces.cli.commands.__init__", "interfaces.cli.commands.transfers"),
    ("compatibility.__init__", "compatibility.registry"),
    ("compatibility.api", "adapters.download.__init__"),
    ("compatibility.api", "adapters.lfs.__init__"),
    ("compatibility.api", "adapters.lfs.pointer"),
    ("compatibility.api", "adapters.lfs.service"),
    ("compatibility.api", "adapters.upload.__init__"),
    ("compatibility.api", "adapters.upload.service"),
    ("compatibility.api", "cli_contracts"),
    ("compatibility.api", "compatibility.__init__"),
    ("compatibility.api", "compatibility.authentication"),
    ("compatibility.api", "compatibility.download"),
    ("compatibility.api", "compatibility.facade"),
    ("compatibility.api", "compatibility.repositories"),
    ("compatibility.api", "config"),
    ("compatibility.api", "runtime"),
    ("compatibility.api", "utils"),
    ("compatibility.authentication", "adapters.atomgit_v5"),
    ("compatibility.authentication", "infrastructure.config"),
    ("compatibility.cli", "api"),
    ("compatibility.cli", "cli_contracts"),
    ("compatibility.cli", "completion"),
    ("compatibility.cli", "config"),
    ("compatibility.cli", "interfaces.cli.__init__"),
    ("compatibility.cli", "interfaces.cli.schema"),
    ("compatibility.cli", "release"),
    ("compatibility.cli", "runtime"),
    ("compatibility.cli", "uninstaller"),
    ("compatibility.cli", "utils"),
    ("compatibility.cli", "version"),
    ("compatibility.download", "adapters.download.service"),
    ("compatibility.download", "infrastructure.config"),
    ("compatibility.download", "infrastructure.validation"),
    ("compatibility.repositories", "adapters.atomgit_v5"),
    ("compatibility.repositories", "infrastructure.config"),
    ("compatibility.repositories", "infrastructure.validation"),
    ("compatibility.registry", "core.parity"),
    ("core.__init__", "core.contracts"),
    ("core.__init__", "core.parity"),
    ("core.__init__", "core.policies"),
    ("core.policies", "core.errors"),
    ("completion", "compatibility.facade"),
    ("completion", "infrastructure.__init__"),
    ("completion", "infrastructure.completion"),
    ("domain.__init__", "domain.authentication"),
    ("domain.__init__", "domain.repositories"),
    ("domain.__init__", "domain.transfers"),
    ("domain.authentication", "core.errors"),
    ("domain.repositories", "core.contracts"),
    ("domain.repositories", "core.policies"),
    ("domain.transfers", "core.contracts"),
    ("domain.transfers", "core.policies"),
    ("infrastructure.completion", "infrastructure.environment"),
    ("infrastructure.completion", "infrastructure.managed_paths"),
    ("infrastructure.environment", "infrastructure.managed_paths"),
    ("infrastructure.uninstall", "infrastructure.environment"),
    ("infrastructure.uninstall", "infrastructure.managed_paths"),
    ("release", "infrastructure.__init__"),
    ("infrastructure.release", "infrastructure.environment"),
    ("config", "infrastructure.config"),
    ("config", "infrastructure.__init__"),
    ("infrastructure.git_credentials", "infrastructure.output"),
    ("infrastructure.utils", "infrastructure.cache"),
    ("infrastructure.utils", "infrastructure.filesystem"),
    ("infrastructure.utils", "infrastructure.git_credentials"),
    ("infrastructure.utils", "infrastructure.output"),
    ("infrastructure.utils", "infrastructure.validation"),
    ("interfaces.sdk.__init__", "interfaces.sdk.client"),
    ("interfaces.sdk.client", "adapters.__init__"),
    ("interfaces.sdk.client", "core.contracts"),
    ("interfaces.sdk.client", "core.errors"),
    ("interfaces.sdk.client", "core.policies"),
    ("interfaces.sdk.client", "infrastructure.config"),
    ("interfaces.sdk.client", "usecases.authentication"),
    ("interfaces.sdk.client", "usecases.repositories"),
    ("interfaces.sdk.client", "usecases.transfers"),
    ("runtime", "infrastructure.runtime"),
    ("runtime", "infrastructure.__init__"),
    ("sdk.__init__", "sdk.datasets"),
    ("sdk.__init__", "sdk.downloads"),
    ("sdk.__init__", "sdk.repositories"),
    ("sdk.__init__", "sdk.uploads"),
    ("uninstaller", "compatibility.facade"),
    ("uninstaller", "infrastructure.__init__"),
    ("uninstaller", "infrastructure.uninstall"),
    ("utils", "infrastructure.utils"),
    ("utils", "infrastructure.__init__"),
    ("cli_contracts", "core.contracts"),
    ("exceptions", "core.errors"),
    ("usecases.__init__", "usecases.authentication"),
    ("usecases.__init__", "usecases.repositories"),
    ("usecases.__init__", "usecases.transfers"),
    ("usecases.authentication", "core.contracts"),
    ("usecases.authentication", "core.ports"),
    ("usecases.authentication", "domain.authentication"),
    ("usecases.repositories", "core.contracts"),
    ("usecases.repositories", "core.policies"),
    ("usecases.repositories", "core.ports"),
    ("usecases.repositories", "domain.repositories"),
    ("usecases.transfers", "core.contracts"),
    ("usecases.transfers", "core.policies"),
    ("usecases.transfers", "core.ports"),
    ("usecases.transfers", "domain.transfers"),
}

LEGACY_FACADE_DEBT = {
    "api": {"max_lines": 6, "max_functions": 0, "max_classes": 0},
    "api.__init__": {"max_lines": 6, "max_functions": 0, "max_classes": 0},
    "atomgit_hub": {"max_lines": 168, "max_functions": 2, "max_classes": 0},
    "cli": {"max_lines": 27, "max_functions": 0, "max_classes": 0},
    "cli.__init__": {"max_lines": 23, "max_functions": 0, "max_classes": 0},
    "cli.__main__": {"max_lines": 6, "max_functions": 0, "max_classes": 0},
    "compatibility.api": {"max_lines": 781, "max_functions": 0, "max_classes": 1},
    "compatibility.cli": {"max_lines": 139, "max_functions": 3, "max_classes": 1},
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
    "atomgit/api.py",
    "atomgit/api/__init__.py",
    "atomgit/atomgit_hub.py",
    "atomgit/cli.py",
    "atomgit/cli/__init__.py",
    "atomgit/cli/__main__.py",
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
    "atomgit/infrastructure/release.py",
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
    "src/atomgit/api.py",
    "src/atomgit/api/__init__.py",
    "src/atomgit/atomgit_hub.py",
    "src/atomgit/cli.py",
    "src/atomgit/cli/__init__.py",
    "src/atomgit/cli/__main__.py",
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
    "src/atomgit/infrastructure/release.py",
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

_NEW_ARCHITECTURE_MODULES = {
    "adapters/__init__.py",
    "adapters/atomgit_v5.py",
    "adapters/config.py",
    "adapters/download/__init__.py",
    "adapters/download/integrity.py",
    "adapters/download/manifest.py",
    "adapters/download/prune.py",
    "adapters/download/resume.py",
    "adapters/download/service.py",
    "adapters/download/transport.py",
    "adapters/huggingface.py",
    "adapters/lfs/__init__.py",
    "adapters/lfs/pointer.py",
    "adapters/lfs/service.py",
    "adapters/sdk_common.py",
    "adapters/sdk_datasets.py",
    "adapters/sdk_downloads.py",
    "adapters/sdk_errors.py",
    "adapters/sdk_repositories.py",
    "adapters/sdk_uploads.py",
    "adapters/upload/__init__.py",
    "adapters/upload/contracts.py",
    "adapters/upload/errors.py",
    "adapters/upload/ordinary.py",
    "adapters/upload/projection.py",
    "adapters/upload/resumable.py",
    "adapters/upload/service.py",
    "compatibility/__init__.py",
    "compatibility/authentication.py",
    "compatibility/api.py",
    "compatibility/cli.py",
    "compatibility/download.py",
    "compatibility/facade.py",
    "compatibility/legacy_packages.py",
    "compatibility/registry.py",
    "compatibility/repositories.py",
    "core/__init__.py",
    "core/contracts.py",
    "core/errors.py",
    "core/parity.py",
    "core/policies.py",
    "core/ports.py",
    "domain/__init__.py",
    "domain/authentication.py",
    "domain/repositories.py",
    "domain/transfers.py",
    "infrastructure/completion.py",
    "infrastructure/environment.py",
    "infrastructure/managed_paths.py",
    "infrastructure/uninstall.py",
    "interfaces/__init__.py",
    "interfaces/cli/__init__.py",
    "interfaces/cli/runner.py",
    "interfaces/cli/schema.py",
    "interfaces/cli/commands/__init__.py",
    "interfaces/cli/commands/authentication.py",
    "interfaces/cli/commands/lifecycle.py",
    "interfaces/cli/commands/repositories.py",
    "interfaces/cli/commands/transfers.py",
    "interfaces/sdk/__init__.py",
    "interfaces/sdk/client.py",
    "usecases/__init__.py",
    "usecases/authentication.py",
    "usecases/repositories.py",
    "usecases/transfers.py",
}
EXPECTED_WHEEL_FILES.update("atomgit/" + path for path in _NEW_ARCHITECTURE_MODULES)
EXPECTED_SDIST_FILES.update("src/atomgit/" + path for path in _NEW_ARCHITECTURE_MODULES)


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
                if (
                    not node.module
                    and resolve_module(base) is not None
                    and not any(resolve_module(candidate) for candidate in candidates)
                ):
                    candidates.append(base)
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
        if module_name == "compatibility.cli" and "_lazy_utility(" in source:
            edges.add(("compatibility.cli", "utils"))
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
        if owners.get(module_name) != "cli" and module_name != "compatibility.cli":
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
