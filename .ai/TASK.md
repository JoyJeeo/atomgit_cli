# Current Issue Contract

# Issue UPLOAD-OPTION-CONFLICTS

Status: `completed`

## Identity

- Local Issue: `UPLOAD-OPTION-CONFLICTS`
- Title: `Upload silently ignores incompatible options`
- Type: `bug`, `cli`
- Priority: `P1`
- Branch: `codex/reject-upload-option-conflicts` (local only)
- Base: `yuto`

## Previous Issue (Closed)

- `REPO-ID-CANONICALIZATION` was delivered by `570feb7` and merged by `bd786a3`.

## Evidence And Scope

Resumable directory upload ignores `path_in_repo` and commit `message`, single
file upload ignores `--resumable`, `--num-workers` without resumable has no
effect, and single-file `--ignore` can ambiguously upload an empty temporary
folder while reporting success.

In scope: reject those CLI conflicts with exit code 2 before upload calls,
retain valid directory resumable and ordinary single-file/directory behavior,
and align help, README, and existing regressions.

Out of scope: changing HF resumable capabilities, direct Python API compatibility,
and adding support for resumable subdirectories or commit messages.

## Acceptance Criteria

- Resumable plus path/message is rejected without an upload call.
- Num-workers without resumable is rejected without an upload call.
- Single-file resumable and single-file ignore are rejected without upload.
- Valid directory resumable options and ordinary uploads remain supported.
- Help/README state the conflicts and focused/full checks pass.

## Permissions And Delivery

- Authorized: local edits/commits, local merge into `yuto`, and push only
  `yuto`; task branches remain local-only.
- Tests are offline and no remote write is required.
- Human acceptance: standing acceptance granted for the approved full plan.
- Implementation: CLI now rejects ineffective resumable path/message, orphaned
  workers, and single-file resumable/ignore combinations with exit code 2.
  Pure local validation precedes authentication, and valid upload paths are
  unchanged. Help and README document the constraints.
- Regression evidence: all four affected scripts failed before implementation;
  resumable path/single-file and single-file ignore still exited 0 and invoked
  upload, while orphaned workers/path/message conflicts were accepted.
- Focused tests: 6/6 affected pytest cases passed; validation includes a 9/9
  matrix and verifies conflicts precede authentication.
- Complete offline suite: 42/42 passed in 34.54 seconds.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Independent review: first pass found validation ordering behind authentication;
  it was moved ahead and covered. Fresh review has no open findings (`APPROVED`).
- Human acceptance: standing acceptance granted for the approved full plan.
- Commit/merge/push: authorized and pending.
