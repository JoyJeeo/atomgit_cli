"""Outbound adapter implementations for locked dependencies and V5."""

from .atomgit_v5 import AtomGitV5Adapter
from .huggingface import HuggingFaceAdapter

__all__ = ["AtomGitV5Adapter", "HuggingFaceAdapter"]
