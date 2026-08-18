#!/usr/bin/env python3
"""Bind AtomGit's representative calls to the locked dependency signatures."""

import ast
import inspect
from pathlib import Path

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
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


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


def mapping_keys_in_function(path, function_name, variable_name):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    function = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
    )
    keys = set()
    for node in ast.walk(function):
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == variable_name
                for target in node.targets
            )
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "dict"
        ):
            keys.update(keyword.arg for keyword in node.value.keywords if keyword.arg)
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Subscript)
            and isinstance(node.targets[0].value, ast.Name)
            and node.targets[0].value.id == variable_name
            and isinstance(node.targets[0].slice, ast.Constant)
            and isinstance(node.targets[0].slice.value, str)
        ):
            keys.add(node.targets[0].slice.value)
    return keys


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

    production_contracts = (
        (
            "CLI upload_file production kwargs bind the locked signature",
            REPOSITORY_ROOT / "api.py",
            "upload_folder",
            "file_kwargs",
            upload_file,
        ),
        (
            "SDK upload_folder production kwargs bind the locked signature",
            REPOSITORY_ROOT / "atomgit_hub.py",
            "upload_folder",
            "upload_kwargs",
            upload_folder,
        ),
    )
    for name, path, function_name, variable_name, callable_obj in production_contracts:
        keys = mapping_keys_in_function(path, function_name, variable_name)
        ok, detail = binds(callable_obj, **{key: None for key in keys})
        check(name, ok and bool(keys), detail or repr(sorted(keys)))

    invalid_source = (
        (REPOSITORY_ROOT / "api.py").read_text(encoding="utf-8")
        + "\ndef _invalid_contract():\n"
        + "    file_kwargs = dict(path_or_fileobj=None, path_in_repo=None, "
        + "repo_id=None, token=None, unsupported=None)\n"
    )
    invalid_path = REPOSITORY_ROOT / "api.py"
    invalid_tree = ast.parse(invalid_source, filename=str(invalid_path))
    invalid_function = invalid_tree.body[-1]
    invalid_keys = {
        keyword.arg
        for node in ast.walk(invalid_function)
        if isinstance(node, ast.Call)
        for keyword in node.keywords
        if keyword.arg
    }
    ok, detail = binds(upload_file, **{key: None for key in invalid_keys})
    check(
        "an unsupported production dependency kwarg fails closed",
        not ok and "unsupported" in detail,
        detail,
    )

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
