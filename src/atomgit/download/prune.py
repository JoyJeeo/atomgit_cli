# ruff: noqa: F401,F403 -- historical private import surface
"""Historical prune helper path backed by the canonical adapter."""

from ..adapters.download.prune import *  # noqa: F401,F403
from ..adapters.download.prune import (
    _normalized_windows_handle_path,
    _prune_managed_download_file,
    _prune_managed_download_file_windows,
    _prune_managed_download_files,
    _repository_filename_parts,
    _uses_windows_prune,
    _WindowsFileAPI,
)

__all__ = ()
