#!/usr/bin/env python3
"""Verify filtered statistics, configurable batching, and projections."""
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


DEFAULT_IGNORES = ["._*", "**/._*", ".DS_Store", "**/.DS_Store"]


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
        "v5_get": api_mod._atomgit_v5_get_json,
    }
    resumable_calls = []
    ordinary_calls = []
    thread_counts = []
    target_validations = []
    resumable_events = []

    class FakeHfApi:
        fail_repo_id = None
        fail_repo_on_call = None
        repo_upload_counts = {}
        missing_repo_id = None
        validation_consumes_timeout = False

        def __init__(self, endpoint=None, token=None):
            self.endpoint = endpoint
            self.token = token

        def upload_large_folder(self, **kwargs):
            repo_id = kwargs["repo_id"]
            resumable_events.append(("upload", repo_id))
            call_number = self.repo_upload_counts.get(repo_id, 0) + 1
            self.repo_upload_counts[repo_id] = call_number
            if (
                repo_id == self.fail_repo_id
                or (repo_id, call_number) == self.fail_repo_on_call
            ):
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

    def fake_v5_get(path, token, timeout=15):
        repo_id = path.removeprefix("/repos/")
        resumable_events.append(("validate", repo_id))
        target_validations.append({
            "path": path,
            "token": token,
            "timeout": timeout,
        })
        if FakeHfApi.validation_consumes_timeout:
            api_mod.time.monotonic()
        if repo_id == FakeHfApi.missing_repo_id:
            raise RuntimeError("Repository Not Found")
        return {"full_name": repo_id, "default_branch": "main"}

    api_mod.HfApi = FakeHfApi
    api_mod.upload_folder = fake_upload_folder
    api_mod._atomgit_v5_get_json = fake_v5_get
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
            (source / "._root.bin").write_bytes(b"appledouble")
            (source / ".DS_Store").write_bytes(b"finder")
            nested = source / "nested"
            nested.mkdir()
            (nested / "._nested.bin").write_bytes(b"appledouble")
            (nested / ".DS_Store").write_bytes(b"finder")
            os.environ["HF_HOME"] = str(root / "hf-home")

            result = api_mod.api.upload_directory(
                source,
                "user/repo",
                ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                resumable=True,
            )
            projection_files = [item for _, files in resumable_calls for item in files]
            no_copy = all(os.path.samefile(item, source / item.name) for item in projection_files)
            resumable_ok = (
                result is True
                and len(resumable_calls) == 2
                and len(target_validations) == 1
                and target_validations[0] == {
                    "path": "/repos/user/repo",
                    "token": "offline-token",
                    "timeout": 300.0,
                }
                and resumable_events[:2]
                == [("validate", "user/repo"), ("upload", "user/repo")]
                and [len(files) for _, files in resumable_calls] == [20, 1]
                and all(kwargs["num_workers"] == 5 for kwargs, _ in resumable_calls)
                and all(join is None for join in InlineProcess.joins)
                and no_copy
                and not (source / ".cache").exists()
            )

            resumable_calls.clear()
            target_validations.clear()
            resumable_events.clear()
            InlineProcess.joins.clear()
            ticks = iter([100.0, 104.0, 105.0, 107.0])
            api_mod.time.monotonic = lambda: next(ticks)
            FakeHfApi.validation_consumes_timeout = True
            deadline_result = api_mod.api.upload_directory(
                source,
                "user/repo",
                ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                resumable=True,
                upload_timeout=10,
            )
            deadline_ok = (
                deadline_result is True
                and InlineProcess.joins == [None, None]
                and len(resumable_calls) == 2
                and target_validations[0]["timeout"] == 10
            )
            FakeHfApi.validation_consumes_timeout = False
            api_mod.time.monotonic = original["monotonic"]

            result = api_mod.api.upload_directory(
                source,
                "user/repo",
                ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                resumable=False,
                num_workers=3,
            )
            ordinary_ok = (
                result is True
                and len(ordinary_calls) == 2
                and [len(call["allow_patterns"]) for call in ordinary_calls] == [20, 1]
                and thread_counts == [3, 3]
                and all("batch_size" not in call for call in ordinary_calls)
            )

            expected_paths = [f"file-{index:02d}.bin" for index in range(21)]
            configurable_results = []
            for batch_size, expected_lengths in (
                (1, [1] * 21),
                (2, [2] * 10 + [1]),
                (10, [10, 10, 1]),
                (20, [20, 1]),
            ):
                ordinary_calls.clear()
                thread_counts.clear()
                configurable_result = api_mod.api.upload_directory(
                    source,
                    f"user/repo-ordinary-{batch_size}",
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                    resumable=False,
                    batch_size=batch_size,
                )
                ordinary_groups = [
                    call["allow_patterns"] for call in ordinary_calls
                ]
                flattened_ordinary = [
                    path for group in ordinary_groups for path in group
                ]

                resumable_calls.clear()
                target_validations.clear()
                configurable_resumable = api_mod.api.upload_directory(
                    source,
                    f"user/repo-resumable-{batch_size}",
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                    resumable=True,
                    batch_size=batch_size,
                )
                resumable_groups = []
                for kwargs, files in resumable_calls:
                    projection = Path(kwargs["folder_path"])
                    resumable_groups.append([
                        path.relative_to(projection).as_posix()
                        for path in files
                    ])
                flattened_resumable = [
                    path for group in resumable_groups for path in group
                ]
                configurable_results.append(
                    configurable_result is True
                    and configurable_resumable is True
                    and [len(group) for group in ordinary_groups]
                    == expected_lengths
                    and [len(group) for group in resumable_groups]
                    == expected_lengths
                    and flattened_ordinary == expected_paths
                    and flattened_resumable == expected_paths
                    and all(
                        "batch_size" not in kwargs
                        for kwargs, _ in resumable_calls
                    )
                )

            resumable_calls.clear()
            state_repo = "user/repo-batch-state"
            first_state = api_mod.api.upload_directory(
                source,
                state_repo,
                ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                resumable=True,
                batch_size=2,
            )
            size_two_projections = [
                Path(kwargs["folder_path"])
                for kwargs, _ in resumable_calls
            ]
            state_sentinel = (
                size_two_projections[0] / ".cache" / "huggingface"
                / "upload" / "batch-size-sentinel"
            )
            state_sentinel.parent.mkdir(parents=True, exist_ok=True)
            state_sentinel.write_text("size-two-state", encoding="utf-8")

            resumable_calls.clear()
            repeated_state = api_mod.api.upload_directory(
                source,
                state_repo,
                ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                resumable=True,
                batch_size=2,
            )
            repeated_projections = [
                Path(kwargs["folder_path"])
                for kwargs, _ in resumable_calls
            ]

            resumable_calls.clear()
            changed_state = api_mod.api.upload_directory(
                source,
                state_repo,
                ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                resumable=True,
                batch_size=10,
            )
            size_ten_projections = [
                Path(kwargs["folder_path"])
                for kwargs, _ in resumable_calls
            ]

            resumable_calls.clear()
            size_one_state = api_mod.api.upload_directory(
                source,
                state_repo,
                ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                resumable=True,
                batch_size=1,
            )
            size_one_projections = [
                Path(kwargs["folder_path"])
                for kwargs, _ in resumable_calls
            ]
            projection_state_ok = (
                first_state is True
                and repeated_state is True
                and changed_state is True
                and size_one_state is True
                and repeated_projections == size_two_projections
                and state_sentinel.read_text(encoding="utf-8")
                == "size-two-state"
                and set(size_ten_projections).isdisjoint(size_two_projections)
                and set(size_one_projections).isdisjoint(size_two_projections)
            )

            lifecycle_output = StringIO()
            resumable_calls.clear()
            target_validations.clear()
            with redirect_stdout(lifecycle_output):
                lifecycle_result = api_mod.api.upload_directory(
                    source,
                    "user/repo-lifecycle",
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
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
            target_validations.clear()
            skip_output = StringIO()
            with redirect_stdout(skip_output):
                skip_result = api_mod.api.upload_directory(
                    source,
                    "user/repo-lifecycle",
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                    resumable=True,
                )
            skip_text = skip_output.getvalue()
            skip_ok = (
                skip_result is True
                and len(resumable_calls) == 2
                and len(target_validations) == 1
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
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                    resumable=True,
                )
            api_mod.read_upload_metadata = original["read_metadata"]
            metadata_failure_text = metadata_failure_output.getvalue()
            metadata_failure_ok = (
                metadata_failure_result is True
                and "上传批次汇总: 计划 21，新增提交 21，续传跳过 0，确认完成 21"
                in metadata_failure_text
            )

            resumable_calls.clear()
            target_validations.clear()
            resumable_events.clear()
            FakeHfApi.missing_repo_id = "user/repo-missing"
            missing_output = StringIO()
            with redirect_stdout(missing_output):
                missing_result = api_mod.api.upload_directory(
                    source,
                    FakeHfApi.missing_repo_id,
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                    resumable=True,
                )
            FakeHfApi.missing_repo_id = None
            missing_text = missing_output.getvalue()
            missing_ok = (
                missing_result is False
                and len(target_validations) == 1
                and not resumable_calls
                and resumable_events == [("validate", "user/repo-missing")]
                and "仓库不存在" in missing_text
            )

            FakeHfApi.fail_repo_id = "user/repo-terminal-failure"
            failure_output = StringIO()
            with redirect_stdout(failure_output):
                failure_result = api_mod.api.upload_directory(
                    source,
                    FakeHfApi.fail_repo_id,
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
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

            configured_failure_repo = "user/repo-configured-failure"
            FakeHfApi.fail_repo_on_call = (configured_failure_repo, 2)
            FakeHfApi.repo_upload_counts.pop(configured_failure_repo, None)
            configured_failure_output = StringIO()
            with redirect_stdout(configured_failure_output):
                configured_failure_result = api_mod.api.upload_directory(
                    source,
                    configured_failure_repo,
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                    resumable=True,
                    batch_size=10,
                )
            FakeHfApi.fail_repo_on_call = None
            configured_failure_text = configured_failure_output.getvalue()
            configured_failure_ok = (
                configured_failure_result is False
                and "上传批次计划: 共 21 个文件，3 个批次，每批最多 10 个文件"
                in configured_failure_text
                and "[批次 1/3] 成功:" in configured_failure_text
                and "[批次 2/3] 失败: 累计确认完成 10/21，剩余 11"
                in configured_failure_text
                and "[批次 3/3] 开始" not in configured_failure_text
                and "上传批次汇总: 计划 21，新增提交 10，续传跳过 0，确认完成 10"
                in configured_failure_text
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
            print(f"[{'PASS' if deadline_ok else 'FAIL'}] validation retains request timeout while batches have no total deadline")
            print(f"[{'PASS' if ordinary_ok else 'FAIL'}] ordinary 20-file batches")
            print(f"[{'PASS' if all(configurable_results) else 'FAIL'}] exact 1/2/10/20 ordinary and resumable groups")
            print(f"[{'PASS' if projection_state_ok else 'FAIL'}] batch size isolates resumable projection state")
            print(f"[{'PASS' if lifecycle_ok else 'FAIL'}] 21-file lifecycle without progress bar")
            print(f"[{'PASS' if skip_ok else 'FAIL'}] completed resumable batches are skipped after remote validation")
            print(f"[{'PASS' if metadata_failure_ok else 'FAIL'}] metadata observation cannot fail upload")
            print(f"[{'PASS' if missing_ok else 'FAIL'}] missing target fails before hashing or upload")
            print(f"[{'PASS' if failure_ok else 'FAIL'}] terminal failure summary and ordering")
            print(f"[{'PASS' if configured_failure_ok else 'FAIL'}] configured mid-plan failure counts")
            print(f"[{'PASS' if large_plan_ok else 'FAIL'}] 700-file lifecycle plan with progress bar")
            return 0 if all((
                resumable_ok,
                deadline_ok,
                ordinary_ok,
                all(configurable_results),
                projection_state_ok,
                lifecycle_ok,
                skip_ok,
                metadata_failure_ok,
                missing_ok,
                failure_ok,
                configured_failure_ok,
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
        api_mod._atomgit_v5_get_json = original["v5_get"]


if __name__ == "__main__":
    raise SystemExit(main())
