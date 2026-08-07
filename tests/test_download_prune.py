#!/usr/bin/env python3
"""Verify manifest-scoped repository download pruning and CLI compatibility."""

import contextlib
import io
import json
import os
import stat
import sys
import tempfile
from pathlib import Path

import atomgit  # noqa: F401
from click.testing import CliRunner


api_mod = sys.modules["atomgit.api"]
cli_mod = sys.modules["atomgit.cli"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" +
          (f" -> {detail}" if detail else ""))


def main():
    original_list = api_mod._atomgit_list_repo_files
    original_fetch = api_mod._download_atomgit_file
    original_credentials = api_mod.config.get_credentials
    original_manifest_root = api_mod._download_manifest_root
    original_manifest_write = api_mod._write_download_manifest
    original_cli_download = cli_mod.api.download_repo
    original_logged_in = cli_mod.config.is_logged_in
    remote_files = []
    failing_file = None

    try:
        with tempfile.TemporaryDirectory() as directory:
            sandbox = Path(directory)
            manifest_root = sandbox / "private-manifests"

            previous_hf_home = os.environ.get("HF_HOME")
            try:
                os.environ["HF_HOME"] = str(sandbox / "actual-cache")
                actual_manifest_root = original_manifest_root()
                check(
                    "actual manifest cache permissions are restrictive",
                    stat.S_IMODE(actual_manifest_root.stat().st_mode) == 0o700,
                )
            finally:
                if previous_hf_home is None:
                    os.environ.pop("HF_HOME", None)
                else:
                    os.environ["HF_HOME"] = previous_hf_home

            def fake_manifest_root():
                manifest_root.mkdir(mode=0o700, parents=True, exist_ok=True)
                os.chmod(manifest_root, 0o700)
                return manifest_root

            def fake_list(*args, **kwargs):
                return "model", list(remote_files)

            def fake_fetch(repo_id, repo_type, filename, destination, token, **kwargs):
                if filename == failing_file:
                    raise OSError("offline transfer failure")
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(("downloaded:" + filename).encode("utf-8"))

            api_mod._download_manifest_root = fake_manifest_root
            api_mod._atomgit_list_repo_files = fake_list
            api_mod._download_atomgit_file = fake_fetch
            api_mod.config.get_credentials = lambda: None

            target = sandbox / "target"
            target.mkdir()
            (target / "user-notes.txt").write_text("keep", encoding="utf-8")
            remote_files[:] = ["a.bin", "nested/b.bin"]
            check(
                "initial forced repository download succeeds",
                api_mod.api.download_repo(
                    "user/repo", target, force_download=True
                ),
            )
            manifest_path = api_mod._download_manifest_path(
                "user/repo", "model", target
            )
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            check(
                "manifest records only downloaded files",
                payload == {
                    "version": 1,
                    "files": ["a.bin", "nested/b.bin"],
                },
                repr(payload),
            )
            check(
                "manifest directory permissions are restrictive",
                stat.S_IMODE(manifest_root.stat().st_mode) == 0o700,
            )
            check(
                "manifest file permissions are restrictive",
                stat.S_IMODE(manifest_path.stat().st_mode) == 0o600,
            )
            check(
                "manifest filename is opaque and credential-free",
                "user" not in manifest_path.name
                and "repo" not in manifest_path.name
                and len(manifest_path.stem) == 64,
                manifest_path.name,
            )

            remote_files[:] = ["a.bin", "c.bin"]
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                pruned = api_mod.api.download_repo(
                    "user/repo", target, prune=True
                )
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            check("prune after successful download succeeds", pruned)
            check("remote-removed managed file is deleted", not (target / "nested/b.bin").exists())
            check("untracked user file is preserved", (target / "user-notes.txt").read_text(encoding="utf-8") == "keep")
            check("new remote file is downloaded", (target / "c.bin").is_file())
            check("manifest advances after prune", payload["files"] == ["a.bin", "c.bin"], repr(payload))
            check("prune reports removed count", "本地多余文件: 1" in output.getvalue(), repr(output.getvalue()))

            adoption_target = sandbox / "adoption"
            adoption_target.mkdir()
            (adoption_target / "preexisting.bin").write_bytes(b"owned-by-user")
            (adoption_target / "notes.txt").write_bytes(b"also-user-owned")
            remote_files[:] = ["preexisting.bin", "new.bin"]
            with contextlib.redirect_stdout(io.StringIO()):
                adoption_ok = api_mod.api.download_repo(
                    "user/adoption", adoption_target, prune=True
                )
            adoption_manifest = api_mod._download_manifest_path(
                "user/adoption", "model", adoption_target
            )
            adoption_payload = json.loads(
                adoption_manifest.read_text(encoding="utf-8")
            )
            check("first prune without manifest succeeds", adoption_ok)
            check(
                "skipped pre-existing file is not adopted",
                adoption_payload["files"] == ["new.bin"],
                repr(adoption_payload),
            )
            remote_files[:] = []
            with contextlib.redirect_stdout(io.StringIO()):
                empty_ok = api_mod.api.download_repo(
                    "user/adoption", adoption_target, prune=True
                )
            check("empty remote repository can be pruned", empty_ok)
            check("managed file is removed from empty repository", not (adoption_target / "new.bin").exists())
            check("unmanaged pre-existing file survives empty prune", (adoption_target / "preexisting.bin").read_bytes() == b"owned-by-user")
            check("untracked notes survive empty prune", (adoption_target / "notes.txt").is_file())

            missing_parent_target = sandbox / "missing-parent"
            remote_files[:] = ["nested/managed.bin"]
            check(
                "missing-parent fixture initial download succeeds",
                api_mod.api.download_repo(
                    "user/missing-parent", missing_parent_target,
                    force_download=True,
                ),
            )
            (missing_parent_target / "nested/managed.bin").unlink()
            (missing_parent_target / "nested").rmdir()
            remote_files[:] = []
            with contextlib.redirect_stdout(io.StringIO()):
                missing_parent_ok = api_mod.api.download_repo(
                    "user/missing-parent", missing_parent_target, prune=True
                )
            check(
                "already-missing managed parent is treated as clean",
                missing_parent_ok,
            )

            failure_target = sandbox / "failure"
            remote_files[:] = ["old.bin"]
            check(
                "failure fixture initial download succeeds",
                api_mod.api.download_repo(
                    "user/failure", failure_target, force_download=True
                ),
            )
            failure_manifest = api_mod._download_manifest_path(
                "user/failure", "model", failure_target
            )
            manifest_before_failure = failure_manifest.read_bytes()
            remote_files[:] = ["new.bin"]
            failing_file = "new.bin"
            with contextlib.redirect_stdout(io.StringIO()):
                failure_result = api_mod.api.download_repo(
                    "user/failure", failure_target, prune=True
                )
            failing_file = None
            check("download failure prevents prune", failure_result is False)
            check("stale managed file survives failed download", (failure_target / "old.bin").is_file())
            check("manifest is unchanged after failed download", failure_manifest.read_bytes() == manifest_before_failure)

            symlink_target = sandbox / "symlink-target"
            remote_files[:] = ["stale.bin"]
            check(
                "symlink fixture initial download succeeds",
                api_mod.api.download_repo(
                    "user/symlink", symlink_target, force_download=True
                ),
            )
            outside = sandbox / "outside.bin"
            outside.write_bytes(b"outside")
            (symlink_target / "stale.bin").unlink()
            (symlink_target / "stale.bin").symlink_to(outside)
            remote_files[:] = []
            with contextlib.redirect_stdout(io.StringIO()):
                symlink_result = api_mod.api.download_repo(
                    "user/symlink", symlink_target, prune=True
                )
            check("prune refuses a managed path replaced by a symlink", symlink_result is False)
            check("symlink is not deleted", (symlink_target / "stale.bin").is_symlink())
            check("symlink target is not deleted", outside.read_bytes() == b"outside")

            parent_symlink_target = sandbox / "parent-symlink-target"
            remote_files[:] = ["nested/stale.bin"]
            check(
                "parent-symlink fixture initial download succeeds",
                api_mod.api.download_repo(
                    "user/parent-symlink", parent_symlink_target,
                    force_download=True,
                ),
            )
            (parent_symlink_target / "nested/stale.bin").unlink()
            (parent_symlink_target / "nested").rmdir()
            outside_directory = sandbox / "outside-directory"
            outside_directory.mkdir()
            (outside_directory / "stale.bin").write_bytes(b"outside-parent")
            (parent_symlink_target / "nested").symlink_to(
                outside_directory, target_is_directory=True
            )
            remote_files[:] = []
            with contextlib.redirect_stdout(io.StringIO()):
                parent_symlink_result = api_mod.api.download_repo(
                    "user/parent-symlink", parent_symlink_target, prune=True
                )
            check(
                "prune refuses a symlinked managed parent",
                parent_symlink_result is False,
            )
            check(
                "file behind symlinked parent is not deleted",
                (outside_directory / "stale.bin").read_bytes()
                == b"outside-parent",
            )

            directory_target = sandbox / "directory-target"
            remote_files[:] = ["stale.bin"]
            check(
                "directory fixture initial download succeeds",
                api_mod.api.download_repo(
                    "user/directory", directory_target, force_download=True
                ),
            )
            (directory_target / "stale.bin").unlink()
            (directory_target / "stale.bin").mkdir()
            remote_files[:] = []
            with contextlib.redirect_stdout(io.StringIO()):
                directory_result = api_mod.api.download_repo(
                    "user/directory", directory_target, prune=True
                )
            check(
                "prune refuses a managed path replaced by a directory",
                directory_result is False,
            )
            check(
                "replacement directory is not deleted",
                (directory_target / "stale.bin").is_dir(),
            )

            malformed_target = sandbox / "malformed"
            remote_files[:] = ["kept.bin"]
            check(
                "malformed fixture initial download succeeds",
                api_mod.api.download_repo(
                    "user/malformed", malformed_target, force_download=True
                ),
            )
            malformed_manifest = api_mod._download_manifest_path(
                "user/malformed", "model", malformed_target
            )
            malformed_manifest.write_text('{"version":1,"files":["../escape"]}', encoding="utf-8")
            malformed_before = malformed_manifest.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()) as malformed_output:
                malformed_default = api_mod.api.download_repo(
                    "user/malformed", malformed_target
                )
            check(
                "malformed manifest does not break default download",
                malformed_default,
            )
            check(
                "default download does not overwrite malformed manifest",
                malformed_manifest.read_bytes() == malformed_before,
            )
            check(
                "default download warns when manifest is unavailable",
                "manifest 不可用" in malformed_output.getvalue(),
                repr(malformed_output.getvalue()),
            )
            with contextlib.redirect_stdout(io.StringIO()):
                malformed_result = api_mod.api.download_repo(
                    "user/malformed", malformed_target, prune=True
                )
            check("unsafe manifest fails closed", malformed_result is False)
            check("unsafe manifest cannot remove a managed file", (malformed_target / "kept.bin").is_file())

            original_manifest_helper = api_mod._download_manifest_root
            api_mod._download_manifest_root = lambda: (_ for _ in ()).throw(
                PermissionError("offline read-only cache")
            )
            unavailable_target = sandbox / "unavailable"
            remote_files[:] = ["new.bin"]
            with contextlib.redirect_stdout(io.StringIO()) as unavailable_output:
                unavailable_default = api_mod.api.download_repo(
                    "user/unavailable", unavailable_target
                )
            check(
                "unwritable manifest cache does not break default download",
                unavailable_default and (unavailable_target / "new.bin").is_file(),
            )
            check(
                "unwritable manifest cache produces a safe warning",
                "manifest 不可用" in unavailable_output.getvalue(),
                repr(unavailable_output.getvalue()),
            )
            with contextlib.redirect_stdout(io.StringIO()):
                unavailable_prune = api_mod.api.download_repo(
                    "user/unavailable", unavailable_target, prune=True
                )
            check(
                "explicit prune fails closed without manifest state",
                unavailable_prune is False,
            )
            api_mod._download_manifest_root = original_manifest_helper

            api_mod._write_download_manifest = (
                lambda *args, **kwargs: (_ for _ in ()).throw(
                    PermissionError("offline manifest write failure")
                )
            )
            write_failure_target = sandbox / "write-failure"
            remote_files[:] = ["new.bin"]
            with contextlib.redirect_stdout(io.StringIO()) as write_output:
                write_default = api_mod.api.download_repo(
                    "user/write-failure", write_failure_target
                )
            check(
                "manifest write failure does not break default download",
                write_default and (write_failure_target / "new.bin").is_file(),
            )
            check(
                "manifest write failure is disclosed",
                "manifest 写入失败" in write_output.getvalue(),
                repr(write_output.getvalue()),
            )
            with contextlib.redirect_stdout(io.StringIO()):
                write_prune = api_mod.api.download_repo(
                    "user/write-failure", write_failure_target, prune=True
                )
            check(
                "explicit prune fails when manifest cannot advance",
                write_prune is False,
            )
            api_mod._write_download_manifest = original_manifest_write

            cli_calls = []
            cli_mod.config.is_logged_in = lambda: True
            cli_mod.api.download_repo = lambda *args, **kwargs: (
                cli_calls.append((args, kwargs)) or True
            )
            runner = CliRunner()
            with runner.isolated_filesystem():
                default_cli = runner.invoke(
                    cli_mod.cli, ["download", "user/repo"]
                )
                prune_cli = runner.invoke(
                    cli_mod.cli, ["download", "user/repo", "--prune"]
                )
                file_help = runner.invoke(cli_mod.cli, ["download-file", "--help"])
            check("default CLI download remains compatible", default_cli.exit_code == 0 and "prune" not in cli_calls[0][1], repr(cli_calls))
            check("CLI forwards explicit prune", prune_cli.exit_code == 0 and cli_calls[1][1].get("prune") is True, repr(cli_calls))
            check("single-file command does not expose prune", file_help.exit_code == 0 and "--prune" not in file_help.output)
    finally:
        api_mod._atomgit_list_repo_files = original_list
        api_mod._download_atomgit_file = original_fetch
        api_mod.config.get_credentials = original_credentials
        api_mod._download_manifest_root = original_manifest_root
        api_mod._write_download_manifest = original_manifest_write
        cli_mod.api.download_repo = original_cli_download
        cli_mod.config.is_logged_in = original_logged_in

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
