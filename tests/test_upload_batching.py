#!/usr/bin/env python3
"""Verify filtered statistics, no-copy projections, and 20-file batching."""
import os
import queue
import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
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
        "read_metadata": api_mod.read_upload_metadata,
    }
    resumable_calls = []
    ordinary_calls = []
    thread_counts = []

    class FakeHfApi:
        fail_repo_id = None

        def __init__(self, token=None):
            self.token = token

        def upload_large_folder(self, **kwargs):
            if kwargs["repo_id"] == self.fail_repo_id:
                raise RuntimeError("offline terminal failure")
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

            lifecycle_output = StringIO()
            resumable_calls.clear()
            with redirect_stdout(lifecycle_output):
                lifecycle_result = api_mod.api.upload_directory(
                    source,
                    "user/repo-lifecycle",
                    ignore_patterns=["*.tmp"],
                    resumable=True,
                    progress_bar=False,
                )
            lifecycle_text = lifecycle_output.getvalue()
            lifecycle_ok = (
                lifecycle_result is True
                and "上传批次计划: 共 21 个文件，2 个批次，每批最多 20 个文件" in lifecycle_text
                and "[批次 1/2] 开始: 20 个文件" in lifecycle_text
                and "[批次 1/2] 成功:" in lifecycle_text
                and "[批次 2/2] 开始: 1 个文件" in lifecycle_text
                and lifecycle_text.index("[批次 1/2] 成功:")
                < lifecycle_text.index("[批次 2/2] 开始:")
                and "上传批次汇总: 计划 21，新增提交 21，续传跳过 0，确认完成 21" in lifecycle_text
            )

            for kwargs, files in resumable_calls:
                projection = Path(kwargs["folder_path"])
                for projected_file in files:
                    relative = projected_file.relative_to(projection).as_posix()
                    paths = api_mod.get_local_upload_paths(projection, relative)
                    metadata = api_mod.read_upload_metadata(projection, relative)
                    metadata.is_committed = True
                    metadata.save(paths)
            resumable_calls.clear()
            skip_output = StringIO()
            with redirect_stdout(skip_output):
                skip_result = api_mod.api.upload_directory(
                    source,
                    "user/repo-lifecycle",
                    ignore_patterns=["*.tmp"],
                    resumable=True,
                )
            skip_text = skip_output.getvalue()
            skip_ok = (
                skip_result is True
                and len(resumable_calls) == 2
                and "[批次 1/2] 续传跳过: 20 个已确认完成文件" in skip_text
                and "[批次 2/2] 续传跳过: 1 个已确认完成文件" in skip_text
                and "上传批次汇总: 计划 21，新增提交 0，续传跳过 21，确认完成 21" in skip_text
            )

            def fail_metadata_read(*args, **kwargs):
                raise OSError("offline metadata read failure")

            api_mod.read_upload_metadata = fail_metadata_read
            metadata_failure_output = StringIO()
            with redirect_stdout(metadata_failure_output):
                metadata_failure_result = api_mod.api.upload_directory(
                    source,
                    "user/repo-metadata-failure",
                    ignore_patterns=["*.tmp"],
                    resumable=True,
                )
            api_mod.read_upload_metadata = original["read_metadata"]
            metadata_failure_text = metadata_failure_output.getvalue()
            metadata_failure_ok = (
                metadata_failure_result is True
                and "上传批次汇总: 计划 21，新增提交 21，续传跳过 0，确认完成 21"
                in metadata_failure_text
            )

            FakeHfApi.fail_repo_id = "user/repo-terminal-failure"
            failure_output = StringIO()
            with redirect_stdout(failure_output):
                failure_result = api_mod.api.upload_directory(
                    source,
                    FakeHfApi.fail_repo_id,
                    ignore_patterns=["*.tmp"],
                    resumable=True,
                )
            FakeHfApi.fail_repo_id = None
            failure_text = failure_output.getvalue()
            failure_ok = (
                failure_result is False
                and "[批次 1/2] 失败: 累计确认完成 0/21，剩余 21" in failure_text
                and "[批次 2/2] 开始" not in failure_text
                and "断点元数据已保留" in failure_text
                and "上传批次汇总: 计划 21，新增提交 0，续传跳过 0，确认完成 0" in failure_text
            )

            large_source = root / "large-source"
            large_source.mkdir()
            for index in range(700):
                (large_source / f"file-{index:03d}.bin").write_bytes(b"x")
            large_output = StringIO()
            with redirect_stdout(large_output):
                large_result = api_mod.api.upload_directory(
                    large_source,
                    "user/repo-large-plan",
                    resumable=True,
                    progress_bar=True,
                )
            large_text = large_output.getvalue()
            large_plan_ok = (
                large_result is True
                and "上传批次计划: 共 700 个文件，35 个批次，每批最多 20 个文件" in large_text
                and "[批次 35/35] 成功:" in large_text
                and "上传批次汇总: 计划 700，新增提交 700，续传跳过 0，确认完成 700" in large_text
            )
            print(f"[{'PASS' if resumable_ok else 'FAIL'}] resumable 20-file batches/no-copy/unlimited")
            print(f"[{'PASS' if deadline_ok else 'FAIL'}] resumable batches share one total deadline")
            print(f"[{'PASS' if ordinary_ok else 'FAIL'}] ordinary 20-file batches")
            print(f"[{'PASS' if lifecycle_ok else 'FAIL'}] 21-file lifecycle without progress bar")
            print(f"[{'PASS' if skip_ok else 'FAIL'}] completed resumable batches are skipped after remote validation")
            print(f"[{'PASS' if metadata_failure_ok else 'FAIL'}] metadata observation cannot fail upload")
            print(f"[{'PASS' if failure_ok else 'FAIL'}] terminal failure summary and ordering")
            print(f"[{'PASS' if large_plan_ok else 'FAIL'}] 700-file lifecycle plan with progress bar")
            return 0 if all((
                resumable_ok,
                deadline_ok,
                ordinary_ok,
                lifecycle_ok,
                skip_ok,
                metadata_failure_ok,
                failure_ok,
                large_plan_ok,
            )) else 1
    finally:
        api_mod.HfApi = original["hf_api"]
        api_mod.multiprocessing.get_all_start_methods = original["methods"]
        api_mod.multiprocessing.get_context = original["context"]
        api_mod.upload_folder = original["upload_folder"]
        config.get_credentials = original["credentials"]
        api_mod.time.monotonic = original["monotonic"]
        api_mod.read_upload_metadata = original["read_metadata"]


if __name__ == "__main__":
    raise SystemExit(main())
