# Current Issue Contract

# Issue CLI-ERROR-REDACTION

Status: `completed`

## Identity

- Local Issue: `CLI-ERROR-REDACTION`
- Title: `Create and upload failures can expose remote credentials or signed URLs`
- Type: `security`, `bug`, `cli`
- Priority: `P0`
- Branch: `codex/redact-cli-errors` (local only)
- Base: `yuto`

## Previous Issue (Closed)

- `DOWNLOAD-EXISTING-FILES` was delivered by `b5e5538` and merged by `b1d23ae`.

## Evidence And Scope

Create and upload exception handlers interpolate raw dependency exceptions into
terminal output. Those exceptions may include Authorization values, access
tokens, signed URLs, or query credentials. Unknown-error hints also repeat the
raw message. Login/whoami must remain safe if credential storage/loading fails.

In scope: remove raw exception text from create/upload output, ensure unknown
classification hints are generic, safely contain login/whoami exceptions, add
regressions with credential-shaped sentinels, and retain actionable categories.

Out of scope: changing operation semantics, download/SDK redaction already
covered elsewhere, and Git-helper diagnostics.

## Acceptance Criteria

- Create, file upload, and directory upload never echo raw exception details.
- Unknown error hints contain an actionable generic message, not the cause.
- Login and whoami contain unexpected config/API exceptions without traceback
  or credential-shaped output.
- Existing categorized guidance and exit behavior remain intact.
- Focused/full tests and required checks pass.

## Permissions And Delivery

- Authorized: local edits/commits, local merge into `yuto`, and push only
  `yuto`; task branches remain local-only.
- Remote validation is not required; the security boundary is verified using
  deterministic injected exceptions and no live failure is induced.
- Human acceptance: standing acceptance granted for the approved full plan.
- Implementation: create/file-upload/directory-upload now emit only fixed error
  categories and actionable hints; unknown hints are generic. Login credential
  save failures and whoami credential read failures are contained with safe
  messages. README documents that raw dependency details are intentionally
  hidden.
- Regression evidence: before the fix, 13/20 security assertions passed; all
  three remote-operation outputs exposed the sentinel and login/whoami allowed
  injected credential errors to escape.
- Focused tests: 8/8 relevant pytest cases passed; the dedicated redaction
  script passed 20/20 assertions.
- Complete offline suite: 42/42 passed in 40.04 seconds.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Independent review: no open findings (`APPROVED`). Tests cover credential
  shaped exceptions without contacting a live service; live destructive error
  injection was intentionally not performed.
- Human acceptance: standing acceptance granted for the approved full plan.
- Commit/merge/push: authorized and pending.
