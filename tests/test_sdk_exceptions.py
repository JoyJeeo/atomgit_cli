#!/usr/bin/env python3
"""Stable SDK exception types preserve causes and sanitize public messages."""

import tempfile
from pathlib import Path

import atomgit
import atomgit_hub


results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def capture(callable_obj):
    try:
        callable_obj()
    except Exception as error:
        return error
    return None


def main():
    exception_types = (
        atomgit_hub.AtomGitAuthenticationError,
        atomgit_hub.AtomGitRepositoryNotFoundError,
        atomgit_hub.AtomGitRepositoryExistsError,
        atomgit_hub.AtomGitRevisionNotFoundError,
        atomgit_hub.AtomGitTimeoutError,
        atomgit_hub.AtomGitNetworkError,
        atomgit_hub.AtomGitUnsupportedError,
    )
    check(
        "all stable exceptions inherit AtomGitError",
        all(issubclass(error_type, atomgit_hub.AtomGitError) for error_type in exception_types),
    )
    check("AtomGitError remains an Exception", issubclass(atomgit_hub.AtomGitError, Exception))
    check("package export shares base class", atomgit.AtomGitError is atomgit_hub.AtomGitError)

    original_snapshot = atomgit_hub.hf_snapshot_download
    try:
        cases = [
            (
                "permission",
                RuntimeError(
                    "HTTP 403 Forbidden https://signed.invalid/file?token=secret"
                ),
                atomgit_hub.AtomGitAuthenticationError,
            ),
            (
                "repository not found",
                RuntimeError("404 Repository Not Found"),
                atomgit_hub.AtomGitRepositoryNotFoundError,
            ),
            (
                "revision",
                RuntimeError("revision dev not found 404"),
                atomgit_hub.AtomGitRevisionNotFoundError,
            ),
            ("timeout", TimeoutError("request timed out"), atomgit_hub.AtomGitTimeoutError),
            (
                "network",
                ConnectionError("connection reset by peer"),
                atomgit_hub.AtomGitNetworkError,
            ),
            ("fallback", RuntimeError("unexpected secret detail"), atomgit_hub.AtomGitError),
        ]
        for name, source, expected_type in cases:
            atomgit_hub.hf_snapshot_download = lambda **kwargs: (_ for _ in ()).throw(source)
            error = capture(lambda: atomgit_hub.snapshot_download("user/repo", token=False))
            check(f"{name} maps to stable type", type(error) is expected_type)
            check(f"{name} preserves cause", error.__cause__ is source)
            check(f"{name} message is sanitized", "signed.invalid" not in str(error) and "secret" not in str(error))
            check(
                f"{name} sensitive cause is sanitized",
                "signed.invalid" not in str(error.__cause__)
                and "secret" not in str(error.__cause__),
            )
    finally:
        atomgit_hub.hf_snapshot_download = original_snapshot

    original_upload = atomgit_hub.hf_upload_folder
    try:
        with tempfile.TemporaryDirectory() as source_dir:
            source = Path(source_dir)
            (source / "file.txt").write_text("content", encoding="utf-8")
            upload_source = RuntimeError("404 https://signed.invalid/upload?token=secret")
            atomgit_hub.hf_upload_folder = lambda **kwargs: (_ for _ in ()).throw(upload_source)
            error = capture(
                lambda: atomgit_hub.upload_folder(
                    source, "user/repo", token="fake-token"
                )
            )
            check(
                "upload not-found uses stable type",
                isinstance(error, atomgit_hub.AtomGitRepositoryNotFoundError),
            )
            check("upload preserves cause", error.__cause__ is upload_source)
            check("upload message is sanitized", "signed.invalid" not in str(error))
    finally:
        atomgit_hub.hf_upload_folder = original_upload

    original_create = atomgit_hub.create_repo
    create_source = RuntimeError("409 repository already exists")
    atomgit_hub.create_repo = lambda **kwargs: (_ for _ in ()).throw(create_source)
    try:
        error = capture(
            lambda: atomgit_hub.create_repository(
                "user/repo", token="fake-token", private=True
            )
        )
        check(
            "create conflict uses stable type",
            isinstance(error, atomgit_hub.AtomGitRepositoryExistsError),
        )
        check("create conflict preserves cause", error.__cause__ is create_source)
        result = atomgit_hub.create_repository(
            "user/repo", token="fake-token", private=True, exist_ok=True
        )
        check("create exist_ok behavior preserved", result == "https://atomgit.com/user/repo")
    finally:
        atomgit_hub.create_repo = original_create

    unsupported = capture(
        lambda: atomgit_hub.create_repository(
            "user/repo", token="fake-token", private=False
        )
    )
    check(
        "unsupported behavior has stable and ValueError contracts",
        isinstance(unsupported, atomgit_hub.AtomGitUnsupportedError)
        and isinstance(unsupported, ValueError),
    )

    missing_token = capture(
        lambda: atomgit_hub.create_repository("user/repo", token=None, private=True)
    )
    if atomgit_hub._get_token() is None:
        check(
            "missing token uses authentication type",
            isinstance(missing_token, atomgit_hub.AtomGitAuthenticationError),
        )

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
