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
        (atomgit_dir / "config.json").write_text(
            json.dumps(
                {
                    "token": "fake-token-never-print",
                    "username": "offline-user",
                }
            )
        )
        helper = atomgit_dir / "git-credential-atomgit"
        env = dict(os.environ, HOME=str(home))
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
            source = helper.read_text()
            output_lines = result.stdout.splitlines()
            checks = [
                ("helper returns cached username", "username=offline-user" in output_lines),
                (
                    "helper returns stored token as password",
                    "password=fake-token-never-print" in output_lines,
                ),
                (
                    "helper source performs no network lookup",
                    "urllib" not in source
                    and "urlopen" not in source
                    and "https://atomgit.com/api/v5/user" not in source,
                ),
            ]

            (atomgit_dir / "config.json").write_text(
                json.dumps({"token": "fake-token-never-print"})
            )
            missing_identity = subprocess.run(
                [str(helper), "get"],
                input="protocol=https\nhost=atomgit.com\n\n",
                text=True,
                capture_output=True,
                env=env,
            )
            checks.append(
                (
                    "missing cached username returns no credentials",
                    missing_identity.returncode == 0
                    and missing_identity.stdout == "",
                )
            )
            for label, unsafe_config in (
                (
                    "unsafe cached username is rejected",
                    {
                        "token": "fake-token-never-print",
                        "username": "offline-user\npassword=injected",
                    },
                ),
                (
                    "unsafe cached token is rejected",
                    {
                        "token": "fake-token-never-print\nusername=injected",
                        "username": "offline-user",
                    },
                ),
            ):
                (atomgit_dir / "config.json").write_text(json.dumps(unsafe_config))
                unsafe_result = subprocess.run(
                    [str(helper), "get"],
                    input="protocol=https\nhost=atomgit.com\n\n",
                    text=True,
                    capture_output=True,
                    env=env,
                )
                checks.append(
                    (
                        label,
                        unsafe_result.returncode == 0 and unsafe_result.stdout == "",
                    )
                )
            passed = 0
            for name, condition in checks:
                print(f"[{'PASS' if condition else 'FAIL'}] {name}")
                passed += bool(condition)
            print(f"summary: {passed}/{len(checks)} passed")
            return 0 if passed == len(checks) else 1
        finally:
            utils.clear_git_credentials()
            if original_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = original_home


if __name__ == "__main__":
    raise SystemExit(main())
