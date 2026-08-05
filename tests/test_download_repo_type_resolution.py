#!/usr/bin/env python3
"""Verify deterministic model/dataset selection for CLI downloads."""

import sys
import tempfile
from pathlib import Path

import atomgit  # noqa: F401


api_mod = sys.modules["atomgit.api"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


class FakeHfApi:
    responses = {}
    calls = []

    def __init__(self, token=None):
        self.token = token

    def list_repo_files(self, repo_id, repo_type=None):
        self.calls.append(repo_type)
        response = self.responses[repo_type]
        if isinstance(response, Exception):
            raise response
        return list(response)


def resolve(responses, repo_type=None):
    FakeHfApi.responses = responses
    FakeHfApi.calls = []
    try:
        result = api_mod._atomgit_list_repo_files(
            "user/repo", "fake-token", repo_type
        )
        return result, None, list(FakeHfApi.calls)
    except Exception as error:
        return None, error, list(FakeHfApi.calls)


def main():
    original_hf_api = api_mod.HfApi
    original_open = api_mod._atomgit_open_url
    api_mod.HfApi = FakeHfApi
    try:
        result, error, calls = resolve(
            {None: [], "dataset": RuntimeError("404 dataset missing")}
        )
        check(
            "successful empty model survives later dataset 404",
            error is None and result == ("model", []),
            f"result={result!r} error={error!r}",
        )

        result, error, calls = resolve(
            {
                None: RuntimeError("401 Unauthorized"),
                "dataset": RuntimeError("404 Not Found"),
            }
        )
        check(
            "authentication failure is not hidden by later 404",
            error is not None and "401" in str(error),
            repr(error),
        )

        result, error, calls = resolve(
            {None: ["same.bin"], "dataset": ["same.bin"]}
        )
        check(
            "identical compatibility listings remain usable",
            error is None
            and result == ("model", ["same.bin"])
            and calls == [None, "dataset"],
            f"result={result!r} calls={calls!r}",
        )

        result, error, calls = resolve(
            {None: ["model.bin"], "dataset": ["dataset.csv"]}
        )
        check(
            "different listings require explicit repository type",
            error is not None and "repo-type" in str(error),
            repr(error),
        )
        check(
            "repository type ambiguity remains actionable after sanitizing",
            api_mod.sanitized_download_error(error)
            == "仓库类型不明确，请使用 --repo-type model 或 dataset",
        )

        result, error, calls = resolve(
            {None: ["model.bin"], "dataset": ["dataset.csv"]},
            repo_type="dataset",
        )
        check(
            "explicit dataset uses only dataset route",
            error is None
            and result == ("dataset", ["dataset.csv"])
            and calls == ["dataset"],
            f"result={result!r} calls={calls!r}",
        )

        opened_urls = []

        def always_missing(request, timeout=60):
            opened_urls.append(request.full_url)
            raise api_mod.urllib.error.HTTPError(
                request.full_url, 404, "Not Found", {}, None
            )

        api_mod._atomgit_open_url = always_missing
        with tempfile.TemporaryDirectory() as temporary_dir:
            try:
                api_mod._download_atomgit_file(
                    "user/repo",
                    "model",
                    "missing.bin",
                    Path(temporary_dir) / "missing.bin",
                    "fake-token",
                )
            except Exception:
                pass
        check(
            "resolve does not fall back to another repository type",
            len(opened_urls) == 1 and "/datasets/" not in opened_urls[0],
            repr(opened_urls),
        )
    finally:
        api_mod.HfApi = original_hf_api
        api_mod._atomgit_open_url = original_open

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
