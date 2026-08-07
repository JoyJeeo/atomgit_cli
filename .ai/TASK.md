# Current Issue Contract

# Issue CLI-UPLOAD-DEFAULT-RESUME

Status: `active`

## Identity

- Local Issue: `CLI-UPLOAD-DEFAULT-RESUME`
- Title: `Default directory uploads to resumable mode with repository prefixes`
- Type: `cli`, `compatibility`
- Priority: `P1`
- Branch: `codex/default-resumable-upload` (local only)
- Base: `yuto`
- Previous Issue: `CLI-BASELINE-MONOTONIC`, delivered by `0274131`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Objective

The maintainer requested that CLI directory uploads support interruption and
resume by default and remain compatible with `--path-in-repo`. Currently a
directory uses the non-resumable HF `upload_folder` path unless `--resumable`
is supplied, while the CLI rejects `--resumable --path-in-repo` before any
upload. Locked `huggingface-hub==1.1.7` exposes no `path_in_repo` parameter on
`HfApi.upload_large_folder`, so forwarding the option directly is not valid.

Make resumable mode the automatic CLI choice for directories, preserve normal
single-file behavior, and construct a stable local projection when a repository
prefix is requested so HF sees the desired relative paths and retains its
resume metadata across repeated commands.

## Scope And Acceptance

- A directory upload with no explicit mode calls the resumable large-folder
  path; a single-file upload continues to use the ordinary file path.
- Existing `--resumable` remains accepted and a new `--no-resumable` selection
  permits the ordinary directory uploader when its commit-message behavior is
  required.
- A directory with `--message` and no explicit mode preserves the message by
  selecting the ordinary uploader; explicit `--resumable --message` remains an
  error rather than silently ignoring the message.
- `--num-workers` is valid for the default resumable directory mode and remains
  invalid for a non-resumable or single-file upload.
- Resumable directory uploads accept a normalized `--path-in-repo`, expose the
  selected source only beneath that remote prefix, and reuse one credential-free
  private projection plus HF metadata for the same source/repository/revision/
  prefix identity.
- Projection synchronization preserves unchanged resume metadata, reflects
  changed and removed source files, excludes HF's source metadata subtree, and
  never follows symbolic links.
- Locked HF method calls keep authenticating through `HfApi(token=...)` and do
  not pass unsupported `path_in_repo` or `token` method arguments.
- Update exact CLI schema, focused offline regressions, README and upload
  behavior documentation. SDK upload defaults and public signatures are out of
  scope. No live AtomGit operation is required or authorized.

## Permissions

- The maintainer explicitly requested this CLI behavior change.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- No live request, test repository access, credential mutation, Git-helper
  mutation, remote write other than the authorized `yuto` push, or release is
  authorized or required.

## Required Evidence And Closure

- [x] A regression fails against the previous default/non-prefix behavior.
- [x] Focused CLI and API projection tests pass offline.
- [x] The exact CLI schema and comprehensive baseline pass.
- [x] Locked dependency signatures, compileall, pip check, diff check, scope,
      credentials, documentation, and independent review pass.
- [ ] Human acceptance is recorded and the authorized local delivery completes.

## Verification Evidence

- Previous-gap regression: after updating `tests/test_upload_resumable.py` but
  before runtime implementation, `python tests/test_upload_resumable.py`
  exited `1` with `14/18`; default directories still called `upload_folder`,
  `--no-resumable` did not exist, and workers required explicit resumable.
- Focused resumable result: `python tests/test_upload_resumable.py` passes
  `46/46`. It proves automatic directory selection, ordinary file behavior,
  explicit opt-out, message compatibility, model/dataset routing, worker and
  revision forwarding, prefix-relative ignore patterns, source synchronization,
  root and prefixed metadata reuse, repository isolation, no source-tree
  metadata pollution, reserved-path guidance, metadata collision rejection,
  and case-insensitive Windows-safe reserved-path handling.
- Locked dependency result: `python tests/test_hf_api_contract.py` passes
  `13/13` against `huggingface-hub==1.1.7` and `datasets==4.4.1`. The real
  large-folder signature accepts neither `token` nor `path_in_repo`; filtering
  binds to the installed `filter_repo_objects` signature.
- Affected ordinary-upload tests explicitly select `--no-resumable`; upload
  validation, path, ignore, type, progress, schema, dataset route, timeout,
  recovery, statistics, and symlink checks pass offline.
- Mandatory comprehensive result: `python tests/run_cli_baseline.py` passed all
  `62` isolated pytest cases in `50.37s` with no skip after the final
  implementation changes.
- Required checks: `python -m compileall -q .`, `python -m pip check`, and
  `git diff --check` pass in the `atomgit_cli` environment.
- Scope and security: no live request, credential read, Git-helper mutation,
  test repository operation, dependency change, SDK behavior change, or remote
  write ran. Projection identities contain no credential and cache roots are
  private on POSIX platforms; the diff credential scan found no real secret.
- Documentation and exact schema describe the new automatic directory mode,
  `--no-resumable`, stable prefix projection, message behavior, and cross-filesystem
  copy/disk-space tradeoff.
- First independent review returned `REQUEST CHANGES`: P1 metadata cleanup for
  a `.cache` prefix and P2 swallowed projection guidance. Both were fixed with
  projection-root-relative metadata protection, collision regressions, and a
  trusted local projection error category. The second review found a P2
  case-insensitive Windows collision; case-folded protection and regression
  now pass. Final independent review found no P0-P3 issue and returned
  `APPROVED`. No live AtomGit upload ran; remote acceptance remains the only
  uncollected evidence and is not required or authorized for this Issue.
- Human acceptance: the maintainer's explicit request defines and accepts the
  requested default-resume and `--path-in-repo` outcome. Authorized delivery
  remains pending.
