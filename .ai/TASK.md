# Current Issue Contract

# Issue ANONYMOUS-HF-TOKEN-ISOLATION

Status: `completed`

## Identity

- Local Issue: `ANONYMOUS-HF-TOKEN-ISOLATION`
- Title: `Anonymous CLI downloads may reuse an unrelated Hugging Face token`
- Type: `security`, `bug`, `compatibility`
- Priority: `P1`
- Branch: `codex/isolate-anonymous-hf-token` (local only)
- Base: `yuto`
- Delivery mode: standing-authorized implementation, review, commit, local merge
  into `yuto`, and push only `yuto`; the task branch remains local-only.

## User Impact And Evidence

When AtomGit credentials are absent, the CLI passes `token=None` to
`huggingface_hub.HfApi`. In locked `huggingface-hub==1.1.7`, `None` means use
the ambient Hugging Face token when one exists. Because AtomGit redirects the
HF endpoint to `https://hub.atomgit.com`, an unrelated Hugging Face credential
can therefore be attached to an anonymous AtomGit repository-list request.

Expected behavior: anonymous AtomGit download discovery must pass
`token=False`, which explicitly disables implicit Hugging Face authentication;
stored AtomGit credentials must still be forwarded unchanged.

## Scope

In scope: the CLI-facing AtomGit file-list client used by repository and
single-file downloads, a regression proving the locked dependency's `None`
versus `False` behavior, an exact boundary test for anonymous and authenticated
calls, and the smallest authoritative documentation update.

Out of scope: SDK token semantics, login storage, Git credential helpers,
download behavior beyond credential selection, new CLI features, dependency
changes, live remote writes, and every later approved feature Issue.

## Compatibility Requirements

- Preserve Python 3.8+ and `huggingface-hub==1.1.7` compatibility.
- Preserve authenticated downloads and all public CLI/SDK signatures.
- Never read, print, or persist a real token in tests or output.

## Acceptance Criteria

- Locked dependency evidence shows `HfApi(token=None)` may resolve ambient HF
  credentials while `HfApi(token=False)` does not.
- Anonymous CLI repository discovery constructs `HfApi(token=False)`.
- Stored AtomGit credentials remain passed as the exact explicit token.
- Repository and single-file download behavior otherwise remains unchanged.
- Focused regression, complete offline suite, compileall, and diff checks pass.
- Independent review reports no open P0/P1 findings.

## Permissions And Acceptance

- Authorized: local source, tests, documentation, task metadata, task-branch
  creation, conventional commit without `czx:` prefix, local merge into
  `yuto`, and push only `yuto`; task branch must not be pushed.
- Remote testing is not required for this credential-selection fix. The
  standing live scope remains limited to the two supplied repositories and
  grants no deletion, publication, or unrelated repository access.
- Human acceptance: standing acceptance granted by the user's instruction to
  complete development, testing, commits, and delivery in the recommended
  order.

## Evidence And Closure

- Implementation: `_atomgit_list_repo_files` now converts only the absent/falsy
  credential case to explicit `False`; configured AtomGit tokens pass through
  unchanged. Architecture documentation records this isolation boundary.
- Regression-before-fix evidence: `python tests/test_anonymous_token_isolation.py`
  passed 5/6 checks and failed because the anonymous `HfApi` constructor
  received `NoneType`; locked HF evidence simultaneously showed `None` added an
  authorization header while `False` did not.
- Focused offline regression: `python tests/test_anonymous_token_isolation.py`,
  `python tests/test_download_contract.py`, and
  `python tests/test_download_repo_type_resolution.py` passed 6/6, 45/45, and
  7/7 custom checks respectively.
- Complete offline suite: `python -m pytest -q` passed 44/44 isolated script
  cases in 40.69 seconds in the `atomgit_cli` environment.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Live tests: not run; the regression is fully observable at the locked HF
  client boundary and sending an unrelated credential remotely would be unsafe.
- Independent review: no findings. The diff preserves explicit AtomGit tokens,
  uses the locked HF client's documented `False` opt-out, restores the test
  environment, changes no public API, and includes a regression that would fail
  before the fix. Residual live-test risk is intentionally accepted because
  remotely reproducing credential disclosure is neither necessary nor safe.
  Verdict: `APPROVED`.
- DoD/security: the final diff is Issue-scoped, contains only fake credential
  values, changes no global runtime state, preserves Python 3.8 syntax, and has
  no open P0/P1 finding. Human acceptance is covered by standing delivery
  authorization.
- Commit/merge/push: authorized; exact references will be reported from Git
  after execution.
