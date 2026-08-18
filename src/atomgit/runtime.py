"""Historical runtime-policy import facade."""

from .infrastructure import runtime as _implementation
from .infrastructure.runtime import *  # noqa: F401,F403

_FACADE_TARGET = _implementation
