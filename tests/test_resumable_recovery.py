#!/usr/bin/env python3
"""Regression tests for request timeouts and cancellable resumable uploads."""

import hashlib
import importlib
import io
import json
import logging
import multiprocessing
import os
import queue
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx

results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def offline_child(result_queue, outcome, ready, observation_queue=None):
    if outcome == "cancel":
        ready.set()
        time.sleep(30)
    elif outcome == "crash":
        os._exit(3)
    elif outcome == "stage-crash":
        observation_queue.put(
            json.dumps(
                {"version": 1, "type": "upload_stage", "stage": "commit"}
            ).encode()
        )
        observation_queue.close()
        observation_queue.join_thread()
        os._exit(3)
    elif outcome == "empty":
        return
    elif outcome == "failure":
        result_queue.put((False, {"category": "timeout"}))
    elif outcome == "success-crash":
        result_queue.put((True, {"recovered": 0}))
        result_queue.close()
        result_queue.join_thread()
        os._exit(3)
    elif outcome == "invalid":
        result_queue.put(("yes", None))
    else:
        if outcome == "invalid-observation" and observation_queue is not None:
            observation_queue.put(b"not-json")
        elif outcome in ("observe", "flood") and observation_queue is not None:
            count = 1_000 if outcome == "flood" else 1
            for sequence in range(1, count + 1):
                encoded = json.dumps(
                    {
                        "version": 1,
                        "type": "flow_state",
                        "sequence": sequence,
                        "flow_key": 1,
                        "payload": {
                            "file_abbrev": "source.bin",
                            "type": "basic",
                            "size": 100,
                            "remaining_bytes": 80,
                            "sample_speed": 20.0,
                            "window_speed": None,
                            "stable_baseline": None,
                            "peer_baseline": None,
                            "slow_windows": 0,
                            "replacement_count": 0,
                            "phase": "establishing_baseline",
                            "last_decision": "none",
                            "trend": [],
                        },
                    },
                    separators=(",", ":"),
                ).encode("utf-8")
                try:
                    observation_queue.put_nowait(encoded)
                except queue.Full:
                    break
        result_queue.put((True, {"recovered": 0}))


def hold_projection_lock(folder_path, ready, release):
    resumable = importlib.import_module("atomgit.adapters.upload.resumable")
    with resumable._resumable_projection_lock(Path(folder_path)):
        ready.set()
        release.wait(5)


def preuploaded_commit_probe(result_queue, folder_path, reject):
    """Run real locked HF worker threads without network or retransfers."""
    import socket
    import atomgit  # noqa: F401
    from atomgit.adapters.upload import resumable

    class OfflineApi:
        def __init__(self, endpoint=None, token=None):
            pass

        def upload_large_folder(self, **kwargs):
            return resumable.hf_large_folder.upload_large_folder_internal(
                self, **kwargs, print_report=False
            )

        def preupload_lfs_files(self, **kwargs):
            raise AssertionError("Already uploaded data must not be transferred again")

        def create_commit(self, **kwargs):
            assert len(kwargs["operations"]) == 1
            if reject:
                request = httpx.Request(
                    "POST", "https://signed.invalid/?token=fake-secret"
                )
                raise httpx.HTTPStatusError(
                    "Authorization: fake-secret",
                    request=request,
                    response=httpx.Response(422, request=request),
                )
            return SimpleNamespace(oid="2" * 40)

    with (
        patch.object(resumable, "HfApi", OfflineApi),
        patch.object(
            resumable, "_resolve_resumable_revision", lambda **kwargs: "1" * 40
        ),
        patch.object(
            socket.socket,
            "connect",
            side_effect=AssertionError("Offline test attempted network access"),
        ),
    ):
        resumable._run_resumable_upload(
            "fake-token",
            {
                "repo_id": "user/repo",
                "repo_type": "model",
                "folder_path": folder_path,
                "num_workers": 1,
                "allow_patterns": ["*.bin"],
            },
            result_queue,
            300,
            (1, 1),
        )


def acquire_projection_lock(folder_path, acquired):
    resumable = importlib.import_module("atomgit.adapters.upload.resumable")
    with resumable._resumable_projection_lock(Path(folder_path)):
        acquired.set()


