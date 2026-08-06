#!/usr/bin/env python3
"""Direct API uploads accept safe refs and reject ambiguous revision names."""

import sys
import tempfile
from pathlib import Path

import atomgit  # noqa: F401
import atomgit_hub
from atomgit.utils import is_supported_upload_revision


api_mod = sys.modules["atomgit.api"]
config = sys.modules["atomgit.config"].config
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    check("None revision supported", is_supported_upload_revision(None))
    check("empty revision supported", is_supported_upload_revision(""))
    check("main revision supported", is_supported_upload_revision("main"))
    check("dev revision supported", is_supported_upload_revision("dev"))
    check("malformed revision unsupported", not is_supported_upload_revision("bad..ref"))

    original_credentials = config.get_credentials
    original_file = api_mod.hf_upload_file
    original_folder = api_mod.upload_folder
    calls = []
    config.get_credentials = lambda: {"token": "fake-token"}
    api_mod.hf_upload_file = lambda **kwargs: calls.append(("file", kwargs))
    api_mod.upload_folder = lambda **kwargs: calls.append(("folder", kwargs))
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_file = root / "file.bin"
            source_file.write_bytes(b"content")
            source_folder = root / "folder"
            source_folder.mkdir()
            (source_folder / "data.txt").write_text("data", encoding="utf-8")

            check(
                "direct API file accepts dev",
                api_mod.api.upload_folder(source_file, "user/repo", revision="dev")
                is True,
            )
            check(
                "direct API directory accepts dev",
                api_mod.api.upload_directory(
                    source_folder, "user/repo", revision="dev"
                )
                is True,
            )
            check("dev API calls reach both HF paths", [item[0] for item in calls] == ["file", "folder"])

            before = len(calls)
            check("direct API rejects malformed ref", api_mod.api.upload_folder(source_file, "user/repo", revision="bad..ref") is False)
            check("malformed ref never reaches HF", len(calls) == before)

            check(
                "direct API file accepts main",
                api_mod.api.upload_folder(source_file, "user/repo", revision="main")
                is True,
            )
            check(
                "direct API directory accepts main",
                api_mod.api.upload_directory(
                    source_folder, "user/repo", revision="main"
                )
                is True,
            )
            check("main API calls reach both HF paths", [item[0] for item in calls[-2:]] == ["file", "folder"])

            error = None
            try:
                atomgit_hub.upload_folder(
                    source_folder,
                    "user/repo",
                    token="fake-token",
                    revision="dev",
                )
            except Exception as caught:
                error = caught
            check(
                "SDK dev uses unsupported exception",
                isinstance(error, atomgit_hub.AtomGitUnsupportedError),
            )
    finally:
        config.get_credentials = original_credentials
        api_mod.hf_upload_file = original_file
        api_mod.upload_folder = original_folder

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
