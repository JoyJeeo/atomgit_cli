#!/usr/bin/env python3
"""The unsupported repo-info placeholder cannot fabricate verified data."""

import contextlib
import inspect
import io
import sys

import atomgit  # noqa: F401


api_mod = sys.modules["atomgit.api"]
results = []


def check(name, condition):
    results.append((name, condition))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")


def main():
    original_credentials = api_mod.config.get_credentials
    original_urlopen = api_mod.urllib.request.urlopen
    side_effects = []

    def forbidden_side_effect(*args, **kwargs):
        side_effects.append((args, kwargs))
        raise AssertionError("repo-info must remain offline")

    api_mod.config.get_credentials = forbidden_side_effect
    api_mod.urllib.request.urlopen = forbidden_side_effect
    try:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = api_mod.api.get_repo_info(
                "secret-repository-input-never-echo"
            )
        text = output.getvalue()
        check("repo-info returns explicit failure sentinel", result is None)
        check(
            "repo-info reports unsupported behavior",
            "暂不支持" in text and "仓库信息" in text,
        )
        check(
            "repo-info output does not echo caller input",
            "secret-repository-input-never-echo" not in text,
        )
        check(
            "repo-info performs no credential or network access",
            side_effects == [],
        )
        parameters = list(
            inspect.signature(api_mod.HuggingFaceAPI.get_repo_info).parameters
        )
        check(
            "repo-info public method signature remains present",
            parameters == ["self", "repo_id"],
        )
    finally:
        api_mod.config.get_credentials = original_credentials
        api_mod.urllib.request.urlopen = original_urlopen

    passed = sum(condition for _, condition in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
