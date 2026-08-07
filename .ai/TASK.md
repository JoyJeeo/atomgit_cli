# Current Issue Contract

# Issue UNICODE-DOWNLOAD-METADATA

Status: `ready-for-delivery`

## Identity

- Local Issue: `UNICODE-DOWNLOAD-METADATA`
- Title: `Support checksum metadata for nested non-ASCII download paths`
- Type: `bug`, `cli`, `download`
- Priority: `P1`
- Branch: `codex/fix-unicode-download-paths` (local only)
- Base: `yuto`
- Previous Issue: `PRIVATE-EXIST-OK-VERIFY`, delivered by `b7f5afe`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

Plain downloads already work around AtomGit resolve routing for nested
non-ASCII filenames by retrying a 404 with raw UTF-8 request-target bytes.
Checksum and resumable downloads first call locked HF metadata lookup with the
percent-encoded resolve URL and have no equivalent fallback. On the authorized
dataset test path `sub/中文样本.csv`, that metadata request can fail before the
working raw transfer path is reached.

The existing `--verify-checksum` and `--resume` options must work for every safe
repository filename returned by the listing endpoint, including nested
non-ASCII paths. Metadata fallback must preserve strong-checksum validation,
bounded redirects, credential isolation, and the existing atomic destination
rules.

## Scope And Acceptance

- Reproduce the metadata failure on the fixed authorized read-only test path
  and in a strict offline regression.
- Add one shared metadata lookup path that tries the standard locked HF request
  first and uses raw UTF-8 request-target bytes only for a non-ASCII 404.
- Extract and validate the same ETag, size, and final location needed by
  checksum and resume flows; accept no weaker checksum or ambiguous response.
- Preserve redirect credential stripping, HTTPS downgrade rejection, bounded
  response handling, timeout behavior, destination containment, atomic writes,
  and cache isolation.
- Cover model/dataset URL selection, nested Unicode paths, authenticated and
  anonymous calls, error behavior, checksum download, and resumable download.
- Update only the authoritative download documentation affected by the fix.
- Do not add commands, flags, capabilities, or fix another audited defect.

## Compatibility And Risks

- Keep `huggingface-hub==1.1.7` and `datasets==4.4.1` compatibility; standard
  ASCII metadata requests must continue through locked `get_hf_file_metadata`.
- Raw metadata handling is an AtomGit interoperability fallback, not a generic
  replacement for HF metadata behavior, and must be limited to non-ASCII 404s.
- Live testing is read-only and limited to `weixin_52273949/test_model` and
  `weixin_52273949/test_datasets`; no remote mutation is needed or allowed.

## Permissions

- The user authorized issue-by-issue fixes for confirmed CLI defects and
  excluded new functionality.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- Read-only live download tests may use only the two fixed test repositories.
  No create, upload, branch, visibility, delete, credential-helper mutation,
  release, publication, or other remote write is authorized.

## Required Evidence And Closure

- [x] Existing live and offline behavior reproduces the failure.
- [x] Checksum metadata succeeds for nested non-ASCII paths without weakening
      validation or credential boundaries.
- [x] `--verify-checksum` and `--resume` both use the corrected metadata path.
- [x] ASCII, model/dataset, anonymous/authenticated, redirect, and failure
      compatibility remain covered.
- [x] Focused and complete offline tests, compileall, pip, and diff checks pass.
- [x] Scoped read-only live evidence passes without changing remote state.
- [x] Documentation, credential scan, scope audit, and independent review pass.
- [x] Human acceptance is covered by the standing ordered-fix authorization.
- [ ] The task is committed, merged into `yuto`, and only `yuto` is pushed.

## Verification Evidence

- Live reproduction before implementation: the fixed authorized dataset path
  `sub/中文样本.csv` failed under `download-file --force --verify-checksum`
  with a sanitized not-found result and produced no local file; login identity
  was verified without exposing the stored token.
- Regression before implementation: the strict Unicode metadata script passed
  only `2/5`; checksum fallback, raw UTF-8 request bytes, and redirect credential
  stripping were absent from the metadata path.
- Implementation: standard ASCII and successful encoded metadata keep using
  locked HF `get_hf_file_metadata`; only a non-ASCII encoded 404 retries through
  bounded raw UTF-8 HEAD. Strong ETag/size validation is shared, conflicting
  sizes fail closed, redirects reuse the existing downgrade and credential
  isolation policy, and checksum/resume consume the same metadata result.
- Focused offline evidence: Unicode metadata `9/9`, checksum `23/23`, resume
  `17/17`, download contract `45/45`, redirect security `9/9`, path security
  `15/15`, and locked HF contract `12/12` passed.
- Complete offline suite: `pytest` collected `54` items and exited `0`.
  `python -m compileall -q .`, `python -m pip check`, and `git diff --check`
  passed in the `atomgit_cli` environment.
- Live read-only evidence after implementation: both `--verify-checksum` and
  `--resume` downloaded the authorized dataset Unicode path, independently
  verified the 31-byte result, and produced identical bytes. Temporary local
  files were removed and no remote state changed.
- Security and scope: the diff contains no real credential or generated
  artifact; signed locations are neither printed nor persisted; changes are
  limited to this download defect, its regression, and authoritative docs.
- Independent review: first pass `REQUEST CHANGES` for missing anonymous model
  test evidence; after adding it and rerunning the complete suite, final verdict
  `APPROVED` with no P0-P3 findings.
