#!/usr/bin/env python3
"""Fail closed on the mechanical ``src`` layout and SDK shim contract."""

import ast
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "src" / "atomgit"
EXPECTED_FIRST_LEVEL_DIRECTORIES = {
    "adapters",
    "compatibility",
    "core",
    "domain",
    "infrastructure",
    "interfaces",
    "usecases",
}
ROOT_PYTHON_ALLOWLIST = {
    "__init__.py",
    "__main__.py",
    "atomgit_hub.py",
    "api.py",
    "cli.py",
    "cli_contracts.py",
    "completion.py",
    "config.py",
    "exceptions.py",
    "lfs_pointer.py",
    "release.py",
    "runtime.py",
    "uninstaller.py",
    "utils.py",
    "version.py",
}
PACKAGE_MODULES = {
    "__init__.py",
    "__main__.py",
    "adapters/__init__.py",
    "adapters/atomgit_v5.py",
    "adapters/config.py",
    "adapters/download/__init__.py",
    "adapters/download/integrity.py",
    "adapters/download/manifest.py",
    "adapters/download/prune.py",
    "adapters/download/resume.py",
    "adapters/download/service.py",
    "adapters/download/transport.py",
    "adapters/huggingface.py",
    "adapters/lfs/__init__.py",
    "adapters/lfs/pointer.py",
    "adapters/lfs/service.py",
    "adapters/sdk_common.py",
    "adapters/sdk_datasets.py",
    "adapters/sdk_downloads.py",
    "adapters/sdk_errors.py",
    "adapters/sdk_repositories.py",
    "adapters/sdk_uploads.py",
    "adapters/upload/__init__.py",
    "adapters/upload/contracts.py",
    "adapters/upload/errors.py",
    "adapters/upload/ordinary.py",
    "adapters/upload/projection.py",
    "adapters/upload/resumable.py",
    "adapters/upload/service.py",
    "api.py",
    "api/__init__.py",
    "atomgit_hub.py",
    "cli.py",
    "cli/__init__.py",
    "cli/__main__.py",
    "cli_contracts.py",
    "completion.py",
    "config.py",
    "commands/__init__.py",
    "commands/authentication.py",
    "commands/lifecycle.py",
    "commands/repositories.py",
    "commands/transfers.py",
    "compatibility/__init__.py",
    "compatibility/authentication.py",
    "compatibility/api.py",
    "compatibility/cli.py",
    "compatibility/download.py",
    "compatibility/facade.py",
    "compatibility/legacy_packages.py",
    "compatibility/registry.py",
    "compatibility/repositories.py",
    "core/__init__.py",
    "core/contracts.py",
    "core/errors.py",
    "core/parity.py",
    "core/policies.py",
    "core/ports.py",
    "domain/__init__.py",
    "domain/authentication.py",
    "domain/repositories.py",
    "domain/transfers.py",
    "download/__init__.py",
    "download/integrity.py",
    "download/manifest.py",
    "download/prune.py",
    "download/resume.py",
    "download/service.py",
    "download/transport.py",
    "exceptions.py",
    "lfs_pointer.py",
    "release.py",
    "runtime.py",
    "uninstaller.py",
    "utils.py",
    "version.py",
    "infrastructure/__init__.py",
    "infrastructure/cache.py",
    "infrastructure/completion.py",
    "infrastructure/config.py",
    "infrastructure/environment.py",
    "infrastructure/filesystem.py",
    "infrastructure/git_credentials.py",
    "infrastructure/managed_paths.py",
    "infrastructure/output.py",
    "infrastructure/release.py",
    "infrastructure/runtime.py",
    "infrastructure/uninstall.py",
    "infrastructure/utils.py",
    "infrastructure/validation.py",
    "interfaces/__init__.py",
    "interfaces/cli/__init__.py",
    "interfaces/cli/runner.py",
    "interfaces/cli/schema.py",
    "interfaces/cli/commands/__init__.py",
    "interfaces/cli/commands/authentication.py",
    "interfaces/cli/commands/lifecycle.py",
    "interfaces/cli/commands/repositories.py",
    "interfaces/cli/commands/transfers.py",
    "interfaces/sdk/__init__.py",
    "interfaces/sdk/client.py",
    "lifecycle/__init__.py",
    "lifecycle/completion.py",
    "lifecycle/environment.py",
    "lifecycle/managed_paths.py",
    "lifecycle/uninstall.py",
    "services/__init__.py",
    "services/authentication.py",
    "services/repositories.py",
    "upload/__init__.py",
    "upload/contracts.py",
    "upload/errors.py",
    "upload/ordinary.py",
    "upload/projection.py",
    "upload/resumable.py",
    "upload/service.py",
    "usecases/__init__.py",
    "usecases/authentication.py",
    "usecases/repositories.py",
    "usecases/transfers.py",
    "lfs/__init__.py",
    "lfs/service.py",
    "sdk/__init__.py",
    "sdk/common.py",
    "sdk/datasets.py",
    "sdk/downloads.py",
    "sdk/errors.py",
    "sdk/repositories.py",
    "sdk/uploads.py",
}
SHIM_PATH = REPOSITORY_ROOT / "src" / "atomgit_hub.py"
EXPECTED_ROOT_PYTHON = {"setup.py"}
LEGACY_DIRECTORIES = {
    "api",
    "cli",
    "commands",
    "download",
    "lfs",
    "lifecycle",
    "sdk",
    "services",
    "upload",
}
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def shim_errors():
    if not SHIM_PATH.is_file():
        return ["missing src/atomgit_hub.py compatibility shim"]
    source = SHIM_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SHIM_PATH))
    imports = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module
    }
    package_imports = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "atomgit"
        for alias in node.names
    }
    forbidden_nodes = tuple(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and getattr(node, "name", "")
        not in {"__getattr__", "_forward_setattr", "_forward_delattr"}
    )
    errors = []
    if "atomgit.atomgit_hub" not in imports and "atomgit_hub" not in package_imports:
        errors.append("shim does not import the single package SDK implementation")
    if forbidden_nodes:
        errors.append("shim contains an implementation instead of forwarding")
    if "huggingface_hub" in source or "datasets" in source:
        errors.append("shim imports heavy SDK dependencies")
    if len(source.splitlines()) > 36:
        errors.append("shim grew beyond the minimal compatibility boundary")
    return errors


