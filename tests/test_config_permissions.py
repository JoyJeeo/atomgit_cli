#!/usr/bin/env python3
"""Verify credential permissions using only isolated temporary homes."""

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

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
            from atomgit.config import Config
            config_module = sys.modules["atomgit.config"]

            check("T1 import does not create config directory",
                  not (fresh_home / ".atomgit").exists())
            fresh = Config()
            check("T2 constructor does not create config directory",
                  not fresh.config_dir.exists())
            check("T3 absent config read stays side-effect free",
                  fresh.get_credentials() is None and not fresh.config_dir.exists())
            fresh.set_credentials("fake-token-never-print")
            check("T4 fresh directory mode=0700", mode(fresh.config_dir) == 0o700,
                  oct(mode(fresh.config_dir)))
            check("T5 fresh config mode=0600", mode(fresh.config_file) == 0o600,
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
            check("T6 constructor does not mutate existing permissions",
                  mode(config_dir) == 0o755 and mode(config_file) == 0o644)
            loaded = existing.is_logged_in()
            check("T7 existing directory migrated to 0700",
                  mode(config_dir) == 0o700, oct(mode(config_dir)))
            check("T8 existing config migrated before use",
                  mode(config_file) == 0o600, oct(mode(config_file)))
            check("T9 existing credentials remain readable", loaded)

            original_bytes = config_file.read_bytes()
            with patch.object(
                config_module.os,
                "replace",
                side_effect=OSError("offline replace failure"),
            ):
                try:
                    existing.set_credentials("replacement-token-never-print")
                    replace_failed = False
                except Exception:
                    replace_failed = True
            check("T10 replacement failure is reported", replace_failed)
            check("T11 replacement failure preserves disk state",
                  config_file.read_bytes() == original_bytes)
            check("T12 replacement failure preserves memory state",
                  existing.get_credentials() == {"token": "fake-existing-token"})
            check("T13 replacement failure cleans temporary files",
                  not list(config_dir.glob(".config.json.*.tmp")))

            config_file.chmod(0o644)
            existing.set_value("test", True)
            check("T14 subsequent save restores 0600",
                  mode(config_file) == 0o600, oct(mode(config_file)))

            unusable_home = Path(td) / "home-is-a-file"
            unusable_home.write_text("not a directory", encoding="utf-8")
            environment = os.environ.copy()
            environment["HOME"] = str(unusable_home)
            help_result = subprocess.run(
                [sys.executable, "-m", "atomgit", "--help"],
                cwd=str(Path(__file__).resolve().parents[1]),
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
            )
            check("T15 help tolerates unusable HOME", help_result.returncode == 0,
                  help_result.stderr[-200:])
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
