"""Historical runtime-policy import facade."""

from atomgit.infrastructure import runtime as _implementation
from atomgit.infrastructure.runtime import *  # noqa: F401,F403

_FACADE_TARGET = _implementation
