#!/usr/bin/env python3
"""Offline contracts for the ordinary-user Release bootstrap."""

import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.sh"
RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append((name, condition, detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))


def run(environment, *arguments):
    return subprocess.run(
        ["sh", str(INSTALLER), *arguments],
        cwd=str(ROOT),
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )


def main():
    with tempfile.TemporaryDirectory(prefix="atomgit-installer-contract-") as directory:
        root = Path(directory)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        log = root / "python.log"
        fake_python = bin_dir / "python"
        fake_python.write_text(
            "#!/bin/sh\n"
            "printf '%s\\n' \"$*\" >> \"$ATOMGIT_INSTALL_TEST_LOG\"\n"
            "if [ \"$ATOMGIT_INSTALL_TEST_COMPLETION_FAIL\" = 1 ] && [ \"$1 $2 $3\" = '-m atomgit completion' ]; then exit 1; fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        fake_python.chmod(0o755)
        environment = os.environ.copy()
        environment.update(
            {
                "CONDA_PREFIX": str(root / "missing-conda"),
                "ATOMGIT_INSTALL_TEST_LOG": str(log),
                "ATOMGIT_INSTALL_TEST_COMPLETION_FAIL": "0",
                "ATOMGIT_RELEASE_API_URL": "https://example.invalid/releases",
                "SHELL": "/bin/zsh",
                "HOME": str(root / "home"),
            }
        )
        (root / "home").mkdir()

        success = run(environment, "--python", str(fake_python), "--no-completion")
        check("explicit target Python is accepted", success.returncode == 0, success.stderr)
        invocations = log.read_text(encoding="utf-8").splitlines()
        check("bootstrap invokes target Python", any(line.startswith("-") for line in invocations), repr(invocations))
        check("bootstrap does not require conda", "activate" not in success.stderr.lower())

        log.unlink()
        completion = run(environment, "--python", str(fake_python))
        invocations = log.read_text(encoding="utf-8").splitlines()
        check("completion remains enabled by default", completion.returncode == 0 and any("completion install" in line for line in invocations))

        log.unlink()
        failed_completion_env = environment.copy()
        failed_completion_env["ATOMGIT_INSTALL_TEST_COMPLETION_FAIL"] = "1"
        failed_completion = run(failed_completion_env, "--python", str(fake_python))
        check("completion setup failure is nonfatal", failed_completion.returncode == 0)
        check("completion setup warning is visible", "warning:" in failed_completion.stderr)

        invalid = run(environment, "--python", str(fake_python), "--version", "v1.2.3")
        check("legacy v version is rejected", invalid.returncode == 1 or invalid.returncode == 2)
        source = run(environment, "--source")
        check("source installer mode is rejected", source.returncode == 2 and "git checkout yuto" in source.stderr)
        help_result = run({}, "--help")
        check("help works without a target environment", help_result.returncode == 0 and "--python" in help_result.stdout)

        text = INSTALLER.read_text(encoding="utf-8")
        check("installer uses structured JSON parsing", "json.loads" in text and "grep" not in text)
        check("installer never bypasses environment safety", all(token not in text for token in ("sudo", "--user", "--break-system-packages")))
        check("installer cleans a unique temporary directory", "mktemp -d" in text and "trap cleanup" in text)

    return 0 if all(condition for _, condition, _ in RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
