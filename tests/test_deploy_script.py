#!/usr/bin/env python3
"""Offline contracts for local packaging helpers."""

import os
import subprocess
import tempfile
import zipfile
from pathlib import Path

from atomgit import __version__ as VERSION
from atomgit.release import validate_release_assets


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
            f"case \"$*\" in *'pip show atomgit'*) printf 'Version: {VERSION}\\nLocation: /fake\\n' ;; esac\n"
            "exit 0\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        env.update({"CONDA_PREFIX": str(conda), "DEPLOY_TEST_LOG": str(log)})

        dist = root / "dist"
        dist.mkdir()
        wheel = dist / f"atomgit-{VERSION}-py3-none-any.whl"
        with zipfile.ZipFile(wheel, "w") as archive:
            archive.writestr(
                f"atomgit-{VERSION}.dist-info/METADATA",
                f"Metadata-Version: 2.1\nName: atomgit\nVersion: {VERSION}\n",
            )
        install_result = run(root, env, "install")
        check("offline local install succeeds", install_result.returncode == 0, install_result.stderr)
        check("install uses target python pip", "-m pip install" in log.read_text(encoding="utf-8"))

        checksum_result = run(root, env, "checksums")
        check("checksum helper succeeds", checksum_result.returncode == 0)
        check("checksum asset is generated", (dist / "SHA256SUMS").exists())
        checksum_text = (dist / "SHA256SUMS").read_text(encoding="utf-8")
        check(
            "checksum uses the exact Release asset name",
            validate_release_assets(wheel, checksum_text, VERSION),
        )

        deploy_text = (root / "deploy.sh").read_text(encoding="utf-8")
        check("legacy PyPI path is absent", all(token not in deploy_text for token in ("twine", "atomgitsdktoken", "pypi")))

        log.write_text("", encoding="utf-8")
        build_result = run(root, env, "build")
        check("offline local build succeeds", build_result.returncode == 0)
        check("build invokes python -m build", "-m build" in log.read_text(encoding="utf-8"))

    return 0 if all(condition for _, condition, _ in RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
