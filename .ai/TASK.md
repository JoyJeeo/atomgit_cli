# Current Issue Contract

Status: active

## Handoff Snapshot

- Updated: 2026-08-17 +0800
- Phase: implementation accepted, independently reviewed, and fully verified;
  ready for authorized task-branch commit and local merge into yuto
- Base branch: yuto
- Proposed task branch: feature/conda-completion-uninstall (local only; never
  push the task branch)
- Base commit: 8dac686c68b4a141bbdcfa5f23e3fdd8a283a531
- Task branch: feature/conda-completion-uninstall (local only; never push)
- Current HEAD: 8dac686c68b4a141bbdcfa5f23e3fdd8a283a531
- Worktree: /Users/yutaozhang/yuto/codes/atomgit_cli
- Worktree state before this handoff edit: clean on yuto and synchronized with
  github/yuto
- Changed paths: .ai/ARCHITECTURE.md, .ai/PRODUCT.md, .ai/TASK.md, MANIFEST.in,
  README.md, cli.py, completion.py, install.sh, release.py, uninstall.sh,
  uninstaller.py, docs/architecture.md, docs/cli_feature_baseline.md,
  docs/development_floor.md, docs/testing.md, tests/cli_baseline_contract.py,
  tests/development_floor_contract.py, tests/test_cli_feature_baseline.py,
  tests/test_cli_surface.py, tests/test_installer.py,
  tests/test_shell_completion.py, tests/test_uninstaller.py, and
  tests/test_wheel_smoke.py
- Last completed action: resolved two independent-review rounds of findings,
  passed the third review with APPROVED, and reran the complete baseline and
  static gates after the final symlink-parent fix
- Next exact action: create the authorized conventional task commit, merge it
  locally into yuto, then create local release/1.1.1 from that exact yuto SHA
- Blockers: none for local development
- Tests run for this Issue: focused completion 19/19, installer contracts,
  uninstaller 14/14, updater contracts, wheel smoke 28/28, development-floor
  contract 15/15, and complete baseline 74 passed; shell syntax, locked Click
  rendering, pip check, compileall, and diff check also passed
- Required continuation worktree while this handoff is uncommitted:
  /Users/yutaozhang/yuto/codes/atomgit_cli

## Active Issue

- Remote Issue: none; do not create one without explicit authorization
- ID: LOCAL-DIST-CONDA-COMPLETION-UNINSTALL
- Title: Isolate Zsh completion by conda environment and add official uninstall
- Primary type: distribution
- Secondary types: cli, compatibility, documentation, testing
- Priority: P2
- Observable objective: ordinary users can install and uninstall AtomGit
  through official curl entrypoints while each conda environment owns and
  loads only its own AtomGit Zsh completion; non-official pip removal is
  detected later and reported without silent cleanup
- User impact: switching conda environments no longer shares stale global
  completion, complete uninstall has one supported path, and users who bypass
  it receive an exact actionable warning rather than unexplained residual
  completion

## Authorization And Delivery

- User authorization: the maintainer explicitly accepted this design and asked
  that it be persisted as the next local Issue for continued development
- Authorized local actions: create the local task branch from yuto; edit
  completion, CLI, installer, uninstaller, tests, documentation, executable
  development-floor contracts, and TASK.md; create temporary isolated
  environment fixtures; run offline tests, packaging checks, and independent
  review
- Remote actions: maintainer authorized completion of delivery for version
  1.1.1 on 2026-08-17: merge locally into yuto, push only yuto, and publish the
  immutable GitHub Release through the protected workflow; never push the task
  or release-preparation branch and do not publish to PyPI/TestPyPI
- Live AtomGit actions: none required or authorized
- Delivery mode: complete implementation and independent review, merge the
  task and release-preparation branches locally into yuto, push only yuto, then
  dispatch and verify the protected release workflow
- Release decision: maintainer selected and authorized stable version 1.1.1;
  this explicit choice overrides the earlier SemVer recommendation for a minor
  version despite the new public uninstall command
- Prohibited: PyPI/TestPyPI publication, historical 1.1.0 tag or Release
  mutation, pushing local task/release branches, global credential/config
  deletion, unrelated runtime changes, upstream main changes, and silent
  cleanup triggered by post-pip detection

## Evidence And Constraints

- AtomGit 1.1.0 is already published as an immutable GitHub Release.
- The current official installer selects a checksummed GitHub Release wheel and
  supports conda, venv, and ordinary Python 3.9+ without requiring conda.
