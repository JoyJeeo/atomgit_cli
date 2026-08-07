# Current Issue Contract

# Issue DOWNLOAD-RESUME

Status: `completed`

## Identity

- Local Issue: `DOWNLOAD-RESUME`
- Title: `Resume interrupted CLI downloads`
- Type: `cli`, `feature`, `data-integrity`
- Priority: `P1`
- Branch: `codex/add-download-resume` (local only)
- Base: `yuto`
- Previous Issue: `DOWNLOAD-CHECKSUM-VERIFICATION`, delivered by `8ec7300`
  and merged by `a616797`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

CLI downloads retry interrupted transfers once but delete temporary data and
restart from byte zero on the next command. Authorized read-only probes confirm
that both test repositories honor Range with HTTP 206 and an exact
Content-Range.

Add opt-in `--resume` to repository and single-file CLI downloads. Incomplete
bytes persist in a restrictive AtomGit cache without credentials or signed
URLs. A later invocation requests only the remaining range, verifies size and
the repository checksum, copies to a unique destination temporary, and then
atomically replaces the target. Default existing-file skip behavior remains
unchanged.

## Scope And Acceptance

- Bind to locked HF `http_get` resume semantics for standard URLs; support raw
  UTF-8 fallback with strict Range/Content-Range validation.
- Keep cached partials private, collision-resistant, credential-free, and
  isolated by endpoint/repository/type/file/checksum.
- Strip credentials for cross-origin download locations and never persist or
  print signed URLs.
- Preserve partial data after retryable interruption, remove corrupt/stale
  partials, checksum before replacement, and preserve existing destinations on
  every failure.
- Add CLI/API, interruption/restart, checksum, redirect, cleanup, default
  compatibility, and raw fallback regressions; update documentation.
- Run focused and full offline tests, compileall, diff checks, authorized
  read-only live interruption/resume evidence, and independent review.

## Permissions

- Standing local development, commit, merge, and `yuto` push permissions apply.
- Live read-only tests may use only `weixin_52273949/test_model` and
  `weixin_52273949/test_datasets`. No remote writes or deletion are authorized.
- Human acceptance is standing-approved for the ordered plan.

## Evidence And Closure

- Implementation: both CLI download commands accept `--resume`; standard
  transfers use locked `http_get` with a safe resolve URL, raw UTF-8 transfers
  enforce exact Range/Content-Range, and all completed content is checksum
  verified before and after copying to the atomic destination temporary.
  Cache/partial/lock permissions are restrictive; keys contain hashes rather
  than credentials, signed URLs, or plaintext repository names.
- Focused regression: `tests/test_download_resume_cli.py` passed 17/17 checks
  for interruption persistence, exact offset reuse, permissions, signed-URL
  exclusion, cross-origin auth stripping, raw range validation, checksum/atomic
  replacement, corrupt-partial restart, stale-checksum cleanup, and both CLI
  paths. All download-focused scripts and locked HF contract tests passed.
- Complete offline suite: `python -m pytest -ra` collected and passed 50/50
  isolated scripts. `python -m compileall -q .` and `git diff --check` passed.
- Live read-only evidence: an authorized dataset LFS partial of 1,048,576 bytes
  resumed from exactly that offset to 12,582,912 bytes; final checksum returned
  true and partial/lock cache was empty. No remote state changed.
- Independent review: the first pass requested explicit corrupt/stale partial
  regressions and accurate from-zero wording. Both were fixed. The final pass
  found no open P0/P1/P2/P3 finding and confirmed locked signature compatibility,
  exact range validation, credential/signed-URL isolation, private cache state,
  atomic replacement, cleanup, CLI compatibility, and documentation. Residual
  non-blocking risk: an intentionally abandoned download retains its partial
  until the same file is resumed or the AtomGit cache is cleared. Verdict:
  `APPROVED`.
- DoD: implementation, focused and complete tests, compileall, diff check,
  documentation, live evidence, independent review, credential safety, and
  final scope audit agree; no secret, artifact, unrelated edit, remote mutation,
  or open finding is present.
- Commit/merge/push: authorized; references will be reported after delivery.
