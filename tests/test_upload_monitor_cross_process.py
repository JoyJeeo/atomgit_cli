#!/usr/bin/env python3
"""Offline spawn-process contract for upload monitoring."""

import functools
import json
import multiprocessing
import os
import queue
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

_FAKE_TOKEN = "fake-cross-process-token-never-print"
_PRIVATE_OBJECT_ID = "private-object-id-never-persist"
_PROCESS_TIMEOUT = 15


def _offline_resumable_worker(
    monitor_read_active,
    _token,
    _upload_kwargs,
    result_queue,
    _request_timeout,
    _batch_context,
    _auto_configure_lfs,
    _configured_lfs_patterns,
    observation_queue,
    _suppress_dataset_warning,
):
    from atomgit.adapters.lfs.service import _SlowFlowCoordinator
    from atomgit.adapters.upload.resumable import _UploadObservationSender

    sender = _UploadObservationSender(observation_queue)
    coordinator = _SlowFlowCoordinator(observation_callback=sender.send)
    object_key = _PRIVATE_OBJECT_ID
    coordinator.register(
        object_key,
        total_bytes=100,
        file_abbrev="source.bin",
        transfer_type="basic",
    )
    if not monitor_read_active.wait(_PROCESS_TIMEOUT):
        result_queue.put((False, {"category": "monitor-timeout"}))
        return
    coordinator.complete(object_key)
    result_queue.put((True, {"recovered": 0}))


def _upload_cli_target(
    hf_home, source, monitor_read_active, terminal_ready, result_queue
):
    import atomgit
    from atomgit.adapters.upload import resumable

    os.environ["HF_HOME"] = hf_home

    api_module = sys.modules["atomgit.api"]
    config_module = sys.modules["atomgit.config"]
    original_upload = api_module.api.upload_directory
    original_logged_in = config_module.config.is_logged_in
    original_credentials = config_module.config.get_credentials

    def fake_upload_directory(actual_source, repo_id, **kwargs):
        assert Path(actual_source) == Path(source)
        assert repo_id == "owner/demo"
        progress_callback = kwargs["progress_callback"]
        progress_callback({"batch": "1/2", "files_total": 21, "files_done": 20})
        original_multiprocessing = resumable.multiprocessing
        original_worker = resumable._run_resumable_upload
        try:
            resumable.multiprocessing = SimpleNamespace(
                get_all_start_methods=lambda: ["spawn"],
                get_context=lambda method: multiprocessing.get_context(method),
            )
            resumable._run_resumable_upload = functools.partial(
                _offline_resumable_worker, monitor_read_active
            )
            worker_result = resumable._execute_resumable_upload_process(
                token=_FAKE_TOKEN,
                upload_kwargs={"folder_path": str(actual_source), "repo_id": repo_id},
                request_timeout=0.1,
                batch_context=(1, 2),
            )
        finally:
            resumable.multiprocessing = original_multiprocessing
            resumable._run_resumable_upload = original_worker
        progress_callback({"batch": "2/2", "files_total": 21, "files_done": 21})
        return worker_result == {"recovered": 0}

    try:
        api_module.api.upload_directory = fake_upload_directory
        config_module.config.is_logged_in = lambda: True
        config_module.config.get_credentials = lambda: {"token": _FAKE_TOKEN}
        result = CliRunner().invoke(
            atomgit.cli,
            [
                "upload",
                source,
                "--repo-id",
                "owner/demo",
                "--resumable",
                "--no-progress-bar",
            ],
        )
        result_queue.put(
            {
                "exit_code": result.exit_code,
                "output": result.output,
                "exception": repr(result.exception) if result.exception else None,
            }
        )
    except BaseException as error:
        result_queue.put({"exit_code": -1, "output": "", "exception": repr(error)})
    finally:
        api_module.api.upload_directory = original_upload
        config_module.config.is_logged_in = original_logged_in
        config_module.config.get_credentials = original_credentials
        terminal_ready.set()


