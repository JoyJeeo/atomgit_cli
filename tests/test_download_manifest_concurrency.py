#!/usr/bin/env python3
"""Concurrent repository downloads cannot overwrite manifest ownership."""

import json
import os
import stat
import sys
import tempfile
import threading
from pathlib import Path

import atomgit  # noqa: F401


api_mod = sys.modules["atomgit.api"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    print(
        f"[{'PASS' if condition else 'FAIL'}] {name}"
        + (f" -> {detail}" if detail else "")
    )


def main():
    original_list = api_mod._atomgit_list_repo_files
    original_fetch = api_mod._download_atomgit_file
    original_credentials = api_mod.config.get_credentials
    original_manifest_root = api_mod._download_manifest_root
    first_transfer_started = threading.Event()
    release_first_transfer = threading.Event()
    second_transfer_started = threading.Event()
    transfer_calls = []
    outcomes = {}

    try:
        with tempfile.TemporaryDirectory() as directory:
            sandbox = Path(directory)
            manifest_root = sandbox / "manifests"
            target = sandbox / "target"

            def fake_manifest_root():
                manifest_root.mkdir(mode=0o700, parents=True, exist_ok=True)
                os.chmod(manifest_root, 0o700)
                return manifest_root

            def fake_list(*args, **kwargs):
                if threading.current_thread().name == "manifest-first":
                    return "model", ["a.bin"]
                return "model", ["b.bin"]

            def fake_fetch(
                repo_id, repo_type, filename, destination, token, **kwargs
            ):
                transfer_calls.append(filename)
                if filename == "a.bin":
                    first_transfer_started.set()
                    if not release_first_transfer.wait(10):
                        raise TimeoutError("offline concurrency fixture timed out")
                else:
                    second_transfer_started.set()
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(filename.encode("ascii"))

            api_mod._download_manifest_root = fake_manifest_root
            api_mod._atomgit_list_repo_files = fake_list
            api_mod._download_atomgit_file = fake_fetch
            api_mod.config.get_credentials = lambda: None

            def run_download(label):
                outcomes[label] = api_mod.api.download_repo(
                    "user/repo", target, force_download=True
                )

            first = threading.Thread(
                target=run_download, args=("first",), name="manifest-first"
            )
            second = threading.Thread(
                target=run_download, args=("second",), name="manifest-second"
            )
            first.start()
            if not first_transfer_started.wait(10):
                raise RuntimeError("first fixture transfer did not start")
            second.start()
            second.join(10)
            release_first_transfer.set()
            first.join(10)

            check(
                "competing checkout download fails while owner succeeds",
                outcomes == {"second": False, "first": True},
                repr(outcomes),
            )
            check(
                "busy download performs no competing transfer",
                not second_transfer_started.is_set() and not (target / "b.bin").exists(),
            )

            manifest_path = api_mod._download_manifest_path(
                "user/repo", "model", target
            )
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            check(
                "winning transaction writes complete manifest",
                payload["files"] == ["a.bin"],
                repr(payload),
            )

            sequential = api_mod.api.download_repo(
                "user/repo", target, force_download=True
            )
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            check(
                "released lock permits later manifest merge",
                sequential and payload["files"] == ["a.bin", "b.bin"],
                repr(payload),
            )
            released_after_error = False
            try:
                with api_mod._download_manifest_lock(manifest_path):
                    raise RuntimeError("offline lock-body failure")
            except RuntimeError:
                with api_mod._download_manifest_lock(manifest_path):
                    released_after_error = True
            check(
                "manifest lock releases after body exception",
                released_after_error,
            )

            manifest_before_busy_prune = manifest_path.read_bytes()
            transfers_before_busy_prune = len(transfer_calls)
            with api_mod._download_manifest_lock(manifest_path):
                busy_prune = api_mod.api.download_repo(
                    "user/repo", target, force_download=True, prune=True
                )
            check(
                "busy prune fails before transfer and preserves state",
                busy_prune is False
                and len(transfer_calls) == transfers_before_busy_prune
                and manifest_path.read_bytes() == manifest_before_busy_prune,
            )

            other_manifest = manifest_root / "other.json"
            independent_identity = False
            with api_mod._download_manifest_lock(manifest_path):
                with api_mod._download_manifest_lock(other_manifest):
                    independent_identity = True
            check(
                "different manifest identities lock independently",
                independent_identity,
            )
            lock_path = manifest_path.with_name(manifest_path.name + ".lock")
            check(
                "persistent lock file is private and opaque",
                lock_path.is_file()
                and stat.S_IMODE(lock_path.stat().st_mode) == 0o600
                and "user" not in lock_path.name
                and "repo" not in lock_path.name,
                lock_path.name,
            )
            check(
                "busy-lock error has actionable sanitized guidance",
                api_mod.sanitized_download_error(
                    RuntimeError("download manifest is already in use")
                )
                == "同一目标目录已有下载任务，请等待完成后重试",
            )
    finally:
        api_mod._atomgit_list_repo_files = original_list
        api_mod._download_atomgit_file = original_fetch
        api_mod.config.get_credentials = original_credentials
        api_mod._download_manifest_root = original_manifest_root

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
