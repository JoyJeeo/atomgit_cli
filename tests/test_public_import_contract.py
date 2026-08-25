#!/usr/bin/env python3
"""Lock source public imports, symbols, identities, and SDK signatures."""

import importlib
import inspect
import sys
from pathlib import Path


TESTS_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = TESTS_DIRECTORY.parent
if str(TESTS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TESTS_DIRECTORY))

from structure_contract import (  # noqa: E402
    PACKAGE_ALL,
    PUBLIC_IMPORTS,
    PUBLIC_SIGNATURES,
    PUBLIC_SYMBOLS,
)


results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def validate_public_surface(modules):
    errors = []
    for module_name in PUBLIC_IMPORTS:
        if module_name not in modules:
            errors.append(f"missing public import: {module_name}")
    for module_name, symbols in PUBLIC_SYMBOLS.items():
        module = modules.get(module_name)
        if module is None:
            continue
        for symbol in symbols:
            if not hasattr(module, symbol):
                errors.append(f"missing public symbol: {module_name}:{symbol}")
    return errors


def main():
    modules = {
        module_name: importlib.import_module(module_name)
        for module_name in PUBLIC_IMPORTS
    }
    errors = validate_public_surface(modules)
    check("all historical source imports and symbols remain available", not errors, repr(errors))

    atomgit = modules["atomgit"]
    api_module = modules["atomgit.api"]
    cli_module = modules["atomgit.cli"]
    package_sdk = importlib.import_module("atomgit.atomgit_hub")
    standalone_sdk = modules["atomgit_hub"]
    owner_pairs = {
        "atomgit.cli_contracts": "atomgit.core.contracts",
        "atomgit.config": "atomgit.infrastructure.config",
        "atomgit.exceptions": "atomgit.core.errors",
        "atomgit.lfs_pointer": "atomgit.adapters.lfs.pointer",
        "atomgit.release": "atomgit.infrastructure.release",
        "atomgit.runtime": "atomgit.infrastructure.runtime",
        "atomgit.version": "atomgit.infrastructure.version",
    }
    identity_symbols = {
        "atomgit.config": ("Config", "config"),
        "atomgit.exceptions": PUBLIC_SYMBOLS["atomgit.exceptions"],
        "atomgit.lfs_pointer": PUBLIC_SYMBOLS["atomgit.lfs_pointer"],
        "atomgit.release": PUBLIC_SYMBOLS["atomgit.release"],
        "atomgit.runtime": PUBLIC_SYMBOLS["atomgit.runtime"],
    }
    check(
        "historical root symbols retain exact canonical owner identities",
        all(
            getattr(modules[historical], symbol)
            is getattr(importlib.import_module(owner), symbol)
            for historical, owner in owner_pairs.items()
            if historical in identity_symbols
            for symbol in identity_symbols[historical]
        ),
    )
    check(
        "historical contract and version values equal their canonical authorities",
        modules["atomgit.cli_contracts"].DEFAULT_UPLOAD_BATCH_SIZE
        == importlib.import_module("atomgit.core.contracts").DEFAULT_UPLOAD_BATCH_SIZE
        and modules["atomgit.version"].__version__
        == importlib.import_module("atomgit.infrastructure.version").__version__,
    )
    check(
        "the package-level config export remains the shared singleton",
        atomgit.config is modules["atomgit.config"].config,
    )
    check(
        "package facade exports preserve the global API and Click entry objects",
        atomgit.api is api_module.api and atomgit.cli is cli_module.cli,
    )
    check(
        "package SDK exports preserve their package-module identities",
        all(
            getattr(atomgit, name) is getattr(package_sdk, name)
            for name in PUBLIC_SYMBOLS["atomgit_hub"]
        ),
    )
    check(
        "top-level atomgit_hub remains a distinct compatibility module",
        standalone_sdk is not package_sdk
        and Path(standalone_sdk.__file__).resolve()
        == REPOSITORY_ROOT / "src" / "atomgit_hub.py"
        and Path(package_sdk.__file__).resolve()
        == REPOSITORY_ROOT / "src" / "atomgit" / "atomgit_hub.py",
    )

    signature_errors = []
    for name, expected in PUBLIC_SIGNATURES.items():
        for label, module in (("package", package_sdk), ("top-level", standalone_sdk)):
            actual = str(inspect.signature(getattr(module, name)))
            if actual != expected:
                signature_errors.append(f"{label} {name}: {actual}")
    check("public SDK signatures are exact at both historical paths", not signature_errors, repr(signature_errors))

    exception_names = tuple(
        name for name in PUBLIC_SYMBOLS["atomgit_hub"] if name.startswith("AtomGit")
    )
    check(
        "public exception hierarchies remain stable within both import paths",
        all(
            issubclass(getattr(module, name), module.AtomGitError)
            for module in (package_sdk, standalone_sdk)
            for name in exception_names
            if name != "AtomGitError"
        ),
    )
    check(
        "package lazy-export inventory remains exact",
        tuple(atomgit.__all__) == PACKAGE_ALL,
        repr(atomgit.__all__),
    )

    missing = dict(modules)
    missing.pop("atomgit.utils")
    missing_errors = validate_public_surface(missing)
    check(
        "removing a historical public import fails closed",
        missing_errors == ["missing public import: atomgit.utils"],
        repr(missing_errors),
    )

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
