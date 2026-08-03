# Current Issue Contract

Status: `completed`

## Identity

- GitHub Issue: `#13`
- Title: `[P1] AtomGit credential helper does not isolate inherited Git helpers`
- Type: `security`, `bug`
- Priority: `P1`
- Branch: `codex/issue-13-credential-helper-isolation`
- Base: `yuto` at `22db026311be589cf5481daa9ccbe51d4a9328f1`
- Delivery mode: authorized self-accepted branch delivery

## User Impact And Evidence

After `atomgit login`, Git combines the AtomGit host-specific helper with an
inherited generic helper. A live private `git ls-remote` invoked the macOS
`osxkeychain` store path and emitted `failed to store: -60006`. A normal user
environment could therefore copy the AtomGit token into an unrelated helper.

The current logout implementation also unsets the complete host-specific key,
so it cannot preserve values that existed before AtomGit login.

## Current And Expected Behavior

- Current: setup writes one host-specific helper value for each AtomGit host;
  inherited generic helpers remain active.
- Current: logout deletes the host-specific helper key rather than restoring
  the user's prior values.
- Expected: AtomGit hosts use an exclusive helper chain owned by AtomGit while
  logged in, unrelated hosts remain unchanged, and logout restores the exact
  prior user-global values.
- Expected: a partial setup failure rolls back both AtomGit host keys.

## Scope

In scope:

- `utils.py` Git credential-helper setup and cleanup behavior;
- `cli.py` logout failure propagation and retry of residual helper state;
- restrictive persistence of the prior host-specific helper state without
  writing the current login token;
- rollback for partial setup failure;
- isolated offline tests using temporary HOME and Git config files;
- affected Git-integration documentation.

Out of scope:

- Issue #8 username lookup authentication and fallback behavior;
- token/config storage policy outside helper-chain state;
- upload, download, repository, SDK, dependency, version, or release changes;
- changes to the user's real Git configuration or keychain.

## Compatibility

- Preserve the `setup_git_credentials(token) -> bool` and
  `clear_git_credentials() -> bool` interfaces.
- Support Python 3.8+ and the installed Git configuration semantics.
- Preserve unrelated Git configuration and all pre-existing multi-valued
  AtomGit host helper entries in order.
- Never persist or print the token in helper-state metadata or test fixtures.

## Acceptance Criteria

- An inherited generic helper is not invoked for AtomGit lookup, store, or
  erase after setup.
- The inherited helper remains active for an unrelated host.
- Setup installs an empty reset entry followed by the AtomGit-owned helper for
  both `atomgit.com` and `hub.atomgit.com`.
- Logout restores exact pre-existing user-global helper values for both hosts.
- A partial two-host setup failure restores the pre-operation state.
- Repeated login does not replace the original backup with AtomGit-owned state.
- Helper state is stored with restrictive permissions and contains no token.
- Logout returns nonzero on helper restoration failure and can retry residual
  state after the login token has already been cleared.
- Existing offline tests, `python -m compileall -q .`, and `git diff --check`
  pass in the `atomgit_cli` conda environment.

## Required Tests

- Focused offline credential-helper integration script with isolated `HOME`
  and `GIT_CONFIG_GLOBAL`, with the real system config explicitly disabled.
- Existing 12 offline test scripts.
- No live AtomGit request is required for implementation acceptance; the
  previously authorized private-repository evidence remains the live baseline.

## Permissions

- Authorized: local source, test, documentation, and `TASK.md` edits; isolated
  temporary Git configuration; local task branch creation; cohesive commit and
  push of this task branch after self-verification; pull request creation,
  merge into `yuto`, and closure of Issue #13 after successful delivery.
- Not authorized: real global Git/keychain mutation, AtomGit remote writes, tag,
  release, or PyPI.

## Delivery Record

- Regression evidence: `python tests/test_git_credentials_isolation.py`
  failed on the previous implementation because setup could not replace
  existing multi-valued helpers and installed neither a reset nor backup.
- Implementation: setup now stores the original two-host values in a `0600`
  state file without writing the current login token, installs an empty reset
  plus the owned helper,
  preserves the original backup on repeated login, and rolls back partial
  configuration failures. Cleanup transactionally restores the original
  values and includes a legacy owned-helper cleanup path.
- Documentation: README, FAQ, human architecture/testing guidance, and the AI
  architecture specification describe helper isolation and restoration.
- Focused offline test: `python tests/test_git_credentials_isolation.py` passed
  33/33 assertions using temporary HOME/global config and a fake inherited
  helper. The real system config is explicitly disabled. Coverage includes
  repeated setup, lookup/store/erase isolation, exact restoration, partial
  setup failure, failed rollback recovery, cleanup-file failure recovery, and
  CLI logout failure/retry behavior.
- Full offline tests: all 13 `tests/test_*.py` scripts passed with zero
  failures in the `atomgit_cli` conda environment after review fixes.
- Static checks: `python -m compileall -q .` and `git diff --check` passed.
- Credential scan: no real token pattern or `ATOMGIT_TEST_TOKEN` reference was
  found in changed implementation, test, or documentation files.
- Live test: the pre-fix evidence was followed by an authorized post-fix
  private `git ls-remote`. Login,
  private remote read, and logout exited 0; the inherited generic helper
  remained configured but produced no keychain/store diagnostic, and owned
  helper/state files were removed.
- DoD audit: implementation, focused regression, documentation, complete
  offline suite, compileall, diff check, credential scan, and scope checks
  passed. Human acceptance remains pending.
- Independent review: initial verdict `REQUEST CHANGES`. It found that setup
  could discard recovery files after a failed rollback and that cleanup could
  restore managed config after deleting the helper. Both findings were fixed
  with persistent-failure tests. Re-review then found a Unix-only `os.fchmod`
  call in the atomic writer; it was removed while retaining private `mkstemp`
  creation and post-replace `chmod`. The final review checked the complete
  diff, failure paths, test isolation, documentation, live evidence, and
  credential scan; no blocking findings remained. Verdict: `APPROVED`.
- Delivery: commit `581545d` was pushed on the task branch; PR #14 was merged
  into `yuto` as merge commit `429f16a9a45b33b873c019ffcaaf26756ddfac04`.
  Issue #13 was closed after merge. No tag or Release was created.
- Human acceptance: maintainer waived manual acceptance and authorized
  self-accepted commit/push, PR merge, and Issue closure after the recorded
  tests and review.
