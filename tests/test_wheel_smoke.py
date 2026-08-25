#!/usr/bin/env python3
"""Build and install the current wheel entirely in temporary directories."""

import os
import re
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import tempfile
import zipfile
from email.parser import BytesParser
from importlib.metadata import metadata, version
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIRECTORY = Path(__file__).resolve().parent
if str(TESTS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TESTS_DIRECTORY))

from structure_contract import EXPECTED_SDIST_FILES, EXPECTED_WHEEL_FILES  # noqa: E402

VERSION_TEXT = (REPOSITORY_ROOT / "src" / "atomgit" / "version.py").read_text(encoding="utf-8")
EXPECTED_VERSION = re.search(r'__version__\s*=\s*["\']([^"\']+)', VERSION_TEXT).group(1)
SOURCE_FILES = tuple(sorted(EXPECTED_SDIST_FILES)) + (
    "setup.py",
    "requirements.txt",
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "MANIFEST.in",
    "pyproject.toml",
    "install.sh",
    "uninstall.sh",
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
                    (
                        str(path.relative_to(REPOSITORY_ROOT)),
                        stat.st_size,
                        stat.st_mtime_ns,
                    )
                )
    return sorted(state)


def main():
    artifacts_before = repository_artifact_state()
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        source = root / "source"
        dist = root / "dist"
        venv = root / "venv"
        editable_venv = root / "editable-venv"
        source.mkdir()
        dist.mkdir()
        for relative_name in SOURCE_FILES:
            destination = source / relative_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPOSITORY_ROOT / relative_name, destination)

        build_result = run(
            [
                sys.executable,
                "-m",
                "build",
                "--wheel",
                "--sdist",
                "--no-isolation",
                "--outdir",
                dist,
            ],
            source,
        )
        check(
            "temporary wheel build succeeds",
            build_result.returncode == 0,
            build_result.stderr[-500:],
        )
        wheels = list(dist.glob("*.whl"))
        check("exactly one wheel produced", len(wheels) == 1)
        sdists = list(dist.glob("*.tar.gz"))
        check("exactly one sdist produced", len(sdists) == 1)
        if not wheels:
            return 1

        with zipfile.ZipFile(wheels[0]) as wheel_archive:
            wheel_names = set(wheel_archive.namelist())
            metadata_names = [
                name for name in wheel_names if name.endswith(".dist-info/METADATA")
            ]
            check("wheel contains one METADATA file", len(metadata_names) == 1)
            actual_wheel_files = {
                name
                for name in wheel_names
                if name.endswith(".py") and ".dist-info/" not in name
            }
            check(
                "wheel contains exactly the intended runtime Python modules",
                actual_wheel_files == EXPECTED_WHEEL_FILES,
                repr(
                    {
                        "missing": sorted(EXPECTED_WHEEL_FILES - actual_wheel_files),
                        "extra": sorted(actual_wheel_files - EXPECTED_WHEEL_FILES),
                    }
                ),
            )
            wheel_metadata = BytesParser().parsebytes(
                wheel_archive.read(metadata_names[0])
            )
        if sdists:
            with tarfile.open(sdists[0], "r:gz") as sdist_archive:
                sdist_names = {
                    name.split("/", 1)[1]
                    for name in sdist_archive.getnames()
                    if "/" in name
                }
            actual_sdist_files = {
                name for name in sdist_names if name.endswith(".py") and name != "setup.py"
            }
            check(
                "sdist contains exactly the intended runtime source modules",
                actual_sdist_files == EXPECTED_SDIST_FILES,
                repr(
                    {
                        "missing": sorted(EXPECTED_SDIST_FILES - actual_sdist_files),
                        "extra": sorted(actual_sdist_files - EXPECTED_SDIST_FILES),
                    }
                ),
            )
            required_sdist_metadata = {"MANIFEST.in", "pyproject.toml", "setup.py"}
            check(
                "sdist preserves build metadata and legacy entrypoint",
                required_sdist_metadata <= sdist_names,
                repr(sorted(required_sdist_metadata - sdist_names)),
            )
        classifiers = wheel_metadata.get_all("Classifier", [])
        check(
            "wheel declares the stable development status",
            "Development Status :: 5 - Production/Stable" in classifiers
            and "Development Status :: 4 - Beta" not in classifiers,
            repr(classifiers),
        )
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
        check(
            "temporary venv creation succeeds",
            venv_result.returncode == 0,
            venv_result.stderr[-500:],
        )
        bin_dir = venv / ("Scripts" if os.name == "nt" else "bin")
        venv_python = bin_dir / ("python.exe" if os.name == "nt" else "python")
        atomgit_command = bin_dir / ("atomgit.exe" if os.name == "nt" else "atomgit")

        install_result = run(
            [venv_python, "-m", "pip", "install", "--no-deps", wheels[0]],
            root,
        )
        check(
            "wheel installation succeeds",
            install_result.returncode == 0,
            install_result.stderr[-500:],
        )

        environment = os.environ.copy()
        smoke_home = root / "home"
        smoke_home.mkdir()
        environment["HOME"] = str(smoke_home)
        checks = [
            ("console version", [atomgit_command, "--version"], EXPECTED_VERSION),
            ("console help", [atomgit_command, "--help"], "Commands:"),
            ("module help", [venv_python, "-m", "atomgit", "--help"], "Commands:"),
            (
                "CLI package module help",
                [venv_python, "-m", "atomgit.cli", "--help"],
                "Commands:",
            ),
            (
                "installed imports",
                [
                    venv_python,
                    "-c",
                    (
                        "import importlib, pathlib, sys, atomgit, atomgit_hub; "
                        "prefix = str(pathlib.Path(sys.prefix).resolve()); "
                        "modules=(atomgit, atomgit_hub) + tuple(importlib.import_module(n) "
                        "for n in ('atomgit.api', 'atomgit.cli', 'atomgit.cli.__main__', 'atomgit.utils', "
                        "'atomgit.completion', 'atomgit.uninstaller', "
                        "'atomgit.release', 'atomgit.lfs_pointer', "
                        "'atomgit.compatibility.authentication', "
                        "'atomgit.compatibility.download', "
                        "'atomgit.compatibility.repositories', "
                        "'atomgit.adapters.sdk_common', "
                        "'atomgit.adapters.sdk_datasets', "
                        "'atomgit.adapters.sdk_downloads', "
                        "'atomgit.adapters.sdk_errors', "
                        "'atomgit.adapters.sdk_repositories', "
                        "'atomgit.adapters.sdk_uploads', "
                        "'atomgit.infrastructure.completion', "
                        "'atomgit.infrastructure.environment', "
                        "'atomgit.infrastructure.managed_paths', "
                        "'atomgit.infrastructure.uninstall', "
                        "'atomgit.infrastructure.validation', "
                        "'atomgit.infrastructure.git_credentials', "
                        "'atomgit.lifecycle.completion', "
                        "'atomgit.lifecycle.environment', "
                        "'atomgit.lifecycle.managed_paths', "
                        "'atomgit.lifecycle.uninstall', "
                        "'atomgit.services.authentication', "
                        "'atomgit.services.repositories')); "
                        "assert all(str(pathlib.Path(m.__file__).resolve()).startswith(prefix) "
                        "for m in modules); "
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
            ("update",),
            ("uninstall",),
            ("repo",),
            ("repo", "create"),
            ("completion",),
            ("completion", "show"),
            ("completion", "install"),
            ("completion", "uninstall"),
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

        uninstall_result = run(
            [venv_python, "-m", "pip", "uninstall", "--yes", "atomgit"],
            root,
        )
        check(
            "temporary wheel uninstall succeeds before editable smoke",
            uninstall_result.returncode == 0,
            uninstall_result.stderr[-500:],
        )
        editable_venv_result = run(
            [sys.executable, "-m", "venv", editable_venv],
            root,
        )
        check(
            "isolated editable venv creation succeeds",
            editable_venv_result.returncode == 0,
            editable_venv_result.stderr[-500:],
        )
        editable_bin = editable_venv / ("Scripts" if os.name == "nt" else "bin")
        editable_python = editable_bin / ("python.exe" if os.name == "nt" else "python")
        editable_environment = environment.copy()
        editable_environment["PYTHONPATH"] = sysconfig.get_paths()["purelib"]
        editable_result = run(
            [
                editable_python,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--no-build-isolation",
                "--editable",
                source,
            ],
            root,
            editable_environment,
        )
        check(
            "isolated editable installation succeeds",
            editable_result.returncode == 0,
            editable_result.stderr[-500:],
        )
        editable_probe = run(
            [
                editable_python,
                "-c",
                (
                    "import importlib, pathlib; import atomgit, atomgit_hub; "
                    "root=pathlib.Path(%r).resolve(); "
                    "modules=(atomgit, atomgit_hub, importlib.import_module('atomgit.release'), "
                    "importlib.import_module('atomgit.lfs_pointer'), "
                    "importlib.import_module('atomgit.compatibility.authentication'), "
                    "importlib.import_module('atomgit.compatibility.download'), "
                    "importlib.import_module('atomgit.compatibility.repositories'), "
                    "importlib.import_module('atomgit.adapters.sdk_common'), "
                    "importlib.import_module('atomgit.adapters.sdk_datasets'), "
                    "importlib.import_module('atomgit.adapters.sdk_downloads'), "
                    "importlib.import_module('atomgit.adapters.sdk_errors'), "
                    "importlib.import_module('atomgit.adapters.sdk_repositories'), "
                    "importlib.import_module('atomgit.adapters.sdk_uploads'), "
                    "importlib.import_module('atomgit.infrastructure.completion'), "
                    "importlib.import_module('atomgit.infrastructure.environment'), "
                    "importlib.import_module('atomgit.infrastructure.managed_paths'), "
                    "importlib.import_module('atomgit.infrastructure.uninstall'), "
                    "importlib.import_module('atomgit.infrastructure.validation'), "
                    "importlib.import_module('atomgit.lifecycle.completion'), "
                    "importlib.import_module('atomgit.lifecycle.environment'), "
                    "importlib.import_module('atomgit.lifecycle.managed_paths'), "
                    "importlib.import_module('atomgit.lifecycle.uninstall'), "
                    "importlib.import_module('atomgit.services.authentication'), "
                    "importlib.import_module('atomgit.services.repositories')); "
                    "invalid=[str(pathlib.Path(m.__file__).resolve()) for m in modules "
                    "if root not in pathlib.Path(m.__file__).resolve().parents]; "
                    "assert not invalid, invalid; print('installed-editable', atomgit.__version__)"
                    % str(source)
                ),
            ],
            root,
            editable_environment,
        )
        check(
            "editable imports resolve only from the isolated source tree",
            editable_probe.returncode == 0
            and "installed-editable " + EXPECTED_VERSION in editable_probe.stdout,
            (editable_probe.stdout + editable_probe.stderr)[-500:],
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
