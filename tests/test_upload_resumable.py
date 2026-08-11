#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI resumable-upload defaults and repository-prefix regressions.

All upload entry points and multiprocessing are replaced with strict inline
fakes. No remote repository or real credential is accessed.
"""

import os
import queue
import sys
import tempfile
from pathlib import Path

from click.testing import CliRunner

import atomgit  # noqa: F401


api_mod = sys.modules["atomgit.api"]
cfg_mod = sys.modules["atomgit.config"]
from atomgit.cli import cli


results = []
uf_captured = []
ulf_captured = []
hfa_init_captured = []
validation_captured = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def fake_upload_folder(**kwargs):
    uf_captured.append(dict(kwargs))
    return "fake-commit-url"


class FakeHfApi:
    """Match the locked HF 1.1.7 large-folder signatures used by AtomGit."""

    def __init__(self, endpoint=None, token=None, library_name=None,
                 library_version=None, user_agent=None, headers=None):
        hfa_init_captured.append({"endpoint": endpoint, "token": token})

    def upload_large_folder(self, repo_id, folder_path, *, repo_type,
                            revision=None, private=None, allow_patterns=None,
                            ignore_patterns=None, num_workers=None,
                            print_report=True, print_report_every=60):
        root = Path(folder_path)
        metadata = root / ".cache" / "huggingface" / "upload" / "sentinel"
        visible_files = sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
            and not path.relative_to(root).as_posix().startswith(
                ".cache/huggingface/"
            )
        )
        ulf_captured.append({
            "repo_id": repo_id,
            "folder_path": folder_path,
            "repo_type": repo_type,
            "revision": revision,
            "private": private,
            "allow_patterns": allow_patterns,
            "ignore_patterns": ignore_patterns,
            "num_workers": num_workers,
            "print_report": print_report,
            "print_report_every": print_report_every,
            "visible_files": visible_files,
            "metadata_present": metadata.exists(),
        })


class InlineQueue:
    def __init__(self):
        self._queue = queue.Queue()

    def put(self, value):
        self._queue.put(value)

    def get(self, timeout=None):
        return self._queue.get(timeout=timeout)


class InlineProcess:
    def __init__(self, target, args):
        self._target = target
        self._args = args
        self.daemon = False
        self._alive = False

    def start(self):
        self._alive = True
        try:
            self._target(*self._args)
        finally:
            self._alive = False

    def join(self, timeout=None):
        return None

    def is_alive(self):
        return self._alive

    def terminate(self):
        self._alive = False


class InlineContext:
    def Queue(self):
        return InlineQueue()

    def Process(self, target, args):
        return InlineProcess(target, args)


def main():
    original_upload_folder = api_mod.upload_folder
    original_upload_file = api_mod.hf_upload_file
    original_hf_api = api_mod.HfApi
    original_methods = api_mod.multiprocessing.get_all_start_methods
    original_context = api_mod.multiprocessing.get_context
    original_hf_home = os.environ.get("HF_HOME")
    original_v5_get = api_mod._atomgit_v5_get_json

    def fake_v5_get(path, token, timeout=15):
        validation_captured.append({
            "path": path,
            "token": token,
            "timeout": timeout,
        })
        if "/branches/" in path:
            return {"name": path.rsplit("/", 1)[-1]}
        return {"full_name": path.removeprefix("/repos/"),
                "default_branch": "main"}

    api_mod.upload_folder = fake_upload_folder
    api_mod.hf_upload_file = fake_upload_folder
    api_mod.HfApi = FakeHfApi
    api_mod._atomgit_v5_get_json = fake_v5_get
    api_mod.multiprocessing.get_all_start_methods = lambda: ["fork"]
    api_mod.multiprocessing.get_context = lambda method: InlineContext()
    cfg_mod.config.is_logged_in = lambda: True
    cfg_mod.config.get_credentials = lambda: {"token": "fake-token-never-print"}

    try:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            os.environ["HF_HOME"] = str(root / "atomgit-cache")
            source_file = root / "file.bin"
            source_file.write_bytes(b"file")
            source = root / "modeldir"
            source.mkdir()
            (source / "a.txt").write_text("a", encoding="utf-8")
            (source / "b.txt").write_text("b", encoding="utf-8")

            runner = CliRunner()

            # Directory uploads automatically select resumable mode.
            uf_captured.clear(); ulf_captured.clear(); hfa_init_captured.clear()
            validation_captured.clear()
            result = runner.invoke(
                cli, ["upload", str(source), "--repo-id", "user/repo"]
            )
            check("T1 default directory succeeds", result.exit_code == 0)
            check(
                "T1 default directory uses upload_large_folder",
                len(ulf_captured) == 1 and not uf_captured,
                f"large={len(ulf_captured)} ordinary={len(uf_captured)}",
            )
            if ulf_captured:
                check("T1 default repo type is model", ulf_captured[0]["repo_type"] == "model")
                check("T1 private projection is used at repository root",
                      ulf_captured[0]["folder_path"] != str(source))
                check("T1 root projection preserves relative file paths",
                      ulf_captured[0]["visible_files"] == ["a.txt", "b.txt"])
                check("T1 HfApi constructor receives token",
                      len(hfa_init_captured) == 1
                      and all(bool(call["token"]) for call in hfa_init_captured))
                check("T1 target is validated once before large-folder upload",
                      validation_captured == [{
                          "path": "/repos/user/repo",
                          "token": "fake-token-never-print",
                          "timeout": 300.0,
                      }])
                first_projection = ulf_captured[0]["folder_path"]
                root_sentinel = (
                    Path(first_projection) / ".cache" / "huggingface"
                    / "upload" / "sentinel"
                )
                root_sentinel.parent.mkdir(parents=True, exist_ok=True)
                root_sentinel.write_text("root-resume-state", encoding="utf-8")
                repeated_root = runner.invoke(
                    cli, ["upload", str(source), "--repo-id", "user/repo"]
                )
                check("T1 repeated root upload succeeds", repeated_root.exit_code == 0)
                check("T1 root upload reuses projection and metadata",
                      ulf_captured[-1]["folder_path"] == first_projection
                      and ulf_captured[-1]["metadata_present"])
                other_repo = runner.invoke(
                    cli, ["upload", str(source), "--repo-id", "user/other"]
                )
                check("T1 second repository upload succeeds", other_repo.exit_code == 0)
                check("T1 repositories have isolated resume state",
                      ulf_captured[-1]["folder_path"] != first_projection)
                check("T1 source tree is not polluted by HF metadata",
                      not (source / ".cache" / "huggingface").exists())

            # An explicit opt-out preserves the ordinary upload-folder path.
            uf_captured.clear(); ulf_captured.clear()
            result = runner.invoke(
                cli,
                ["upload", str(source), "--repo-id", "user/repo", "--no-resumable"],
            )
            check("T2 --no-resumable succeeds", result.exit_code == 0)
            check("T2 --no-resumable uses upload_folder",
                  len(uf_captured) == 1 and not ulf_captured)

            # Dataset keeps the verified AtomGit model compatibility route.
            uf_captured.clear(); ulf_captured.clear()
            result = runner.invoke(
                cli,
                ["upload", str(source), "--repo-id", "user/repo",
                 "--repo-type", "dataset"],
            )
            check("T3 default dataset resumable succeeds", result.exit_code == 0)
            if ulf_captured:
                check("T3 dataset uses model transfer route",
                      ulf_captured[0]["repo_type"] == "model")

            # Existing explicit resumable options remain supported.
            uf_captured.clear(); ulf_captured.clear()
            result = runner.invoke(
                cli,
                ["upload", str(source), "--repo-id", "user/repo", "--resumable",
                 "--revision", "dev", "--ignore", "*.tmp", "--num-workers", "4"],
            )
            check("T4 explicit resumable options succeed", result.exit_code == 0)
            if ulf_captured:
                call = ulf_captured[0]
                check("T4 revision forwarded", call["revision"] == "dev")
                check("T4 ignore patterns forwarded", call["ignore_patterns"] == ["*.tmp"])
                check("T4 worker count forwarded", call["num_workers"] == 4)

            # path-in-repo uses one stable projection and preserves HF metadata.
            uf_captured.clear(); ulf_captured.clear()
            (source / "ignored.tmp").write_text("ignored", encoding="utf-8")
            (source / "logs").mkdir()
            (source / "logs" / "run.log").write_text("ignored", encoding="utf-8")
            prefixed_args = [
                "upload", str(source), "--repo-id", "user/repo",
                "--path-in-repo", "weights/checkpoints/",
                "--ignore", "*.tmp,logs/",
            ]
            first = runner.invoke(cli, prefixed_args)
            check("T5 resumable path-in-repo succeeds", first.exit_code == 0,
                  f"exit={first.exit_code}")
            first_call = ulf_captured[-1] if ulf_captured else None
            if first_call:
                projection = Path(first_call["folder_path"])
                check("T5 projection differs from source", projection != source)
                check(
                    "T5 projection exposes only prefixed files",
                    first_call["visible_files"]
                    == ["weights/checkpoints/a.txt", "weights/checkpoints/b.txt"],
                    repr(first_call["visible_files"]),
                )
                check(
                    "T5 ignore patterns are relative to projected prefix",
                    first_call["ignore_patterns"]
                    == ["weights/checkpoints/*.tmp", "weights/checkpoints/logs/"],
                    repr(first_call["ignore_patterns"]),
                )
                sentinel = projection / ".cache" / "huggingface" / "upload" / "sentinel"
                sentinel.parent.mkdir(parents=True, exist_ok=True)
                sentinel.write_text("resume-state", encoding="utf-8")
                (source / "a.txt").write_text("changed", encoding="utf-8")
                (source / "b.txt").unlink()
                (source / "c.txt").write_text("c", encoding="utf-8")

                second = runner.invoke(cli, prefixed_args)
                check("T5 repeated prefixed upload succeeds", second.exit_code == 0)
                second_call = ulf_captured[-1]
                check("T5 repeated upload reuses projection",
                      second_call["folder_path"] == first_call["folder_path"])
                check("T5 HF resume metadata survives synchronization",
                      second_call["metadata_present"])
                check(
                    "T5 projection reflects changed and removed files",
                    second_call["visible_files"]
                    == ["weights/checkpoints/a.txt", "weights/checkpoints/c.txt"],
                    repr(second_call["visible_files"]),
                )
                check(
                    "T5 changed content is visible",
                    (projection / "weights" / "checkpoints" / "a.txt").read_text(
                        encoding="utf-8"
                    ) == "changed",
                )

            # A .cache prefix must preserve the projection-root HF metadata.
            uf_captured.clear(); ulf_captured.clear()
            cache_prefix_args = [
                "upload", str(source), "--repo-id", "user/repo",
                "--path-in-repo", ".cache",
            ]
            first_cache = runner.invoke(cli, cache_prefix_args)
            check("T5b .cache prefix succeeds", first_cache.exit_code == 0)
            if ulf_captured:
                cache_projection = Path(ulf_captured[-1]["folder_path"])
                cache_sentinel = (
                    cache_projection / ".cache" / "huggingface"
                    / "upload" / "sentinel"
                )
                cache_sentinel.parent.mkdir(parents=True, exist_ok=True)
                cache_sentinel.write_text("cache-prefix-state", encoding="utf-8")
                repeated_cache = runner.invoke(cli, cache_prefix_args)
                check("T5b repeated .cache prefix succeeds",
                      repeated_cache.exit_code == 0)
                check("T5b .cache prefix preserves HF metadata",
                      ulf_captured[-1]["metadata_present"])

                conflict = source / "huggingface"
                conflict.mkdir()
                (conflict / "payload.bin").write_bytes(b"conflict")
                call_count = len(ulf_captured)
                conflict_result = runner.invoke(cli, cache_prefix_args)
                check("T5b metadata path collision is rejected",
                      conflict_result.exit_code == 1 and len(ulf_captured) == call_count)
                check("T5b collision guidance is actionable",
                      "--no-resumable" in conflict_result.output)
                check("T5b rejected collision retains metadata", cache_sentinel.exists())
                (conflict / "payload.bin").unlink()
                conflict.rmdir()

            reserved_result = runner.invoke(
                cli,
                ["upload", str(source), "--repo-id", "user/repo",
                 "--path-in-repo", ".cache/huggingface"],
            )
            check("T5c reserved HF prefix is rejected", reserved_result.exit_code == 1)
            check("T5c reserved prefix suggests ordinary upload",
                  "--no-resumable" in reserved_result.output)
            reserved_case_result = runner.invoke(
                cli,
                ["upload", str(source), "--repo-id", "user/repo",
                 "--path-in-repo", ".CACHE/HUGGINGFACE"],
            )
            check("T5c reserved prefix is case-insensitive",
                  reserved_case_result.exit_code == 1
                  and "--no-resumable" in reserved_case_result.output)

            # Files remain ordinary unless resumable is explicitly requested.
            uf_captured.clear(); ulf_captured.clear()
            result = runner.invoke(
                cli, ["upload", str(source_file), "--repo-id", "user/repo"]
            )
            check("T6 default file upload succeeds", result.exit_code == 0)
            check("T6 default file uses ordinary uploader",
                  len(uf_captured) == 1 and not ulf_captured)

            uf_captured.clear(); ulf_captured.clear()
            result = runner.invoke(
                cli,
                ["upload", str(source_file), "--repo-id", "user/repo", "--resumable"],
            )
            check("T7 file --resumable is rejected", result.exit_code == 2)
            check("T7 rejected file calls no uploader", not uf_captured and not ulf_captured)

            # A message without an explicit mode keeps ordinary commit semantics.
            uf_captured.clear(); ulf_captured.clear()
            result = runner.invoke(
                cli,
                ["upload", str(source), "--repo-id", "user/repo",
                 "--message", "release"],
            )
            check("T8 directory message succeeds", result.exit_code == 0)
            check("T8 message selects ordinary upload",
                  len(uf_captured) == 1 and not ulf_captured)
            if uf_captured:
                check("T8 message is forwarded",
                      uf_captured[0]["commit_message"] == "release")

            # Workers can tune the automatic resumable mode.
            uf_captured.clear(); ulf_captured.clear()
            result = runner.invoke(
                cli,
                ["upload", str(source), "--repo-id", "user/repo",
                 "--num-workers", "2"],
            )
            check("T9 workers accepted for default resumable mode", result.exit_code == 0)
            if ulf_captured:
                check("T9 worker count forwarded", ulf_captured[0]["num_workers"] == 2)
    finally:
        api_mod.upload_folder = original_upload_folder
        api_mod.hf_upload_file = original_upload_file
        api_mod.HfApi = original_hf_api
        api_mod.multiprocessing.get_all_start_methods = original_methods
        api_mod.multiprocessing.get_context = original_context
        api_mod._atomgit_v5_get_json = original_v5_get
        if original_hf_home is None:
            os.environ.pop("HF_HOME", None)
        else:
            os.environ["HF_HOME"] = original_hf_home

    print("\n" + "=" * 50)
    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
