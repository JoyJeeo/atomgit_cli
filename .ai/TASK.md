# Current Issue Contract

# Issue AUTH-STATUS-SEMANTICS

Status: `active`

## Identity

- Local Issue: `AUTH-STATUS-SEMANTICS`
- Title: `Distinguish authentication failures from permission denials`
- Type: `bug`, `cli`, `sdk`, `diagnostics`
- Priority: `P2`
- Branch: `codex/fix-auth-status-semantics` (local only)
- Base: `yuto`
- Previous Issue: `BRANCH-SOURCE-VERIFICATION`, delivered by `702bcb6`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

The shared authentication predicate treats any exception text containing the
digits `401` or `403` as an authentication error. Unrelated filenames, IDs, or
counts can therefore be misclassified. Real 403 permission denials are also
reported with the same re-login guidance as 401 invalid/expired credentials in
download, upload, repository creation, and SDK diagnostics.

Status evidence and explicit protocol wording must drive classification. A 401
means authentication failed; a 403 means the credential was understood but the
operation lacks permission. Incidental digits must not affect error semantics.

## Scope And Acceptance

- Add one shared credential-error classifier that returns authentication,
  permission, or no credential classification.
- Prefer structured HTTP status attributes from urllib/HF/httpx exceptions;
  use bounded explicit status/wording patterns only as compatibility fallback.
- Keep `is_auth_error` as the existing combined compatibility predicate.
- Give 401 and 403 distinct, credential-safe guidance in download, upload,
  repository creation, and SDK translation paths.
- Preserve higher-priority repository-not-found, gated, disabled, revision,
  request, timeout, network, and unknown classifications.
- Preserve the public SDK exception hierarchy: permission errors remain the
  existing compatible `AtomGitAuthenticationError` type but use permission
  semantics in the message.
- Add focused regressions for structured 401/403, explicit text fallbacks,
  incidental digits, precedence, and credential redaction.
- Do not change login behavior, commands, flags, network calls, exception API,
  credentials, or unrelated functionality.

## Compatibility And Risks

- Callers using `is_auth_error` or catching `AtomGitAuthenticationError` remain
  compatible; only false positives and user-facing categorization change.
- Text fallback cannot infer every arbitrary third-party message, so structured
  status attributes are authoritative whenever available.
- No live request is needed; strict offline exception objects cover this Issue.

## Permissions

- The user authorized fixing already audited defects one Issue at a time and
  explicitly excluded new functionality.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- No live request, remote write, credential mutation, or repository operation is
  authorized or required for this Issue.

## Required Evidence And Closure

- [x] Incidental 401/403 digits are reproduced as false-positive auth failures.
- [x] Structured and explicit 401/403 evidence is classified distinctly.
- [x] Download, upload, create, and SDK guidance reflects auth versus permission.
- [x] Existing classification precedence and public exception types are stable.
- [x] Focused and complete offline tests, compileall, pip, and diff checks pass.
- [x] Documentation, credential scan, scope audit, and independent review pass.
- [x] Human acceptance is covered by the standing ordered-fix authorization.
- [ ] The task is committed, merged into `yuto`, and only `yuto` is pushed.

## Verification Evidence

- Regression before implementation: the new credential semantics contract
  passed only `1/14`; the old predicate treated an incidental `401` count as an
  authentication failure and provided no structured auth/permission distinction.
- Implementation: `auth_error_kind` prefers integer status on dependency
  responses, direct status attributes, and urllib HTTP errors. Its text fallback
  accepts explicit HTTP/status/401/403 forms plus credential-specific wording;
  arbitrary digits and local filesystem `PermissionError` are not credential
  evidence. Existing `is_auth_error` remains the combined compatibility wrapper.
- User semantics: download, upload, repository creation, and SDK translation now
  direct 401 users to re-login and 403 users to repository/namespace permissions.
  SDK 403 remains `AtomGitAuthenticationError`, preserving public catch behavior.
- Focused results: credential semantics `15/15`; upload classification, upload
  error handling, SDK exceptions, download recovery, and repository-type
  resolution scripts all exited `0` offline.
- Complete offline suite: `pytest -q` exited `0` with all `55` collected tests;
  `python -m compileall -q .`, `python -m pip check`, and `git diff --check`
  passed in the `atomgit_cli` environment.
- Security and scope: no live request, network behavior, command, flag, public
  exception type, credential, dependency, generated artifact, or new feature is
  present; user output remains sanitized.
- Independent review: two pre-approval fallback weaknesses were resolved. Bare
  leading status numbers are no longer accepted, and filesystem permission text
  cannot become a remote 403. Final review is `APPROVED` with no open P0-P3
  findings; residual unknown third-party text safely falls through unless it
  exposes structured or explicit protocol evidence.
