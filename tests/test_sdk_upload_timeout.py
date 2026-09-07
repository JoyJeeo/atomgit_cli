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


def main():
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
                    and error.__cause__ is not None
                    and "offline upload failure" in str(error.__cause__),
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
