# Current Issue Contract

# Issue DOWNLOAD-PRUNE

Status: `completed`

## Identity

- Local Issue: `DOWNLOAD-PRUNE`
- Title: `Safely prune files removed from remote repositories`
- Type: `cli`, `feature`, `data-safety`
- Priority: `P1`
- Branch: `codex/add-download-prune` (local only)
- Base: `yuto`
- Previous Issue: `DOWNLOAD-RESUME`, delivered by `2f5a7ee` and merged by
  `108e5c0`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

Repository downloads intentionally skip existing files and never remove local
content. A blind `--force` cleanup would risk deleting user-owned files that
were never downloaded by the CLI.

Add opt-in `--prune` to whole-repository downloads. Track only files actually
downloaded by the CLI in a private external manifest, then remove only tracked
regular files that are absent from a successfully validated remote file list.
Default download and single-file behavior remain unchanged.

## Scope And Acceptance

- Store a versioned, credential-free manifest outside the destination tree,
  keyed by endpoint, repository, type, and resolved destination path.
- Use restrictive directory/file permissions and atomic manifest replacement.
- Never adopt pre-existing skipped files as managed files.
- Prune only after every download succeeds and only from the prior manifest;
  never scan the destination tree or delete directories, symlinks, or
  untracked files.
- Handle empty repositories, missing/malformed manifests, missing managed
  files, download failure, and path/symlink replacement safely.
- Add CLI/API and compatibility regressions, update documentation, and run the
  complete offline verification and independent review.

## Permissions

- Standing local development, commit, merge, and `yuto` push permissions apply.
- Live read-only tests may use only `weixin_52273949/test_model` and
  `weixin_52273949/test_datasets`. No remote writes or deletion are authorized.
- Human acceptance is standing-approved for the ordered plan.

## Evidence And Closure

- Implementation: whole-repository downloads maintain an external versioned
  manifest keyed by endpoint, normalized repository ID, effective type, and
  resolved destination. Only files actually written by successful downloads
  are managed; skipped pre-existing files are never adopted. `--prune` runs
  only after all transfers succeed and removes only prior-manifest regular
  files absent from the complete remote list.
- Data safety: manifest directories/files use `0700`/`0600`, opaque keys contain
  no token or URL, writes are atomic, malformed or unavailable state fails
  closed for explicit prune, and descriptor-relative deletion refuses leaf or
  parent symlinks and directories. Missing paths are already clean; untracked
  files are never scanned. Ordinary downloads preserve their existing success
  behavior when manifest state is unavailable and emit a safe warning.
- Focused regression: `tests/test_download_prune.py` passed 49/49 checks for
  initial tracking, prune transitions, empty repositories, first-run adoption,
  restrictive permissions, download/write failures, missing parents, malformed
  state, symlink/directory replacement, CLI forwarding, and default/single-file
  compatibility. Existing download contract, path, checksum, resume, and skip
  regressions also passed.
- Complete offline suite: `python -m pytest -ra` collected and passed 51/51
  isolated scripts. `python -m compileall -q .` and `git diff --check` passed.
- Live evidence: not run. Proving remote removal requires a remote mutation or
  deletion, which is outside the standing authorization for the two fixed test
  repositories. No remote state was changed.
- Independent review: the first pass found a P1 default-compatibility issue
  because manifest errors could fail ordinary downloads. It was fixed with
  best-effort default tracking and strict explicit-prune behavior, with focused
  regressions and documentation. The second pass found no open P0/P1/P2/P3
  finding and confirmed manifest scoping, permission and path safety, atomic
  state, failure ordering, CLI compatibility, and credential isolation.
  Residual live-service risk is limited to server-side list completeness, which
  cannot be exercised without an authorized remote content change. Verdict:
  `APPROVED`.
- DoD: implementation, documentation, focused and complete tests, compileall,
  diff check, independent review, credential scan, scope audit, and standing
  human acceptance agree; no secret, artifact, unrelated edit, remote mutation,
  or open finding is present.
- Commit/merge/push: authorized; references will be reported after delivery.
