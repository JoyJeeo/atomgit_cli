#!/usr/bin/env python3
"""Fail closed on the mechanical ``src`` layout and SDK shim contract."""

import ast
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "src" / "atomgit"
PACKAGE_MODULES = {
    "__init__.py",
    "__main__.py",
    "api.py",
    "atomgit_hub.py",
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
    "infrastructure/__init__.py",
    "infrastructure/cache.py",
    "infrastructure/config.py",
    "infrastructure/filesystem.py",
    "infrastructure/git_credentials.py",
    "infrastructure/output.py",
    "infrastructure/runtime.py",
    "infrastructure/utils.py",
    "infrastructure/validation.py",
    "lifecycle/__init__.py",
    "lifecycle/completion.py",
    "lifecycle/environment.py",
    "lifecycle/managed_paths.py",
    "lifecycle/uninstall.py",
}
SHIM_PATH = REPOSITORY_ROOT / "src" / "atomgit_hub.py"
EXPECTED_ROOT_PYTHON = {"setup.py"}
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


def main():
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
    check(
        "source layout does not create placeholder production modules",
        all(path.stat().st_size > 0 for path in PACKAGE_ROOT.rglob("*.py")),
    )
    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
