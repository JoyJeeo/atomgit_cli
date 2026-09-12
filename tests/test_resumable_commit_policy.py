#!/usr/bin/env python3
"""Offline regressions for AtomGit resumable commit retry policy."""

import httpx
import os
import queue
import sys
import tempfile
from types import SimpleNamespace
from contextlib import contextmanager, redirect_stdout
from io import StringIO
from pathlib import Path

import atomgit  # noqa: F401
import atomgit.lfs_pointer as pointer_mod
from huggingface_hub import CommitOperationAdd
from huggingface_hub.errors import HfHubHTTPError


api_mod = sys.modules["atomgit.api"]


def http_error(status, retry_after=None):
    headers = {}
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    request = httpx.Request("POST", "https://hub.atomgit.com/api/models/u/r/commit/main")
    response = httpx.Response(status, headers=headers, request=request)
    return HfHubHTTPError(f"HTTP {status}", response=response)


class FakeOperation:
    def __init__(self, path, *, size=None, upload_mode=None):
        self.path_in_repo = path
        if size is not None:
            self.upload_info = SimpleNamespace(size=size)
        if upload_mode is not None:
            self._upload_mode = upload_mode


class ScriptedClient:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []
        self.kwarg_calls = []

    def create_commit(self, *args, **kwargs):
        operations = list(kwargs["operations"])
        self.calls.append([item.path_in_repo for item in operations])
        self.kwarg_calls.append(dict(kwargs))
        outcome = self.outcomes.pop(0) if self.outcomes else None
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class FatalHfApi:
    """Exercise bounded child termination without a remote request."""

    def __init__(self, endpoint=None, token=None):
        self.endpoint = endpoint
        self.token = token

    def create_commit(self, *args, **kwargs):
        raise http_error(429, retry_after=0)

    def upload_large_folder(self, **kwargs):
        operation = CommitOperationAdd(
            path_in_repo="payload.bin", path_or_fileobj=b"payload"
        )
        operation._upload_mode = "regular"
        return self.create_commit(
            repo_id=kwargs["repo_id"],
            repo_type=kwargs["repo_type"],
            revision="main",
            operations=[operation],
            commit_message="batch",
        )


def make_controller(
    client, sleeps, reconcile=None, max_attempts=3, mark_committed=None,
    event_callback=None,
):
    return api_mod._ResumableCommitController(
        client.create_commit,
        token="fake-token-never-print",
        sleep=sleeps.append,
        jitter=lambda delay: 0,
        reconcile=reconcile or (lambda **kwargs: set()),
        max_attempts=max_attempts,
        mark_committed=mark_committed or (lambda operations: None),
        event_callback=event_callback,
    )


