#!/usr/bin/env python3
"""Fail closed on unowned modules, dependency debt, and facade growth."""

import copy
import sys
from pathlib import Path

TESTS_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = TESTS_DIRECTORY.parent
if str(TESTS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TESTS_DIRECTORY))

from structure_contract import (  # noqa: E402
    CURRENT_INTERNAL_EDGES,
    EXPECTED_WHEEL_FILES,
    LEGACY_FACADE_DEBT,
    LEGACY_FORBIDDEN_EDGES,
    PRODUCTION_MODULE_OWNERS,
    discover_internal_edges,
    discover_source_texts,
    validate_artifact_contract,
    validate_structure,
)

results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def main():
    source_texts = discover_source_texts(REPOSITORY_ROOT)
    current_edges = discover_internal_edges(source_texts)
    current_errors = validate_structure(source_texts)
    check(
        "every production module has one declared capability owner",
        set(source_texts) == set(PRODUCTION_MODULE_OWNERS),
        repr(sorted(set(source_texts) ^ set(PRODUCTION_MODULE_OWNERS))),
    )
    check(
        "current internal edges are registered and contain no hidden growth",
        current_edges == CURRENT_INTERNAL_EDGES,
        repr(sorted(current_edges ^ CURRENT_INTERNAL_EDGES)),
    )
    check(
        "package execution adapters register their package-facade dependency",
        ("cli.__main__", "cli.__init__") in current_edges,
        repr(sorted(current_edges)),
    )
    check(
        "the current structure satisfies its monotonic contract",
        not current_errors,
        repr(current_errors),
    )
    check(
        "legacy forbidden dependency debt is explicit and exact",
        LEGACY_FORBIDDEN_EDGES == set(),
        repr(LEGACY_FORBIDDEN_EDGES),
    )

    unowned = dict(source_texts)
    unowned["future_placeholder"] = "VALUE = 1\n"
    errors = validate_structure(unowned)
    check(
        "an unowned production module fails closed",
        any("future_placeholder" in error and "unowned" in error for error in errors),
        repr(errors),
    )

    forbidden = dict(source_texts)
    forbidden["runtime"] += "\nfrom .cli import cli\n"
    errors = validate_structure(forbidden)
    check(
        "a new infrastructure-to-CLI edge fails closed",
        any("legacy dependency debt contract" in error for error in errors),
        repr(errors),
    )
    check(
        "a new dependency cycle fails closed",
        any("dependency cycle" in error for error in errors),
        repr(errors),
    )

    growing = dict(source_texts)
    growing["api.__init__"] += "\n\ndef future_unowned_behavior():\n    return None\n"
    errors = validate_structure(growing)
    check(
        "legacy facade function or line growth fails closed",
        any(
            "legacy facade debt contract is stale in api.__init__" in error
            for error in errors
        ),
        repr(errors),
    )

    growing_edge = dict(source_texts)
    growing_edge["cli.__init__"] = growing_edge["cli.__init__"].replace(
        'api = _LazyObject("api", "api")',
        'api = _LazyObject("api", "api")\n_import_runtime_module("atomgit_hub")',
    )
    errors = validate_structure(growing_edge)
    check(
        "new facade dependency edges fail closed after legacy debt removal",
        any("internal dependency contract is stale" in error for error in errors),
        repr(errors),
    )

    shrinking_facade = dict(source_texts)
    shrinking_facade["api.__init__"] = shrinking_facade["api.__init__"].replace(
        "\n\n", "\n", 1
    )
    errors = validate_structure(shrinking_facade)
    check(
        "reduced facade debt requires its exact ceiling to tighten immediately",
        any(
            "legacy facade debt contract is stale in api.__init__" in error
            for error in errors
        ),
        repr(errors),
    )

    empty = dict(source_texts)
    empty["runtime"] = '"""Placeholder."""\npass\n'
    errors = validate_structure(empty)
    check(
        "empty placeholder production modules fail closed",
        any("empty placeholder" in error for error in errors),
        repr(errors),
    )

    weakened_debt = copy.deepcopy(LEGACY_FACADE_DEBT)
    weakened_debt["api.__init__"]["max_functions"] += 1
    weakened_debt["api.__init__"]["max_lines"] += 4
    check(
        "the test fixture demonstrates that relaxing debt would hide growth",
        not validate_structure(growing, legacy_debt=weakened_debt),
    )

    incomplete_wheel = set(EXPECTED_WHEEL_FILES)
    incomplete_wheel.remove("atomgit/release.py")
    artifact_errors = validate_artifact_contract(wheel_files=incomplete_wheel)
    check(
        "omitting an owned runtime module from the wheel contract fails closed",
        any("atomgit/release.py" in error for error in artifact_errors),
        repr(artifact_errors),
    )

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
