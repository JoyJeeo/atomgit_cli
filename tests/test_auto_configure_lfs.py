#!/usr/bin/env python3
"""Offline contracts for opt-in remote Git LFS policy repair."""

import io
import inspect
import os
import queue
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


class ProactivePolicyApi:
    items = []
    events = []
    route = "upload_mode"

    def __init__(self, endpoint=None, token=None):
        self.endpoint = endpoint
        self.token = token

    def create_commit(self, *args, **kwargs):
        self.events.append("commit")

    def upload_large_folder(self, **kwargs):
        if self.route == "upload_mode":
            api_mod.hf_large_folder._get_upload_mode(
                self.items,
                api=self,
                repo_id=kwargs["repo_id"],
                repo_type=kwargs["repo_type"],
                revision="main",
            )
            self.events.append("upload-mode-returned")
            return
        api_mod.hf_large_folder._preupload_lfs(
            self.items,
            api=self,
            repo_id=kwargs["repo_id"],
            repo_type=kwargs["repo_type"],
            revision="main",
        )


def server_select_lfs(items, *args, **kwargs):
    for _, metadata in items:
        metadata.upload_mode = "lfs"


def record_preupload(items, *args, **kwargs):
    ProactivePolicyApi.events.append("preupload")


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
    original_get_upload_mode = api_mod.hf_large_folder._get_upload_mode
    original_preupload_lfs = api_mod.hf_large_folder._preupload_lfs
    original_close_session = api_mod.close_hf_session

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

        proactive_item = FakeUploadModeItem(
            "prefix/capture.bag", 10, mode=None
        ).pair()
        ProactivePolicyApi.items = [proactive_item]
        ProactivePolicyApi.events = []
        ProactivePolicyApi.route = "upload_mode"
        api_mod.HfApi = ProactivePolicyApi
        api_mod.hf_large_folder._get_upload_mode = server_select_lfs
        api_mod.close_hf_session = lambda: None
        result_queue = queue.Queue()
        api_mod._run_resumable_upload(
            "fake-token-never-print",
            {"repo_id": "user/repo", "folder_path": ".", "repo_type": "model"},
            result_queue,
            300.0,
            (1, 1),
            True,
            (),
        )
        check(
            "new server-selected LFS extension stops before upload-mode return",
            result_queue.get_nowait()
            == (
                False,
                {"category": "lfs_attributes", "lfs_patterns": ["*.bag"]},
            )
            and ProactivePolicyApi.events == [],
            repr(ProactivePolicyApi.events),
        )

        proactive_item[1].upload_mode = "lfs"
        ProactivePolicyApi.events = []
        ProactivePolicyApi.route = "preupload"
        api_mod.hf_large_folder._preupload_lfs = record_preupload
        result_queue = queue.Queue()
        api_mod._run_resumable_upload(
            "fake-token-never-print",
            {"repo_id": "user/repo", "folder_path": ".", "repo_type": "model"},
            result_queue,
            300.0,
            (1, 1),
            True,
            (),
        )
        check(
            "cached LFS extension stops before object preupload",
            result_queue.get_nowait()
            == (
                False,
                {"category": "lfs_attributes", "lfs_patterns": ["*.bag"]},
            )
            and ProactivePolicyApi.events == [],
            repr(ProactivePolicyApi.events),
        )

        ProactivePolicyApi.events = []
        result_queue = queue.Queue()
        api_mod._run_resumable_upload(
            "fake-token-never-print",
            {"repo_id": "user/repo", "folder_path": ".", "repo_type": "model"},
            result_queue,
            300.0,
            (1, 1),
            True,
            ("*.bag",),
        )
        check(
            "confirmed LFS extension proceeds without another policy stop",
            result_queue.get_nowait() == (True, {"recovered": 0})
            and ProactivePolicyApi.events == ["preupload"],
            repr(ProactivePolicyApi.events),
        )
        proactive_item[1].upload_mode = None
        ProactivePolicyApi.items = [proactive_item]
        ProactivePolicyApi.events = []
        ProactivePolicyApi.route = "upload_mode"
        api_mod.hf_large_folder._get_upload_mode = server_select_lfs
        result_queue = queue.Queue()
        api_mod._run_resumable_upload(
            "fake-token-never-print",
            {"repo_id": "user/repo", "folder_path": ".", "repo_type": "model"},
            result_queue,
            300.0,
            (1, 1),
            False,
            (),
        )
        check(
            "disabled option leaves server-selected LFS flow unchanged",
            result_queue.get_nowait() == (True, {"recovered": 0})
            and ProactivePolicyApi.events == ["upload-mode-returned"],
        )
        with tempfile.TemporaryDirectory(
            prefix="atomgit-lfs-completed-projection-"
        ) as completed_name:
            completed_projection = Path(completed_name)
            completed_file = completed_projection / "completed.bag"
            completed_file.write_bytes(b"completed offline fixture")
            completed_paths = api_mod.get_local_upload_paths(
                completed_projection, "completed.bag"
            )
            completed_metadata = api_mod.read_upload_metadata(
                completed_projection, "completed.bag"
            )
            completed_metadata.sha256 = "12" * 32
            completed_metadata.upload_mode = "lfs"
            completed_metadata.should_ignore = False
            completed_metadata.is_uploaded = True
            completed_metadata.is_committed = True
            completed_metadata.save(completed_paths)
            ProactivePolicyApi.items = []
            ProactivePolicyApi.events = []
            ProactivePolicyApi.route = "upload_mode"
            result_queue = queue.Queue()
            api_mod._run_resumable_upload(
                "fake-token-never-print",
                {
                    "repo_id": "user/repo",
                    "folder_path": str(completed_projection),
                    "repo_type": "model",
                },
                result_queue,
                300.0,
                (1, 1),
                True,
                (),
            )
            check(
                "fully committed cached LFS extension still requests verification",
                result_queue.get_nowait()
                == (
                    False,
                    {
                        "category": "lfs_attributes",
                        "lfs_patterns": ["*.bag"],
                    },
                )
                and ProactivePolicyApi.events == [],
            )
        api_mod.HfApi = original_hf_api
        api_mod.hf_large_folder._get_upload_mode = original_get_upload_mode
        api_mod.hf_large_folder._preupload_lfs = original_preupload_lfs
        api_mod.close_hf_session = original_close_session

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
        lfs_items = [
            FakeUploadModeItem("prefix/a.bag", 10, mode="lfs").pair(),
            FakeUploadModeItem("prefix/b.MCAP", 10, mode="lfs").pair(),
            FakeUploadModeItem("prefix/no-extension", 10, mode="lfs").pair(),
            FakeUploadModeItem("prefix/regular.zip", 10).pair(),
        ]
        lfs_items.append(
            (
                SimpleNamespace(path_in_repo="prefix/ignored.tar"),
                SimpleNamespace(
                    size=10, upload_mode="lfs", should_ignore=True
                ),
            )
        )
        check(
            "server-selected LFS patterns are safe and deterministic",
            api_mod._resumable_lfs_patterns(lfs_items)
            == ("*.bag", "*.MCAP"),
        )
        too_many_lfs_items = [
            FakeUploadModeItem(
                f"prefix/file.ext{index}", 10, mode="lfs"
            ).pair()
            for index in range(api_mod._RESUMABLE_LFS_PATTERN_MAX_COUNT + 1)
        ]
        try:
            api_mod._resumable_lfs_patterns(too_many_lfs_items)
        except api_mod.ResumableLfsAttributesError as error:
            overflow_envelope = api_mod._resumable_failure_envelope(error)
        else:
            overflow_envelope = None
        check(
            "too many LFS extensions stop safely without an oversized envelope",
            overflow_envelope == {"category": "lfs_attributes"},
            repr(overflow_envelope),
        )
        proactive_envelope = api_mod._resumable_failure_envelope(
            api_mod.ResumableLfsAttributesError(
                ("*.bag", "*.MCAP", "*", "/private/source.secret")
            )
        )
        check(
            "proactive worker envelope carries only validated patterns",
            proactive_envelope
            == {
                "category": "lfs_attributes",
                "lfs_patterns": ["*.bag", "*.MCAP"],
            }
            and "/private/" not in repr(proactive_envelope),
            repr(proactive_envelope),
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
        partially_merged, partial_appended = api_mod._merge_lfs_gitattributes(
            b"*.bag filter=lfs diff=lfs merge=lfs -text\n",
            ("*.bag", "*.mcap"),
        )
        check(
            "a multi-pattern merge appends only the missing effective rule",
            partial_appended == ("*.mcap",)
            and partially_merged.count(b"*.bag ") == 1
            and partially_merged.endswith(
                b"*.mcap filter=lfs diff=lfs merge=lfs -text\n"
            ),
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
        broad_override = (
            b"*.bag filter=lfs diff=lfs merge=lfs -text\n"
            b"* -filter -diff -merge text\n"
        )
        broad_repaired, broad_appended = api_mod._merge_lfs_gitattributes(
            broad_override, ("*.bag",)
        )
        check(
            "a later broad attribute override is repaired at the file end",
            broad_appended == ("*.bag",)
            and not api_mod._gitattributes_contains_lfs_patterns(
                broad_override, ("*.bag",)
            )
            and api_mod._gitattributes_contains_lfs_patterns(
                broad_repaired, ("*.bag",)
            ),
        )
        suffix_block = (
            b"* -filter -diff -merge text\n"
            b"*.bag filter=lfs diff=lfs merge=lfs -text\n"
            b"*.mcap filter=lfs diff=lfs merge=lfs -text\n"
            b"# trailing comment\n\n"
        )
        check(
            "a trailing standard LFS block remains idempotent",
            api_mod._gitattributes_contains_lfs_patterns(
                suffix_block, ("*.bag", "*.mcap")
            )
            and api_mod._merge_lfs_gitattributes(
                suffix_block, ("*.bag", "*.mcap")
            ) == (suffix_block, ()),
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
                        "lfs_attributes", ("*.bag",)
                    )
                return {"recovered": 0}

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
                "opt-in proactive configuration retries the same batch",
                resumed and len(attempts) == 2 and len(repairs) == 1,
            )
            check(
                "retry carries confirmed extensions into the next child",
                attempts[0]["auto_configure_lfs"] is True
                and attempts[0]["configured_lfs_patterns"] == ()
                and attempts[1]["configured_lfs_patterns"] == ("*.bag",),
            )
            check(
                "dataset repair uses the verified model compatibility route",
                repairs[0]["repo_type"] == "model"
                and repairs[0]["revision"] == "dev",
                repr(repairs),
            )
            check(
                "proactive synchronization prints the repository-wide rule",
                "*.bag" in text and "服务端判定为 LFS" in text
                and "整个仓库" in text,
                text,
            )

            (source / "second.bag").write_bytes(b"second offline fixture")
            attempts.clear()
            repairs.clear()

            def execute_once_per_new_pattern(**kwargs):
                attempts.append(kwargs)
                if "*.bag" not in kwargs["configured_lfs_patterns"]:
                    raise api_mod.ResumableWorkerError(
                        "lfs_attributes", ("*.bag",)
                    )
                return {"recovered": 0}

            api_mod._execute_resumable_upload_process = (
                execute_once_per_new_pattern
            )
            output = io.StringIO()
            with redirect_stdout(output):
                cross_batch = api_mod.api.upload_directory(
                    source,
                    "user/repo",
                    resumable=True,
                    auto_configure_lfs=True,
                    batch_size=1,
                )
            check(
                "one LFS extension is configured once across outer batches",
                cross_batch and len(attempts) == 3 and len(repairs) == 1
                and attempts[0]["configured_lfs_patterns"] == ()
                and all(
                    call["configured_lfs_patterns"] == ("*.bag",)
                    for call in attempts[1:]
                ),
            )
            (source / "second.bag").unlink()

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
        api_mod.hf_large_folder._get_upload_mode = original_get_upload_mode
        api_mod.hf_large_folder._preupload_lfs = original_preupload_lfs
        api_mod.close_hf_session = original_close_session
        if original_home is None:
            os.environ.pop("HF_HOME", None)
        else:
            os.environ["HF_HOME"] = original_home

    passed = sum(results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
