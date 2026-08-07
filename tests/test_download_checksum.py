#!/usr/bin/env python3
"""Verify opt-in CLI checksum validation and atomic failure behavior."""

import contextlib
import hashlib
import io
import sys
import tempfile
import urllib.error
from pathlib import Path

import atomgit  # noqa: F401
from click.testing import CliRunner


api_mod = sys.modules["atomgit.api"]
cli_mod = sys.modules["atomgit.cli"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def sha256_checksum(content):
    return "sha256", hashlib.sha256(content).hexdigest(), len(content)


def git_blob_checksum(content):
    digest = hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    ).hexdigest()
    return "git-sha1", digest, len(content)


class FakeMetadata:
    def __init__(self, etag, size):
        self.etag = etag
        self.size = size


class FakeResponse:
    def __init__(self, content):
        self.content = content

    def read(self, size=-1):
        if size is None or size < 0:
            content, self.content = self.content, b""
            return content
        content, self.content = self.content[:size], self.content[size:]
        return content

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeSocket:
    def close(self):
        pass


def main():
    content = b"checksum-content"
    sha256 = sha256_checksum(content)
    git_sha1 = git_blob_checksum(content)

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        sha_file = root / "sha.bin"
        sha_file.write_bytes(content)
        api_mod._verify_download_checksum(sha_file, sha256)
        check("SHA-256 verifier accepts matching file", True)

        git_file = root / "git.bin"
        git_file.write_bytes(content)
        api_mod._verify_download_checksum(git_file, git_sha1)
        check("Git blob SHA-1 verifier accepts matching file", True)

        original_open = api_mod._atomgit_open_url
        try:
            destination = root / "standard.bin"
            destination.write_bytes(b"original")
            api_mod._atomgit_open_url = lambda request, timeout=60: FakeResponse(content)
            api_mod._download_atomgit_file(
                "user/repo", "model", "standard.bin", destination, None,
                checksum=sha256,
            )
            check("verified standard download replaces destination", destination.read_bytes() == content)

            attempts = []

            def corrupt_open(request, timeout=60):
                attempts.append(request.full_url)
                return FakeResponse(b"corrupt-content")

            api_mod._atomgit_open_url = corrupt_open
            destination.write_bytes(b"preserve-me")
            try:
                api_mod._download_atomgit_file(
                    "user/repo", "model", "standard.bin", destination, None,
                    checksum=sha256,
                )
                mismatch = None
            except Exception as error:
                mismatch = error
            check("checksum mismatch retries once", len(attempts) == 2, str(len(attempts)))
            check(
                "checksum mismatch preserves destination and cleans temporary",
                mismatch is not None
                and destination.read_bytes() == b"preserve-me"
                and not list(root.glob(".standard.bin.*.part")),
                repr(mismatch),
            )
        finally:
            api_mod._atomgit_open_url = original_open

        original_raw_get = api_mod._atomgit_raw_http_get
        try:
            raw_destination = root / "raw.bin"

            def raw_get(*args, **kwargs):
                return 200, {"content-length": str(len(content))}, io.BytesIO(content), FakeSocket()

            api_mod._atomgit_raw_http_get = raw_get
            api_mod._atomgit_download_raw(
                "https://hub.atomgit.com/user/repo/resolve/main/中文.bin",
                raw_destination,
                {},
                checksum=sha256,
            )
            check("verified raw UTF-8 download succeeds", raw_destination.read_bytes() == content)

            raw_destination.write_bytes(b"preserve-raw")

            def corrupt_raw_get(*args, **kwargs):
                corrupt = b"corrupt-content"
                return 200, {"content-length": str(len(corrupt))}, io.BytesIO(corrupt), FakeSocket()

            api_mod._atomgit_raw_http_get = corrupt_raw_get
            try:
                api_mod._atomgit_download_raw(
                    "https://hub.atomgit.com/user/repo/resolve/main/中文.bin",
                    raw_destination,
                    {},
                    checksum=sha256,
                )
                raw_mismatch = None
            except Exception as error:
                raw_mismatch = error
            check(
                "raw checksum mismatch preserves destination and cleans temporary",
                raw_mismatch is not None
                and raw_destination.read_bytes() == b"preserve-raw"
                and not list(root.glob(".raw.bin.*.part")),
                repr(raw_mismatch),
            )

            original_open = api_mod._atomgit_open_url

            def not_found(request, timeout=60):
                raise urllib.error.HTTPError(
                    request.full_url, 404, "Not Found", {}, None
                )

            api_mod._atomgit_open_url = not_found
            fallback_destination = root / "fallback.bin"
            fallback_destination.write_bytes(b"preserve-fallback")
            try:
                api_mod._download_atomgit_file(
                    "user/repo",
                    "model",
                    "sub/中文.bin",
                    fallback_destination,
                    None,
                    checksum=sha256,
                )
                fallback_mismatch = None
            except Exception as error:
                fallback_mismatch = error
            finally:
                api_mod._atomgit_open_url = original_open
            check(
                "encoded 404 raw fallback enforces checksum",
                fallback_mismatch is not None
                and fallback_destination.read_bytes() == b"preserve-fallback"
                and not list(root.glob(".fallback.bin.*.part")),
                repr(fallback_mismatch),
            )
        finally:
            api_mod._atomgit_raw_http_get = original_raw_get

    original_list = api_mod._atomgit_list_repo_files
    original_fetch = api_mod._download_atomgit_file
    original_metadata = api_mod.get_hf_file_metadata
    original_credentials = api_mod.config.get_credentials
    metadata_calls = []
    fetch_calls = []
    try:
        api_mod._atomgit_list_repo_files = lambda *args, **kwargs: (
            "model", ["file.bin"]
        )
        api_mod.config.get_credentials = lambda: None

        def fake_metadata(url, token=None, timeout=None, endpoint=None):
            metadata_calls.append((url, token, timeout, endpoint))
            return FakeMetadata(sha256[1], sha256[2])

        def fake_fetch(repo_id, repo_type, filename, destination, token, checksum=None):
            fetch_calls.append((filename, checksum))
            destination.write_bytes(content)

        api_mod.get_hf_file_metadata = fake_metadata
        api_mod._download_atomgit_file = fake_fetch
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / "file.bin"
            existing.write_bytes(content)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                verified = api_mod.api.download_file(
                    "user/repo", "file.bin", root, verify_checksum=True
                )
            check("matching existing file verifies without download", verified and not fetch_calls)
            check("existing verification is reported", "checksum" in output.getvalue().lower())
            check(
                "anonymous metadata lookup disables ambient HF token",
                metadata_calls[-1][1] is False,
                repr(metadata_calls[-1][1]),
            )
            check(
                "metadata lookup uses explicit endpoint and no query credential",
                metadata_calls[-1][3] == "https://hub.atomgit.com"
                and "?" not in metadata_calls[-1][0],
            )

            existing.write_bytes(b"corrupt")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rejected = api_mod.api.download_file(
                    "user/repo", "file.bin", root, verify_checksum=True
                )
            check("corrupt existing file fails without replacement", not rejected and existing.read_bytes() == b"corrupt")
            check("corrupt existing file gives force guidance", "--force" in output.getvalue())

            with contextlib.redirect_stdout(io.StringIO()):
                forced = api_mod.api.download_file(
                    "user/repo", "file.bin", root,
                    force_download=True, verify_checksum=True,
                )
            check("forced verified download succeeds", forced)
            check("checksum specification reaches downloader", fetch_calls[-1][1] == sha256)

            metadata_calls.clear()
            fetch_calls.clear()
            with contextlib.redirect_stdout(io.StringIO()):
                skipped = api_mod.api.download_file("user/repo", "file.bin", root)
            check("default existing-file policy still skips", skipped and not metadata_calls and not fetch_calls)

            api_mod.get_hf_file_metadata = lambda *args, **kwargs: FakeMetadata("weak-etag", len(content))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                unsupported = api_mod.api.download_file(
                    "user/repo", "file.bin", root,
                    force_download=True, verify_checksum=True,
                )
            check("unsupported checksum metadata fails closed", not unsupported and not fetch_calls)
            check("unsupported metadata failure is actionable", "checksum" in output.getvalue().lower())
    finally:
        api_mod._atomgit_list_repo_files = original_list
        api_mod._download_atomgit_file = original_fetch
        api_mod.get_hf_file_metadata = original_metadata
        api_mod.config.get_credentials = original_credentials

    original_cli_repo = cli_mod.api.download_repo
    original_cli_file = cli_mod.api.download_file
    original_logged_in = cli_mod.config.is_logged_in
    cli_calls = []
    try:
        cli_mod.config.is_logged_in = lambda: True
        cli_mod.api.download_repo = lambda *args, **kwargs: cli_calls.append(("repo", kwargs)) or True
        cli_mod.api.download_file = lambda *args, **kwargs: cli_calls.append(("file", kwargs)) or True
        runner = CliRunner()
        with runner.isolated_filesystem():
            repo_result = runner.invoke(
                cli_mod.cli, ["download", "user/repo", "--verify-checksum"]
            )
            existing_target = Path("existing-target")
            existing_target.mkdir()
            (existing_target / "file.bin").write_bytes(content)
            existing_result = runner.invoke(
                cli_mod.cli,
                [
                    "download",
                    "user/repo",
                    "--directory",
                    str(existing_target),
                    "--verify-checksum",
                ],
            )
            file_result = runner.invoke(
                cli_mod.cli,
                ["download-file", "user/repo", "file.bin", "--verify-checksum"],
            )
        check("repository checksum option succeeds", repo_result.exit_code == 0)
        check(
            "existing repository checksum message is consistent",
            existing_result.exit_code == 0
            and "校验已有文件" in existing_result.output
            and "不校验内容" not in existing_result.output,
            repr(existing_result.output),
        )
        check("single-file checksum option succeeds", file_result.exit_code == 0)
        check(
            "checksum option is forwarded by both commands",
            len(cli_calls) == 3
            and all(call[1].get("verify_checksum") is True for call in cli_calls),
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
