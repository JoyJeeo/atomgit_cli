"""Historical release import facade."""

import sys
import types

from .infrastructure import release as _implementation

# Keep every established release symbol available at its historical path.
for _name in dir(_implementation):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_implementation, _name)


def _forward_release_patch(module, name, value):
    if name in {"_implementation", "__all__"} or name.startswith("__"):
        types.ModuleType.__setattr__(module, name, value)
    else:
        setattr(_implementation, name, value)
        types.ModuleType.__setattr__(module, name, value)


def _delete_release_patch(module, name):
    if name in {"_implementation", "__all__"} or name.startswith("__"):
        types.ModuleType.__delattr__(module, name)
    else:
        if hasattr(_implementation, name):
            delattr(_implementation, name)
        types.ModuleType.__delattr__(module, name)


_module = sys.modules[__name__]
_module.__class__ = type(
    "_ReleaseCompatibilityModule",
    (types.ModuleType,),
    {"__setattr__": _forward_release_patch, "__delattr__": _delete_release_patch},
)


if __name__ == "__main__":
    raise SystemExit(_main())  # noqa: F821 -- forwarded owner symbol