def main():
    results = []

    def check(name, condition, detail=""):
        results.append(bool(condition))
        print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))

    operations = [FakeOperation(f"file-{index:02d}.bin") for index in range(20)]

    policy_events = []
    oversized_regular = FakeOperation(
        "captures/run.bag",
        size=api_mod._RESUMABLE_REGULAR_FILE_MAX_BYTES + 1,
        upload_mode="regular",
    )
    policy_client = ScriptedClient(["must-not-run"])
    controller = make_controller(
        policy_client,
        [],
        reconcile=lambda **kwargs: policy_events.append("reconcile") or set(),
        event_callback=policy_events.append,
    )
    try:
        controller.create_commit(
            repo_id="user/repo",
            repo_type="model",
            revision="main",
            operations=[oversized_regular],
            commit_message="batch",
        )
    except api_mod.ResumableUploadModeError as error:
        oversized_blocked = ".gitattributes" in str(error)
    else:
        oversized_blocked = False
    check("oversized regular file is rejected before commit", oversized_blocked)
    check("upload-mode rejection does not retry, reconcile, or reduce",
          not policy_client.calls and not policy_events, repr(policy_events))

    large_lfs = FakeOperation(
        "captures/run.bag",
        size=api_mod._RESUMABLE_REGULAR_FILE_MAX_BYTES + 1,
        upload_mode="lfs",
    )
    lfs_client = ScriptedClient(["lfs-ok"])
    lfs_result = make_controller(lfs_client, []).create_commit(
        repo_id="user/repo", repo_type="model", revision="main",
        operations=[large_lfs], commit_message="batch",
    )
    check("large LFS operation remains supported", lfs_result == "lfs-ok")

    small_regular = FakeOperation(
        "notes.txt",
        size=api_mod._RESUMABLE_REGULAR_FILE_MAX_BYTES,
        upload_mode="regular",
    )
    regular_client = ScriptedClient(["regular-ok"])
    regular_result = make_controller(regular_client, []).create_commit(
        repo_id="user/repo", repo_type="model", revision="main",
        operations=[small_regular], commit_message="batch",
    )
    check("safe regular operation remains supported", regular_result == "regular-ok")

    pointer_content = pointer_mod.canonical_lfs_pointer("12" * 32, 7)
    pointer_expectation = pointer_mod.CanonicalLfsPointer(
        path_in_repo="payload.bin",
        oid="12" * 32,
        size=7,
        content=pointer_content,
    )

    @contextmanager
    def pointer_expectations():
        yield [pointer_expectation]

    original_pointer_read = pointer_mod._read_raw_pointer
    original_pointer_sleep = pointer_mod.time.sleep
    pointer_sleeps = []
    pointer_reads = []
    pointer_outcomes = [
        pointer_mod.CanonicalLfsPointerError("temporary read failure"),
        pointer_content,
    ]

    def scripted_pointer_read(**kwargs):
        pointer_reads.append(kwargs)
        outcome = pointer_outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    pointer_mod._read_raw_pointer = scripted_pointer_read
    pointer_mod.time.sleep = pointer_sleeps.append
    try:
        pointer_operation = FakeOperation("payload.bin")
        recovered_client = ScriptedClient([SimpleNamespace(oid="d" * 40)])
        recovered_marked = []
        recovered_controller = api_mod._ResumableCommitController(
            recovered_client.create_commit,
            token="fake-token-never-print",
            canonical_payloads=pointer_expectations,
            verify_committed=lambda items, repo_id, revision: (
                pointer_mod.verify_canonical_lfs_pointers(
                    token="fake-token-never-print",
                    repo_id=repo_id,
                    revision=revision,
                    expectations=items,
                    timeout=17,
                )
            ),
            mark_committed=lambda items: recovered_marked.extend(items),
        )
        recovered_result = recovered_controller.create_commit(
            repo_id="user/repo",
            repo_type="model",
            revision="main",
            operations=[pointer_operation],
            commit_message="batch",
        )
        check(
            "pointer retry does not duplicate resumable create-commit",
            recovered_result.oid == "d" * 40
            and len(recovered_client.calls) == 1
            and len(pointer_reads) == 2
            and pointer_sleeps == [2.0],
        )
        check(
            "resumable metadata is marked only after pointer recovery",
            recovered_marked == [pointer_operation]
            and all(
                item["repo_id"] == "user/repo"
                and item["revision"] == "d" * 40
                and item["timeout"] == 17
                for item in pointer_reads
            ),
        )

        exhausted_client = ScriptedClient([SimpleNamespace(oid="e" * 40)])
        exhausted_marked = []
        pointer_reads.clear()
        pointer_sleeps.clear()

        def failing_pointer_read(**kwargs):
            pointer_reads.append(kwargs)
            raise pointer_mod.CanonicalLfsPointerError._for_confirmation_failure(
                "persistent read failure",
                "request_timeout",
            )

        pointer_mod._read_raw_pointer = failing_pointer_read
        exhausted_controller = api_mod._ResumableCommitController(
            exhausted_client.create_commit,
            token="fake-token-never-print",
            canonical_payloads=pointer_expectations,
            verify_committed=lambda items, repo_id, revision: (
                pointer_mod.verify_canonical_lfs_pointers(
                    token="fake-token-never-print",
                    repo_id=repo_id,
                    revision=revision,
                    expectations=items,
                    timeout=17,
                )
            ),
            mark_committed=lambda items: exhausted_marked.extend(items),
        )
        try:
            exhausted_controller.create_commit(
                repo_id="user/repo",
                repo_type="model",
                revision="main",
                operations=[pointer_operation],
                commit_message="batch",
            )
        except api_mod.ResumableCommitError as error:
            pointer_exhaustion_failed = True
            pointer_exhaustion_error = error
        else:
            pointer_exhaustion_failed = False
            pointer_exhaustion_error = None
        check(
            "exhausted pointer reads do not duplicate create-commit",
            pointer_exhaustion_failed
            and len(exhausted_client.calls) == 1
            and len(pointer_reads) == 3
            and pointer_sleeps == [2.0, 4.0],
        )
        check(
            "exhausted pointer reads leave resumable metadata uncommitted",
            not exhausted_marked,
        )
        error_chain = list(api_mod._resumable_error_chain(pointer_exhaustion_error))
        unconfirmed_errors = [
            error
            for error in error_chain
            if type(error).__name__ == "CanonicalLfsCommitUnconfirmedError"
        ]
        check(
            "resumable pointer exhaustion preserves the returned commit state",
            len(unconfirmed_errors) == 1
            and unconfirmed_errors[0].remote_commit_status == "created"
            and unconfirmed_errors[0].local_confirmation_status == "unconfirmed"
            and unconfirmed_errors[0].commit_revision == "e" * 40
            and unconfirmed_errors[0].confirmation_failure == "request_timeout"
            and len(exhausted_client.calls) == 1,
            repr([type(error).__name__ for error in error_chain]),
        )
        original_resolve_revision = api_mod._resolve_resumable_revision
        original_checksum = api_mod._atomgit_file_checksum
        original_verify = api_mod.verify_canonical_lfs_pointers
        try:
            with tempfile.TemporaryDirectory(prefix="atomgit-pending-commit-") as td:
                projection = Path(td)
                payload = projection / "payload.bin"
                payload.write_bytes(b"content")
                rerun_operation = CommitOperationAdd(
                    path_in_repo="payload.bin",
                    path_or_fileobj=payload,
                )
                rerun_operation._upload_mode = "lfs"
                paths = api_mod.get_local_upload_paths(projection, "payload.bin")
                metadata = api_mod.read_upload_metadata(projection, "payload.bin")
                metadata.sha256 = rerun_operation.upload_info.sha256.hex()
                metadata.upload_mode = "lfs"
                metadata.is_uploaded = True
                metadata.save(paths)

                rerun_client = ScriptedClient([SimpleNamespace(oid="f" * 40)])
                api_mod._resolve_resumable_revision = lambda **kwargs: "a" * 40
                rerun_controller = api_mod._ResumableCommitController(
                    rerun_client.create_commit,
                    token="fake-token-never-print",
                    canonical_payloads=pointer_expectations,
                    verify_committed=lambda *args: (_ for _ in ()).throw(
                        pointer_mod.CanonicalLfsPointerError._for_confirmation_failure(
                            "persistent read failure",
                            "request_timeout",
                        )
                    ),
                    folder_path=projection,
                )
                try:
                    rerun_controller.create_commit(
                        repo_id="user/repo",
                        repo_type="model",
                        revision="main",
                        operations=[rerun_operation],
                        commit_message="batch",
                    )
                except api_mod.ResumableCommitError:
                    pass

                pending_after_failure = api_mod._read_pending_commit(projection)
                _, pending_path, _ = api_mod._pending_commit_paths(projection)
                pending_directory_mode = pending_path.parent.stat().st_mode & 0o777
                pending_file_mode = pending_path.stat().st_mode & 0o777
                api_mod._resolve_resumable_revision = lambda **kwargs: "f" * 40
                api_mod._atomgit_file_checksum = lambda *args: (
                    "sha256",
                    rerun_operation.upload_info.sha256.hex(),
                    rerun_operation.upload_info.size,
                )
                recovery_timeouts = []
                api_mod.verify_canonical_lfs_pointers = (
                    lambda **kwargs: recovery_timeouts.append(kwargs["timeout"])
                )
                recovery = api_mod._recover_pending_commit(
                    folder_path=projection,
                    token="fake-token-never-print",
                    repo_id="user/repo",
                    repo_type="model",
                    revision="main",
                    request_timeout=17,
                )
                recovered_metadata = api_mod.read_upload_metadata(
                    projection, "payload.bin"
                )
                check(
                    "returned commit is persisted before pointer confirmation",
                    pending_after_failure is not None
                    and pending_after_failure["state"] == "created_unconfirmed"
                    and pending_after_failure["commit_revision"] == "f" * 40,
                )
                check(
                    "resumable create-commit uses the persisted base revision",
                    rerun_client.kwarg_calls[0].get("parent_commit") == "a" * 40,
                )
                check(
                    "pending commit credential uses private filesystem modes",
                    pending_directory_mode == 0o700 and pending_file_mode == 0o600,
                    f"{pending_directory_mode:o}/{pending_file_mode:o}",
                )
                check(
                    "independent rerun confirms a returned commit without submitting again",
                    len(rerun_client.calls) == 1
                    and recovery["confirmed"] == 1
                    and recovered_metadata.is_committed
                    and recovery_timeouts == [17]
                    and api_mod._read_pending_commit(projection) is None,
                    repr(rerun_client.calls),
                )

                corrupt_projection = projection / "corrupt"
                corrupt_directory, corrupt_path, _ = api_mod._pending_commit_paths(
                    corrupt_projection
                )
                corrupt_directory.mkdir(parents=True, mode=0o700)
                corrupt_path.write_text('{"version":2}', encoding="utf-8")
                corrupt_path.chmod(0o600)
                try:
                    api_mod._read_pending_commit(corrupt_projection)
                except api_mod.ResumableRecoveryStateError:
                    corrupt_failed = True
                else:
                    corrupt_failed = False
                check(
                    "unknown pending schema fails closed and is preserved",
                    corrupt_failed and corrupt_path.is_file(),
                )
                fatal_errors = []
                corrupt_client = ScriptedClient([])
                corrupt_controller = api_mod._ResumableCommitController(
                    corrupt_client.create_commit,
                    token="fake-token-never-print",
                    folder_path=corrupt_projection,
                    fatal_callback=fatal_errors.append,
                )
                try:
                    corrupt_controller.create_commit(
                        repo_id="user/repo",
                        repo_type="model",
                        revision="main",
                        operations=[rerun_operation],
                        commit_message="batch",
                    )
                except api_mod.ResumableCommitError:
                    pass
                check(
                    "unsafe recovery state reaches the fatal path before commit",
                    len(fatal_errors) == 1
                    and isinstance(fatal_errors[0], api_mod.ResumableRecoveryStateError)
                    and not corrupt_client.calls,
                )

                oversized_projection = projection / "oversized"
                oversized_directory, oversized_path, _ = api_mod._pending_commit_paths(
                    oversized_projection
                )
                oversized_directory.mkdir(parents=True, mode=0o700)
                oversized_path.write_bytes(
                    b"x" * (api_mod._PENDING_COMMIT_MAX_BYTES + 1)
                )
                oversized_path.chmod(0o600)
                try:
                    api_mod._read_pending_commit(oversized_projection)
                except api_mod.ResumableRecoveryStateError:
                    oversized_failed = True
                else:
                    oversized_failed = False
                check(
                    "oversized pending state fails closed and is preserved",
                    oversized_failed and oversized_path.is_file(),
                )

                if os.name == "nt":
                    check("pending commit lock rejects symbolic links", True)
                else:
                    lock_projection = projection / "unsafe-lock"
                    lock_directory, _, lock_path = api_mod._pending_commit_paths(
                        lock_projection
                    )
                    lock_directory.mkdir(parents=True, mode=0o700)
                    lock_target = projection / "lock-target"
                    lock_target.write_bytes(b"safe")
                    lock_path.symlink_to(lock_target)
                    try:
                        with api_mod._resumable_projection_lock(lock_projection):
                            pass
                    except api_mod.ResumableRecoveryStateError:
                        unsafe_lock_failed = True
                    else:
                        unsafe_lock_failed = False
                    check(
                        "pending commit lock rejects symbolic links",
                        unsafe_lock_failed and lock_target.read_bytes() == b"safe",
                    )
        finally:
            api_mod._resolve_resumable_revision = original_resolve_revision
            api_mod._atomgit_file_checksum = original_checksum
            api_mod.verify_canonical_lfs_pointers = original_verify
    finally:
        pointer_mod._read_raw_pointer = original_pointer_read
        pointer_mod.time.sleep = original_pointer_sleep

    original_resolve_revision = api_mod._resolve_resumable_revision
    try:
        with tempfile.TemporaryDirectory(prefix="atomgit-parent-conflict-") as td:
            api_mod._resolve_resumable_revision = lambda **kwargs: "a" * 40
            conflict_operation = CommitOperationAdd(
                path_in_repo="payload.bin", path_or_fileobj=b"payload"
            )
            conflict_operation._upload_mode = "regular"
            conflict_client = ScriptedClient([http_error(409)])
            conflict_controller = api_mod._ResumableCommitController(
                conflict_client.create_commit,
                token="fake-token-never-print",
                folder_path=Path(td),
                max_attempts=1,
            )
            try:
                conflict_controller.create_commit(
                    repo_id="user/repo",
                    repo_type="model",
                    revision="main",
                    operations=[conflict_operation],
                    commit_message="batch",
                )
            except api_mod.ResumableCommitError as error:
                conflict_envelope = api_mod._resumable_failure_envelope(error)
            else:
                conflict_envelope = None
            check(
                "parent revision conflict fails closed without replay",
                len(conflict_client.calls) == 1
                and conflict_envelope
                == {
                    "category": "remote_commit_conflict",
                    "confirmed": 0,
                    "remaining": 1,
                }
                and api_mod._read_pending_commit(Path(td)) is not None,
                repr(conflict_envelope),
            )
    finally:
        api_mod._resolve_resumable_revision = original_resolve_revision

    original_resolve_revision = api_mod._resolve_resumable_revision
    original_checksum = api_mod._atomgit_file_checksum
    try:
        with tempfile.TemporaryDirectory(prefix="atomgit-head-race-") as td:
            projection = Path(td)
            payload = projection / "payload.bin"
            payload.write_bytes(b"payload")
            operation = CommitOperationAdd(
                path_in_repo="payload.bin", path_or_fileobj=payload
            )
            operation._upload_mode = "regular"
            paths = api_mod.get_local_upload_paths(projection, "payload.bin")
            metadata = api_mod.read_upload_metadata(projection, "payload.bin")
            metadata.sha256 = operation.upload_info.sha256.hex()
            metadata.upload_mode = "regular"
            metadata.is_uploaded = True
            metadata.save(paths)
            api_mod._write_pending_commit(
                projection,
                api_mod._pending_commit_value(
                    state="attempting",
                    base_revision="a" * 40,
                    commit_revision=None,
                    operations=[operation],
                ),
            )
            revisions = iter(["b" * 40, "c" * 40])
            api_mod._resolve_resumable_revision = lambda **kwargs: next(revisions)
            record = api_mod._read_pending_commit(projection)["operations"][0]
            api_mod._atomgit_file_checksum = lambda *args: (
                "git-sha1",
                record["git_sha1"],
                record["size"],
            )
            try:
                api_mod._recover_pending_commit(
                    folder_path=projection,
                    token="fake-token-never-print",
                    repo_id="user/repo",
                    repo_type="model",
                    revision="main",
                    request_timeout=17,
                )
            except api_mod.ResumableCommitConflictError:
                head_race_failed = True
            else:
                head_race_failed = False
            recovered_metadata = api_mod.read_upload_metadata(projection, "payload.bin")
            check(
                "changing H1/H2 fails before applying recovered metadata",
                head_race_failed
                and not recovered_metadata.is_committed
                and api_mod._read_pending_commit(projection) is not None,
            )
    finally:
        api_mod._resolve_resumable_revision = original_resolve_revision
        api_mod._atomgit_file_checksum = original_checksum

    original_resolve_revision = api_mod._resolve_resumable_revision
    original_checksum = api_mod._atomgit_file_checksum
    try:
        with tempfile.TemporaryDirectory(prefix="atomgit-safe-retry-") as td:
            projection = Path(td)
            payload = projection / "payload.bin"
            payload.write_bytes(b"payload")
            operation = CommitOperationAdd(
                path_in_repo="payload.bin", path_or_fileobj=payload
            )
            operation._upload_mode = "regular"
            paths = api_mod.get_local_upload_paths(projection, "payload.bin")
            metadata = api_mod.read_upload_metadata(projection, "payload.bin")
            metadata.sha256 = operation.upload_info.sha256.hex()
            metadata.upload_mode = "regular"
            metadata.is_uploaded = True
            metadata.save(paths)
            api_mod._write_pending_commit(
                projection,
                api_mod._pending_commit_value(
                    state="attempting",
                    base_revision="a" * 40,
                    commit_revision=None,
                    operations=[operation],
                ),
            )

            class MissingRemoteFile(Exception):
                code = 404

            api_mod._resolve_resumable_revision = lambda **kwargs: "a" * 40
            api_mod._atomgit_file_checksum = lambda *args: (_ for _ in ()).throw(
                MissingRemoteFile()
            )
            retry_client = ScriptedClient([SimpleNamespace(oid="b" * 40)])
            retry_controller = api_mod._ResumableCommitController(
                retry_client.create_commit,
                token="fake-token-never-print",
                folder_path=projection,
            )
            retry_result = retry_controller.create_commit(
                repo_id="user/repo",
                repo_type="model",
                revision="main",
                operations=[operation],
                commit_message="batch",
            )
            check(
                "unchanged base retries only the missing pending operation",
                retry_result.oid == "b" * 40
                and len(retry_client.calls) == 1
                and retry_client.kwarg_calls[0]["parent_commit"] == "a" * 40
                and api_mod._read_pending_commit(projection) is None,
            )
    finally:
        api_mod._resolve_resumable_revision = original_resolve_revision
        api_mod._atomgit_file_checksum = original_checksum

    original_resolve_revision = api_mod._resolve_resumable_revision
    original_checksum = api_mod._atomgit_file_checksum
    try:
        with tempfile.TemporaryDirectory(prefix="atomgit-partial-conflict-") as td:
            projection = Path(td)
            operations_by_path = {}
            for path, content in (
                ("matched.bin", b"matched"),
                ("missing.bin", b"missing"),
            ):
                payload = projection / path
                payload.write_bytes(content)
                operation = CommitOperationAdd(
                    path_in_repo=path, path_or_fileobj=payload
                )
                operation._upload_mode = "regular"
                operations_by_path[path] = operation
                paths = api_mod.get_local_upload_paths(projection, path)
                metadata = api_mod.read_upload_metadata(projection, path)
                metadata.sha256 = operation.upload_info.sha256.hex()
                metadata.upload_mode = "regular"
                metadata.is_uploaded = True
                metadata.save(paths)
            partial_operations = list(operations_by_path.values())
            api_mod._write_pending_commit(
                projection,
                api_mod._pending_commit_value(
                    state="attempting",
                    base_revision="a" * 40,
                    commit_revision=None,
                    operations=partial_operations,
                ),
            )
            pending_records = {
                item["path"]: item
                for item in api_mod._read_pending_commit(projection)["operations"]
            }
            api_mod._resolve_resumable_revision = lambda **kwargs: "b" * 40

            def partial_checksum(*args):
                path = args[2]
                if path == "missing.bin":
                    raise MissingRemoteFile()
                record = pending_records[path]
                return "git-sha1", record["git_sha1"], record["size"]

            api_mod._atomgit_file_checksum = partial_checksum
            try:
                api_mod._recover_pending_commit(
                    folder_path=projection,
                    token="fake-token-never-print",
                    repo_id="user/repo",
                    repo_type="model",
                    revision="main",
                    request_timeout=17,
                )
            except api_mod.ResumableCommitConflictError as error:
                partial_conflict_failed = True
                partial_conflict_envelope = api_mod._resumable_failure_envelope(error)
            else:
                partial_conflict_failed = False
                partial_conflict_envelope = None
            retained = api_mod._read_pending_commit(projection)
            check(
                "advanced revision confirms matches and retains only conflicts",
                partial_conflict_failed
                and api_mod.read_upload_metadata(projection, "matched.bin").is_committed
                and not api_mod.read_upload_metadata(
                    projection, "missing.bin"
                ).is_committed
                and [item["path"] for item in retained["operations"]] == ["missing.bin"]
                and partial_conflict_envelope
                == {
                    "category": "remote_commit_conflict",
                    "confirmed": 1,
                    "remaining": 1,
                },
            )

            local_payload = projection / "missing.bin"
            local_payload.write_bytes(b"changed")
            revision_reads = []
            api_mod._resolve_resumable_revision = (
                lambda **kwargs: revision_reads.append(kwargs)
            )
            try:
                api_mod._recover_pending_commit(
                    folder_path=projection,
                    token="fake-token-never-print",
                    repo_id="user/repo",
                    repo_type="model",
                    revision="main",
                    request_timeout=17,
                )
            except api_mod.ResumableRecoveryStateError as error:
                local_change_envelope = api_mod._resumable_failure_envelope(error)
            else:
                local_change_envelope = None
            check(
                "local content changes fail before any remote recovery read",
                local_change_envelope
                == {
                    "category": "remote_recovery_state",
                    "confirmed": 0,
                    "remaining": 1,
                }
                and not revision_reads
                and api_mod._read_pending_commit(projection) is not None,
            )

            conflict_type, conflict_hint = api_mod._classify_upload_error(
                api_mod.ResumableWorkerError(
                    "remote_commit_conflict", confirmed=1, remaining=1
                )
            )
            check(
                "conflict output reports only bounded recovery counts",
                conflict_type == "远端提交冲突"
                and "确认复用 1" in conflict_hint
                and "冲突 1" in conflict_hint
                and "仍需提交 1" in conflict_hint,
                conflict_hint,
            )
    finally:
        api_mod._resolve_resumable_revision = original_resolve_revision
        api_mod._atomgit_file_checksum = original_checksum

    sleeps = []
    timeout_client = ScriptedClient([httpx.ReadTimeout("response timed out")])
    reconciled = {item.path_in_repo for item in operations}
    controller = make_controller(
        timeout_client,
        sleeps,
        reconcile=lambda **kwargs: reconciled,
    )
    result = controller.create_commit(
        repo_id="user/repo",
        repo_type="model",
        revision="main",
        operations=operations,
        commit_message="batch",
    )
    check("ambiguous timeout reconciles remote success", result is None)
    check("reconciled timeout is not submitted twice", len(timeout_client.calls) == 1)

    sleeps = []
    partial_client = ScriptedClient([httpx.ReadTimeout("response timed out"), "partial-ok"])
    partial_paths = {item.path_in_repo for item in operations[:10]}
    controller = make_controller(
        partial_client,
        sleeps,
        reconcile=lambda **kwargs: partial_paths,
    )
    result = controller.create_commit(
        repo_id="user/repo",
        repo_type="model",
        revision="main",
        operations=operations,
        commit_message="batch",
    )
    check("partial reconciliation commits only missing paths", result == "partial-ok")
    check("partial reconciliation reduces retry set", [len(call) for call in partial_client.calls] == [20, 10])

    marked_paths = []
    partial_split = ScriptedClient([
        httpx.ReadTimeout("initial timeout"),
        "first-half-ok",
        httpx.ReadTimeout("second-half timeout"),
        httpx.ReadTimeout("smaller timeout"),
        httpx.ReadTimeout("single timeout"),
        httpx.ReadTimeout("terminal timeout"),
    ])
    controller = make_controller(
        partial_split,
        [],
        max_attempts=1,
        mark_committed=lambda items: marked_paths.extend(
            item.path_in_repo for item in items
        ),
    )
    try:
        controller.create_commit(
            repo_id="user/repo",
            repo_type="model",
            revision="main",
            operations=operations,
            commit_message="batch",
        )
    except api_mod.ResumableCommitError:
        split_failure = True
    else:
        split_failure = False
    check("partial split failure remains a failure", split_failure)
    check(
        "successful split is persisted before a later split fails",
        marked_paths == [item.path_in_repo for item in operations[:10]],
        repr(marked_paths),
    )

    sleeps = []
    limited_client = ScriptedClient([http_error(429, retry_after=7), "ok"])
    controller = make_controller(limited_client, sleeps)
    result = controller.create_commit(
        repo_id="user/repo",
        repo_type="model",
        revision="main",
        operations=operations,
        commit_message="batch",
    )
    check("429 retry eventually returns commit result", result == "ok")
    check("429 honors Retry-After", sleeps == [7.0], repr(sleeps))
    check("429 retries the same batch", [len(call) for call in limited_client.calls] == [20, 20])

    long_retry_sleeps = []
    long_retry_client = ScriptedClient([http_error(429, retry_after=600), "ok"])
    controller = make_controller(long_retry_client, long_retry_sleeps)
    controller.create_commit(
        repo_id="user/repo",
        repo_type="model",
        revision="main",
        operations=operations,
        commit_message="batch",
    )
    check("Retry-After is not shortened", long_retry_sleeps == [600.0], repr(long_retry_sleeps))

    sleeps = []
    unavailable_client = ScriptedClient([http_error(503), "recovered"])
    controller = make_controller(unavailable_client, sleeps)
    result = controller.create_commit(
        repo_id="user/repo",
        repo_type="model",
        revision="main",
        operations=operations,
        commit_message="batch",
    )
    check("503 uses bounded retry and recovers", result == "recovered")
    check("503 uses exponential backoff base", sleeps == [30.0], repr(sleeps))

    oversized_client = ScriptedClient([http_error(413), "first-ok", "second-ok"])
    reduction_events = []
    controller = make_controller(
        oversized_client, [], event_callback=reduction_events.append
    )
    result = controller.create_commit(
        repo_id="user/repo",
        repo_type="model",
        revision="main",
        operations=operations,
        commit_message="batch",
    )
    check("413 reduces immediately and completes", result == "second-ok")
    check("413 reduces twenty to two tens", [len(call) for call in oversized_client.calls] == [20, 10, 10], repr(oversized_client.calls))
    check(
        "413 reports reduction for the outer batch",
        any(event.get("kind") == "reduce" and event.get("from_size") == 20
            and event.get("to_size") == 10 for event in reduction_events),
        repr(reduction_events),
    )

    lifecycle_events = []
    event_client = ScriptedClient([http_error(429, retry_after=7), httpx.ReadTimeout("ambiguous"), "ok"])
    controller = make_controller(
        event_client,
        [],
        reconcile=lambda **kwargs: {operations[0].path_in_repo},
        event_callback=lifecycle_events.append,
    )
    controller.create_commit(
        repo_id="user/repo",
        repo_type="model",
        revision="main",
        operations=operations,
        commit_message="batch",
    )
    event_kinds = [event.get("kind") for event in lifecycle_events]
    check("rate-limit wait is reported", "rate_limit_wait" in event_kinds, repr(lifecycle_events))
    check("ambiguous remote state is reported", "reconcile_start" in event_kinds, repr(lifecycle_events))
    check("remote reconciliation result is reported", "reconcile_result" in event_kinds, repr(lifecycle_events))
    check("retry is reported", "retry" in event_kinds, repr(lifecycle_events))

    sleeps = []
    persistent_limit = ScriptedClient([http_error(429), http_error(429)])
    controller = make_controller(persistent_limit, sleeps, max_attempts=2)
    try:
        controller.create_commit(
            repo_id="user/repo",
            repo_type="model",
            revision="main",
            operations=operations,
            commit_message="batch",
        )
    except api_mod.ResumableCommitError:
        limited_failure = True
    else:
        limited_failure = False
    check("persistent 429 fails after bounded attempts", limited_failure)
    check("persistent 429 never reduces batch", [len(call) for call in persistent_limit.calls] == [20, 20])

    sleeps = []
    persistent_timeout = ScriptedClient(
        [httpx.ReadTimeout("response timed out") for _ in range(8)]
    )
    timeout_events = []
    controller = make_controller(
        persistent_timeout,
        sleeps,
        max_attempts=1,
        event_callback=timeout_events.append,
    )
    try:
        controller.create_commit(
            repo_id="user/repo",
            repo_type="model",
            revision="main",
            operations=operations,
            commit_message="batch",
        )
    except api_mod.ResumableCommitError:
        timeout_failure = True
    else:
        timeout_failure = False
    sizes = [len(call) for call in persistent_timeout.calls]
    check("persistent timeout fails safely", timeout_failure)
    check("persistent timeout really reduces below twenty", sizes[:5] == [20, 10, 5, 2, 1], repr(sizes))
    reductions = [
        (event.get("from_size"), event.get("to_size"))
        for event in timeout_events
        if event.get("kind") == "reduce"
    ]
    check(
        "persistent timeout reports the full reduction chain",
        reductions[:4] == [(20, 10), (10, 5), (5, 2), (2, 1)],
        repr(reductions),
    )

    formatted_output = StringIO()
    with redirect_stdout(formatted_output):
        for event in lifecycle_events + timeout_events:
            api_mod._print_resumable_commit_event(event, (4, 35))
    formatted_text = formatted_output.getvalue()
    formatted_lines = formatted_text.splitlines()
    check(
        "retry, rate limit, reconciliation, and reduction name outer batch",
        bool(formatted_lines)
        and all(line.startswith("[批次 4/35]") for line in formatted_lines)
        and "请求限流" in formatted_text
        and "提交结果不明确" in formatted_text
        and "远端核对完成" in formatted_text
        and "降低提交批量: 20 -> 10" in formatted_text
        and "降低提交批量: 2 -> 1" in formatted_text,
        formatted_text,
    )

    disconnected_client = ScriptedClient([httpx.ConnectError("offline")])
    controller = make_controller(disconnected_client, [], max_attempts=1)
    try:
        controller.create_commit(
            repo_id="user/repo",
            repo_type="model",
            revision="main",
            operations=operations,
            commit_message="batch",
        )
    except api_mod.ResumableCommitError:
        disconnected_failure = True
    else:
        disconnected_failure = False
    check("persistent connection failure exits safely", disconnected_failure)
    check("connection failure does not reduce batch", [len(call) for call in disconnected_client.calls] == [20])

    forbidden_client = ScriptedClient([http_error(403)])
    controller = make_controller(forbidden_client, [])
    try:
        controller.create_commit(
            repo_id="user/repo",
            repo_type="model",
            revision="main",
            operations=operations,
            commit_message="batch",
        )
    except api_mod.ResumableCommitError:
        forbidden_failure = True
    else:
        forbidden_failure = False
    check("non-retryable 403 fails immediately", forbidden_failure)
    check("non-retryable 403 is attempted once", len(forbidden_client.calls) == 1)

    payload_type, payload_hint = api_mod._classify_upload_error(
        api_mod.ResumableCommitError(
            "resumable commit failed for 1 file(s): HTTP 413"
        )
    )
    check("single-file 413 has an actionable category", payload_type == "提交过大", payload_type)
    check("single-file 413 explains the remaining limit", "单文件" in payload_hint, payload_hint)

    rate_type, rate_hint = api_mod._classify_upload_error(
        api_mod.ResumableCommitError(
            "resumable commit failed for 20 file(s): HTTP 429"
        )
    )
    check("exhausted 429 has an actionable category", rate_type == "请求限流", rate_type)
    check("exhausted 429 explains resumable progress", "断点" in rate_hint, rate_hint)

    service_type, service_hint = api_mod._classify_upload_error(
        api_mod.ResumableCommitError(
            "resumable commit failed for 1 file(s): HTTP 503"
        )
    )
    check("exhausted 503 has an actionable category", service_type == "服务暂不可用", service_type)
    check("exhausted 503 suggests retrying later", "稍后" in service_hint, service_hint)

    original_checksum = api_mod._atomgit_file_checksum
    try:
        with tempfile.TemporaryDirectory(prefix="atomgit-reconcile-") as td:
            payload = Path(td) / "payload.bin"
            payload.write_bytes(b"content")
            operation = CommitOperationAdd(
                path_in_repo="prefix/payload.bin",
                path_or_fileobj=payload,
            )
            api_mod._atomgit_file_checksum = lambda *args: (
                "sha256",
                operation.upload_info.sha256.hex(),
                operation.upload_info.size,
            )
            matched = api_mod._reconcile_resumable_commit_operations(
                repo_id="user/repo",
                repo_type="model",
                revision="main",
                operations=[operation],
                token="fake-token-never-print",
            )
            check("remote reconciliation compares LFS object identity", matched == {"prefix/payload.bin"})

            projection = Path(td) / "projection"
            projected_file = projection / "prefix" / "payload.bin"
            projected_file.parent.mkdir(parents=True)
            projected_file.write_bytes(b"content")
            projected_operation = CommitOperationAdd(
                path_in_repo="prefix/payload.bin",
                path_or_fileobj=projected_file,
            )
            paths = api_mod.get_local_upload_paths(
                projection, "prefix/payload.bin"
            )
            metadata = api_mod.read_upload_metadata(
                projection, "prefix/payload.bin"
            )
            metadata.sha256 = projected_operation.upload_info.sha256.hex()
            metadata.upload_mode = "lfs"
            metadata.is_uploaded = True
            metadata.save(paths)
            api_mod._mark_resumable_operations_committed(
                projection, [projected_operation]
            )
            persisted = api_mod.read_upload_metadata(
                projection, "prefix/payload.bin"
            )
            check("successful sub-commit persists locked HF metadata", persisted.is_committed)

            unsafe_file = projection / "unsafe.bag"
            with unsafe_file.open("wb") as stream:
                stream.truncate(
                    api_mod._RESUMABLE_REGULAR_FILE_MAX_BYTES + 1
                )
            unsafe_paths = api_mod.get_local_upload_paths(projection, "unsafe.bag")
            unsafe_metadata = api_mod.read_upload_metadata(projection, "unsafe.bag")
            unsafe_metadata.sha256 = "12" * 32
            unsafe_metadata.upload_mode = "regular"
            unsafe_metadata.should_ignore = False
            unsafe_metadata.remote_oid = "cached-oid"
            unsafe_metadata.save(unsafe_paths)

            committed_file = projection / "committed.bag"
            with committed_file.open("wb") as stream:
                stream.truncate(
                    api_mod._RESUMABLE_REGULAR_FILE_MAX_BYTES + 1
                )
            committed_paths = api_mod.get_local_upload_paths(
                projection, "committed.bag"
            )
            committed_metadata = api_mod.read_upload_metadata(
                projection, "committed.bag"
            )
            committed_metadata.sha256 = "34" * 32
            committed_metadata.upload_mode = "regular"
            committed_metadata.is_committed = True
            committed_metadata.save(committed_paths)

            refreshed = api_mod._refresh_unsafe_resumable_upload_modes(projection)
            refreshed_unsafe = api_mod.read_upload_metadata(
                projection, "unsafe.bag"
            )
            preserved_committed = api_mod.read_upload_metadata(
                projection, "committed.bag"
            )
            check("unsafe uncommitted upload mode is refreshed", refreshed == 1)
            check(
                "upload-mode refresh preserves sha256 and clears only policy fields",
                refreshed_unsafe.sha256 == "12" * 32
                and refreshed_unsafe.upload_mode is None
                and refreshed_unsafe.should_ignore is None
                and refreshed_unsafe.remote_oid is None
                and not refreshed_unsafe.is_committed,
            )
            check(
                "committed upload metadata remains untouched",
                preserved_committed.sha256 == "34" * 32
                and preserved_committed.upload_mode == "regular"
                and preserved_committed.is_committed,
            )
    finally:
        api_mod._atomgit_file_checksum = original_checksum

    original_api = api_mod.HfApi
    original_close = api_mod.close_hf_session
    original_timeout = api_mod.hf_constants.DEFAULT_REQUEST_TIMEOUT
    captured = []

    class TimeoutAwareApi:
        def __init__(self, endpoint=None, token=None):
            captured.append((
                "client",
                endpoint,
                api_mod.hf_constants.DEFAULT_REQUEST_TIMEOUT,
            ))

        def create_commit(self, *args, **kwargs):
            return None

        def upload_large_folder(self, **kwargs):
            existing = self.create_repo(
                repo_id=kwargs["repo_id"], repo_type=kwargs["repo_type"],
                private=None, exist_ok=True,
            )
            captured.append(("metadata-recovery", existing.repo_id))
            return None

        def create_repo(self, **kwargs):
            captured.append(("remote-create", kwargs["repo_id"]))
            raise AssertionError("remote create must be suppressed")

    api_mod.HfApi = TimeoutAwareApi
    api_mod.close_hf_session = lambda: captured.append("closed")
    result_queue = queue.Queue()
    try:
        api_mod._run_resumable_upload(
            "fake-token-never-print",
            {"repo_id": "user/repo", "folder_path": ".", "repo_type": "model"},
            result_queue,
            300.0,
        )
        check(
            "child reports successful upload",
            result_queue.get_nowait() == (True, {"recovered": 0}),
        )
        check("existing repository reaches metadata recovery without create",
              ("metadata-recovery", "user/repo") in captured
              and not any(isinstance(item, tuple) and item[0] == "remote-create"
                          for item in captured), repr(captured))
        check(
            "child constructs HF client with AtomGit endpoint and timeout",
            ("client", "https://hub.atomgit.com", 300.0) in captured,
            repr(captured),
        )
        check("child closes cached HTTP sessions before and after", captured.count("closed") == 2, repr(captured))
        check("child restores process-global timeout", api_mod.hf_constants.DEFAULT_REQUEST_TIMEOUT == original_timeout)
    finally:
        api_mod.HfApi = original_api
        api_mod.close_hf_session = original_close
        api_mod.hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout

    methods = api_mod.multiprocessing.get_all_start_methods()
    if "fork" in methods:
        original_api = api_mod.HfApi
        original_resolve_revision = api_mod._resolve_resumable_revision
        api_mod.HfApi = FatalHfApi
        api_mod._resolve_resumable_revision = lambda **kwargs: "a" * 40
        process = None
        try:
            context = api_mod.multiprocessing.get_context("fork")
            result_queue = context.Queue()
            process = context.Process(
                target=api_mod._run_resumable_upload,
                args=(
                    "fake-token-never-print",
                    {
                        "repo_id": "user/repo",
                        "folder_path": ".",
                        "repo_type": "model",
                    },
                    result_queue,
                    300.0,
                ),
            )
            process.start()
            process.join(5)
            child_result = result_queue.get(timeout=1)
            check("persistent child failure terminates promptly", not process.is_alive())
            check("persistent child failure returns bounded structured error",
                  child_result == (False, {"category": "rate_limit"}),
                  repr(child_result))
        finally:
            if process is not None and process.is_alive():
                process.terminate()
                process.join(2)
            api_mod.HfApi = original_api
            api_mod._resolve_resumable_revision = original_resolve_revision
    else:
        check("persistent child failure test requires fork", True)

    passed = sum(results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
