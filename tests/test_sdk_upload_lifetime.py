#!/usr/bin/env python3
"""SDK subdirectory uploads keep temporary content alive through the HF call."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import atomgit_hub


results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    original_upload = atomgit_hub.hf_upload_folder
    captured_paths = []
    try:
        with tempfile.TemporaryDirectory() as source_dir:
            source = Path(source_dir)
            (source / "weights.bin").write_bytes(b"weights")

            def successful_upload(**kwargs):
                upload_path = Path(kwargs["folder_path"])
                captured_paths.append(upload_path)
                check("temporary tree exists during call", upload_path.is_dir())
                check(
                    "temporary tree contains nested source",
                    (upload_path / "models" / "weights.bin").read_bytes()
                    == b"weights",
                )
                return "commit-url"

            atomgit_hub.hf_upload_folder = successful_upload
            result = atomgit_hub.upload_folder(
                source,
                "user/repo",
                token="fake-token",
                path_in_repo="models/",
            )
            check("successful upload result preserved", result == "commit-url")
            check(
                "temporary tree removed after success",
                len(captured_paths) == 1 and not captured_paths[-1].exists(),
            )

            def failing_upload(**kwargs):
                upload_path = Path(kwargs["folder_path"])
                captured_paths.append(upload_path)
                check("failure path exists during call", upload_path.is_dir())
                raise RuntimeError("offline failure")

            atomgit_hub.hf_upload_folder = failing_upload
            try:
                atomgit_hub.upload_folder(
                    source,
                    "user/repo",
                    token="fake-token",
                    path_in_repo="models/",
                )
            except Exception as error:
                check("HF failure remains actionable", "offline failure" in str(error))
            else:
                check("HF failure remains actionable", False, "no exception")
            check(
                "temporary tree removed after failure",
                len(captured_paths) == 2 and not captured_paths[-1].exists(),
            )

            preparation_paths = []

            class TrackingTemporaryDirectory(tempfile.TemporaryDirectory):
                def __init__(self):
                    super().__init__()
                    preparation_paths.append(Path(self.name))

            with patch(
                "tempfile.TemporaryDirectory", TrackingTemporaryDirectory
            ), patch("shutil.copytree", side_effect=OSError("copy failed")):
                try:
                    atomgit_hub.upload_folder(
                        source,
                        "user/repo",
                        token="fake-token",
                        path_in_repo="models/",
                    )
                except OSError as error:
                    check("preparation failure preserved", "copy failed" in str(error))
                else:
                    check("preparation failure preserved", False, "no exception")
            check(
                "temporary tree removed after preparation failure",
                len(preparation_paths) == 1 and not preparation_paths[0].exists(),
            )

            def root_upload(**kwargs):
                captured_paths.append(Path(kwargs["folder_path"]))
                return "root-commit"

            atomgit_hub.hf_upload_folder = root_upload
            result = atomgit_hub.upload_folder(
                source,
                "user/repo",
                token="fake-token",
            )
            check("root upload result preserved", result == "root-commit")
            check("root upload uses original directory", captured_paths[-1] == source)
    finally:
        atomgit_hub.hf_upload_folder = original_upload

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