def observation_failure_checks():
    resumable = importlib.import_module("atomgit.adapters.upload.resumable")
    result_queue = queue.Queue()

    class FinishedProcess:
        daemon = False
        exitcode = 0

        def __init__(self, args):
            self._result_queue = args[2]

        def start(self):
            self._result_queue.put((True, {"recovered": 0}))

        def is_alive(self):
            return False

        def join(self, timeout=None):
            pass

    queue_calls = 0

    def queue_factory(maxsize=0):
        nonlocal queue_calls
        queue_calls += 1
        if queue_calls == 1:
            return result_queue
        raise OSError("observation queue unavailable")

    adapter = SimpleNamespace(
        get_all_start_methods=lambda: ["spawn"],
        get_context=lambda selected: SimpleNamespace(
            Queue=queue_factory,
            Process=lambda target, args: FinishedProcess(args),
        ),
    )
    with patch.object(resumable, "multiprocessing", adapter):
        result = resumable._execute_resumable_upload_process(
            token="fake-token-never-print",
            upload_kwargs={},
            request_timeout=0.01,
            batch_context=(1, 1),
        )
    check(
        "observation queue creation failure cannot change upload success",
        result == {"recovered": 0},
    )

    cleanup_calls = []

    class BrokenCleanupQueue:
        def close(self):
            cleanup_calls.append("close")
            raise OSError("close failed")

        def join_thread(self):
            cleanup_calls.append("join_thread")
            raise OSError("join failed")

    resumable._close_upload_observation_queue(BrokenCleanupQueue())
    check(
        "observation queue cleanup failures are isolated",
        cleanup_calls == ["close", "join_thread"],
    )


def process_lifecycle_checks():
    resumable = importlib.import_module("atomgit.adapters.upload.resumable")
    for method in multiprocessing.get_all_start_methods():
        context = multiprocessing.get_context(method)
        serialized_warning_flags = []
        for outcome in (
            "success",
            "observe",
            "flood",
            "invalid-observation",
            "failure",
            "empty",
            "crash",
            "stage-crash",
            "success-crash",
            "invalid",
            "cancel",
        ):
            ready = context.Event()
            children = []

            def process_factory(target, args):
                serialized_warning_flags.append(args[-1])
                child = context.Process(
                    target=offline_child,
                    args=(
                        args[2],
                        outcome,
                        ready,
                        args[7] if len(args) > 7 else None,
                    ),
                )
                children.append(child)
                if outcome == "cancel":
                    real_join = child.join
                    interrupted = False

                    def interrupt_join(timeout=None):
                        nonlocal interrupted
                        if not interrupted:
                            interrupted = True
                            assert ready.wait(5), "upload child did not start"
                            raise KeyboardInterrupt
                        return real_join(timeout)

                    class InterruptibleProcess:
                        def __getattr__(self, name):
                            return getattr(child, name)

                        def join(self, timeout=None):
                            return interrupt_join(timeout)

                    child.daemon = True
                    return InterruptibleProcess()
                return child

            adapter = SimpleNamespace(
                get_all_start_methods=lambda: [method],
                get_context=lambda selected: SimpleNamespace(
                    Process=process_factory, Queue=context.Queue
                ),
            )
            error = None
            observations = []
            lfs_service = importlib.import_module("atomgit.adapters.lfs.service")
            previous_observer = lfs_service._upload_observer
            try:
                lfs_service.set_upload_observer(observations.append)
                try:
                    with (
                        patch.object(resumable, "multiprocessing", adapter),
                        patch.object(
                            resumable._UploadProgress, "clear_terminal"
                        ) as cleanup,
                    ):
                        resumable._execute_resumable_upload_process(
                            token="fake-token-never-print",
                            upload_kwargs={},
                            request_timeout=0.01,
                            batch_context=(1, 1),
                            suppress_dataset_warning=True,
                        )
                finally:
                    lfs_service.set_upload_observer(previous_observer)
            except BaseException as exc:
                error = exc
            try:
                check(
                    f"parent reclaims child progress area {method}/{outcome}",
                    cleanup.call_count == 1,
                )
                expected = (
                    error is None
                    if outcome
                    in (
                        "success",
                        "observe",
                        "flood",
                        "invalid-observation",
                    )
                    else (
                        isinstance(error, KeyboardInterrupt)
                        if outcome == "cancel"
                        else (
                            isinstance(error, resumable.ResumableWorkerError)
                            and error.category == "timeout"
                            if outcome == "failure"
                            else isinstance(error, RuntimeError)
                        )
                    )
                )
                check(f"{method} {outcome} result classified", expected)
                if outcome in (
                    "empty",
                    "crash",
                    "stage-crash",
                    "success-crash",
                    "invalid",
                ):
                    diagnostic = getattr(error, "diagnostic", {})
                    check(
                        f"{method} {outcome} has safe process diagnostics",
                        isinstance(error, resumable.ResumableWorkerError)
                        and error.category == "worker_process"
                        and diagnostic.get("exit_code") == children[0].exitcode
                        and diagnostic.get("reason")
                        in {"no_result", "invalid_result", "abnormal_exit"},
                    )
                    if outcome == "stage-crash":
                        check(
                            f"{method} retains last stage after hard exit",
                            diagnostic.get("stage") == "commit",
                        )
                if outcome == "observe":
                    check(
                        f"{method} observation crosses the explicit queue",
                        len(observations) == 2
                        and observations[0]["envelope"]["type"] == "flow_state"
                        and observations[1]["terminal"] == "completed",
                    )
                if outcome == "flood":
                    check(
                        f"{method} observation flood cannot block result delivery",
                        len(observations) >= 2
                        and observations[0]["envelope"]["sequence"] == 1
                        and observations[-1]["terminal"] == "completed",
                    )
                if outcome == "invalid-observation":
                    check(
                        f"{method} invalid observation is dropped",
                        len(observations) == 1
                        and observations[0].get("terminal") == "completed",
                    )
                check(
                    f"{method} {outcome} child reaped",
                    len(children) == 1
                    and not children[0].is_alive()
                    and children[0].exitcode is not None,
                )
            finally:
                for child in children:
                    if child.is_alive():
                        child.kill()
                        child.join()
                    child.close()
        check(
            f"{method} serializes the dataset warning policy explicitly",
            len(serialized_warning_flags) == 11
            and all(flag is True for flag in serialized_warning_flags),
        )

    methods = multiprocessing.get_all_start_methods()
    if "fork" not in methods:
        check("projection lock cross-process check requires fork", True)
        return
    context = multiprocessing.get_context("fork")
    with tempfile.TemporaryDirectory(prefix="atomgit-projection-lock-") as td:
        ready = context.Event()
        release = context.Event()
        acquired = context.Event()
        holder = context.Process(target=hold_projection_lock, args=(td, ready, release))
        contender = context.Process(target=acquire_projection_lock, args=(td, acquired))
        try:
            holder.start()
            holder_started = ready.wait(5)
            contender.start()
            contender_blocked = not acquired.wait(0.2)
            release.set()
            contender_acquired = acquired.wait(5)
            holder.join(5)
            contender.join(5)
            check(
                "projection lock serializes independent upload processes",
                holder_started
                and contender_blocked
                and contender_acquired
                and holder.exitcode == 0
                and contender.exitcode == 0,
            )
        finally:
            release.set()
            for child in (holder, contender):
                if child.is_alive():
                    child.kill()
                    child.join()
                child.close()


