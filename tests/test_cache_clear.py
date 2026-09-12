#!/usr/bin/env python3
"""Verify the cache clear shortcut is scoped to the AtomGit HF cache."""
import os
import tempfile
from pathlib import Path
from click.testing import CliRunner

from atomgit.cli import cli


def main():
    with tempfile.TemporaryDirectory(prefix="atomgit-cache-test-") as td:
        root = Path(td) / "hf-home"
        root.mkdir()
        (root / "upload-projections").mkdir()
        (root / "upload-projections" / "payload.bin").write_bytes(b"cache")
        pending = (
            root
            / "upload-projections"
            / ".cache"
            / "huggingface"
            / "atomgit"
            / "pending-commit-v1.json"
        )
        pending.parent.mkdir(parents=True)
        pending.write_text("pending", encoding="utf-8")
        (root / "hub-cache.json").write_text("cache", encoding="utf-8")
        environment = os.environ.get("HF_HOME")
        os.environ["HF_HOME"] = str(root)
        try:
            result = CliRunner().invoke(cli, ["cache", "clear"])
        finally:
            if environment is None:
                os.environ.pop("HF_HOME", None)
            else:
                os.environ["HF_HOME"] = environment
        ok = (
            result.exit_code == 0
            and root.is_dir()
            and not any(root.iterdir())
        )
        print(f"[{'PASS' if ok else 'FAIL'}] cache clear exit={result.exit_code}")
        if not ok:
            print(result.output)
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
