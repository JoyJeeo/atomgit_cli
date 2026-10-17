#!/usr/bin/env python3
"""SDK upload parameters reach the strict Hugging Face 1.1.7 boundary."""

import inspect
import tempfile
import warnings
from pathlib import Path

import atomgit_hub
from huggingface_hub import upload_folder as real_upload_folder


results = []
HF_DATASET_REPO_WARNING = (
    "It seems that you are about to commit a data file (records/data.parquet) "
    "to a model repository. You are sure this is intended? If you are trying "
    "to upload a dataset, please set `repo_type='dataset'` or "
    "`--repo-type=dataset` in a CLI."
)


def warn_hf_dataset_repo():
    warnings.warn_explicit(
        HF_DATASET_REPO_WARNING,
        UserWarning,
        filename="huggingface_hub/hf_api.py",
        lineno=1,
        module="huggingface_hub.hf_api",
    )


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def path_boundary_checks():
    from unittest.mock import patch

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "source"
        source.mkdir()
        (source / "fixture.txt").write_text("fixture", encoding="utf-8")
        for prefix in ("stage/../../escape", "stage\\..\\escape"):
            with (
                patch("shutil.copytree") as copy,
                patch.object(atomgit_hub, "hf_upload_folder") as upload,
            ):
                try:
                    atomgit_hub.upload_folder(
                        source, "fake/repo", token="fake-token", path_in_repo=prefix
                    )
                except ValueError:
                    rejected = True
                else:
                    rejected = False
                check(
                    "traversal rejected before copy or upload",
                    rejected and not copy.called and not upload.called,
                )
        seen = []

        def capture(**kwargs):
            seen.append(
                (Path(kwargs["folder_path"]) / ".records" / "fixture.txt").is_file()
            )
            return "commit"

        with patch.object(atomgit_hub, "hf_upload_folder", capture):
            atomgit_hub.upload_folder(
                source, "fake/repo", token="fake-token", path_in_repo=".records/"
            )
        check("legal dot-prefixed destination is preserved", seen == [True])


def native_option_checks():
    from unittest.mock import patch

    from huggingface_hub import HfApi, close_session, get_session
    from huggingface_hub.utils import are_progress_bars_disabled

    from atomgit.interfaces.sdk import AtomGitClient

    class Config:
        def get_credentials(self):
            return None

    calls = []

    def commit(client, repo_id, operations, **kwargs):
        calls.append(
            (
                kwargs.get("num_threads"),
                are_progress_bars_disabled(),
                get_session().timeout.read,
            )
        )
        return "commit"

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        file = root / "data.txt"
        file.write_text("fixture", encoding="utf-8")
        client = AtomGitClient(config=Config())
        with (
            patch.object(HfApi, "create_commit", commit),
            patch(
                "socket.socket.connect", side_effect=AssertionError("offline network")
            ),
        ):
            client.upload_folder(
                root,
                "fake/repo",
                token="fake-token",
                progress=False,
                num_workers=2,
                timeout=41,
            )
            check(
                "native ordinary folder options reach real HF commit boundary",
                calls[-1] == (2, True, 41),
            )
            client.upload_file(
                file,
                "fake/repo",
                token="fake-token",
                progress=False,
                num_workers=3,
                timeout=42,
            )
            check(
                "native file options reach real HF commit boundary",
                calls[-1] == (3, True, 42),
            )
            before = len(calls)
            try:
                client.upload_folder(
                    root, "fake/repo", token="fake-token", auto_configure_lfs=True
                )
            except ValueError:
                rejected = True
            else:
                rejected = False
            check(
                "ordinary SDK rejects unsupported automatic LFS before upload",
                rejected and len(calls) == before,
            )
    close_session()


def main():
    native_option_checks()

    path_boundary_checks()

    original_upload = atomgit_hub.hf_upload_folder
    calls = []

    def strict_upload(**kwargs):
        inspect.signature(real_upload_folder).bind(**kwargs)
        warn_hf_dataset_repo()
        check(
            "upload source exists at strict boundary",
            Path(kwargs["folder_path"]).exists(),
        )
        calls.append(kwargs)
        return "commit-url"

    atomgit_hub.hf_upload_folder = strict_upload
    try:
        with tempfile.TemporaryDirectory() as source_dir:
            source = Path(source_dir)
            (source / "data.parquet").write_bytes(b"offline parquet fixture")

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                result = atomgit_hub.upload_folder(
                    source,
                    "team/dataset",
                    token="fake-token",
                    repo_type="dataset",
                    revision="main",
                    commit_message="upload data",
                    commit_description="offline parameter contract",
                    path_in_repo="records/",
                    ignore_patterns=["*.tmp", "logs/"],
                )
            check("SDK result preserved", result == "commit-url")
            check("legacy dataset warning is suppressed", not caught)
            call = calls[-1]
            check(
                "dataset uses compatible model transfer route",
                call.get("repo_type") == "model",
            )
            check("main revision forwarded", call.get("revision") == "main")
            check(
                "commit description forwarded",
                call.get("commit_description") == "offline parameter contract",
            )
            check(
                "source-relative ignores follow the staged repository prefix",
                call.get("ignore_patterns") == ["records/*.tmp", "records/logs/"],
                repr(call.get("ignore_patterns")),
            )
            check("commit message forwarded", call.get("commit_message") == "upload data")

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                atomgit_hub.upload_folder(
                    source,
                    "team/model",
                    token="fake-token",
                    repo_type="model",
                )
            check("model type forwarded", calls[-1].get("repo_type") == "model")
            check("unset revision omitted", "revision" not in calls[-1])
            check(
                "legacy model warning remains visible",
                len(caught) == 1 and str(caught[0].message) == HF_DATASET_REPO_WARNING,
            )

            before = len(calls)
            try:
                atomgit_hub.upload_folder(
                    source,
                    "team/model",
                    token="fake-token",
                    revision="dev",
                )
            except ValueError as error:
                check("non-main revision is actionable", "main" in str(error))
            else:
                check("non-main revision is actionable", False, "no exception")
            check("non-main revision makes no HF call", len(calls) == before)

            try:
                atomgit_hub.upload_folder(
                    source,
                    "team/model",
                    token="fake-token",
                    repo_type="space",
                )
            except ValueError as error:
                check("unsupported repo type is actionable", "model" in str(error))
            else:
                check("unsupported repo type is actionable", False, "no exception")
            check("unsupported repo type makes no HF call", len(calls) == before)
    finally:
        atomgit_hub.hf_upload_folder = original_upload

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
