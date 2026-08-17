#!/usr/bin/env python3
"""Offline contracts for the official, environment-scoped uninstaller."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

import atomgit


ROOT = Path(__file__).resolve().parents[1]
UNINSTALLER = ROOT / "uninstall.sh"
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail and not condition else ""))


def main():
    results.clear()
    cli_mod = sys.modules["atomgit.cli"]
    runner = CliRunner()

    help_result = runner.invoke(cli_mod.cli, ["uninstall", "--help"])
    check(
        "uninstall is public and has an automation flag",
        help_result.exit_code == 0 and "--yes" in help_result.output,
        help_result.output,
    )

    plan = {
        "python": sys.executable,
        "prefix": sys.prefix,
        "version": atomgit.__version__,
        "managed_paths": ("/isolated/atomgit-completion.sh",),
    }
    calls = []
    with patch.object(cli_mod, "build_uninstall_plan", return_value=plan), patch.object(
        cli_mod, "run_uninstall", side_effect=lambda selected: calls.append(selected)
    ):
        refused = runner.invoke(cli_mod.cli, ["uninstall"], input="n\n")
        refused_calls = list(calls)
        accepted = runner.invoke(cli_mod.cli, ["uninstall"], input="y\n")
        automated = runner.invoke(cli_mod.cli, ["uninstall", "--yes"])
    check(
        "interactive uninstall shows identity and confirms before mutation",
        refused.exit_code != 0
        and not refused_calls
        and sys.executable in refused.output
        and atomgit.__version__ in refused.output,
        refused.output,
    )
    check(
        "confirmed and automated uninstall dispatch the reviewed plan",
        accepted.exit_code == 0 and automated.exit_code == 0 and calls == [plan, plan],
        repr(calls),
    )

    import atomgit.uninstaller as uninstaller

    with patch.object(
        uninstaller, "_is_source_or_editable_install", return_value=True
    ):
        try:
            uninstaller.build_uninstall_plan()
        except uninstaller.UninstallError as error:
            editable_error = str(error)
        else:
            editable_error = ""
    check(
        "source and editable installs are rejected without pip mutation",
        "可编辑源码" in editable_error,
        editable_error,
    )

    runtime_plan = {
        "python": sys.executable,
        "prefix": str(Path(sys.prefix).resolve()),
        "version": atomgit.__version__,
        "managed_paths": (),
    }
    with patch.object(
        uninstaller, "build_uninstall_plan", return_value=runtime_plan
    ), patch.object(
        uninstaller, "active_conda_prefix", return_value=None
    ), patch.object(
        uninstaller,
        "subprocess",
    ) as subprocess_mock:
        subprocess_mock.run.return_value = subprocess.CompletedProcess([], 0)
        uninstaller.run_uninstall(runtime_plan)
    check(
        "package uninstall uses the running interpreter and exact pip command",
        subprocess_mock.run.call_args.args[0]
        == [sys.executable, "-m", "pip", "uninstall", "--yes", "atomgit"],
        repr(subprocess_mock.run.call_args),
    )

    with tempfile.TemporaryDirectory(prefix="atomgit-uninstall-contract-") as directory:
        root = Path(directory)
        prefix = root / "env"
        user_config = root / "home" / ".atomgit" / "config.json"
        user_config.parent.mkdir(parents=True)
        user_config.write_text('{"token": "preserved-test-value"}\n', encoding="utf-8")
        paths = uninstaller.managed_completion_paths(prefix)
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("managed\n", encoding="utf-8")
        unrelated = prefix / "etc" / "conda" / "activate.d" / "unrelated.sh"
        unrelated.write_text("keep\n", encoding="utf-8")

        removed = uninstaller.remove_managed_completion(prefix)
        removed_again = uninstaller.remove_managed_completion(prefix)
        check(
            "managed cleanup is exact, preserving user and unrelated data",
            {path.resolve() for path in removed} == {path.resolve() for path in paths}
            and removed_again == ()
            and all(not path.exists() for path in paths)
            and unrelated.read_text(encoding="utf-8") == "keep\n"
            and user_config.exists(),
        )

        symlink_target = root / "target"
        symlink_target.write_text("keep\n", encoding="utf-8")
        paths[0].parent.mkdir(parents=True, exist_ok=True)
        paths[0].symlink_to(symlink_target)
        try:
            uninstaller.remove_managed_completion(prefix)
        except uninstaller.UninstallError as error:
            symlink_error = str(error)
        else:
            symlink_error = ""
        check(
            "managed cleanup refuses symbolic links",
            bool(symlink_error) and symlink_target.read_text(encoding="utf-8") == "keep\n",
            symlink_error,
        )

        parent_symlink_prefix = root / "parent-symlink-env"
        parent_symlink_prefix.mkdir()
        outside_share = root / "outside-share"
        outside_file = outside_share / "atomgit/completions/atomgit.zsh"
        outside_file.parent.mkdir(parents=True)
        outside_file.write_text("outside-kept\n", encoding="utf-8")
        (parent_symlink_prefix / "share").symlink_to(outside_share)
        try:
            uninstaller.remove_managed_completion(parent_symlink_prefix)
        except uninstaller.UninstallError as error:
            parent_symlink_error = str(error)
        else:
            parent_symlink_error = ""
        check(
            "Python cleanup refuses symlinked parents outside the environment",
            bool(parent_symlink_error)
            and outside_file.read_text(encoding="utf-8") == "outside-kept\n",
            parent_symlink_error,
        )

        fallback_prefix = root / "fallback-conda"
        venv_result = subprocess.run(
            [sys.executable, "-m", "venv", str(fallback_prefix)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        fallback_python = fallback_prefix / "bin" / "python"
        fallback_paths = uninstaller.managed_completion_paths(fallback_prefix)
        for path in fallback_paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fallback-managed\n", encoding="utf-8")
        fallback_unrelated = (
            fallback_prefix / "etc/conda/activate.d/unrelated-fallback.sh"
        )
        fallback_unrelated.write_text("keep\n", encoding="utf-8")
        fallback_environment = os.environ.copy()
        fallback_environment.update(
            {"CONDA_PREFIX": str(fallback_prefix), "HOME": str(root / "home")}
        )
        fallback = subprocess.run(
            ["sh", str(UNINSTALLER), "--python", str(fallback_python)],
            cwd=str(root),
            env=fallback_environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        fallback_again = subprocess.run(
            ["sh", str(UNINSTALLER), "--python", str(fallback_python)],
            cwd=str(root),
            env=fallback_environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        check(
            "already-removed fallback executes exactly and is idempotent",
            venv_result.returncode == 0
            and fallback.returncode == 0
            and fallback_again.returncode == 0
            and all(not path.exists() for path in fallback_paths)
            and fallback_unrelated.read_text(encoding="utf-8") == "keep\n"
            and user_config.exists(),
            fallback.stderr + fallback_again.stderr,
        )

        (fallback_prefix / "share/atomgit/completions").rmdir()
        (fallback_prefix / "share/atomgit").rmdir()
        (fallback_prefix / "share").rmdir()
        fallback_outside_share = root / "fallback-outside-share"
        fallback_outside_file = (
            fallback_outside_share / "atomgit/completions/atomgit.zsh"
        )
        fallback_outside_file.parent.mkdir(parents=True)
        fallback_outside_file.write_text("outside-kept\n", encoding="utf-8")
        (fallback_prefix / "share").symlink_to(fallback_outside_share)
        fallback_symlink = subprocess.run(
            ["sh", str(UNINSTALLER), "--python", str(fallback_python)],
            cwd=str(root),
            env=fallback_environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        check(
            "shell fallback refuses symlinked parents outside the environment",
            fallback_symlink.returncode != 0
            and fallback_outside_file.read_text(encoding="utf-8")
            == "outside-kept\n",
            fallback_symlink.stderr,
        )

        dispatch_log = root / "dispatch.log"
        fake_python = root / "fake-installed-python"
        fake_python.write_text(
            "#!/bin/sh\n"
            'printf "%s\\n" "$*" >> "$ATOMGIT_UNINSTALL_TEST_LOG"\n'
            "exit 0\n",
            encoding="utf-8",
        )
        fake_python.chmod(0o755)
        installed_environment = os.environ.copy()
        installed_environment.pop("CONDA_PREFIX", None)
        installed_environment["ATOMGIT_UNINSTALL_TEST_LOG"] = str(dispatch_log)
        installed_dispatch = subprocess.run(
            ["sh", str(UNINSTALLER), "--python", str(fake_python)],
            cwd=str(root),
            env=installed_environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        dispatches = dispatch_log.read_text(encoding="utf-8").splitlines()
        check(
            "installed-package script dispatches the supported automated CLI path",
            installed_dispatch.returncode == 0
            and dispatches[-1] == "-m atomgit uninstall --yes",
            repr(dispatches),
        )

    text = UNINSTALLER.read_text(encoding="utf-8") if UNINSTALLER.exists() else ""
    check(
        "official uninstall script supports installed and already-removed states",
        'm.distribution("atomgit")' in text
        and '-m atomgit uninstall --yes' in text
        and "config.json" not in text,
        text[:500],
    )
    import atomgit.uninstaller as uninstaller

    check(
        "shell and Python cleanup share the exact managed path contract",
        all(
            str(relative) in text
            for relative in uninstaller.MANAGED_COMPLETION_RELATIVE_PATHS
        ),
    )
    check(
        "official uninstall script is POSIX syntax valid",
        UNINSTALLER.exists()
        and subprocess.run(
            ["sh", "-n", str(UNINSTALLER)], capture_output=True, text=True
        ).returncode
        == 0,
    )

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
