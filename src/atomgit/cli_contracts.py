"""Historical CLI path for lightweight upload contracts."""

from .upload.contracts import (
    _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_UPLOAD_BATCH_SIZE,
)

__all__ = ("_RESUMABLE_DEFAULT_REQUEST_TIMEOUT", "DEFAULT_UPLOAD_BATCH_SIZE")
