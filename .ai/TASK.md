# Current Issue Contract

# Issue REPO-ID-CANONICALIZATION

Status: `completed`

## Identity

- Local Issue: `REPO-ID-CANONICALIZATION`
- Title: `Repository ID validation and normalization disagree on encoded or unsafe paths`
- Type: `security`, `bug`, `cli`, `sdk`
- Priority: `P1`
- Branch: `codex/canonicalize-repo-ids` (local only)
- Base: `yuto`

## Previous Issue (Closed)

- `CONFIG-LIFECYCLE` was delivered by `660ef93` and merged by `19e9547`.

## Evidence And Scope

CLI validation URL-decodes IDs but normalization forwards the original text, so
`owner%2Frepo` validates as two segments yet is sent as one encoded segment.
Dot segments, control characters, backslashes, and ambiguous percent encodings
also lack one shared boundary for direct API/SDK calls.

In scope: make validation and normalization use one strict ASCII repository-ID
parser, reject encoded/empty/dot/control/backslash/invalid segments, require at
least owner/repository, preserve the established multi-level mapping, and cover
CLI/API/SDK helpers.

Out of scope: changing AtomGit's multi-level mapping, filenames/revisions, and
remote repository naming policy beyond the existing allowed character set.

## Acceptance Criteria

- Safe two-level and multi-level IDs retain current normalized results.
- Encoded separators/dot segments and any percent ambiguity are rejected.
- Empty, dot, control, backslash, invalid-character, and single-segment IDs are
  rejected consistently.
- CLI validation returns false; API/SDK normalization raises a safe ValueError
  before remote calls.
- Focused/full tests and required checks pass.

## Permissions And Delivery

- Authorized: local edits/commits, local merge into `yuto`, and push only
  `yuto`; task branches remain local-only.
- No remote test is required because all invalid cases must stop before I/O.
- Human acceptance: standing acceptance granted for the approved full plan.
- Implementation: validation and normalization now share a literal ASCII parser
  with one safe error. It requires owner/repository, rejects percent ambiguity,
  unsafe path forms and invalid characters, and preserves established safe
  two-level/multi-level mapping.
- Regression evidence: before implementation, only 29/44 original extended
  assertions passed; normalization accepted every unsafe input and validation
  accepted encoded separators/dot segments.
- Focused tests: repository-ID regression passed 66/66 assertions after adding
  explicit API and SDK boundary checks; 6/6 related pytest cases passed.
- Complete offline suite: 42/42 passed in 35.06 seconds before the final
  assertion-only boundary expansion; the focused regression was rerun after it.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Independent review: no open findings (`APPROVED`). The historical multi-level
  physical-name mapping is intentionally unchanged.
- Human acceptance: standing acceptance granted for the approved full plan.
- Commit/merge/push: authorized and pending.
