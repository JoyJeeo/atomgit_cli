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

        completion_module = importlib.import_module("atomgit.completion")
        from atomgit.cli import cli

        isolated_home = patch.dict(
            os.environ,
            {"HOME": str(home), "ZDOTDIR": str(home)},
        )
        isolated_home.start()

        prefix_a = root / "conda-a"
        prefix_b = root / "conda-b"
        prefix_a.mkdir()
        prefix_b.mkdir()
        zshrc = home / ".zshrc"
        zshrc.write_text("export USER_SETTING=kept\n", encoding="utf-8")

        with patch.object(completion_module, "_active_conda_prefix", return_value=prefix_a):
            paths_a = completion_module.install_completion(cli)
            first_contents = tuple(path.read_text(encoding="utf-8") for path in paths_a)
            completion_module.install_completion(cli)
        check(
            "completion is owned only by the active conda environment",
            paths_a
            == (
                prefix_a / "share/atomgit/completions/atomgit.zsh",
                prefix_a / "etc/conda/activate.d/atomgit-completion.sh",
                prefix_a / "etc/conda/deactivate.d/atomgit-completion.sh",
            )
            and all(path.is_file() for path in paths_a)
            and tuple(path.read_text(encoding="utf-8") for path in paths_a)
            == first_contents
            and zshrc.read_text(encoding="utf-8") == "export USER_SETTING=kept\n"
            and not (home / ".atomgit").exists(),
        )
        check(
            "hooks use the locked Click function and unload before switching",
            "_atomgit_completion" in first_contents[1]
            and "compdef -d atomgit" in first_contents[1]
            and "_atomgit_completion" in first_contents[2]
            and "compdef -d atomgit" in first_contents[2],
        )

        with patch.object(completion_module, "_active_conda_prefix", return_value=prefix_b):
            paths_b = completion_module.install_completion(cli)
        check(
            "two conda environments own isolated completion adapters",
            all(path.is_file() for path in paths_a + paths_b)
            and set(paths_a).isdisjoint(paths_b),
        )

        for prefix in (prefix_a, prefix_b):
            environment_python = prefix / "bin/python"
            environment_python.parent.mkdir()
            environment_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            environment_python.chmod(0o755)
        paths_a[0].write_text(
            "_atomgit_completion() { print ENV_A; }\n"
            "compdef _atomgit_completion atomgit\n",
            encoding="utf-8",
        )
        paths_b[0].write_text(
            "_atomgit_completion() { print ENV_B; }\n"
            "compdef _atomgit_completion atomgit\n",
            encoding="utf-8",
        )
        switch_script = r'''
autoload -Uz compinit
compinit -d "$HOME/.zcompdump"
export CONDA_PREFIX="$1"
source "$2"
[[ "${functions[_atomgit_completion]}" == *ENV_A* ]] || exit 11
[[ "${_comps[atomgit]-}" == "_atomgit_completion" ]] || exit 12
source "$3"
(( ! $+functions[_atomgit_completion] )) || exit 13
[[ -z "${_comps[atomgit]-}" ]] || exit 14
export CONDA_PREFIX="$4"
source "$5"
[[ "${functions[_atomgit_completion]}" == *ENV_B* ]] || exit 15
[[ "${_comps[atomgit]-}" == "_atomgit_completion" ]] || exit 16
'''
        switched = run(
            [
                "zsh",
                "-f",
                "-c",
                switch_script,
                "zsh",
                prefix_a,
                paths_a[1],
                paths_a[2],
                prefix_b,
                paths_b[1],
            ],
            os.environ.copy(),
        )
        check(
            "Zsh deactivation unloads A before activation loads B",
            switched.returncode == 0,
            switched.stdout + switched.stderr,
        )

        paths_a[0].write_text(first_contents[0], encoding="utf-8")
        fake_python = prefix_a / "bin/python"
        fake_python.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        fake_python.chmod(0o755)
        warning = run(
            ["zsh", "-c", 'source "$1"', "zsh", paths_a[1]],
            {**os.environ, "CONDA_PREFIX": str(prefix_a)},
        )
        check(
            "post-pip activation warning is exact and non-mutating",
            warning.returncode == 0
            and warning.stderr == completion_module._ACTIVATION_WARNING
            and tuple(path.read_text(encoding="utf-8") for path in paths_a)
            == first_contents,
            warning.stderr,
        )

        with patch.object(completion_module, "_active_conda_prefix", return_value=prefix_a):
            completion_module.uninstall_completion()
            completion_module.uninstall_completion()
        check(
            "environment completion removal is exact and idempotent",
            all(not path.exists() for path in paths_a)
            and all(path.exists() for path in paths_b)
            and zshrc.read_text(encoding="utf-8") == "export USER_SETTING=kept\n",
        )

        old_script = home / ".atomgit/completions/atomgit.zsh"
        old_script.parent.mkdir(parents=True)
        old_script.write_text("legacy\n", encoding="utf-8")
        original_zshrc = "export USER_SETTING=kept\n"
        zshrc.write_text(
            original_zshrc + completion_module._managed_block(old_script, True),
            encoding="utf-8",
        )
        with patch.object(completion_module, "_active_conda_prefix", return_value=prefix_a):
            try:
                completion_module.install_completion(cli)
            except completion_module.CompletionConfigError as error:
                migration_error = str(error)
            else:
                migration_error = ""
            migrated_paths = completion_module.install_completion(
                cli, migrate_legacy=True
            )
        check(
            "legacy global completion requires confirmation and migrates safely",
            "明确确认" in migration_error
            and not old_script.exists()
            and zshrc.read_text(encoding="utf-8") == original_zshrc
            and (home / ".zshrc.atomgit.bak").is_file()
            and all(path.exists() for path in migrated_paths),
            migration_error,
        )

        no_newline_home = root / "legacy-no-newline-home"
        no_newline_home.mkdir()
        no_newline_script = no_newline_home / ".atomgit/completions/atomgit.zsh"
        no_newline_script.parent.mkdir(parents=True)
        no_newline_script.write_text("legacy\n", encoding="utf-8")
        no_newline_zshrc = no_newline_home / ".zshrc"
        no_newline_original = "export NO_FINAL_NEWLINE=1"
        no_newline_managed = (
            no_newline_original
            + "\n"
            + completion_module._managed_block(no_newline_script, False)
        )
        no_newline_zshrc.write_text(no_newline_managed, encoding="utf-8")
        no_newline_zshrc.chmod(0o640)
        no_newline_prefix = root / "legacy-no-newline-conda"
        no_newline_prefix.mkdir()
        with patch.dict(
            os.environ,
            {"HOME": str(no_newline_home), "ZDOTDIR": str(no_newline_home)},
        ), patch.object(
            completion_module,
            "_active_conda_prefix",
            return_value=no_newline_prefix,
        ):
            completion_module.install_completion(cli, migrate_legacy=True)
        no_newline_backup = no_newline_home / ".zshrc.atomgit.bak"
        check(
            "legacy migration preserves bytes, mode, backup, and final-newline state",
            no_newline_zshrc.read_text(encoding="utf-8") == no_newline_original
            and stat.S_IMODE(no_newline_zshrc.stat().st_mode) == 0o640
            and no_newline_backup.read_text(encoding="utf-8") == no_newline_managed
            and stat.S_IMODE(no_newline_backup.stat().st_mode) == 0o640,
        )

        concurrent_home = root / "legacy-concurrent-home"
        concurrent_home.mkdir()
        concurrent_script = concurrent_home / ".atomgit/completions/atomgit.zsh"
        concurrent_script.parent.mkdir(parents=True)
        concurrent_script.write_text("legacy\n", encoding="utf-8")
        concurrent_zshrc = concurrent_home / ".zshrc"
        concurrent_zshrc.write_text(
            "export BEFORE=1\n"
            + completion_module._managed_block(concurrent_script, True),
            encoding="utf-8",
        )
        concurrent_prefix = root / "legacy-concurrent-conda"
        concurrent_prefix.mkdir()
        actual_atomic_write = completion_module._atomic_write

        def edit_legacy_during_migration(path, *args, **kwargs):
            if path == concurrent_zshrc:
                concurrent_zshrc.write_text(
                    "export CONCURRENT_EDIT=kept\n",
                    encoding="utf-8",
                )
            return actual_atomic_write(path, *args, **kwargs)

        with patch.dict(
            os.environ,
            {"HOME": str(concurrent_home), "ZDOTDIR": str(concurrent_home)},
        ), patch.object(
            completion_module,
            "_active_conda_prefix",
            return_value=concurrent_prefix,
        ), patch.object(
            completion_module,
            "_atomic_write",
            side_effect=edit_legacy_during_migration,
        ):
            try:
                completion_module.install_completion(cli, migrate_legacy=True)
            except completion_module.CompletionConfigError as error:
                concurrent_error = str(error)
            else:
                concurrent_error = ""
        check(
            "legacy migration preserves a concurrent Zsh edit and rolls back environment files",
            "并发修改" in concurrent_error
            and concurrent_zshrc.read_text(encoding="utf-8")
            == "export CONCURRENT_EDIT=kept\n"
            and concurrent_script.exists()
            and all(
                not path.exists()
                for path in completion_module.managed_completion_paths(
                    concurrent_prefix
                )
            ),
            concurrent_error,
        )

        unsafe_prefix = root / "unsafe-conda"
        unsafe_prefix.mkdir()
        symlink_target = root / "outside-share"
        symlink_target.mkdir()
        (unsafe_prefix / "share").symlink_to(symlink_target)
        with patch.object(
            completion_module, "_active_conda_prefix", return_value=unsafe_prefix
        ):
            try:
                completion_module.install_completion(cli)
            except completion_module.CompletionConfigError as error:
                symlink_error = str(error)
            else:
                symlink_error = ""
        check(
            "completion refuses symlinked managed directories",
            "符号链接" in symlink_error and not list(symlink_target.iterdir()),
            symlink_error,
        )

        rollback_prefix = root / "rollback-conda"
        rollback_prefix.mkdir()
        rollback_paths = completion_module.managed_completion_paths(rollback_prefix)
        actual_atomic_write = completion_module._atomic_write

        def fail_second_write(path, *args, **kwargs):
            if path == rollback_paths[1]:
                raise completion_module.CompletionConfigError("injected failure")
            return actual_atomic_write(path, *args, **kwargs)

        with patch.object(
            completion_module, "_active_conda_prefix", return_value=rollback_prefix
        ), patch.object(
            completion_module, "legacy_completion_present", return_value=False
        ), patch.object(
            completion_module, "_atomic_write", side_effect=fail_second_write
        ):
            try:
                completion_module.install_completion(cli)
            except completion_module.CompletionConfigError as error:
                rollback_error = str(error)
            else:
                rollback_error = ""
        check(
            "multi-file completion install rolls back on failure",
            "injected failure" in rollback_error
            and all(not path.exists() for path in rollback_paths),
            rollback_error,
        )
        isolated_home.stop()

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
