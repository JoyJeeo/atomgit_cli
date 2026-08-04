"""Shared Hugging Face runtime policy for AtomGit entry points."""

import os
from pathlib import Path


ATOMGIT_HF_ENDPOINT = "https://hub.atomgit.com"
ATOMGIT_DISABLE_XET = "1"


def configure_hf_environment() -> Path:
    """Apply AtomGit's idempotent Hugging Face process environment."""
    cache_dir = Path.home() / ".cache" / "atomgit"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["HF_ENDPOINT"] = ATOMGIT_HF_ENDPOINT
    os.environ["HF_HUB_DISABLE_XET"] = ATOMGIT_DISABLE_XET
    os.environ["HF_HOME"] = str(cache_dir)
    return cache_dir