def progress_policy_checks():
    resumable = importlib.import_module("atomgit.adapters.upload.resumable")
    standard, hf = resumable.std_tqdm, resumable.hf_tqdm
    before = (standard.monitor_interval, hf.monitor_interval)
    # Start an actual monitor to cover already-created bars as well.
    existing = standard(total=1, disable=True)
    monitor = standard.monitor
    with patch("tqdm.std.TMonitor") as factory:
        with resumable._scoped_resumable_progress():

            def create_bar(number):
                with hf(total=1, disable=True) as bar:
                    bar.update(1)
                with standard(total=1, disable=True) as bar:
                    bar.update(1)

            with ThreadPoolExecutor(max_workers=5) as executor:
                list(executor.map(create_bar, range(100)))
            check(
                "upload progress does not create background monitors",
                not factory.called,
            )
            check(
                "both progress classes disable monitors",
                standard.monitor_interval == hf.monitor_interval == 0,
            )
            check(
                "existing tqdm monitor is stopped",
                monitor is None or not monitor.is_alive(),
            )
    existing.close()
    check(
        "tqdm monitor intervals are restored",
        (standard.monitor_interval, hf.monitor_interval) == before,
    )


def append_output_probe(result_queue, folder_path, terminal, fail):
    """Exercise real HF renderers in isolated fork/spawn workers, offline."""
    import socket

    import atomgit  # noqa: F401
    from atomgit.adapters.upload import resumable

    hf_progress = importlib.import_module("huggingface_hub.utils.tqdm")

    class Output(io.StringIO):
        def isatty(self):
            return terminal

    class OfflineApi:
        def __init__(self, **kwargs):
            pass

        def upload_large_folder(self, *, print_report=True, **kwargs):
            from huggingface_hub import CommitOperationAdd, lfs

            def transfer(number):
                source = Path(folder_path) / f"file-{number}.bin"
                source.write_bytes(bytes([number]) * 40)
                operation = CommitOperationAdd(
                    path_in_repo=f"nested/{source.name}", path_or_fileobj=source
                )
                lfs._upload_single_part(operation, "https://offline.invalid/upload")

            failed_transfers = threading.Barrier(2)

            def send(method, url, *, data, **kwargs):
                clock = iter(range(0, 1000, 5))
                data._monotonic = lambda: next(clock)
                data._last_read_end = 0
                while data.read(10):
                    print("transfer event", flush=True)
                    print("stderr event", file=sys.stderr, flush=True)
                    logger.warning("token=fake-secret")
                if fail:
                    # Both file reports must exist before one failure cancels peers.
                    failed_transfers.wait(timeout=5)
                    raise RuntimeError("offline failure")
                return SimpleNamespace()

            controller = lfs._upload_single_part.__self__
            controller._http_backoff = send
            controller._raise_for_status = lambda response: None
            with ThreadPoolExecutor(max_workers=2) as pool:
                list(pool.map(transfer, range(2)))
            for number in range(2):
                with hf_progress.tqdm(total=1, desc="file.bin") as bar:
                    bar.update(1)
                if print_report:
                    resumable.hf_large_folder._print_overwrite(
                        f"report {number}\nFiles: committed {number}/2\nWorkers: 1"
                    )
                with ThreadPoolExecutor(max_workers=2) as pool:
                    list(
                        pool.map(
                            lambda n: print(f"retry {number}-{n}", flush=True), range(2)
                        )
                    )
            if fail:
                raise RuntimeError("offline failure")

    output = Output()
    logger = logging.getLogger("huggingface_hub.progress_probe")
    handler = logging.StreamHandler(output)
    logger.handlers = [handler]
    logger.propagate = False
    outcomes = queue.Queue()
    original_report = resumable.hf_large_folder._print_overwrite
    before = dict(hf_progress.progress_bar_states)
    # An explicit HF enable must not reintroduce dynamic bars in log mode.
    with (
        patch.object(hf_progress, "HF_HUB_DISABLE_PROGRESS_BARS", False),
        patch.object(resumable, "HfApi", OfflineApi),
        patch.object(socket.socket, "connect", side_effect=AssertionError("network")),
        redirect_stdout(output),
        redirect_stderr(output),
    ):
        resumable._run_resumable_upload(
            "fake-token",
            {"repo_id": "user/repo", "repo_type": "model", "folder_path": folder_path},
            outcomes,
        )
        print("batch finished", flush=True)
    result_queue.put(
        (
            output.getvalue(),
            outcomes.get_nowait()[0],
            resumable.hf_large_folder._print_overwrite is original_report,
            hf_progress.progress_bar_states == before,
            handler.stream is output,
        )
    )


