"""Historical shell-completion compatibility facade."""

# ruff: noqa: F401

import os
import sys
import types

from .lifecycle import _delete_legacy_patch, _forward_legacy_patch
from .lifecycle import completion as _implementation
from .lifecycle import environment as _environment
from .lifecycle import managed_paths as _managed_paths
from .lifecycle.completion import *  # noqa: F401,F403

_COMPLETE_VAR = _implementation._COMPLETE_VAR
_PROGRAM_NAME = _implementation._PROGRAM_NAME
_START_MARKER = _implementation._START_MARKER
_END_MARKER = _implementation._END_MARKER
_FINAL_NEWLINE_MARKER = _implementation._FINAL_NEWLINE_MARKER
_UNSET = _implementation._UNSET
_ACTIVATION_WARNING = _implementation._ACTIVATION_WARNING
_completion_path = _implementation._completion_path
_active_conda_prefix = _implementation._active_conda_prefix
_ensure_managed_directory = _implementation._ensure_managed_directory
_activation_hook = _implementation._activation_hook
_deactivation_hook = _implementation._deactivation_hook
_zshrc_path = _implementation._zshrc_path
_ensure_directory = _implementation._ensure_directory
_file_fingerprint = _implementation._file_fingerprint
_read_snapshot = _implementation._read_snapshot
_atomic_write = _implementation._atomic_write
_write_backup_once = _implementation._write_backup_once
_remove_if_unchanged = _implementation._remove_if_unchanged
_split_managed_block = _implementation._split_managed_block
_managed_block = _implementation._managed_block
_remove_legacy_completion = _implementation._remove_legacy_completion


_PATCH_TARGETS = {
    "os": (_implementation,),
    "Path": (_implementation,),
    "get_completion_class": (_implementation,),
    "shlex": (_implementation,),
    "stat": (_implementation,),
    "sys": (_implementation,),
    "tempfile": (_implementation,),
    "active_conda_prefix": (_implementation,),
    "managed_completion_paths": (_implementation,),
    "remove_managed_completion": (_implementation,),
    "UninstallError": (_implementation,),
    **{
        name: (_implementation,)
        for name in (
            "SUPPORTED_SHELLS",
            "CompletionConfigError",
            "completion_script",
            "_COMPLETE_VAR",
            "_PROGRAM_NAME",
            "_START_MARKER",
            "_END_MARKER",
            "_FINAL_NEWLINE_MARKER",
            "_UNSET",
            "_ACTIVATION_WARNING",
            "_completion_path",
            "_active_conda_prefix",
            "_ensure_managed_directory",
            "_activation_hook",
            "_deactivation_hook",
            "_zshrc_path",
            "_ensure_directory",
            "_file_fingerprint",
            "_read_snapshot",
            "_atomic_write",
            "_write_backup_once",
            "_remove_if_unchanged",
            "_split_managed_block",
            "_managed_block",
            "legacy_completion_present",
            "_remove_legacy_completion",
            "install_completion",
            "uninstall_completion",
        )
    },
}


_FacadeModule = type(
    "_FacadeModule",
    (types.ModuleType,),
    {"__setattr__": _forward_legacy_patch, "__delattr__": _delete_legacy_patch},
)
sys.modules[__name__].__class__ = _FacadeModule
