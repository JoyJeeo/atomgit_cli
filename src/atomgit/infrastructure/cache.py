"""AtomGit-owned cache lifecycle policy."""

import os
import shutil
from pathlib import Path


def clear_atomgit_cache() -> int:
    """Clear only the AtomGit-owned HF cache tree and return removed entries."""
    cache_root = Path(
        os.environ.get("HF_HOME", Path.home() / ".cache" / "atomgit")
    ).expanduser()
    resolved_root = cache_root.resolve(strict=False)
    unsafe_roots = {
        Path("/"),
        Path.home().resolve(strict=False),
        Path("/tmp"),
        Path("/private/tmp"),
    }
    if resolved_root in unsafe_roots or len(resolved_root.parts) <= 2:
        raise ValueError("AtomGit 缓存目录范围过大，已拒绝清理")
    if cache_root.exists() and (cache_root.is_symlink() or not cache_root.is_dir()):
        raise ValueError("AtomGit 缓存目录不是安全的普通目录")
    cache_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(cache_root, 0o700)
    removed = 0
    for child in list(cache_root.iterdir()):
        if child.is_symlink() or child.is_file():
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)
        else:
            continue
        removed += 1
    return removed
