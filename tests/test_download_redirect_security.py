#!/usr/bin/env python3
"""Verify that CLI download redirects cannot disclose bearer credentials."""

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

    @property
    def port(self):
        return self.server.server_port

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.server.shutdown()
        self.thread.join(timeout=2)
        self.server.server_close()


def _sink_handler(seen_headers):
    class SinkHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen_headers.append(self.headers.get("Authorization"))
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *args):
            pass

    return SinkHandler


def _private_token_sink_handler(seen_headers):
    class SinkHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen_headers.append(self.headers.get("Private-Token"))
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *args):
            pass

    return SinkHandler


def _redirect_handler(location):
    class RedirectHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", location())
            self.end_headers()

        def log_message(self, *args):
            pass

    return RedirectHandler


def main():
    original_endpoint = api_mod.os.environ.get("HF_ENDPOINT")
    token = "fake-download-token-never-print"
    try:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)

            standard_seen = []
            with _Server(_sink_handler(standard_seen)) as sink:
                location = lambda: f"http://localhost:{sink.port}/blob"
                with _Server(_redirect_handler(location)) as redirect:
                    api_mod.os.environ["HF_ENDPOINT"] = (
                        f"http://127.0.0.1:{redirect.port}"
                    )
                    api_mod._download_atomgit_file(
                        "user/repo", "model", "file.bin",
                        root / "standard.bin", token,
                    )
            check(
                "standard cross-origin redirect strips bearer token",
                standard_seen == [None],
                repr(standard_seen),
            )

            raw_seen = []
            with _Server(_sink_handler(raw_seen)) as sink:
                location = lambda: f"http://localhost:{sink.port}/blob"
                with _Server(_redirect_handler(location)) as redirect:
                    api_mod._atomgit_download_raw(
                        f"http://127.0.0.1:{redirect.port}/sub/中文.bin",
                        root / "raw.bin",
                        {"Authorization": f"Bearer {token}"},
                    )
            check(
                "raw cross-origin redirect strips bearer token",
                raw_seen == [None],
                repr(raw_seen),
            )

            private_token_seen = []
            with _Server(_private_token_sink_handler(private_token_seen)) as sink:
                location = lambda: f"http://localhost:{sink.port}/repos"
                with _Server(_redirect_handler(location)) as redirect:
                    request = api_mod.urllib.request.Request(
                        f"http://127.0.0.1:{redirect.port}/api/v5/user/repos",
                        headers={"PRIVATE-TOKEN": token},
                    )
                    with api_mod._atomgit_open_url(request) as response:
                        response.read()
            check(
                "V5 cross-origin redirect strips private token",
                private_token_seen == [None],
                repr(private_token_seen),
            )

            _, same_origin_headers = api_mod._prepare_download_redirect(
                "https://hub.atomgit.com/user/repo/resolve/main/file.bin",
                "/blob/file.bin",
                {"Authorization": f"Bearer {token}"},
            )
            check(
                "same-origin redirect retains bearer token",
                same_origin_headers.get("Authorization") == f"Bearer {token}",
            )

            _, same_origin_absolute_headers = api_mod._prepare_download_redirect(
                "https://hub.atomgit.com/file.bin",
                "https://hub.atomgit.com/other.bin",
                {"Authorization": f"Bearer {token}"},
            )
            check(
                "same-origin absolute redirect retains bearer token",
                same_origin_absolute_headers.get("Authorization")
                == f"Bearer {token}",
            )

            cross_url, stripped_headers = api_mod._prepare_download_redirect(
                "https://hub.atomgit.com/file.bin",
                "https://cdn.example/file.bin",
                {"Authorization": f"Bearer {token}"},
            )
            _, returned_headers = api_mod._prepare_download_redirect(
                cross_url,
                "https://hub.atomgit.com/file.bin",
                stripped_headers,
            )
            check(
                "cross-origin redirect never restores bearer token",
                "Authorization" not in returned_headers,
            )

            _, changed_port_headers = api_mod._prepare_download_redirect(
                "https://hub.atomgit.com/file.bin",
                "https://hub.atomgit.com:8443/file.bin",
                {"Authorization": f"Bearer {token}"},
            )
            check(
                "port change strips bearer token",
                "Authorization" not in changed_port_headers,
            )

            try:
                api_mod._prepare_download_redirect(
                    "https://hub.atomgit.com/file.bin",
                    "http://hub.atomgit.com/file.bin",
                    {"Authorization": f"Bearer {token}"},
                )
                downgrade_rejected = False
            except api_mod.urllib.error.URLError:
                downgrade_rejected = True
            check("HTTPS downgrade is rejected", downgrade_rejected)

            try:
                api_mod._prepare_download_redirect(
                    "https://hub.atomgit.com/file.bin",
                    "file:///tmp/file.bin",
                    {"Authorization": f"Bearer {token}"},
                )
                unsupported_rejected = False
            except api_mod.urllib.error.URLError:
                unsupported_rejected = True
            check("unsupported redirect scheme is rejected", unsupported_rejected)
    finally:
        if original_endpoint is None:
            api_mod.os.environ.pop("HF_ENDPOINT", None)
        else:
            api_mod.os.environ["HF_ENDPOINT"] = original_endpoint

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
