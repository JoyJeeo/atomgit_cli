#!/usr/bin/env python3
"""Contract tests for loading AtomGit datasets through a local snapshot."""

import sys
import tempfile
from pathlib import Path

import atomgit_hub


results = []
snapshot_calls = []
load_calls = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" +
          (f" -> {detail}" if detail else ""))


def fake_snapshot_download(**kwargs):
    snapshot_calls.append(dict(kwargs))
    return "/stable/cache/dataset-snapshot"


def fake_load_dataset(**kwargs):
    load_calls.append(dict(kwargs))
    return {"loaded": True}


def main():
    original_snapshot = atomgit_hub.hf_snapshot_download
    original_loader = atomgit_hub.ds_load_dataset
    original_get_token = atomgit_hub._get_token
    atomgit_hub.hf_snapshot_download = fake_snapshot_download
    atomgit_hub.ds_load_dataset = fake_load_dataset
    atomgit_hub._get_token = lambda: "fake-token-never-print"
    try:
        with tempfile.TemporaryDirectory() as td:
            result = atomgit_hub.load_dataset(
                "user/dataset",
                name="default",
                data_dir="data",
                data_files={"train": ["train*.csv"], "test": "test.csv"},
                split="train",
                cache_dir=Path(td),
                streaming=True,
                revision="dev",
                keep_in_memory=True,
            )
        check("T1 wrapper returns datasets result", result == {"loaded": True})
        call = snapshot_calls[0]
        check("T2 snapshot uses dataset repo type", call.get("repo_type") == "dataset")
        check("T3 snapshot receives stored token", bool(call.get("token")))
        check("T4 snapshot receives revision", call.get("revision") == "dev")
        check("T5 snapshot resolves data_files relative to data_dir",
              call.get("allow_patterns") == [
                  "data/train*.csv", "data/test.csv"
              ],
              repr(call.get("allow_patterns")))
        load_call = load_calls[0]
        check("T6 datasets loads stable local snapshot",
              load_call.get("path") == "/stable/cache/dataset-snapshot")
        check("T7 public arguments are preserved",
              load_call.get("name") == "default"
              and load_call.get("data_dir") == "data"
              and load_call.get("split") == "train"
              and load_call.get("streaming") is True
              and load_call.get("keep_in_memory") is True)
        check("T8 remote-only arguments are not forwarded locally",
              "token" not in load_call and "revision" not in load_call)
    finally:
        atomgit_hub.hf_snapshot_download = original_snapshot
        atomgit_hub.ds_load_dataset = original_loader
        atomgit_hub._get_token = original_get_token

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
