"""Historical environment-uninstaller compatibility facade."""

# ruff: noqa: F401

import subprocess
import sys
import types

from .lifecycle import _delete_legacy_patch, _forward_legacy_patch
from .lifecycle import environment as _environment
from .lifecycle import managed_paths as _managed_paths
from .lifecycle import uninstall as _implementation
from .lifecycle.uninstall import *  # noqa: F401,F403

MANAGED_COMPLETION_RELATIVE_PATHS = _managed_paths.MANAGED_COMPLETION_RELATIVE_PATHS
UninstallError = _managed_paths.UninstallError
os = _environment.os
stat = _managed_paths.stat
_is_source_or_editable_install = _implementation._is_source_or_editable_install
_resolved_directory = _environment._resolved_directory
active_conda_prefix = _environment.active_conda_prefix
managed_completion_paths = _managed_paths.managed_completion_paths
_fingerprint = _managed_paths._fingerprint
_managed_parent_exists = _managed_paths._managed_parent_exists
remove_managed_completion = _managed_paths.remove_managed_completion


_PATCH_TARGETS = {
    "importlib": (_implementation,),
    "os": (_environment,),
    "Path": (_environment, _managed_paths, _implementation),
    "stat": (_managed_paths,),
    "subprocess": (_implementation,),
    "sys": (_environment, _implementation),
    "MANAGED_COMPLETION_RELATIVE_PATHS": (_managed_paths,),
    "UninstallError": (_managed_paths, _environment, _implementation),
    "_resolved_directory": (_environment,),
    "_is_source_or_editable_install": (_implementation,),
    "is_source_or_editable_install": (_environment, _implementation),
    "active_conda_prefix": (_implementation,),
    "managed_completion_paths": (_managed_paths, _implementation),
    "_fingerprint": (_managed_paths,),
    "_managed_parent_exists": (_managed_paths,),
    "remove_managed_completion": (_managed_paths, _implementation),
    "build_uninstall_plan": (_implementation,),
    "run_uninstall": (_implementation,),
}


_FacadeModule = type(
    "_FacadeModule",
    (types.ModuleType,),
    {"__setattr__": _forward_legacy_patch, "__delattr__": _delete_legacy_patch},
)
sys.modules[__name__].__class__ = _FacadeModule
