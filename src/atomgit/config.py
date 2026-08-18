"""Historical configuration import facade."""

import os  # noqa: F401

from .infrastructure import config as _implementation
from .infrastructure.config import *  # noqa: F401,F403

_FACADE_TARGET = _implementation
_is_safe_credential_text = _implementation._is_safe_credential_text
_set_private_file_mode = _implementation._set_private_file_mode
