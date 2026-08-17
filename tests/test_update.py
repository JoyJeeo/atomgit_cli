#!/usr/bin/env python3
"""Offline contracts for the public Release-based updater."""

import sys
from pathlib import Path

from click.testing import CliRunner

import atomgit


RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append((name, condition, detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    cli_mod = sys.modules["atomgit.cli"]
    runner = CliRunner()
    help_result = runner.invoke(cli_mod.cli, ["update", "--help"])
    check("update is a public command", help_result.exit_code == 0 and "--version" in help_result.output)
    check("update exposes force reinstall", "--force-reinstall" in help_result.output)

    original = cli_mod.run_update
    try:
        calls = []
        cli_mod.run_update = lambda **kwargs: calls.append(kwargs) or {
            "status": "skipped",
            "version": atomgit.__version__,
        }
        result = runner.invoke(cli_mod.cli, ["update"])
        check("update targets the running interpreter", result.exit_code == 0 and calls and calls[0]["python"] == sys.executable)
        check(
            "equal-version update reports a skip",
            atomgit.__version__ in result.output and "跳过" in result.output,
        )

        cli_mod.run_update = lambda **kwargs: {"status": "source", "version": None}
        source_result = runner.invoke(cli_mod.cli, ["update"])
        check(
            "source update is refused without mutation",
            source_result.exit_code != 0 and "git checkout yuto" in source_result.output,
        )
        invalid_result = runner.invoke(cli_mod.cli, ["update", "--version", "v1.2.3"])
        check("update rejects legacy v versions", invalid_result.exit_code == 2)
    finally:
        cli_mod.run_update = original

    if any(not passed for _, passed, _ in RESULTS):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
