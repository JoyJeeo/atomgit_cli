#!/usr/bin/env python3
"""Strict offline download contracts across CLI, API, and SDK."""

import contextlib
import inspect
import io
import sys
import tempfile
import warnings
from pathlib import Path

import atomgit  # noqa: F401
import atomgit_hub
from click.testing import CliRunner
from huggingface_hub import hf_hub_download as real_file_download
from huggingface_hub import snapshot_download as real_snapshot_download


api_mod = sys.modules["atomgit.api"]
cli_mod = sys.modules["atomgit.cli"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    original_sdk_snapshot = atomgit_hub.hf_snapshot_download
    original_sdk_file = atomgit_hub.hf_hub_download
    original_get_token = atomgit_hub._get_token
    sdk_snapshot_calls = []
    sdk_file_calls = []

    def strict_snapshot(**kwargs):
        inspect.signature(real_snapshot_download).bind(**kwargs)
        sdk_snapshot_calls.append(kwargs)
        return "/tmp/sdk-snapshot"

    def strict_file(**kwargs):
        inspect.signature(real_file_download).bind(**kwargs)
        sdk_file_calls.append(kwargs)
        return "/tmp/README.md"

    atomgit_hub.hf_snapshot_download = strict_snapshot
    atomgit_hub.hf_hub_download = strict_file
    atomgit_hub._get_token = lambda: "fake-stored-token"
    try:
        result = atomgit_hub.snapshot_download(
            "user/repo",
            revision="main",
            local_dir="/tmp/sdk-local",
            force_download=True,
            allow_patterns=["*.json"],
        )
        check("SDK snapshot result preserved", result == "/tmp/sdk-snapshot")
        call = sdk_snapshot_calls[-1]
        check("SDK snapshot uses stored token", call.get("token") == "fake-stored-token")
        check("SDK snapshot forwards revision", call.get("revision") == "main")
        check("SDK snapshot forwards local directory", call.get("local_dir") == "/tmp/sdk-local")
        check("SDK snapshot forwards force", call.get("force_download") is True)
        check("SDK snapshot forwards patterns", call.get("allow_patterns") == ["*.json"])

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            atomgit_hub.snapshot_download(
                "user/repo",
                token=False,
                local_dir_use_symlinks=False,
                proxies={"https": "http://proxy.invalid"},
                resume_download=True,
            )
        legacy_call = sdk_snapshot_calls[-1]
        check("explicit anonymous token preserved", legacy_call.get("token") is False)
        check(
            "removed legacy options omitted",
            all(
                name not in legacy_call
                for name in ("local_dir_use_symlinks", "proxies", "resume_download")
            ),
        )
        check("non-default legacy options warn", len(caught) == 1 and "ignores" in str(caught[0].message))

        result = atomgit_hub.download_file(
            "user/repo",
            "README.md",
            local_dir="/tmp/sdk-file",
            revision="main",
            token="fake-explicit-token",
            force_download=True,
        )
        check("SDK file result preserved", result == "/tmp/README.md")
        file_call = sdk_file_calls[-1]
        check("SDK file explicit token forwarded", file_call.get("token") == "fake-explicit-token")
        check("SDK file force forwarded", file_call.get("force_download") is True)
    finally:
        atomgit_hub.hf_snapshot_download = original_sdk_snapshot
        atomgit_hub.hf_hub_download = original_sdk_file
        atomgit_hub._get_token = original_get_token

    original_api_snapshot = api_mod.snapshot_download
    original_api_list = api_mod._atomgit_list_repo_files
    original_api_fetch = api_mod._download_atomgit_file
    original_credentials = api_mod.config.get_credentials
    list_calls = []
    fetch_calls = []

    def fake_list(repo_id, token, repo_type=None):
        list_calls.append((repo_id, token, repo_type))
        return "model", ["config.json", "weights/layer0.bin"]

    def fake_fetch(repo_id, repo_type, filename, dest, token):
        fetch_calls.append((repo_id, repo_type, filename, str(dest), token))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"content")

    api_mod._atomgit_list_repo_files = fake_list
    api_mod._download_atomgit_file = fake_fetch
    try:
        with tempfile.TemporaryDirectory() as local_dir:
            api_mod.config.get_credentials = lambda: None
            check(
                "API anonymous download succeeds",
                api_mod.api.download_repo("user/repo", Path(local_dir)) is True,
            )
            check("API anonymous list uses no token", list_calls[-1][1] is None)
            check(
                "API downloads all repo files",
                {c[2] for c in fetch_calls} == {"config.json", "weights/layer0.bin"},
            )
            check(
                "API repo files land in local dir",
                (Path(local_dir) / "config.json").read_text() == "content",
            )

            api_mod.config.get_credentials = lambda: {"token": "fake-stored-token"}
            fetch_calls.clear()
            check(
                "API authenticated download succeeds",
                api_mod.api.download_repo(
                    "user/repo", Path(local_dir), force_download=True
                )
                is True,
            )
            check("API stored token forwarded", list_calls[-1][1] == "fake-stored-token")
            check("API force redownloads existing files", len(fetch_calls) == 2)

            fetch_calls.clear()
            check(
                "API without force skips existing files",
                api_mod.api.download_repo("user/repo", Path(local_dir)) is True,
            )
            check("API existing files are skipped", len(fetch_calls) == 0)

            # 回归：修复前 download_repo 依赖 snapshot_download，其第一步
            # repo_info 在 AtomGit 返回 404，导致任何下载都被误判为空仓库；
            # 新路径不得再调用 snapshot_download。
            def forbidden_snapshot(**kwargs):
                raise AssertionError("snapshot_download must not be called")

            api_mod.snapshot_download = forbidden_snapshot
            fetch_calls.clear()
            check(
                "API bypasses repo_info/snapshot_download",
                api_mod.api.download_repo(
                    "user/repo", Path(local_dir), force_download=True
                )
                is True,
            )
            api_mod.snapshot_download = original_api_snapshot

            def empty_list(repo_id, token, repo_type=None):
                return "model", []

            api_mod._atomgit_list_repo_files = empty_list
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                empty_ok = api_mod.api.download_repo("user/repo", Path(local_dir)) is True
            empty_output = captured.getvalue()
            check("API empty repo is not a download failure", empty_ok)
            check(
                "API empty repo gives a clear message",
                "仓库为空" in empty_output,
                f"output={empty_output!r}",
            )

            def failing_list(repo_id, token, repo_type=None):
                raise ValueError("unrelated value error")

            api_mod._atomgit_list_repo_files = failing_list
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                other_failed = api_mod.api.download_repo("user/repo", Path(local_dir)) is False
            other_output = captured.getvalue()
            check("API unrelated ValueError still fails", other_failed)
            check(
                "API unrelated ValueError is reported",
                "下载失败" in other_output,
                f"output={other_output!r}",
            )

            # 单文件下载
            api_mod._atomgit_list_repo_files = fake_list
            fetch_calls.clear()
            check(
                "API single file download succeeds",
                api_mod.api.download_file("user/repo", "config.json", Path(local_dir), force_download=True) is True,
            )
            check(
                "API single file fetches target only",
                [c[2] for c in fetch_calls] == ["config.json"],
            )
            check(
                "API missing file fails cleanly",
                api_mod.api.download_file("user/repo", "missing.bin", Path(local_dir)) is False,
            )
            # 回归：中文文件名必须做 URL 百分号编码，否则 urllib 发送请求行
            # 时抛 UnicodeEncodeError（下载 中文样本.csv 曾直接失败）
            original_urlopen = api_mod.urllib.request.urlopen
            seen_urls = []

            class FakeHttpResponse:
                def __init__(self, data=b"content"):
                    self._data = data

                def read(self, size=-1):
                    if size is None or size < 0:
                        data, self._data = self._data, b""
                        return data
                    chunk, self._data = self._data[:size], self._data[size:]
                    return chunk

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

            def recording_urlopen(req, timeout=None):
                seen_urls.append(req.full_url)
                return FakeHttpResponse()

            api_mod.urllib.request.urlopen = recording_urlopen
            try:
                original_api_fetch(
                    "user/repo", "dataset", "中文样本.csv",
                    Path(local_dir) / "中文样本.csv", "fake-token",
                )
            finally:
                api_mod.urllib.request.urlopen = original_urlopen
            from urllib.parse import quote as _quote
            expected_suffix = "/resolve/main/" + _quote("中文样本.csv", safe="/")
            check(
                "API Chinese filename URL is percent-encoded",
                len(seen_urls) == 1 and seen_urls[0].endswith(expected_suffix),
                seen_urls[0] if seen_urls else "(no url)",
            )
            check(
                "API Chinese filename URL is ASCII-safe",
                all(ord(c) < 128 for c in seen_urls[0]),
                seen_urls[0] if seen_urls else "(no url)",
            )

            # 回归：AtomGit resolve 路由对「子目录+中文文件名」的百分号编码
            # 路径无法命中（404），但原始 UTF-8 字节路径可命中；编码 URL 全部
            # 404 时必须回退到原始字节 URL 下载。
            original_raw_download = api_mod._atomgit_download_raw
            raw_calls = []

            def fake_raw_download(url, dest, headers, timeout=60, max_redirects=5):
                raw_calls.append(url)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(b"raw-content")

            def not_found_urlopen(req, timeout=None):
                raise api_mod.urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)

            api_mod._atomgit_download_raw = fake_raw_download
            api_mod.urllib.request.urlopen = not_found_urlopen
            try:
                raw_calls.clear()
                original_api_fetch(
                    "user/repo", "model", "sub/中文样本.csv",
                    Path(local_dir) / "sub" / "中文样本.csv", "fake-token",
                )
            finally:
                api_mod.urllib.request.urlopen = original_urlopen
                api_mod._atomgit_download_raw = original_raw_download
            check(
                "API nested Chinese file falls back to raw URL",
                len(raw_calls) == 1 and "sub/中文样本.csv" in raw_calls[0],
                raw_calls[0] if raw_calls else "(no raw call)",
            )
            check(
                "API nested Chinese raw fallback writes file",
                (Path(local_dir) / "sub" / "中文样本.csv").read_text() == "raw-content",
            )
            raw_url = api_mod._atomgit_resolve_url_raw("user/repo", "model", "sub/中文样本.csv")
            check(
                "API raw resolve URL keeps raw filename",
                raw_url.endswith("/resolve/main/sub/中文样本.csv"),
                raw_url,
            )
            check(
                "API raw resolve URL is non-ASCII",
                any(ord(ch) > 127 for ch in raw_url),
            )

            # ASCII 文件名不应触发原始字节回退。
            seen_ascii = []

            def ok_urlopen(req, timeout=None):
                seen_ascii.append(req.full_url)
                return FakeHttpResponse()

            def forbidden_raw(url, dest, headers, timeout=60, max_redirects=5):
                raise AssertionError("raw fallback must not run for ASCII names")

            api_mod._atomgit_download_raw = forbidden_raw
            api_mod.urllib.request.urlopen = ok_urlopen
            try:
                original_api_fetch(
                    "user/repo", "model", "config.json",
                    Path(local_dir) / "config.json", "fake-token",
                )
            finally:
                api_mod.urllib.request.urlopen = original_urlopen
                api_mod._atomgit_download_raw = original_raw_download
            check(
                "API ASCII filename never uses raw fallback",
                len(seen_ascii) == 1 and seen_ascii[0].endswith("/resolve/main/config.json"),
                seen_ascii[0] if seen_ascii else "(no url)",
            )

    finally:
        api_mod.snapshot_download = original_api_snapshot
        api_mod._atomgit_list_repo_files = original_api_list
        api_mod._download_atomgit_file = original_api_fetch
        api_mod.config.get_credentials = original_credentials

    original_cli_download = cli_mod.api.download_repo
    original_logged_in = cli_mod.config.is_logged_in
    cli_calls = []
    cli_mod.config.is_logged_in = lambda: False
    cli_mod.api.download_repo = lambda repo_id, local_path, force_download=False: (
        cli_calls.append((repo_id, Path(local_path), force_download)) or True
    )
    try:
        runner = CliRunner()
        with runner.isolated_filesystem():
            default_result = runner.invoke(cli_mod.cli, ["download", "user/repo"])
            check("CLI default download succeeds", default_result.exit_code == 0)
            check("CLI default directory uses repo name", cli_calls[-1][1].name == "repo")
            explicit_result = runner.invoke(
                cli_mod.cli,
                ["download", "user/repo", "--directory", "target", "--force"],
            )
            check("CLI explicit force succeeds", explicit_result.exit_code == 0)
            check("CLI explicit directory forwarded", cli_calls[-1][1].name == "target")
            check("CLI force forwarded", cli_calls[-1][2] is True)

            cli_mod.api.download_repo = lambda *args, **kwargs: False
            failed = runner.invoke(cli_mod.cli, ["download", "user/repo", "-d", "failed"])
            check("CLI failed download exits nonzero", failed.exit_code == 1)
            check("CLI anonymous failure gives login guidance", "login" in failed.output)
    finally:
        cli_mod.api.download_repo = original_cli_download
        cli_mod.config.is_logged_in = original_logged_in

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
