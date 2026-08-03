#!/usr/bin/env python3
"""Dataset resumable/LFS guard prevents known unsupported remote calls."""
import tempfile
from pathlib import Path
import sys
import atomgit  # noqa: F401


def main():
    api_mod = sys.modules["atomgit.api"]
    cfg = sys.modules["atomgit.config"].config
    cfg.get_credentials = lambda: {"token": "fake-token-never-print"}
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "dataset"
        root.mkdir()
        (root / "data.csv").write_text("x\n")
        result = api_mod.api.upload_directory(root, "user/dataset", repo_type="dataset", resumable=True)
    ok = result is False
    print(f"[{'PASS' if ok else 'FAIL'}] dataset resumable upload rejected clearly")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
