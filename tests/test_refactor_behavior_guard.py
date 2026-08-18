#!/usr/bin/env python3
"""Lock representative deterministic CLI observations and dispatch calls."""

import sys
from click.testing import CliRunner

import atomgit  # noqa: F401


cli_module = sys.modules["atomgit.cli"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def main():
    runner = CliRunner()
    original_update = cli_module.run_update
    original_plan = cli_module.build_uninstall_plan
    original_uninstall = cli_module.run_uninstall
    try:
        update_calls = []

        def skipped_update(**kwargs):
            update_calls.append(kwargs)
            return {"status": "skipped", "version": "1.1.1"}

        cli_module.run_update = skipped_update
        update = runner.invoke(
            cli_module.cli,
            ["update", "--version", "1.1.1", "--force-reinstall"],
            prog_name="atomgit",
        )
        check(
            "successful update observation is exact",
            update.exit_code == 0
            and update.stdout == "AtomGit CLI 已是 1.1.1，跳过更新。\n"
            and update.stderr == ""
            and update.exception is None,
            repr((update.exit_code, update.stdout, update.stderr, update.exception)),
        )
        check(
            "update dispatch preserves target, arguments, and call count",
            update_calls
            == [{
                "version": "1.1.1",
                "force_reinstall": True,
                "python": sys.executable,
            }],
            repr(update_calls),
        )

        plan = {
            "python": "/env/bin/python",
            "prefix": "/env",
            "version": "1.1.1",
            "managed_paths": (),
        }
        uninstall_calls = []
        cli_module.build_uninstall_plan = lambda: dict(plan)
        cli_module.run_uninstall = uninstall_calls.append
        aborted = runner.invoke(
            cli_module.cli,
            ["uninstall"],
            input="n\n",
            prog_name="atomgit",
        )
        expected_stdout = (
            "Python 解释器: /env/bin/python\n"
            "环境根目录: /env\n"
            "AtomGit 版本: 1.1.1\n"
            "环境补全文件: 无（当前解释器不属于活动 conda 环境）\n"
            "确认卸载 AtomGit CLI？ [y/N]: n\n"
        )
        check(
            "abort prompt, streams, and exit status are exact",
            aborted.exit_code == 1
            and aborted.stdout == expected_stdout
            and aborted.stderr == "Aborted!\n"
            and isinstance(aborted.exception, SystemExit),
            repr((aborted.exit_code, aborted.stdout, aborted.stderr)),
        )
        check("aborted uninstall performs no downstream mutation", uninstall_calls == [])

        secret = "raw-refactor-secret"
        usage = runner.invoke(
            cli_module.cli,
            ["login", "--token", secret, "--token-stdin"],
            prog_name="atomgit",
        )
        expected_stderr = (
            "Usage: atomgit login [OPTIONS]\n"
            "Try 'atomgit login --help' for help.\n\n"
            "Error: --token 与 --token-stdin 不能同时使用\n"
        )
        check(
            "usage failure preserves exact streams and redacts the supplied token",
            usage.exit_code == 2
            and usage.stdout == ""
            and usage.stderr == expected_stderr
            and secret not in usage.output
            and isinstance(usage.exception, SystemExit),
            repr((usage.exit_code, usage.stdout, usage.stderr)),
        )
        raised_usage = runner.invoke(
            cli_module.cli,
            ["login", "--token", secret, "--token-stdin"],
            prog_name="atomgit",
            standalone_mode=False,
        )
        check(
            "non-standalone dispatch preserves the Click exception category",
            raised_usage.exit_code == 1
            and raised_usage.stdout == ""
            and raised_usage.stderr == ""
            and isinstance(raised_usage.exception, cli_module.click.UsageError)
            and secret not in str(raised_usage.exception),
            repr(raised_usage.exception),
        )
    finally:
        cli_module.run_update = original_update
        cli_module.build_uninstall_plan = original_plan
        cli_module.run_uninstall = original_uninstall

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
