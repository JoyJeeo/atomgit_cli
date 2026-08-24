"""Outbound adapter exports with lazy loading for schema-only imports."""

from importlib import import_module

_EXPORTS = {
    "AtomGitDownloadAdapter": (".download", "AtomGitDownloadAdapter"),
    "AtomGitV5Adapter": (".atomgit_v5", "AtomGitV5Adapter"),
    "HuggingFaceAdapter": (".huggingface", "HuggingFaceAdapter"),
}


def __getattr__(name):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    value = getattr(import_module(target[0], __name__), target[1])
    globals()[name] = value
    return value


__all__ = tuple(_EXPORTS)
