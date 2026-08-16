#!/usr/bin/env python3
"""Zsh completion stays dynamic, lightweight, local, and safely managed."""

import json
import importlib
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_IMPORTS = (
    "atomgit.api",
    "atomgit.atomgit_hub",
    "atomgit_hub",
    "huggingface_hub",
    "datasets",
    "torch",
    "pyarrow",
    "pandas",
)
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def run(command, environment):
    return subprocess.run(
        [str(part) for part in command],
        cwd=str(REPOSITORY_ROOT),
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
    )


def completion_environment(home, words, current):
    environment = os.environ.copy()
    environment.update(
        {
            "HOME": str(home),
            "ZDOTDIR": str(home),
            "_ATOMGIT_COMPLETE": "zsh_complete",
            "COMP_WORDS": words,
            "COMP_CWORD": str(current),
        }
    )
    return environment


def completion_command():
    return [
        sys.executable,
        "-c",
        (
            "from atomgit.cli import cli; "
            "cli.main(prog_name='atomgit', complete_var='_ATOMGIT_COMPLETE')"
        ),
    ]


def main():
    results.clear()
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        home = root / "home"
        home.mkdir()

        import_probe = run(
            [
                sys.executable,
                "-c",
                (
                    "import json, sys; import atomgit.cli; "
                    f"names={FORBIDDEN_IMPORTS!r}; "
                    "print(json.dumps([name for name in names if name in sys.modules]))"
                ),
            ],
            completion_environment(home, "atomgit r", 1),
        )
        imported = None
        if import_probe.returncode == 0:
            try:
                imported = json.loads(import_probe.stdout)
            except json.JSONDecodeError:
                imported = None
        check(
            "completion command schema excludes heavy business imports",
            import_probe.returncode == 0 and imported == [],
            import_probe.stdout.strip() or import_probe.stderr.strip(),
        )

        root_completion = run(
            completion_command(),
            completion_environment(home, "atomgit re", 1),
        )
        check(
            "native Zsh protocol completes a root command",
            root_completion.returncode == 0 and "\nrepo\n" in root_completion.stdout,
            root_completion.stdout or root_completion.stderr,
        )
        check(
            "completion creates no AtomGit configuration state",
            not (home / ".atomgit").exists(),
            str(list(home.iterdir())),
        )

        option_completion = run(
            completion_command(),
            completion_environment(home, "atomgit upload --re", 2),
        )
        check(
            "Zsh protocol completes command options",
            option_completion.returncode == 0
            and "--repo-id" in option_completion.stdout
            and "--repo-type" in option_completion.stdout
            and "--revision" in option_completion.stdout,
            option_completion.stdout or option_completion.stderr,
        )

        choice_completion = run(
            completion_command(),
            completion_environment(home, "atomgit repo create user/repo --type d", 5),
        )
        check(
            "Zsh protocol completes Click choices",
            choice_completion.returncode == 0
            and "\ndataset\n" in choice_completion.stdout,
            choice_completion.stdout or choice_completion.stderr,
        )

        path_completion = run(
            completion_command(),
            completion_environment(home, "atomgit upload ./", 2),
        )
        check(
            "Zsh protocol delegates local path completion",
            path_completion.returncode == 0
            and path_completion.stdout.startswith("file\n"),
            path_completion.stdout or path_completion.stderr,
        )

        dynamic_script = (
            "import click; from atomgit.cli import cli; "
            "cli.add_command(click.Command('future-command', "
            "callback=lambda: (_ for _ in ()).throw(RuntimeError('called')))); "
            "cli.main(prog_name='atomgit', complete_var='_ATOMGIT_COMPLETE')"
        )
        dynamic_completion = run(
            [sys.executable, "-c", dynamic_script],
            completion_environment(home, "atomgit future", 1),
        )
        check(
            "new Click commands join completion without a second registry",
            dynamic_completion.returncode == 0
            and "\nfuture-command\n" in dynamic_completion.stdout,
            dynamic_completion.stdout or dynamic_completion.stderr,
        )

        normal_environment = os.environ.copy()
        normal_environment.update(
            {"HOME": str(home), "ZDOTDIR": str(home), "SHELL": "/bin/zsh"}
        )
        show = run(
            [sys.executable, "-m", "atomgit", "completion", "show", "zsh"],
            normal_environment,
        )
        check(
            "public show command emits the Click Zsh adapter",
            show.returncode == 0
            and "#compdef atomgit" in show.stdout
            and "_ATOMGIT_COMPLETE=zsh_complete" in show.stdout,
            show.stdout or show.stderr,
        )

        zshrc = home / ".zshrc"
        zshrc.write_text("export USER_SETTING=kept\n", encoding="utf-8")
        install = run(
            [sys.executable, "-m", "atomgit", "completion", "install", "--shell", "zsh"],
            normal_environment,
        )
        completion_file = home / ".atomgit" / "completions" / "atomgit.zsh"
        installed_zshrc = zshrc.read_text(encoding="utf-8")
        check(
            "completion install writes only managed Zsh content",
            install.returncode == 0
            and completion_file.is_file()
            and (home / ".zshrc.atomgit.bak").read_text(encoding="utf-8")
            == "export USER_SETTING=kept\n"
            and "export USER_SETTING=kept" in installed_zshrc
            and installed_zshrc.count(">>> atomgit completion >>>") == 1
            and installed_zshrc.count("<<< atomgit completion <<<") == 1,
            install.stdout or install.stderr,
        )
        check(
            "completion files use private modes without changing HOME",
            stat.S_IMODE(home.stat().st_mode) != 0o700
            and stat.S_IMODE((home / ".atomgit").stat().st_mode) == 0o700
            and stat.S_IMODE(completion_file.parent.stat().st_mode) == 0o700
            and stat.S_IMODE(completion_file.stat().st_mode) == 0o600,
            oct(stat.S_IMODE(home.stat().st_mode)),
        )
        install_again = run(
            [sys.executable, "-m", "atomgit", "completion", "install", "--shell", "zsh"],
            normal_environment,
        )
        check(
            "completion installation is idempotent",
            install_again.returncode == 0
            and zshrc.read_text(encoding="utf-8") == installed_zshrc,
            install_again.stdout or install_again.stderr,
        )

        uninstall = run(
            [sys.executable, "-m", "atomgit", "completion", "uninstall", "--shell", "zsh"],
            normal_environment,
        )
        check(
            "completion uninstall preserves unrelated Zsh configuration",
            uninstall.returncode == 0
            and not completion_file.exists()
            and zshrc.read_text(encoding="utf-8") == "export USER_SETTING=kept\n",
            uninstall.stdout or uninstall.stderr,
        )
        uninstall_again = run(
            [sys.executable, "-m", "atomgit", "completion", "uninstall", "--shell", "zsh"],
            normal_environment,
        )
        check(
            "completion removal is idempotent",
            uninstall_again.returncode == 0,
            uninstall_again.stdout or uninstall_again.stderr,
        )

        appended_home = root / "appended-home"
        appended_home.mkdir()
        appended_zshrc = appended_home / ".zshrc"
        appended_zshrc.write_text("export BEFORE=1", encoding="utf-8")
        appended_environment = normal_environment.copy()
        appended_environment.update(
            {"HOME": str(appended_home), "ZDOTDIR": str(appended_home)}
        )
        appended_install = run(
            [sys.executable, "-m", "atomgit", "completion", "install"],
            appended_environment,
        )
        with appended_zshrc.open("a", encoding="utf-8") as file:
            file.write("export AFTER=1\n")
        appended_uninstall = run(
            [sys.executable, "-m", "atomgit", "completion", "uninstall"],
            appended_environment,
        )
        check(
            "completion removal separates configuration appended after its block",
            appended_install.returncode == 0
            and appended_uninstall.returncode == 0
            and appended_zshrc.read_text(encoding="utf-8")
            == "export BEFORE=1\nexport AFTER=1\n",
            appended_uninstall.stdout or appended_uninstall.stderr,
        )

        malformed_home = root / "malformed-home"
        malformed_home.mkdir()
        malformed_zshrc = malformed_home / ".zshrc"
        malformed_content = "# >>> atomgit completion >>>\nuser-content\n"
        malformed_zshrc.write_text(malformed_content, encoding="utf-8")
        malformed_environment = normal_environment.copy()
        malformed_environment.update(
            {"HOME": str(malformed_home), "ZDOTDIR": str(malformed_home)}
        )
        malformed = run(
            [sys.executable, "-m", "atomgit", "completion", "install"],
            malformed_environment,
        )
        check(
            "malformed managed markers fail without changing Zsh content",
            malformed.returncode != 0
            and malformed_zshrc.read_text(encoding="utf-8") == malformed_content,
            malformed.stdout or malformed.stderr,
        )

        symlink_home = root / "symlink-home"
        symlink_home.mkdir()
        symlink_target = symlink_home / "real-zshrc"
        symlink_target.write_text("export LINK_TARGET=kept\n", encoding="utf-8")
        (symlink_home / ".zshrc").symlink_to(symlink_target)
        symlink_environment = normal_environment.copy()
        symlink_environment.update(
            {"HOME": str(symlink_home), "ZDOTDIR": str(symlink_home)}
        )
        symlink_result = run(
            [sys.executable, "-m", "atomgit", "completion", "install"],
            symlink_environment,
        )
        check(
            "symbolic-link Zsh configuration fails closed",
            symlink_result.returncode != 0
            and symlink_target.read_text(encoding="utf-8")
            == "export LINK_TARGET=kept\n",
            symlink_result.stdout or symlink_result.stderr,
        )

        relative_environment = normal_environment.copy()
        relative_environment["ZDOTDIR"] = "relative-zdotdir"
        relative_result = run(
            [sys.executable, "-m", "atomgit", "completion", "install"],
            relative_environment,
        )
        check(
            "relative ZDOTDIR fails closed",
            relative_result.returncode != 0
            and "绝对路径" in (relative_result.stdout + relative_result.stderr),
            relative_result.stdout or relative_result.stderr,
        )

        completion_module = importlib.import_module("atomgit.completion")
        concurrent_home = root / "concurrent-home"
        concurrent_home.mkdir()
        concurrent_zshrc = concurrent_home / ".zshrc"
        concurrent_zshrc.write_text("export ORIGINAL=1\n", encoding="utf-8")
        actual_atomic_write = completion_module._atomic_write

        def edit_during_install(path, *args, **kwargs):
            if path == concurrent_zshrc:
                concurrent_zshrc.write_text("export CONCURRENT=1\n", encoding="utf-8")
            return actual_atomic_write(path, *args, **kwargs)

        concurrent_environment = {
            "HOME": str(concurrent_home),
            "ZDOTDIR": str(concurrent_home),
        }
        install_error = None
        with patch.dict(os.environ, concurrent_environment), patch.object(
            completion_module,
            "_atomic_write",
            side_effect=edit_during_install,
        ):
            try:
                completion_module.install_completion(None)
            except completion_module.CompletionConfigError as error:
                install_error = error
        concurrent_script = (
            concurrent_home / ".atomgit" / "completions" / "atomgit.zsh"
        )
        check(
            "completion install preserves concurrent Zsh edits and rolls back",
            install_error is not None
            and "并发修改" in str(install_error)
            and concurrent_zshrc.read_text(encoding="utf-8")
            == "export CONCURRENT=1\n"
            and not concurrent_script.exists()
            and not (concurrent_home / ".zshrc.atomgit.bak").exists(),
            str(install_error),
        )

        script_failure_home = root / "script-failure-home"
        script_failure_home.mkdir()
        script_failure_zshrc = script_failure_home / ".zshrc"
        script_failure_zshrc.write_text("export ORIGINAL=2\n", encoding="utf-8")
        script_failure_environment = {
            "HOME": str(script_failure_home),
            "ZDOTDIR": str(script_failure_home),
        }
        script_failure_path = (
            script_failure_home / ".atomgit" / "completions" / "atomgit.zsh"
        )

        def fail_script_write(path, *args, **kwargs):
            if path == script_failure_path:
                raise completion_module.CompletionConfigError("injected script failure")
            return actual_atomic_write(path, *args, **kwargs)

        script_error = None
        with patch.dict(os.environ, script_failure_environment), patch.object(
            completion_module,
            "_atomic_write",
            side_effect=fail_script_write,
        ):
            try:
                completion_module.install_completion(None)
            except completion_module.CompletionConfigError as error:
                script_error = error
        check(
            "completion install removes a new backup when script setup fails",
            script_error is not None
            and script_failure_zshrc.read_text(encoding="utf-8")
            == "export ORIGINAL=2\n"
            and not script_failure_path.exists()
            and not (script_failure_home / ".zshrc.atomgit.bak").exists(),
            str(script_error),
        )

        with patch.dict(os.environ, concurrent_environment):
            completion_module.install_completion(None)
        installed_content = concurrent_zshrc.read_text(encoding="utf-8")

        def edit_during_uninstall(path, *args, **kwargs):
            if path == concurrent_zshrc:
                concurrent_zshrc.write_text(
                    installed_content + "export CONCURRENT=2\n",
                    encoding="utf-8",
                )
            return actual_atomic_write(path, *args, **kwargs)

        uninstall_error = None
        with patch.dict(os.environ, concurrent_environment), patch.object(
            completion_module,
            "_atomic_write",
            side_effect=edit_during_uninstall,
        ):
            try:
                completion_module.uninstall_completion()
            except completion_module.CompletionConfigError as error:
                uninstall_error = error
        check(
            "completion uninstall preserves concurrent Zsh edits",
            uninstall_error is not None
            and "并发修改" in str(uninstall_error)
            and concurrent_zshrc.read_text(encoding="utf-8").endswith(
                "export CONCURRENT=2\n"
            )
            and concurrent_script.exists(),
            str(uninstall_error),
        )

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
