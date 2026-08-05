#!/usr/bin/env python3
"""All CLI/API/SDK boundaries share one multi-level repository ID mapping."""

import contextlib
import io
import sys
import tempfile
from pathlib import Path

import atomgit  # noqa: F401
import atomgit_hub
from atomgit.utils import normalize_repo_id


api_mod = sys.modules["atomgit.api"]
config = sys.modules["atomgit.config"].config
RAW_ID = "org/namespace/repository/variant"
NORMALIZED_ID = "org-namespace/repository/variant"
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        single = normalize_repo_id("repo")
        two_level = normalize_repo_id("owner/repo")
        multi_level = normalize_repo_id(RAW_ID)
    check("single-level ID unchanged", single == "repo")
    check("two-level ID unchanged", two_level == "owner/repo")
    check("multi-level ID maps first separator", multi_level == NORMALIZED_ID)
    check("normalization itself is silent", output.getvalue() == "")

    original_credentials = config.get_credentials
    original_create = api_mod.create_repo
    original_file_upload = api_mod.hf_upload_file
    original_folder_upload = api_mod.upload_folder
    original_snapshot = api_mod.snapshot_download
    original_api_list = api_mod._atomgit_list_repo_files
    original_api_fetch = api_mod._download_atomgit_file
    api_calls = {}
    config.get_credentials = lambda: {"token": "fake-token"}
    api_mod.create_repo = lambda **kwargs: api_calls.setdefault("create", kwargs)
    api_mod.hf_upload_file = lambda **kwargs: api_calls.setdefault("file", kwargs)
    api_mod.upload_folder = lambda **kwargs: api_calls.setdefault("folder", kwargs)

    def fake_list(repo_id, token, repo_type=None):
        api_calls.setdefault("download", {})["repo_id"] = repo_id
        return "model", ["file.bin"]

    def fake_fetch(repo_id, repo_type, filename, dest, token):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"content")

    api_mod._atomgit_list_repo_files = fake_list
    api_mod._download_atomgit_file = fake_fetch

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_file = root / "file.bin"
            source_file.write_bytes(b"content")
            source_folder = root / "folder"
            source_folder.mkdir()
            (source_folder / "data.txt").write_text("data", encoding="utf-8")

            check("API create succeeds", api_mod.api.create_repo(RAW_ID, private=True))
            check("API file upload succeeds", api_mod.api.upload_folder(source_file, RAW_ID))
            check("API directory upload succeeds", api_mod.api.upload_directory(source_folder, RAW_ID))
            check("API snapshot download succeeds", api_mod.api.download_repo(RAW_ID, root / "download"))
        for operation in ("create", "file", "folder", "download"):
            check(
                f"API {operation} uses normalized ID",
                api_calls[operation]["repo_id"] == NORMALIZED_ID,
            )
    finally:
        config.get_credentials = original_credentials
        api_mod.create_repo = original_create
        api_mod.hf_upload_file = original_file_upload
        api_mod.upload_folder = original_folder_upload
        api_mod.snapshot_download = original_snapshot
        api_mod._atomgit_list_repo_files = original_api_list
        api_mod._download_atomgit_file = original_api_fetch

    original_sdk_token = atomgit_hub._get_token
    original_sdk_snapshot = atomgit_hub.hf_snapshot_download
    original_sdk_file = atomgit_hub.hf_hub_download
    original_sdk_upload = atomgit_hub.hf_upload_folder
    original_sdk_create = atomgit_hub.create_repo
    original_dataset_loader = atomgit_hub.ds_load_dataset
    sdk_calls = {}
    atomgit_hub._get_token = lambda: "fake-token"
    atomgit_hub.hf_snapshot_download = lambda **kwargs: sdk_calls.setdefault("snapshot", kwargs) or "/tmp/snapshot"
    atomgit_hub.hf_hub_download = lambda **kwargs: sdk_calls.setdefault("file", kwargs) or "/tmp/file"
    atomgit_hub.hf_upload_folder = lambda **kwargs: sdk_calls.setdefault("upload", kwargs) or "commit"
    atomgit_hub.create_repo = lambda **kwargs: sdk_calls.setdefault("create", kwargs) or "repo-url"

    def dataset_snapshot(**kwargs):
        sdk_calls["dataset"] = kwargs
        return "/tmp/dataset"

    atomgit_hub.ds_load_dataset = lambda **kwargs: {"loaded": kwargs["path"]}
    try:
        check("SDK snapshot succeeds", bool(atomgit_hub.snapshot_download(RAW_ID)))
        check("SDK file download succeeds", bool(atomgit_hub.download_file(RAW_ID, "README.md")))
        with tempfile.TemporaryDirectory() as source_dir:
            source = Path(source_dir)
            (source / "file.txt").write_text("content", encoding="utf-8")
            check(
                "SDK upload succeeds",
                bool(atomgit_hub.upload_folder(source, RAW_ID, token="fake-token")),
            )
        check(
            "SDK create succeeds",
            bool(
                atomgit_hub.create_repository(
                    RAW_ID, token="fake-token", private=True
                )
            ),
        )
        url = atomgit_hub.hub_download_url(RAW_ID, "README.md")
        check("SDK URL uses normalized ID", f"/{NORMALIZED_ID}/" in url)

        atomgit_hub.hf_snapshot_download = dataset_snapshot
        dataset = atomgit_hub.load_dataset(RAW_ID, token="fake-token")
        check("SDK dataset load succeeds", dataset == {"loaded": "/tmp/dataset"})

        for operation in ("snapshot", "file", "upload", "create", "dataset"):
            check(
                f"SDK {operation} uses normalized ID",
                sdk_calls[operation]["repo_id"] == NORMALIZED_ID,
            )
    finally:
        atomgit_hub._get_token = original_sdk_token
        atomgit_hub.hf_snapshot_download = original_sdk_snapshot
        atomgit_hub.hf_hub_download = original_sdk_file
        atomgit_hub.hf_upload_folder = original_sdk_upload
        atomgit_hub.create_repo = original_sdk_create
        atomgit_hub.ds_load_dataset = original_dataset_loader

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
