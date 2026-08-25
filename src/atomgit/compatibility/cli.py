#!/usr/bin/env python3
# ruff: noqa: F401 -- historical CLI assignment and monkeypatch surface
"""Historical CLI compatibility facade and Click context."""

import importlib
import sys
from getpass import getpass
from pathlib import Path

import click

try:
    from ..infrastructure.runtime import configure_hf_environment
    from .facade import _install_legacy_cli_main
except ImportError:
    from compatibility.facade import _install_legacy_cli_main
    from infrastructure.runtime import configure_hf_environment

configure_hf_environment()

try:
    from ..core.contracts import (
        _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
        DEFAULT_UPLOAD_BATCH_SIZE,
    )
    from ..infrastructure.completion import (
        CompletionConfigError,
        completion_script,
        install_completion,
        legacy_completion_present,
        uninstall_completion,
    )
    from ..infrastructure.config import config
    from ..infrastructure.managed_paths import UninstallError
    from ..infrastructure.release import ReleaseError, is_stable_version, run_update
    from ..infrastructure.uninstall import build_uninstall_plan, run_uninstall
    from ..infrastructure.version import __version__
except ImportError:
    from core.contracts import (
        _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
        DEFAULT_UPLOAD_BATCH_SIZE,
    )
    from infrastructure.completion import (
        CompletionConfigError,
        completion_script,
        install_completion,
        legacy_completion_present,
        uninstall_completion,
    )
    from infrastructure.config import config
    from infrastructure.managed_paths import UninstallError
    from infrastructure.release import ReleaseError, is_stable_version, run_update
    from infrastructure.uninstall import build_uninstall_plan, run_uninstall
    from infrastructure.version import __version__


_COMMAND_CONTEXT = sys.modules[__name__]


def _import_runtime_module(name):
    if name == "utils":
        name = "infrastructure.utils"
    if __package__:
        return importlib.import_module(f"..{name}", __package__)
    return importlib.import_module(name)


class _LazyObject:
    """Preserve patchable CLI globals without importing their runtime module."""

    def __init__(self, module_name, attribute_name, prepend_context=False):
        object.__setattr__(self, "_module_name", module_name)
        object.__setattr__(self, "_attribute_name", attribute_name)
        object.__setattr__(self, "_prepend_context", prepend_context)

    def _resolve(self):
        module = _import_runtime_module(object.__getattribute__(self, "_module_name"))
        return getattr(module, object.__getattribute__(self, "_attribute_name"))

    def __getattr__(self, name):
        return getattr(self._resolve(), name)

    def __setattr__(self, name, value):
        setattr(self._resolve(), name, value)

    def __delattr__(self, name):
        delattr(self._resolve(), name)

    def __call__(self, *args, **kwargs):
        if object.__getattribute__(self, "_prepend_context"):
            args = (sys.modules[__name__],) + args
        return self._resolve()(*args, **kwargs)


api = _LazyObject("api", "api")
run_usecase = _LazyObject("interfaces.cli", "run", prepend_context=True)


def _lazy_utility(name):
    def call(*args, **kwargs):
        return getattr(_import_runtime_module("utils"), name)(*args, **kwargs)

    call.__name__ = name
    return call


for _utility_name in (
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "validate_repo_name",
    "is_supported_upload_revision",
    "format_file_size",
    "get_upload_file_stats",
    "clear_atomgit_cache",
    "is_valid_path",
    "ensure_directory",
    "setup_git_credentials",
    "clear_git_credentials",
    "check_git_available",
    "normalize_path_in_repo",
    "parse_ignore_patterns",
    "effective_cli_upload_ignore_patterns",
    "is_macos_metadata_file",
    "get_atomgit_git_helper_status",
    "validate_upload_path_no_symlinks",
):
    globals()[_utility_name] = _lazy_utility(_utility_name)


from ..interfaces.cli.schema import build_cli  # noqa: E402


def cli():
    """Placeholder retained for the historical facade's source contract."""


cli = build_cli(_COMMAND_CONTEXT)  # noqa: F811


if __name__ == "__main__":
    cli()
