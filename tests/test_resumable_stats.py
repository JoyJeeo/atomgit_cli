#!/usr/bin/env python3
"""Verify resumable metadata is excluded only from upload statistics."""
import tempfile
from pathlib import Path
from atomgit.utils import count_files_in_directory, get_directory_size


def main():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "model.bin").write_bytes(b"model")
        (root / ".cache" / "huggingface" / "upload").mkdir(parents=True)
        (root / ".cache" / "huggingface" / "upload" / "state.lock").write_bytes(b"x" * 100)
        (root / "nested" / ".cache").mkdir(parents=True)
        (root / "nested" / ".cache" / "user.bin").write_bytes(b"user")
        normal = (count_files_in_directory(root), get_directory_size(root))
        resumable = (count_files_in_directory(root, True), get_directory_size(root, True))
        ok = normal == (3, 109) and resumable == (2, 9)
        print(f"[{'PASS' if ok else 'FAIL'}] normal={normal} resumable={resumable}")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