def append_output_checks():
    for method in multiprocessing.get_all_start_methods():
        if method not in {"fork", "spawn"}:
            continue
        for terminal in (True, False):
            for fail in (False, True):
                with tempfile.TemporaryDirectory() as folder:
                    context = multiprocessing.get_context(method)
                    output_queue = context.Queue()
                    child = context.Process(
                        target=append_output_probe,
                        args=(output_queue, folder, terminal, fail),
                    )
                    try:
                        child.start()
                        (
                            output,
                            ok,
                            restored_report,
                            restored_progress,
                            restored_handler,
                        ) = output_queue.get(timeout=15)
                        child.join(5)
                        label = f"{method} terminal={terminal} failure={fail}"
                        check(
                            f"append-only output {label}",
                            child.exitcode == 0
                            and ok is not fail
                            and (
                                terminal
                                or ("\r" not in output and "\x1b" not in output)
                            )
                            and "file.bin" not in output
                            and "file-0.bin" in output
                            and "file-1.bin" in output
                            and "stderr event" in output
                            and "上传依赖日志已脱敏" in output
                            and "fake-secret" not in output
                            and (
                                fail
                                or all(
                                    f"report {n}\nFiles: committed {n}/2\nWorkers: 1\n"
                                    in output
                                    for n in range(2)
                                )
                            )
                            and (
                                fail
                                or all(
                                    f"retry {n}-{w}\n" in output
                                    for n in range(2)
                                    for w in range(2)
                                )
                            )
                            and ("传输完成，等待提交确认" in output) is not fail
                            and output.endswith("batch finished\n"),
                        )
                        check(
                            f"output state restored {label}",
                            restored_report and restored_progress and restored_handler,
                        )
                    finally:
                        if child.is_alive():
                            child.kill()
                            child.join()
                        child.close()
                        output_queue.close()
                        output_queue.join_thread()


