"""Declarative modern-packaging and incremental-tooling contract."""

import ast
import hashlib
import json
import subprocess
import sys
from difflib import unified_diff
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover - exercised by the Python 3.9 gate
    import tomli as tomllib


BUILD_SYSTEM = {
    "requires": ["setuptools>=77,<82", "wheel>=0.43,<0.48"],
    "build-backend": "setuptools.build_meta",
}

PROJECT_METADATA = {
    "name": "atomgit",
    "dynamic": [
        "authors",
        "classifiers",
        "dependencies",
        "description",
        "keywords",
        "license",
        "readme",
        "requires-python",
        "scripts",
        "urls",
        "version",
    ],
}

SETUPTOOLS_LAYOUT = {
    "packages": ["atomgit", "atomgit.infrastructure"],
    "py-modules": ["atomgit_hub"],
    "package-dir": {"": "src"},
    "include-package-data": False,
}

PYTEST_POLICY = {
    "testpaths": ["tests"],
    "python_files": ["pytest_*.py"],
    "addopts": "-ra",
}

TOOL_POLICY = {
    "black": {"line-length": 88, "target-version": ["py39"]},
    "isort": {
        "profile": "black",
        "line_length": 88,
        "py_version": 39,
        "known_first_party": ["atomgit", "atomgit_hub"],
    },
    "ruff": {"line-length": 88, "target-version": "py39"},
    "ruff.lint": {"select": ["E4", "E7", "E9", "F"]},
}

# Exact normalized debt for the pinned tool versions in requirements-dev.txt.
# These declarations must tighten in the same change whenever debt is removed.
LEGACY_TOOL_DEBT = {
    "black": {
        "files": 88,
        "changes": 633,
        "digest": "02fe19beeba439f383ca0b3b32a0a3c2299203734cbcecfefbbf682303a809a0",
    },
    "isort": {
        "files": 89,
        "changes": 110,
        "digest": "00588fd87184d9470cd3dfafa8254b08eb7eea822e6d0404507d2d3745dbf3ad",
    },
    "ruff": {
        "files": 19,
        "changes": 204,
        "digest": "9241c79a4203ad2ce230bd318928a9542f1ebc2bb2974d8f74f9ae1504589487",
    },
}

CLEAN_POLICY_FILES = {
    "src/atomgit/config.py",
    "src/atomgit/infrastructure/__init__.py",
    "src/atomgit/infrastructure/cache.py",
    "src/atomgit/infrastructure/filesystem.py",
    "src/atomgit/infrastructure/output.py",
    "src/atomgit/infrastructure/utils.py",
    "src/atomgit/infrastructure/validation.py",
    "src/atomgit/runtime.py",
    "src/atomgit/utils.py",
    "setup.py",
    "src/atomgit_hub.py",
    "tests/packaging_contract.py",
    "tests/test_src_layout_migration.py",
    "tests/test_packaging_metadata.py",
    "tests/test_infrastructure_utils_ownership.py",
}


def load_pyproject(path):
    with Path(path).open("rb") as stream:
        return tomllib.load(stream)


def discover_python_files(repository_root):
    root = Path(repository_root)
    return tuple(
        sorted(
            (
                *root.glob("*.py"),
                *root.joinpath("src").glob("*.py"),
                *root.joinpath("src", "atomgit").rglob("*.py"),
                *root.joinpath("tests").glob("*.py"),
            )
        )
    )


def legacy_python_files(repository_root):
    root = Path(repository_root)
    return tuple(
        path
        for path in discover_python_files(root)
        if _relative(path, root) not in CLEAN_POLICY_FILES
    )


