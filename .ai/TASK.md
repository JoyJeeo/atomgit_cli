# Current Issue Contract

# Issue CREATE-EXIST-OK

Status: `completed`

## Identity

- Local Issue: `CREATE-EXIST-OK`
- Title: `CLI create reports an existing repository as newly created`
- Type: `bug`, `cli`, `api`
- Priority: `P1`
- Branch: `codex/fix-create-exist-ok` (local only)
- Base: `yuto`

## Previous Issue (Closed)

- `UPLOAD-OPTION-CONFLICTS` was delivered by `019c17b` and merged by `469a180`.

## Evidence And Scope

The CLI-facing API always passes `exist_ok=True` to Hugging Face create, so an
already existing repository returns success and the CLI says it was created.
The standalone SDK already exposes the correct default-false contract.

In scope: default CLI/API creation to `exist_ok=False`, add explicit CLI
`--exist-ok`, forward it through the API, update tests/docs, and validate the
two modes against the authorized existing model repository.

Out of scope: public repository support, repository deletion, SDK behavior, and
creating any new remote repository.

## Acceptance Criteria

- Default CLI/API creation forwards `exist_ok=False`.
- `--exist-ok` explicitly forwards true and preserves idempotent automation.
- CLI success text distinguishes creation from already-existing acceptance.
- Existing SDK default behavior remains unchanged.
- Offline/full checks and authorized non-destructive live checks pass.

## Permissions And Delivery

- Authorized: local edits/commits, local merge into `yuto`, and push only
  `yuto`; task branches remain local-only.
- Live testing is limited to `weixin_52273949/test_model`; no new repository is
  created and no content is modified.
- Human acceptance: standing acceptance granted for the approved full plan.
- Implementation: CLI/API default to `exist_ok=False`; CLI adds explicit
  `--exist-ok` and accurate “already exists or created” success text. Because
  AtomGit itself returned success for an existing repository even with false,
  default mode now performs an authenticated read-only tree preflight and does
  not send create when the repository already exists.
- Regression evidence: initial default forwarding assertions failed and the API
  lacked `exist_ok`. The first live check proved forwarding alone insufficient:
  both default and explicit modes returned true for the existing repository.
- Focused tests: 6/6 related pytest cases passed, including strict dependency
  signature binding, no-create existing behavior, CLI forwarding, and unchanged
  SDK coverage.
- Complete offline suite: 42/42 passed in 37.37 seconds.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Authorized live check: on `weixin_52273949/test_model`, default existing mode
  returned false without create; explicit exist-ok returned true. No repository
  or content was created, deleted, or modified.
- Independent review: no open findings (`APPROVED`). A create race between the
  preflight and server call remains possible because the server ignores false;
  eliminating it requires server-side conditional create semantics.
- Human acceptance: standing acceptance granted for the approved full plan.
- Commit/merge/push: authorized and pending.