def file_progress_policy_checks():
    from atomgit.adapters.lfs.service import _SlowFlowCoordinator
    from atomgit.adapters.upload.progress import _UploadProgress

    output = io.StringIO()
    now = [0]
    observations = []
    progress = _UploadProgress(monotonic=lambda: now[0])
    coordinator = _SlowFlowCoordinator(
        progress_callback=progress.observe,
        observation_callback=observations.append,
    )
    original_streams = sys.stdout, sys.stderr
    with redirect_stdout(output), redirect_stderr(output), progress:
        coordinator.register("object", total_bytes=100, file_abbrev="nested/file.bin")
        now[0] = 5
        coordinator.observe_sample("object", 5, 75)
        now[0] = 10
        coordinator.observe_sample("object", 5, 50)
        before_complete = output.getvalue()
        now[0] = 20
        coordinator.observe_sample("object", 0, 50)
        coordinator.complete("object")
        coordinator.register("object", total_bytes=100, file_abbrev="nested/file.bin")
        coordinator.complete("object", reset_windows=True)
    text = output.getvalue()
    check(
        "file snapshots are bounded to ten seconds",
        before_complete.count("上传中") == 2,
    )
    check(
        "file snapshots expose bytes speed and ETA",
        "50%" in text
        and "50.0B/100B" in text
        and "5.00B/s" in text
        and "00:10" in text,
    )
    check(
        "file retries restart their displayed progress", text.count("上传中：0%") == 2
    )
    check("zero speed is not shown as unknown", "0.00B/s" in text)
    check(
        "file completion differs from failure and commit",
        text.count("传输完成，等待提交确认") == 1 and "传输中断" in text,
    )
    check(
        "redirected progress has no cursor controls",
        "\r" not in text and "\x1b" not in text,
    )
    check(
        "display names do not enter observation envelopes",
        all(set(item) == {"type", "flow_key", "payload"} for item in observations),
    )
    check("output streams restored", (sys.stdout, sys.stderr) == original_streams)
    disabled_output = io.StringIO()
    with (
        redirect_stdout(disabled_output),
        redirect_stderr(disabled_output),
        _UploadProgress(False) as disabled,
    ):
        disabled.observe({"type": "file_name", "flow_key": 1, "name": "hidden.bin"})
        print("batch event", flush=True)
    check(
        "disabled progress preserves lifecycle text only",
        disabled_output.getvalue() == "batch event\n",
    )

    # A broken display must not change transfer policy or monitor observations.
    coordinator = _SlowFlowCoordinator(progress_callback=lambda message: 1 / 0)
    coordinator.register("object", total_bytes=10)
    coordinator.complete("object")
    check(
        "display failure cannot change transfer state",
        coordinator._states["object"].phase == "completed",
    )


