#!/usr/bin/env python3
"""Offline contract checks for the read-only upload monitor."""

import json
import os
import tempfile

from click.testing import CliRunner

import atomgit
from atomgit.adapters.lfs import service as lfs_service
from atomgit.infrastructure import upload_observe


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
