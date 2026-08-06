# Current Issue Contract

# Issue EXPLICIT-BRANCH-UPLOAD

Status: `completed`

## Identity

- Local Issue: `EXPLICIT-BRANCH-UPLOAD`
- Title: `Create explicit branches and upload to non-main revisions`
- Type: `cli`, `feature`, `compatibility`
- Priority: `P1`
- Branch: `codex/add-branch-upload` (local only)
- Base: `yuto`
- Previous Issue: `REPOSITORY-VISIBILITY-AND-PUBLIC-CREATE`, delivered by
  `04e060a` and merged by `ec82486`.
- Delivery mode: standing-authorized implementation, review, commit, local merge
  into `yuto`, and push only `yuto`; task branch remains local-only.

## Contract

AtomGit previously ignored implicit HF branch creation, so uploads rejected every
non-main revision. Official V5 API documents POST and GET
`/api/v5/repos/:owner/:repo/branches`; its compatible request body uses
`branch_name` and source `refs`.

Expected workflow: users explicitly run
`atomgit repo branch create REPO_ID BRANCH --from main`, which POSTs and then
GET-verifies the branch. `atomgit upload --revision BRANCH` then forwards the
validated existing branch to locked HF upload calls. Upload never auto-creates a
branch and missing-branch errors remain nonzero and actionable.

## Scope And Acceptance

- Add safe Git branch-name validation and reject ambiguous/unsafe ref names.
- Add bounded V5 POST JSON support, encoded branch paths, create + GET verify,
  and `repo branch create` CLI help/login/error behavior.
- Permit validated non-main revision forwarding for file, directory, and
  resumable upload; preserve empty/main compatibility and SDK behavior.
- Update tests/docs that currently state main-only behavior.
- Run focused and full offline tests, compileall, diff checks, and independent
  review with no open P0/P1 findings.

## Permissions

- Authorized local development/delivery follows standing rules.
- No live branch creation or upload is authorized in this Issue because those
  are remote writes; strict offline API/HF contracts apply.
- Human acceptance is standing-approved for the ordered plan.

## Evidence And Closure

- Official API evidence: AtomGit documents POST/GET branch endpoints; the V5
  compatible body uses `branch_name` and `refs`.
- Implementation: V5 POST support, strict ref validation, explicit branch
  create + GET verification, CLI branch command, and safe non-main forwarding
  now cover file, directory, and resumable CLI uploads. SDK remains main-only.
- Regression evidence: former main-only tests were converted to prove `dev`
  forwarding and malformed-ref rejection; new branch tests cover exact POST
  JSON, encoded verification path, CLI forwarding, and invalid names.
- Focused tests: branch create 8/8, API revision 14/14, file upload 16/16,
  dataset resumable 8/8, and upload resumable 13/13 custom checks passed.
- Complete offline suite: `python -m pytest -q` passed 48/48 isolated script
  cases in 46.64 seconds in the `atomgit_cli` environment.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Live tests: not run because branch creation and upload are remote writes not
  authorized for this Issue.
- Independent review: no open findings. The change requires explicit branch
  creation, verifies the remote branch before success, forwards only validated
  refs, preserves SDK main-only behavior, binds all existing HF upload paths,
  keeps credentials header-only, and documents that upload does not auto-create
  branches. Residual risk is AtomGit service acceptance of the documented V5
  compatible body and encoded slash branch path without an authorized live
  write. Verdict: `APPROVED`.
- DoD: implementation, regressions, full suite, docs, compileall, and diff
  checks agree; no token, artifact, unrelated edit, remote mutation, or open
  P0/P1 finding is present.
- Commit/merge/push: authorized; exact references will be reported from Git.