- Current completion install writes a user-global script under
  ~/.atomgit/completions and a managed block in ~/.zshrc, so different conda
  environments share one completion definition.
- Removing completion files does not unload functions already sourced into the
  current Zsh process.
- A child process started through curl-pipe-sh or python-m-atomgit cannot mutate
  its parent Zsh process. Disk cleanup commands must therefore print an exact
  reactivation or exec-zsh instruction when in-memory state may remain.
- pip has no reliable package post-install or post-uninstall callback. Direct
  python -m pip install/uninstall is a non-official path and cannot be
  intercepted reliably by AtomGit.
- The warning after non-official pip removal must be implemented by a standalone
  conda activation hook left by the official installer. It must not depend on
  importing AtomGit after the package has been removed.
- Detection is read-only. It may inspect package presence and managed paths and
  print guidance, but it must not delete, rewrite, reinstall, invoke pip, or
  change user configuration.
- huggingface-hub==1.1.7, datasets==4.4.1, Click 8.4.2, Python >=3.9, both CLI
  entry points, and all unrelated CLI/SDK behavior remain locked compatibility
  contracts.

## Accepted Product Design

### Official Commands

The supported ordinary-user lifecycle is:

    curl -fsSL https://raw.githubusercontent.com/JoyJeeo/atomgit_cli/yuto/install.sh | sh
    curl -fsSL https://raw.githubusercontent.com/JoyJeeo/atomgit_cli/yuto/uninstall.sh | sh
    atomgit completion install
    atomgit completion uninstall
    atomgit uninstall

The completion commands have no scope option and operate only on the current
active conda environment. The uninstall command may expose an explicit yes flag
for the official non-interactive script while remaining confirm-before-delete
for direct interactive use.

### Environment-Owned Completion

For an active conda environment, managed files live only below CONDA_PREFIX:

    $CONDA_PREFIX/share/atomgit/completions/atomgit.zsh
    $CONDA_PREFIX/etc/conda/activate.d/atomgit-completion.sh
    $CONDA_PREFIX/etc/conda/deactivate.d/atomgit-completion.sh

- Activation loads the completion generated by that environment's installed
  AtomGit.
- Deactivation removes that environment's in-memory completion binding before
  another environment loads its own.
- Exact Click-generated functions and compdef cleanup must be derived from the
  real locked Click 8.4.2 output before implementation.
- New installs do not write ~/.zshrc or a global ~/.atomgit completion.
- Non-conda package installation remains supported; automatic Zsh completion is
  skipped with an accurate message rather than making conda mandatory.

### Completion Management

- atomgit completion install writes only the current conda environment's
  managed script and hooks and is atomic, idempotent, symlink-safe, and
  concurrency-safe.
- atomgit completion uninstall removes only those current-environment files.
- Neither command can directly unload the parent shell when invoked as a child
  process; when necessary it prints the exact command to reactivate the
  environment or execute exec zsh.
- Existing global managed completion is not silently removed. Migration must
  identify the old managed block, explain the change, and require explicit user
  confirmation while preserving all unrelated .zshrc content and backups.

### Complete Uninstall

- atomgit uninstall shows the selected interpreter, environment root, package
  version, and managed targets before mutation and asks for confirmation unless
  an explicit automation flag is supplied.
- It cleans the current environment's completion and conda hooks, then invokes
  that same interpreter's python -m pip uninstall atomgit.
- It preserves ~/.atomgit/config.json, credentials, caches, repositories, and
  every unrelated user or conda file.
- It rejects source/editable installs with accurate developer guidance.
- uninstall.sh is an official, idempotent cleanup entrypoint. It works both
  while AtomGit is installed and after pip has already removed the package.
- If the package still exists, uninstall.sh uses the supported internal
  uninstall path. If it is absent, the script cleans only the exact managed
  environment paths after showing what will change.

### Non-Official pip Removal Warning

After python -m pip uninstall atomgit, the next activation of an environment
that still owns AtomGit completion prints exactly this guidance and performs no
other action:

    [AtomGit] 检测到 atomgit 已通过 pip 卸载，但当前环境仍有补全配置。

    请执行官方清理命令：
      curl -fsSL https://raw.githubusercontent.com/JoyJeeo/atomgit_cli/yuto/uninstall.sh | sh

    当前 shell 中已加载的补全需要重新启动 Zsh：
      exec zsh

The warning repeats on later activations until the user explicitly runs the
official cleanup. It does not create a marker, rewrite a hook, or silently
acknowledge itself.

## Current And Expected Behavior

### Current

- Official installation writes a global completion file and managed .zshrc
  block.
