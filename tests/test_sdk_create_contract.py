#!/usr/bin/env python3
"""SDK repository creation exposes only verified AtomGit semantics."""

import inspect

import atomgit_hub
from huggingface_hub import create_repo as real_create_repo


results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    original_create = atomgit_hub.create_repo
    calls = []

    def strict_create(**kwargs):
        inspect.signature(real_create_repo).bind(**kwargs)
        calls.append(kwargs)
        return "https://atomgit.com/team/repo"

    atomgit_hub.create_repo = strict_create
    try:
        for private in (False,):
            try:
                atomgit_hub.create_repository(
                    "team/repo",
                    token="fake-token",
                    private=private,
                )
            except ValueError as error:
                check("public creation rejected clearly", "private=True" in str(error))
            else:
                check("public creation rejected clearly", False, "no exception")
        check("public creation makes no HF call", not calls)

        for repo_type in ("model", "dataset"):
            result = atomgit_hub.create_repository(
                f"team/{repo_type}-repo",
                token="fake-token",
                private=True,
                repo_type=repo_type,
                exist_ok=True,
            )
            check(f"private {repo_type} result preserved", bool(result))
            call = calls[-1]
            check(f"private {repo_type} type forwarded", call["repo_type"] == repo_type)
            check(f"private {repo_type} privacy forwarded", call["private"] is True)
            check(f"private {repo_type} exist_ok forwarded", call["exist_ok"] is True)
            check(f"private {repo_type} token forwarded", call["token"] == "fake-token")

        before = len(calls)
        try:
            atomgit_hub.create_repository(
                "team/repo",
                token="fake-token",
                private=True,
                repo_type="space",
            )
        except ValueError as error:
            check("unsupported repo type rejected clearly", "model" in str(error))
        else:
            check("unsupported repo type rejected clearly", False, "no exception")
        check("unsupported repo type makes no HF call", len(calls) == before)

        space_cases = {
            "space_sdk": "gradio",
            "space_hardware": "cpu-basic",
            "space_storage": "small",
            "space_sleep_time": 0,
            "space_secrets": [],
            "space_variables": [],
        }
        for name, value in space_cases.items():
            try:
                atomgit_hub.create_repository(
                    "team/repo",
                    token="fake-token",
                    private=True,
                    **{name: value},
                )
            except ValueError as error:
                check(f"{name} rejected clearly", name in str(error))
            else:
                check(f"{name} rejected clearly", False, "no exception")
        check("Space options make no HF calls", len(calls) == before)
    finally:
        atomgit_hub.create_repo = original_create

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
