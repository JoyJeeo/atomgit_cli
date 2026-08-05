# Current Issue Contract

# Issue DOWNLOAD-REPO-TYPE

Status: `completed`

## Identity

- Local Issue: `DOWNLOAD-REPO-TYPE`
- Title: `Download type probing can misclassify empty repositories or mix model and dataset routes`
- Type: `bug`, `cli`, `compatibility`
- Priority: `P1`
- Branch: `codex/fix-download-repo-type` (local only)
- Base: `yuto`

## Previous Issue (Closed)

- `DOWNLOAD-RAW-INTEGRITY` was delivered by `2a7d245` and merged by `09371a8`.

## Evidence And Scope

The automatic list helper discards a successful empty model result and raises a
later dataset 404. Per-file resolve also falls back to the other repository
type, which can return unrelated same-named content. The CLI exposes no way to
select the intended type.

In scope: add optional `download --repo-type`, preserve successful empty list
results, define deterministic error precedence, reject genuinely ambiguous
different model/dataset listings, bind resolve downloads to the selected type,
and update tests/documentation.

Out of scope: existing-file skip behavior, SDK download semantics, and writes.

## Acceptance Criteria

- Explicit type is forwarded and only that type is used.
- Auto mode returns a successful empty repository when the other route fails.
- Authentication errors are not hidden by a later 404.
- Identical compatibility-route listings remain usable; different non-empty
  listings require explicit type selection.
- Resolve never switches repository type after listing.
- Focused/full tests and required checks pass; both authorized repositories
  retain read-only download compatibility.

## Permissions And Delivery

- Authorized: local edits/commits, local merge into `yuto`, push only `yuto`,
  and read-only tests against the two maintainer-provided repositories.
- Human acceptance: standing acceptance granted for the approved full plan.
- Implementation: `download --repo-type model|dataset` is forwarded end to end;
  explicit selection uses only that list/resolve route. Auto mode probes both,
  preserves successful empty results, prioritizes authentication/non-404
  failures, accepts identical compatibility listings, and rejects different
  non-empty listings with actionable guidance.
- Regression evidence: before implementation, 1/6 original repository-type
  assertions passed. The final regression covers empty success, error
  precedence, identical/different listings, explicit selection, sanitized
  guidance, and resolve route isolation.
- Focused offline tests: 4/4 pytest cases passed.
- Complete offline suite: 40/40 passed in 38.63 seconds.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Authorized read-only live checks: explicit model download from
  `weixin_52273949/test_model` and explicit dataset download from
  `weixin_52273949/test_datasets` both succeeded.
- Independent review: implementation, tests, documentation, compatibility,
  and credential exposure reviewed; no open findings (`APPROVED`).
- Human acceptance: standing acceptance granted for the approved full plan.
- Commit/merge/push: authorized and pending.
