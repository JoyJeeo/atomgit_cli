#!/usr/bin/env python3
"""Verify credential permissions using only isolated temporary homes."""

import json
import os
import stat
import sys
import tempfile
from pathlib import Path

results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def mode(path):
    return stat.S_IMODE(path.stat().st_mode)


def main():
    original_home = os.environ.get("HOME")
    try:
        with tempfile.TemporaryDirectory() as td:
            fresh_home = Path(td) / "fresh"
            fresh_home.mkdir()
            os.environ["HOME"] = str(fresh_home)
            # Import only after HOME is isolated because the module owns a
            # process-global Config instance.
            from atomgit.config import Config

            fresh = Config()
            fresh.set_credentials("fake-token-never-print")
            check("T1 fresh directory mode=0700", mode(fresh.config_dir) == 0o700,
                  oct(mode(fresh.config_dir)))
            check("T2 fresh config mode=0600", mode(fresh.config_file) == 0o600,
                  oct(mode(fresh.config_file)))

            existing_home = Path(td) / "existing"
            config_dir = existing_home / ".atomgit"
            config_dir.mkdir(parents=True, mode=0o755)
            config_file = config_dir / "config.json"
            config_file.write_text(
                json.dumps({"token": "fake-existing-token"}), encoding="utf-8"
            )
            config_dir.chmod(0o755)
            config_file.chmod(0o644)
            os.environ["HOME"] = str(existing_home)
            existing = Config()
            check("T3 existing directory migrated to 0700",
                  mode(config_dir) == 0o700, oct(mode(config_dir)))
            check("T4 existing config migrated before use",
                  mode(config_file) == 0o600, oct(mode(config_file)))
            check("T5 existing credentials remain readable",
                  existing.is_logged_in())

            config_file.chmod(0o644)
            existing.set_value("test", True)
            check("T6 subsequent save restores 0600",
                  mode(config_file) == 0o600, oct(mode(config_file)))
    finally:
        if original_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = original_home

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
