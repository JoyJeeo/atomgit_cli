#!/usr/bin/env python3
"""SDK upload restores Hugging Face process-global timeout state."""

import tempfile
from pathlib import Path

import atomgit_hub
from huggingface_hub import constants as hf_constants

from atomgit.interfaces.sdk import AtomGitClient


results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def concurrent_session_checks():
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from unittest.mock import patch

    from huggingface_hub import close_session, get_session

    from atomgit.adapters import sdk_uploads

    initial = hf_constants.DEFAULT_REQUEST_TIMEOUT
    entered, second_entered, release = (
        threading.Event(),
        threading.Event(),
        threading.Event(),
    )
    observations = []

    def upload(**kwargs):
        label = kwargs["commit_message"]
        if label == "first":
            entered.set()
            assert release.wait(5)
        else:
            second_entered.set()
        observations.append((label, get_session().timeout.read))
        return "commit"

    def first(source):
        return sdk_uploads.upload_folder(
            source,
            "fake/repo",
            token="fake-token",
            upload_timeout=10,
            commit_message="first",
        )

    try:
        hf_constants.DEFAULT_REQUEST_TIMEOUT = 19
        close_session()
        get_session()  # Deliberately create a cached client before either upload.
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(sdk_uploads, "hf_upload_folder", upload),
            ThreadPoolExecutor(max_workers=2) as executor,
        ):
            source = Path(directory)
            (source / "data.bin").write_bytes(b"fixture")
            a = executor.submit(first, source)
            assert entered.wait(5)
            b = executor.submit(
                sdk_uploads.upload_folder,
                source,
                "fake/repo",
                token="fake-token",
                upload_timeout=20,
                commit_message="second",
            )
            try:
                check(
                    "ordinary uploads do not overlap global timeout scopes",
                    not second_entered.wait(0.2),
                )
            finally:
                release.set()
            a.result(8)
            b.result(8)
        check(
            "actual cached HTTP sessions use each requested timeout",
            sorted(observations) == [("first", 10), ("second", 20)],
        )
        check(
            "concurrent upload restores original HTTP timeout",
            hf_constants.DEFAULT_REQUEST_TIMEOUT == 19
            and get_session().timeout.read == 19,
        )
    finally:
        release.set()
        close_session()
        hf_constants.DEFAULT_REQUEST_TIMEOUT = initial


def isolated_worker(connection, fail):
    from huggingface_hub import get_session
    from huggingface_hub.utils import are_progress_bars_disabled

    from atomgit.adapters.upload.ordinary import _scoped_upload_settings

    original = hf_constants.DEFAULT_REQUEST_TIMEOUT
    try:
        with _scoped_upload_settings(7, False):
            connection.send((get_session().timeout.read, are_progress_bars_disabled()))
            connection.recv()
            if fail:
                raise RuntimeError("offline failure")
    except RuntimeError:
        pass
    connection.send(hf_constants.DEFAULT_REQUEST_TIMEOUT == original)
    connection.close()


def process_isolation_checks():
    import multiprocessing

    from huggingface_hub import close_session, get_session
    from huggingface_hub.utils import are_progress_bars_disabled

    original = hf_constants.DEFAULT_REQUEST_TIMEOUT
    try:
        hf_constants.DEFAULT_REQUEST_TIMEOUT = 23
        close_session()
        parent_session = get_session()
        parent_progress = are_progress_bars_disabled()
        for fail in (False, True):
            context = multiprocessing.get_context("spawn")
            parent, child = context.Pipe()
            process = context.Process(target=isolated_worker, args=(child, fail))
            process.start()
            child.close()
            try:
                assert parent.poll(10), "worker did not enter upload scope"
                check(
                    "independent process applies its own upload settings",
                    parent.recv() == (7, True),
                )
                check(
                    "concurrent caller HF session and progress stay unchanged",
                    get_session() is parent_session
                    and not parent_session.is_closed
                    and get_session().timeout.read == 23
                    and are_progress_bars_disabled() == parent_progress,
                )
                parent.send("continue")
                assert parent.poll(10), "worker did not restore settings"
                check(
                    "isolated worker restores settings on success and failure",
                    parent.recv() is True,
                )
                process.join(10)
                check("isolated worker exits cleanly", process.exitcode == 0)
            finally:
                if process.is_alive():
                    process.terminate()
                    process.join(5)
                parent.close()
    finally:
        close_session()
        hf_constants.DEFAULT_REQUEST_TIMEOUT = original


