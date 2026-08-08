#!/usr/bin/env python3
"""Offline installer tests using a local Release mirror and fake conda Python."""

import hashlib
import os
import subprocess
import tempfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPOSITORY_ROOT / "install.sh"
VERSION = "1.0.6"
PACKAGE_VERSION = "1.0.6"
WHEEL_NAME = f"atomgit-{PACKAGE_VERSION}-py3-none-any.whl"
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def run_installer(environment, *arguments):
    return subprocess.run(
        ["sh", str(INSTALLER), *arguments],
        cwd=str(REPOSITORY_ROOT),
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        release = root / f"v{VERSION}"
        release.mkdir()
        wheel = release / WHEEL_NAME
        wheel.write_bytes(b"offline-wheel-content")
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        checksums = release / "SHA256SUMS"
        checksums.write_text(f"{digest}  {WHEEL_NAME}\n", encoding="utf-8")

        conda_prefix = root / "conda"
        bin_dir = conda_prefix / "bin"
        bin_dir.mkdir(parents=True)
        invocation_log = root / "python-invocation.txt"
        fake_python = bin_dir / "python"
        fake_python.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$*\" > \"$ATOMGIT_INSTALL_TEST_LOG\"\n",
            encoding="utf-8",
        )
        fake_python.chmod(0o755)

        environment = os.environ.copy()
        environment.update(
            {
                "CONDA_PREFIX": str(conda_prefix),
                "ATOMGIT_INSTALL_BASE_URL": release.parent.as_uri(),
                "ATOMGIT_INSTALL_TEST_LOG": str(invocation_log),
            }
        )
        success = run_installer(environment)
        check("default version install succeeds", success.returncode == 0, success.stderr)
        invocation = invocation_log.read_text(encoding="utf-8")
        check("active conda Python runs pip", invocation.startswith("-m pip install "))
        check("fixed wheel name is installed", WHEEL_NAME in invocation)
        check("success reports checksum verification", "Checksum verified" in success.stdout)

        invocation_log.unlink()
        explicit = run_installer(environment, "--version", VERSION)
        check("explicit valid version succeeds", explicit.returncode == 0, explicit.stderr)
        check("explicit version invokes pip", invocation_log.exists())

        invocation_log.unlink()
        checksums.write_text(f"{'0' * 64}  {WHEEL_NAME}\n", encoding="utf-8")
        corrupt = run_installer(environment, "--version", VERSION)
        check("corrupt checksum fails", corrupt.returncode != 0)
        check("corrupt checksum never invokes pip", not invocation_log.exists())

        invalid = run_installer(environment, "--version", "../latest")
        check("invalid version fails", invalid.returncode == 2)
        check("invalid version never invokes pip", not invocation_log.exists())

        no_conda_environment = environment.copy()
        no_conda_environment.pop("CONDA_PREFIX")
        no_conda = run_installer(no_conda_environment)
        check("missing conda fails", no_conda.returncode != 0)
        check("missing conda explains activation", "activate" in no_conda.stderr)
        check("missing conda never invokes pip", not invocation_log.exists())

        help_result = run_installer(no_conda_environment, "--help")
        check("help works without conda", help_result.returncode == 0)

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
