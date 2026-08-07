# Current Issue Contract

# Issue CLI-BASELINE-DOD-GATE

Status: `active`

## Identity

- Local Issue: `CLI-BASELINE-DOD-GATE`
- Title: `Make the CLI feature baseline a mandatory DoD gate`
- Type: `process`, `testing`, `documentation`, `compatibility`
- Priority: `P1`
- Branch: `codex/require-cli-baseline-dod` (local only)
- Base: `yuto`
- Previous Issue: `CLI-BASELINE-CONTRACT`, delivered by `1004ff7`.
- Delivery mode: standing-authorized documentation change, review, commit,
  local merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Objective

Make `tests/test_cli_feature_baseline.py` a non-optional acceptance gate for
every feature and bug-fix Issue. A failing baseline must return the Issue to
implementation and block completion, delivery, and merge until the regression
is fixed and the gate passes.

## Scope And Acceptance

- Add an explicit mandatory CLI baseline gate to `.ai/DOD.md`.
- Require the gate after implementation and fixes, before acceptance, closure,
  delivery, or merge.
- Require failure evidence to trigger repair and repeated execution until all
  baseline checks pass.
- Prevent bypassing a regression by weakening the baseline unless the active
  Issue explicitly authorizes a public compatibility break.
- Require the command and result to be recorded in `TASK.md` evidence.
- Do not change runtime code, tests, dependencies, or unrelated workflow rules.

## Permissions

- The maintainer explicitly requested this DoD quality gate and repair loop.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- No live request, repository access, remote write other than the authorized
  `yuto` push, credential mutation, or external side effect is required.

## Required Evidence And Closure

- [x] DoD makes the CLI feature baseline mandatory for every feature/bug fix.
- [x] Failure blocks acceptance, completion, delivery, and merge until repaired.
- [x] Intentional compatibility changes require explicit authorization and an
      updated passing baseline rather than silently weakening the test.
- [x] The baseline test and documentation checks pass.
- [x] Diff, scope, credentials, and independent review pass.
- [ ] The task is committed, merged into `yuto`, and only `yuto` is pushed.

## Verification Evidence

- `.ai/DOD.md` now defines a non-optional gate for every feature and bug-fix
  Issue, even when the change is not expected to affect the CLI.
- The gate runs after implementation and every fix, before human acceptance,
  Issue completion, delivery, or merge. Failure blocks delivery and returns the
  active Issue to the repair-and-test loop until every check passes.
- The DoD forbids skipping, removing, or weakening the baseline to hide a
  regression. An intentional public compatibility break requires explicit
  maintainer authorization, matching docs and baseline changes, and a passing
  final gate.
- `python tests/test_cli_feature_baseline.py` passed `56/56` in the
  `atomgit_cli` environment; the command and referenced files exist.
- `git diff --check`, documentation consistency, scope, and credential scans
  passed. Only `.ai/DOD.md` and `.ai/TASK.md` changed; no runtime, test,
  dependency, packaging, credential, Git-helper, or remote behavior changed.
- Full pytest, compileall, and pip checks were not repeated because this is a
  process-documentation-only change; the mandatory executable baseline did run.
- Independent review: `APPROVED` with no P0-P3 finding and no runtime or live
  service residual risk introduced by this change.
- Human acceptance is provided by the maintainer's explicit instruction to add
  this mandatory blocking and repair loop to the DoD.
