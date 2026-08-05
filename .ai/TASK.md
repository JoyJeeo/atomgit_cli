# Current Issue Contract

# Issue DOWNLOAD-PATH-TRAVERSAL

Status: `completed`

## Identity

- Local Issue: `DOWNLOAD-PATH-TRAVERSAL`
- Title: `Remote repository filenames can escape the requested download directory`
- Type: `security`, `cli`
- Priority: `P0`
- Branch: `codex/fix-download-path-traversal` (local only)
- Base: `yuto`
- Delivery mode: implement and review locally, commit, merge into `yuto`, and
  push only `yuto`.

## Previous Issue (Closed)

- `DOWNLOAD-REDIRECT-AUTH` was delivered by `ce4b1ae` and merged into `yuto`
  by `b570b7c`. Cross-origin redirects no longer receive the bearer token.

## User Impact And Evidence

`download_repo` and `download_file` currently join server-provided names with
the local root using `local_path / filename`. No containment validation rejects
`../escape`, absolute paths, Windows drive/UNC paths, control characters, or an
existing symlink that resolves outside the root. An offline probe confirmed
that `../escape.bin` produced a destination outside the requested directory
while the command reported success.

## Scope

In scope:

- define one shared safe destination resolver for repository filenames;
- reject absolute, parent-relative, Windows drive/UNC, backslash-separated,
  empty-segment, and control-character filenames;
- reject existing symlink components or destination symlinks that resolve
  outside the selected download root;
- apply the resolver to repository and single-file CLI download paths;
- add offline regressions proving rejected names never reach the downloader.

Out of scope: redirect policy, raw HTTP framing, repository type resolution,
and the approved default behavior of skipping existing safe files.

## Acceptance Criteria

- Every destination returned by the resolver is contained by the resolved
  download root.
- Malicious POSIX and Windows-style paths fail before directory creation or
  file download outside the root.
- Existing symlink escapes are rejected where the platform supports symlinks.
- Normal nested ASCII and non-ASCII repository paths remain supported.
- Focused download tests, the complete offline suite, compileall, and
  `git diff --check` pass.

## Permissions

- Authorized: local edits, local task branch and commits, local merge into
  `yuto`, and push of `yuto` only.
- Authorized remote tests: only `weixin_52273949/test_model` and
  `weixin_52273949/test_datasets`; this Issue requires no remote write.
- Not authorized: pushing the task branch, other remote repositories, `main`,
  release, or publication.

## Delivery Record

- Implementation: `_safe_download_destination` rejects empty, absolute,
  parent-relative, dot-segment, Windows drive/UNC, backslash-separated, and
  control-character names. It resolves existing symlinks and requires the
  destination to remain under the resolved download root. Repository downloads
  validate the complete file list before starting the first transfer; the same
  resolver protects single-file downloads.
- Regression evidence: before the fix, all 14 initial safety assertions failed;
  traversal, absolute, Windows, control-character, and symlink paths reached the
  downloader, and `../escape.bin` was reported as successfully downloaded.
- Focused offline tests: download path security, download contract, and repo-ID
  contract passed as 3 pytest cases.
- Complete offline suite: `python -m pytest` passed 38/38 in 32.87 seconds.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Authorized read-only live check: `sub/中文样本.csv` downloaded successfully
  from `weixin_52273949/test_model`, remained inside the temporary root, and
  had size 31 bytes.
- Independent review: no open findings; `APPROVED`. Residual risk is limited to
  a local attacker racing a symlink replacement after validation; existing
  symlink escapes are rejected and final file replacement remains atomic.
- Human acceptance: standing acceptance granted for the approved full plan.
- Commit/merge/push: authorized.
