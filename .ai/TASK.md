# Current Issue Contract

# Issue DOWNLOAD-EXISTING-FILES

Status: `completed`

## Identity

- Local Issue: `DOWNLOAD-EXISTING-FILES`
- Title: `Existing downloads are described as resumable although they are only skipped`
- Type: `bug`, `cli`, `documentation`
- Priority: `P1`
- Branch: `codex/clarify-download-existing-files` (local only)
- Base: `yuto`

## Previous Issue (Closed)

- `DOWNLOAD-REPO-TYPE` was delivered by `6a344cd` and merged by `a278b45`.

## Evidence And Scope

The CLI says an existing non-empty destination enables resumable mode, but the
implementation only checks whether each path exists and skips it without size
or checksum verification. This can falsely imply integrity or partial-transfer
recovery.

In scope: preserve the maintainer-selected default of skipping existing files,
state that skipped content is not verified, retain `--force` as the explicit
overwrite mechanism, and align CLI/API output, tests, and README.

Out of scope: checksums, remote metadata, partial-file resume, and changing the
default overwrite policy.

## Acceptance Criteria

- Default downloads skip existing paths without fetching them.
- Output clearly says the skipped content was not verified and names `--force`.
- No output describes download skipping as resumable behavior.
- `--force` continues to fetch and replace existing paths.
- Focused/full tests and required checks pass.

## Permissions And Delivery

- Authorized: local edits/commits, local merge into `yuto`, and push only
  `yuto`; task branches remain local-only.
- Remote validation is not required because the behavior is local and existing
  live download compatibility was verified in the preceding Issue.
- Human acceptance: standing acceptance granted for the approved full plan.
- Implementation: existing paths remain skipped by default, but CLI and API
  output now explicitly say content is not verified and point to `--force`;
  the misleading download-resume claim was removed and README matches.
- Regression evidence: before the fix, 7/11 assertions passed; all four output
  semantics assertions failed while skip/force mechanics already worked.
- Focused regression: 11/11 assertions passed.
- Complete offline suite: 41/41 passed in 39.09 seconds.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Independent review: no open findings (`APPROVED`). Residual behavior is
  intentional: existence is the only default skip criterion; integrity checks
  require a future explicitly scoped feature.
- Human acceptance: standing acceptance granted for the approved full plan.
- Commit/merge/push: authorized and pending.
