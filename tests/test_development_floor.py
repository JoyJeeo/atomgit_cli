#!/usr/bin/env python3
"""Executable contract for the permanent development-floor registry."""

import copy
import sys
from pathlib import Path


try:
    from development_floor_contract import (
        BASELINE_CAPABILITY_COUNT,
        BASELINE_INVARIANT_COUNT,
        CAPABILITY_REGISTRY,
        FORMAL_DEFINITION,
        capability_test_map,
        validate_development_floor,
        validate_workflow_documents,
    )
except ImportError as error:
    print(f"[FAIL] development-floor contract is importable -> {error}")
    raise SystemExit(1)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def _baseline_scripts():
    from cli_baseline_contract import BASELINE_TEST_GROUPS

    return {
        script
        for scripts in BASELINE_TEST_GROUPS.values()
        for script in scripts
    }


def _first_capability(registry):
    return next(iter(registry.values()))


def main():
    results.clear()
    baseline_scripts = _baseline_scripts()

    errors = validate_development_floor(
        CAPABILITY_REGISTRY,
        baseline_scripts,
        REPOSITORY_ROOT,
    )
    check(
        "development-floor registry is complete and internally consistent",
        not errors,
        repr(errors),
    )

    check(
        "capability ledger count matches its monotonic baseline",
        len(CAPABILITY_REGISTRY) == BASELINE_CAPABILITY_COUNT,
        f"actual={len(CAPABILITY_REGISTRY)}, baseline={BASELINE_CAPABILITY_COUNT}",
    )
    invariant_count = sum(
        len(capability["invariants"])
        for capability in CAPABILITY_REGISTRY.values()
    )
    check(
        "invariant ledger count matches its monotonic baseline",
        invariant_count == BASELINE_INVARIANT_COUNT,
        f"actual={invariant_count}, baseline={BASELINE_INVARIANT_COUNT}",
    )

    mapped_tests = capability_test_map(CAPABILITY_REGISTRY)
    check(
        "every registered offline test maps to a capability",
        set(mapped_tests) == baseline_scripts,
        repr(
            {
                "unmapped": sorted(baseline_scripts - set(mapped_tests)),
                "stale": sorted(set(mapped_tests) - baseline_scripts),
            }
        ),
    )
    check(
        "the focused development-floor test protects its own meta-capability",
        "FLOOR-REGISTRY" in mapped_tests.get(
            "test_development_floor.py", ()
        ),
        repr(mapped_tests.get("test_development_floor.py")),
    )

    workflow_errors = validate_workflow_documents(REPOSITORY_ROOT)
    check(
        "AI and human workflow documents carry the development floor",
        not workflow_errors,
        repr(workflow_errors),
    )
    check(
        "the formal definition is stable and complete",
        FORMAL_DEFINITION.startswith(
            "AtomGit CLI 的所有已实现能力，都必须拥有稳定的能力登记"
        )
        and FORMAL_DEFINITION.endswith(
            "不得进入 Issue 完成、合并、发布或继续扩展开发阶段。"
        ),
        FORMAL_DEFINITION,
    )

    missing_capability = copy.deepcopy(CAPABILITY_REGISTRY)
    missing_capability.pop(next(iter(missing_capability)))
    check(
        "removing a registered capability fails closed",
        bool(
            validate_development_floor(
                missing_capability, baseline_scripts, REPOSITORY_ROOT
            )
        ),
    )

    incomplete_capability = copy.deepcopy(CAPABILITY_REGISTRY)
    _first_capability(incomplete_capability)["risk"] = ""
    check(
        "incomplete capability metadata fails closed",
        bool(
            validate_development_floor(
                incomplete_capability, baseline_scripts, REPOSITORY_ROOT
            )
        ),
    )

    duplicate_invariant = copy.deepcopy(CAPABILITY_REGISTRY)
    capabilities = iter(duplicate_invariant.values())
    first = next(capabilities)
    second = next(capabilities)
    second["invariants"][0]["id"] = first["invariants"][0]["id"]
    check(
        "duplicate invariant IDs fail closed",
        bool(
            validate_development_floor(
                duplicate_invariant, baseline_scripts, REPOSITORY_ROOT
            )
        ),
    )

    missing_statement = copy.deepcopy(CAPABILITY_REGISTRY)
    _first_capability(missing_statement)["invariants"][0]["statement"] = ""
    check(
        "empty observable invariant statements fail closed",
        bool(
            validate_development_floor(
                missing_statement, baseline_scripts, REPOSITORY_ROOT
            )
        ),
    )

    stale_test = copy.deepcopy(CAPABILITY_REGISTRY)
    _first_capability(stale_test)["tests"] = (
        *_first_capability(stale_test)["tests"],
        "test_removed_capability.py",
    )
    check(
        "stale test evidence fails closed",
        bool(
            validate_development_floor(
                stale_test, baseline_scripts, REPOSITORY_ROOT
            )
        ),
    )

    unmapped_test = copy.deepcopy(CAPABILITY_REGISTRY)
    target_test = next(iter(baseline_scripts))
    for capability in unmapped_test.values():
        capability["tests"] = tuple(
            test for test in capability["tests"] if test != target_test
        )
    check(
        "an unmapped offline regression fails closed",
        bool(
            validate_development_floor(
                unmapped_test, baseline_scripts, REPOSITORY_ROOT
            )
        ),
    )

    stale_document = copy.deepcopy(CAPABILITY_REGISTRY)
    _first_capability(stale_document)["documents"] = (
        "docs/removed-capability.md",
    )
    check(
        "stale documentation evidence fails closed",
        bool(
            validate_development_floor(
                stale_document, baseline_scripts, REPOSITORY_ROOT
            )
        ),
    )

    invalid_remote_status = copy.deepcopy(CAPABILITY_REGISTRY)
    _first_capability(invalid_remote_status)["remote_evidence"] = "assumed"
    check(
        "unrecognized controlled-remote evidence fails closed",
        bool(
            validate_development_floor(
                invalid_remote_status, baseline_scripts, REPOSITORY_ROOT
            )
        ),
    )

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nDevelopment-floor contract: {passed}/{len(results)} checks passed")
    if passed != len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