- Completion is shared across conda environments rather than owned by one.
- There is no official uninstall.sh or public atomgit uninstall command.
- Direct pip removal can leave global completion with no lifecycle guidance.

### Expected

- Official conda installation writes only environment-owned completion and
  activation/deactivation hooks.
- Switching environments unloads the previous environment's binding and loads
  the active environment's schema.
- Official uninstall cleans package-owned environment state while preserving
  user data.
- Direct pip removal remains possible but unsupported; the next activation
  emits the accepted warning without mutation.
- Plain Python and venv installation remain functional and receive a truthful
  completion-skipped message.

## Scope

### In Scope

- Refactor completion path/state ownership from global user files to the active
  conda environment.
- Add safe conda activation and deactivation hooks.
- Add public atomgit uninstall with confirmation and an automation flag.
- Add official uninstall.sh with installed-package and already-removed fallback
  behavior.
- Update install.sh and update-time completion refresh to the environment model.
- Add explicit legacy-global migration behavior with confirmation.
- Add exact non-mutating pip-removal warning behavior.
- Update CLI schema, dispatch, development-floor registry, user documentation,
  installation/uninstallation guidance, and focused tests.

### Out Of Scope

- Intercepting, wrapping, disabling, or replacing pip.
- Publishing AtomGit on PyPI or TestPyPI.
- Automatic cleanup after detecting non-official pip removal.
- Deleting user credentials, configuration, caches, repositories, or unrelated
  shell/conda files.
- Bash/Fish completion, non-conda activation frameworks, dependency upgrades,
  runtime feature work, version selection, tag creation, or Release publication.

## Affected Capability IDs

- FLOOR-REGISTRY: register all new tests and monotonic invariants.
- CLI-SURFACE: add atomgit uninstall and its exact parameters/help.
- CLI-DISPATCH: prove uninstall dispatch and failure/confirmation exits.
- RUNTIME: preserve completion's no-network, no-credential, lightweight path.
- PACKAGING: installer, uninstaller, completion ownership, and recovery warning.
- PORTABILITY: preserve non-conda installation and supported Python behavior.

## Protected Existing Invariants

- FLOOR-001 through FLOOR-004 remain complete, monotonic, isolated, and
  blocking.
- CLI-001 through CLI-004 preserve the exact existing public schema, usable
  entry points, live-schema completion, and update options except for the
  explicitly added uninstall command.
- DISPATCH-001 preserves successful isolated dispatch for every public leaf.
- RUNTIME-003 completion never imports business dependencies, reads
  credentials, accesses the network, or creates AtomGit runtime configuration.
- PKG-001 and PKG-002 preserve wheel entry points and safe installer/deploy
  invocation.
- PKG-004 through PKG-008 preserve checksummed stable Release selection and all
  protected publication behavior.
- PORT-001 through PORT-003 preserve Python/platform safety and installation
  without requiring conda.

## New Or Changed Invariants

- CLI-005: atomgit uninstall has an exact registered schema, confirms destructive
  intent by default, uses the running interpreter, and rejects source/editable
  installs.
- PKG-003 changes through an authorized compatibility migration: official Zsh
  completion is owned by the active conda environment rather than global
  ~/.zshrc state, while install opt-out and safe failure reporting remain.
- PKG-009: environment activation/deactivation loads and unloads only the
  active conda environment's AtomGit completion.
- PKG-010: official internal and curl uninstall paths are idempotent, remove
  only exact package-managed environment state, and preserve all user data.
- PKG-011: an environment with AtomGit removed by pip and managed completion
  remaining emits the exact accepted warning on activation and performs no
  mutation.
- PORT-004: non-conda installation remains supported and skips environment-only
  completion with accurate guidance.

## Acceptance Criteria

1. No new installation writes global ~/.zshrc or
   ~/.atomgit/completions/atomgit.zsh.
2. Two isolated synthetic conda environments can own distinct completion
   scripts; deactivating A removes A's binding before B loads B's binding.
3. Completion install/uninstall operates only under the active matching
   CONDA_PREFIX, is idempotent and symlink/concurrency safe, and never touches
   another environment.
4. Legacy global completion migration requires explicit confirmation and
   preserves unrelated .zshrc bytes, mode, final newline, backups, and
   concurrent edits.
5. atomgit uninstall is present in the exact CLI schema, prompts by default,
   supports explicit automation, uses sys.executable, and rejects editable
   installs.
6. Official uninstall preserves configuration, credentials, cache, repositories,
   and unrelated environment files.
7. uninstall.sh succeeds both before and after direct pip removal and is
   idempotent.
