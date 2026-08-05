# Current Issue Contract

# Issue LOGIN-TOKEN-INPUT

Status: `completed`

## Identity

- Local Issue: `LOGIN-TOKEN-INPUT`
- Title: `Login needs a safer non-interactive token input without removing --token`
- Type: `security`, `cli`, `documentation`
- Priority: `P1`
- Branch: `codex/add-login-token-stdin` (local only)
- Base: `yuto`

## Previous Issue (Closed)

- `CLI-ERROR-REDACTION` was delivered by `e62ebb9` and merged by `5e270c5`.

## Evidence And Scope

`login --token VALUE` is required for compatibility but command-line values can
be retained in shell history or process listings. Interactive login is safe but
there is no explicit pipe/redirection mode for automation.

In scope: retain `--token`, document its exposure tradeoff, add mutually
exclusive `--token-stdin`, reject missing stdin data safely, and verify that
the token is neither echoed nor altered.

Out of scope: removing/deprecating `--token`, environment-variable token input,
credential storage format, and Git helper behavior.

## Acceptance Criteria

- Existing `login --token VALUE` remains supported.
- `login --token-stdin` reads one token from stdin without echoing it.
- Supplying both input modes or empty stdin exits with a usage error and makes
  no login call.
- Help/README recommend interactive or stdin input and warn about shell history.
- Focused/full tests and required checks pass.

## Permissions And Delivery

- Authorized: local edits/commits, local merge into `yuto`, and push only
  `yuto`; task branches remain local-only.
- No live login is required; the existing authenticated session was already
  verified and tests inject a fake login API.
- Human acceptance: standing acceptance granted for the approved full plan.
- Implementation: `--token-stdin` reads exactly one line and strips only line
  terminators; it is mutually exclusive with the retained `--token`. Help and
  README recommend interactive/stdin input and explain command-line exposure.
- Regression evidence: the original CLI rejected `--token-stdin`; 44/46
  extended CLI assertions passed before implementation and both new success/
  forwarding assertions failed.
- Focused tests: CLI regression 46/46 assertions and 3/3 relevant pytest cases
  passed.
- Complete offline suite: 42/42 passed in 39.14 seconds.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Independent review: no open findings (`APPROVED`). The token file/producer is
  caller-managed; the CLI neither echoes nor persists stdin beyond normal login.
- Human acceptance: standing acceptance granted for the approved full plan.
- Commit/merge/push: authorized and pending.
