#!/usr/bin/env python3
"""Prevent ambient Hugging Face credentials from reaching AtomGit."""

import os
import sys

import atomgit  # noqa: F401
from huggingface_hub import HfApi as RealHfApi


api_mod = sys.modules["atomgit.api"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    original_hf_token = os.environ.get("HF_TOKEN")
    try:
        os.environ["HF_TOKEN"] = "hf_fake_unrelated_credential"
        implicit_headers = RealHfApi(token=None)._build_hf_headers()
        anonymous_headers = RealHfApi(token=False)._build_hf_headers()
        check(
            "locked HF client resolves ambient token for None",
            "authorization" in implicit_headers,
        )
        check(
            "locked HF client disables ambient token for False",
            "authorization" not in anonymous_headers,
        )
    finally:
        if original_hf_token is None:
            os.environ.pop("HF_TOKEN", None)
        else:
            os.environ["HF_TOKEN"] = original_hf_token

    original_hf_api = api_mod.HfApi
    constructor_tokens = []

    class RecordingHfApi:
        def __init__(self, token=None):
            constructor_tokens.append(token)

        def list_repo_files(self, repo_id, repo_type=None):
            return ["README.md"]

    api_mod.HfApi = RecordingHfApi
    try:
        repo_type, files = api_mod._atomgit_list_repo_files(
            "user/repo", None, "model"
        )
        check("anonymous repository type is preserved", repo_type == "model")
        check("anonymous repository files are preserved", files == ["README.md"])
        check(
            "anonymous AtomGit client explicitly disables HF auth",
            constructor_tokens[-1] is False,
            f"token type={type(constructor_tokens[-1]).__name__}",
        )

        explicit_token = "atomgit_fake_explicit_credential"
        api_mod._atomgit_list_repo_files(
            "user/repo", explicit_token, "dataset"
        )
        check(
            "explicit AtomGit token is forwarded unchanged",
            constructor_tokens[-1] == explicit_token,
        )
    finally:
        api_mod.HfApi = original_hf_api

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
