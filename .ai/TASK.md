# Current Issue Contract

# Issue GIT-HELPER-CACHED-IDENTITY

Status: `completed`

## Identity

- Local Issue: `GIT-HELPER-CACHED-IDENTITY`
- Title: `Git credential lookup depends on a live username API request`
- Type: `security`, `bug`, `cli`
- Priority: `P1`
- Branch: `codex/cache-git-helper-identity` (local only)
- Base: `yuto`
- Delivery mode: local acceptance, authorized commit, local merge into `yuto`,
  and push only `yuto`; task branch remains local-only.

## Previous Issue (Closed)

- `CONFIG-SHOW-GIT-STATUS` was delivered by `6537fba` and merged by `563a3fc`.

## User Impact And Evidence

The generated Git credential helper calls `https://atomgit.com/api/v5/user`
for every Git credential `get`. A transient network/API failure therefore
prevents Git from using an otherwise valid locally stored token and repeatedly
sends the token to the identity endpoint.

Current path: `login -> api.login -> Config.set_credentials ->
setup_git_credentials -> generated helper -> live identity API on every get`.

Expected path: the already verified login name is persisted as non-sensitive
configuration and the helper returns cached username plus token without network
I/O.

## Scope

In scope: persist the verified login name with the token, generate an offline
helper that uses only local configuration, keep `get_credentials()` token-only,
clear cached username on logout, add isolated regressions, and update user/
architecture documentation.

Out of scope: token encryption, changing Git helper registration/rollback,
supporting arbitrary hosts, and automatic migration without re-login.

## Acceptance Criteria

- Successful login atomically stores token and verified username.
- Generated helper performs no HTTP/network import or request.
- Supported-host `get` returns cached username/token; missing username returns
  no credentials without exposing token.
- Unrelated hosts and store/erase behavior remain unchanged.
- `get_credentials()` continues returning only the token compatibility shape.
- Existing installations migrate by re-running `atomgit login`, documented.
- Focused/full offline tests, compileall, and `git diff --check` pass.

## Permissions And Acceptance

- Authorized: local edits, tests, commits, local merge into `yuto`, and push
  only `yuto`; no task-branch push.
- Git tests must use isolated HOME/global config and must not mutate real user
  Git configuration.
- No live AtomGit test is required; no real token or config content may be read.
- Human acceptance: standing acceptance granted for the approved full plan.
- Implementation: `Config.set_credentials(token, username=...)` atomically
  persists the verified non-sensitive login while preserving the token-only
  `get_credentials()` shape. Login forwards its verified `login`. The generated
  helper now imports only stdlib JSON/path modules, reads local username/token,
  and performs no HTTP request. Missing or control-character-bearing values
  return no credential; logout already removes both username and token.
- Regression evidence: before implementation, 1/4 extended helper assertions
  passed and login configuration rejected the username parameter. The old
  helper source contained urllib, the identity API URL, and returned nothing
  offline despite a valid cached token.
- Focused offline command: `python -m pytest -q
  tests/pytest_offline_scripts.py -k 'git_helper_identity or login_config or
  git_credentials_isolation or config_permissions or cli_surface'` passed 5/5
  pytest cases in the `atomgit_cli` environment.
- Complete offline command: `python -m pytest -q` passed 42/42 pytest cases in
  40.02 seconds with local-loopback permission. The first sandboxed run passed
  40/42; its only failures were `PermissionError` while binding 127.0.0.1 in
  existing HTTP transport tests, not assertion failures.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Dependency compatibility: no HF call signature changed; existing locked
  signature contract tests passed in the full suite. Python 3.8-compatible
  syntax is retained.
- Documentation: README, architecture, and FAQ describe cached identity,
  offline helper lookup, and the required one-time re-login migration.
- Independent review: first review found P2 credential-protocol injection via
  CR/LF in cached values (`REQUEST CHANGES`). Persistence and helper output now
  reject all control characters with regressions. Fresh review found no open
  findings (`APPROVED`).
- DoD/security: tests use isolated HOME/global Git config and fake credentials;
  no real token/config was read, no real Git helper was changed, and no remote
  test was run. Residual migration risk is explicit: an old config without
  username yields no Git credentials until the user logs in again.
- Human acceptance: standing acceptance granted for the approved full plan.
- Commit/merge/push: authorized and pending.
