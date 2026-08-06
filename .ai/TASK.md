# Current Issue Contract

# Issue DOWNLOAD-STANDARD-PART-CLEANUP

Status: `completed`

## Identity

- Local Issue: `DOWNLOAD-STANDARD-PART-CLEANUP`
- Title: `Failed standard URL downloads leave partial files behind`
- Type: `bug`, `security`
- Priority: `P2`
- Branch: `codex/cleanup-download-parts` (local only)
- Base: `yuto`
- Delivery mode: local acceptance, authorized commit, local merge into `yuto`,
  and push only `yuto`; task branch remains local-only.

## Previous Issue (Closed)

- `GIT-HELPER-CACHED-IDENTITY` was delivered by `5505766` and merged by
  `ca3d7cc`.

## User Impact And Evidence

The standard percent-encoded download path writes `<destination>.part` and only
renames it on success, but it has no failure cleanup. Interrupted reads or
exhausted retries can leave partial repository content on disk. Both standard
and raw UTF-8 paths use the fixed name, which also collides with a legitimate
repository file at that path.

## Scope

In scope: use a unique same-directory temporary file for each standard and raw
UTF-8 attempt, clean it on every failure (including exhausted retry and pre-open
failure), preserve existing destination and neighboring repository files until
a complete successful replace, add offline regressions, and align architecture
documentation.

Out of scope: resume support, checksum verification, raw transport framing,
destination path policy, and changing the default existing-file skip behavior.

## Acceptance Criteria

- A mid-stream standard response failure leaves no temporary file from the
  failed attempt.
- Retry remains bounded and each attempt starts clean.
- A failure before response open creates no temporary file.
- An existing destination is preserved on failure.
- A legitimate `<destination>.part` repository file is preserved on failure and
  success across both transports.
- Successful standard downloads still atomically replace the destination.
- Focused/full offline tests, compileall, and `git diff --check` pass.

## Permissions And Acceptance

- Authorized: local edits, tests, commits, local merge into `yuto`, and push
  only `yuto`; no task-branch push.
- Tests are offline with fake responses; no real token/config or remote service
  is used.
- Human acceptance: standing acceptance granted for the approved full plan.
- Implementation: standard and raw UTF-8 resolve transports now create a unique
  0600 temporary file in the destination directory, close it before atomic
  replacement, and remove it in every unsuccessful path. Fixed-name
  `<destination>.part` files are no longer opened, truncated, or deleted.
- Regression evidence: the original standard-path regression passed 6/8
  assertions; interrupted reads left the fixed `.part` behind and pre-open
  failures left an existing fragment untouched. The completed regression passes
  11/11 assertions and additionally protects legitimate neighboring files. Raw
  transport tests cover the same neighboring-file behavior on success and
  truncated responses.
- Focused offline command: `python -m pytest -q
  tests/pytest_offline_scripts.py -k 'download_standard_cleanup or
  download_contract or download_recovery or download_raw_integrity'` passed 4/4
  pytest cases in the `atomgit_cli` environment. The standalone standard-path
  script passed 11/11 assertions.
- Complete offline command: `python -m pytest -q` passed 43/43 pytest cases in
  41.10 seconds with local-loopback permission. An earlier sandboxed focused run
  passed 3/4; its only failure was `PermissionError` while binding 127.0.0.1 in
  the existing raw HTTP transport test, not an assertion failure.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Dependency compatibility: no Hugging Face or datasets call signature changed;
  the locked dependency contract tests passed in the complete suite. The
  `tempfile.NamedTemporaryFile` call uses the Python 3.8-compatible signature.
- Documentation: architecture documentation describes unique same-directory
  temporary files, atomic replacement, cleanup, and fixed-name collision safety.
- Independent review: the first review found the same fixed-name collision in
  the raw UTF-8 fallback (`REQUEST CHANGES`). The raw path and its regressions
  were corrected; a fresh review found no open findings (`APPROVED`).
- DoD/security: tests use fake responses, temporary HOME/directories, and local
  loopback only. No real token/config was read and no remote service was called.
  Residual risk: process termination that bypasses Python cleanup can leave a
  uniquely named hidden temporary file; normal exceptions and retries clean it.
- Commit/merge/push: authorized and pending.
