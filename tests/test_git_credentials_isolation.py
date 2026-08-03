#!/usr/bin/env python3
"""Verify Git credential isolation without touching user-owned Git state."""

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

from click.testing import CliRunner


results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def git(*args, input_text=None, check_result=True):
    result = subprocess.run(
        ["git", *args],
        input=input_text,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    if check_result and result.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed with {result.returncode}: {result.stderr}"
        )
    return result


def set_values(key, values):
    git("config", "--global", "--unset-all", key, check_result=False)
    for value in values:
        git("config", "--global", "--add", key, value)


def get_values(key):
    result = git("config", "--global", "--get-all", key, check_result=False)
    if result.returncode == 1:
        return []
    if result.returncode != 0:
        raise AssertionError(f"failed to read {key}: {result.stderr}")
    return result.stdout.splitlines()


def mode(path):
    return stat.S_IMODE(path.stat().st_mode)


def main():
    original_env = os.environ.copy()
    utils = None
    real_run = None
    try:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            home = root / "home"
            home.mkdir()
            global_config = root / "global.gitconfig"
            marker = root / "generic-helper-called"
            generic_helper = root / "generic-helper.py"
            generic_helper.write_text(
                """#!/usr/bin/env python3
import os
import sys

operation = sys.argv[1] if len(sys.argv) > 1 else "get"
for line in sys.stdin:
    if not line.strip():
        break
with open(os.environ["GENERIC_HELPER_MARKER"], "a", encoding="utf-8") as stream:
    stream.write(operation + "\\n")
""",
                encoding="utf-8",
            )
            generic_helper.chmod(0o755)

            os.environ.update({
                "HOME": str(home),
                "GIT_CONFIG_GLOBAL": str(global_config),
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_TERMINAL_PROMPT": "0",
                "GENERIC_HELPER_MARKER": str(marker),
            })
            # Import only after HOME/global config are isolated and system
            # configuration is disabled.
            from atomgit import utils as isolated_utils

            utils = isolated_utils
            real_run = utils.subprocess.run
            git(
                "config", "--global",
                "credential.helper", f"!{generic_helper}",
            )

            atomgit_key = "credential.https://atomgit.com.helper"
            hub_key = "credential.https://hub.atomgit.com.helper"
            original_atomgit = ["!original-one", "!original-two"]
            original_hub = ["!hub-original"]
            set_values(atomgit_key, original_atomgit)
            set_values(hub_key, original_hub)

            check("T1 setup succeeds", utils.setup_git_credentials("fake-token-never-print"))
            helper_path = home / ".atomgit" / "git-credential-atomgit"
            state_path = home / ".atomgit" / "git-helper-state.json"
            expected_managed = ["", f"!{helper_path}"]
            check("T2 atomgit host resets inherited helpers",
                  get_values(atomgit_key) == expected_managed,
                  repr(get_values(atomgit_key)))
            check("T3 hub host resets inherited helpers",
                  get_values(hub_key) == expected_managed,
                  repr(get_values(hub_key)))
            check("T4 helper state exists with mode 0600",
                  state_path.exists() and mode(state_path) == 0o600,
                  oct(mode(state_path)) if state_path.exists() else "missing")

            state = json.loads(state_path.read_text(encoding="utf-8"))
            check("T5 state preserves original atomgit values",
                  state["hosts"]["atomgit.com"] == original_atomgit)
            check("T6 state preserves original hub values",
                  state["hosts"]["hub.atomgit.com"] == original_hub)
            check("T7 state contains no token", "token" not in state_path.read_text())

            check("T8 repeated setup succeeds",
                  utils.setup_git_credentials("different-fake-token-never-print"))
            repeated_state = json.loads(state_path.read_text(encoding="utf-8"))
            check("T9 repeated setup keeps original backup", repeated_state == state)

            credential_input = (
                "protocol=https\nhost=atomgit.com\n"
                "username=test-user\npassword=fake-password-never-print\n\n"
            )
            marker.unlink(missing_ok=True)
            fill = git(
                "credential", "fill",
                input_text="protocol=https\nhost=atomgit.com\n\n",
                check_result=False,
            )
            check("T10 atomgit lookup does not invoke inherited helper",
                  not marker.exists(), f"exit={fill.returncode}")
            git("credential", "approve", input_text=credential_input)
            git("credential", "reject", input_text=credential_input)
            check("T11 atomgit store/erase do not invoke inherited helper",
                  not marker.exists())

            unrelated_input = (
                "protocol=https\nhost=example.com\n"
                "username=test-user\npassword=fake-password-never-print\n\n"
            )
            git("credential", "approve", input_text=unrelated_input)
            check("T12 unrelated host still invokes generic helper",
                  marker.read_text(encoding="utf-8").splitlines() == ["store"])

            check("T13 cleanup succeeds", utils.clear_git_credentials())
            check("T14 atomgit original values restored",
                  get_values(atomgit_key) == original_atomgit,
                  repr(get_values(atomgit_key)))
            check("T15 hub original values restored",
                  get_values(hub_key) == original_hub,
                  repr(get_values(hub_key)))
            check("T16 owned files removed",
                  not helper_path.exists() and not state_path.exists())

            rollback_atomgit = ["!rollback-atomgit"]
            rollback_hub = ["!rollback-hub-one", "!rollback-hub-two"]
            set_values(atomgit_key, rollback_atomgit)
            set_values(hub_key, rollback_hub)

            failure_injected = False

            def fail_second_host(args, *run_args, **run_kwargs):
                nonlocal failure_injected
                if (
                    not failure_injected
                    and "--add" in args
                    and hub_key in args
                    and args[-1].startswith("!")
                ):
                    failure_injected = True
                    return subprocess.CompletedProcess(
                        args=args, returncode=1, stdout="", stderr="forced failure"
                    )
                return real_run(args, *run_args, **run_kwargs)

            utils.subprocess.run = fail_second_host
            check("T17 partial setup reports failure",
                  not utils.setup_git_credentials("fake-token-never-print"))
            utils.subprocess.run = real_run
            check("T18 partial setup restores atomgit state",
                  get_values(atomgit_key) == rollback_atomgit,
                  repr(get_values(atomgit_key)))
            check("T19 partial setup restores hub state",
                  get_values(hub_key) == rollback_hub,
                  repr(get_values(hub_key)))
            check("T20 failed first setup removes owned files",
                  not helper_path.exists() and not state_path.exists())

            persistent_atomgit = ["!persistent-atomgit"]
            persistent_hub = ["!persistent-hub"]
            set_values(atomgit_key, persistent_atomgit)
            set_values(hub_key, persistent_hub)
            persistent_failure_started = False

            def fail_second_host_and_rollback(args, *run_args, **run_kwargs):
                nonlocal persistent_failure_started
                if "git" == args[0] and hub_key in args and (
                    persistent_failure_started or "--add" in args
                ):
                    persistent_failure_started = True
                    return subprocess.CompletedProcess(
                        args=args, returncode=1, stdout="", stderr="forced failure"
                    )
                return real_run(args, *run_args, **run_kwargs)

            utils.subprocess.run = fail_second_host_and_rollback
            check("T21 failed rollback reports setup failure",
                  not utils.setup_git_credentials("fake-token-never-print"))
            utils.subprocess.run = real_run
            preserved_state = json.loads(state_path.read_text(encoding="utf-8"))
            check("T22 failed rollback preserves recovery state",
                  preserved_state["hosts"]["atomgit.com"] == persistent_atomgit
                  and preserved_state["hosts"]["hub.atomgit.com"] == persistent_hub)
            check("T23 failed rollback preserves owned helper",
                  helper_path.exists())
            check("T24 recovery cleanup succeeds", utils.clear_git_credentials())
            check("T25 recovery cleanup restores both hosts",
                  get_values(atomgit_key) == persistent_atomgit
                  and get_values(hub_key) == persistent_hub)

            check("T26 setup for cleanup failure succeeds",
                  utils.setup_git_credentials("fake-token-never-print"))
            real_unlink = Path.unlink

            def fail_state_unlink(path, *unlink_args, **unlink_kwargs):
                if path == state_path:
                    raise OSError("forced state cleanup failure")
                return real_unlink(path, *unlink_args, **unlink_kwargs)

            Path.unlink = fail_state_unlink
            try:
                check("T27 file cleanup failure is reported",
                      not utils.clear_git_credentials())
            finally:
                Path.unlink = real_unlink
            check("T28 file cleanup failure keeps restored Git values",
                  get_values(atomgit_key) == persistent_atomgit
                  and get_values(hub_key) == persistent_hub)
            check("T29 stale recovery state can be cleaned",
                  utils.clear_git_credentials())
            check("T30 final cleanup removes owned state", not state_path.exists())

            import importlib
            cli_module = importlib.import_module("atomgit.cli")
            original_is_logged_in = cli_module.config.is_logged_in
            original_clear_credentials = cli_module.config.clear_credentials
            original_git_available = cli_module.check_git_available
            original_clear_git = cli_module.clear_git_credentials
            login_state = {"logged_in": True}
            cleanup_results = iter((False, True))
            cleanup_calls = []

            def clear_login():
                login_state["logged_in"] = False

            def clear_git():
                cleanup_calls.append(True)
                return next(cleanup_results)

            cli_module.config.is_logged_in = lambda: login_state["logged_in"]
            cli_module.config.clear_credentials = clear_login
            cli_module.check_git_available = lambda: True
            cli_module.clear_git_credentials = clear_git
            state_path.write_text("{}", encoding="utf-8")
            try:
                runner = CliRunner()
                first_logout = runner.invoke(cli_module.cli, ["logout"])
                check("T31 cleanup failure makes logout nonzero",
                      first_logout.exit_code != 0,
                      f"exit={first_logout.exit_code}")
                check("T32 partial logout explains recovery failure",
                      "Git 凭证配置恢复失败" in first_logout.output)
                second_logout = runner.invoke(cli_module.cli, ["logout"])
                check("T33 logged-out retry runs Git cleanup again",
                      second_logout.exit_code == 0 and len(cleanup_calls) == 2,
                      f"exit={second_logout.exit_code} calls={len(cleanup_calls)}")
            finally:
                cli_module.config.is_logged_in = original_is_logged_in
                cli_module.config.clear_credentials = original_clear_credentials
                cli_module.check_git_available = original_git_available
                cli_module.clear_git_credentials = original_clear_git
                state_path.unlink(missing_ok=True)
    finally:
        if utils is not None and real_run is not None:
            utils.subprocess.run = real_run
        os.environ.clear()
        os.environ.update(original_env)

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
