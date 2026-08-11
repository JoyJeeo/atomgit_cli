#!/usr/bin/env python3
"""Bind AtomGit's representative calls to the locked dependency signatures."""

import inspect

import datasets
import huggingface_hub
from huggingface_hub import (
    HfApi,
    create_repo,
    get_hf_file_metadata,
    hf_hub_download,
    snapshot_download,
    upload_file,
    upload_folder,
)
from huggingface_hub.file_download import http_get
from huggingface_hub.utils import filter_repo_objects


results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def binds(callable_obj, *args, **kwargs):
    try:
        inspect.signature(callable_obj).bind(*args, **kwargs)
    except TypeError as error:
        return False, str(error)
    return True, ""


def main():
    check(
        "locked huggingface-hub version",
        huggingface_hub.__version__ == "1.1.7",
        huggingface_hub.__version__,
    )
    check(
        "locked datasets version",
        datasets.__version__ == "4.4.1",
        datasets.__version__,
    )

    calls = [
        (
            "upload_file contract",
            upload_file,
            (),
            {
                "path_or_fileobj": "/tmp/file.bin",
                "path_in_repo": "weights/file.bin",
                "repo_id": "user/repo",
                "token": "fake-token",
                "repo_type": "model",
                "revision": "main",
                "commit_message": "upload file",
            },
        ),
        (
            "upload_folder contract",
            upload_folder,
            (),
            {
                "repo_id": "user/repo",
                "folder_path": "/tmp/folder",
                "path_in_repo": "data",
                "commit_message": "upload folder",
                "commit_description": "offline contract",
                "token": "fake-token",
                "repo_type": "model",
                "revision": "main",
                "ignore_patterns": ["*.tmp"],
            },
        ),
        (
            "snapshot_download contract",
            snapshot_download,
            ("user/repo",),
            {
                "repo_type": "model",
                "revision": "main",
                "local_dir": "/tmp/download",
                "force_download": False,
                "token": "fake-token",
                "allow_patterns": ["*.json"],
                "ignore_patterns": ["*.tmp"],
            },
        ),
        (
            "hf_hub_download contract",
            hf_hub_download,
            ("user/repo", "README.md"),
            {
                "repo_type": "model",
                "revision": "main",
                "local_dir": "/tmp/download",
                "force_download": False,
                "token": "fake-token",
            },
        ),
        (
            "file metadata contract",
            get_hf_file_metadata,
            ("https://hub.atomgit.com/user/repo/resolve/main/file.bin",),
            {
                "token": False,
                "timeout": 60,
                "endpoint": "https://hub.atomgit.com",
            },
        ),
        (
            "resumable HTTP download contract",
            http_get,
            ("https://cdn.example/file.bin", object()),
            {
                "resume_size": 10,
                "headers": {"Range": "bytes=10-"},
                "expected_size": 100,
                "displayed_filename": "file.bin",
            },
        ),
        (
            "create_repo contract",
            create_repo,
            ("user/repo",),
            {
                "token": "fake-token",
                "private": True,
                "repo_type": "model",
                "exist_ok": True,
            },
        ),
        (
            "HfApi authentication contract",
            HfApi.__init__,
            (None,),
            {"endpoint": "https://hub.atomgit.com", "token": "fake-token"},
        ),
        (
            "upload_large_folder contract",
            HfApi.upload_large_folder,
            (None, "user/repo", "/tmp/folder"),
            {
                "repo_type": "model",
                "revision": "main",
                "ignore_patterns": ["*.tmp"],
                "num_workers": 2,
            },
        ),
        (
            "read-only resumable target validation contract",
            HfApi.list_repo_tree,
            (None, "user/repo"),
            {
                "revision": "main",
                "repo_type": None,
                "recursive": False,
            },
        ),
        (
            "upload projection filtering contract",
            filter_repo_objects,
            (["a.txt", "logs/a.txt"],),
            {"ignore_patterns": ["logs/"], "key": lambda item: item},
        ),
    ]

    for name, callable_obj, args, kwargs in calls:
        ok, detail = binds(callable_obj, *args, **kwargs)
        check(name, ok, detail)

    ok, detail = binds(
        HfApi.upload_large_folder,
        None,
        "user/repo",
        "/tmp/folder",
        repo_type="model",
        token="fake-token",
    )
    check(
        "upload_large_folder rejects method token",
        not ok and "token" in detail,
        detail,
    )

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
