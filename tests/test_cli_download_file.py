#!/usr/bin/env python3
"""Offline CLI contract for downloading one repository file."""

import sys
from pathlib import Path

import atomgit  # noqa: F401
from click.testing import CliRunner


cli_mod = sys.modules["atomgit.cli"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    runner = CliRunner()
    root_help = runner.invoke(cli_mod.cli, ["--help"])
    check(
        "root help advertises single-file download",
        root_help.exit_code == 0 and "download-file" in root_help.output,
    )
    command_help = runner.invoke(cli_mod.cli, ["download-file", "--help"])
    check("download-file help succeeds", command_help.exit_code == 0)
    check(
        "download-file help names required arguments",
        "REPO_ID" in command_help.output and "FILENAME" in command_help.output,
    )

    original_download = cli_mod.api.download_file
    original_logged_in = cli_mod.config.is_logged_in
    calls = []

    def fake_download(
        repo_id, filename, local_path, force_download=False, repo_type=None
    ):
        calls.append(
            (repo_id, filename, Path(local_path), force_download, repo_type)
        )
        return True

    cli_mod.api.download_file = fake_download
    cli_mod.config.is_logged_in = lambda: False
    try:
        with runner.isolated_filesystem():
            default_result = runner.invoke(
                cli_mod.cli,
                ["download-file", "user/repo", "weights/model.bin"],
            )
            check("default single-file download succeeds", default_result.exit_code == 0)
            check(
                "default destination is current directory",
                calls[-1][2].resolve() == Path.cwd().resolve(),
                str(calls[-1][2]),
            )
            check(
                "repository filename is forwarded unchanged",
                calls[-1][1] == "weights/model.bin",
            )
            check(
                "anonymous mode is explained",
                "公开仓库" in default_result.output,
            )

            explicit_result = runner.invoke(
                cli_mod.cli,
                [
                    "download-file",
                    "user/repo",
                    "data/sample.csv",
                    "--directory",
                    "target",
                    "--force",
                    "--repo-type",
                    "dataset",
                ],
            )
            check("explicit single-file download succeeds", explicit_result.exit_code == 0)
            check(
                "all single-file options are forwarded",
                calls[-1]
                == (
                    "user/repo",
                    "data/sample.csv",
                    Path("target"),
                    True,
                    "dataset",
                ),
                repr(calls[-1]),
            )

            calls.clear()
            invalid_repo = runner.invoke(
                cli_mod.cli, ["download-file", "invalid", "README.md"]
            )
            check("invalid repository ID fails", invalid_repo.exit_code == 1)
            check("invalid repository ID avoids API", not calls)

            Path("destination-file").write_text("occupied")
            invalid_destination = runner.invoke(
                cli_mod.cli,
                [
                    "download-file",
                    "user/repo",
                    "README.md",
                    "--directory",
                    "destination-file",
                ],
            )
            check("file destination is rejected", invalid_destination.exit_code == 1)
            check("file destination avoids API", not calls)

            cli_mod.api.download_file = lambda *args, **kwargs: False
            failed = runner.invoke(
                cli_mod.cli,
                ["download-file", "user/repo", "missing.bin", "-d", "failed"],
            )
            check("API failure exits nonzero", failed.exit_code == 1)
            check("anonymous failure provides login guidance", "login" in failed.output)
    finally:
        cli_mod.api.download_file = original_download
        cli_mod.config.is_logged_in = original_logged_in

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
