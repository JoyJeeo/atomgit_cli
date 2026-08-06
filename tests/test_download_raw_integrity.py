#!/usr/bin/env python3
"""Verify raw UTF-8-path downloads enforce HTTP response framing."""

import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import atomgit  # noqa: F401


api_mod = sys.modules["atomgit.api"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


class _Server:
    def __init__(self, handler):
        self.server = HTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.server.shutdown()
        self.thread.join(timeout=2)
        self.server.server_close()


def _handler(headers, body):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self):
            self.send_response(200)
            for key, value in headers:
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()
            self.close_connection = True

        def log_message(self, *args):
            pass

    return Handler


def _download(root, name, headers, body, existing=None, neighboring=None):
    destination = root / name
    if existing is not None:
        destination.write_bytes(existing)
    if neighboring is not None:
        destination.with_name(destination.name + ".part").write_bytes(neighboring)
    handler = _handler(headers, body)
    with _Server(handler) as server:
        url = f"http://127.0.0.1:{server.server.server_port}/file.bin"
        try:
            api_mod._atomgit_download_raw(url, destination, {})
            error = None
        except Exception as caught:
            error = caught
    return destination, error


def main():
    with tempfile.TemporaryDirectory() as temporary_dir:
        root = Path(temporary_dir)

        destination, error = _download(
            root,
            "chunked.bin",
            [("Transfer-Encoding", "chunked")],
            b"4\r\ndata\r\n0\r\n\r\n",
        )
        check(
            "chunked framing is decoded",
            error is None and destination.read_bytes() == b"data",
            repr(destination.read_bytes()) if destination.exists() else repr(error),
        )

        destination, error = _download(
            root,
            "fixed.bin",
            [("Content-Length", "4")],
            b"data",
            neighboring=b"repository-content",
        )
        check(
            "valid Content-Length body succeeds",
            error is None and destination.read_bytes() == b"data",
        )
        check(
            "successful raw download preserves neighboring file",
            destination.with_name(destination.name + ".part").read_bytes()
            == b"repository-content",
        )
        check(
            "successful raw download leaves no unique temporary",
            not list(destination.parent.glob(f".{destination.name}.*.part")),
        )

        destination, error = _download(
            root,
            "truncated.bin",
            [("Content-Length", "10")],
            b"short",
            existing=b"original",
            neighboring=b"repository-content",
        )
        check(
            "truncated Content-Length preserves destination",
            error is not None
            and destination.read_bytes() == b"original"
            and destination.with_name(destination.name + ".part").read_bytes()
            == b"repository-content"
            and not list(destination.parent.glob(f".{destination.name}.*.part")),
            repr(error),
        )

        destination, error = _download(
            root,
            "malformed-chunk.bin",
            [("Transfer-Encoding", "chunked")],
            b"ZZ\r\ndata\r\n0\r\n\r\n",
            existing=b"original",
        )
        check(
            "malformed chunk preserves destination",
            error is not None
            and destination.read_bytes() == b"original"
            and not destination.with_name(destination.name + ".part").exists(),
            repr(error),
        )

        destination, error = _download(
            root,
            "ambiguous.bin",
            [("Transfer-Encoding", "chunked"), ("Content-Length", "4")],
            b"4\r\ndata\r\n0\r\n\r\n",
            existing=b"original",
        )
        check(
            "conflicting framing is rejected",
            error is not None and destination.read_bytes() == b"original",
            repr(error),
        )

        destination, error = _download(
            root,
            "unsupported.bin",
            [("Transfer-Encoding", "gzip")],
            b"data",
            existing=b"original",
        )
        check(
            "unsupported transfer coding is rejected",
            error is not None and destination.read_bytes() == b"original",
            repr(error),
        )

        destination, error = _download(
            root,
            "signed-length.bin",
            [("Content-Length", "+4")],
            b"data",
            existing=b"original",
        )
        check(
            "non-decimal Content-Length syntax is rejected",
            error is not None and destination.read_bytes() == b"original",
            repr(error),
        )

        destination, error = _download(
            root,
            "signed-chunk.bin",
            [("Transfer-Encoding", "chunked")],
            b"+4\r\ndata\r\n0\r\n\r\n",
            existing=b"original",
        )
        check(
            "non-hexadecimal chunk-size syntax is rejected",
            error is not None and destination.read_bytes() == b"original",
            repr(error),
        )

        destination, error = _download(
            root,
            "chunk-trailer.bin",
            [("Transfer-Encoding", "chunked")],
            b"4;name=value\r\ndata\r\n0\r\nX-Check: yes\r\n\r\n",
        )
        check(
            "chunk extensions and valid trailers are supported",
            error is None and destination.read_bytes() == b"data",
            repr(error),
        )

        destination, error = _download(
            root,
            "close-delimited.bin",
            [],
            b"data",
        )
        check(
            "close-delimited body remains supported",
            error is None and destination.read_bytes() == b"data",
        )

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
