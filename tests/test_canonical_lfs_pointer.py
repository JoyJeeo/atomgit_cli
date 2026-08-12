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
        request.full_url,
    )
    check(
        "verification authenticates without putting token in the URL",
        request.get_header("Private-token") == "fake-pointer-token"
        and "fake-pointer-token" not in request.full_url,
    )

    pointer_mod._open_atomgit_url = lambda request, timeout: FakeResponse(
        expected[:-1]
    )
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
    check("verification rejects a pointer missing its final LF", missing_lf_rejected)

    def failing_open(request, timeout):
        raise urllib.error.HTTPError(
            "https://api.atomgit.com/private/repository/path?ref=fake-secret-ref",
            404,
            "Not Found fake-secret-body",
            {},
            None,
        )

    pointer_mod._open_atomgit_url = failing_open
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
        "verification transport failure is credential-safe",
        "fake-secret-ref" not in safe_rendered_error
        and "fake-secret-body" not in safe_rendered_error
        and "fake-pointer-token" not in safe_rendered_error
        and "fake-secret-ref" not in fetch_hint,
    )

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

    pointer_mod._open_atomgit_url = exact_open

    def fake_upload():
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

    opened.clear()
    wrapped_result = run_canonical_lfs_upload(
        fake_upload,
        token="fake-pointer-token",
        repo_id="owner/repo",
    )
    check(
        "upload wrapper verifies the exact returned commit",
        wrapped_result.oid == "b" * 40
        and len(opened) == 1
        and "ref=" + ("b" * 40) in opened[0][0].full_url,
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

    passed = sum(results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
