#!/usr/bin/env python3
"""Nested non-ASCII downloads obtain strong metadata through raw fallback."""

import hashlib
import io
import sys
import tempfile
import urllib.error
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


class FakeSocket:
    def close(self):
        pass


def main():
    content = b"nested-unicode-resume"
    digest = hashlib.sha256(content).hexdigest()
    original_metadata = api_mod.get_hf_file_metadata
    original_raw_head = api_mod._atomgit_raw_http_head
    original_raw_resume = api_mod._atomgit_resume_raw
    original_cache_root = api_mod._resume_cache_root
    metadata_calls = []
    raw_calls = []

    def encoded_not_found(url, **kwargs):
        metadata_calls.append((url, kwargs))
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    def raw_metadata(host, port, scheme, raw_path, headers, timeout):
        raw_calls.append((host, port, scheme, raw_path, dict(headers), timeout))
        if host == "hub.atomgit.com":
            return (
                302,
                {"location": "https://cdn.example/object?signature=redacted"},
                io.BytesIO(),
                FakeSocket(),
            )
        return (
            200,
            {
                "x-linked-etag": digest,
                "x-linked-size": str(len(content)),
                "content-length": str(len(content)),
            },
            io.BytesIO(),
            FakeSocket(),
        )

    api_mod.get_hf_file_metadata = encoded_not_found
    api_mod._atomgit_raw_http_head = raw_metadata
    try:
        try:
            checksum = api_mod._atomgit_file_checksum(
                "user/repo", "dataset", "sub/中文样本.csv", "fake-token"
            )
            checksum_error = None
        except Exception as error:
            checksum = None
            checksum_error = error
        check(
            "Unicode checksum metadata falls back after encoded 404",
            checksum == ("sha256", digest, len(content)),
            repr(checksum_error),
        )
        check(
            "standard metadata request remains first and percent encoded",
            len(metadata_calls) == 1
            and "%E4%B8%AD%E6%96%87" in metadata_calls[0][0]
            and metadata_calls[0][1].get("token") == "fake-token"
            and metadata_calls[0][1].get("timeout") == 60,
            repr(
                [
                    (url, kwargs.get("timeout"), bool(kwargs.get("token")))
                    for url, kwargs in metadata_calls
                ]
            ),
        )
        check(
            "raw fallback sends UTF-8 path bytes with bounded requests",
            len(raw_calls) == 2
            and b"sub/\xe4\xb8\xad\xe6\x96\x87\xe6\xa0\xb7\xe6\x9c\xac.csv"
            in raw_calls[0][3]
            and raw_calls[0][5] == 60,
            repr([(call[0], call[3], call[5]) for call in raw_calls]),
        )
        check(
            "raw metadata strips credentials across origins",
            raw_calls
            and "Authorization" in raw_calls[0][4]
            and not any(
                name.lower() in ("authorization", "private-token")
                for name in raw_calls[-1][4]
            ),
        )

        raw_calls.clear()
        anonymous_checksum = api_mod._atomgit_file_checksum(
            "user/repo", "model", "nested/中文.bin", None
        )
        check(
            "anonymous model metadata uses raw fallback without credentials",
            anonymous_checksum == ("sha256", digest, len(content))
            and len(raw_calls) == 2
            and raw_calls[0][3].startswith(
                b"/user/repo/resolve/main/nested/"
            )
            and b"/datasets/" not in raw_calls[0][3]
            and all(
                not any(
                    name.lower() in ("authorization", "private-token")
                    for name in call[4]
                )
                for call in raw_calls
            ),
            repr([(call[0], call[3]) for call in raw_calls]),
        )

        resume_calls = []

        def resume_raw(
            url, stream, headers, resume_size, expected_size, **kwargs
        ):
            resume_calls.append((url, dict(headers), resume_size, expected_size))
            stream.write(content[resume_size:])

        api_mod._atomgit_resume_raw = resume_raw
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = root / "cache"
            cache.mkdir(mode=0o700)
            destination = root / "sub" / "中文样本.csv"
            api_mod._resume_cache_root = lambda: cache
            api_mod._download_atomgit_file_resumable(
                "user/repo",
                "dataset",
                "sub/中文样本.csv",
                destination,
                "fake-token",
            )
            check(
                "Unicode resume consumes the corrected metadata path",
                destination.read_bytes() == content
                and len(resume_calls) == 1
                and "中文样本.csv" in resume_calls[0][0]
                and resume_calls[0][2:] == (0, len(content))
                and not list(cache.iterdir()),
                repr(
                    [
                        (url, resume_size, expected_size)
                        for url, _, resume_size, expected_size in resume_calls
                    ]
                ),
            )

        def ambiguous_raw(*args, **kwargs):
            return (
                200,
                {
                    "x-linked-etag": digest,
                    "x-linked-size": str(len(content)),
                    "content-length": str(len(content) + 1),
                },
                io.BytesIO(),
                FakeSocket(),
            )

        api_mod._atomgit_raw_http_head = ambiguous_raw
        try:
            api_mod._atomgit_file_checksum(
                "user/repo", "dataset", "sub/中文样本.csv", "fake-token"
            )
            ambiguous_error = None
        except Exception as error:
            ambiguous_error = error
        check(
            "raw metadata rejects conflicting sizes",
            isinstance(
                ambiguous_error, api_mod.DownloadChecksumMetadataError
            ),
            repr(ambiguous_error),
        )

        api_mod._atomgit_raw_http_head = raw_metadata
        raw_calls.clear()
        try:
            api_mod._atomgit_file_checksum(
                "user/repo", "model", "ascii.bin", "fake-token"
            )
            ascii_error = None
        except Exception as error:
            ascii_error = error
        check(
            "ASCII metadata 404 does not use raw fallback",
            isinstance(ascii_error, urllib.error.HTTPError) and not raw_calls,
            repr(ascii_error),
        )

        def encoded_server_error(url, **kwargs):
            raise urllib.error.HTTPError(
                url, 500, "Server Error", {}, None
            )

        api_mod.get_hf_file_metadata = encoded_server_error
        raw_calls.clear()
        try:
            api_mod._atomgit_file_checksum(
                "user/repo", "dataset", "sub/中文样本.csv", "fake-token"
            )
            server_error = None
        except Exception as error:
            server_error = error
        check(
            "non-404 metadata errors do not use raw fallback",
            isinstance(server_error, urllib.error.HTTPError)
            and server_error.code == 500
            and not raw_calls,
            repr(server_error),
        )
    finally:
        api_mod.get_hf_file_metadata = original_metadata
        api_mod._atomgit_raw_http_head = original_raw_head
        api_mod._atomgit_resume_raw = original_raw_resume
        api_mod._resume_cache_root = original_cache_root

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