def _monitor_cli_target(
    hf_home,
    session_id,
    monitor_read_active,
    terminal_ready,
    result_queue,
    fail_after_active=False,
):
    import atomgit
    from atomgit.interfaces.cli.commands import monitor as monitor_command

    os.environ["HF_HOME"] = hf_home
    original_sleep = monitor_command.time.sleep

    def synchronized_sleep(seconds):
        if seconds == 1:
            monitor_read_active.set()
            if fail_after_active:
                raise RuntimeError("controlled monitor failure")
            if not terminal_ready.wait(_PROCESS_TIMEOUT):
                raise RuntimeError("upload terminal snapshot was not published")

    try:
        monitor_command.time.sleep = synchronized_sleep
        result = CliRunner().invoke(
            atomgit.cli, ["monitor", "upload", "status", session_id]
        )
        result_queue.put(
            {
                "exit_code": result.exit_code,
                "output": result.output,
                "exception": repr(result.exception) if result.exception else None,
            }
        )
    except BaseException as error:
        result_queue.put({"exit_code": -1, "output": "", "exception": repr(error)})
    finally:
        monitor_command.time.sleep = original_sleep


def _hang_forever():
    while True:
        time.sleep(1)


def _exit_without_result():
    pass


def _return_invalid_result(result_queue):
    result_queue.put("invalid")


def _crash():
    os._exit(3)


def _stop_process(process):
    if process.is_alive():
        process.terminate()
        process.join(2)
    if process.is_alive():
        process.kill()
        process.join()


def _collect_process(process, result_queue, label, timeout=_PROCESS_TIMEOUT):
    process.join(timeout)
    if process.is_alive():
        _stop_process(process)
        raise AssertionError(f"{label} timed out and was terminated")
    if process.exitcode != 0:
        raise AssertionError(f"{label} exited with status {process.exitcode}")
    try:
        result = result_queue.get(timeout=1)
    except queue.Empty as error:
        raise AssertionError(f"{label} exited without a result") from error
    if not isinstance(result, dict) or set(result) != {
        "exit_code",
        "output",
        "exception",
    }:
        raise AssertionError(f"{label} returned an invalid result")
    return result


def _wait_for_active_snapshot(hf_home, upload, upload_results):
    deadline = time.monotonic() + _PROCESS_TIMEOUT
    directory = Path(hf_home) / "upload-observe" / "v1"
    last_session = None
    while time.monotonic() < deadline:
        if not upload.is_alive():
            try:
                result = upload_results.get(timeout=1)
            except queue.Empty:
                result = "missing result"
            raise AssertionError(
                f"upload CLI exited before the active snapshot: {result!r}"
            )
        for path in directory.glob("*.json"):
            try:
                session = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            last_session = session
            flows = session.get("flows", [])
            if (
                session.get("status") == "active"
                and session.get("batch") == "1/2"
                and session.get("files_done") == 20
                and session.get("files_total") == 21
                and any(flow.get("flow_id") == "Flow-01" for flow in flows)
            ):
                return path, session
        time.sleep(0.05)
    raise AssertionError(f"active upload snapshot was not published: {last_session!r}")


def _close_queue(result_queue):
    result_queue.close()
    result_queue.join_thread()


