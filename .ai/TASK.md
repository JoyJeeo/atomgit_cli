# Current Issue Contract

# Issue CONFIG-LIFECYCLE

Status: `completed`

## Identity

- Local Issue: `CONFIG-LIFECYCLE`
- Title: `Import-time config writes and non-atomic saves can break help or credentials`
- Type: `bug`, `security`, `cli`
- Priority: `P1`
- Branch: `codex/harden-config-lifecycle` (local only)
- Base: `yuto`

## Previous Issue (Closed)

- `LOGIN-TOKEN-INPUT` was delivered by `0b78274` and merged by `d65ba00`.

## Evidence And Scope

The global Config constructor creates/chmods `~/.atomgit` during import and the
runtime policy creates `~/.cache/atomgit`, so read-only commands such as
`--help` can fail under an invalid or read-only HOME. Saving truncates
`config.json` in place, so interruption or write failure can destroy the last
valid credential state.

In scope: defer configuration I/O until access, make runtime environment setup
path-only, keep read-only absent config access side-effect free, migrate
existing credential permissions when loaded, write via a 0600 same-directory
temporary file and atomic replacement, clean failed temporaries, and keep
in-memory state consistent on failure.

Out of scope: changing JSON schema, token migration/encryption, Git-helper state,
and cross-process locking.

## Acceptance Criteria

- Import and `--help` perform no config filesystem mutation and tolerate an
  unusable HOME path.
- Reading an absent config does not create `~/.atomgit`.
- Existing config permission migration remains 0700/0600 when credentials load.
- Failed replacement preserves old disk and in-memory state and leaves no temp.
- Successful saves are atomic and retain 0600 permissions.
- Focused/full tests and required checks pass.

## Permissions And Delivery

- Authorized: local edits/commits, local merge into `yuto`, and push only
  `yuto`; task branches remain local-only.
- Tests use isolated HOME directories; no live credentials are read or changed.
- Human acceptance: standing acceptance granted for the approved full plan.
- Implementation: Config now resolves paths at construction but loads only on
  first access; absent reads and imports create nothing. Runtime policy sets
  `HF_HOME` without creating it. Saves use a private same-directory temporary,
  flush/fsync, atomic replace, failure cleanup, and persist-before-memory commit.
  Non-object/corrupt JSON safely becomes logged-out state and is repairable.
- Regression evidence: before implementation, import/constructor/absent-read/
  no-mutation assertions failed, existing permissions mutated at construction,
  and `--help` failed when HOME was unusable.
- Focused tests: config lifecycle 15/15 assertions and 5/5 related pytest cases
  passed.
- Complete offline suite: 42/42 passed in 37.98 seconds.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Independent review: no open findings (`APPROVED`). Cross-process write locking
  and encrypted token storage remain explicitly out of scope.
- Human acceptance: standing acceptance granted for the approved full plan.
- Commit/merge/push: authorized and pending.
