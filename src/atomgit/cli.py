"""Historical CLI import and module-execution shim."""

import sys
import types

from .compatibility import cli as _owner
from .compatibility.facade import _delete_legacy_patch, _forward_legacy_patch

for _name, _value in vars(_owner).items():
    if not _name.startswith("__"):
        globals()[_name] = _value

_PATCH_TARGETS = {
    name: (_owner,)
    for name in vars(_owner)
    if not name.startswith("__") and name != "_PATCH_TARGETS"
}
_FacadeModule = type(
    "_FacadeModule",
    (types.ModuleType,),
    {"__setattr__": _forward_legacy_patch, "__delattr__": _delete_legacy_patch},
)

if __name__ == "__main__":
    _owner.cli()
else:
    sys.modules[__name__].__class__ = _FacadeModule
