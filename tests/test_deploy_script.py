#!/usr/bin/env python3
"""Offline contracts for local packaging helpers."""

import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "deploy.sh"
RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append((name, condition, detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))


def run(root, environment, command):
    return subprocess.run(
        ["bash", str(root / "deploy.sh"), command],
        cwd=str(root),
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )


def main():
    with tempfile.TemporaryDirectory(prefix="atomgit-deploy-contract-") as directory:
        root = Path(directory)
        (root / "deploy.sh").write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
        (root / "deploy.sh").chmod(0o755)
        env = os.environ.copy()
        help_result = run(root, env, "help")
        check("help works without conda", help_result.returncode == 0)
        rejected = run(root, env, "build")
        check("build rejects missing conda", rejected.returncode != 0)

        conda = root / "conda"
        (conda / "bin").mkdir(parents=True)
        log = root / "python.log"
        fake = conda / "bin" / "python"
        fake.write_text(
            "#!/bin/sh\n"
            "printf '%s\\n' \"$*\" >> \"$DEPLOY_TEST_LOG\"\n"
            "case \"$*\" in *'pip show atomgit'*) printf 'Version: 1.0.6\\nLocation: /fake\\n' ;; esac\n"
            "exit 0\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        env.update({"CONDA_PREFIX": str(conda), "DEPLOY_TEST_LOG": str(log)})

        dist = root / "dist"
        dist.mkdir()
        wheel = dist / "atomgit-1.0.6-py3-none-any.whl"
        wheel.write_bytes(b"wheel")
        install_result = run(root, env, "install")
        check("offline local install succeeds", install_result.returncode == 0, install_result.stderr)
        check("install uses target python pip", "-m pip install" in log.read_text(encoding="utf-8"))

        checksum_result = run(root, env, "checksums")
        check("checksum helper succeeds", checksum_result.returncode == 0)
        check("checksum asset is generated", (dist / "SHA256SUMS").exists())

        deploy_text = (root / "deploy.sh").read_text(encoding="utf-8")
        check("legacy PyPI path is absent", all(token not in deploy_text for token in ("twine", "atomgitsdktoken", "pypi")))

        log.write_text("", encoding="utf-8")
        build_result = run(root, env, "build")
        check("offline local build succeeds", build_result.returncode == 0)
        check("build invokes python -m build", "-m build" in log.read_text(encoding="utf-8"))

    return 0 if all(condition for _, condition, _ in RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
