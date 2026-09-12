#!/usr/bin/env python3
"""Exercise Windows-compatible persistence, Git helper, and prune contracts."""

import errno
import json
import ntpath
import os
import subprocess
import sys
import tempfile
from pathlib import Path, PureWindowsPath

import atomgit  # noqa: F401


api_mod = sys.modules["atomgit.api"]
config_mod = sys.modules["atomgit.config"]
utils_mod = sys.modules["atomgit.utils"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    print(
        f"[{'PASS' if condition else 'FAIL'}] {name}"
        + (f" -> {detail}" if detail else "")
    )


class FakeWindowsAPI:
    FILE_ATTRIBUTE_DIRECTORY = 0x10
    FILE_ATTRIBUTE_REPARSE_POINT = 0x400

    def __init__(self, root_path, target_path, target_attributes=0x80):
        self.root_path = root_path
        self.target_path = target_path
        self.target_attributes = target_attributes
        self.opened = []
        self.closed = []
        self.deleted = []
        self.fail_target_missing = False
        self.fail_final_path = False
        self.handle_paths = {}
        self.root_input = None

    def open_path(self, path, delete=False):
        self.opened.append((path, delete))
        if delete and self.fail_target_missing:
            raise FileNotFoundError(path)
        if delete:
            handle = "target"
        elif self.root_input is None:
            self.root_input = os.fspath(path)
            handle = "root"
        else:
            handle = f"directory-{len(self.handle_paths)}"
        self.handle_paths[handle] = os.fspath(path)
        return handle

    def final_path(self, handle):
        if self.fail_final_path:
            raise OSError("offline final-path failure")
        if handle == "target":
            return self.target_path
        if handle == "root":
            return self.root_path
        relative = ntpath.relpath(self.handle_paths[handle], self.root_input)
        return ntpath.join(self.root_path, relative)

    def attributes(self, handle):
        if handle != "target":
            return self.FILE_ATTRIBUTE_DIRECTORY
        return self.target_attributes

    def mark_delete(self, handle):
        self.deleted.append(handle)

    def close(self, handle):
        self.closed.append(handle)


class FakeWindowsLocking:
    LK_NBLCK = 1
    LK_UNLCK = 2

    def __init__(self):
        self.calls = []
        self.busy = False

    def locking(self, descriptor, mode, size):
        self.calls.append((descriptor, mode, size))
        if self.busy and mode == self.LK_NBLCK:
            raise OSError(errno.EACCES, "offline lock busy")


def run_git(*args, environment):
    return subprocess.run(
        ["git", *args],
        input=(
            "protocol=https\nhost=atomgit.com\n\n"
            if args == ("credential", "fill")
            else None
        ),
        capture_output=True,
        text=True,
        env=environment,
    )


def main():
    original_fchmod = getattr(os, "fchmod", None)
    original_environment = os.environ.copy()
    try:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            os.fchmod = None
            config_home = root / "config-home"
            config_home.mkdir()
            os.environ["HOME"] = str(config_home)
            config = config_mod.Config()
            try:
                config.set_credentials(
                    "fake-windows-token-never-print", username="windows-user"
                )
                config_error = None
            except Exception as error:
                config_error = error
            check(
                "credential save works without os.fchmod",
                config_error is None
                and config.get_credentials()
                == {"token": "fake-windows-token-never-print"},
                type(config_error).__name__ if config_error else "",
            )

            manifest = root / "manifest.json"
            try:
                api_mod._write_download_manifest(manifest, {"nested/file.bin"})
                manifest_error = None
            except Exception as error:
                manifest_error = error
            check(
                "manifest save works without os.fchmod",
                manifest_error is None
                and json.loads(manifest.read_text(encoding="utf-8"))["files"]
                == ["nested/file.bin"],
                type(manifest_error).__name__ if manifest_error else "",
            )
            pending_projection = root / "pending-projection"
            try:
                api_mod._write_pending_commit(
                    pending_projection,
                    {
                        "version": 1,
                        "state": "attempting",
                        "base_revision": "a" * 40,
                        "commit_revision": None,
                        "operations": [
                            {
                                "path": "payload.bin",
                                "size": 1,
                                "sha256": "b" * 64,
                                "upload_mode": "regular",
                                "git_sha1": "c" * 40,
                            }
                        ],
                    },
                )
                pending_error = None
            except Exception as error:
                pending_error = error
            check(
                "pending commit save works without os.fchmod",
                pending_error is None
                and api_mod._read_pending_commit(pending_projection)["state"]
                == "attempting",
                type(pending_error).__name__ if pending_error else "",
            )
            os.fchmod = original_fchmod

            original_lock_module = api_mod._windows_file_lock_module
            fake_locking = FakeWindowsLocking()
            api_mod._windows_file_lock_module = lambda: fake_locking
            lock_file = root / "windows-manifest.lock"
            descriptor = os.open(
                str(lock_file), os.O_CREAT | os.O_RDWR, 0o600
            )
            try:
                windows_locked = (
                    api_mod._try_lock_download_manifest_descriptor_windows(
                        descriptor
                    )
                )
                api_mod._unlock_download_manifest_descriptor_windows(
                    descriptor
                )
                fake_locking.busy = True
                windows_busy = (
                    api_mod._try_lock_download_manifest_descriptor_windows(
                        descriptor
                    )
                )
            finally:
                os.close(descriptor)
                api_mod._windows_file_lock_module = original_lock_module
            check(
                "Windows manifest lock uses nonblocking byte-range contract",
                windows_locked is True
                and windows_busy is False
                and lock_file.stat().st_size == 1
                and [call[1] for call in fake_locking.calls]
                == [
                    fake_locking.LK_NBLCK,
                    fake_locking.LK_UNLCK,
                    fake_locking.LK_NBLCK,
                ],
                repr(fake_locking.calls),
            )

            helper_builder = getattr(utils_mod, "_git_helper_command", None)
            if helper_builder is None:
                windows_helper = None
            else:
                windows_helper = helper_builder(
                    PureWindowsPath(
                        r"C:\Users\Test User\.atomgit\git-credential-atomgit"
                    ),
                    python_executable=PureWindowsPath(
                        r"C:\Program Files\Python\python.exe"
                    ),
                    windows=True,
                )
            check(
                "Windows helper command quotes interpreter and normalized path",
                windows_helper
                == "!'C:/Program Files/Python/python.exe' "
                "'C:/Users/Test User/.atomgit/git-credential-atomgit'",
                repr(windows_helper),
            )
            legacy_helper = (
                r"!C:\Users\Test User\.atomgit\git-credential-atomgit"
            )
            cleaned_helpers = utils_mod._legacy_cleanup_values(
                ["!generic", "", legacy_helper, "", windows_helper],
                {legacy_helper, windows_helper},
            )
            check(
                "legacy cleanup removes old and current managed commands",
                cleaned_helpers == ["!generic"],
                repr(cleaned_helpers),
            )

            helper_home = root / "home with spaces"
            helper_home.mkdir()
            atomgit_dir = helper_home / ".atomgit"
            atomgit_dir.mkdir()
            (atomgit_dir / "config.json").write_text(
                json.dumps(
                    {
                        "token": "fake-helper-token-never-print",
                        "username": "windows-user",
                    }
                ),
                encoding="utf-8",
            )
            global_config = root / "global config"
            os.environ.update(
                {
                    "HOME": str(helper_home),
                    "GIT_CONFIG_GLOBAL": str(global_config),
                    "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_TERMINAL_PROMPT": "0",
                }
            )
            helper_setup = utils_mod.setup_git_credentials(
                "fake-helper-token-never-print"
            )
            fill = run_git("credential", "fill", environment=os.environ.copy())
            check(
                "helper executes from a path containing spaces",
                helper_setup
                and fill.returncode == 0
                and "username=windows-user" in fill.stdout
                and "password=fake-helper-token-never-print" in fill.stdout,
                f"setup={helper_setup} exit={fill.returncode}",
            )
            if helper_setup:
                utils_mod.clear_git_credentials()

            helper_path = atomgit_dir / "git-credential-atomgit"
            legacy_value = f"!{helper_path}"
            for host in ("atomgit.com", "hub.atomgit.com"):
                key = f"credential.https://{host}.helper"
                run_git(
                    "config", "--global", "--add", key, "",
                    environment=os.environ.copy(),
                )
                run_git(
                    "config", "--global", "--add", key, legacy_value,
                    environment=os.environ.copy(),
                )
            upgraded = utils_mod.setup_git_credentials(
                "fake-helper-token-never-print"
            )
            upgraded_state = json.loads(
                (atomgit_dir / "git-helper-state.json").read_text(
                    encoding="utf-8"
                )
            )
            upgraded_cleanup = utils_mod.clear_git_credentials()
            restored_values = []
            for host in ("atomgit.com", "hub.atomgit.com"):
                result = run_git(
                    "config",
                    "--global",
                    "--get-all",
                    f"credential.https://{host}.helper",
                    environment=os.environ.copy(),
                )
                restored_values.append(result.stdout.splitlines())
            check(
                "upgrade does not restore a stale legacy managed helper",
                upgraded
                and upgraded_cleanup
                and upgraded_state["hosts"]
                == {"atomgit.com": [], "hub.atomgit.com": []}
                and restored_values == [[], []],
                repr(restored_values),
            )

            windows_prune = getattr(
                api_mod, "_prune_managed_download_file_windows", None
            )
            root_final = r"\\?\C:\safe\root"
            target_final = root_final + r"\nested\managed.bin"
            if windows_prune is None:
                valid_prune = None
                valid_api = None
            else:
                valid_api = FakeWindowsAPI(root_final, target_final)
                valid_prune = windows_prune(
                    r"C:\safe\root",
                    ("nested", "managed.bin"),
                    windows_api=valid_api,
                )
            check(
                "Windows prune deletes opened in-root regular file by handle",
                valid_prune is True
                and valid_api.deleted == ["target"]
                and set(valid_api.closed)
                == {"root", "directory-1", "target"},
                repr(valid_api.deleted if valid_api else None),
            )

            def rejected(attributes=0x80, target_path=target_final, fail=False):
                if windows_prune is None:
                    return None, None
                fake = FakeWindowsAPI(root_final, target_path, attributes)
                fake.fail_final_path = fail
                try:
                    windows_prune(
                        r"C:\safe\root",
                        ("nested", "managed.bin"),
                        windows_api=fake,
                    )
                    error = None
                except Exception as caught:
                    error = caught
                return error, fake

            reparse_error, reparse_api = rejected(
                FakeWindowsAPI.FILE_ATTRIBUTE_REPARSE_POINT
            )
            directory_error, directory_api = rejected(
                FakeWindowsAPI.FILE_ATTRIBUTE_DIRECTORY
            )
            escaped_error, escaped_api = rejected(
                target_path=r"\\?\C:\outside\managed.bin"
            )
            uncertain_error, uncertain_api = rejected(fail=True)
            check(
                "Windows prune rejects reparse points and directories",
                isinstance(reparse_error, ValueError)
                and isinstance(directory_error, ValueError)
                and not reparse_api.deleted
                and not directory_api.deleted,
            )
            check(
                "Windows prune rejects escaped and uncertain final paths",
                isinstance(escaped_error, ValueError)
                and isinstance(uncertain_error, OSError)
                and not escaped_api.deleted
                and not uncertain_api.deleted,
            )

            if windows_prune is None:
                missing_result = None
                missing_api = None
            else:
                missing_api = FakeWindowsAPI(root_final, target_final)
                missing_api.fail_target_missing = True
                missing_result = windows_prune(
                    r"C:\safe\root",
                    ("nested", "missing.bin"),
                    windows_api=missing_api,
                )
            check(
                "missing Windows managed file is already clean",
                missing_result is False
                and missing_api.deleted == []
                and set(missing_api.closed) == {"root", "directory-1"},
                repr(missing_api.closed if missing_api else None),
            )

            original_platform = api_mod._uses_windows_prune
            original_windows_prune = (
                api_mod._prune_managed_download_file_windows
            )
            dispatched = []
            api_mod._uses_windows_prune = lambda: True
            api_mod._prune_managed_download_file_windows = (
                lambda local_root, parts: dispatched.append(
                    (local_root, parts)
                )
                or True
            )
            try:
                dispatch_result = api_mod._prune_managed_download_file(
                    root, "nested/managed.bin"
                )
            finally:
                api_mod._uses_windows_prune = original_platform
                api_mod._prune_managed_download_file_windows = (
                    original_windows_prune
                )
            check(
                "platform dispatcher selects Windows handle pruning",
                dispatch_result is True
                and len(dispatched) == 1
                and dispatched[0][0] == root.resolve()
                and dispatched[0][1] == ("nested", "managed.bin"),
                repr(dispatched),
            )
    finally:
        if original_fchmod is None:
            try:
                del os.fchmod
            except AttributeError:
                pass
        else:
            os.fchmod = original_fchmod
        os.environ.clear()
        os.environ.update(original_environment)

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
