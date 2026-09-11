#!/usr/bin/env python3
"""Offline exact-byte contracts for canonical AtomGit LFS pointers."""

import base64
import hashlib
import json
import shutil
import subprocess
import tempfile
import urllib.error
from pathlib import Path
from types import SimpleNamespace

import httpx
import huggingface_hub.hf_api as hf_api
from huggingface_hub._commit_api import CommitOperationAdd

import atomgit  # noqa: F401
import atomgit.lfs_pointer as pointer_mod
import atomgit_hub as sdk_mod
from atomgit.lfs_pointer import (
    CanonicalLfsPointerError,
    canonical_lfs_payloads,
    canonical_lfs_pointer,
    run_canonical_lfs_upload,
    verify_canonical_lfs_pointers,
)


api_mod = __import__("sys").modules["atomgit.api"]


results = []


def check(name, condition, detail=""):
    results.append(bool(condition))
    print(
        f"[{'PASS' if condition else 'FAIL'}] {name}"
        + (f" -> {detail}" if detail else "")
    )


def main():
    content = b"canonical pointer fixture"
    oid = hashlib.sha256(content).hexdigest()
    expected = (
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{oid}\n"
        f"size {len(content)}\n"
    ).encode("ascii")

    pointer = canonical_lfs_pointer(oid, len(content))
    check("serializer emits exact canonical bytes", pointer == expected)
    check(
        "serializer ends in exactly one LF",
        pointer.endswith(b"\n") and not pointer.endswith(b"\n\n"),
    )

    git_lfs = shutil.which("git-lfs")
    if git_lfs is None:
        check(
            "git-lfs strict integration when available",
            True,
            "git-lfs is not installed",
        )
    else:
        with tempfile.TemporaryDirectory(prefix="atomgit-lfs-pointer-") as temp_name:
            canonical_path = Path(temp_name) / "canonical.pointer"
            missing_lf_path = Path(temp_name) / "missing-lf.pointer"
            canonical_path.write_bytes(pointer)
            missing_lf_path.write_bytes(pointer[:-1])
            canonical_check = subprocess.run(
                [git_lfs, "pointer", "--check", "--strict", "--file", str(canonical_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            missing_lf_check = subprocess.run(
                [git_lfs, "pointer", "--check", "--strict", "--file", str(missing_lf_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        check(
            "git-lfs strict accepts canonical and rejects missing final LF",
            canonical_check.returncode == 0 and missing_lf_check.returncode != 0,
            "canonical={} missing_lf={}".format(
                canonical_check.returncode, missing_lf_check.returncode
            ),
        )

    invalid_values = (
        ("A" * 64, len(content)),
        ("0" * 63, len(content)),
        ("g" * 64, len(content)),
        (oid, -1),
        (oid, True),
    )
    rejected = 0
    for invalid_oid, invalid_size in invalid_values:
        try:
            canonical_lfs_pointer(invalid_oid, invalid_size)
        except CanonicalLfsPointerError:
            rejected += 1
    check(
        "serializer rejects malformed OID and size metadata",
        rejected == len(invalid_values),
        f"rejected={rejected}/{len(invalid_values)}",
    )

    operation = CommitOperationAdd(
        path_in_repo="nested/fixture.bin",
        path_or_fileobj=content,
    )
    operation._upload_mode = "lfs"
    with canonical_lfs_payloads() as expectations:
        payload = list(
            hf_api._prepare_commit_payload(
                operations=[operation],
                files_to_copy={},
                commit_message="test canonical pointer",
            )
        )

    check("payload retains one header and one operation", len(payload) == 2)
    item = payload[1] if len(payload) == 2 else {}
    check("lfsFile is replaced by an exact regular file", item.get("key") == "file")
    value = item.get("value", {})
    decoded = base64.b64decode(value.get("content", ""))
    check("replacement path is unchanged", value.get("path") == "nested/fixture.bin")
    check("replacement encoding is base64", value.get("encoding") == "base64")
    check("replacement bytes are canonical", decoded == expected)
    check(
        "expected pointer metadata is recorded for verification",
        len(expectations) == 1
        and expectations[0].path_in_repo == "nested/fixture.bin"
        and expectations[0].oid == oid
        and expectations[0].size == len(content)
        and expectations[0].content == expected,
    )

    outside_operation = CommitOperationAdd(
        path_in_repo="outside.bin",
        path_or_fileobj=content,
    )
    outside_operation._upload_mode = "lfs"
    outside_payload = list(
        hf_api._prepare_commit_payload(
            operations=[outside_operation],
            files_to_copy={},
            commit_message="outside AtomGit context",
        )
    )
    check(
        "payload outside AtomGit context preserves locked HF behavior",
        outside_payload[1].get("key") == "lfsFile",
    )

    class FakeResponse:
        def __init__(self, raw):
            self.payload = json.dumps(
                {
                    "content": base64.b64encode(raw).decode("ascii"),
                    "encoding": "base64",
                }
            ).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self, size):
            return self.payload

    original_open = pointer_mod._open_atomgit_url
    original_sleep = pointer_mod.time.sleep
    opened = []

    def exact_open(request, timeout):
        opened.append((request, timeout))
        return FakeResponse(expected)

    pointer_mod._open_atomgit_url = exact_open
    try:
        verify_canonical_lfs_pointers(
            token="fake-pointer-token",
            repo_id="owner/nested/repo",
            revision="a" * 40,
            expectations=expectations,
            timeout=9,
        )
    except Exception as error:
        verification_passed = False
        verification_detail = type(error).__name__
    else:
        verification_passed = True
        verification_detail = ""
    check("exact raw pointer verification succeeds", verification_passed, verification_detail)
    request, timeout = opened[0]
    check(
        "verification uses encoded repository, path, and exact revision",
        "/repos/owner/nested%2Frepo/contents/nested/fixture.bin" in request.full_url
        and "ref=" + ("a" * 40) in request.full_url
        and timeout == 9,
    )
    check(
        "verification authenticates without putting token in the URL",
        request.get_header("Private-token") == "fake-pointer-token"
        and "fake-pointer-token" not in request.full_url,
    )

    opened.clear()
    verify_canonical_lfs_pointers(
        token="fake-pointer-token",
        repo_id="owner/repo",
        revision="main",
        expectations=expectations,
    )
    check(
        "verification defaults to the project request timeout",
        opened[0][1] == 300.0,
        f"timeout={opened[0][1]}",
    )

    retry_outcomes = [
        urllib.error.URLError("temporary pointer read failure"),
        FakeResponse(expected),
    ]
    retry_sleeps = []

    def recover_on_second_read(request, timeout):
        opened.append((request, timeout))
        outcome = retry_outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    opened.clear()
    pointer_mod._open_atomgit_url = recover_on_second_read
    pointer_mod.time.sleep = retry_sleeps.append
    try:
        verify_canonical_lfs_pointers(
            token="fake-pointer-token",
            repo_id="owner/repo",
            revision="main",
            expectations=expectations,
            timeout=9,
        )
    except CanonicalLfsPointerError:
        transient_read_recovered = False
    else:
        transient_read_recovered = True
    check(
        "pointer verification retries a transient read failure",
        transient_read_recovered
        and len(opened) == 2
        and all(timeout == 9 for _, timeout in opened),
        f"recovered={transient_read_recovered} calls={len(opened)}",
    )
    check("first retry waits two seconds", retry_sleeps == [2.0], repr(retry_sleeps))

    malformed_response = FakeResponse(expected)
    malformed_response.payload = b"not-json"
    retry_outcomes[:] = [
        malformed_response,
        urllib.error.URLError("second temporary failure"),
        FakeResponse(expected),
    ]
    opened.clear()
    retry_sleeps.clear()
    verify_canonical_lfs_pointers(
        token="fake-pointer-token",
        repo_id="owner/repo",
        revision="main",
        expectations=expectations,
        timeout=11,
    )
    check(
        "pointer verification recovers on the third read",
        len(opened) == 3
        and all(timeout == 11 for _, timeout in opened)
        and retry_sleeps == [2.0, 4.0],
        f"calls={len(opened)} sleeps={retry_sleeps!r}",
    )

    retry_outcomes[:] = [FakeResponse(expected[:-1]), FakeResponse(expected)]
    opened.clear()
    retry_sleeps.clear()
    verify_canonical_lfs_pointers(
        token="fake-pointer-token",
        repo_id="owner/repo",
        revision="main",
        expectations=expectations,
    )
    check(
        "temporary pointer mismatch is retried",
        len(opened) == 2 and retry_sleeps == [2.0],
        f"calls={len(opened)} sleeps={retry_sleeps!r}",
    )

    second_content = b"second canonical pointer fixture"
    second_oid = hashlib.sha256(second_content).hexdigest()
    second_pointer = canonical_lfs_pointer(second_oid, len(second_content))
    second_expectation = pointer_mod.CanonicalLfsPointer(
        path_in_repo="nested/second.bin",
        oid=second_oid,
        size=len(second_content),
        content=second_pointer,
    )
    path_reads = {"nested/fixture.bin": 0, "nested/second.bin": 0}

    def multi_pointer_open(request, timeout):
        path = (
            "nested/second.bin"
            if "nested/second.bin" in request.full_url
            else "nested/fixture.bin"
        )
        path_reads[path] += 1
        if path == "nested/second.bin" and path_reads[path] == 1:
            return FakeResponse(expected)
        return FakeResponse(second_pointer if path == "nested/second.bin" else expected)

    pointer_mod._open_atomgit_url = multi_pointer_open
    retry_sleeps.clear()
    verify_canonical_lfs_pointers(
        token="fake-pointer-token",
        repo_id="owner/repo",
        revision="main",
        expectations=[expectations[0], second_expectation],
    )
    check(
        "retrying one pointer does not reread an already confirmed pointer",
        path_reads == {"nested/fixture.bin": 1, "nested/second.bin": 2}
        and retry_sleeps == [2.0],
        f"reads={path_reads!r} sleeps={retry_sleeps!r}",
    )

    mismatch_reads = []

    def mismatched_open(request, timeout):
        mismatch_reads.append((request, timeout))
        return FakeResponse(expected[:-1])

    pointer_mod._open_atomgit_url = mismatched_open
    retry_sleeps.clear()
    try:
        verify_canonical_lfs_pointers(
            token="fake-pointer-token",
            repo_id="owner/repo",
            revision="main",
            expectations=expectations,
        )
    except CanonicalLfsPointerError as error:
        missing_lf_rejected = (
            "noncanonical" in str(error)
            and "fake-pointer-token" not in str(error)
        )
    else:
        missing_lf_rejected = False
    check(
        "verification rejects a pointer missing its final LF after three reads",
        missing_lf_rejected
        and len(mismatch_reads) == 3
        and retry_sleeps == [2.0, 4.0],
        f"calls={len(mismatch_reads)} sleeps={retry_sleeps!r}",
    )

    failed_reads = []
    def failing_open(request, timeout):
        failed_reads.append((request, timeout))
        raise urllib.error.HTTPError(
            "https://api.atomgit.com/private/repository/path?ref=fake-secret-ref",
            404,
            "Not Found fake-secret-body",
            {},
            None,
        )

    pointer_mod._open_atomgit_url = failing_open
    retry_sleeps.clear()
    try:
        verify_canonical_lfs_pointers(
            token="fake-pointer-token",
            repo_id="owner/repo",
            revision="main",
            expectations=expectations,
        )
    except CanonicalLfsPointerError as error:
        verification_fetch_error = error
    else:
        verification_fetch_error = None
    fetch_kind, fetch_hint = api_mod._classify_upload_error(
        verification_fetch_error or RuntimeError("verification unexpectedly passed")
    )
    fetch_envelope = api_mod._resumable_failure_envelope(
        verification_fetch_error or RuntimeError("verification unexpectedly passed")
    )
    fetch_sdk_error = sdk_mod._sdk_error(
        verification_fetch_error or RuntimeError("verification unexpectedly passed"),
        "上传目录",
        "owner/repo",
    )
    safe_rendered_error = str(verification_fetch_error)
    check(
        "verification transport failures use the pointer contract",
        isinstance(verification_fetch_error, CanonicalLfsPointerError)
        and fetch_kind == "LFS 指针验证失败"
        and fetch_envelope == {"category": "lfs_pointer"}
        and "Git LFS pointer 验证失败" in str(fetch_sdk_error),
    )
    check(
        "verification transport retries are bounded",
        len(failed_reads) == 3 and retry_sleeps == [2.0, 4.0],
        f"calls={len(failed_reads)} sleeps={retry_sleeps!r}",
    )
    check(
        "verification transport failure is credential-safe",
        "fake-secret-ref" not in safe_rendered_error
        and "fake-secret-body" not in safe_rendered_error
        and "fake-pointer-token" not in safe_rendered_error
        and "fake-secret-ref" not in fetch_hint,
    )

    def response_with_payload(payload):
        response = FakeResponse(expected)
        response.payload = payload
        return response

    reason_cases = (
        (
            "authentication_failed",
            lambda: urllib.error.HTTPError(
                "https://secret.invalid", 401, "secret", {}, None
            ),
        ),
        (
            "permission_denied",
            lambda: urllib.error.HTTPError(
                "https://secret.invalid", 403, "secret", {}, None
            ),
        ),
        (
            "pointer_unavailable",
            lambda: urllib.error.HTTPError(
                "https://secret.invalid", 404, "secret", {}, None
            ),
        ),
        (
            "rate_limited",
            lambda: urllib.error.HTTPError(
                "https://secret.invalid", 429, "secret", {}, None
            ),
        ),
        (
            "service_unavailable",
            lambda: urllib.error.HTTPError(
                "https://secret.invalid", 503, "secret", {}, None
            ),
        ),
        ("request_timeout", lambda: TimeoutError("fake-secret-timeout")),
        (
            "connection_failed",
            lambda: urllib.error.URLError(ConnectionResetError("fake-secret-reset")),
        ),
        (
            "request_rejected",
            lambda: urllib.error.HTTPError(
                "https://secret.invalid", 302, "secret", {}, None
            ),
        ),
        (
            "response_too_large",
            lambda: response_with_payload(b"x" * (64 * 1024 + 1)),
        ),
        (
            "response_malformed",
            lambda: response_with_payload(b"fake-secret-invalid-json"),
        ),
        ("content_mismatch", lambda: FakeResponse(expected[:-1])),
        ("unknown_read_failure", lambda: RuntimeError("fake-secret-unknown")),
    )
    classified_reasons = []
    for expected_reason, outcome_factory in reason_cases:
        reason_reads = []

        def classified_open(request, timeout):
            reason_reads.append((request, timeout))
            outcome = outcome_factory()
            if isinstance(outcome, BaseException):
                raise outcome
            return outcome

        pointer_mod._open_atomgit_url = classified_open
        retry_sleeps.clear()
        try:
            verify_canonical_lfs_pointers(
                token="fake-pointer-token",
                repo_id="owner/repo",
                revision="main",
                expectations=expectations,
                timeout=13,
            )
        except CanonicalLfsPointerError as error:
            classified_reasons.append(getattr(error, "confirmation_failure", None))
            rendered = str(error)
        else:
            classified_reasons.append(None)
            rendered = ""
        check(
            f"pointer failure is classified as {expected_reason}",
            classified_reasons[-1] == expected_reason
            and len(reason_reads) == 3
            and retry_sleeps == [2.0, 4.0]
            and "fake-secret" not in rendered
            and "secret.invalid" not in rendered,
            repr((classified_reasons[-1], len(reason_reads), retry_sleeps)),
        )
    check(
        "pointer failure reasons use the exact accepted whitelist",
        set(classified_reasons) == {reason for reason, _ in reason_cases},
        repr(classified_reasons),
    )

    def malformed_status_open(request, timeout):
        raise urllib.error.HTTPError("https://secret.invalid", None, "secret", {}, None)

    pointer_mod._open_atomgit_url = malformed_status_open
    retry_sleeps.clear()
    try:
        verify_canonical_lfs_pointers(
            token="fake-pointer-token",
            repo_id="owner/repo",
            revision="main",
            expectations=expectations,
        )
    except CanonicalLfsPointerError as error:
        malformed_status_reason = error.confirmation_failure
    else:
        malformed_status_reason = None
    check(
        "malformed HTTP status safely uses request_rejected",
        malformed_status_reason == "request_rejected" and retry_sleeps == [2.0, 4.0],
    )

    mixed_outcomes = [
        urllib.error.HTTPError("https://secret.invalid", 401, "secret", {}, None),
        TimeoutError("fake-secret-timeout"),
        FakeResponse(expected[:-1]),
    ]

    def mixed_failure_open(request, timeout):
        outcome = mixed_outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    pointer_mod._open_atomgit_url = mixed_failure_open
    retry_sleeps.clear()
    try:
        verify_canonical_lfs_pointers(
            token="fake-pointer-token",
            repo_id="owner/repo",
            revision="main",
            expectations=expectations,
        )
    except CanonicalLfsPointerError as error:
        mixed_failure_reason = getattr(error, "confirmation_failure", None)
    else:
        mixed_failure_reason = None
    check(
        "mixed retries report only the final failure reason",
        mixed_failure_reason == "content_mismatch" and retry_sleeps == [2.0, 4.0],
        repr((mixed_failure_reason, retry_sleeps)),
    )

    validation_reads = []
    pointer_mod._open_atomgit_url = lambda request, timeout: validation_reads.append(
        (request, timeout)
    )
    invalid_inputs = (
        {"token": ""},
        {"repo_id": "invalid"},
        {"revision": ""},
        {"timeout": 0},
        {"timeout": True},
    )
    invalid_rejected = 0
    retry_sleeps.clear()
    for changes in invalid_inputs:
        arguments = {
            "token": "fake-pointer-token",
            "repo_id": "owner/repo",
            "revision": "main",
            "expectations": expectations,
            "timeout": 9,
        }
        arguments.update(changes)
        try:
            verify_canonical_lfs_pointers(**arguments)
        except CanonicalLfsPointerError:
            invalid_rejected += 1
    check(
        "invalid verification inputs fail before reads or waits",
        invalid_rejected == len(invalid_inputs)
        and not validation_reads
        and not retry_sleeps,
        f"rejected={invalid_rejected} reads={len(validation_reads)}",
    )

    interrupted_reads = []

    def interrupting_open(request, timeout):
        interrupted_reads.append((request, timeout))
        raise KeyboardInterrupt

    pointer_mod._open_atomgit_url = interrupting_open
    retry_sleeps.clear()
    try:
        verify_canonical_lfs_pointers(
            token="fake-pointer-token",
            repo_id="owner/repo",
            revision="main",
            expectations=expectations,
        )
    except KeyboardInterrupt:
        read_interrupt_propagated = True
    else:
        read_interrupt_propagated = False
    check(
        "read interruption propagates without retry",
        read_interrupt_propagated
        and len(interrupted_reads) == 1
        and not retry_sleeps,
    )

    pointer_mod._open_atomgit_url = failing_open
    pointer_mod.time.sleep = lambda delay: (_ for _ in ()).throw(KeyboardInterrupt())
    failed_reads.clear()
    try:
        verify_canonical_lfs_pointers(
            token="fake-pointer-token",
            repo_id="owner/repo",
            revision="main",
            expectations=expectations,
        )
    except KeyboardInterrupt:
        sleep_interrupt_propagated = True
    else:
        sleep_interrupt_propagated = False
    check(
        "backoff interruption propagates before another read",
        sleep_interrupt_propagated and len(failed_reads) == 1,
        f"calls={len(failed_reads)}",
    )
    pointer_mod.time.sleep = retry_sleeps.append

    contract_error = CanonicalLfsPointerError(
        "noncanonical pointer for fake-token-secret"
    )
    cli_kind, cli_hint = api_mod._classify_upload_error(contract_error)
    check(
        "CLI classifies the pointer contract violation explicitly",
        cli_kind == "LFS 指针验证失败"
        and "Git LFS pointer" in cli_hint
        and "fake-token-secret" not in cli_hint,
    )
    envelope = api_mod._resumable_failure_envelope(contract_error)
    worker_kind, worker_hint = api_mod._classify_upload_error(
        api_mod.ResumableWorkerError(envelope["category"])
    )
    check(
        "resumable envelope preserves only the safe pointer category",
        envelope == {"category": "lfs_pointer"}
        and worker_kind == "LFS 指针验证失败"
        and "Git LFS pointer" in worker_hint,
    )
    sdk_error = sdk_mod._sdk_error(contract_error, "上传目录", "owner/repo")
    check(
        "SDK error identifies pointer verification without leaking details",
        "Git LFS pointer 验证失败" in str(sdk_error)
        and "fake-token-secret" not in str(sdk_error),
    )

    upload_calls = []

    def fake_upload():
        upload_calls.append(True)
        upload_operation = CommitOperationAdd(
            path_in_repo="nested/fixture.bin",
            path_or_fileobj=content,
        )
        upload_operation._upload_mode = "lfs"
        list(
            hf_api._prepare_commit_payload(
                operations=[upload_operation],
                files_to_copy={},
                commit_message="wrapped upload",
            )
        )
        return SimpleNamespace(oid="b" * 40)

    retry_outcomes[:] = [
        urllib.error.URLError("temporary post-commit read failure"),
        FakeResponse(expected),
    ]
    pointer_mod._open_atomgit_url = recover_on_second_read
    opened.clear()
    retry_sleeps.clear()
    wrapped_result = run_canonical_lfs_upload(
        fake_upload,
        token="fake-pointer-token",
        repo_id="owner/repo",
    )
    check(
        "upload wrapper verifies the exact returned commit",
        wrapped_result.oid == "b" * 40
        and upload_calls == [True]
        and len(opened) == 2
        and "ref=" + ("b" * 40) in opened[0][0].full_url
        and all(timeout == 300.0 for _, timeout in opened)
        and retry_sleeps == [2.0],
    )

    pointer_mod._open_atomgit_url = failing_open
    failed_reads.clear()
    retry_sleeps.clear()
    try:
        run_canonical_lfs_upload(
            fake_upload,
            token="fake-pointer-token",
            repo_id="owner/repo",
        )
    except CanonicalLfsPointerError as error:
        unconfirmed_error = error
    else:
        unconfirmed_error = None
    unconfirmed_type = getattr(pointer_mod, "CanonicalLfsCommitUnconfirmedError", None)
    check(
        "post-commit pointer failure preserves created and unconfirmed state",
        unconfirmed_type is not None
        and isinstance(unconfirmed_error, unconfirmed_type)
        and unconfirmed_error.remote_commit_status == "created"
        and unconfirmed_error.local_confirmation_status == "unconfirmed"
        and unconfirmed_error.commit_revision == "b" * 40
        and unconfirmed_error.confirmation_failure == "pointer_unavailable"
        and isinstance(unconfirmed_error.__cause__, CanonicalLfsPointerError)
        and len(failed_reads) == 3
        and retry_sleeps == [2.0, 4.0]
        and "b" * 40 not in str(unconfirmed_error)
        and "fake-pointer-token" not in str(unconfirmed_error),
        type(unconfirmed_error).__name__ if unconfirmed_error else "no error",
    )

    multi_reads = []

    def multi_pointer_open(request, timeout):
        multi_reads.append((request, timeout))
        if len(multi_reads) == 1:
            return FakeResponse(expected)
        raise urllib.error.URLError("later pointer is unavailable")

    def multi_pointer_upload():
        operations = []
        for path in ("nested/confirmed.bin", "nested/unconfirmed.bin"):
            operation = CommitOperationAdd(
                path_in_repo=path,
                path_or_fileobj=content,
            )
            operation._upload_mode = "lfs"
            operations.append(operation)
        list(
            hf_api._prepare_commit_payload(
                operations=operations,
                files_to_copy={},
                commit_message="multi pointer upload",
            )
        )
        return SimpleNamespace(oid="c" * 40)

    pointer_mod._open_atomgit_url = multi_pointer_open
    retry_sleeps.clear()
    try:
        run_canonical_lfs_upload(
            multi_pointer_upload,
            token="fake-pointer-token",
            repo_id="owner/repo",
        )
    except CanonicalLfsPointerError as error:
        multi_pointer_error = error
    else:
        multi_pointer_error = None
    check(
        "a later pointer failure leaves the whole returned commit unconfirmed",
        isinstance(multi_pointer_error, unconfirmed_type)
        and multi_pointer_error.commit_revision == "c" * 40
        and len(multi_reads) == 4
        and retry_sleeps == [2.0, 4.0],
        type(multi_pointer_error).__name__ if multi_pointer_error else "no error",
    )

    opened.clear()
    failed_reads.clear()

    def invalid_revision_upload():
        fake_upload()
        return SimpleNamespace(oid="not-a-commit-sha")

    try:
        run_canonical_lfs_upload(
            invalid_revision_upload,
            token="fake-pointer-token",
            repo_id="owner/repo",
        )
    except CanonicalLfsPointerError as error:
        invalid_revision_error = error
    else:
        invalid_revision_error = None
    check(
        "invalid commit metadata never claims a created remote commit",
        isinstance(invalid_revision_error, CanonicalLfsPointerError)
        and not isinstance(invalid_revision_error, unconfirmed_type)
        and not opened
        and not failed_reads,
        type(invalid_revision_error).__name__ if invalid_revision_error else "no error",
    )

    original_preupload = hf_api.HfApi.preupload_lfs_files

    def fake_preupload(self, *, additions, **kwargs):
        for addition in additions:
            addition._upload_mode = "lfs"

    hf_api.HfApi.preupload_lfs_files = fake_preupload
    no_op_operation = CommitOperationAdd(
        path_in_repo="nested/fixture.bin",
        path_or_fileobj=content,
    )

    def fake_no_op_upload():
        client = hf_api.HfApi(endpoint="https://hub.atomgit.com")
        client.preupload_lfs_files(
            repo_id="owner/repo",
            additions=[no_op_operation],
            token="fake-pointer-token",
            repo_type="model",
            revision="main",
            create_pr=False,
            num_threads=1,
            free_memory=False,
        )
        return SimpleNamespace(oid="c" * 40)

    pointer_mod._open_atomgit_url = exact_open
    opened.clear()
    run_canonical_lfs_upload(
        fake_no_op_upload,
        token="fake-pointer-token",
        repo_id="owner/repo",
    )
    check(
        "no-op LFS upload is still verified at the returned commit",
        len(opened) == 1
        and "ref=" + ("c" * 40) in opened[0][0].full_url,
    )
    hf_api.HfApi.preupload_lfs_files = original_preupload

    ambiguous_operation = CommitOperationAdd(
        path_in_repo="nested/fixture.bin",
        path_or_fileobj=content,
    )
    ambiguous_operation._upload_mode = "lfs"
    verified = []
    marked = []

    def ambiguous_commit(**kwargs):
        list(
            hf_api._prepare_commit_payload(
                operations=kwargs["operations"],
                files_to_copy={},
                commit_message="ambiguous upload",
            )
        )
        raise httpx.ReadTimeout("ambiguous test timeout")

    controller = api_mod._ResumableCommitController(
        ambiguous_commit,
        token="fake-pointer-token",
        reconcile=lambda **kwargs: {"nested/fixture.bin"},
        mark_committed=lambda operations: marked.extend(operations),
        verify_committed=lambda items, repo_id, revision: verified.append(
            (list(items), repo_id, revision)
        ),
    )
    ambiguous_result = controller.create_commit(
        repo_id="owner/repo",
        repo_type="model",
        revision="main",
        operations=[ambiguous_operation],
        commit_message="ambiguous upload",
    )
    check("ambiguous remote success returns without duplicate commit", ambiguous_result is None)
    check(
        "ambiguous remote success verifies before marking committed",
        len(verified) == 1
        and verified[0][0][0].content == expected
        and verified[0][1:] == ("owner/repo", "main")
        and marked == [ambiguous_operation],
    )

    pointer_mod._open_atomgit_url = original_open
    pointer_mod.time.sleep = original_sleep

    passed = sum(results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
