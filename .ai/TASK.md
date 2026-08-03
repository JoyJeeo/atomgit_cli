# Current Issue Contract

Status: `active`

## Issue Identity

- ID: GitHub Issue #7
- Title: Recover downloads after incomplete HTTP response bodies
- Type: `bug`, `security`, `compatibility`
- Priority: `P1`
- Human owner: repository maintainer
- AI phase: `delivery`

## Evidence And Expected Behavior

A 404,468,341-byte LFS download ended after 242,498,596 bytes with
`RemoteProtocolError`. Repeating the same HF call reused local partial state and
completed with the expected SHA-256. Current CLI/SDK return immediately and may
print the full signed LFS URL from the exception.

## Scope And Acceptance

- Retry one time for incomplete response bodies, connection interruptions, and
  read timeouts in repository and file download paths.
- Do not retry authentication, permission, repository, revision, or input
  errors.
- Never include raw remote URLs or signed query parameters in user errors.
- Preserve force/incremental semantics and public SDK signatures.
- Add deterministic CLI/SDK tests and run all offline checks.
- Use the prior successful 404 MB manual retry as live evidence; do not upload
  another large file unless regression evidence requires it.

## Permissions

- Authorized repository reads and dedicated token are allowed.
- Local source/test documentation edits and GitHub Issue updates are allowed.
- The maintainer authorized committing the current worktree changes and pushing
  them to `github/yuto` on 2026-08-03.
- PR, merge, Issue closure, release, and publication are not authorized.

## Implementation And Review Record

- Design: `run_download_with_retry` retries an interrupted HF download once so
  the locked client can reuse partial cache state. Shared classification keeps
  authentication and deterministic lookup failures out of the retry path, and
  all CLI/SDK download failures are converted to stable messages without raw
  URLs. SDK wrappers suppress the original exception traceback.
- Issue-owned files changed: `utils.py`, `api.py`, `atomgit_hub.py`,
  `tests/test_download_recovery.py`, and the download section of
  `docs/architecture.md`.
- Focused offline test: `python tests/test_download_recovery.py` passed 12/12
  in the `atomgit_cli` conda environment.
- Complete offline suite: all 12 `tests/test_*.py` scripts passed in the
  `atomgit_cli` conda environment.
- Static checks: `python -m compileall -q .`, `git diff --check`, and the
  environment-token diff scan passed.
- Dependency contract: download calls match the installed
  `huggingface-hub==1.1.7` `snapshot_download` and `hf_hub_download`
  signatures.
- Live evidence: the earlier 404,468,341-byte interrupted LFS transfer
  completed when repeated against the same partial state and matched the
  expected SHA-256. No additional live upload or forced interruption was run.
- Independent review: no blocking findings; verdict `APPROVED`.
- Residual risk: deterministic offline interruption fakes cover the wrapper,
  while automatic retry under a newly induced live interruption was not
  repeated to avoid another large transfer.
- Human acceptance: accepted through the explicit commit-and-push request on
  2026-08-03.
