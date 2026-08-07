# Current Issue Contract

# Issue CLI-BASELINE-CONTRACT

Status: `active`

## Identity

- Local Issue: `CLI-BASELINE-CONTRACT`
- Title: `Lock the existing CLI feature baseline with regression tests`
- Type: `testing`, `cli`, `compatibility`, `documentation`
- Priority: `P1`
- Branch: `codex/lock-cli-baseline` (local only)
- Base: `yuto`
- Previous Issue: `LOGIN-RESPONSE-BOUND`, delivered by `a1ed142`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Objective And Evidence

The current suite has strong focused tests, but the supported CLI baseline is
distributed across many files and there is no single executable contract that
enumerates every command, required option/argument, and minimal successful
dispatch. A later refactor can therefore remove or rename a basic capability
without one concise failure explaining which public contract regressed.

Create a human-readable feature inventory and a centralized offline regression
that protects the existing command tree, option aliases, help availability,
exit behavior, and minimum happy-path dispatch for every public command.

## Scope And Acceptance

- Inventory all current root, repository, branch, upload, and download commands.
- Record authentication requirements, remote effect, and important guarantees.
- Assert every existing command path remains present; future additive commands
  must not fail the baseline merely because they are new.
- Assert current public arguments and option aliases remain available.
- Invoke every leaf command through Click with isolated configuration, Git,
  filesystem, and strict API fakes; verify exit code and downstream parameters.
- Preserve all current runtime code and behavior; this Issue changes tests and
  documentation only.
- Do not test remote AtomGit, real HOME, real global Git configuration, or
  credentials; do not add features or fix audit findings in this Issue.

## Permissions

- The user explicitly requested stronger tests that prevent existing basic CLI
  functionality from regressing in later development.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- No live request, repository access, remote write, credential mutation, or
  external side effect is authorized or required.

## Required Evidence And Closure

- [x] The documented inventory covers every current public CLI command.
- [x] The centralized interface contract covers command paths and option aliases.
- [x] Every leaf command has a minimal isolated successful dispatch regression.
- [x] Existing focused tests and the complete offline suite pass.
- [x] Compileall, pip, diff, scope, credentials, and independent review pass.
- [ ] The task is committed, merged into `yuto`, and only `yuto` is pushed.

## Verification Evidence

- Inventory: `docs/cli_feature_baseline.md` records all 12 current leaf
  commands across authentication, configuration, repository and branch
  management, upload, repository download, and single-file download.
- Central contract: `python tests/test_cli_feature_baseline.py` passed `56/56`
  checks for command paths, arguments, option aliases, help pages, exit codes,
  strict API dispatch, isolated HOME/filesystem state, and token redaction.
- Focused compatibility: CLI surface passed `50/50`, create `42/42`, repository
  list `24/24`, visibility `30/30`, delete `48/48`, branch create `28/28`,
  upload validation `9/9`, download contract `45/45`, and CLI single-file
  download `15/15`.
- Complete offline suite: `python -m pytest -q` exited `0` with all `61`
  collected tests passing. `python -m compileall -q .`, `python -m pip check`,
  and `git diff --check` also passed in the `atomgit_cli` environment.
- Scope and compatibility: no runtime source, public implementation, dependency,
  or packaging file changed. Locked versions are confirmed as
  `huggingface-hub==1.1.7` and `datasets==4.4.1`.
- Security and isolation: strict fakes replace APIs, Git availability, HOME,
  and credentials; no live request, test repository access, remote write, real
  token, global Git mutation, or user-state mutation occurred.
- Independent review: `APPROVED` with no P0-P3 finding. The only residual risk
  is live service availability, which is outside this offline compatibility
  contract and does not require a live test for acceptance.
- Human acceptance is provided by the maintainer's explicit request to inventory
  existing features and prevent future regressions through stronger tests.
