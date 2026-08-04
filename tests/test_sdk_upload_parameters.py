#!/usr/bin/env python3
"""SDK upload parameters reach the strict Hugging Face 1.1.7 boundary."""

import inspect
import tempfile
from pathlib import Path

import atomgit_hub
from huggingface_hub import upload_folder as real_upload_folder


results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    original_upload = atomgit_hub.hf_upload_folder
    calls = []

    def strict_upload(**kwargs):
        inspect.signature(real_upload_folder).bind(**kwargs)
        check(
            "upload source exists at strict boundary",
            Path(kwargs["folder_path"]).exists(),
        )
        calls.append(kwargs)
        return "commit-url"

    atomgit_hub.hf_upload_folder = strict_upload
    try:
        with tempfile.TemporaryDirectory() as source_dir:
            source = Path(source_dir)
            (source / "data.csv").write_text("value\n1\n", encoding="utf-8")

            result = atomgit_hub.upload_folder(
                source,
                "team/dataset",
                token="fake-token",
                repo_type="dataset",
                revision="main",
                commit_message="upload data",
                commit_description="offline parameter contract",
                path_in_repo="records/",
                ignore_patterns=["*.tmp"],
            )
            check("SDK result preserved", result == "commit-url")
            call = calls[-1]
            check(
                "dataset uses compatible model transfer route",
                call.get("repo_type") == "model",
            )
            check("main revision forwarded", call.get("revision") == "main")
            check(
                "commit description forwarded",
                call.get("commit_description") == "offline parameter contract",
            )
            check("ignore patterns forwarded", call.get("ignore_patterns") == ["*.tmp"])
            check("commit message forwarded", call.get("commit_message") == "upload data")

            atomgit_hub.upload_folder(
                source,
                "team/model",
                token="fake-token",
                repo_type="model",
            )
            check("model type forwarded", calls[-1].get("repo_type") == "model")
            check("unset revision omitted", "revision" not in calls[-1])

            before = len(calls)
            try:
                atomgit_hub.upload_folder(
                    source,
                    "team/model",
                    token="fake-token",
                    revision="dev",
                )
            except ValueError as error:
                check("non-main revision is actionable", "main" in str(error))
            else:
                check("non-main revision is actionable", False, "no exception")
            check("non-main revision makes no HF call", len(calls) == before)

            try:
                atomgit_hub.upload_folder(
                    source,
                    "team/model",
                    token="fake-token",
                    repo_type="space",
                )
            except ValueError as error:
                check("unsupported repo type is actionable", "model" in str(error))
            else:
                check("unsupported repo type is actionable", False, "no exception")
            check("unsupported repo type makes no HF call", len(calls) == before)
    finally:
        atomgit_hub.hf_upload_folder = original_upload

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