8. The post-pip activation path prints the accepted Chinese warning exactly and
   produces no filesystem, package, environment, or shell-config mutation.
9. Commands that cannot modify their parent Zsh print accurate exec-zsh or
   reactivation guidance.
10. Non-conda installation and both CLI entry points remain functional without
    global completion side effects.
11. README and authoritative docs describe official versus non-official
    lifecycle behavior and the future-release requirement accurately.
12. Independent review returns APPROVED with no open P0/P1; all focused checks,
    the complete baseline, compileall, pip check, and diff check pass.

## Required Implementation Investigation

- Capture the real Click 8.4.2 Zsh adapter and function/compdef names.
- Verify conda activate.d/deactivate.d sourcing order for Zsh and environment
  switches without relying on transcript assumptions.
- Reuse or deliberately extend the existing editable-install detection in
  release.py rather than duplicating incompatible logic.
- Define exact environment matching between CONDA_PREFIX, sys.prefix, selected
  --python, and executable paths, including symlinked interpreters.
- Define a single manifest of managed paths shared contractually by Python and
  shell cleanup so uninstall.sh fallback cannot drift.

## Focused Tests And Evidence

- Extend tests/test_shell_completion.py for environment paths, activation,
  deactivation, migration confirmation, isolation, symlinks, modes, concurrent
  edits, parent-shell guidance, and no business imports/network/config.
- Extend tests/test_installer.py for conda-owned setup, non-conda skip,
  --no-completion, exact interpreter selection, and hook contents.
- Add tests/test_uninstaller.py for installed and already-pip-removed states,
  confirmation, automation, editable refusal, idempotency, exact target
  ownership, preserved user data, and exact warning-only activation behavior.
- Register the new script in tests/cli_baseline_contract.py and map it to the
  affected development-floor capabilities and invariants.
- Update tests/test_cli_feature_baseline.py, tests/test_cli_surface.py,
  tests/development_floor_contract.py, tests/test_development_floor.py,
  tests/test_update.py, and tests/test_wheel_smoke.py as required by the exact
  CLI, update-refresh, package, and floor contracts.
- Use isolated temporary HOME, CONDA_PREFIX, ZDOTDIR, Git config, and synthetic
  environment trees. No test may inspect the maintainer's real credentials or
  mutate the real ~/.zshrc or active conda environment.

## Required Verification

- Focused scripts listed above in the atomgit_cli conda environment.
- Shell syntax checks for install.sh, uninstall.sh, and generated hooks.
- Real locked Click 8.4.2 adapter inspection.
- Isolated wheel build/install smoke for both entry points and the new command.
- python tests/run_cli_baseline.py after the final implementation edit and
  after every review fix.
- python -m compileall -q .
- python -m pip check.
- git diff --check plus artifact, credential, generated-file, and unrelated-diff
  audit.
- Independent review is mandatory because the change affects installation,
  deletion, shell startup, public CLI surface, and packaging.
- Live AtomGit evidence: not applicable.

## Completion And Release Boundary

- Complete-baseline evidence: `python tests/run_cli_baseline.py` passed all 74
  isolated offline cases in 61.72 seconds after the final review fix.
- Independent review: APPROVED on the third review. Round one requested changes
  for missing executable fallback/shell-switch/migration evidence, incomplete
  shell fingerprints, and dead migration code. Round two found that Python and
  shell cleanup could follow symlinked parent directories. All findings were
  fixed, covered by regression tests, and reverified; no P0/P1/P2/P3 remains.
- Human acceptance: accepted for end-to-end delivery by the maintainer's
  explicit 2026-08-17 instruction to complete development, verification,
  commit, upload, and publish 1.1.1 after the recorded gates pass.
- Additional evidence: focused scripts and isolated wheel smoke passed; Click
  8.4.2 rendered `_atomgit_completion`; conda 26.1.1 source/order inspection
  confirmed deactivate-before-prefix-change and activate-after-prefix-change;
  `sh -n` and `zsh -n` checks, `python -m pip check`,
  `python -m compileall -q .`, `git diff --check`, artifact inspection, and
  credential-pattern audit passed.
- Remaining risks: behavior is executable against Zsh 5.9 and synthetic conda
  environments but has not been manually exercised across older conda/Zsh
  combinations; child processes cannot unload their parent shell and therefore
  print reactivation/`exec zsh` guidance by design.
- Release boundary: maintainer selected and authorized 1.1.1; release identity
  and notes will be prepared on a separate local release branch only after this
  Issue is reviewed and merged locally into yuto.
