# Current Issue Contract

Status: `completed`

## Handoff Snapshot

- Updated: `2026-08-16 +0800`
- Phase: `implementation accepted, committed, merged into yuto, pushed, and GitHub Issue #25 closed`
- Base branch: `yuto`
- Task branch: `codex/fast-zsh-completion`
- Base commit: `b47cf06355bcddf79f32ab4856d7437841cbd2b8`
- Current HEAD before branch creation: `b47cf06355bcddf79f32ab4856d7437841cbd2b8`
- Task commit: `e9776bf feat(completion): add fast zsh completion`
- Merge commit: `f947ba8 merge: add fast zsh completion`
- Current HEAD before this final delivery record: `f947ba88340ca515778011ee09596c7f58afb6ae`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `clean after this final delivery record is committed and pushed`
- Changed paths: `none after the final delivery-record commit`
- Last completed action: `pushed yuto through f947ba8 and closed GitHub Issue #25 with final verification evidence`
- Next exact action: `none; reset TASK.md to inactive before selecting another Issue`
- Blockers: `none`
- Tests run: `pre-implementation test_shell_completion.py failed 6/12 as required; final post-review test_shell_completion.py passed 20/20, test_installer.py 21/21, and test_cli_feature_baseline.py 63/63; final python tests/run_cli_baseline.py passed 71/71 in 63.96s after the last review fix and documentation sync; python -m compileall -q ., python -m pip check, git diff --check, Click 8.4.2/HF 1.1.7/datasets 4.4.1 signature checks, credential diff scan, and completion performance probe passed; console completion first invocation was 0.0279 seconds and warm median was 0.0289 seconds`
- Required worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`

## Active Issue

- Remote Issue: `#25 https://github.com/JoyJeeo/atomgit_cli/issues/25`
- ID: `GH-25-FAST-ZSH-COMPLETION`
- Title: `Add fast, automatically installed Zsh completion`
- Primary type: `cli`
- Secondary type: `distribution`
- Priority: `P2`
- Observable objective: `derive Zsh completion from the live Click tree, keep completion on a lightweight import path, and enable it by default through the official installer`
- User impact: `Zsh users receive command, nested-command, option, choice, and local-path completion after official installation, while future Click commands join automatically`

## Starting Evidence

- Locked Click `8.4.2` already returns valid AtomGit completion candidates through `_ATOMGIT_COMPLETE=zsh_complete`.
- Current completion subprocesses take approximately 1.1-1.3 seconds after warm-up.
- Console startup executes package `__init__.py`, which eagerly imports `api`, `cli`, and `atomgit_hub`; the SDK reaches `datasets`, while `cli.py` independently imports the complete API and a utility module with an eager HF import.
- Candidate matching is lightweight; the delay comes from importing HF Hub, datasets, Torch, PyArrow, Pandas, and related modules first.
- Official `install.sh` verifies and installs a fixed wheel but does not configure completion.

## Current And Expected Behavior

- Current: Click's environment protocol can serve Zsh completion, but no public management command or installer integration exists and each candidate request imports the full business/SDK graph.
- Expected: package and command-schema imports remain lightweight; business dependencies load only when used; public completion commands manage the Zsh adapter; official installation enables it by default for Zsh with opt-out.

## Affected Call Path

```text
install.sh -> checksummed wheel install -> completion install for Zsh
Zsh Tab -> Click adapter -> lightweight package/command tree -> candidates
normal CLI -> Click parse -> command-local config/api/utils import -> business call
Python SDK -> compatible lazy package export -> SDK module only when requested
```

## Affected Capability IDs

- `FLOOR-REGISTRY`: register the focused test and new invariants.
- `CLI-SURFACE`: add the public completion group without changing old surface.
- `CLI-DISPATCH`: cover new leaves and preserve existing leaves.
- `SDK-DOWNLOAD`, `SDK-UPLOAD`, `SDK-REPO`: preserve lazy package exports and exception identities.
- `RUNTIME`: preserve HF environment ordering while excluding HF initialization from completion.
- `PACKAGING`: preserve wheel/entry/import contracts and extend the official installer.

## Protected Existing Invariants

- Existing CLI commands, parameters, defaults, types, help, dispatch, output meaning, and exit codes remain compatible.
- `atomgit`, `python -m atomgit`, console entrypoints, package-level SDK imports, and direct `atomgit_hub` APIs remain compatible on Python 3.9+.
- HF endpoint/cache/XET policy is configured before every real HF import.
- Config loading remains lazy and absent config paths are not created by imports.
- Wheel checksum verification, fixed release identity, and active-conda requirements remain unchanged.
- Offline tests remain isolated from real HOME, credentials, Git configuration, and network.

## New Or Changed Invariants

- Package and Click-schema imports for completion do not import `atomgit.api`, `atomgit_hub`, `huggingface_hub`, `datasets`, `torch`, `pyarrow`, or `pandas`.
- Completion does not read credentials, access the network, or create configuration/business state.
- Zsh completion uses only the live Click tree and includes every new non-hidden command without completion-specific command data.
- `completion show/install/uninstall` provide Zsh script output, idempotent installation, and idempotent removal.
- Completion management changes only AtomGit-owned script content and a bounded marked Zsh configuration block using safe atomic handling.
- Official `install.sh` enables completion only for Zsh by default, supports `--no-completion`, leaves non-Zsh startup files unchanged, and reports setup failure as a non-fatal warning after successful package installation.
- Raw `pip install` keeps standard packaging behavior and requires explicit completion installation.

