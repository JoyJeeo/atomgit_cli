#!/usr/bin/env python3
"""Dataset resumable uploads use AtomGit's verified shared model route."""

import queue
import sys
import tempfile
from pathlib import Path

import atomgit  # noqa: F401


api_mod = sys.modules["atomgit.api"]
config = sys.modules["atomgit.config"].config
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


class InlineQueue:
    def __init__(self):
        self._queue = queue.Queue()

    def put(self, value):
        self._queue.put(value)

    def get(self, timeout=None):
        return self._queue.get(timeout=timeout)


class InlineProcess:
    def __init__(self, target, args):
        self._target = target
        self._args = args
        self.daemon = False
        self._alive = False

    def start(self):
        self._alive = True
        try:
            self._target(*self._args)
        finally:
            self._alive = False

    def join(self, timeout=None):
        return None

    def is_alive(self):
        return self._alive

    def terminate(self):
        self._alive = False


class InlineContext:
    def Queue(self):
        return InlineQueue()

    def Process(self, target, args):
        return InlineProcess(target, args)


def main():
    original_api = api_mod.HfApi
    original_credentials = config.get_credentials
    original_methods = api_mod.multiprocessing.get_all_start_methods
    original_context = api_mod.multiprocessing.get_context
    constructor_calls = []
    upload_calls = []

    class StrictHfApi:
        def __init__(self, token=None):
            constructor_calls.append({"token": token})

        def upload_large_folder(
            self,
            repo_id,
            folder_path,
            *,
            repo_type,
            revision=None,
            private=None,
            allow_patterns=None,
            ignore_patterns=None,
            num_workers=None,
            print_report=True,
            print_report_every=60,
        ):
            upload_calls.append(
                {
                    "repo_id": repo_id,
                    "folder_path": folder_path,
                    "repo_type": repo_type,
                    "revision": revision,
                    "ignore_patterns": ignore_patterns,
                    "num_workers": num_workers,
                }
            )

    api_mod.HfApi = StrictHfApi
    config.get_credentials = lambda: {"token": "fake-dataset-resumable-token"}
    api_mod.multiprocessing.get_all_start_methods = lambda: ["fork"]
    api_mod.multiprocessing.get_context = lambda method: InlineContext()
    try:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / "dataset"
            root.mkdir()
            (root / "data.csv").write_text("x\n", encoding="utf-8")
            result = api_mod.api.upload_directory(
                root,
                "user/dataset",
                repo_type="dataset",
                revision="dev",
                ignore_patterns=["*.tmp"],
                resumable=True,
                num_workers=3,
            )

        check("dataset resumable succeeds", result is True)
        check(
            "token authenticates HfApi instance",
            constructor_calls == [{"token": "fake-dataset-resumable-token"}],
        )
        check("exactly one large-folder call", len(upload_calls) == 1)
        if upload_calls:
            call = upload_calls[0]
            check("dataset uses shared model route", call["repo_type"] == "model")
            check("repo id preserved", call["repo_id"] == "user/dataset")
            check("non-main revision forwarded", call["revision"] == "dev")
            check("ignore patterns forwarded", call["ignore_patterns"] == ["*.tmp"])
            check("worker count forwarded", call["num_workers"] == 3)
    finally:
        api_mod.HfApi = original_api
        config.get_credentials = original_credentials
        api_mod.multiprocessing.get_all_start_methods = original_methods
        api_mod.multiprocessing.get_context = original_context

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
