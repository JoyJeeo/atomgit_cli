# Current Issue Contract

# Issue LOGIN-ERROR-SEMANTICS

Status: `active`

## Identity

- Local Issue: `LOGIN-ERROR-SEMANTICS`
- Title: `Preserve actionable login and whoami failure semantics`
- Type: `bug`, `cli`, `authentication`, `diagnostics`
- Priority: `P2`
- Branch: `codex/fix-login-error-semantics` (local only)
- Base: `yuto`
- Previous Issue: `REPO-INFO-STUB-SEMANTICS`, delivered by `9c2563a`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

`_get_login_user_by_token` catches every exception and returns `None`. Both
`login` and `whoami` consequently erase the difference between invalid
credentials, insufficient permission, network failure, timeout, service
failure, and malformed responses. The CLI then tells every failed login to
check the token, which is incorrect and can send users toward the wrong fix.

Authentication failures must remain failures, but output must retain a fixed,
credential-safe and actionable category. Network and service failures must not
be reported as an invalid token. Raw exception text, response bodies, and token
values must never be printed.

## Scope And Acceptance

- Preserve command names, options, exit codes, API method signatures, endpoint,
  request headers, timeout, credential persistence, and Git-helper behavior.
- Categorize 401, 403, 429, 5xx, network/timeout, and malformed-response
  failures using fixed credential-safe text.
- Ensure `login` and `whoami` both surface the category once without misleading
  token advice.
- Preserve the existing short-token rejection and successful login behavior.
- Add focused offline regression coverage proving prior failure and token/raw
  exception redaction.
- Do not add a command, option, exception type, retry policy, remote call, or
  unrelated authentication feature.

## Permissions

- The user authorized fixing already audited defects one Issue at a time and
  explicitly excluded new functionality.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- No live request, repository access, remote write, credential mutation, or
  external side effect is authorized or required for this Issue.

## Required Evidence And Closure

- [x] Previous behavior is reproduced by a failing focused regression.
- [x] Login and whoami preserve safe actionable failure categories.
- [x] Tokens and raw exception details are absent from output.
- [x] Existing login/configuration and CLI compatibility tests pass.
- [x] Complete offline tests, compileall, pip, and diff checks pass.
- [x] Scope, credentials, documentation, and independent review pass.
- [ ] The task is committed, merged into `yuto`, and only `yuto` is pushed.

## Verification Evidence

- Regression before implementation: `python tests/test_login_error_semantics.py`
  exited `1` with `1/7` checks passing. Every remote failure returned only
  `获取用户信息失败`, `whoami` emitted no category, and the CLI advised checking
  the token for an arbitrary failure.
- Focused result after implementation: the expanded regression exited `0` with
  `11/11` checks covering the unchanged success request contract plus 401, 403,
  429, 503, network, timeout, malformed JSON, `whoami`, CLI exit behavior, and
  credential/raw-error redaction.
- Compatibility result: `test_login_config.py` passed `16/16`,
  `test_cli_surface.py` passed `50/50`, `test_auth_status_semantics.py` passed
  `15/15`, and `test_cli_error_redaction.py` passed `20/20`.
- Complete offline suite: `python -m pytest -q` exited `0` with all `59`
  collected tests; `python -m compileall -q .`, `python -m pip check`, and
  `git diff --check` passed in the `atomgit_cli` environment.
- Compatibility and isolation: the endpoint, authorization header, user agent,
  accept header, ten-second timeout, method signatures, credential persistence,
  exit codes, and Git-helper path are unchanged. Tests replace urllib and
  configuration methods and perform no live request or real credential write.
- Locked dependencies remain `huggingface-hub==1.1.7` and `datasets==4.4.1`;
  this change introduces no dependency call or dependency version change.
- Independent review: `APPROVED` with no open P0-P3 finding. The only residual
  limitation is that live AtomGit status behavior was not exercised; the test
  uses strict offline urllib failures and response fakes, as required by scope.
- Human acceptance is covered by the maintainer's standing ordered-fix and
  delivery authorization; no remote Issue transition is requested or made.
