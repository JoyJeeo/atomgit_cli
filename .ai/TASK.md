# Current Issue Contract

# Issue CREATE-ERROR-REPORTING

Status: `in_progress`

## Identity

- Local Issue: `CREATE-ERROR-REPORTING`
- Title: `Report the real failure reason when repo create fails`
- Type: `bug`, `cli`, `usability`
- Priority: `P1`
- Branch: `czx/fix-create-repo-error-reporting` (local only)
- Base: `yuto`
- Delivery mode: fix the swallowed exception, add offline regressions, commit
  locally with `czx:` prefix, merge into `yuto`, push only `yuto`.

## User Impact And Evidence

`atomgit repo create weixin_52273949/test_model --type model --private` and
`atomgit repo create weixin_52273949/test_datasets --type dataset --private`
both fail with only the generic message `仓库 ... 创建失败` and no reason.

Local diagnosis (read-only, token never printed): `~/.atomgit/config.json`
stores a 22-char `fake-...` token; AtomGit v5 `/api/v5/user` returns
`401 token not found`; no `ATOMGIT_TEST_TOKEN` env var. HF `create_repo` then
raises 401, and `HuggingFaceAPI.create_repo` swallowed every exception
(`except Exception as e: return False`), so the CLI hid the cause.

## Scope

In scope: classify create-repo failures into actionable categories, print the
real reason plus a hint from `api.py`, and add offline contract tests that
assert the reason surfaces. No live writes, no credential changes.

Out of scope: remote issue creation, milestones, token/credential recovery,
other commands.

## Acceptance Criteria

- `create_repo` prints `创建仓库失败[<类别>]: <错误>` and `💡 建议: <hint>` and
  still returns `False` (public bool contract unchanged).
- A 401/403/invalid-token failure is classified as `认证失败` with an
  `atomgit login` hint.
- Offline checks pass: `tests/test_create_contract.py` 25/25; full suite stays
  28 passed / 8 failed (pre-existing environment-only failures unchanged);
  `python -m compileall -q .`; `git diff --check`.

## Permissions

- Authorized: local source/test/TASK edits, local commit, local merge into
  `yuto`, push of `yuto` only.
- Not authorized: live repo create/upload/delete, credential changes, pushing
  the task branch, merging into `main`, release.

## Delivery Record

- Root cause: stored token `fake-...` is invalid (AtomGit 401 `token not
  found`); `api.py create_repo` swallowed the exception and returned `False`.
- Fix: added `_classify_create_repo_error` (auth / bad-request / timeout /
  network / unknown) and made `create_repo` print the classified reason and
  hint before returning `False`.
- Tests: `tests/test_create_contract.py` now asserts the real reason is
  printed for a dependency failure and that an auth failure suggests
  re-login. Result: 25/25 passed.
- Full suite: 28 passed / 8 failed (baseline-identical; failures are
  environment-only: config permissions, deploy/installer, git helper,
  resumable recovery, runtime policy, wheel smoke).
- Remaining risk: user must run `atomgit login` with a real AtomGit token;
  the `E:\桌面文件\atomgit_cli` copy needs the same fix (api.py + test file).
