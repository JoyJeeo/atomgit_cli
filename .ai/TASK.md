# Current Issue Contract

# Issue CONFIG-SHOW-GIT-STATUS

Status: `completed`

## Identity

- Local Issue: `CONFIG-SHOW-GIT-STATUS`
- Title: `config-show reports full Git integration when only one host is configured`
- Type: `bug`, `cli`
- Priority: `P2`
- Branch: `codex/fix-config-show-helper-status` (local only)
- Base: `yuto`

## Previous Issue (Closed)

- `CREATE-EXIST-OK` was delivered by `3dc1fb0` and merged by `028a832`.

## Evidence And Scope

`config-show` queries two AtomGit credential-helper keys but reports enabled when
either host contains the managed helper. It also uses `git config --get`, while
login installs a multi-value reset/helper chain.

In scope: inspect all helper values for both supported hosts, report full,
partial (including configured/missing hosts), missing, and inspection failure,
without displaying helper command values or tokens.

Out of scope: repairing configuration, changing login/logout helper state, and
checking unrelated Git hosts.

## Acceptance Criteria

- Full status requires both AtomGit hosts to contain the managed helper.
- Partial status names configured and missing supported hosts.
- Missing and command-failure states remain distinct.
- No helper command or token value is printed.
- Focused/full tests and required checks pass.

## Permissions And Delivery

- Authorized: local edits/commits, local merge into `yuto`, and push only
  `yuto`; task branches remain local-only.
- Tests isolate and mock Git configuration; user Git state is not modified.
- Human acceptance: standing acceptance granted for the approved full plan.
- Implementation: config-show now reads all global helper values through the
  shared Git utility for both supported hosts. It reports dynamic full counts,
  partial configured/missing host lists, missing, or inspection failure without
  printing values. README documents the status meanings.
- Regression evidence: the extended CLI regression initially passed 45/48;
  full-format and both partial-state assertions failed because either host was
  treated as full integration.
- Focused tests: CLI surface passed 48/48 assertions and 3/3 related pytest
  cases passed.
- Complete offline suite: 42/42 passed in 35.26 seconds.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Independent review: no open findings (`APPROVED`). Tests mock all Git reads;
  no user helper configuration was modified.
- Human acceptance: standing acceptance granted for the approved full plan.
- Commit/merge/push: authorized and pending.