def main():
    process_isolation_checks()
    concurrent_session_checks()

    original_upload = atomgit_hub.hf_upload_folder
    original_canonical_upload = atomgit_hub.run_canonical_lfs_upload
    suite_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT
    pointer_timeouts = []

    def capture_canonical_upload(upload, *, token, repo_id, timeout):
        pointer_timeouts.append(timeout)
        return upload()

    atomgit_hub.run_canonical_lfs_upload = capture_canonical_upload
    try:
        with tempfile.TemporaryDirectory() as source_dir:
            source = Path(source_dir)
            (source / "file.bin").write_bytes(b"content")
            hf_constants.DEFAULT_REQUEST_TIMEOUT = 19
            request_timeouts = []

            def successful_upload(**kwargs):
                request_timeouts.append(hf_constants.DEFAULT_REQUEST_TIMEOUT)
                return "commit-url"

            atomgit_hub.hf_upload_folder = successful_upload
            result = atomgit_hub.upload_folder(
                source,
                "user/repo",
                token="fake-token",
                upload_timeout=10,
            )
            check("success result preserved", result == "commit-url")
            check(
                "legacy SDK forwards the requested timeout to upload and verification",
                request_timeouts[-1] == 10 and pointer_timeouts[-1] == 10,
            )
            check(
                "timeout restored after success",
                hf_constants.DEFAULT_REQUEST_TIMEOUT == 19,
            )

            default_result = atomgit_hub.upload_folder(
                source,
                "user/repo",
                token="fake-token",
            )
            check(
                "legacy SDK defaults upload and verification to 300 seconds",
                default_result == "commit-url"
                and request_timeouts[-1] == 300.0
                and pointer_timeouts[-1] == 300.0,
            )
            native_result = AtomGitClient(token="fake-token").upload_folder(
                source,
                "user/repo",
                token="fake-token",
                resumable=False,
                timeout=28800,
            )
            check(
                "native SDK ordinary upload keeps a large verification timeout",
                native_result.ok
                and request_timeouts[-1] == 28800
                and pointer_timeouts[-1] == 28800,
            )

            commit_revision = "a" * 40
            legacy_unconfirmed = atomgit_hub.CanonicalLfsCommitUnconfirmedError(
                commit_revision
            )
            check(
                "legacy post-commit errors default to an unknown safe reason",
                legacy_unconfirmed.confirmation_failure == "unknown_read_failure",
            )

            def unconfirmed_upload(*args, **kwargs):
                raise atomgit_hub.CanonicalLfsCommitUnconfirmedError._for_confirmation_failure(
                    commit_revision,
                    "response_malformed",
                )

            atomgit_hub.run_canonical_lfs_upload = unconfirmed_upload
            try:
                atomgit_hub.upload_folder(
                    source,
                    "user/repo",
                    token="fake-token",
                )
            except atomgit_hub.CanonicalLfsPointerError as error:
                check(
                    "legacy SDK preserves the post-commit error subclass",
                    isinstance(error, atomgit_hub.CanonicalLfsCommitUnconfirmedError)
                    and error.commit_revision == commit_revision
                    and error.confirmation_failure == "response_malformed",
                )
            else:
                check(
                    "legacy SDK preserves the post-commit error subclass",
                    False,
                    "no exception",
                )
            atomgit_hub.run_canonical_lfs_upload = capture_canonical_upload

            def failing_upload(**kwargs):
                check(
                    "requested timeout visible during failure",
                    hf_constants.DEFAULT_REQUEST_TIMEOUT == 11,
                )
                raise RuntimeError("offline upload failure")

            atomgit_hub.hf_upload_folder = failing_upload
            try:
                atomgit_hub.upload_folder(
                    source,
                    "user/repo",
                    token="fake-token",
                    upload_timeout=11,
                )
            except Exception as error:
                check(
                    "failure remains actionable",
                    isinstance(error, atomgit_hub.AtomGitError)
                    and error.__cause__ is None
                    and error.__suppress_context__,
                )
            else:
                check("failure remains actionable", False, "no exception")
            check(
                "timeout restored after failure",
                hf_constants.DEFAULT_REQUEST_TIMEOUT == 19,
            )

            before = hf_constants.DEFAULT_REQUEST_TIMEOUT
            try:
                atomgit_hub.upload_folder(
                    source,
                    "user/repo",
                    token="fake-token",
                    revision="dev",
                    upload_timeout=23,
                )
            except ValueError:
                pass
            check(
                "preflight failure leaves timeout unchanged",
                hf_constants.DEFAULT_REQUEST_TIMEOUT == before,
            )
    finally:
        atomgit_hub.hf_upload_folder = original_upload
        atomgit_hub.run_canonical_lfs_upload = original_canonical_upload
        hf_constants.DEFAULT_REQUEST_TIMEOUT = suite_timeout

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
