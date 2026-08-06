# Current Issue Contract

# Issue CLI-REPOSITORY-LIST

Status: `completed`

## Identity

- Local Issue: `CLI-REPOSITORY-LIST`
- Title: `List repositories available to the authenticated user`
- Type: `cli`, `feature`
- Priority: `P2`
- Branch: `codex/add-repo-list` (local only)
- Base: `yuto`
- Previous Issue: `CLI-SINGLE-FILE-DOWNLOAD`, delivered by `6258822` and
  merged by `d874747`.
- Delivery mode: standing-authorized implementation, review, commit, local merge
  into `yuto`, and push only `yuto`; task branch remains local-only.

## User Impact And API Contract

The CLI can act on a known repository ID but cannot discover repositories
available to the logged-in user. AtomGit's official V5 API documents
`GET https://api.atomgit.com/api/v5/user/repos`, authenticated by request header,
with a JSON repository collection response.

Expected behavior: `atomgit repo list` requires AtomGit login, requests the
authorized repository collection without putting credentials in the URL, and
prints stable repository IDs plus public/private visibility when present.

## Scope

In scope: a minimal authenticated AtomGit V5 JSON GET boundary, repository-list
API method, `repo list` CLI command, robust parsing of documented array and
defensive collection wrappers, concise output, sanitized errors, offline tests,
and README/architecture documentation.

Out of scope: public-user discovery, organization aggregation, filters,
server-side pagination options not documented for this endpoint, create/update/
delete operations, SDK exposure, and access to any repository beyond the
existing standing live authorization.

## Compatibility Requirements

- Preserve existing CLI/API behavior and Python 3.8+ syntax.
- Use `https://api.atomgit.com/api/v5` and header authentication; tokens must
  never appear in URLs, output, errors, or fixtures except clearly fake values.
- Do not change locked HF/datasets dependencies.

## Acceptance Criteria

- `atomgit repo list` is advertised in help and rejects logged-out use before
  network access.
- The API sends one authenticated GET to `/api/v5/user/repos`, requests JSON,
  applies a finite timeout, and rejects malformed/non-collection JSON.
- CLI output handles empty results, standard `full_name`, owner/name fallback,
  private boolean, visibility string, and missing optional fields.
- HTTP/network/JSON failures exit nonzero with a concise sanitized message and
  never expose the credential.
- Focused and complete offline tests, compileall, and diff checks pass.
- Independent review has no open P0/P1 findings.

## Permissions And Acceptance

- Authorized: local source/tests/docs/task metadata, task branch, conventional
  commit without `czx:` prefix, local merge into `yuto`, and push only `yuto`.
- No live list call is authorized because this endpoint enumerates repositories
  outside the two fixed test repositories. Official documentation and strict
  offline HTTP contracts are the acceptance boundary for this Issue.
- Human acceptance: standing acceptance granted for the ordered feature plan.

## Evidence And Closure

- Official API evidence: AtomGit OpenAPI introduction documents the
  `https://api.atomgit.com/api/v5` base and header token authentication; the
  repository-list page documents `GET /api/v5/user/repos` with a 200 response.
- Implementation: a bounded authenticated V5 JSON GET helper now backs
  `HuggingFaceAPI.list_repos`; `atomgit repo list` formats direct and fallback
  repository IDs plus visibility, while README and architecture document the
  command and credential boundary. Cross-origin redirects strip both bearer and
  V5 private-token headers.
- Regression-before-implementation: `python tests/test_repo_list.py` failed 0/2
  because neither the `repo list` command nor API method existed.
- Focused offline tests: `python tests/test_repo_list.py`,
  `python tests/test_download_redirect_security.py`,
  `python tests/test_create_contract.py`, and `python tests/test_cli_surface.py`
  passed 24/24, 9/9, 33/33, and 50/50 custom checks respectively.
- Complete offline suite: `python -m pytest -q` passed 46/46 isolated script
  cases in 41.51 seconds in the `atomgit_cli` environment.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Live tests: not run because `/user/repos` necessarily enumerates repositories
  beyond the two fixed repositories authorized for live access.
- Independent review: no findings. Official endpoint and authentication agree
  with the implementation; credentials are absent from URLs and sanitized from
  failures, cross-origin redirects remove both supported credential headers,
  response parsing is bounded and strict, and existing repository creation
  remains covered. The lack of live enumeration is an accepted authorization
  boundary, not missing local evidence. Verdict: `APPROVED`.
- DoD: Issue-scoped implementation, regression, redirect security coverage,
  full suite, documentation, compileall, and diff checks agree; no real token,
  generated artifact, unrelated change, or open P0/P1 finding is present.
- Commit/merge/push: authorized; exact references will be reported from Git
  after execution.
