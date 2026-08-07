# Current Issue Contract

# Issue DOWNLOAD-CHECKSUM-VERIFICATION

Status: `completed`

## Identity

- Local Issue: `DOWNLOAD-CHECKSUM-VERIFICATION`
- Title: `Verify CLI downloads against AtomGit checksums`
- Type: `cli`, `feature`, `data-integrity`
- Priority: `P1`
- Branch: `codex/add-download-checksum` (local only)
- Base: `yuto`
- Previous Issue: `EXPLICIT-BRANCH-UPLOAD`, delivered by `5444646` and
  merged by `f543288`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

CLI repository and single-file downloads currently stream resolve responses to
unique temporary files and atomically replace destinations, but they do not
compare downloaded bytes with repository metadata. Existing files are skipped
by default without verification.

Authorized read-only probes of `weixin_52273949/test_model` and
`weixin_52273949/test_datasets` confirm that locked
`get_hf_file_metadata()` returns a size plus a 40-hex Git blob SHA-1 for regular
Git files and a 64-hex content SHA-256 for LFS files.

Add opt-in `--verify-checksum` behavior to both CLI download commands. Default
skip semantics remain unchanged. When enabled, existing files are verified
without network content transfer; mismatches fail with `--force` guidance.
New or forced downloads are checked in their unique temporary file before the
destination is replaced. Missing, malformed, unsupported, or mismatched
metadata fails closed and never claims verification.

## Scope And Acceptance

- Bind checksum metadata lookup to the real `huggingface-hub==1.1.7` signature
  with explicit AtomGit or anonymous authentication.
- Support content SHA-256 and Git blob SHA-1, including expected-size checks,
  using streamed local hashing.
- Preserve default existing-file skip behavior and all CLI/API compatibility;
  SDK download behavior is out of scope.
- Verify standard and raw UTF-8 fallback downloads before atomic replacement;
  mismatch must preserve an existing destination and clean unique temporaries.
- Add CLI forwarding, existing-file, valid checksum, corrupt download,
  unsupported metadata, and credential-isolation regressions.
- Update authoritative user and architecture documentation.
- Run focused and full offline tests, compileall, diff checks, and independent
  review with no open P0/P1 findings.

## Permissions

- Authorized local development/delivery follows standing rules.
- Read-only live checksum verification may use only
  `weixin_52273949/test_model` and `weixin_52273949/test_datasets` with the
  already supplied login. No remote create, upload, branch, visibility, delete,
  credential-helper mutation, publication, or other remote write is authorized
  by this Issue.
- Human acceptance is standing-approved for the ordered plan.

## Evidence And Closure

- Implementation: `--verify-checksum` is available on repository and
  single-file CLI downloads. Metadata lookup uses explicit `False` for
  anonymous HF authentication, validates only 40/64-hex strong checksums and a
  nonnegative size, streams Git blob SHA-1 or SHA-256 locally, and verifies
  unique temporary files before atomic replacement. Existing default skip
  behavior and SDK behavior are unchanged.
- Regression evidence: `tests/test_download_checksum.py` passed 23/23 custom
  checks covering both algorithms, standard/raw transfers, mismatch retry and
  cleanup, encoded-URL-to-raw fallback enforcement, existing-file validation,
  unsupported metadata, credential isolation, default compatibility, and both
  CLI options and consistent existing-directory guidance. All download-focused
  scripts plus the locked HF contract passed.
- Complete offline suite: `python -m pytest -ra` collected and passed 49/49
  isolated script cases in the `atomgit_cli` environment.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Live tests: read-only `download-file --force --verify-checksum` succeeded on
  authorized model `ignore_test/config.json` (Git blob SHA-1, 77 bytes) and
  dataset `part1.bin` (SHA-256, 12,582,912 bytes); independent local verification
  returned true for both. No remote state was changed.
- Independent review: the first pass requested a raw-fallback enforcement
  regression and corrected retry documentation; the second pass found
  contradictory existing-directory CLI guidance. Both findings were fixed and
  covered by regressions. The final pass found no open P0/P1/P2/P3 finding.
  Residual risk is limited to AtomGit repositories that do not return the
  observed 40/64-hex strong metadata; explicit verification fails closed for
  them rather than silently accepting content. Verdict: `APPROVED`.
- DoD: implementation, regressions, complete offline suite, locked signature,
  documentation, compileall, diff checks, scoped live evidence, credential
  safety, atomic cleanup, and final independent review agree. No token,
  generated artifact, unrelated edit, remote mutation, or open finding is
  present.
- Commit/merge/push: authorized; exact references will be recorded after
  successful delivery.
