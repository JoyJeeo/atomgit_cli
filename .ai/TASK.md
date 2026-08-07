# Current Issue Contract

# Issue CLI-BASELINE-MONOTONIC

Status: `completed`

## Identity

- Local Issue: `CLI-BASELINE-MONOTONIC`
- Title: `Make the CLI regression baseline comprehensive and monotonic`
- Type: `testing`, `cli`, `compatibility`, `process`
- Priority: `P1`
- Branch: `codex/strengthen-cli-baseline` (local only)
- Base: `yuto`
- Previous Issue: `CLI-BASELINE-DOD-GATE`, delivered by `263063c`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Objective

The current baseline protects the presence of known commands and option aliases
with subset comparisons and 56 lightweight checks. It deliberately allows new
commands or options without baseline registration and does not execute the 61
existing focused offline regression scripts. A feature can therefore expand the
public surface without updating the baseline, while the mandatory DoD command
still exercises only happy-path smoke behavior.

Turn the baseline into a monotonic contract: the full public CLI schema and all
offline regression scripts must be explicitly registered, new public surface or
new tests must update that registration, and one mandatory runner must execute
the complete offline suite. Regressions must be fixed in implementation code;
the baseline may change only for an explicitly authorized compatibility change
or a genuine new capability with matching tests and documentation.

## Scope And Acceptance

- Replace subset command checks with an exact public CLI schema contract that
  includes root/group/leaf paths, parameter order and kind, option aliases,
  required/default/flag semantics, types, and choices.
- Add a complete capability registry covering every current offline
  `tests/test_*.py` script; unregistered additions and stale registrations fail.
- Add guard regressions proving an unregistered command, option/schema change,
  missing leaf dispatch, and unregistered test script are detected.
- Preserve isolated successful dispatch coverage for every current leaf command.
- Add one comprehensive baseline runner that executes the entire isolated
  pytest matrix, not only the interface smoke checks.
- Update DoD and testing documentation so new features must add focused tests,
  register them in the baseline, update the exact schema when applicable, and
  pass the comprehensive gate.
- Document that regressions are repaired in runtime code; weakening a baseline
  is forbidden without explicit maintainer authorization for a compatibility
  break.
- Preserve runtime code, dependencies, packaging, CLI behavior, and all current
  tests. No live AtomGit operation is in scope.

## Permissions

- The maintainer explicitly requested a comprehensive, monotonically growing
  baseline and mandatory repair loop for future feature development.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- No live request, test repository access, credential mutation, Git-helper
  mutation, remote write other than the authorized `yuto` push, or release is
  authorized or required.

## Required Evidence And Closure

- [x] A regression test fails against the previous permissive baseline.
- [x] Exact CLI schema drift and incomplete leaf dispatch coverage are blocked.
- [x] Every offline test script is explicitly registered and the registry is
      exact in both directions.
- [x] The comprehensive baseline runner executes the full isolated test matrix.
- [x] DoD and maintainer documentation enforce monotonic feature registration
      and implementation-first regression repair.
- [x] Focused regressions, comprehensive baseline, full suite, compileall, pip,
      diff, scope, credentials, and independent review pass.
- [x] The task is committed, merged into `yuto`, and only `yuto` is pushed.

## Verification Evidence

- Previous-gap regression: before implementation,
  `python tests/test_cli_baseline_guard.py` exited `1` with `0/1`; the previous
  baseline exposed none of the exact-schema, registry, dispatch, or monotonic
  validators required by the new guard.
- Guard result: the same command now passes `14/14`, proving unregistered
  commands and options, unregistered or stale test scripts, missing leaf
  dispatches, inert non-executing tests, and runner failure propagation are all
  detected. Monotonic ledger totals are 15 command paths, 40 public parameters,
  12 leaf commands, and 62 offline scripts.
- Exact interface result: `python tests/test_cli_feature_baseline.py` passes
  `47/47`. It checks root/group/leaf schema, parameter order and declarations,
  required/default/type/path/Choice/flag/help semantics, test registration and
  entrypoints, leaf coverage, and isolated happy-path API dispatch.
- Mandatory comprehensive result: `python tests/run_cli_baseline.py` invokes
  the complete isolated pytest matrix and passed all `62` collected cases in
  `60.01s` with no skip. Each legacy script runs in a subprocess with temporary
  HOME and Git configuration through `tests/pytest_offline_scripts.py`.
- Process contract: `.ai/DOD.md`, `.ai/TESTING.md`, `docs/testing.md`, README,
  and `docs/cli_feature_baseline.md` require focused tests for new behavior,
  exact schema/dispatch updates for public CLI growth, registration for every
  new script, and implementation repair rather than baseline weakening.
- Compatibility: implicit Click unset defaults and false `show_default` values
  are normalized by effective public semantics rather than Click internals.
  The installed Click is `8.4.2`; locked dependencies remain
  `huggingface-hub==1.1.7` and `datasets==4.4.1`.
- Required checks: `python -m compileall -q .`, `python -m pip check`, and
  `git diff --check` passed in the `atomgit_cli` environment.
- Scope and security: runtime source, dependencies, packaging, CLI behavior,
  credentials, Git helper, and remote state are unchanged. No live request or
  test repository operation ran; the credential scan found only an existing
  explicitly fake authorization fixture.
- Independent review: `APPROVED` with no P0-P3 finding. Residual governance
  risk from deliberately editing both tests and contracts is controlled by the
  explicit compatibility authorization rule and independent diff review.
- Human acceptance is provided by the maintainer's explicit request for this
  comprehensive monotonic baseline and implementation-first repair loop.
- Delivery implementation commit: `9f471bf` (`test(cli): enforce monotonic
  feature baseline`). The closure commit is merged locally through the standing
  delivery workflow; the task branch remains local-only and only `yuto` is
  pushed.
