#!/usr/bin/env python3
"""Verify filtered statistics, no-copy projections, and 20-file batching."""
import os
import queue
import sys
import tempfile
from pathlib import Path

import atomgit  # noqa: F401

api_mod = sys.modules["atomgit.api"]
config = sys.modules["atomgit.config"].config


class InlineQueue:
    def __init__(self):
        self._queue = queue.Queue()

    def put(self, value):
        self._queue.put(value)

    def get(self, timeout=None):
        return self._queue.get(timeout=timeout)


class InlineProcess:
    joins = []

    def __init__(self, target, args):
        self.target, self.args, self.alive = target, args, False

    def start(self):
        self.alive = True
        try:
            self.target(*self.args)
        finally:
            self.alive = False

    def join(self, timeout=None):
        self.joins.append(timeout)

    def is_alive(self):
        return self.alive

    def terminate(self):
        self.alive = False


class InlineContext:
    def Queue(self):
        return InlineQueue()

    def Process(self, target, args):
        return InlineProcess(target, args)


def main():
    original = {
        "hf_api": api_mod.HfApi,
        "methods": api_mod.multiprocessing.get_all_start_methods,
        "context": api_mod.multiprocessing.get_context,
        "upload_folder": api_mod.upload_folder,
        "credentials": config.get_credentials,
        "monotonic": api_mod.time.monotonic,
    }
    resumable_calls = []
    ordinary_calls = []
    thread_counts = []

    class FakeHfApi:
        def __init__(self, token=None):
            self.token = token

        def upload_large_folder(self, **kwargs):
            root = Path(kwargs["folder_path"])
            files = sorted(
                path for path in root.rglob("*")
                if path.is_file()
                and not path.relative_to(root).as_posix().startswith(".cache/")
            )
            resumable_calls.append((kwargs, files))

        def create_commit(self, **kwargs):
            thread_counts.append(kwargs.get("num_threads"))

        def upload_folder(self, **kwargs):
            ordinary_calls.append(kwargs)
            self.create_commit(**kwargs)

    def fake_upload_folder(**kwargs):
        ordinary_calls.append(kwargs)

    api_mod.HfApi = FakeHfApi
    api_mod.upload_folder = fake_upload_folder
    api_mod.multiprocessing.get_all_start_methods = lambda: ["fork"]
    api_mod.multiprocessing.get_context = lambda method: InlineContext()
    config.get_credentials = lambda: {"token": "offline-token"}
    try:
        with tempfile.TemporaryDirectory(prefix="atomgit-batch-") as td:
            root = Path(td)
            source = root / "source"
            source.mkdir()
            for index in range(21):
                (source / f"file-{index:02d}.bin").write_bytes(bytes([index]))
            (source / "ignored.tmp").write_bytes(b"ignored")
            os.environ["HF_HOME"] = str(root / "hf-home")

            result = api_mod.api.upload_directory(
                source,
                "user/repo",
                ignore_patterns=["*.tmp"],
                resumable=True,
            )
            projection_files = [item for _, files in resumable_calls for item in files]
            no_copy = all(os.path.samefile(item, source / item.name) for item in projection_files)
            resumable_ok = (
                result is True
                and len(resumable_calls) == 2
                and [len(files) for _, files in resumable_calls] == [20, 1]
                and all(kwargs["num_workers"] == 5 for kwargs, _ in resumable_calls)
                and all(join is None for join in InlineProcess.joins)
                and no_copy
                and not (source / ".cache").exists()
            )

            resumable_calls.clear()
            InlineProcess.joins.clear()
            ticks = iter([100.0, 101.0, 103.0])
            api_mod.time.monotonic = lambda: next(ticks)
            deadline_result = api_mod.api.upload_directory(
                source,
                "user/repo",
                ignore_patterns=["*.tmp"],
                resumable=True,
                upload_timeout=10,
            )
            deadline_ok = (
                deadline_result is True
                and InlineProcess.joins == [9.0, 7.0]
            )
            api_mod.time.monotonic = original["monotonic"]

            result = api_mod.api.upload_directory(
                source,
                "user/repo",
                ignore_patterns=["*.tmp"],
                resumable=False,
                num_workers=3,
            )
            ordinary_ok = (
                result is True
                and len(ordinary_calls) == 2
                and [len(call["allow_patterns"]) for call in ordinary_calls] == [20, 1]
                and thread_counts == [3, 3]
            )
            print(f"[{'PASS' if resumable_ok else 'FAIL'}] resumable 20-file batches/no-copy/unlimited")
            print(f"[{'PASS' if deadline_ok else 'FAIL'}] resumable batches share one total deadline")
            print(f"[{'PASS' if ordinary_ok else 'FAIL'}] ordinary 20-file batches")
            return 0 if resumable_ok and deadline_ok and ordinary_ok else 1
    finally:
        api_mod.HfApi = original["hf_api"]
        api_mod.multiprocessing.get_all_start_methods = original["methods"]
        api_mod.multiprocessing.get_context = original["context"]
        api_mod.upload_folder = original["upload_folder"]
        config.get_credentials = original["credentials"]
        api_mod.time.monotonic = original["monotonic"]


if __name__ == "__main__":
    raise SystemExit(main())
