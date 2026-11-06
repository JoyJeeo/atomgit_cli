#!/usr/bin/env python3
"""Verify persistent, checksummed CLI download resume behavior."""

import hashlib
import io
import multiprocessing
import os
import stat
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from click.testing import CliRunner

import atomgit  # noqa: F401

api_mod = sys.modules["atomgit.api"]
cli_mod = sys.modules["atomgit.cli"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    print(
        f"[{'PASS' if condition else 'FAIL'}] {name}"
        + (f" -> {detail}" if detail else "")
    )


class ReadError(Exception):
    pass


class FakeSocket:
    def close(self):
        pass


def lock_worker(connection, path):
    from atomgit.adapters.download.resume import _resume_download_lock

    try:
        with _resume_download_lock(Path(path)):
            connection.send("acquired")
            connection.recv()
    except Exception as error:
        connection.send(type(error).__name__)
    finally:
        connection.close()


def lock_checks():
    from unittest.mock import patch

    from atomgit.adapters.download import resume

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        lock = root / "resume.lock"
        lock.write_text("99999999")
        barrier = threading.Barrier(2)
        first_inside = threading.Event()
        second_inside = threading.Event()
        overlapping = []
        occupancy = [0]
        occupancy_lock = threading.Lock()
        errors = []

        def stale_owner(pid):
            barrier.wait(timeout=3)
            if threading.current_thread().name == "second":
                if not first_inside.wait(3):
                    raise TimeoutError("first contender did not enter")
            return False

        def contender():
            try:
                with resume._resume_download_lock(lock):
                    with occupancy_lock:
                        occupancy[0] += 1
                        overlapping.append(occupancy[0] > 1)
                    try:
                        if threading.current_thread().name == "first":
                            first_inside.set()
                            second_inside.wait(0.2)
                        else:
                            second_inside.set()
                    finally:
                        with occupancy_lock:
                            occupancy[0] -= 1
            except RuntimeError:
                errors.append("busy")

        with patch.object(resume, "_process_is_running", stale_owner):
            first = threading.Thread(target=contender, name="first")
            second = threading.Thread(target=contender, name="second")
            first.start()
            second.start()
            first.join(5)
            second.join(5)
        check(
            "stale lock recovery never admits concurrent writers", not any(overlapping)
        )
        check("resume lock file persists after release", lock.is_file())

        import ctypes
        from types import SimpleNamespace

        closed = []

        def open_process(*args):
            return 123

        def wait_process(*args):
            return 258  # WAIT_TIMEOUT: still running

        def close_handle(handle):
            closed.append(handle)
            return True

        kernel = SimpleNamespace(
            OpenProcess=open_process,
            WaitForSingleObject=wait_process,
            CloseHandle=close_handle,
        )
        with (
            patch.object(resume.os, "name", "nt"),
            patch.object(ctypes, "WinDLL", return_value=kernel, create=True),
            patch.object(
                resume.os, "kill", side_effect=AssertionError("destructive PID probe")
            ),
        ):
            check(
                "Windows probe uses non-destructive process handles",
                resume._process_is_running(123),
            )
            check("Windows probe closes its process handle", closed == [123])

        context = multiprocessing.get_context("spawn")
        parent, child = context.Pipe()
        worker = context.Process(target=lock_worker, args=(child, str(lock)))
        worker.start()
        child.close()
        try:
            check(
                "real child acquires existing lock",
                parent.poll(5) and parent.recv() == "acquired",
            )
            check(
                "PID query reports a live disposable child",
                resume._process_is_running(worker.pid),
            )
            worker.join(0.1)
            check("PID query leaves the child alive", worker.is_alive())
            try:
                with resume._resume_download_lock(lock):
                    busy = False
            except RuntimeError:
                busy = True
            check("another process cannot acquire an owned resume lock", busy)
            with resume._resume_download_lock(root / "other.lock"):
                check("different files lock independently", True)
            worker.terminate()
            worker.join(5)
            with resume._resume_download_lock(lock):
                check("crashed owner releases the OS lock", True)
        finally:
            if worker.is_alive():
                worker.terminate()
            worker.join(5)
            parent.close()
        check(
            "dead process is reported absent",
            not resume._process_is_running(worker.pid),
        )
        try:
            with resume._resume_download_lock(lock):
                raise ValueError("fixture")
        except ValueError:
            with resume._resume_download_lock(lock):
                check("body exceptions release the lock", True)


def main():
    lock_checks()
    content = b"persistent-resume-content"
    checksum = ("sha256", hashlib.sha256(content).hexdigest(), len(content))
    original_metadata = api_mod._atomgit_file_download_metadata
    original_http_get = api_mod.hf_http_get
    original_cache_root = api_mod._resume_cache_root
    try:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = root / "cache"
            cache.mkdir(mode=0o700)
            destination = root / "target.bin"
            destination.write_bytes(b"preserve-target")
            api_mod._resume_cache_root = lambda: cache
            api_mod._atomgit_file_download_metadata = lambda *args: (
                checksum,
                "https://cdn.example/signed-object?secret=redacted",
            )
            calls = []

            def interrupted_get(url, stream, **kwargs):
                calls.append((url, dict(kwargs)))
                stream.write(content[:8])
                raise ReadError("offline interruption")

            api_mod.hf_http_get = interrupted_get
            try:
                api_mod._download_atomgit_file_resumable(
                    "user/repo",
                    "model",
                    "target.bin",
                    destination,
                    "fake-token-never-print",
                )
                first_error = None
            except Exception as error:
                first_error = error
            partials = list(cache.glob("*.part"))
            check("interruption is reported", isinstance(first_error, ReadError))
            check(
                "interruption preserves destination",
                destination.read_bytes() == b"preserve-target",
            )
            check(
                "interruption preserves one private partial",
                len(partials) == 1 and partials[0].read_bytes() == content[:8],
            )
            check(
                "partial permissions are restrictive",
                stat.S_IMODE(partials[0].stat().st_mode) == 0o600,
            )
            check(
                "resume cache contains no signed URL",
                "secret" not in partials[0].name
                and len(list(cache.glob("*.part"))) == 1,
            )

            def completing_get(url, stream, **kwargs):
                calls.append((url, dict(kwargs)))
                check("second request starts at saved byte", kwargs["resume_size"] == 8)
                check(
                    "resume downloader receives only unsigned resolve URL",
                    url.startswith("https://hub.atomgit.com/") and "?" not in url,
                    url,
                )
                stream.write(content[kwargs["resume_size"] :])

            api_mod.hf_http_get = completing_get
            api_mod._download_atomgit_file_resumable(
                "user/repo",
                "model",
                "target.bin",
                destination,
                "fake-token-never-print",
            )
            check(
                "resumed content atomically replaces destination",
                destination.read_bytes() == content,
            )
            check(
                "successful resume removes partial and keeps one persistent lock",
                not list(cache.glob("*.part")) and len(list(cache.glob("*.lock"))) == 1,
            )

            identity = api_mod._resume_cache_identity(
                "user/repo", "model", "target.bin"
            )
            corrupt_partial = cache / f"{identity}.{checksum[1]}.part"
            corrupt_partial.write_bytes(b"corrupt!")
            stale_partial = cache / f"{identity}.{'0' * 64}.part"
            stale_partial.write_bytes(b"stale")
            recovery_offsets = []

            def recovering_get(url, stream, **kwargs):
                offset = kwargs["resume_size"]
                recovery_offsets.append(offset)
                stream.write(content[offset:])

            api_mod.hf_http_get = recovering_get
            api_mod._download_atomgit_file_resumable(
                "user/repo",
                "model",
                "target.bin",
                destination,
                "fake-token-never-print",
            )
            check(
                "corrupt partial is discarded and restarted from zero",
                recovery_offsets == [8, 0] and destination.read_bytes() == content,
                repr(recovery_offsets),
            )
            check(
                "stale checksum partial is removed",
                not list(cache.glob("*.part")),
            )

            raw_partial = io.BytesIO(content[:5])
            raw_partial.seek(0, os.SEEK_END)

            def ranged_raw(*args, **kwargs):
                remaining = content[5:]
                headers = {
                    "content-range": f"bytes 5-{len(content) - 1}/{len(content)}",
                    "content-length": str(len(remaining)),
                }
                return 206, headers, io.BytesIO(remaining), FakeSocket()

            original_raw = api_mod._atomgit_raw_http_get
            api_mod._atomgit_raw_http_get = ranged_raw
            try:
                api_mod._atomgit_resume_raw(
                    "https://hub.atomgit.com/user/repo/resolve/main/中文.bin",
                    raw_partial,
                    {},
                    5,
                    len(content),
                )
                check(
                    "raw UTF-8 range resumes exact bytes",
                    raw_partial.getvalue() == content,
                )

                def wrong_range(*args, **kwargs):
                    remaining = content[5:]
                    headers = {
                        "content-range": f"bytes 4-{len(content) - 1}/{len(content)}",
                        "content-length": str(len(remaining)),
                    }
                    return 206, headers, io.BytesIO(remaining), FakeSocket()

                api_mod._atomgit_raw_http_get = wrong_range
                invalid_partial = io.BytesIO(content[:5])
                invalid_partial.seek(0, os.SEEK_END)
                try:
                    api_mod._atomgit_resume_raw(
                        "https://hub.atomgit.com/user/repo/resolve/main/中文.bin",
                        invalid_partial,
                        {},
                        5,
                        len(content),
                    )
                    range_error = None
                except Exception as error:
                    range_error = error
                check(
                    "raw resume rejects an unexpected Content-Range",
                    range_error is not None
                    and invalid_partial.getvalue() == content[:5],
                    repr(range_error),
                )
            finally:
                api_mod._atomgit_raw_http_get = original_raw
    finally:
        api_mod._atomgit_file_download_metadata = original_metadata
        api_mod.hf_http_get = original_http_get
        api_mod._resume_cache_root = original_cache_root

    target_auth = []

    class TargetHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            target_auth.append(self.headers.get("Authorization"))
            self.send_response(200)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, *args):
            pass

    target_server = HTTPServer(("127.0.0.1", 0), TargetHandler)

    class RedirectHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302)
            self.send_header(
                "Location",
                f"http://127.0.0.1:{target_server.server_port}/object",
            )
            self.end_headers()

        def log_message(self, *args):
            pass

    redirect_server = HTTPServer(("127.0.0.1", 0), RedirectHandler)
    threads = [
        threading.Thread(target=server.serve_forever, daemon=True)
        for server in (target_server, redirect_server)
    ]
    for thread in threads:
        thread.start()
    try:
        output = io.BytesIO()
        original_http_get(
            f"http://127.0.0.1:{redirect_server.server_port}/resolve",
            output,
            headers={"Authorization": "Bearer fake-token-never-print"},
            expected_size=len(content),
            displayed_filename="file.bin",
        )
        check(
            "locked resumable downloader strips auth across origins",
            output.getvalue() == content and target_auth == [None],
            repr(target_auth),
        )
    finally:
        for server in (redirect_server, target_server):
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(timeout=2)

    original_cli_repo = cli_mod.api.download_repo
    original_cli_file = cli_mod.api.download_file
    original_logged_in = cli_mod.config.is_logged_in
    cli_calls = []
    try:
        cli_mod.config.is_logged_in = lambda: True
        cli_mod.api.download_repo = (
            lambda *args, **kwargs: cli_calls.append(("repo", kwargs)) or True
        )
        cli_mod.api.download_file = (
            lambda *args, **kwargs: cli_calls.append(("file", kwargs)) or True
        )
        runner = CliRunner()
        with runner.isolated_filesystem():
            repo_result = runner.invoke(
                cli_mod.cli, ["download", "user/repo", "--resume"]
            )
            file_result = runner.invoke(
                cli_mod.cli,
                ["download-file", "user/repo", "file.bin", "--resume"],
            )
        check("repository resume option succeeds", repo_result.exit_code == 0)
        check("single-file resume option succeeds", file_result.exit_code == 0)
        check(
            "resume option reaches both API paths",
            len(cli_calls) == 2
            and all(call[1].get("resume_download") is True for call in cli_calls),
            repr(cli_calls),
        )
    finally:
        cli_mod.api.download_repo = original_cli_repo
        cli_mod.api.download_file = original_cli_file
        cli_mod.config.is_logged_in = original_logged_in

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
