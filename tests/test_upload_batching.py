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

    def get_nowait(self):
        return self._queue.get_nowait()

    def put_nowait(self, value):
        self._queue.put_nowait(value)


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
    def Queue(self, maxsize=0):
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
        "execute_resumable": api_mod._execute_resumable_upload_process,
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
        checkpoint_repo_id = None
        corrupt_checkpoint_repo_id = None
        corrupt_metadata_path = None
        validation_consumes_timeout = False

        def __init__(self, endpoint=None, token=None):
            self.endpoint = endpoint
            self.token = token

        def upload_large_folder(self, **kwargs):
            repo_id = kwargs["repo_id"]
            resumable_events.append(("upload", repo_id))
            call_number = self.repo_upload_counts.get(repo_id, 0) + 1
            self.repo_upload_counts[repo_id] = call_number
            root = Path(kwargs["folder_path"])
            files = sorted(
                path
                for path in root.rglob("*")
                if path.is_file()
                and not path.relative_to(root).as_posix().startswith(".cache/")
            )
            if repo_id == self.checkpoint_repo_id:
                for index, file_path in enumerate(files):
                    relative = file_path.relative_to(root).as_posix()
                    paths = api_mod.get_local_upload_paths(root, relative)
                    metadata = api_mod.read_upload_metadata(root, relative)
                    metadata.sha256 = f"{index:064x}"
                    metadata.upload_mode = "lfs" if index < 2 else "regular"
                    metadata.is_uploaded = index == 0
                    metadata.is_committed = index == 2
                    metadata.save(paths)
                raise RuntimeError("offline checkpoint failure")
            if repo_id == self.corrupt_checkpoint_repo_id:
                relative = files[0].relative_to(root).as_posix()
                paths = api_mod.get_local_upload_paths(root, relative)
                paths.metadata_path.write_text("corrupt\n", encoding="utf-8")
                type(self).corrupt_metadata_path = paths.metadata_path
                raise RuntimeError("offline corrupt checkpoint failure")
            if (
                repo_id == self.fail_repo_id
                or (repo_id, call_number) == self.fail_repo_on_call
            ):
                raise RuntimeError("offline terminal failure")
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

            def recover_every_file(**kwargs):
                projection = Path(kwargs["upload_kwargs"]["folder_path"])
                recovered = sum(
                    1
                    for path in projection.rglob("*")
                    if path.is_file()
                    and not path.relative_to(projection)
                    .as_posix()
                    .startswith(".cache/")
                )
                return {"recovered": recovered}

            recovery_output = StringIO()
            api_mod._execute_resumable_upload_process = recover_every_file
            with redirect_stdout(recovery_output):
                recovery_result = api_mod.api.upload_directory(
                    source,
                    "user/repo-recovered",
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                    resumable=True,
                )
            api_mod._execute_resumable_upload_process = original["execute_resumable"]
            recovery_text = recovery_output.getvalue()
            recovery_summary_ok = (
                recovery_result is True
                and "上传批次汇总: 计划 21，新增提交 0，续传跳过 21，确认完成 21"
                in recovery_text
            )
            target_validations.clear()
            resumable_events.clear()

            def recover_one_then_conflict(**kwargs):
                projection = Path(kwargs["upload_kwargs"]["folder_path"])
                path = sorted(
                    item.relative_to(projection).as_posix()
                    for item in projection.rglob("*")
                    if item.is_file()
                    and not item.relative_to(projection)
                    .as_posix()
                    .startswith(".cache/")
                )[0]
                paths = api_mod.get_local_upload_paths(projection, path)
                metadata = api_mod.read_upload_metadata(projection, path)
                metadata.sha256 = "00" * 32
                metadata.upload_mode = "regular"
                metadata.is_committed = True
                metadata.save(paths)
                raise api_mod.ResumableWorkerError(
                    "remote_commit_conflict", confirmed=1, remaining=19
                )

            conflict_output = StringIO()
            api_mod._execute_resumable_upload_process = recover_one_then_conflict
            with redirect_stdout(conflict_output):
                conflict_result = api_mod.api.upload_directory(
                    source,
                    "user/repo-conflict",
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                    resumable=True,
                )
            api_mod._execute_resumable_upload_process = original["execute_resumable"]
            conflict_text = conflict_output.getvalue()
            conflict_summary_ok = (
                conflict_result is False
                and "上传批次汇总: 计划 21，新增提交 0，续传跳过 1，确认完成 1"
                in conflict_text
                and "确认复用 1，冲突 19，仍需提交 19" in conflict_text
            )
            target_validations.clear()
            resumable_events.clear()

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
                progress_callback=lambda progress: ordinary_calls.append(progress),
            )
            ordinary_ok = (
                result is True
                and len(ordinary_calls) == 2
                and all("batch" not in call for call in ordinary_calls)
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
            lifecycle_progress = []
            resumable_calls.clear()
            target_validations.clear()
            with redirect_stdout(lifecycle_output):
                lifecycle_result = api_mod.api.upload_directory(
                    source,
                    "user/repo-lifecycle",
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                    resumable=True,
                    progress_bar=False,
                    progress_callback=lifecycle_progress.append,
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
                and lifecycle_progress
                == [
                    {"batch": "0/2", "files_total": 21, "files_done": 0},
                    {"batch": "1/2", "files_total": 21, "files_done": 0},
                    {"batch": "1/2", "files_total": 21, "files_done": 20},
                    {"batch": "2/2", "files_total": 21, "files_done": 20},
                    {"batch": "2/2", "files_total": 21, "files_done": 21},
                ]
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
            skip_progress = []
            skip_output = StringIO()
            with redirect_stdout(skip_output):
                skip_result = api_mod.api.upload_directory(
                    source,
                    "user/repo-lifecycle",
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                    resumable=True,
                    progress_callback=skip_progress.append,
                )
            skip_text = skip_output.getvalue()
            skip_ok = (
                skip_result is True
                and len(resumable_calls) == 2
                and len(target_validations) == 1
                and "[批次 1/2] 续传跳过: 20 个已确认完成文件" in skip_text
                and "[批次 2/2] 续传跳过: 1 个已确认完成文件" in skip_text
                and "上传批次汇总: 计划 21，新增提交 0，续传跳过 21，确认完成 21" in skip_text
                and skip_progress[-1]
                == {"batch": "2/2", "files_total": 21, "files_done": 21}
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
            missing_progress = []
            missing_output = StringIO()
            with redirect_stdout(missing_output):
                missing_result = api_mod.api.upload_directory(
                    source,
                    FakeHfApi.missing_repo_id,
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                    resumable=True,
                    progress_callback=missing_progress.append,
                )
            FakeHfApi.missing_repo_id = None
            missing_text = missing_output.getvalue()
            missing_ok = (
                missing_result is False
                and len(target_validations) == 1
                and not resumable_calls
                and resumable_events == [("validate", "user/repo-missing")]
                and "仓库不存在" in missing_text
                and missing_progress
                == [{"batch": "0/2", "files_total": 21, "files_done": 0}]
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

            checkpoint_repo = "user/repo-checkpoint-failure"
            FakeHfApi.checkpoint_repo_id = checkpoint_repo
            checkpoint_progress = []
            checkpoint_failure_output = StringIO()
            with redirect_stdout(checkpoint_failure_output):
                checkpoint_failure_result = api_mod.api.upload_directory(
                    source,
                    checkpoint_repo,
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                    resumable=True,
                    path_in_repo="remote/prefix",
                    progress_callback=checkpoint_progress.append,
                )
            FakeHfApi.checkpoint_repo_id = None
            checkpoint_failure_text = checkpoint_failure_output.getvalue()
            checkpoint_failure_ok = (
                checkpoint_failure_result is False
                and "[批次 1/2] 失败: 累计确认完成 1/21，剩余 20"
                in checkpoint_failure_text
                and "[批次 1/2] 断点状态: 已哈希 20/20（20.0 B/20.0 B），"
                "LFS 已预上传 1/2（1.0 B/2.0 B），"
                "本地待确认 19（19.0 B）" in checkpoint_failure_text
                and "上传批次汇总: 计划 21，新增提交 1，续传跳过 0，确认完成 1"
                in checkpoint_failure_text
                and checkpoint_progress[-1]
                == {"batch": "1/2", "files_total": 21, "files_done": 1}
            )

            corrupt_repo = "user/repo-corrupt-checkpoint"
            FakeHfApi.corrupt_checkpoint_repo_id = corrupt_repo
            corrupt_output = StringIO()
            with redirect_stdout(corrupt_output):
                corrupt_result = api_mod.api.upload_directory(
                    source,
                    corrupt_repo,
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                    resumable=True,
                )
            FakeHfApi.corrupt_checkpoint_repo_id = None
            corrupt_text = corrupt_output.getvalue()
            corrupt_ok = (
                corrupt_result is False
                and "[批次 1/2] 断点状态: 已哈希 0/20（0 B/20.0 B），"
                "LFS 已预上传 0/0（0 B/0 B），本地待确认 19（19.0 B），"
                "状态未知 1（1.0 B）" in corrupt_text
                and FakeHfApi.corrupt_metadata_path is not None
                and FakeHfApi.corrupt_metadata_path.read_text(encoding="utf-8")
                == "corrupt\n"
                and str(FakeHfApi.corrupt_metadata_path) not in corrupt_text
                and "offline corrupt checkpoint failure" not in corrupt_text
            )

            configured_failure_repo = "user/repo-configured-failure"
            FakeHfApi.fail_repo_on_call = (configured_failure_repo, 2)
            FakeHfApi.repo_upload_counts.pop(configured_failure_repo, None)
            configured_failure_progress = []
            configured_failure_output = StringIO()
            with redirect_stdout(configured_failure_output):
                configured_failure_result = api_mod.api.upload_directory(
                    source,
                    configured_failure_repo,
                    ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                    resumable=True,
                    batch_size=10,
                    progress_callback=configured_failure_progress.append,
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
                and configured_failure_progress[-1]
                == {"batch": "2/3", "files_total": 21, "files_done": 10}
            )

            def broken_progress_callback(progress):
                raise RuntimeError("must not affect upload")

            callback_failure_result = api_mod.api.upload_directory(
                source,
                "user/repo-callback-failure",
                ignore_patterns=DEFAULT_IGNORES + ["*.tmp"],
                resumable=True,
                progress_callback=broken_progress_callback,
            )
            callback_failure_ok = callback_failure_result is True

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
            print(
                f"[{'PASS' if checkpoint_failure_ok else 'FAIL'}] failure summary preserves checkpoint progress"
            )
            print(
                f"[{'PASS' if corrupt_ok else 'FAIL'}] corrupt checkpoint remains unchanged and unknown"
            )
            print(f"[{'PASS' if configured_failure_ok else 'FAIL'}] configured mid-plan failure counts")
            print(
                f"[{'PASS' if callback_failure_ok else 'FAIL'}] "
                "progress callback failures are isolated"
            )
            print(f"[{'PASS' if large_plan_ok else 'FAIL'}] 700-file lifecycle plan with progress bar")
            print(
                f"[{'PASS' if recovery_summary_ok else 'FAIL'}] "
                "recovered batches report zero new commits"
            )
            print(
                f"[{'PASS' if conflict_summary_ok else 'FAIL'}] "
                "conflict summaries do not count recovered files as new commits"
            )
            return (
                0
                if all(
                    (
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
                        checkpoint_failure_ok,
                        corrupt_ok,
                        configured_failure_ok,
                        callback_failure_ok,
                        large_plan_ok,
                        recovery_summary_ok,
                        conflict_summary_ok,
                    )
                )
                else 1
            )
    finally:
        api_mod.HfApi = original["hf_api"]
        api_mod.multiprocessing.get_all_start_methods = original["methods"]
        api_mod.multiprocessing.get_context = original["context"]
        api_mod.upload_folder = original["upload_folder"]
        config.get_credentials = original["credentials"]
        api_mod.time.monotonic = original["monotonic"]
        api_mod.read_upload_metadata = original["read_metadata"]
        api_mod._atomgit_v5_get_json = original["v5_get"]
        api_mod._execute_resumable_upload_process = original["execute_resumable"]


def retry_round_checks():
    from unittest.mock import patch

    import httpx

    from atomgit.adapters.upload import retry
    from atomgit.adapters.upload.errors import ResumableRecoveryStateError

    attempts = []
    committed = []

    def mode(items, api, repo_id, repo_type, revision):
        for paths, metadata in items:
            metadata.upload_mode = "lfs"
            metadata.should_ignore = False
            metadata.save(paths)

    def preupload(items, api, repo_id, repo_type, revision):
        paths, metadata = items[0]
        attempts.append(paths.path_in_repo)
        if paths.path_in_repo == "bad.bin" and attempts.count("bad.bin") <= 12:
            raise httpx.ConnectError("secret=never-log-this")
        metadata.is_uploaded = True
        metadata.save(paths)

    def commit(items, api, repo_id, repo_type, revision):
        paths, metadata = items[0]
        committed.append(paths.path_in_repo)
        metadata.is_committed = True
        metadata.save(paths)

    with (
        tempfile.TemporaryDirectory() as td,
        patch.object(retry.hf, "_get_upload_mode", mode),
        patch.object(retry.hf, "_preupload_lfs", preupload),
        patch.object(retry.hf, "_commit", commit),
        patch.object(retry, "retry_delay", return_value=0),
    ):
        root = Path(td)
        (root / "bad.bin").write_bytes(b"bad")
        (root / "good.bin").write_bytes(b"good")
        output = StringIO()
        with redirect_stdout(output):
            result = retry.run_upload_round(
                None, "user/test", root, repo_type="dataset", num_workers=2
            )
        assert result["pending"] == 1 and committed == ["good.bin"]
        assert attempts.count("bad.bin") == 3
        first_log = output.getvalue()
        assert first_log.count("[上传失败]") == 3, first_log
        assert "bad.bin" in first_log and "阶段：LFS 预上传" in first_log
        assert (
            "原因：网络连接失败" in first_log and "异常类型：ConnectError" in first_log
        )
        assert first_log.count("[本轮重试]") == 2, first_log
        assert first_log.count("[加入候补]") == 1, first_log
        assert "当前候补：1 个｜正在补传：0 个｜异常待处理：0 个" in first_log
        with redirect_stdout(output):
            for _ in range(4):
                result = retry.run_upload_round(
                    None, "user/test", root, repo_type="dataset", num_workers=2
                )
        assert output.getvalue().count("[加入候补]") == 4
        assert "当前候补：2 个" not in output.getvalue()
        state = retry.RetryState(root).files["bad.bin"]
        assert result["pending"] == 0 and attempts.count("bad.bin") == 13
        assert state["failures"] == 12 and state["rounds"] == 4
        assert committed == ["good.bin", "bad.bin"], committed
        assert "never-log-this" not in output.getvalue()
        checkpoint = retry.RetryState(root)
        checkpoint.path.write_text("invalid", encoding="utf-8")
        try:
            retry.RetryState(root)
        except ResumableRecoveryStateError:
            pass
        else:
            raise AssertionError("corrupt retry state must stop safely")

    mode_calls = []

    def changed_server_mode(items, api, repo_id, repo_type, revision):
        mode_calls.append(1)
        mode(items, api, repo_id, repo_type, revision)
        paths, metadata = items[0]
        metadata.should_ignore = len(mode_calls) == 1
        metadata.save(paths)

    with (
        tempfile.TemporaryDirectory() as td,
        patch.object(retry.hf, "_get_upload_mode", changed_server_mode),
        patch.object(retry.hf, "_preupload_lfs", preupload),
        patch.object(retry.hf, "_commit", commit),
        patch.object(retry, "retry_delay", return_value=0),
    ):
        root = Path(td)
        (root / "excluded.bin").write_bytes(b"content")
        abnormal_output = StringIO()
        with redirect_stdout(abnormal_output):
            result = retry.run_upload_round(
                None, "user/test", root, repo_type="dataset"
            )
            assert result["abnormal"] == 1
        assert (
            "当前候补：0 个｜正在补传：0 个｜异常待处理：1 个"
            in abnormal_output.getvalue()
        )
        assert "[加入候补]" not in abnormal_output.getvalue()
        assert (
            retry.run_upload_round(None, "user/test", root, repo_type="dataset")[
                "pending"
            ]
            == 0
        )
        assert len(mode_calls) == 2, "cached exclusions must be queried again"

    class Terminal(StringIO):
        def isatty(self):
            return True

    terminal = Terminal()
    with (
        redirect_stdout(terminal),
        patch.object(retry.sys, "stderr", terminal),
        patch.dict(os.environ),
    ):
        os.environ.pop("NO_COLOR", None)
        retry._warning("pending", abnormal=True)
    assert "\x1b[31m" in terminal.getvalue()

    request = httpx.Request("PUT", "https://hub.gitcode.com/object")
    error = httpx.HTTPStatusError(
        "secret",
        request=request,
        response=httpx.Response(429, headers={"Retry-After": "900"}, request=request),
    )
    assert retry.retry_delay(error) == 900
    assert retry.retry_delay(httpx.ConnectError("offline"), 1000000) == 300
    report = retry.RetryReport()
    report.batches[0] = {"pending": 1, "abnormal": 1, "failures": 12}
    assert not callable(report), "queue accounting must not schedule periodic warnings"
    assert report.counts() == {"queued": 0, "abnormal": 1}
    print(
        "[PASS] fair file retries exceed twelve failures; healthy file commits first; durable counters and safe logs"
    )


def retry_parent_checks():
    from unittest.mock import patch

    from huggingface_hub._local_folder import (
        get_local_upload_paths,
        read_upload_metadata,
    )

    from atomgit.adapters.upload import service
    from atomgit.adapters.upload.errors import ResumableWorkerError

    calls = []
    events = []

    def execute(**kwargs):
        selected = kwargs["selected_paths"]
        calls.append(selected)
        root = Path(kwargs["upload_kwargs"]["folder_path"])
        remaining = 1 if len(calls) == 1 else 0
        for name in selected[remaining:]:
            paths = get_local_upload_paths(root, name)
            metadata = read_upload_metadata(root, name)
            metadata.is_committed = True
            metadata.save(paths)
        return {
            "recovered": 0,
            "pending": remaining,
            "delay": 0,
            "cooldown": 0,
            "abnormal": 0,
            "failures": 3 if remaining else 0,
        }

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        source = root / "source"
        source.mkdir()
        for index in range(4):
            (source / f"{index}.bin").write_bytes(b"file")
        with (
            patch.dict(os.environ, {"HF_HOME": str(root / "cache")}),
            patch.object(
                config, "get_credentials", return_value={"token": "offline-token"}
            ),
            patch.object(service, "_validate_resumable_upload_target"),
            patch.object(service, "_execute_resumable_upload_process", execute),
            redirect_stdout(StringIO()) as output,
        ):
            result = api_mod.api.upload_directory(
                source,
                "user/rotation",
                resumable=True,
                batch_size=2,
                progress_callback=events.append,
            )
        assert result is True
        assert calls == [
            ("0.bin", "1.bin"),
            ("2.bin", "3.bin"),
            ("0.bin", "1.bin"),
        ], calls
        assert events[-1]["files_done"] == 4
        assert (
            "计划 4，新增提交 4，续传跳过 0，确认完成 4" in output.getvalue()
        ), output.getvalue()
        with (
            patch.dict(os.environ, {"HF_HOME": str(root / "cache")}),
            patch.object(
                config, "get_credentials", return_value={"token": "offline-token"}
            ),
            patch.object(service, "_validate_resumable_upload_target"),
            patch.object(
                service,
                "_execute_resumable_upload_process",
                side_effect=ResumableWorkerError("timeout"),
            ) as execute_failure,
            patch.object(service.time, "sleep", side_effect=KeyboardInterrupt),
            redirect_stdout(StringIO()),
        ):
            try:
                api_mod.api.upload_directory(
                    source, "user/cancel-retry", resumable=True, batch_size=2
                )
            except KeyboardInterrupt:
                pass
            else:
                raise AssertionError(
                    "transient failures must keep retrying until cancellation"
                )
        assert (
            execute_failure.call_count >= 2
        ), "later batches must get their turn before cooldown"
        with (
            patch.dict(os.environ, {"HF_HOME": str(root / "cache")}),
            patch.object(
                config, "get_credentials", return_value={"token": "offline-token"}
            ),
            patch.object(service, "_validate_resumable_upload_target"),
            patch.object(
                service,
                "_execute_resumable_upload_process",
                side_effect=ResumableWorkerError("authentication"),
            ) as execute_failure,
            redirect_stdout(StringIO()),
        ):
            assert (
                api_mod.api.upload_directory(
                    source, "user/auth-failure", resumable=True, batch_size=2
                )
                is False
            )
        assert execute_failure.call_count == 1
    calls.clear()
    roots = {}

    def invalidate_then_finish(**kwargs):
        index = kwargs["batch_context"][0]
        root = Path(kwargs["upload_kwargs"]["folder_path"])
        roots[index] = root
        result = execute(**kwargs)
        if len(calls) == 2:
            get_local_upload_paths(roots[1], "1.bin").metadata_path.unlink()
        elif len(calls) == 3:
            for name in kwargs["selected_paths"]:
                get_local_upload_paths(root, name).metadata_path.unlink()
            result.update(pending=2, failures=6)
        return result

    with tempfile.TemporaryDirectory() as td:
        source = Path(td) / "source"
        source.mkdir()
        for index in range(4):
            (source / f"{index}.bin").write_bytes(b"file")
        with (
            patch.dict(os.environ, {"HF_HOME": str(Path(td) / "cache")}),
            patch.object(
                config, "get_credentials", return_value={"token": "offline-token"}
            ),
            patch.object(service, "_validate_resumable_upload_target"),
            patch.object(
                service, "_execute_resumable_upload_process", invalidate_then_finish
            ),
            redirect_stdout(StringIO()) as output,
        ):
            assert api_mod.api.upload_directory(
                source, "user/invalidation", resumable=True, batch_size=2
            )
        assert len(calls) == 4
        assert (
            "计划 4，新增提交 4，续传跳过 0，确认完成 4" in output.getvalue()
        ), output.getvalue()
    print(
        "[PASS] later batches commit before retries; partial counts stay exact; transient cancellation and global auth stop"
    )


def queue_observability_checks():
    from unittest.mock import patch

    import httpx
    from huggingface_hub._local_folder import (
        get_local_upload_paths,
        read_upload_metadata,
    )

    from atomgit.adapters.upload import retry, service

    failing = True
    calls = []
    uploads = []
    roots = []

    def mode(items, **kwargs):
        for paths, metadata in items:
            metadata.upload_mode = "lfs"
            metadata.should_ignore = False
            metadata.save(paths)

    def preupload(items, **kwargs):
        paths, metadata = items[0]
        uploads.append(paths.path_in_repo)
        if failing:
            raise httpx.ConnectError("signed-url-secret-must-not-appear")
        metadata.is_uploaded = True
        metadata.save(paths)

    def commit(items, **kwargs):
        for paths, metadata in items:
            metadata.is_committed = True
            metadata.save(paths)

    def execute(**kwargs):
        calls.append(kwargs["retry_counts"])
        if failing and len(calls) == 3:
            raise KeyboardInterrupt
        root = Path(kwargs["upload_kwargs"]["folder_path"])
        roots.append(root)
        return {
            "recovered": 0,
            **retry.run_upload_round(
                None,
                **kwargs["upload_kwargs"],
                selected_paths=kwargs["selected_paths"],
                retry_counts=kwargs["retry_counts"],
                batch_context=kwargs["batch_context"],
            ),
        }

    with (
        tempfile.TemporaryDirectory() as td,
        patch.object(
            config, "get_credentials", return_value={"token": "offline-token"}
        ),
        patch.object(service, "_validate_resumable_upload_target"),
        patch.object(service, "_execute_resumable_upload_process", execute),
        patch.object(retry.hf, "_get_upload_mode", mode),
        patch.object(retry.hf, "_preupload_lfs", preupload),
        patch.object(retry.hf, "_commit", commit),
        patch.object(retry, "retry_delay", return_value=0),
        patch.dict(os.environ, {"HF_HOME": str(Path(td) / "cache")}),
    ):
        source = Path(td) / "source"
        source.mkdir()
        for name in ("a.bin", "b.bin"):
            (source / name).write_bytes(b"data")
        first = StringIO()
        with redirect_stdout(first):
            try:
                api_mod.api.upload_directory(
                    source,
                    "user/queue",
                    resumable=True,
                    batch_size=1,
                    path_in_repo="prefix",
                    num_workers=1,
                )
            except KeyboardInterrupt:
                pass
            else:
                raise AssertionError("expected explicit cancellation after two rounds")
        text = first.getvalue()
        assert text.count("[加入候补]") == 2, text
        assert "当前候补：2 个｜正在补传：0 个｜异常待处理：0 个" in text
        assert calls[:2] == [{"queued": 0, "abnormal": 0}, {"queued": 1, "abnormal": 0}]
        assert len(uploads) == 6
        # Restart: global totals must include the later batch before it runs.
        failing = False
        calls.clear()
        second = StringIO()
        with redirect_stdout(second):
            assert api_mod.api.upload_directory(
                source,
                "user/queue",
                resumable=True,
                batch_size=1,
                path_in_repo="prefix",
                num_workers=1,
            )
        text = second.getvalue()
        assert "[恢复候补队列] 当前候补：2 个" in text, text
        assert "当前候补：1 个｜正在补传：1 个｜异常待处理：0 个" in text
        assert "当前候补：0 个｜正在补传：1 个｜异常待处理：0 个" in text
        assert "复用已有哈希" in text and "整文件 PUT 从头传输" in text
        assert calls == [{"queued": 1, "abnormal": 0}, {"queued": 0, "abnormal": 0}]
        assert len(uploads) == 8
        assert "signed-url-secret" not in text + first.getvalue()
        # Successful metadata excludes historical failures; a changed source
        # invalidates completion, while deselected and duplicate entries do not inflate totals.
        state = retry.RetryState(roots[0])
        assert state.pending_summary(["prefix/a.bin"])["pending"] == 0
        (source / "a.bin").write_bytes(b"changed-source")
        assert state.pending_summary(["prefix/a.bin", "prefix/a.bin"])["pending"] == 1
        assert state.pending_summary(["prefix/b.bin"])["pending"] == 0
        # Counters reconstruct from source even when the projection still points
        # to an old inode; observational reads never repair corrupt metadata.
        paths = get_local_upload_paths(roots[1], "prefix/b.bin")
        replacement = source / "replacement"
        replacement.write_bytes(b"different inode")
        replacement.replace(source / "b.bin")
        other = retry.RetryState(roots[1])
        assert (
            other.pending_summary(["prefix/b.bin"], {"prefix/b.bin": source / "b.bin"})[
                "pending"
            ]
            == 1
        )
        paths.metadata_path.write_text("broken metadata")
        assert other.pending_summary(["prefix/b.bin"])["pending"] == 1
        assert paths.metadata_path.read_text() == "broken metadata"
        record = other.files["prefix/b.bin"]
        record.update(category="unknown", status="prepare", attempts=1, rounds=0)
        other.save()
        assert (
            retry.RetryState(roots[1]).pending_summary(["prefix/b.bin"])["abnormal"]
            == 1
        )

    # An object already uploaded before a failed commit must not be sent again.
    with (
        tempfile.TemporaryDirectory() as td,
        patch.object(retry.hf, "_get_upload_mode", mode),
        patch.object(
            retry.hf, "_preupload_lfs", side_effect=AssertionError("must reuse object")
        ),
        patch.object(retry.hf, "_commit", commit),
    ):
        root = Path(td)
        (root / "object.bin").write_bytes(b"object")
        paths = get_local_upload_paths(root, "object.bin")
        metadata = read_upload_metadata(root, "object.bin")
        retry.hf._compute_sha256((paths, metadata))
        metadata.upload_mode = "lfs"
        metadata.should_ignore = False
        metadata.is_uploaded = True
        metadata.save(paths)
        state = retry.RetryState(root)
        record = state.record("object.bin")
        stat = paths.file_path.stat()
        record.update(
            failures=3,
            attempts=3,
            rounds=1,
            status="retry",
            category="connection",
            signature=[stat.st_size, stat.st_mtime_ns],
        )
        state.save()
        output = StringIO()
        with redirect_stdout(output):
            result = retry.run_upload_round(
                None,
                "user/test",
                root,
                repo_type="model",
                selected_paths=("object.bin", "object.bin"),
            )
        assert result["pending"] == 0
        assert output.getvalue().count("[开始补传]") == 1
        assert "本地记录对象已上传，尝试复用并核对提交" in output.getvalue()
        assert "从头传输" not in output.getvalue()
        # A stale retry record for an already committed object is not queued.
        assert retry.RetryState(root).pending_summary(["object.bin"])["pending"] == 0
        output = StringIO()
        with redirect_stdout(output):
            retry.run_upload_round(None, "user/test", root, repo_type="model")
        assert "[开始补传]" not in output.getvalue(), output.getvalue()
        assert "已确认提交，跳过上传" in output.getvalue()
    print(
        "[PASS] immediate global queue counts, cross-batch restart, deduplication and truthful object reuse"
    )

    # Concurrent retry dispatch subtracts waiting files exactly once, while
    # nontransient failures enter the separate abnormal category.
    import threading

    barrier = threading.Barrier(2)

    def abnormal_upload(items, **kwargs):
        barrier.wait(timeout=5)
        raise ValueError("secret-never-print")

    with (
        tempfile.TemporaryDirectory() as td,
        patch.object(retry.hf, "_get_upload_mode", mode),
        patch.object(retry.hf, "_preupload_lfs", abnormal_upload),
        patch.object(retry, "retry_delay", return_value=0),
    ):
        root = Path(td)
        state = retry.RetryState(root)
        for name in ("one.bin", "two.bin"):
            (root / name).write_bytes(b"data")
            state.record(name).update(
                failures=3, attempts=3, rounds=1, status="retry", category="connection"
            )
        state.save()
        output = StringIO()
        with redirect_stdout(output):
            result = retry.run_upload_round(
                None,
                "user/test",
                root,
                repo_type="model",
                num_workers=2,
                selected_paths=("one.bin", "two.bin"),
                retry_counts={"queued": 7, "abnormal": 2},
            )
        text = output.getvalue()
        assert "当前候补：8 个｜正在补传：1 个｜异常待处理：2 个" in text
        assert "当前候补：7 个｜正在补传：2 个｜异常待处理：2 个" in text
        assert "当前候补：7 个｜正在补传：0 个｜异常待处理：4 个" in text
        assert result["abnormal"] == result["pending"] == 2
        assert "secret-never-print" not in text
        # An interrupted first round's ordinary backoff is not formal enqueue.
        state = retry.RetryState(root)
        for record in state.files.values():
            record.update(
                failures=1,
                attempts=1,
                rounds=0,
                status="retry",
                category="connection",
                next_attempt=retry.time.time() + 60,
            )
        state.save()
        assert state.pending_summary(["one.bin", "two.bin"])["pending"] == 0
        output = StringIO()
        with redirect_stdout(output):
            result = retry.run_upload_round(
                None, "user/test", root, repo_type="model", num_workers=2
            )
        assert result["pending"] == 2 and "[开始补传]" not in output.getvalue()
        report = retry.RetryReport()
        report.batches[0] = {**result, "queued": 0}
        assert report.counts() == {"queued": 0, "abnormal": 0}
        for record in state.files.values():
            record.update(category="unknown", status="prepare")
        state.save()
        with redirect_stdout(StringIO()):
            result = retry.run_upload_round(
                None, "user/test", root, repo_type="model", num_workers=2
            )
        assert result["abnormal"] == 2, result


def event_failure_checks():
    import ssl
    import time
    from unittest.mock import patch

    import httpx

    from atomgit.adapters.upload import retry, service

    request = httpx.Request("PUT", "https://hub.gitcode.com/object?token=do-not-log")
    errors = [
        httpx.HTTPStatusError(
            "do-not-log", request=request, response=httpx.Response(502, request=request)
        ),
        httpx.WriteTimeout("do-not-log", request=request),
        httpx.ConnectError(
            "do-not-log",
            request=httpx.Request(
                "POST",
                "https://hub.atomgit.com/user/repo.git/info/lfs/objects/batch?token=do-not-log",
            ),
        ),
        RuntimeError("do-not-log"),
    ]
    errors[2].__cause__ = ssl.SSLEOFError("do-not-log")
    clock = [time.time() + 1]
    attempted = []

    def mode(items, **kwargs):
        for paths, metadata in items:
            metadata.upload_mode = "lfs"
            metadata.should_ignore = False
            metadata.save(paths)

    def fail(items, **kwargs):
        attempted.append(1)
        raise errors[len(attempted) - 1]

    with (
        tempfile.TemporaryDirectory() as td,
        patch.object(retry.hf, "_get_upload_mode", mode),
        patch.object(retry.hf, "_preupload_lfs", fail),
        patch.object(retry, "retry_delay", return_value=30),
        patch.object(retry.time, "time", side_effect=lambda: clock[0]),
        patch.object(retry.time, "monotonic", side_effect=lambda: clock[0]),
        patch.object(
            retry.time,
            "sleep",
            side_effect=lambda seconds: clock.__setitem__(0, clock[0] + 10),
        ),
    ):
        root = Path(td)
        filename = "failure\x1b[31m\n.bag" if os.name != "nt" else "failure.bag"
        (root / filename).write_bytes(b"payload")
        output = StringIO()
        with redirect_stdout(output):
            first = retry.run_upload_round(
                None,
                "user/test",
                root,
                repo_type="model",
                num_workers=1,
                print_report=False,
                batch_context=(2, 25),
            )
            # A delayed candidate is returned without a fabricated new failure.
            deferred = retry.run_upload_round(
                None,
                "user/test",
                root,
                repo_type="model",
                num_workers=1,
                print_report=False,
            )
            clock[0] += 60
            second = retry.run_upload_round(
                None,
                "user/test",
                root,
                repo_type="model",
                num_workers=1,
                print_report=False,
            )
        text = output.getvalue()
        assert first["pending"] == deferred["pending"] == second["pending"] == 1
        assert len(attempted) == text.count("[上传失败]") == 4, text
        assert text.count("[加入候补]") == 1 and text.count("[异常待处理]") == 1
        assert "[待处理异常]" not in text and "do-not-log" not in text
        assert "HTTP 502" in text and "WriteTimeout" in text and "SSLEOFError" in text
        assert "方法：PUT" in text and "域名：hub.gitcode.com" in text
        assert "方法：POST" in text and "域名：hub.atomgit.com" in text
        assert "原因：未识别" in text
        displayed_name = "failure?[31m?.bag" if os.name != "nt" else filename
        assert displayed_name in text
        assert "\x1b" not in text and "阶段：LFS 预上传" in text
        assert "本轮失败：3/3｜累计失败：3 次" in text
        assert "[队列状态] 当前候补：1 个｜正在补传：0 个｜异常待处理：0 个" in text
        assert "等待至少 30 秒" in text and "[批次 2/25]" in text

    with (
        tempfile.TemporaryDirectory() as td,
        patch.object(
            config, "get_credentials", return_value={"token": "offline-token"}
        ),
        patch.object(
            service,
            "_validate_resumable_upload_target",
            side_effect=[httpx.ConnectError("do-not-log"), KeyboardInterrupt],
        ),
        patch.object(service, "retry_delay", return_value=30),
        patch.object(service.time, "monotonic", side_effect=lambda: clock[0]),
        patch.object(
            service.time,
            "sleep",
            side_effect=lambda seconds: clock.__setitem__(0, clock[0] + 10),
        ),
    ):
        root = Path(td)
        (root / "sample.bin").write_bytes(b"payload")
        output = StringIO()
        with redirect_stdout(output):
            try:
                api_mod.api.upload_directory(root, "user/test", resumable=True)
            except KeyboardInterrupt:
                pass
            else:
                raise AssertionError(
                    "explicit cancellation must still stop target validation"
                )
        assert output.getvalue().count("[仓库检查失败]") == 1
        assert "阶段：初始化" in output.getvalue()
        assert "[待处理异常]" not in output.getvalue()
    print(
        "[PASS] one diagnostic per real failure, no timed repeats, safe filenames and causes"
    )


if __name__ == "__main__":
    retry_round_checks()
    retry_parent_checks()
    queue_observability_checks()
    event_failure_checks()
    raise SystemExit(main())