def progress_pty_checks():
    if os.name != "posix":
        return
    import fcntl
    import pty
    import re
    import struct
    import termios
    import unicodedata

    from atomgit.adapters.lfs.service import _SlowFlowCoordinator
    from atomgit.adapters.upload.progress import _UploadProgress

    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 120, 0, 0))
    terminal = os.fdopen(slave, "w", buffering=1)
    captured = []

    def drain():
        while True:
            try:
                data = os.read(master, 4096)
            except OSError:
                break
            if not data:
                break
            captured.append(data)

    reader = threading.Thread(target=drain)
    reader.start()
    try:
        with (
            redirect_stdout(terminal),
            redirect_stderr(terminal),
            _UploadProgress() as progress,
        ):
            coordinator = _SlowFlowCoordinator(progress_callback=progress.observe)
            coordinator.register("a", total_bytes=100, file_abbrev="a.bin")
            coordinator.register("b", total_bytes=100, file_abbrev="b.bin")
            print("LOG-A", flush=True)
            coordinator.observe_sample("a", 5, 50)
            print("LOG-B", file=sys.stderr, flush=True)
            coordinator.complete("a")
            coordinator.complete("b")
            print("BATCH-OK", flush=True)
    finally:
        terminal.close()
        reader.join(5)
        os.close(master)
    text = b"".join(captured).decode()
    check(
        "real PTY renders multiple file bars and logs",
        not reader.is_alive()
        and "a.bin" in text
        and "b.bin" in text
        and "50%" in text
        and text.count("LOG-A") == text.count("LOG-B") == 1
        and text.endswith("BATCH-OK\r\n"),
    )
    # Interpret the cursor operations actually emitted by tqdm, so merely
    # finding a log in the byte stream cannot conceal its later erasure.
    rows = [[]]
    row = column = 0
    for match in re.finditer(r"\x1b\[([0-9;]*)([A-Za-z])|([^\x1b])", text, re.S):
        amount, command, char = match.groups()
        if command == "A":
            row = max(0, row - int(amount or 1))
        elif command == "K":
            rows[row] = rows[row][:column] if amount != "2" else []
        elif char == "\r":
            column = 0
        elif char == "\n":
            row += 1
            if row == len(rows):
                rows.append([])
        elif char and char.isprintable():
            width = 2 if unicodedata.east_asian_width(char) in "WF" else 1
            rows[row].extend([" "] * max(0, column + width - len(rows[row])))
            rows[row][column : column + width] = [char] + [""] * (width - 1)
            column += width
    screen = "\n".join("".join(line).rstrip() for line in rows)
    check(
        "PTY keeps log history after bars close",
        all(line in screen.splitlines() for line in ("LOG-A", "LOG-B", "BATCH-OK"))
        and "50%" not in screen,
    )


def phase_isolation_checks():
    resumable = importlib.import_module("atomgit.adapters.upload.resumable")
    sender = resumable._UploadObservationSender(None)
    commit_ready, preupload_ready = threading.Event(), threading.Event()

    def commit():
        sender.stage("commit")
        commit_ready.set()
        assert preupload_ready.wait(2)
        return getattr(sender, "failure_stage", sender.last_stage)

    def preupload():
        assert commit_ready.wait(2)
        sender.stage("preupload")
        preupload_ready.set()
        return getattr(sender, "failure_stage", sender.last_stage)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.submit(commit), pool.submit(preupload)
        check(
            "reported failures use the failing worker phase",
            (first.result(), second.result()) == ("commit", "preupload"),
        )


def preuploaded_commit_checks():
    from huggingface_hub._local_folder import (
        get_local_upload_paths,
        read_upload_metadata,
    )

    context = multiprocessing.get_context("spawn")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "data.bin").write_bytes(b"offline-already-uploaded")
        paths = get_local_upload_paths(root, "data.bin")
        metadata = read_upload_metadata(root, "data.bin")
        metadata.sha256 = hashlib.sha256(paths.file_path.read_bytes()).hexdigest()
        metadata.upload_mode = "lfs"
        metadata.should_ignore = False
        metadata.is_uploaded = True
        metadata.save(paths)
        for reject in (True, False):
            result_queue = context.Queue()
            child = context.Process(
                target=preuploaded_commit_probe, args=(result_queue, str(root), reject)
            )
            try:
                child.start()
                child.join(12)
                if child.is_alive():
                    child.kill()
                    child.join()
                    check("real HF preuploaded worker finishes without hanging", False)
                    break
                result = result_queue.get(timeout=1)
                if reject:
                    check(
                        "real HF commit failure retains safe stage, type and HTTP status",
                        child.exitcode == 1
                        and result
                        == (
                            False,
                            {
                                "category": "unknown",
                                "diagnostic": {
                                    "stage": "commit",
                                    "reason": "reported",
                                    "error_type": "HTTPStatusError",
                                    "status_code": 422,
                                },
                            },
                        ),
                    )
                    retained = read_upload_metadata(root, "data.bin")
                    check(
                        "commit failure preserves preupload and hash",
                        retained.is_uploaded
                        and not retained.is_committed
                        and retained.sha256 == metadata.sha256,
                    )
                else:
                    check(
                        "real HF rerun reuses uploaded data and confirms commit",
                        child.exitcode == 0
                        and result == (True, {"recovered": 0})
                        and read_upload_metadata(root, "data.bin").is_committed,
                    )
            finally:
                child.close()
                result_queue.close()
                result_queue.join_thread()


