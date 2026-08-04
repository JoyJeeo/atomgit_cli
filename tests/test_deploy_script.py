#!/usr/bin/env python3
"""Deployment shell commands remain conda-explicit and offline-testable."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = REPOSITORY_ROOT / "deploy.sh"
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def run(root, environment, command, input_text=None):
    return subprocess.run(
        ["bash", "deploy.sh", command],
        cwd=str(root),
        env=environment,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=30,
    )


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        shutil.copy2(DEPLOY_SCRIPT, root / "deploy.sh")
        environment = os.environ.copy()
        environment.pop("CONDA_PREFIX", None)

        help_result = run(root, environment, "help")
        check("help works without conda", help_result.returncode == 0)

        dist = root / "dist"
        dist.mkdir()
        sentinel = dist / "keep.whl"
        sentinel.write_bytes(b"keep")
        rejected = run(root, environment, "build")
        check("build rejects missing conda", rejected.returncode != 0)
        check("rejected build preserves dist", sentinel.exists())

        conda = root / "conda"
        bin_dir = conda / "bin"
        bin_dir.mkdir(parents=True)
        log = root / "python.log"
        fake_python = bin_dir / "python"
        fake_python.write_text(
            (
                "#!/bin/sh\n"
                "printf '%s\\n' \"$*\" >> \"$DEPLOY_TEST_LOG\"\n"
                "case \"$*\" in *'pip show atomgit'*) "
                "printf 'Version: 1.0.5+yuto.1\\nLocation: /fake\\n' ;; esac\n"
            ),
            encoding="utf-8",
        )
        fake_python.chmod(0o755)
        environment.update(
            {"CONDA_PREFIX": str(conda), "DEPLOY_TEST_LOG": str(log)}
        )

        install_result = run(root, environment, "install")
        check("offline install command succeeds", install_result.returncode == 0)
        install_log = log.read_text(encoding="utf-8")
        check("uninstall uses conda python -m pip", "-m pip uninstall atomgit -y" in install_log)
        check("install uses conda python -m pip", "-m pip install dist/keep.whl" in install_log)
        check("version lookup uses conda python -m pip", "-m pip show atomgit" in install_log)

        log.write_text("", encoding="utf-8")
        environment["atomgitsdktoken"] = "fake-publish-token"
        twine_result = run(root, environment, "twine", input_text="y\n")
        check("offline twine command succeeds", twine_result.returncode == 0)
        twine_log = log.read_text(encoding="utf-8")
        check("twine uses conda python module", "-m twine upload dist/keep.whl" in twine_log)
        check("token is absent from command arguments", "fake-publish-token" not in twine_log)

        log.write_text("", encoding="utf-8")
        caller = root / "caller"
        caller_dist = caller / "dist"
        caller_dist.mkdir(parents=True)
        caller_sentinel = caller_dist / "caller.whl"
        caller_sentinel.write_bytes(b"caller")
        build_result = subprocess.run(
            ["bash", str(root / "deploy.sh"), "build"],
            cwd=str(caller),
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        check("offline build command succeeds", build_result.returncode == 0)
        check("build uses conda python module", "-m build" in log.read_text(encoding="utf-8"))
        check(
            "build cleanup is confined to script directory",
            not sentinel.exists() and caller_sentinel.exists(),
        )

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
