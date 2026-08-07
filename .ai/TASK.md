# Current Issue Contract

# Issue LOGIN-RESPONSE-BOUND

Status: `active`

## Identity

- Local Issue: `LOGIN-RESPONSE-BOUND`
- Title: `Bound AtomGit login identity responses before parsing`
- Type: `bug`, `security`, `authentication`, `resource-safety`
- Priority: `P2`
- Branch: `codex/bound-login-response` (local only)
- Base: `yuto`
- Previous Issue: `LOGIN-ERROR-SEMANTICS`, delivered by `cdcbf17`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

`_get_login_user_by_token` calls `response.read()` without a byte count before
JSON decoding. A faulty or hostile identity response can therefore consume
unbounded process memory. The authenticated V5 request path already reads at
most its fixed limit plus one byte and rejects oversized JSON before parsing.

The identity endpoint must apply the same bounded-read pattern with a limit
appropriate for one user profile. Oversized responses must fail through the
existing safe malformed-response category without parsing or exposing their
body, exception details, or token.

## Scope And Acceptance

- Introduce one fixed identity JSON byte limit and read at most limit plus one.
- Reject an oversized body before UTF-8 decoding or JSON parsing.
- Preserve endpoint, headers, timeout, method signatures, successful identity
  shape, credential persistence, error category, CLI behavior, and Git helper.
- Add an offline regression that fails on the prior unbounded read, proves the
  exact maximum read request, and proves oversized data never reaches JSON.
- Document the identity response bound for maintainers.
- Do not change the general V5 limit, add streaming JSON, add retries, change
  token validation, or implement unrelated authentication functionality.

## Permissions

- The user authorized completion of all confirmed defects one Issue at a time.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- No live request, repository access, remote write, real credential mutation,
  or external side effect is authorized or required for this Issue.

## Required Evidence And Closure

- [x] Previous unbounded read is reproduced by a failing focused regression.
- [x] Identity responses are bounded and oversized data is rejected pre-parse.
- [x] Existing login behavior and credential/error redaction remain compatible.
- [x] Complete offline tests, compileall, pip, and diff checks pass.
- [x] Scope, credentials, documentation, and independent review pass.
- [ ] The task is committed, merged into `yuto`, and only `yuto` is pushed.

## Verification Evidence

- Regression before implementation: `python tests/test_login_response_bound.py`
  exited `1` with `1/5` checks passing. The configured bound was absent, both
  responses recorded `read(-1)`, and oversized data reached the JSON parser.
- Focused result: the same regression exited `0` with `5/5` checks. A normal
  response requests exactly `1,048,577` bytes; an oversized body is rejected
  before decoding/parsing and uses the existing safe invalid-response message.
- Compatibility result: `test_login_error_semantics.py` passed `11/11`,
  `test_login_config.py` passed `16/16`, `test_cli_surface.py` passed `50/50`,
  and `test_cli_error_redaction.py` passed `20/20`.
- Complete offline suite: `python -m pytest -q` exited `0` with all `60`
  collected tests; `python -m compileall -q .`, `python -m pip check`, and
  `git diff --check` passed in the `atomgit_cli` environment.
- Compatibility and scope: the new constant is one MiB, only the identity body
  read changed, and the endpoint, headers, ten-second timeout, public method
  signatures, successful result, persistence, CLI, and Git helper are unchanged.
- Locked dependencies remain `huggingface-hub==1.1.7` and `datasets==4.4.1`;
  this Issue changes only Python standard-library response handling.
- Security and isolation: fakes replace urllib and credential persistence; no
  real token, HOME mutation, live request, repository access, or remote write
  occurred. Oversized bytes and parser assertion text are absent from output.
- Independent review: `APPROVED` with no open P0-P3 finding. No live test is
  needed because the defect and the byte boundary are entirely client-local.
- Human acceptance is covered by the maintainer's instruction to complete all
  confirmed defects under the standing delivery workflow.
