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
        and Path(standalone_sdk.__file__).resolve() == REPOSITORY_ROOT / "atomgit_hub.py"
        and Path(package_sdk.__file__).resolve() == REPOSITORY_ROOT / "atomgit_hub.py",
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
