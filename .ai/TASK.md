# Current Issue Contract

# Issue REPO-DELETE

Status: `completed`

## Identity

- Local Issue: `REPO-DELETE`
- Title: `Delete repositories with explicit confirmation and verification`
- Type: `cli`, `feature`, `data-safety`
- Priority: `P1`
- Branch: `codex/add-repo-delete` (local only)
- Base: `yuto`
- Previous Issue: `DOWNLOAD-PRUNE`, delivered by `19b5222` and merged by
  `c13a859`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

The repository-management CLI can create, list, and change visibility but has
no deletion command. AtomGit's official V5 documentation defines repository
deletion as `DELETE /api/v5/repos/:owner/:repo`, matching the endpoint already
used for repository visibility and detail verification.

Add `atomgit repo delete REPO_ID --confirm REPO_ID`. Require login, a valid
repository ID, and an exact literal confirmation before any API call. Perform
an authenticated preflight GET, issue DELETE, then require a GET 404 before
reporting success. Ambiguous network outcomes must be verified when possible
and otherwise reported as unknown, without exposing credentials.

## Scope And Acceptance

- Extend the bounded V5 request helper to support bodyless DELETE requests.
- Reuse normalized and percent-encoded V5 repository paths for multi-level IDs.
- Reject missing or mismatched confirmation locally with a nonzero exit and no
  API call.
- Preflight the exact target, delete it, and verify absence; never report
  success merely because the DELETE request returned.
- Recover an ambiguous DELETE response as success only when the verification
  GET proves the repository is absent; distinguish still-present and unknown
  states with credential-safe output.
- Keep this a CLI-only capability; do not add or alter the public Python SDK.
- Add strict request, failure, CLI, compatibility, and credential regressions;
  update user/product/architecture documentation.
- Run focused and complete offline tests, compileall, diff checks, and an
  independent review.

## Permissions

- Standing local development, commit, merge, and `yuto` push permissions apply.
- Live read-only tests may use only `weixin_52273949/test_model` and
  `weixin_52273949/test_datasets`. No remote deletion or other remote write is
  authorized, so this Issue must not execute a live DELETE request.
- Human acceptance is standing-approved for the ordered plan.

## Evidence And Closure

- Official contract: the AtomGit V5 documentation page
  `/docs/apis/delete-api-v-5-repos-owner-repo` identifies repository deletion
  as `DELETE /api/v5/repos/:owner/:repo`. The implementation reuses the existing
  bounded V5 client, `PRIVATE-TOKEN` header, normalized repository path, and
  credential-safe redirect handler; it does not use the type-dependent HF
  deletion method.
- Implementation: `atomgit repo delete REPO_ID --confirm REPO_ID` requires
  login, a valid ID, and exact literal confirmation at both CLI and exported API
  boundaries. It performs GET preflight, a bodyless DELETE, and a final GET;
  success requires the final request to return 404. Confirmations, credentials,
  and multi-level normalized paths are never mixed or silently rewritten.
- Failure semantics: deterministic HTTP 4xx DELETE responses fail immediately
  and cannot be converted to success. Network loss, timeout, server failure, or
  a successful response that cannot be parsed is treated as ambiguous and may
  recover only through a final GET 404. A still-present repository or failed
  verification returns nonzero with credential-safe present/unknown guidance.
- Focused regression: `python tests/test_repo_delete.py` passed 48/48 checks for
  request method/path/body/header/timeout, preflight and absence verification,
  multi-level IDs, confirmation at both boundaries, deterministic 4xx,
  ambiguous recovery, present/unknown/malformed/missing states, token isolation,
  CLI help, argument rejection, forwarding, and exit codes. Repository list and
  visibility regressions also passed.
- Complete offline suite: `python -m pytest -ra` collected and passed 52/52
  isolated scripts. `python -m compileall -q .` and `git diff --check` passed in
  the `atomgit_cli` conda environment.
- Live evidence: no live DELETE was run. The standing test-repository permission
  expressly excludes remote deletion, so neither fixed test repository nor any
  other remote state was changed.
- Independent review: the first pass found a P1 false-success path where a
  deterministic HTTP 4xx could be followed by GET 404 and incorrectly recover.
  The implementation now allows recovery only for ambiguous outcomes and has a
  strict regression. The second pass found no open P0/P1/P2/P3 finding and
  confirmed official endpoint alignment, dual confirmation, bounded requests,
  deterministic/ambiguous separation, absence verification, CLI-only SDK
  scope, multi-level normalization, and token-safe output. Residual risk: a GET
  404 means inaccessible according to the remote API and cannot distinguish a
  rare concurrent access revocation from deletion without broader server-side
  evidence. Verdict: `APPROVED`.
- DoD: implementation, documentation, focused and complete offline tests,
  compileall, diff check, dependency-signature inspection, independent review,
  credential scan, scope audit, and standing human acceptance agree; no secret,
  generated artifact, unrelated edit, unauthorized remote mutation, or open
  finding is present.
- Commit/merge/push: authorized; references will be reported after delivery.
