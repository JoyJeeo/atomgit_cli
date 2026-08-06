#!/usr/bin/env python3
"""Standard URL download attempts must not leave partial repository files."""

import sys
import tempfile
from pathlib import Path

import atomgit  # noqa: F401


api_mod = sys.modules["atomgit.api"]
results = []


class ReadError(Exception):
    pass


class InterruptedResponse:
    def __init__(self):
        self.reads = 0

    def read(self, size=-1):
        self.reads += 1
        if self.reads == 1:
            return b"partial-content"
        raise ReadError("offline interrupted body")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class CompleteResponse:
    def __init__(self):
        self.content = b"complete-content"

    def read(self, size=-1):
        if not self.content:
            return b""
        content, self.content = self.content, b""
        return content

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    original_open = api_mod._atomgit_open_url
    try:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "file.bin"
            neighboring_file = destination.with_name(destination.name + ".part")
            destination.write_bytes(b"old-content")
            neighboring_file.write_bytes(b"repository-content")
            calls = []

            def interrupted_open(request, timeout=60):
                calls.append(request.full_url)
                return InterruptedResponse()

            api_mod._atomgit_open_url = interrupted_open
            try:
                api_mod._download_atomgit_file(
                    "user/repo", "model", "file.bin", destination, "fake-token"
                )
                interrupted_error = None
            except Exception as error:
                interrupted_error = error

            check("interrupted standard download fails", isinstance(interrupted_error, ReadError))
            check("interrupted standard download retries once", len(calls) == 2, repr(calls))
            check(
                "interrupted standard download cleans unique temporary",
                not list(destination.parent.glob(f".{destination.name}.*.part")),
            )
            check("interrupted standard download preserves destination", destination.read_bytes() == b"old-content")
            check(
                "interrupted standard download preserves neighboring file",
                neighboring_file.read_bytes() == b"repository-content",
            )

            def open_failure(request, timeout=60):
                raise RuntimeError("offline open failure")

            api_mod._atomgit_open_url = open_failure
            try:
                api_mod._download_atomgit_file(
                    "user/repo", "model", "file.bin", destination, "fake-token"
                )
            except RuntimeError:
                pass
            check(
                "pre-open failure leaves no unique temporary",
                not list(destination.parent.glob(f".{destination.name}.*.part")),
            )
            check("pre-open failure preserves destination", destination.read_bytes() == b"old-content")
            check(
                "pre-open failure preserves neighboring file",
                neighboring_file.read_bytes() == b"repository-content",
            )

            api_mod._atomgit_open_url = lambda request, timeout=60: CompleteResponse()
            api_mod._download_atomgit_file(
                "user/repo", "model", "file.bin", destination, "fake-token"
            )
            check("successful standard download replaces destination", destination.read_bytes() == b"complete-content")
            check(
                "successful standard download leaves no unique temporary",
                not list(destination.parent.glob(f".{destination.name}.*.part")),
            )
            check(
                "successful standard download preserves neighboring file",
                neighboring_file.read_bytes() == b"repository-content",
            )
    finally:
        api_mod._atomgit_open_url = original_open

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
