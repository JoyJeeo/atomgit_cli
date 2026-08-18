"""Owned authentication and repository service implementations."""

import types


def _forward_legacy_patch(module, name, value):
    for target in module._PATCH_TARGETS.get(name, ()):
        setattr(target, name, value)
    types.ModuleType.__setattr__(module, name, value)


def _delete_legacy_patch(module, name):
    for target in module._PATCH_TARGETS.get(name, ()):
        if hasattr(target, name):
            delattr(target, name)
    types.ModuleType.__delattr__(module, name)


__all__ = ("authentication", "repositories")
