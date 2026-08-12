#!/usr/bin/env python3
"""Offline contracts for opt-in remote Git LFS policy repair."""

import io
import inspect
import os
import stat
import sys
import tempfile
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

import httpx
from click.testing import CliRunner

import atomgit  # noqa: F401
from atomgit.cli import cli


api_mod = sys.modules["atomgit.api"]
cfg_mod = sys.modules["atomgit.config"]
results = []


def check(name, condition, detail=""):
    results.append(bool(condition))
    print(
        f"[{'PASS' if condition else 'FAIL'}] {name}"
        + (f" -> {detail}" if detail else "")
    )


class FakeUploadModeItem:
    def __init__(self, path, size, mode="regular"):
        self.paths = SimpleNamespace(path_in_repo=path)
        self.metadata = SimpleNamespace(size=size, upload_mode=mode)

    def pair(self):
        return self.paths, self.metadata


class FakeRemote:
    def __init__(self, content=None):
        self.content = content
        self.sha_index = 1
        self.uploads = []
        self.fail_before_write = None
        self.fail_after_write = None

    @property
    def sha(self):
        return f"{self.sha_index:040x}"

    def revision_sha(self, **kwargs):
        return self.sha

    def download(self, *, destination, **kwargs):
        if self.content is None:
            return False
        Path(destination).write_bytes(self.content)
        return True

    def api_type(self):
        remote = self

        class FakeHfApi:
            def __init__(self, endpoint=None, token=None):
                self.endpoint = endpoint
                self.token = token

            def upload_file(self, **kwargs):
                path = Path(kwargs["path_or_fileobj"])
                remote.uploads.append(
                    {
                        **kwargs,
                        "endpoint": self.endpoint,
                        "client_token": self.token,
                        "content": path.read_bytes(),
                        "path_exists": path.exists(),
                        "file_mode": stat.S_IMODE(path.stat().st_mode),
                        "parent_mode": stat.S_IMODE(path.parent.stat().st_mode),
                    }
                )
                if remote.fail_before_write is not None:
                    error, concurrent_content = remote.fail_before_write
                    remote.fail_before_write = None
                    remote.content = concurrent_content
                    remote.sha_index += 1
                    raise error
                remote.content = path.read_bytes()
                remote.sha_index += 1
                if remote.fail_after_write is not None:
                    raise remote.fail_after_write
                return SimpleNamespace(oid=remote.sha)

        return FakeHfApi


