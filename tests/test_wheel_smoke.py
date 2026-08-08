#!/usr/bin/env python3
"""Build and install the current wheel entirely in temporary directories."""

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from email.parser import BytesParser
from importlib.metadata import metadata, version
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "1.0.6"
SOURCE_FILES = (
    "__init__.py",
    "__main__.py",
    "api.py",
    "atomgit_hub.py",
    "cli.py",
    "config.py",
    "exceptions.py",
    "utils.py",
    "setup.py",
    "requirements.txt",
    "runtime.py",
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "MANIFEST.in",
    "install.sh",
)
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def run(command, cwd, environment=None):
    return subprocess.run(
        [str(part) for part in command],
        cwd=str(cwd),
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
    )


def repository_artifact_state():
    state = []
    for pattern in ("build", "dist", "*.egg-info"):
        for artifact in REPOSITORY_ROOT.glob(pattern):
            if artifact.is_file():
                paths = [artifact]
            else:
                paths = [path for path in artifact.rglob("*") if path.is_file()]
            for path in paths:
                stat = path.stat()
                state.append(
                    (str(path.relative_to(REPOSITORY_ROOT)), stat.st_size, stat.st_mtime_ns)
                )
    return sorted(state)


def main():
    artifacts_before = repository_artifact_state()
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        source = root / "source"
        dist = root / "dist"
        venv = root / "venv"
        source.mkdir()
        dist.mkdir()
        for relative_name in SOURCE_FILES:
            shutil.copy2(REPOSITORY_ROOT / relative_name, source / relative_name)

        build_result = run(
            [sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", dist],
            source,
        )
        check("temporary wheel build succeeds", build_result.returncode == 0, build_result.stderr[-500:])
        wheels = list(dist.glob("*.whl"))
        check("exactly one wheel produced", len(wheels) == 1)
        if not wheels:
            return 1

        with zipfile.ZipFile(wheels[0]) as wheel_archive:
            metadata_names = [
                name for name in wheel_archive.namelist()
                if name.endswith(".dist-info/METADATA")
            ]
            check("wheel contains one METADATA file", len(metadata_names) == 1)
            wheel_metadata = BytesParser().parsebytes(
                wheel_archive.read(metadata_names[0])
            )
        classifiers = wheel_metadata.get_all("Classifier", [])
        check(
            "wheel requires Python 3.9 or newer",
            wheel_metadata.get("Requires-Python") == ">=3.9",
            repr(wheel_metadata.get("Requires-Python")),
        )
        check(
            "wheel classifiers omit Python 3.8 and retain Python 3.9",
            "Programming Language :: Python :: 3.8" not in classifiers
            and "Programming Language :: Python :: 3.9" in classifiers,
            repr(classifiers),
        )
        dependency_minimums = {
            dependency: metadata(dependency).get("Requires-Python")
            for dependency in ("huggingface-hub", "datasets")
        }
        check(
            "locked dependencies independently require Python 3.9",
            version("huggingface-hub") == "1.1.7"
            and version("datasets") == "4.4.1"
            and dependency_minimums
            == {"huggingface-hub": ">=3.9.0", "datasets": ">=3.9.0"},
            repr(dependency_minimums),
        )

        venv_result = run(
            [sys.executable, "-m", "venv", "--system-site-packages", venv],
            root,
        )
        check("temporary venv creation succeeds", venv_result.returncode == 0, venv_result.stderr[-500:])
        bin_dir = venv / ("Scripts" if os.name == "nt" else "bin")
        venv_python = bin_dir / ("python.exe" if os.name == "nt" else "python")
        atomgit_command = bin_dir / ("atomgit.exe" if os.name == "nt" else "atomgit")

        install_result = run(
            [venv_python, "-m", "pip", "install", "--no-deps", wheels[0]],
            root,
        )
        check("wheel installation succeeds", install_result.returncode == 0, install_result.stderr[-500:])

        environment = os.environ.copy()
        smoke_home = root / "home"
        smoke_home.mkdir()
        environment["HOME"] = str(smoke_home)
        checks = [
            ("console version", [atomgit_command, "--version"], EXPECTED_VERSION),
            ("console help", [atomgit_command, "--help"], "Commands:"),
            ("module help", [venv_python, "-m", "atomgit", "--help"], "Commands:"),
            (
                "installed imports",
                [
                    venv_python,
                    "-c",
                    (
                        "import pathlib, sys, atomgit, atomgit_hub; "
                        "prefix = str(pathlib.Path(sys.prefix).resolve()); "
                        "assert str(pathlib.Path(atomgit.__file__).resolve()).startswith(prefix); "
                        "assert str(pathlib.Path(atomgit_hub.__file__).resolve()).startswith(prefix); "
                        "print('installed-wheel', atomgit.__version__)"
                    ),
                ],
                "installed-wheel " + EXPECTED_VERSION,
            ),
        ]
        for command in (
            ("login",),
            ("logout",),
            ("whoami",),
            ("repo",),
            ("repo", "create"),
            ("upload",),
            ("download",),
            ("config-show",),
        ):
            label = " ".join(command)
            checks.append(
                (
                    f"installed {label} help",
                    [atomgit_command, *command, "--help"],
                    "Usage:",
                )
            )
        for name, command, marker in checks:
            result = run(command, root, environment)
            check(
                f"{name} succeeds",
                result.returncode == 0 and marker in result.stdout,
                (result.stdout + result.stderr)[-500:],
            )

    check(
        "repository build artifacts remain unchanged",
        repository_artifact_state() == artifacts_before,
    )
    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
