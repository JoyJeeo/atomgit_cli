#!/usr/bin/env python3
"""Offline contract checks for the read-only upload monitor."""

import json
import os
import queue
import sys
import tempfile
from pathlib import Path

from click.testing import CliRunner

import atomgit
from atomgit.adapters.lfs import service as lfs_service
from atomgit.adapters.upload import resumable as upload_resumable
from atomgit.infrastructure import upload_observe


class FakePublisher:
    def __init__(self):
        self.snapshots = []

    def submit(self, value):
        self.snapshots.append(dict(value))

    def stop(self):
        pass


def flow_envelope(sequence, *, flow_key=1, **updates):
    payload = {
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
    }
    payload.update(updates)
    return {
        "version": 1,
        "type": "flow_state",
        "sequence": sequence,
        "flow_key": flow_key,
        "payload": payload,
    }


def main():
    checks = []

    def check(name, ok):
        checks.append(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")

    runner = CliRunner()
    result = runner.invoke(atomgit.cli, ["monitor", "upload", "status", "--help"])
    check("monitor status help", result.exit_code == 0 and "--list" in result.output)
    rejected = runner.invoke(atomgit.cli, ["monitor", "upload", "status", "--watch"])
    check("--watch rejected", rejected.exit_code == 2)

    api_mod = sys.modules["atomgit.api"]
    cfg_mod = sys.modules["atomgit.config"]
    original_upload_directory = api_mod.api.upload_directory
    original_logged_in = cfg_mod.config.is_logged_in
    original_hf_home = os.environ.get("HF_HOME")
    cli_progress = []

    def fake_upload_directory(source, repo_id, **kwargs):
        progress_callback = kwargs["progress_callback"]
        for progress in (
            {"batch": "0/2", "files_total": 21, "files_done": 0},
            {"batch": "1/2", "files_total": 21, "files_done": 0},
            {"batch": "1/2", "files_total": 21, "files_done": 20},
            {"batch": "2/2", "files_total": 21, "files_done": 20},
            {"batch": "2/2", "files_total": 21, "files_done": 21},
        ):
            cli_progress.append(progress)
            progress_callback(progress)
        return True

    try:
        with tempfile.TemporaryDirectory() as td:
            os.environ["HF_HOME"] = td
            source = Path(td) / "source"
            source.mkdir()
            for index in range(21):
                (source / f"file-{index:02d}.bin").write_bytes(b"x")
            api_mod.api.upload_directory = fake_upload_directory
            cfg_mod.config.is_logged_in = lambda: True
            cli_result = runner.invoke(
                atomgit.cli,
                ["upload", str(source), "--repo-id", "owner/demo", "--resumable"],
            )
            sessions = upload_observe.load_sessions()
            final_session = sessions[0] if sessions else {}
            detailed = upload_observe.render_session(final_session)
            listed = upload_observe.render_list(sessions)
            check(
                "CLI private callback publishes actual batch and file progress",
                cli_result.exit_code == 0
                and len(cli_progress) == 5
                and final_session.get("status") == "finished"
                and final_session.get("batch") == "2/2"
                and final_session.get("files_total") == 21
                and final_session.get("files_done") == 21
                and "已确认文件 21/21" in detailed
                and "2/2" in listed,
            )
    finally:
        api_mod.api.upload_directory = original_upload_directory
        cfg_mod.config.is_logged_in = original_logged_in
        if original_hf_home is None:
            os.environ.pop("HF_HOME", None)
        else:
            os.environ["HF_HOME"] = original_hf_home

    legacy_rendered = upload_observe.render_session(
        {"session_id": "legacy", "status": "finished", "batch": "1/1"}
    )
    check(
        "old v1 snapshots omit unavailable file progress",
        "已确认文件" not in legacy_rendered and "0/0" not in legacy_rendered,
    )
    queued = []

    class ObservationQueue:
        def put_nowait(self, value):
            queued.append(value)

    sender = upload_resumable._UploadObservationSender(ObservationQueue())
    sender.send(
        {"type": "flow_state", "flow_key": 1, "payload": flow_envelope(1)["payload"]}
    )
    decoded = upload_resumable._decode_upload_observation(queued[-1])
    check(
        "child observation sender emits compact v1 UTF-8 bytes",
        decoded is not None
        and decoded["sequence"] == 1
        and decoded["flow_key"] == 1
        and len(queued[-1]) <= 16 * 1024,
    )

    class FullQueue:
        def put_nowait(self, value):
            raise queue.Full

    full_sender = upload_resumable._UploadObservationSender(FullQueue())
    full_sender.send(
        {"type": "flow_state", "flow_key": 1, "payload": flow_envelope(1)["payload"]}
    )
    oversized = []

    class OversizedQueue:
        def put_nowait(self, value):
            oversized.append(value)

    oversized_sender = upload_resumable._UploadObservationSender(OversizedQueue())
    oversized_sender.send(
        {"type": "flow_event", "flow_key": 1, "payload": {"event": "x" * 20_000}}
    )
    check(
        "queue-full and oversized observations are dropped without retry",
        oversized == [],
    )
    check(
        "invalid observation envelopes are rejected",
        upload_resumable._decode_upload_observation(b"not-json") is None
        and upload_resumable._decode_upload_observation(
            json.dumps({"version": 2}).encode()
        )
        is None,
    )

    class BrokenObservationQueue:
        def get_nowait(self):
            raise EOFError

    upload_resumable._drain_upload_observations(
        BrokenObservationQueue(), "private-source"
    )
    check("a broken observation pipe is isolated from upload results", True)
    with tempfile.TemporaryDirectory() as td:
        os.environ["HF_HOME"] = td
        path = upload_observe.publish_snapshot(
            {
                "session_id": "s1",
                "repo_name": "demo",
                "status": "finished",
                "updated_at": "2026-08-26T10:00:00Z",
                "batch": "1/1",
                "events": [{"message": "done"}] * 300,
                "flows": [
                    {
                        "flow_id": "01",
                        "basename": "abcdefghijk",
                        "trend": list(range(20)),
                    }
                ],
            }
        )
        check(
            "atomic snapshot exists",
            path.exists() and path.stat().st_mode & 0o777 == 0o600,
        )
        data = json.loads(path.read_text(encoding="utf-8"))
        check(
            "snapshot bounds",
            len(data["events"]) == 200 and len(data["flows"][0]["trend"]) == 12,
        )
        check(
            "basename abbreviation",
            upload_observe.abbreviate_basename("abcdefghijk") == "bcdefghijk",
        )
    events = []
    previous = lfs_service._upload_observer
    try:
        lfs_service.set_upload_observer(events.append)
        coordinator = lfs_service._SlowFlowCoordinator(event_callback=None)
        coordinator._emit("sample", flow_id="01")
        check(
            "LFS observer callback is isolated",
            events == [{"kind": "sample", "flow_id": "01"}],
        )
    finally:
        lfs_service.set_upload_observer(previous)
    publisher = FakePublisher()
    structured = upload_observe.UploadSession("structured", publisher=publisher)
    source_a = object()
    source_b = object()
    first = flow_envelope(1)
    check(
        "structured Flow state is accepted",
        structured.observe({"source_id": source_a, "envelope": first}) is True
        and structured.data["flows"][0]["flow_id"] == "Flow-01"
        and structured.data["active_flows"] == 1,
    )
    unchanged_at = structured.data["updated_at"]
    check(
        "duplicate sequence is ignored without touching the session",
        structured.observe({"source_id": source_a, "envelope": first}) is False
        and structured.data["updated_at"] == unchanged_at
        and len(structured.data["flows"]) == 1,
    )
    check(
        "the same child Flow key from a new source gets a new session Flow",
        structured.observe({"source_id": source_b, "envelope": flow_envelope(1)})
        is True
        and [flow["flow_id"] for flow in structured.data["flows"]]
        == ["Flow-01", "Flow-02"],
    )
    event = {
        "version": 1,
        "type": "flow_event",
        "sequence": 2,
        "flow_key": 1,
        "payload": {
            "event": "replacement_approved",
            "replacement": 1,
            "delay": 2.0,
            "probe": False,
        },
    }
    check(
        "bounded structured events retain only safe parent-owned identity",
        structured.observe({"source_id": source_a, "envelope": event}) is True
        and structured.data["events"][-1]["flow_id"] == "Flow-01"
        and "source_id" not in json.dumps(structured.data, ensure_ascii=False),
    )
    invalid = flow_envelope(3, token="must-not-survive")
    unchanged_at = structured.data["updated_at"]
    check(
        "unknown or sensitive Flow fields fail closed",
        structured.observe({"source_id": source_a, "envelope": invalid}) is False
        and structured.data["updated_at"] == unchanged_at
        and "must-not-survive" not in repr(structured.data),
    )
    reconnecting = flow_envelope(
        3,
        replacement_count=1,
        phase="verifying_reconnect",
        last_decision="reconnect_started",
    )
    improved = {
        "version": 1,
        "type": "flow_event",
        "sequence": 4,
        "flow_key": 1,
        "payload": {"event": "improvement_passed", "replacement": 1},
    }
    check(
        "invalid messages do not consume sequence and totals remain idempotent",
        structured.observe({"source_id": source_a, "envelope": reconnecting}) is True
        and structured.observe({"source_id": source_a, "envelope": improved}) is True
        and structured.observe({"source_id": source_a, "envelope": improved}) is False
        and structured.data["replacement_total"] == 1
        and structured.data["improvement_total"] == 1,
    )
    for sequence in range(5, 210):
        structured.observe(
            {
                "source_id": source_a,
                "envelope": {
                    "version": 1,
                    "type": "flow_event",
                    "sequence": sequence,
                    "flow_key": 1,
                    "payload": {"event": "replacement_disabled"},
                },
            }
        )
    check(
        "structured events stay bounded and disabled totals are idempotent",
        len(structured.data["events"]) == upload_observe.MAX_EVENTS
        and structured.data["disabled_total"] == 1,
    )
    check(
        "parent terminal convergence updates only known active source Flows",
        structured.observe({"source_id": source_a, "terminal": "failed"}) is True
        and structured.data["flows"][0]["phase"] == "failed"
        and structured.data["flows"][1]["phase"] == "establishing_baseline"
        and structured.data["active_flows"] == 1,
    )
    rendered = upload_observe.render_session(structured.data)
    check(
        "Flow renderer shows bounded speeds, ratios, trend and Chinese phase",
        "Flow-01" in rendered
        and "20.0B/s" in rendered
        and "失败" in rendered
        and "0/3" in rendered,
    )
    integrated_queue = queue.Queue(maxsize=256)
    integrated_sender = upload_resumable._UploadObservationSender(integrated_queue)
    integrated_publisher = FakePublisher()
    integrated = upload_observe.UploadSession(
        "integrated", publisher=integrated_publisher
    )
    previous = lfs_service._upload_observer
    try:
        lfs_service.set_upload_observer(integrated.observe)
        coordinator = lfs_service._SlowFlowCoordinator(
            observation_callback=integrated_sender.send
        )
        coordinator.register(
            "private-oid",
            total_bytes=100,
            file_abbrev="source.bin",
            transfer_type="basic",
        )
        upload_resumable._drain_upload_observations(integrated_queue, "private-source")
    finally:
        lfs_service.set_upload_observer(previous)
    check(
        "coordinator state crosses the transport into the parent session",
        len(integrated.data["flows"]) == 1
        and integrated.data["flows"][0]["flow_id"] == "Flow-01"
        and "private-oid" not in repr(integrated.data),
    )
    with tempfile.TemporaryDirectory() as td:
        os.environ["HF_HOME"] = td
        publisher = upload_observe.SnapshotPublisher(
            interval=0.05, heartbeat=0.05
        ).start()
        publisher.submit({"session_id": "background", "status": "active"})
        import time

        time.sleep(0.12)
        publisher.stop()
        check(
            "background publisher writes latest snapshot",
            (upload_observe.observe_root() / "background.json").exists(),
        )
        session = upload_observe.UploadSession("lifecycle", repo_name="owner/demo")
        session.finish("finished")
        session.close()
        final = json.loads(
            (upload_observe.observe_root() / "lifecycle.json").read_text()
        )
        check(
            "session close flushes final state",
            final["status"] == "finished" and final["repo_name"] == "demo",
        )
    print(f"summary: {sum(checks)}/{len(checks)} passed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