def copy_ignore(directory, names):
    ignored = {"__pycache__"} & set(names)
    if Path(directory).resolve() == PACKAGE_ROOT.resolve():
        ignored.update(LEGACY_DIRECTORIES & set(names))
    return ignored


def main():
    first_level_directories = {
        path.name
        for path in PACKAGE_ROOT.iterdir()
        if path.is_dir() and path.name != "__pycache__"
    }
    check(
        "src/atomgit has exactly the seven canonical responsibility directories",
        first_level_directories == EXPECTED_FIRST_LEVEL_DIRECTORIES,
        repr(sorted(first_level_directories ^ EXPECTED_FIRST_LEVEL_DIRECTORIES)),
    )
    root_python = {path.name for path in REPOSITORY_ROOT.glob("*.py")}
    package_python = (
        {
            path.relative_to(PACKAGE_ROOT).as_posix()
            for path in PACKAGE_ROOT.rglob("*.py")
        }
        if PACKAGE_ROOT.is_dir()
        else set()
    )
    check(
        "all production modules move into the src package",
        PACKAGE_ROOT.is_dir() and package_python == PACKAGE_MODULES,
        repr(sorted(PACKAGE_MODULES - package_python)),
    )
    check(
        "the repository root contains only packaging Python code",
        root_python == EXPECTED_ROOT_PYTHON,
        repr(sorted(root_python - EXPECTED_ROOT_PYTHON)),
    )
    package_root_python = {path.name for path in PACKAGE_ROOT.glob("*.py")}
    check(
        "src/atomgit root Python files use the frozen compatibility allowlist",
        package_root_python <= ROOT_PYTHON_ALLOWLIST,
        repr(sorted(package_root_python - ROOT_PYTHON_ALLOWLIST)),
    )
    check(
        "the top-level SDK compatibility shim is minimal and single-sourced",
        not shim_errors(),
        repr(shim_errors()),
    )
    check(
        "the package implementation is present exactly once",
        (PACKAGE_ROOT / "atomgit_hub.py").is_file()
        and len(list(REPOSITORY_ROOT.rglob("atomgit_hub.py"))) == 2,
    )
    patch_probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from unittest.mock import patch; import atomgit_hub; "
                "original=atomgit_hub.hf_upload_folder; "
                "context=patch.object(atomgit_hub, 'hf_upload_folder', object()); "
                "replacement=context.start(); "
                "assert atomgit_hub.hf_upload_folder is replacement; "
                "context.stop(); "
                "assert atomgit_hub.hf_upload_folder is original"
            ),
        ],
        cwd=str(REPOSITORY_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    check(
        "the compatibility proxy preserves patch.object read, write, and cleanup",
        patch_probe.returncode == 0,
        patch_probe.stderr.strip(),
    )
    with tempfile.TemporaryDirectory(prefix="atomgit-seven-layout-") as directory:
        isolated_root = Path(directory)
        isolated_src = isolated_root / "src"
        isolated_src.mkdir()
        shutil.copytree(
            PACKAGE_ROOT,
            isolated_src / "atomgit",
            ignore=copy_ignore,
        )
        shutil.copy2(SHIM_PATH, isolated_src / SHIM_PATH.name)
        isolated_home = isolated_root / "home"
        isolated_home.mkdir()
        environment = os.environ.copy()
        environment.update(
            {"HOME": str(isolated_home), "PYTHONPATH": str(isolated_src)}
        )
        import_probe = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import importlib, atomgit; "
                    "pairs={"
                    "'atomgit.commands.authentication':'atomgit.interfaces.cli.commands.authentication',"
                    "'atomgit.download.service':'atomgit.compatibility.download',"
                    "'atomgit.lfs.service':'atomgit.adapters.lfs.service',"
                    "'atomgit.lifecycle.environment':'atomgit.infrastructure.environment',"
                    "'atomgit.sdk.downloads':'atomgit.adapters.sdk_downloads',"
                    "'atomgit.services.repositories':'atomgit.compatibility.repositories',"
                    "'atomgit.upload.service':'atomgit.adapters.upload.service'}; "
                    "assert all(importlib.import_module(old) is importlib.import_module(new) "
                    "for old,new in pairs.items()); "
                    "importlib.import_module('atomgit.api'); "
                    "importlib.import_module('atomgit.cli')"
                ),
            ],
            cwd=str(isolated_root),
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        module_probe = subprocess.run(
            [sys.executable, "-m", "atomgit.cli", "--help"],
            cwd=str(isolated_root),
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    check(
        "historical imports survive after legacy directories are physically absent",
        import_probe.returncode == 0
        and module_probe.returncode == 0
        and "Commands:" in module_probe.stdout,
        (import_probe.stderr + module_probe.stderr).strip(),
    )
    check(
        "source layout does not create placeholder production modules",
        all(path.stat().st_size > 0 for path in PACKAGE_ROOT.rglob("*.py")),
    )
    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