## Scope

In scope:

- Add Python 3.9-compatible lazy package exports preserving current public imports.
- Keep `cli.py` metadata lightweight and move business imports behind command execution.
- Move or defer only constants/helpers that force heavy completion imports.
- Add Zsh-only `atomgit completion show/install/uninstall` using the locked Click contract.
- Add safe, atomic, idempotent completion-file and marked `.zshrc` management.
- Extend `install.sh` with default Zsh setup, `--no-completion`, and non-fatal warning semantics.
- Add/register focused offline coverage, exact schema/dispatch and floor entries, and architecture/CLI/install/user documentation.

Out of scope:

- No remote repository, branch, tag, or filename completion; no Bash/Fish completion; no daemon or candidate cache.
- No dependency upgrade, public command removal, release/tag/publication, live AtomGit operation, credential-helper mutation, or real startup-file mutation during tests.
- No non-standard setuptools/pip post-install hook.

## Compatibility Requirements

- Preserve Python `>=3.9`, Click `>=8.1.7`, `huggingface-hub==1.1.7`, and `datasets==4.4.1` contracts.
- Preserve exports in `atomgit.__all__`, including stable SDK exception identities.
- Preserve tests that import the package before submodules or patch module API objects.
- Bind script generation to the installed Click API and verify its real signature.
- Keep checksum and conda validation before installer completion setup.

## Acceptance Criteria

1. Zsh completes root/nested commands, options, Click choices, and local paths with descriptions where available.
2. A newly registered non-hidden command appears without completion-specific data or adapter reinstallation.
3. Completion does not import heavy modules, read credentials, access network, or create config files.
4. Existing CLI and package/direct SDK imports remain compatible, including exception identities and runtime ordering.
5. Completion management is documented, idempotent, preserves unrelated `.zshrc` content, and fails safely on unsafe targets.
6. Official install defaults completion on for Zsh, supports opt-out, preserves package success on a reported setup warning, and leaves non-Zsh startup files unchanged.
7. Structural import guards pass and maintainer warm completion median is at most 200 ms; timing is evidence rather than the sole CI gate.
8. Focused tests, affected regressions, wheel smoke, complete baseline, compileall, pip check, and diff check pass.
9. Architecture, CLI, release/install, development-floor, and README documentation agree with delivered behavior and direct-pip limitation.

## Focused Tests And Evidence

- Add/register `tests/test_shell_completion.py`; first demonstrate missing commands, eager imports, and installer integration failure.
- Use subprocesses and temporary HOME/ZDOTDIR; forbid network and real configuration reads.
- Prove dynamic discovery, Zsh source/candidates, no callback, no heavy modules, and no config creation.
- Extend installer regression for default/opt-out/non-Zsh/non-fatal behavior and exact invocation.
- Extend wheel smoke for packaged completion support and installed entry behavior.
- Update schema, leaf dispatch, test inventory, capability mappings, and affected documentation.
- Inspect real Click `8.4.2` signatures and locked HF/datasets versions.

## Complete Baseline Evidence

- Required: `python tests/run_cli_baseline.py` after the final implementation/review fix.
- Supporting: `python -m compileall -q .`, `python -m pip check`, `git diff --check`.
- Current result: `passed 71/71 in 63.96s after the final review fix and documentation sync`.

## Residual Risks

- Zsh frameworks initialize completion differently; offline tests cannot cover every plugin manager.
- Timing varies by machine/cache; the import boundary is authoritative and the 200 ms target is local evidence.
- Standard pip has no reliable cross-platform post-install hook, so direct pip users install completion explicitly.
- No live modification of the maintainer's `.zshrc` is required or authorized.

## Verification And Delivery

- Demonstrate focused failure before implementation, then run focused/affected tests and exact floor guards.
- Run the complete baseline, compileall, pip check, diff check, credential/artifact audit, and independent review.
- Delivery mode: `accepted local task commit, local merge into yuto, push only yuto, and close Issue #25`.
- Authorized: `create/update/close Issue #25; edit required source/tests/installer/docs; create local branch; run offline tests; review; commit; merge locally; push only yuto`.
- Not authorized: `task-branch push, PR, tag, release, publication, live AtomGit operation, real credentials/Git-helper/startup-file mutation`.
- Human acceptance: `accepted on 2026-08-16; maintainer explicitly authorized commit, merge, push, and Issue closure`.

## Review Record

- First verdict: `REQUEST CHANGES`.
- P2 finding: `completion.py could overwrite .zshrc edits made after its initial read during install or uninstall`.
- P2 finding: `an install failure after writing the adapter could leave a partial script or newly created backup`.
- Disposition: `added file snapshots and optimistic concurrency checks, transactional script/backup rollback, focused failure injection, and matching documentation`.
- Second verdict: `REQUEST CHANGES`.
- P2 finding: `when the original .zshrc had no final newline, configuration appended after the managed block could be concatenated with preceding content during uninstall`.
- Disposition: `preserve the separator whenever unmanaged suffix content exists and cover the exact append-then-uninstall sequence`.
- Final verdict: `APPROVED`; no open findings.
- Residual risk: `offline tests cannot cover every Zsh framework or eliminate the final platform-level check-to-replace race window; unsafe detected changes fail closed, and no real startup file was modified`.
