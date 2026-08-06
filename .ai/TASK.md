# Current Issue Contract

# Issue REPOSITORY-VISIBILITY-AND-PUBLIC-CREATE

Status: `completed`

## Identity

- Local Issue: `REPOSITORY-VISIBILITY-AND-PUBLIC-CREATE`
- Title: `Manage repository visibility and create verifiably public repositories`
- Type: `cli`, `feature`, `compatibility`
- Priority: `P1`
- Branch: `codex/add-repo-visibility` (local only)
- Base: `yuto`
- Previous Issue: `CLI-REPOSITORY-LIST`, delivered by `f95b202` and merged by
  `de22527`.
- Delivery mode: standing-authorized implementation, review, commit, local merge
  into `yuto`, and push only `yuto`; task branch remains local-only.

## User Impact And API Contract

HF-compatible `create_repo(private=False)` has returned success while AtomGit
kept the repository private. The CLI therefore previously rejected public
creation and had no command to change visibility. Controlled prior evidence
showed that AtomGit V5 repository settings can supply the missing visibility
transition.

Official AtomGit documentation defines `PATCH /api/v5/repos/:owner/:repo` for
repository settings and `GET` on the same path for verification. Public create
will retain the proven HF model/dataset creation route, initially create private,
then apply `{"private": false}` through V5 and verify remote state before
reporting success.

## Scope

In scope: bounded V5 GET/PATCH JSON support, repository path quoting, verified
visibility API, `repo visibility REPO_ID public|private`, explicit `--public`
creation, preservation of `--private`, CLI/API regressions, and documentation.

Out of scope: destructive cleanup after partial public creation, organization
repository creation, code-repository creation through V5, repository deletion,
SDK create changes, branch behavior, and live remote mutation.

## Compatibility And Safety

- Existing `repo create ... --private` behavior remains supported.
- Creation requires exactly one of `--private` and `--public`; no implicit
  visibility is inferred.
- A failed public transition reports failure and never auto-deletes. Because a
  PATCH response or verification GET can be lost after remote mutation, the
  CLI must state that visibility may be unknown and require an explicit check.
- V5 credentials stay in headers, JSON responses are bounded, errors are
  sanitized, and repository path segments are percent encoded.
- Preserve Python 3.8+ and locked dependencies.

## Acceptance Criteria

- Visibility update sends exact PATCH JSON and then GET-verifies the requested
  state from `private` boolean or `visibility` string.
- A mismatch, malformed response, HTTP/network error, missing login, or invalid
  repo ID returns nonzero without leaking credentials.
- Public create first uses the established HF-compatible model route with
  `private=True`, then transitions and verifies public state; it reports failure
  and accurate unknown-state guidance if verification fails.
- Private create never performs a visibility PATCH.
- CLI requires explicit mutually exclusive `--private`/`--public`, documents
  the partial-failure safety behavior, and exposes `repo visibility` in help.
- Focused and full offline tests, compileall, and diff checks pass; independent
  review has no open P0/P1 findings.

## Permissions And Acceptance

- Authorized: local source/tests/docs/task metadata, task branch, conventional
  commit without `czx:` prefix, local merge into `yuto`, and push only `yuto`.
- Live create/privacy mutation is not authorized for this Issue; fixed test
  repositories must not have visibility changed without exact additional
  permission. Strict offline HTTP and existing prior service evidence apply.
- Human acceptance: standing acceptance granted for the ordered feature plan.

## Evidence And Closure

- Official API evidence: AtomGit documents `PATCH` and `GET`
  `/api/v5/repos/:owner/:repo`; its quick start defines public and private
  repositories. Existing project evidence shows HF public create is unreliable
  and V5 visibility update is effective.
- Implementation: V5 JSON exchange now supports bounded GET/PATCH with header
  credentials; visibility updates use an encoded shared repository ID, exact
  `private` JSON, and mandatory GET verification. CLI adds explicit public/
  private create flags and `repo visibility`; public create starts private and
  never reports success if transition verification fails, instead reporting the
  potentially unknown remote state. Product, README, architecture, and testing
  documentation distinguish CLI support from the unchanged SDK.
- Regression-before-implementation: `python tests/test_repo_visibility.py`
  failed 0/2 because the command and API did not exist.
- Focused offline tests: visibility passed 22/22, create contract passed 41/41,
  public-create safety passed both custom checks, SDK create remained 21/21,
  repository list passed 24/24, redirect security passed 9/9, and CLI surface
  passed 50/50.
- Complete offline suite: after resolving review feedback,
  `python -m pytest -q` passed 47/47 isolated script cases in 42.53 seconds in
  the `atomgit_cli` environment.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Live tests: not run because repository creation and privacy changes are remote
  mutations not authorized for the fixed test repositories in this Issue.
- Independent review: first review found a P1 false safety claim: PATCH may have
  succeeded even when the verification GET fails, so the repository cannot be
  promised private. Implementation, output, task contract, docs, and regression
  now report a potentially unknown remote state and require immediate explicit
  checking. Fresh review found no open findings: exact V5 JSON, mandatory GET
  verification, HF signature binding, CLI option conflicts, SDK separation,
  credential isolation, and partial-failure guidance are covered. Verdict:
  `APPROVED`.
- DoD: Issue-scoped implementation, regressions, full suite, locked HF call,
  documentation consistency, compileall, and diff checks agree. No real token,
  generated artifact, unrelated edit, remote mutation, or open P0/P1 finding is
  present.
- Commit/merge/push: authorized; exact references will be reported from Git
  after execution.