def main():
    checks = []

    def check(name, condition, detail=""):
        checks.append(bool(condition))
        flag = "PASS" if condition else "FAIL"
        suffix = f" -> {detail}" if detail and not condition else ""
        print(f"[{flag}] {name}{suffix}")

    context = multiprocessing.get_context("spawn")
    missing_result = context.Queue()
    hanging = context.Process(target=_hang_forever)
    hanging.start()
    timeout_error = None
    try:
        _collect_process(hanging, missing_result, "controlled timeout", timeout=0.2)
    except AssertionError as error:
        timeout_error = str(error)
    finally:
        _stop_process(hanging)
        _close_queue(missing_result)
    check(
        "bounded timeout reports failure and reaps the child",
        timeout_error == "controlled timeout timed out and was terminated"
        and not hanging.is_alive(),
        timeout_error or "no timeout failure",
    )

    failure_cases = (
        (_exit_without_result, (), "exited without a result"),
        (_return_invalid_result, None, "returned an invalid result"),
        (_crash, (), "exited with status 3"),
    )
    for target, target_args, expected in failure_cases:
        failure_results = context.Queue()
        args = (failure_results,) if target_args is None else target_args
        process = context.Process(target=target, args=args)
        process.start()
        failure = None
        try:
            _collect_process(process, failure_results, "controlled failure")
        except AssertionError as error:
            failure = str(error)
        finally:
            _stop_process(process)
            _close_queue(failure_results)
        check(
            f"{expected} is explicit and reaps the child",
            failure == f"controlled failure {expected}" and not process.is_alive(),
            failure or "no failure",
        )

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        hf_home = root / "hf-home"
        source = root / "private-source"
        source.mkdir()
        for index in range(21):
            (source / f"file-{index:02d}.bin").write_bytes(b"x")

        monitor_read_active = context.Event()
        failed_monitor_read = context.Event()
        terminal_ready = context.Event()
        upload_results = context.Queue()
        monitor_results = context.Queue()
        failed_monitor_results = context.Queue()
        upload = context.Process(
            target=_upload_cli_target,
            args=(
                str(hf_home),
                str(source),
                monitor_read_active,
                terminal_ready,
                upload_results,
            ),
        )
        monitor = None
        failed_monitor = None
        upload.start()
        try:
            snapshot_path, active = _wait_for_active_snapshot(
                hf_home, upload, upload_results
            )
            session_id = active["session_id"]
            failed_monitor = context.Process(
                target=_monitor_cli_target,
                args=(
                    str(hf_home),
                    session_id,
                    failed_monitor_read,
                    terminal_ready,
                    failed_monitor_results,
                    True,
                ),
            )
            failed_monitor.start()
            failed_monitor_result = _collect_process(
                failed_monitor, failed_monitor_results, "failed monitor CLI"
            )
            upload_survived_monitor_failure = upload.is_alive()
            monitor = context.Process(
                target=_monitor_cli_target,
                args=(
                    str(hf_home),
                    session_id,
                    monitor_read_active,
                    terminal_ready,
                    monitor_results,
                ),
            )
            monitor.start()
            upload_result = _collect_process(upload, upload_results, "upload CLI")
            monitor_result = _collect_process(monitor, monitor_results, "monitor CLI")
            final = json.loads(snapshot_path.read_text(encoding="utf-8"))
            raw_snapshot = snapshot_path.read_text(encoding="utf-8")
        finally:
            _stop_process(upload)
            if monitor is not None:
                _stop_process(monitor)
            if failed_monitor is not None:
                _stop_process(failed_monitor)
            _close_queue(upload_results)
            _close_queue(monitor_results)
            _close_queue(failed_monitor_results)

        active_output = f"会话 {session_id} | active | 仓库 demo | 批次 1/2"
        final_output = f"会话 {session_id} | finished | 仓库 demo | 批次 2/2"
        check(
            "upload CLI publishes parent batch progress and worker Flow",
            active.get("files_done") == 20
            and active.get("files_total") == 21
            and active.get("flows", [{}])[0].get("flow_id") == "Flow-01",
        )
        check(
            "a failed independent monitor cannot alter the upload",
            failed_monitor_result["exit_code"] != 0
            and "controlled monitor failure"
            in (failed_monitor_result["exception"] or "")
            and active_output in failed_monitor_result["output"]
            and upload_survived_monitor_failure,
            failed_monitor_result["exception"] or failed_monitor_result["output"],
        )
        check(
            "independent monitor reads active and terminal frames then exits",
            monitor_result["exit_code"] == 0
            and monitor_result["exception"] is None
            and active_output in monitor_result["output"]
            and final_output in monitor_result["output"]
            and "已确认文件 20/21" in monitor_result["output"]
            and "已确认文件 21/21" in monitor_result["output"],
            monitor_result["exception"] or monitor_result["output"],
        )
        check(
            "upload CLI owns the real finished lifecycle and remains successful",
            upload_result["exit_code"] == 0
            and upload_result["exception"] is None
            and final.get("session_id") == session_id
            and final.get("status") == "finished"
            and final.get("batch") == "2/2"
            and final.get("files_done") == 21
            and final.get("files_total") == 21
            and not upload.is_alive()
            and not monitor.is_alive(),
            upload_result["exception"] or upload_result["output"],
        )
        forbidden = (
            _FAKE_TOKEN,
            str(source),
            _PRIVATE_OBJECT_ID,
            "source_id",
            "object at 0x",
        )
        check(
            "snapshot is bounded to anonymous redacted state",
            snapshot_path.stat().st_mode & 0o777 == 0o600
            and all(value not in raw_snapshot for value in forbidden),
        )

    passed = sum(checks)
    print(f"summary: {passed}/{len(checks)} passed")
    if passed != len(checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