def main():
    original_home = os.environ.get("HOME")
    try:
        with tempfile.TemporaryDirectory() as td:
            os.environ["HOME"] = td
            import sys

            import atomgit  # noqa: F401

            api_module = sys.modules["atomgit.api"]
            config = sys.modules["atomgit.config"].config

            source = Path(td) / "source"
            source.mkdir()
            (source / "payload.bin").write_bytes(b"resumable-test")
            config.get_credentials = lambda: {"token": "fake-token-never-print"}

            original_hf_api = api_module.HfApi
            original_progress = api_module._set_progress_bar
            original_v5_get = api_module._atomgit_v5_get_json
            calls = []

            api_module._atomgit_v5_get_json = lambda *args, **kwargs: {
                "full_name": "user/repo",
                "default_branch": "main",
            }

            class SlowHfApi:
                def __init__(self, endpoint=None, token=None):
                    calls.append(("init", endpoint, token))

                def upload_large_folder(self, **kwargs):
                    calls.append(("upload", kwargs))
                    time.sleep(0.25)

            class FastHfApi:
                def __init__(self, endpoint=None, token=None):
                    calls.append(("init-fast", endpoint, token))

                def upload_large_folder(self, **kwargs):
                    calls.append(("upload-fast", kwargs))

            api_module.HfApi = SlowHfApi
            api_module._set_progress_bar = lambda enabled: None
            try:
                started = time.monotonic()
                result = api_module.api.upload_directory(
                    source,
                    "user/repo",
                    upload_timeout=0.05,
                    progress_bar=False,
                    resumable=True,
                    num_workers=1,
                )
                elapsed = time.monotonic() - started
                check("T1 request timeout does not cap upload lifetime", result is True)
                check(
                    "T2 healthy worker finishes beyond request timeout",
                    elapsed >= 0.25,
                    f"elapsed={elapsed:.3f}s",
                )
                check(
                    "T3 no upload child is left alive",
                    not api_module.multiprocessing.active_children(),
                )
            finally:
                api_module.HfApi = original_hf_api
                api_module._atomgit_v5_get_json = original_v5_get
                api_module._set_progress_bar = original_progress

            from huggingface_hub import constants as hf_constants
            from huggingface_hub.utils import _http

            before = hf_constants.DEFAULT_REQUEST_TIMEOUT
            for timeout_error in (httpx.ReadTimeout, httpx.WriteTimeout):

                class FailedHfApi:
                    def __init__(self, endpoint=None, token=None):
                        pass

                    def upload_large_folder(self, **kwargs):
                        with _http.default_client_factory() as client:
                            assert client.timeout.read == 0.05
                            assert client.timeout.connect == 0.05
                            assert client.timeout.pool == 0.05
                            assert client.timeout.write == 60.0
                        raise timeout_error("offline request timeout")

                output = io.StringIO()
                with (
                    redirect_stdout(output),
                    patch.object(api_module, "HfApi", FailedHfApi),
                    patch.object(
                        api_module, "_atomgit_v5_get_json", lambda *a, **kw: {}
                    ),
                ):
                    failed = api_module.api.upload_directory(
                        source,
                        "user/repo",
                        upload_timeout=0.05,
                        resumable=True,
                        progress_bar=False,
                    )
                check(
                    f"{timeout_error.__name__} fails through upload service",
                    failed is False and "上传目录失败[请求超时]" in output.getvalue(),
                )
                check(
                    "request timeout restored after failure",
                    hf_constants.DEFAULT_REQUEST_TIMEOUT == before,
                )

            observation_failure_checks()
            process_lifecycle_checks()
            progress_policy_checks()
            append_output_checks()
            file_progress_policy_checks()
            progress_pty_checks()
            phase_isolation_checks()
            preuploaded_commit_checks()

            calls.clear()
            api_module.HfApi = FastHfApi
            api_module._atomgit_v5_get_json = lambda *args, **kwargs: {
                "full_name": "user/repo",
                "default_branch": "main",
            }
            try:
                result = api_module.api.upload_directory(
                    source,
                    "user/repo",
                    upload_timeout=1,
                    progress_bar=False,
                    resumable=True,
                    num_workers=1,
                )
                check("T4 successful child returns success", result is True)
                check("T5 successful worker completes within timeout", result is True)
            finally:
                api_module.HfApi = original_hf_api
                api_module._atomgit_v5_get_json = original_v5_get

    finally:
        if original_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = original_home

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
