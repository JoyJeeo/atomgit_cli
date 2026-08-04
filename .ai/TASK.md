# Current Issue Contract

# Issue EMPTY-REPO-DOWNLOAD

Status: `in_progress`

## Identity

- Local Issue: `EMPTY-REPO-DOWNLOAD`
- Title: `Download of an empty repository reports 下载失败（ValueError）`
- Type: `bug`, `cli`, `compatibility`
- Priority: `P1`
- Branch: `czx/fix-empty-repo-download` (local only)
- Base: `yuto`
- Delivery mode: guard the huggingface_hub empty-repo crash, add offline
  regressions, commit locally with `czx:` prefix, merge into `yuto`, push only
  `yuto`.

## Previous Issue (Closed)

- `CREATE-ERROR-REPORTING` completed: `api.py create_repo` now prints the
  classified reason (`认证失败` + `atomgit login` hint) instead of swallowing
  the exception. Commits `6f2309a` / merge `a89bc9f` on `yuto`.

## User Impact And Evidence

`python -m atomgit download weixin_52273949/test_model` (no `-d`, downloads
into `./test_model`) fails with:

```
Downloading (incomplete total...): 0.00B [00:00, ?B/s]仓库下载失败: 下载失败（ValueError）
✗ 仓库下载失败: weixin_52273949/test_model
```

The local `test_model` directory is created but stays empty. Root cause:
`huggingface_hub==1.1.7` `snapshot_download` on an **empty repository**
(`repo_info.siblings` empty) passes an empty iterable to `tqdm.thread_map`,
which raises CPython `ValueError: min() iterable argument is empty`. The CLI
maps it to the unhelpful `下载失败（ValueError）`. Reproduced offline-free with
a read-only probe against the live repo; the repo currently exists but has
zero files.

## Scope

In scope: `api.py download_repo` handles the empty-repo ValueError with a
clear message and success result; `tests/test_download_contract.py` adds
offline regressions. No live writes.

Out of scope: remote issues, milestones, credentials, other commands,
`atomgit_hub.py` SDK wrapper behavior.

## Acceptance Criteria

- `download_repo` on an empty repo prints `仓库为空，没有可下载的文件；本地目录已创建`
  and returns `True` (CLI shows success, no crash, no `ValueError`).
- An unrelated `ValueError` still fails loudly (not masked).
- Offline checks pass: `tests/test_download_contract.py` 28/28,
  `tests/test_create_contract.py` 25/25, full suite baseline 28 passed / 8
  failed, `python -m compileall -q .`, `git diff --check`.

## Permissions

- Authorized: local source/test/TASK edits, local commit, local merge into
  `yuto`, push of `yuto` only.
- Not authorized: live repo create/upload/delete, credential changes, pushing
  the task branch, merging into `main`, release.

## Delivery Record

- Fix: `download_repo` now intercepts the CPython `min() iterable argument is
  empty` ValueError raised inside `snapshot_download`/tqdm for empty repos,
  prints a clear message, and returns `True`; other ValueErrors re-raise.
- Live check (read-only): `download_repo('weixin_52273949/test_model')` now
  prints `仓库为空，没有可下载的文件；本地目录已创建` and succeeds.
- Tests: `test_download_contract.py` 28/28 (new: empty repo succeeds with
  clear message; unrelated ValueError still fails); `test_create_contract.py`
  25/25.
- Remaining risk: none known for this path; user should upload a file first to
  see real content download. `E:\桌面文件\atomgit_cli` copy needs api.py +
  test sync (performed after merge).
