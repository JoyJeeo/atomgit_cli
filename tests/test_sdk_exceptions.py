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


def nested_error_checks():
    import logging
    import traceback
    from io import StringIO
    from unittest.mock import patch

    from atomgit.interfaces.sdk import AtomGitClient

    class Config:
        def get_credentials(self):
            return None

    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory)
        (source / "file.txt").write_text("fixture", encoding="utf-8")

        def nested(**kwargs):
            try:
                raise ValueError(
                    "https://fixture.invalid/?signature=FAKE_SECRET_MARKER"
                )
            except ValueError as cause:
                raise RuntimeError("request failed") from cause

        with patch.object(atomgit_hub, "hf_upload_folder", nested):
            error = capture(
                lambda: atomgit_hub.upload_folder(
                    source, "fake/repo", token="fake-token"
                )
            )
        rendered = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        check(
            "complete SDK traceback excludes nested credential",
            "FAKE_SECRET_MARKER" not in rendered,
        )
        import httpx
        from huggingface_hub.errors import BadRequestError

        def rejected(**kwargs):
            raise BadRequestError(
                "https://fixture.invalid/?signature=FAKE_REMOTE_ERROR",
                response=httpx.Response(
                    400, request=httpx.Request("GET", "https://fixture.invalid")
                ),
            )

        with patch("huggingface_hub.HfApi.upload_file", staticmethod(rejected)):
            failure = capture(
                lambda: AtomGitClient(config=Config()).upload_file(
                    source / "file.txt", "fake/repo", token="fake-token"
                )
            )
        rendered = "".join(
            traceback.format_exception(type(failure), failure, failure.__traceback__)
        )
        check(
            "native dependency ValueError cannot bypass redaction",
            isinstance(failure, atomgit_hub.AtomGitError)
            and "FAKE_REMOTE_ERROR" not in rendered,
        )
        output = StringIO()
        logger = logging.getLogger("huggingface_hub.boundary_fixture")
        handler = logging.StreamHandler(output)
        logger.addHandler(handler)

        def noisy(**kwargs):
            logger.warning("https://fixture.invalid/?signature=FAKE_SECRET_MARKER")
            return "commit"

        try:
            with (
                patch("huggingface_hub.upload_file", noisy),
                patch("huggingface_hub.HfApi.upload_file", staticmethod(noisy)),
                patch(
                    "socket.socket.connect",
                    side_effect=AssertionError("offline test attempted network"),
                ),
            ):
                AtomGitClient(config=Config()).upload_file(
                    source / "file.txt", "fake/repo", token="fake-token"
                )
            check(
                "native single-file dependency logs are redacted",
                "FAKE_SECRET_MARKER" not in output.getvalue(),
            )
        finally:
            logger.removeHandler(handler)


def main():
    nested_error_checks()

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
            check(
                f"{name} suppresses raw cause",
                error.__cause__ is None and error.__suppress_context__,
            )
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
            check(
                "upload suppresses raw cause",
                error.__cause__ is None and error.__suppress_context__,
            )
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
        check(
            "create conflict suppresses raw cause",
            error.__cause__ is None and error.__suppress_context__,
        )
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
