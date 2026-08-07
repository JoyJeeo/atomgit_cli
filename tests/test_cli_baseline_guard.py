#!/usr/bin/env python3
"""Prove that the CLI baseline detects unregistered capability growth."""

import copy
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import atomgit  # noqa: F401


TESTS_DIRECTORY = Path(__file__).resolve().parent
if str(TESTS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TESTS_DIRECTORY))

import test_cli_feature_baseline as baseline  # noqa: E402
import run_cli_baseline as baseline_runner  # noqa: E402


results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def main():
    required_attributes = (
        "BASELINE_LEAF_COMMAND_COUNT",
        "BASELINE_PUBLIC_COMMAND_COUNT",
        "BASELINE_PUBLIC_PARAMETER_COUNT",
        "BASELINE_TEST_SCRIPT_COUNT",
        "BASELINE_TEST_GROUPS",
        "EXPECTED_PUBLIC_SCHEMA",
        "LEAF_DISPATCH_PATHS",
        "discover_public_schema",
        "validate_leaf_dispatches",
        "validate_public_schema",
        "validate_test_entrypoints",
        "validate_test_registry",
    )
    missing = [
        name for name in required_attributes if not hasattr(baseline, name)
    ]
    check(
        "baseline exposes monotonic contract validators",
        not missing,
        f"missing={missing!r}",
    )
    if missing:
        passed = sum(condition for _, condition, _ in results)
        print(f"summary: {passed}/{len(results)} passed")
        return 1

    actual_schema = baseline.discover_public_schema(baseline.cli_mod.cli)
    registered_test_count = sum(
        len(scripts) for scripts in baseline.BASELINE_TEST_GROUPS.values()
    )
    check(
        "monotonic ledger counters match the registered baseline",
        len(actual_schema) == baseline.BASELINE_PUBLIC_COMMAND_COUNT
        and sum(len(spec["params"]) for spec in actual_schema.values())
        == baseline.BASELINE_PUBLIC_PARAMETER_COUNT
        and len(baseline.LEAF_DISPATCH_PATHS)
        == baseline.BASELINE_LEAF_COMMAND_COUNT
        and registered_test_count == baseline.BASELINE_TEST_SCRIPT_COUNT,
        (
            f"commands={len(actual_schema)}, "
            f"parameters={sum(len(spec['params']) for spec in actual_schema.values())}, "
            f"leaves={len(baseline.LEAF_DISPATCH_PATHS)}, "
            f"tests={registered_test_count}"
        ),
    )
    schema_errors = baseline.validate_public_schema(actual_schema)
    check(
        "current public CLI exactly matches the registered schema",
        not schema_errors,
        repr(schema_errors),
    )

    extra_command_schema = copy.deepcopy(actual_schema)
    extra_command_schema[("future-command",)] = {
        "kind": "command",
        "params": (),
    }
    extra_command_errors = baseline.validate_public_schema(extra_command_schema)
    check(
        "unregistered command is rejected",
        any("future-command" in error for error in extra_command_errors),
        repr(extra_command_errors),
    )

    changed_option_schema = copy.deepcopy(actual_schema)
    upload_spec = changed_option_schema[("upload",)]
    upload_spec["params"] = upload_spec["params"] + (
        {
            "kind": "option",
            "name": "future_mode",
            "declarations": ("--future-mode",),
            "required": False,
            "default": False,
            "type": "bool",
            "nargs": 1,
            "is_flag": True,
            "multiple": False,
        },
    )
    changed_option_errors = baseline.validate_public_schema(
        changed_option_schema
    )
    check(
        "unregistered option schema change is rejected",
        any("upload" in error for error in changed_option_errors),
        repr(changed_option_errors),
    )

    discovered_tests = {
        path.name for path in TESTS_DIRECTORY.glob("test_*.py")
    }
    registry_errors = baseline.validate_test_registry(discovered_tests)
    check(
        "every current offline script is registered exactly once",
        not registry_errors,
        repr(registry_errors),
    )

    extra_test_errors = baseline.validate_test_registry(
        discovered_tests | {"test_future_capability.py"}
    )
    check(
        "unregistered new test script is rejected",
        any("test_future_capability.py" in error for error in extra_test_errors),
        repr(extra_test_errors),
    )

    registered_tests = {
        script
        for scripts in baseline.BASELINE_TEST_GROUPS.values()
        for script in scripts
    }
    removed_test = sorted(registered_tests)[0]
    missing_test_errors = baseline.validate_test_registry(
        discovered_tests - {removed_test}
    )
    check(
        "stale test registration is rejected",
        any(removed_test in error for error in missing_test_errors),
        repr(missing_test_errors),
    )

    entrypoint_errors = baseline.validate_test_entrypoints(
        {
            path.name: path.read_text(encoding="utf-8")
            for path in TESTS_DIRECTORY.glob("test_*.py")
        }
    )
    check(
        "every registered offline script is self-executing",
        not entrypoint_errors,
        repr(entrypoint_errors),
    )

    inert_test_errors = baseline.validate_test_entrypoints(
        {"test_inert_feature.py": "def test_feature():\n    assert True\n"}
    )
    check(
        "an inert test file that the collector would not execute is rejected",
        any("test_inert_feature.py" in error for error in inert_test_errors),
        repr(inert_test_errors),
    )

    dispatch_errors = baseline.validate_leaf_dispatches(
        baseline.LEAF_DISPATCH_PATHS,
        actual_schema,
    )
    check(
        "every current leaf command has registered dispatch coverage",
        not dispatch_errors,
        repr(dispatch_errors),
    )

    missing_dispatch = baseline.LEAF_DISPATCH_PATHS[:-1]
    missing_dispatch_errors = baseline.validate_leaf_dispatches(
        missing_dispatch,
        actual_schema,
    )
    check(
        "missing leaf dispatch registration is rejected",
        bool(missing_dispatch_errors),
        repr(missing_dispatch_errors),
    )

    with patch.object(
        baseline_runner.subprocess,
        "run",
        return_value=subprocess.CompletedProcess([], 0),
    ) as run_mock:
        runner_result = baseline_runner.main()
    check(
        "comprehensive runner invokes the complete pytest matrix",
        runner_result == 0
        and run_mock.call_args.args[0]
        == [sys.executable, "-m", "pytest", "-q"]
        and run_mock.call_args.kwargs["cwd"]
        == str(baseline_runner.REPOSITORY_ROOT)
        and run_mock.call_args.kwargs["check"] is False,
        repr(run_mock.call_args),
    )

    with patch.object(
        baseline_runner.subprocess,
        "run",
        return_value=subprocess.CompletedProcess([], 7),
    ):
        failing_runner_result = baseline_runner.main()
    check(
        "comprehensive runner propagates a failing pytest status",
        failing_runner_result == 7,
        repr(failing_runner_result),
    )

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
