# Current Issue Contract

# Issue BRANCH-SOURCE-VERIFICATION

Status: `active`

## Identity

- Local Issue: `BRANCH-SOURCE-VERIFICATION`
- Title: `Verify a created branch points to the requested source`
- Type: `bug`, `cli`, `reliability`
- Priority: `P2`
- Branch: `codex/fix-branch-source-verification` (local only)
- Base: `yuto`
- Previous Issue: `V5-AMBIGUOUS-WRITE-VERIFICATION`, delivered by `16341b2`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

Branch creation sends the requested source in `refs`, but post-write verification
only compares the returned branch name. A pre-existing or incorrectly created
same-name branch can therefore be accepted even when it points to a different
source commit, especially while recovering an ambiguous POST result.

The CLI must resolve the requested source before creation, then verify that the
target branch points to the same immutable commit after creation. Branch name
alone is not sufficient evidence.

## Scope And Acceptance

- Use the existing authenticated V5 commit read to resolve the source and the
  branch read to verify the target branch's immutable commit identifier.
- Resolve the source before POST so later source movement cannot change the
  expected value during verification.
- Return false with sanitized guidance if either V5 response lacks its required
  commit identity or if target and source commits differ.
- Preserve ambiguous-write recovery: matching target commit may recover success;
  HTTP 4xx remains definitive and skips post-write recovery reads.
- Preserve paths, POST body, token headers, timeouts, CLI arguments, and exit
  behavior.
- Add focused regressions for normal match, mismatch, malformed response,
  encoded source names, ambiguous recovery, and credential redaction.
- Do not add commands, flags, retries, revision types, or unrelated features.

## Compatibility And Risks

- This adds one pre-write GET to branch creation and requires AtomGit's existing
  branch response to expose a stable commit identity.
- A source branch may advance after the pre-write read; verification intentionally
  checks the exact commit requested at operation start, not the later branch tip.
- No live branch creation is authorized. Read-only schema inspection may use only
  the maintainer-provided test repository; write behavior remains strict offline.

## Permissions

- The user authorized fixing already audited defects one Issue at a time and
  explicitly excluded new functionality.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- No live branch creation, upload, deletion, visibility mutation, repository
  creation, or other remote write is authorized or required.

## Required Evidence And Closure

- [x] Branch-name-only false success is reproduced by a failing regression.
- [x] Source and target are compared using a stable commit identity.
- [x] Missing or mismatched identities fail with credential-safe output.
- [x] Ambiguous write and HTTP 4xx semantics remain correct.
- [x] Existing request paths, body, timeout, and CLI behavior remain compatible.
- [x] Focused and complete offline tests, compileall, pip, and diff checks pass.
- [x] Documentation, credential scan, scope audit, and independent review pass.
- [x] Human acceptance is covered by the standing ordered-fix authorization.
- [ ] The task is committed, merged into `yuto`, and only `yuto` is pushed.

## Verification Evidence

- Regression before implementation: branch creation passed `16/17`; a target
  with the requested name but a different `commit.id` was incorrectly accepted.
- Implementation: before POST, `GET /commits/:sha` resolves the requested
  branch, tag, or commit to the response's top-level `sha`. After POST,
  `GET /branches/:branch` must return the requested name and the same nested
  `commit.id`; missing or conflicting identities fail without exposing values.
- Request contract: strict regressions preserve the encoded repository/source/
  target paths, exact `{"branch_name", "refs"}` body, three 15-second bounds,
  CLI arguments, and exit behavior. Source failure stops before POST; HTTP 4xx
  stops before post-write GET; ambiguous writes recover only on exact match.
- Focused results: branch creation `28/28`, visibility `30/30`, repository
  deletion `48/48`, creation visibility `3/3`, and creation contract `42/42`
  passed offline.
- Complete offline suite: `pytest -q` exited `0` with all `55` collected tests;
  `python -m compileall -q .`, `python -m pip check`, and `git diff --check`
  passed in the `atomgit_cli` environment.
- Read-only live contract check used only `weixin_52273949/test_datasets`: V5
  commit responses expose top-level `sha`, branch responses expose nested
  `commit.id`, and both `main` and its complete SHA resolved to the same commit.
  The repository had no tag, so tag resolution remains offline-tested only.
- Security and scope: no live write, command, flag, retry, dependency change,
  credential, generated artifact, or unrelated feature is present.
- Independent review: one pre-approval field-shape weakness was reproduced at
  `27/28` and resolved by strict source/target extractors (`28/28`). Final review
  is `APPROVED` with no open P0-P3 findings. Residual risk is a safe false failure
  if a mutable source advances between its pre-read and the POST.