def _digest(records):
    payload = json.dumps(records, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _relative(path, root):
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def black_debt(repository_root):
    import black

    root = Path(repository_root)
    mode = black.Mode(
        line_length=TOOL_POLICY["black"]["line-length"],
        target_versions={black.TargetVersion.PY39},
    )
    records = []
    for path in legacy_python_files(root):
        source = path.read_text(encoding="utf-8")
        try:
            formatted = black.format_file_contents(source, fast=False, mode=mode)
        except black.NothingChanged:
            continue
        diff = "".join(
            unified_diff(
                source.splitlines(keepends=True),
                formatted.splitlines(keepends=True),
                fromfile=_relative(path, root),
                tofile=_relative(path, root),
            )
        )
        records.append((_relative(path, root), diff))
    return {
        "files": len(records),
        "changes": sum(record[1].count("\n@@ ") for record in records),
        "digest": _digest(records),
    }


def isort_debt(repository_root):
    import isort

    root = Path(repository_root)
    config = isort.Config(settings_path=str(root))
    records = []
    for path in legacy_python_files(root):
        source = path.read_text(encoding="utf-8")
        formatted = isort.code(source, config=config, file_path=path)
        if source == formatted:
            continue
        diff = "".join(
            unified_diff(
                source.splitlines(keepends=True),
                formatted.splitlines(keepends=True),
                fromfile=_relative(path, root),
                tofile=_relative(path, root),
            )
        )
        records.append((_relative(path, root), diff))
    return {
        "files": len(records),
        "changes": sum(record[1].count("\n@@ ") for record in records),
        "digest": _digest(records),
    }


def ruff_debt(repository_root):
    root = Path(repository_root)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--output-format=json",
            *[_relative(path, root) for path in legacy_python_files(root)],
        ],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if result.returncode not in {0, 1}:
        raise RuntimeError(result.stderr or result.stdout)
    diagnostics = json.loads(result.stdout)
    records = sorted(
        (
            _relative(item["filename"], root),
            item["code"],
            item["location"]["row"],
            item["location"]["column"],
            item["end_location"]["row"],
            item["end_location"]["column"],
        )
        for item in diagnostics
    )
    return {
        "files": len({record[0] for record in records}),
        "changes": len(records),
        "digest": _digest(records),
    }


def setup_layout(setup_path):
    tree = ast.parse(Path(setup_path).read_text(encoding="utf-8"))
    setup_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "setup"
    ]
    if len(setup_calls) != 1:
        raise ValueError("setup.py must contain exactly one setup() call")
    keywords = {item.arg: item.value for item in setup_calls[0].keywords if item.arg}
    return {
        "packages": ast.literal_eval(keywords["packages"]),
        "py-modules": ast.literal_eval(keywords["py_modules"]),
        "package-dir": ast.literal_eval(keywords["package_dir"]),
        "include-package-data": ast.literal_eval(keywords["include_package_data"]),
    }


def validate_metadata(pyproject, setup_mapping):
    errors = []
    if pyproject.get("build-system") != BUILD_SYSTEM:
        errors.append("build-system contract mismatch")
    if pyproject.get("project") != PROJECT_METADATA:
        errors.append("project metadata migration contract mismatch")
    packaging_policy = pyproject.get("tool", {}).get("atomgit", {}).get("packaging", {})
    if packaging_policy != SETUPTOOLS_LAYOUT:
        errors.append("package discovery contract mismatch")
    setuptools_policy = pyproject.get("tool", {}).get("setuptools", {})
    if setuptools_policy != SETUPTOOLS_LAYOUT:
        errors.append("setuptools package discovery contract mismatch")
    if setup_mapping != SETUPTOOLS_LAYOUT:
        errors.append("setup.py and pyproject layout mismatch")
    pytest_policy = pyproject.get("tool", {}).get("pytest", {}).get("ini_options")
    if pytest_policy != PYTEST_POLICY:
        errors.append("pytest policy contract mismatch")
    tool = pyproject.get("tool", {})
    ruff_policy = dict(tool.get("ruff", {}))
    ruff_lint_policy = ruff_policy.pop("lint", None)
    actual_tools = {
        "black": tool.get("black"),
        "isort": tool.get("isort"),
        "ruff": ruff_policy,
        "ruff.lint": ruff_lint_policy,
    }
    if actual_tools != TOOL_POLICY:
        errors.append("Python 3.9 tool policy contract mismatch")
    return errors


def clean_policy_errors(repository_root):
    root = Path(repository_root)
    files = sorted(CLEAN_POLICY_FILES)
    commands = {
        "black": [sys.executable, "-m", "black", "--check", *files],
        "isort": [sys.executable, "-m", "isort", "--check-only", *files],
        "ruff": [sys.executable, "-m", "ruff", "check", *files],
    }
    errors = []
    for name, command in commands.items():
        result = subprocess.run(
            command,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if result.returncode:
            errors.append(f"{name}: {result.stdout}{result.stderr}")
    return errors
