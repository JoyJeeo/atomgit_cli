#!/usr/bin/env python3
"""Offline tests for generated Git helper identity behavior."""
import json
import os
import subprocess
import tempfile
from pathlib import Path


def main():
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        atomgit_dir = home / ".atomgit"
        atomgit_dir.mkdir(mode=0o700)
        (atomgit_dir / "config.json").write_text(json.dumps({"token": "fake-token-never-print"}))
        helper = atomgit_dir / "git-credential-atomgit"
        env = dict(os.environ, HOME=str(home))
        env["ATOMGIT_IDENTITY_MODE"] = "success"
        original_home = os.environ.get("HOME")
        os.environ["HOME"] = str(home)
        from atomgit import utils
        try:
            # Reuse the production script template by installing credentials.
            assert utils.setup_git_credentials("fake-token-never-print")
            result = subprocess.run(
                [str(helper), "get"], input="protocol=https\nhost=atomgit.com\n\n",
                text=True, capture_output=True, env=env)
            if result.returncode != 0:
                print("[FAIL] helper exits successfully")
                return 1
            # The generated helper imports its own function, so verify the
            # script's auth scheme and ensure no fallback identity remains.
            source = helper.read_text()
            ok = "'Authorization': token" in source and "atomgit-user" not in source
            print(f"[{'PASS' if ok else 'FAIL'}] helper uses raw token and no fake fallback")
            return 0 if ok else 1
        finally:
            utils.clear_git_credentials()
            if original_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = original_home


if __name__ == "__main__":
    raise SystemExit(main())