def main():
    original_home = os.environ.get("HF_HOME")
    original_hf_api = api_mod.HfApi
    original_revision_sha = getattr(
        api_mod, "_remote_revision_commit_sha", None
    )
    original_download = getattr(
        api_mod, "_download_remote_gitattributes", None
    )
    original_open_url = api_mod._atomgit_open_url
    original_execute = api_mod._execute_resumable_upload_process
    original_validate = api_mod._validate_resumable_upload_target
    original_configure = getattr(
        api_mod, "_configure_remote_lfs_attributes", None
    )
    original_credentials = cfg_mod.config.get_credentials
    original_logged_in = cfg_mod.config.is_logged_in
    original_upload_directory = api_mod.api.upload_directory

    try:
        try:
            inspect.signature(original_hf_api.upload_file).bind(
                object(),
                path_or_fileobj="/isolated/.gitattributes",
                path_in_repo=".gitattributes",
                repo_id="user/repo",
                repo_type="model",
                revision="dev",
                commit_message="chore: configure Git LFS",
                parent_commit="1" * 40,
            )
        except TypeError as error:
            signature_supported = False
            signature_detail = str(error)
        else:
            signature_supported = True
            signature_detail = ""
        check(
            "locked HF upload_file accepts the optimistic one-file contract",
            signature_supported,
            signature_detail,
        )

        unsafe_items = [
            FakeUploadModeItem(
                "prefix/capture.bag",
                api_mod._RESUMABLE_REGULAR_FILE_MAX_BYTES + 1,
            ).pair(),
            FakeUploadModeItem(
                "prefix/second.MCAP",
                api_mod._RESUMABLE_REGULAR_FILE_MAX_BYTES + 2,
            ).pair(),
            FakeUploadModeItem(
                "prefix/third.mcap",
                api_mod._RESUMABLE_REGULAR_FILE_MAX_BYTES + 2,
            ).pair(),
            FakeUploadModeItem(
                "/private/source/secret-no-extension",
                api_mod._RESUMABLE_REGULAR_FILE_MAX_BYTES + 3,
            ).pair(),
        ]
        try:
            api_mod._validate_resumable_upload_mode_items(unsafe_items)
        except api_mod.ResumableUploadModeError as error:
            patterns = error.lfs_patterns
            envelope = api_mod._resumable_failure_envelope(error)
        else:
            patterns = ()
            envelope = {}
        check(
            "unsafe upload modes expose only validated extension patterns",
            patterns == ("*.bag", "*.MCAP", "*.mcap"),
            repr(patterns),
        )
        check(
            "worker envelope carries bounded patterns without source paths",
            envelope
            == {
                "category": "upload_mode",
                "lfs_patterns": ["*.bag", "*.MCAP", "*.mcap"],
            }
            and "/private/" not in repr(envelope),
            repr(envelope),
        )

        merged, appended = api_mod._merge_lfs_gitattributes(
            b"# keep this byte-for-byte\n*.zip filter=lfs\ntrailing-without-newline",
            ("*.bag", "*.MCAP"),
        )
        check(
            "existing attributes are preserved and missing newline is repaired",
            merged.startswith(
                b"# keep this byte-for-byte\n*.zip filter=lfs\n"
                b"trailing-without-newline\n"
            ),
        )
        check(
            "standard LFS lines are appended in deterministic order",
            merged.endswith(
                b"*.bag filter=lfs diff=lfs merge=lfs -text\n"
                b"*.MCAP filter=lfs diff=lfs merge=lfs -text\n"
            )
            and appended == ("*.bag", "*.MCAP"),
            repr(appended),
        )
        unchanged, duplicate = api_mod._merge_lfs_gitattributes(
            merged, ("*.bag", "*.MCAP")
        )
        check(
            "a final generated rule is idempotent",
            unchanged == merged and duplicate == (),
        )
        overridden, override_appended = api_mod._merge_lfs_gitattributes(
            b"*.bag filter=lfs diff=lfs merge=lfs -text\n"
            b"*.bag -filter -diff -merge text\n",
            ("*.bag",),
        )
        check(
            "an earlier overridden rule is appended again at the end",
            override_appended == ("*.bag",)
            and overridden.endswith(
                b"*.bag -filter -diff -merge text\n"
                b"*.bag filter=lfs diff=lfs merge=lfs -text\n"
            ),
        )
        check(
            "remote verification rejects an earlier overridden rule",
            not api_mod._gitattributes_contains_lfs_patterns(
                b"*.bag filter=lfs diff=lfs merge=lfs -text\n"
                b"*.bag -filter -diff -merge text\n",
                ("*.bag",),
            )
            and api_mod._gitattributes_contains_lfs_patterns(
                overridden, ("*.bag",)
            ),
        )
        try:
            api_mod._merge_lfs_gitattributes(
                b"x" * (api_mod._LFS_GITATTRIBUTES_MAX_BYTES + 1),
                ("*.bag",),
            )
        except ValueError:
            oversized_rejected = True
        else:
            oversized_rejected = False
        check(
            "oversized remote attributes are rejected before mutation",
            oversized_rejected,
        )

        with tempfile.TemporaryDirectory(prefix="atomgit-lfs-test-") as td:
            os.environ["HF_HOME"] = str(Path(td) / "cache")
            missing_error = urllib.error.HTTPError(
                "https://hub.atomgit.com/user/repo/resolve/main/.gitattributes",
                404,
                "Not Found",
                {},
                None,
            )
            api_mod._atomgit_open_url = lambda *args, **kwargs: (
                (_ for _ in ()).throw(missing_error)
            )

            class TreeHfApi:
                files = []

                def __init__(self, endpoint=None, token=None):
                    self.endpoint = endpoint
                    self.token = token

                def list_repo_files(
                    self, repo_id, *, revision=None, repo_type=None
                ):
                    return list(self.files)

            api_mod.HfApi = TreeHfApi
            missing_path = Path(td) / "missing-attributes"
            confirmed_missing = api_mod._download_remote_gitattributes(
                token="fake-token-never-print",
                repo_id="user/repo",
                repo_type="model",
                revision="1" * 40,
                destination=missing_path,
                request_timeout=17,
            )
            check(
                "resolve 404 is accepted only when the tree confirms absence",
                not confirmed_missing and not missing_path.exists(),
            )
            TreeHfApi.files = [".gitattributes"]
            try:
                api_mod._download_remote_gitattributes(
                    token="fake-token-never-print",
                    repo_id="user/repo",
                    repo_type="model",
                    revision="1" * 40,
                    destination=missing_path,
                    request_timeout=17,
                )
            except urllib.error.HTTPError as error:
                existing_404_rejected = error.code == 404
            else:
                existing_404_rejected = False
            check(
                "an existing path resolve 404 is not misclassified as missing",
                existing_404_rejected,
            )

            api_mod._atomgit_open_url = original_open_url
            remote = FakeRemote()
            api_mod.HfApi = remote.api_type()
            api_mod._remote_revision_commit_sha = remote.revision_sha
            api_mod._download_remote_gitattributes = remote.download

            outcome = api_mod._configure_remote_lfs_attributes(
                token="fake-token-never-print",
                repo_id="user/repo",
                repo_type="model",
                revision="dev",
                patterns=("*.bag",),
                request_timeout=17,
            )
            upload = remote.uploads[0]
            check(
                "missing attributes produce one isolated one-file commit",
                outcome["changed"]
                and outcome["created"]
                and len(remote.uploads) == 1
                and upload["path_in_repo"] == ".gitattributes"
                and upload["repo_id"] == "user/repo"
                and upload["repo_type"] == "model"
                and upload["revision"] == "dev"
                and upload["parent_commit"] == f"{1:040x}",
                repr(upload),
            )
            check(
                "configuration client is pinned and buffer is private",
                upload["endpoint"] == "https://hub.atomgit.com"
                and upload["client_token"] == "fake-token-never-print"
                and upload["path_exists"]
                and upload["file_mode"] == 0o600
                and upload["parent_mode"] == 0o700
                and "lfs-config" in str(upload["path_or_fileobj"]),
            )
            check(
                "configuration commit contains only the generated rule",
                upload["content"]
                == b"*.bag filter=lfs diff=lfs merge=lfs -text\n",
            )

            no_change = api_mod._configure_remote_lfs_attributes(
                token="fake-token-never-print",
                repo_id="user/repo",
                repo_type="model",
                revision="dev",
                patterns=("*.bag",),
                request_timeout=17,
            )
            check(
                "confirmed existing rules do not create an empty commit",
                not no_change["changed"] and len(remote.uploads) == 1,
            )

            remote_timeout = FakeRemote(b"# existing\n")
            remote_timeout.fail_after_write = httpx.ReadTimeout(
                "response timeout without sensitive response"
            )
            api_mod.HfApi = remote_timeout.api_type()
            api_mod._remote_revision_commit_sha = remote_timeout.revision_sha
            api_mod._download_remote_gitattributes = remote_timeout.download
            reconciled = api_mod._configure_remote_lfs_attributes(
                token="fake-token-never-print",
                repo_id="user/repo",
                repo_type="model",
                revision=None,
                patterns=("*.bag",),
                request_timeout=17,
            )
            check(
                "ambiguous upload response is accepted only after remote readback",
                reconciled["changed"]
                and reconciled["verified_after_error"]
                and len(remote_timeout.uploads) == 1,
            )

            request = httpx.Request(
                "POST", "https://hub.atomgit.com/api/models/user/repo/commit/dev"
            )
            response = httpx.Response(409, request=request)
            conflict_error = httpx.HTTPStatusError(
                "concurrent branch update", request=request, response=response
            )
            remote_conflict = FakeRemote(b"# base\n")
            remote_conflict.fail_before_write = (
                conflict_error,
                b"# base\n# concurrent change\n",
            )
            api_mod.HfApi = remote_conflict.api_type()
            api_mod._remote_revision_commit_sha = remote_conflict.revision_sha
            api_mod._download_remote_gitattributes = remote_conflict.download
            conflict_outcome = api_mod._configure_remote_lfs_attributes(
                token="fake-token-never-print",
                repo_id="user/repo",
                repo_type="model",
                revision="dev",
                patterns=("*.bag",),
                request_timeout=17,
            )
            check(
                "concurrent branch changes are re-read and preserved",
                conflict_outcome["changed"]
                and len(remote_conflict.uploads) == 2
                and remote_conflict.uploads[0]["parent_commit"] == f"{1:040x}"
                and remote_conflict.uploads[1]["parent_commit"] == f"{2:040x}"
                and remote_conflict.content.startswith(
                    b"# base\n# concurrent change\n"
                ),
                repr(remote_conflict.uploads),
            )

            source = Path(td) / "source"
            source.mkdir()
            (source / "capture.bag").write_bytes(b"small offline fixture")
            cfg_mod.config.get_credentials = lambda: {
                "token": "fake-token-never-print"
            }
            api_mod._validate_resumable_upload_target = lambda **kwargs: None
            attempts = []
            repairs = []

            def execute_once_then_succeed(**kwargs):
                attempts.append(kwargs)
                if len(attempts) == 1:
                    raise api_mod.ResumableWorkerError(
                        "upload_mode", ("*.bag",)
                    )

            def configure_once(**kwargs):
                repairs.append(kwargs)
                return {
                    "changed": True,
                    "created": True,
                    "verified_after_error": False,
                    "patterns": kwargs["patterns"],
                }

            api_mod._execute_resumable_upload_process = execute_once_then_succeed
            api_mod._configure_remote_lfs_attributes = configure_once
            output = io.StringIO()
            with redirect_stdout(output):
                resumed = api_mod.api.upload_directory(
                    source,
                    "user/repo",
                    repo_type="dataset",
                    revision="dev",
                    resumable=True,
                    auto_configure_lfs=True,
                )
            text = output.getvalue()
            check(
                "opt-in repair retries the same batch",
                resumed and len(attempts) == 2 and len(repairs) == 1,
            )
            check(
                "dataset repair uses the verified model compatibility route",
                repairs[0]["repo_type"] == "model"
                and repairs[0]["revision"] == "dev",
                repr(repairs),
            )
            check(
                "detected repair prints the rule and repository-wide warning",
                "*.bag" in text and "整个仓库" in text,
                text,
            )

            attempts.clear()
            repairs.clear()
            def execute_always_mode(**kwargs):
                attempts.append(kwargs)
                raise api_mod.ResumableWorkerError(
                    "upload_mode", ("*.bag",)
                )

            api_mod._execute_resumable_upload_process = execute_always_mode
            output = io.StringIO()
            with redirect_stdout(output):
                rejected = api_mod.api.upload_directory(
                    source,
                    "user/repo",
                    resumable=True,
                    auto_configure_lfs=False,
                )
            text = output.getvalue()
            check(
                "default behavior remains a safe failure without remote repair",
                not rejected and len(attempts) == 1 and not repairs,
            )
            check(
                "default failure recommends the explicit configuration option",
                "--auto-configure-lfs" in text,
                text,
            )

            attempts.clear()
            repairs.clear()
            output = io.StringIO()
            with redirect_stdout(output):
                bounded = api_mod.api.upload_directory(
                    source,
                    "user/repo",
                    resumable=True,
                    auto_configure_lfs=True,
                )
            check(
                "one detected rule is never configured in an infinite loop",
                not bounded and len(attempts) == 2 and len(repairs) == 1,
                output.getvalue(),
            )

            attempts.clear()
            repairs.clear()

            def execute_quota_failure(**kwargs):
                attempts.append(kwargs)
                raise api_mod.ResumableWorkerError("lfs_quota")

            api_mod._execute_resumable_upload_process = execute_quota_failure
            output = io.StringIO()
            with redirect_stdout(output):
                quota_failure = api_mod.api.upload_directory(
                    source,
                    "user/repo",
                    resumable=True,
                    auto_configure_lfs=True,
                )
            quota_text = output.getvalue()
            check(
                "LFS Batch quota failure never invokes policy repair",
                not quota_failure and len(attempts) == 1 and not repairs,
            )
            check(
                "LFS quota output is not commit-size guidance",
                "LFS 存储空间不足" in quota_text
                and "提交已降至单文件" not in quota_text
                and "--auto-configure-lfs" not in quota_text,
                quota_text,
            )

            cli_calls = []

            def fake_upload_directory(*args, **kwargs):
                cli_calls.append((args, kwargs))
                return True

            api_mod.api.upload_directory = fake_upload_directory
            cfg_mod.config.is_logged_in = lambda: True
            runner = CliRunner()
            enabled = runner.invoke(
                cli,
                [
                    "upload",
                    str(source),
                    "--repo-id",
                    "user/repo",
                    "--auto-configure-lfs",
                ],
            )
            check(
                "public option is accepted and forwarded only by directory resumable",
                enabled.exit_code == 0
                and len(cli_calls) == 1
                and cli_calls[0][1]["auto_configure_lfs"] is True,
                enabled.output,
            )
            invalid_file = runner.invoke(
                cli,
                [
                    "upload",
                    str(source / "capture.bag"),
                    "--repo-id",
                    "user/repo",
                    "--auto-configure-lfs",
                ],
            )
            invalid_ordinary = runner.invoke(
                cli,
                [
                    "upload",
                    str(source),
                    "--repo-id",
                    "user/repo",
                    "--no-resumable",
                    "--auto-configure-lfs",
                ],
            )
            check(
                "file and ordinary uploads reject the remote mutation option",
                invalid_file.exit_code == 2
                and invalid_ordinary.exit_code == 2
                and len(cli_calls) == 1,
                invalid_file.output + invalid_ordinary.output,
            )
            help_result = runner.invoke(cli, ["upload", "--help"])
            check(
                "upload help documents the explicit option",
                help_result.exit_code == 0
                and "--auto-configure-lfs" in help_result.output,
                help_result.output,
            )
    finally:
        api_mod.HfApi = original_hf_api
        api_mod._atomgit_open_url = original_open_url
        if original_revision_sha is None:
            api_mod.__dict__.pop("_remote_revision_commit_sha", None)
        else:
            api_mod._remote_revision_commit_sha = original_revision_sha
        if original_download is None:
            api_mod.__dict__.pop("_download_remote_gitattributes", None)
        else:
            api_mod._download_remote_gitattributes = original_download
        api_mod._execute_resumable_upload_process = original_execute
        api_mod._validate_resumable_upload_target = original_validate
        if original_configure is None:
            api_mod.__dict__.pop("_configure_remote_lfs_attributes", None)
        else:
            api_mod._configure_remote_lfs_attributes = original_configure
        cfg_mod.config.get_credentials = original_credentials
        cfg_mod.config.is_logged_in = original_logged_in
        api_mod.api.upload_directory = original_upload_directory
        if original_home is None:
            os.environ.pop("HF_HOME", None)
        else:
            os.environ["HF_HOME"] = original_home

    passed = sum(results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
