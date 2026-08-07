# Current Issue Contract

# Issue DOWNLOAD-MANIFEST-CONCURRENCY

Status: `active`

## Identity

- Local Issue: `DOWNLOAD-MANIFEST-CONCURRENCY`
- Title: `Serialize repository download manifest transactions`
- Type: `bug`, `cli`, `download`, `reliability`
- Priority: `P3`
- Branch: `codex/fix-download-manifest-concurrency` (local only)
- Base: `yuto`
- Previous Issue: `AUTH-STATUS-SEMANTICS`, delivered by `4b071b1`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

Repository downloads load a manifest, transfer files, then atomically replace
the manifest. Atomic replacement prevents partial JSON, but it does not make the
read-modify-write sequence atomic. Two commands targeting the same repository,
type, and local directory can both read the old set and overwrite each other's
managed-file updates; concurrent prune can also act on stale ownership state.

Only one manifest transaction may operate on an identical checkout identity at
a time. A competing command must fail safely with actionable sanitized guidance,
without downloading, pruning, or advancing the manifest.

## Scope And Acceptance

- Add an OS-backed nonblocking advisory lock beside each opaque manifest.
- Hold the lock from immediately before manifest load until download, optional
  prune, and manifest write have completed or failed.
- Use automatic OS lock release on process exit; do not depend on stale PID-file
  deletion. Keep lock files credential-free and private.
- If the manifest cache is unavailable in default non-prune mode, preserve the
  existing best-effort download behavior and warning.
- If a valid manifest identity is busy, fail both normal and prune downloads
  before reading ownership state or transferring files.
- Preserve manifest validation, atomic write, prune boundaries, default skip,
  CLI arguments, remote calls, and existing exit behavior.
- Add focused regressions for exclusive acquisition, release after success and
  exceptions, busy download behavior, state preservation, and permissions.
- Do not add commands, flags, waiting/retry policy, download functionality, or
  unrelated changes.

## Compatibility And Risks

- Concurrent commands for the same checkout now fail fast and can be retried;
  different repositories, types, or local directories retain independent locks.
- Advisory locking must support POSIX and Windows using Python standard-library
  primitives, while the current environment provides real execution only on
  POSIX. Windows behavior requires strict mocked contract evidence.
- Persistent small lock files are safe private state; the OS releases ownership
  automatically after normal exit, exceptions, or process termination.

## Permissions

- The user authorized fixing already audited defects one Issue at a time and
  explicitly excluded new functionality.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- No live request, repository access, remote write, credential mutation, or
  destructive external action is authorized or required for this Issue.

## Required Evidence And Closure

- [x] Unserialized lost-update behavior is reproduced by a failing regression.
- [x] One checkout identity permits only one active manifest transaction.
- [x] Busy commands fail before transfer/prune and preserve manifest state.
- [x] Lock release, permissions, identity isolation, and Windows contract pass.
- [x] Existing manifest/prune/download behavior remains compatible.
- [x] Focused and complete offline tests, compileall, pip, and diff checks pass.
- [x] Documentation, credential scan, scope audit, and independent review pass.
- [x] Human acceptance is covered by the standing ordered-fix authorization.
- [ ] The task is committed, merged into `yuto`, and only `yuto` is pushed.

## Verification Evidence

- Regression before implementation: the concurrent-download contract passed
  `2/5`. Both commands transferred and returned success after reading the same
  empty manifest, while the delayed last writer replaced the other command's
  managed-file record.
- Implementation: each opaque manifest has a private `.lock` sibling. POSIX
  uses nonblocking `flock`; Windows uses one-byte nonblocking `msvcrt.locking`.
  An `ExitStack` holds ownership from before manifest load through transfer,
  optional prune, atomic manifest replacement, and every failure path.
- Busy behavior: a competing normal or prune command returns false with
  sanitized retry guidance before file transfer or deletion. The existing
  manifest remains byte-for-byte unchanged, and the winning transaction alone
  advances it. Sequential reuse merges ownership after lock release.
- Lock safety: exception release, independent manifest identities, opaque names,
  `0600` permissions, persistent-file reuse, and Windows busy/unlock calls are
  covered. OS advisory ownership requires no stale PID-file cleanup.
- Focused results: concurrency `9/9`, manifest/prune `49/49`, and Windows
  compatibility `12/12` passed offline.
- Complete offline suite: `pytest -q` exited `0` with all `55` collected tests;
  `python -m compileall -q .`, `python -m pip check`, and `git diff --check`
  passed in the `atomgit_cli` environment.
- Security and scope: no live request, repository access, remote or destructive
  write, command, flag, retry/wait policy, credential, dependency, generated
  artifact, or new feature is present.
- Independent review: `APPROVED` with no open P0-P3 findings. Lock release uses
  standard context management and descriptor close as the final backstop.
  Residual platform risk is that the Windows backend has strict mocked contract
  evidence but no real Windows execution in the current environment.
