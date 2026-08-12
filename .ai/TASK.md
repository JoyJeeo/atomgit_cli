# Current Issue Contract

Status: `completed`

This is the repository's single persistent handoff for active, multi-turn, or
cross-conversation work. It records task facts and permissions; it does not
authorize work by itself. The current user request and real Git state remain
authoritative.

This is a local Issue contract. It is not backed by, and does not require, a
remote GitHub Issue.

## Handoff Snapshot

- Updated: `2026-08-12 11:47:14 +0800`
- Status: `completed`
- Phase: `bounded LFS preupload failure policy delivered to github/yuto and subsequently verified by an authorized live resumable LFS upload, download, pointer inspection, and no-op resume against cli_demo_dataset`
- Base branch: `yuto`
- Task branch: `codex/bound-lfs-preupload-failures`
- Base commit: `86a26b6084decbde5e0ba38c09bb25b2cd0c921e`
- Task commit: `71f8fdb fix(upload): bound LFS preupload failures`
- Merge commit: `163ef5b merge: bound LFS preupload failures`
- Remote delivery: `github/yuto verified at 6b871fb4c73b09c45f40b4d51ba2d425693cd740 before this live-acceptance record`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit/atomgit_cli`
- Worktree state: `clean and synchronized with github/yuto after this final delivery record is committed and pushed`
- Changed paths: `.ai/TASK.md`, `README.md`, `api.py`, `docs/architecture.md`, `docs/upload_command_analysis.md`, `tests/cli_baseline_contract.py`, `tests/test_auto_configure_lfs.py`, and new `tests/test_lfs_preupload_policy.py`
- Required worktree: `none; the Issue is delivered`
- Last completed action: `performed the newly authorized live validation against weixin_52273949/cli_demo_dataset and proved upload, exact download, canonical pointer, and no-op resume behavior without touching existing repository paths`
- Next exact action: `none; the two queued follow-up Issues remain inactive and require separate explicit activation`
- Blockers: `none; the explicitly authorized cli_demo_dataset live validation is complete; deletion, other repositories, and unrelated remote paths remain outside this delivery`
- Tests run this turn: `pre-fix python tests/test_lfs_preupload_policy.py failed with missing _ResumableLfsPreuploadController; final focused scripts passed: test_lfs_preupload_policy.py 89/89, test_auto_configure_lfs.py 28/28, test_resumable_commit_policy.py 51/51, test_resumable_recovery.py 5/5, test_dataset_resumable_route.py 11/11, test_upload_resumable.py 47/47, test_upload_error_classify.py 42/42, test_hf_api_contract.py 13/13, test_canonical_lfs_pointer.py 24/24, and test_resumable_stats.py; the mandatory python tests/run_cli_baseline.py passed 68/68 after implementation and again after each review fix, with the final run passing in 57.86s; final python -m compileall -q ., python -m pip check, and git diff --check passed; authorized live validation uploaded one 201-byte *.bin through dataset resumable mode to codex-live/lfs-preupload-20260812-1142/probe.bin, advancing remote main from 4b2874c46554f027fc6b14b2a5bf490cd544e249 to 9f06c68be31cc3fa9e0df62cc5eac2d9101fc27c; CLI download-file --verify-checksum and cmp matched SHA-256 d2cc9e5d0f9e091d3d4ae0de946da80300e6ace91227e0fcfa75ce9f2ee6e21f; skip-smudge Git inspection found a canonical 128-byte three-line pointer with the same OID and size 201; repeating the exact upload reported one resume skip, zero new commits, and left remote main unchanged at 9f06c68`
- Tests not run: `the live validation exercised the successful LFS Batch path rather than manufacturing quota, bandwidth, rate-limit, service-failure, or timeout responses against the real service; those failure policies remain covered by offline regressions`

## Active Issue Identity

- ID: `LOCAL-BOUNDED-LFS-PREUPLOAD-FAILURES`
- Title: `Bound and classify resumable LFS preupload failures`
- Primary type: `bug`
- Priority: `P1`
- Delivery mode: `local task branch based on yuto; implementation, tests, review, human acceptance, and Git delivery remain separate phases`
- Observable objective: `a resumable AtomGit upload must never spin indefinitely when the Git LFS Batch API rejects or cannot process an object; terminal failures must stop promptly with an accurate credential-safe category, transient failures must use bounded retries and backoff, and resumable metadata must remain valid for a later retry`
- User impact: `one terminal LFS capacity response was retried 548 times without delay, flooded logs, never returned a semantic CLI failure, and required Ctrl-C even though no retry could succeed`

## Confirmed Root-Cause Evidence

### Remote Capacity Root Cause — Confirmed And Operationally Resolved

- The failing repository was `weixin_52273949/test_datasets`.
- A controlled, single-object, read-only LFS Batch negotiation returned HTTP
  `413` with AtomGit's structured message that current LFS usage was
  `115705728911 B` and the LFS limit was `107374182400 B`.
- This equals `107.76 GiB` used against a `100 GiB` limit, already `7.76 GiB`
  over quota. The original selected upload was `622.50 GiB`; the remaining 600
  files were approximately `522.43 GiB`, so retrying or reducing client batches
  could not make that upload fit.
- The maintainer confirmed on 2026-08-12 that the remote problem was the 100 GB
  LFS capacity ceiling and that upload works normally after switching to
  `weixin_52273949/cli_demo_dataset`.
- Therefore remote capacity is no longer an open root-cause question for this
  incident. It is also not permission for the AI to write to the new repository.

### Client Retry Amplification — Confirmed And Fixed On The Task Branch

- The failure occurs at `HfApi.preupload_lfs_files -> post_lfs_batch_info`,
  before object transfer and before `create_commit`.
- The affected batch's 20 metadata records all had SHA-256 and `upload_mode=lfs`
  but `is_uploaded=0` and `is_committed=0`; `.gitattributes`, regular-blob commit
  size, canonical pointer generation, and commit reconciliation are not the
  failing boundaries.
- AtomGit runtime disables XET, so locked `huggingface-hub==1.1.7` negotiates one
  LFS object per Batch request. A representative request body is approximately
  204 bytes; the 413 was not caused by the CLI's outer 20-file batch.
- In locked HF 1.1.7, `_upload_large_folder._worker_job` catches every exception
  from `_preupload_lfs`, logs it, immediately requeues the same item, and has no
  attempt limit or delay. The parent loop cannot observe a terminal failure.
- The captured run emitted the same 413 548 times before Ctrl-C. This is the
  client defect owned by the current Issue.
- Git LFS Batch protocol assigns 413 to a Batch request that is too large, 507
  to insufficient storage, and 509 to bandwidth quota. AtomGit returned the
  wrong HTTP semantic for this quota case, so the client must recognize both a
  structured AtomGit quota response and protocol-standard capacity responses
  without treating every generic 413 as storage quota.

## Current And Expected Behavior

### Current Behavior

1. HF large-folder selects an LFS item and calls the Batch endpoint.
2. Any exception, including terminal 4xx/quota failures, is swallowed inside
   the worker thread.
3. The same item is immediately requeued with no backoff or maximum attempts.
4. The child process remains alive indefinitely when no overall `--timeout` was
   supplied, so the parent receives neither success nor a structured error.
5. A raw dependency error containing the remote URL is printed once per loop.

### Expected Behavior

1. Each LFS preupload attempt is classified at the preupload atomic boundary.
2. Terminal responses fail once and exit the child promptly through the existing
   bounded, credential-safe worker envelope.
3. Transient responses retry only under an explicit attempt and time budget,
   with backoff and `Retry-After` support.
4. The CLI reports an accurate action: resolve storage quota, wait for rate
   limiting/service recovery, reauthenticate, check permissions/repository, or
   contact support for a generic Batch rejection.
5. SHA-256, upload mode, and previously committed metadata remain reusable;
   unconfirmed objects are never marked uploaded or committed.
6. No token, signed URL, response body, object OID, or local path crosses the
   child-process boundary or appears in ordinary CLI output.

## Detailed Implementation Plan

### 1. Intercept The Correct Atomic Boundary

- Inspect the real locked signatures and implementation of
  `huggingface_hub._upload_large_folder._preupload_lfs`,
  `_upload_large_folder._worker_job`, and `HfApi.preupload_lfs_files` before
  editing.
- Add an AtomGit-only, child-process-scoped preupload controller at the smallest
  seam that can classify the exception before HF's generic worker catches and
  requeues it.
- Prefer wrapping `_preupload_lfs` inside `_run_resumable_upload`, analogous to
  the existing scoped upload-mode and commit controllers. Restore every patched
  dependency global in `finally`.
- Do not modify the installed HF package, change the dependency pin, enable XET,
  replace resumable uploads with ordinary folder uploads, or patch behavior
  outside AtomGit's isolated child process.

### 2. Use Explicit Error Semantics

Add bounded internal categories without carrying raw exception text:

- `lfs_quota`: AtomGit's validated structured capacity response or protocol
  `507`. Terminal, no retry. The hint must state that LFS storage capacity must
  be increased or actually reclaimed by server-side LFS garbage collection.
- `lfs_bandwidth`: protocol `509`. Terminal, no immediate retry; instruct the
  user to wait for/reset the quota or contact platform support.
- `lfs_batch_rejected`: generic `413` or `422` that is not a validated storage
  quota response. Terminal, no retry; do not mislabel it as Git commit size.
- Existing safe categories for `401`, `403`, and `404`: terminal and mapped to
  authentication, permission, and repository failures.
- `rate_limit`: `429`; transient and eligible for bounded retry, honoring a
  valid bounded `Retry-After` value.
- `service_unavailable`: `500`, `502`, `503`, and `504`; transient and eligible
  for bounded retry.
- `timeout` / `connection`: transient and eligible for bounded retry.
- Unknown 4xx and malformed Batch responses: terminal safe failure rather than
  speculative retry.

AtomGit currently reports the storage response as `413`, `error_code_name` of
`UN_KNOW`, and an English `error_message`. Parsing must be narrow:

- accept only a bounded JSON object from an AtomGit LFS response;
- match a stable structured code when the service provides one in the future;
- retain a narrowly tested compatibility match for the current exact semantic
  marker `Insufficient LFS space`;
- never place `error_message`, trace ID, URL, headers, OID, or body in the worker
  envelope;
- treat any nonmatching 413 as `lfs_batch_rejected`, not `lfs_quota`.

### 3. Bound Retry And Waiting

- Use a fixed maximum of three total attempts per preupload atomic call unless
  repository policy selects another value during implementation review.
- For retryable failures, use deterministic exponential backoff before jitter,
  for example 2 seconds then 4 seconds. Inject sleep/jitter in tests.
- Honor only syntactically valid, nonnegative, bounded `Retry-After`; it must not
  exceed the remaining explicit upload deadline or a documented per-wait cap.
- An explicit resumable `--timeout` remains the overall deadline. Retry sleep and
  request time must both respect the remaining deadline.
- Omitting `--timeout` may leave total successful upload duration unlimited, but
  it must never make the attempt count unlimited.
- Emit at most one sanitized status line per retry decision. A terminal failure
  must not be requeued and must not produce a dependency URL flood.

### 4. Fail Through The Existing Child Envelope

- On terminal failure or retry exhaustion, invoke the existing child fatal path
  so the parent receives one validated category and the short-lived process
  exits even though HF's worker loop would otherwise continue.
- Extend the allowlist used by `ResumableWorkerError` and CLI classification for
  the new categories. Unknown categories must continue to collapse to `unknown`.
- Keep payloads bounded and credential-safe. Do not serialize exceptions.
- Ensure queue close/join and process termination remain prompt and do not leave
  worker threads, cached HF sessions, patched functions, timeout globals, or
  progress state alive in the parent.

### 5. Preserve Correct Resume State

- A failed Batch negotiation must leave `is_uploaded=False` and
  `is_committed=False`.
- Preserve SHA-256, file size, safe `upload_mode=lfs`, target identity, and every
  previously committed batch.
- Do not clear LFS upload mode as if this were the existing unsafe-regular-file
  case, and do not invoke `--auto-configure-lfs`.
- When capacity or a transient service problem is resolved, rerunning the same
  command must skip confirmed batches and resume at the first unconfirmed item.
- Ambiguous failures after actual object transfer are a separate state and must
  not be marked uploaded without authoritative HF metadata or remote evidence.

### 6. User-Facing Messages

Required examples, subject to repository style review:

- Quota: `LFS 存储空间不足` with a hint to increase the repository/account LFS
  quota or remove unused objects and complete server-side LFS GC before retrying.
- Generic 413: `LFS 协商请求被拒绝` with a hint that the Batch request was
  rejected and the retained breakpoint can be retried after platform support
  resolves it.
- Retry exhaustion: state the bounded attempt count and that breakpoint metadata
  is preserved.
- Do not reuse `提交过大` / `提交已降至单文件`, because no Git commit was
  attempted in this failure path.

## Required Regression Tests

Add the smallest new focused executable test file and register it in
`tests/cli_baseline_contract.py`. It must fail against current `yuto` before the
implementation and cover at least:

1. Current structured AtomGit 413 capacity response becomes `lfs_quota` after
   one request, with no requeue or sleep.
2. Generic 413 becomes `lfs_batch_rejected`, not quota and not commit size.
3. Protocol 507 becomes `lfs_quota`; 509 becomes `lfs_bandwidth`.
4. 401/403/404 terminate once with existing safe semantic categories.
5. 422 and unknown 4xx terminate once.
6. 429 honors a bounded `Retry-After`, succeeds within the attempt limit, and
   fails safely when exhausted.
7. 500/502/503/504, timeout, and connection failures retry with the exact
   bounded backoff sequence and never exceed three total attempts.
8. An explicit upload deadline truncates waiting and terminates promptly.
9. Terminal child failure reaches the parent as a bounded envelope and exits
   without requiring Ctrl-C.
10. Logs and envelopes contain no fake token, authorization header, signed URL,
    response body, OID, trace ID, or local full path.
11. Failed objects retain SHA-256 and LFS mode but remain unuploaded and
    uncommitted; prior committed items stay committed.
12. A later successful rerun reuses metadata and resumes without hashing or
    submitting confirmed batches again.
13. `--auto-configure-lfs` is not invoked for LFS Batch failures.
14. Model and dataset logical types, revision forwarding, normalized multi-level
    repository IDs, and custom repository prefixes retain existing behavior.
15. Every dependency monkeypatch and process-global setting is restored after
    success and failure.

Run affected existing suites including resumable upload, recovery, commit
policy, error classification, dataset routing, runtime policy, canonical LFS
pointer, CLI surface, and SDK exception tests. Then run:

```text
python tests/run_cli_baseline.py
python -m compileall -q .
python -m pip check
git diff --check
```

The complete baseline must run after every review fix. Inspect locked
`huggingface-hub==1.1.7` and `datasets==4.4.1` callable signatures in the real
`atomgit_cli` conda environment.

## Acceptance Criteria

- The reproduction that currently emits repeated 413 errors exits after one
  terminal quota response without requeueing the item.
- No preupload failure can retry indefinitely, regardless of whether overall
  upload duration is unlimited.
- Only documented transient classes retry, at most three total attempts with
  bounded backoff and deadline enforcement.
- CLI output distinguishes LFS storage quota, bandwidth quota, Batch rejection,
  rate limiting, service unavailability, timeout, connection, authentication,
  permission, and repository failures.
- A quota 413 is not mislabeled as Git commit size, and generic 413 is not
  guessed to be quota.
- Parent and child exit codes are nonzero for terminal failure; no success line
  or completed-batch count is emitted for an unconfirmed item.
- Previously committed work and reusable metadata survive, and the same command
  resumes correctly after the external condition is fixed.
- No credential, URL, response body, OID, trace ID, or local path leaks through
  logs, exceptions, queues, fixtures, or commits.
- Locked dependency behavior outside the AtomGit child context is unchanged.
- Focused tests, affected suites, the complete mandatory baseline, compile,
  dependency, and diff checks all pass in the conda environment.
- A fresh independent no-edit review returns `APPROVED`, then the maintainer
  provides human acceptance before any delivery.

## Out Of Scope

- Increasing, deleting, reclaiming, or automatically managing remote LFS quota.
- Writing to `weixin_52273949/test_datasets`, deleting the retained live fixture,
  or writing outside the authorized unique path in
  `weixin_52273949/cli_demo_dataset` without separate exact authorization.
- Treating a repository switch as a client fix.
- Adding a speculative quota preflight against a nonexistent/undocumented API.
- Changing AtomGit's incorrect server-side 413/`UN_KNOW` response; that belongs
  to the service implementation. The client only provides narrow compatibility.
- Changing HF/datasets pins, enabling XET, replacing resumable upload, changing
  outer 20-file batching, lowering workers, or extending timeouts as a workaround.
- Modifying canonical LFS pointer serialization, automatic `.gitattributes`,
  ordinary upload, download, authentication storage, or Git credential helpers.
- Remote Issue creation, release, publication, or unrelated roadmap work.

## Permissions And Delivery

- Local Issue registration and this `.ai/TASK.md` handoff: `authorized by the maintainer on 2026-08-12`.
- Runtime source, focused tests, and affected human documentation: `authorized for the next implementation conversation by the maintainer's explicit request for subsequent client development`.
- Task branch based on `yuto`: `authorized`; use
  `codex/bound-lfs-preupload-failures`.
- Offline diagnostics, regression tests, full baseline, and independent review:
  `authorized`.
- Live AtomGit read/write validation against
  `weixin_52273949/cli_demo_dataset`: `explicitly authorized by the maintainer on
  2026-08-12 and completed only under codex-live/lfs-preupload-20260812-1142`.
- Local commit, local merge into `yuto`, and push of only `yuto`: `authorized by
  the maintainer's 2026-08-12 request to complete tests, commit, and push`.
- Push of the task branch, PR, remote Issue transition, release, publication,
  service deployment, fixture deletion, other remote paths, and other live
  AtomGit repositories: `not authorized`.
- Task branches remain local-only under standing delivery rules.

## Next-Conversation Recovery Checklist

1. Read `AGENTS.md`, `.ai/README.md`, and this complete Issue contract.
2. Inspect Git root, current branch/HEAD, worktrees, status, recent log, and the
   `.ai/TASK.md` diff. Reconcile against the snapshot before editing.
3. Read `.ai/MASTER_PROMPT.md`, `.ai/DEVELOPMENT_RULES.md`, `.ai/DOD.md`,
   `.ai/TESTING.md`, `.ai/STYLE_GUIDE.md`, `.ai/ARCHITECTURE.md`,
   `.ai/PRODUCT.md`, and `.ai/REVIEW.md` as routed by `.ai/README.md`.
4. Confirm the `atomgit_cli` conda environment and real locked versions and
   signatures.
5. Preserve this uncommitted Issue registration while creating/switching to the
   planned local task branch based on `yuto`.
6. Reproduce the infinite-requeue boundary offline with a failing focused test.
   Do not make a remote request to prove an already confirmed root cause.
7. Implement only the bounded preupload failure policy, run focused and complete
   gates, update this handoff, perform independent review, and request human
   acceptance and separate Git delivery authorization.

## Human Acceptance And Delivery Status

- Issue selection and detailed plan: `accepted through the maintainer's explicit request to record the follow-up local Issue`.
- Implementation: `delivered by task commit 71f8fdb and local merge 163ef5b`.
- Definition of done: `passed: task-scoped implementation and documentation, failing-before-fix regression, focused suites, complete 68-script baseline after every review fix, locked signatures, compileall, pip check, diff check, credential-safety audit, no open review finding, and authorized Git delivery`.
- Independent review: `APPROVED after two review fixes: retry exhaustion now prints its bounded three-attempt limit, and unclassified local resource failures fall back to the existing credential-safe client_resource category; fresh post-fix review found no remaining P0-P3 findings`.
- Human implementation acceptance: `the maintainer explicitly requested end-to-end development, tests, commit, and push; final observable result will be reported after delivery`.
- Delivery: `task commit 71f8fdb merged locally by 163ef5b; github/yuto verified at 163ef5bab01563f0c4864495a26c468ce640699e; task branch remained local-only`.
- Remote root cause: `confirmed as the 100 GB LFS limit and operationally resolved by the maintainer using a repository with available capacity`.
- Live acceptance: `explicitly authorized by the maintainer on 2026-08-12 for read/write operations against weixin_52273949/cli_demo_dataset (git@atomgit.com:weixin_52273949/cli_demo_dataset.git); passed at commit 9f06c68be31cc3fa9e0df62cc5eac2d9101fc27c using only the unique codex-live/lfs-preupload-20260812-1142 path; the test object remains in the repository because no deletion was requested or performed`.

## Queued Follow-Up Issue — Inactive

The following local Issue was registered at the maintainer's request on
`2026-08-12 10:58:43 +0800`. It is intentionally `queued` and `inactive` because
`LOCAL-BOUNDED-LFS-PREUPLOAD-FAILURES` is the single active Issue. Do not
implement, branch for, merge with, or silently expand the active Issue to
include this follow-up. Activate it only after the current Issue is completed,
cancelled, or otherwise made inactive by an explicit maintainer decision.

### Identity And Objective

- ID: `LOCAL-DEFAULT-IGNORE-MACOS-UPLOAD-METADATA`
- Title: `Ignore AppleDouble and .DS_Store files by default during CLI uploads`
- Status: `queued / inactive`
- Primary type: `bug`
- Priority: `P2`
- Proposed task branch: `codex/ignore-macos-upload-metadata`
- Observable objective: `directory uploads through every CLI upload mode must
  exclude macOS AppleDouble files and .DS_Store by default, without requiring
  --ignore, while preserving normal hidden repository files and treating the
  user's --ignore value as additional patterns`.
- User impact: `macOS can create ._* AppleDouble sidecars and .DS_Store files,
  especially on external filesystems; the CLI currently uploads them unless
  every user supplies ignore patterns. A ._name.bag sidecar also matches a
  repository *.bag Git LFS rule and can be committed as a regular blob, causing
  clone/checkout to report that a file should have been an LFS pointer`.

### Reproducible Evidence And Dependency Contract

- A `GIT_LFS_SKIP_SMUDGE=1` clone of the affected dataset repository reported
  23 nested `._*.bag` paths as files that should have been pointers but were
  not. Skip-smudge prevents large object download; it cannot make a regular
  AppleDouble blob satisfy a Git LFS pointer rule.
- The files are macOS AppleDouble metadata sidecars, not the corresponding real
  `.bag` payloads. Their `.bag` suffix causes `*.bag filter=lfs` to match them.
- Locked `huggingface-hub==1.1.7` uses Unix shell-style `fnmatch` matching in
  `filter_repo_objects`. Read-only inspection proved that `._*` covers only the
  upload root and `**/._*` covers nested paths; both are required. The same is
  true for `.DS_Store` and `**/.DS_Store`.
- Current CLI parsing already accepts comma-separated `--ignore` patterns, and
  ordinary upload selection, resumable selection/projection, batching, and CLI
  statistics already converge on `filter_repo_objects` when passed the same
  effective pattern list.

### Expected Default Policy

Define one internal immutable policy in `utils.py`:

```python
DEFAULT_CLI_UPLOAD_IGNORE_PATTERNS = (
    "._*",
    "**/._*",
    ".DS_Store",
    "**/.DS_Store",
)
```

- Apply this policy by default to CLI directory uploads only.
- Merge user patterns after the defaults with stable deduplication. Existing
  `--ignore` semantics become additive rather than the sole ignore source.
- Do not default-ignore `.*`, `**/.*`, or all hidden files; those broad rules
  would incorrectly exclude `.gitattributes`, `.gitignore`, and other intended
  repository content.
- Do not add a public opt-out in this Issue. AppleDouble and `.DS_Store` are
  platform metadata rather than intentional repository payloads. A future
  opt-out would require a separate compatibility decision.

### Detailed Implementation Plan

1. Add `DEFAULT_CLI_UPLOAD_IGNORE_PATTERNS`, a stable-deduplicating
   `effective_cli_upload_ignore_patterns(user_patterns=None)` helper, and an
   `is_macos_metadata_file(path)` basename predicate in `utils.py`.
2. In `cli.upload`, retain a distinct `user_ignore_patterns` value for CLI
   validation and user-facing reporting. Merge defaults only after the input is
   known to be a directory. Do not pass a nonempty default list into the current
   single-file `--ignore` conflict check, because that would incorrectly route
   or reject every normal single-file upload.
3. If the explicitly selected single file has basename `.DS_Store` or begins
   with `._`, reject it before authentication or any remote call with a concise
   nonzero result. Do not silently print upload success when nothing was sent.
4. Pass the effective directory patterns consistently to
   `get_upload_file_stats`, `_collect_resumable_upload_files`, ordinary
   `upload_folder`, resumable projection synchronization,
   `_prefix_resumable_ignore_patterns`, and `upload_large_folder`.
5. Preserve the current resumable projection cleanup behavior: files absent
   from the newly filtered `desired_paths` set must be removed from an existing
   projection while HF resume metadata under `.cache/huggingface` remains.
6. Keep model/dataset routing, revision, repository normalization,
   `path_in_repo`, batching, LFS pointer canonicalization, user-provided ignore
   patterns, and SDK behavior otherwise unchanged.
7. Update CLI help and output to distinguish `default macOS metadata ignores`
   from `additional user ignore patterns`; do not represent internal defaults
   as if the user supplied them.

### CLI Versus SDK Boundary

- The requested contract is explicitly for CLI uploads. The public
  `atomgit_hub.upload_folder(ignore_patterns=...)` SDK parameter must retain its
  current caller-controlled semantics unless the maintainer separately
  authorizes an SDK compatibility change.
- Shared low-level API helpers must therefore receive an explicit effective
  pattern list from the CLI rather than silently imposing CLI policy on every
  SDK caller.
- Direct SDK upload of these metadata files remains a documented residual risk
  unless a later Issue intentionally aligns SDK defaults.

### Required Regression Tests

Prefer extending existing registered scripts rather than adding a new test
file solely for this behavior:

1. `tests/test_upload_ignore.py`: without `--ignore`, CLI directory upload uses
   the four default rules; user patterns are appended and stably deduplicated.
2. Prove root and nested `._*` plus root and nested `.DS_Store` are excluded,
   while `normal.bag`, `.gitattributes`, `.gitignore`, and ordinary dotfiles are
   retained.
3. Direct single-file upload of `._file.bag` or `.DS_Store` exits nonzero and
   never calls the API; an ordinary single-file upload remains unchanged.
4. CLI displayed file count and byte size exclude default-ignored metadata.
5. `tests/test_upload_resumable.py`: default and prefixed projections exclude
   the metadata, correctly prefix dependency patterns, remove stale sidecars
   from a reused projection, and preserve HF resume metadata.
6. `tests/test_upload_batching.py`: default-ignored files never enter ordinary
   or resumable 20-file batch counts, and both modes select the same payload
   set.
7. Preserve existing explicit `--ignore`, `--path-in-repo`, model/dataset,
   revision, canonical LFS pointer, and dependency-signature coverage.

After implementation and every review fix, run in the `atomgit_cli` conda
environment:

```text
python tests/test_upload_ignore.py
python tests/test_upload_resumable.py
python tests/test_upload_batching.py
python tests/run_cli_baseline.py
python -m compileall -q .
python -m pip check
git diff --check
```

### Acceptance Criteria

- A CLI directory upload with no `--ignore` excludes AppleDouble and
  `.DS_Store` at the upload root and at arbitrary nested depths in ordinary and
  resumable modes.
- User `--ignore` patterns remain supported and are applied in addition to the
  defaults without duplicate or order-dependent behavior.
- CLI pre-upload statistics, batch plans, projections, and actual HF calls
  agree on the selected file set.
- Normal `.bag` files and intentional hidden files such as `.gitattributes` and
  `.gitignore` remain uploadable.
- Explicit single-file selection of AppleDouble or `.DS_Store` fails clearly
  before authentication or a remote call; normal single-file upload is
  unchanged.
- Reusing an existing resumable projection removes now-ignored sidecars without
  deleting HF resume metadata or confirmed upload state for valid files.
- No public CLI parameter is added or removed, locked dependency pins remain
  unchanged, and SDK caller-controlled ignore behavior is unchanged.
- Focused tests, the complete mandatory baseline, compile, dependency, and diff
  checks pass; independent review returns `APPROVED`; human acceptance precedes
  any delivery.

### Documentation Plan

- Update `README.md` upload documentation and examples to state the default
  exclusions and additive `--ignore` behavior.
- Update `docs/cli_feature_baseline.md` so the default exclusion is a protected
  CLI compatibility contract.
- Update `docs/upload_command_analysis.md` with merge order, matching details,
  statistics/projection behavior, and the CLI/SDK boundary.
- Update `.ai/PRODUCT.md` with the eventual product contract only when runtime
  implementation and tests make the statement true.

### Out Of Scope And Permissions

- Existing remote AppleDouble and `.DS_Store` blobs are not deleted or repaired
  by this client change. Cleaning a branch tip is a separate remote write task;
  history rewriting is separately out of scope.
- Do not alter `.gitattributes`, canonical LFS pointer serialization, LFS
  objects, download behavior, remote repository contents, dependencies, or the
  SDK default in this Issue.
- Local registration of this queued Issue in `.ai/TASK.md`: `authorized by the
  maintainer on 2026-08-12`.
- Implementation, task-branch creation, tests that write repository files,
  local commit, merge, push, PR, remote Issue transition, live AtomGit
  operations, release, and publication: `not authorized by this registration;
  require activation and the applicable explicit permissions`.

## Queued Follow-Up Issue — Configurable Upload Batch Size — Inactive

This additional local Issue was registered at the maintainer's request on
`2026-08-12 11:00:38 +0800`. It is `queued / inactive`; it must not displace or
expand the single active `LOCAL-BOUNDED-LFS-PREUPLOAD-FAILURES` Issue, and it is
independent from the queued macOS metadata-ignore Issue. Activate and implement
only after the active Issue is completed, cancelled, or made inactive by an
explicit maintainer decision.

### Identity And Objective

- ID: `LOCAL-CONFIGURABLE-UPLOAD-BATCH-SIZE`
- Title: `Make CLI directory-upload batch size configurable`
- Status: `queued / inactive`
- Primary type: `cli`
- Priority: `P2`
- Proposed task branch: `codex/configurable-upload-batch-size`
- Observable objective: `atomgit upload must let a user select the maximum
  number of directory files processed by each outer upload batch, including 2
  or 10 files per batch, while retaining 20 as the default when the option is
  omitted`.
- User impact: `the current hard-coded group size of 20 prevents users from
  reducing the amount of work and failure scope in each ordinary or resumable
  directory-upload batch without changing source code`.

### Confirmed Current Boundary

- `api.HuggingFaceAPI.upload_directory` currently slices the deterministically
  selected files with `range(0, len(selected_files), 20)` and prints
  `每批最多 20 个文件` through `_print_upload_batch_plan`.
- The same outer `batches` collection drives both ordinary `upload_folder`
  calls and resumable `upload_large_folder` projections, so one parameter can
  consistently control both CLI directory modes.
- This outer file count is not `--num-workers`: workers control concurrency
  inside the upload implementation, while batch size controls how many selected
  source files belong to one parent-planned group.
- It is also distinct from `_RESUMABLE_COMMIT_BATCH_SIZES` and
  `_next_resumable_commit_batch_size`, which reduce commit-operation groups
  after specific remote commit failures. This Issue must not conflate or replace
  that recovery policy.

### Public CLI Contract

Add the following option to `atomgit upload`:

```text
--batch-size INTEGER RANGE
    Maximum files per directory-upload batch. Default: 20.
```

- Public Python name: `batch_size` or the more explicit internal name
  `max_files_per_batch`; select one consistently during implementation review.
- Click type: `click.IntRange(min=1, max=20)` with `default=20` and
  `show_default=True`.
- Required examples:

  ```text
  atomgit upload DIR --repo-id OWNER/REPO --batch-size 2
  atomgit upload DIR --repo-id OWNER/REPO --batch-size 10
  atomgit upload DIR --repo-id OWNER/REPO
  ```

  The last command must remain exactly equivalent to batches of at most 20.
- The initial supported range is 1 through 20. The request requires smaller
  batches while preserving 20 as the current safety ceiling; allowing values
  above 20 would change established load and failure-size assumptions and
  requires separate evidence and authorization.
- The option applies only to directory uploads. Normal single-file upload keeps
  its existing direct path. An explicitly supplied value on a single-file
  command may be rejected as a usage error if Click parameter-source inspection
  is implemented reliably; otherwise the documented option can be accepted but
  have no effect on the inherently one-file operation. The implementation must
  choose and test one clear behavior rather than silently diverging by code
  path.
- Zero, negative values, non-integers, and values above 20 must fail with Click
  exit code 2 before authentication or any remote call.

### Detailed Implementation Plan

1. Define a single internal default such as
   `DEFAULT_UPLOAD_BATCH_SIZE = 20`; do not retain independent numeric literals
   in CLI defaults, slicing, output, tests, and documentation.
2. Add `--batch-size` to `cli.upload`, pass its validated value only to the
   directory path, display the chosen maximum with the directory upload plan,
   and preserve all existing `--num-workers`, `--timeout`, `--ignore`,
   `--path-in-repo`, `--repo-type`, `--revision`, and resumable mode behavior.
3. Extend `HuggingFaceAPI.upload_directory` with a backward-compatible defaulted
   parameter. Validate it defensively at the API boundary as a real integer,
   excluding booleans, within 1..20, because tests and internal callers can
   bypass Click.
4. Replace hard-coded slicing with the validated value:

   ```python
   batches = [
       selected_files[index:index + batch_size]
       for index in range(0, len(selected_files), batch_size)
   ] or [[]]
   ```

5. Change `_print_upload_batch_plan` to receive the configured maximum and
   print the actual value instead of a hard-coded 20. Batch start, success,
   failure, summary, submitted, skipped, and completed counts must remain
   derived from the real groups.
6. For resumable uploads, include the configured maximum in the projection
   identity/batch key, for example `batch-2-0`, `batch-10-0`, or an equivalent
   collision-safe representation. Switching an existing source/repository from
   20 to 2 or 10 must not reuse incompatible per-batch HF metadata from a
   previous grouping. Repeating the same value must continue to reuse the same
   stable projection and resume metadata.
7. Do not forward this outer grouping value as an invented argument to locked
   `HfApi.upload_large_folder` or `upload_folder`; neither dependency signature
   owns this CLI orchestration setting.
8. Keep deterministic file ordering and apply ignore filtering before slicing,
   so the configured size counts only actual selected upload files. When the
   queued macOS metadata-ignore Issue is later implemented, its excluded files
   must likewise not consume batch slots.
9. Do not change outer batch size automatically in response to LFS quota,
   authentication, permission, or preupload failures. User configuration and
   the separate bounded-failure Issue have different responsibilities.

### Compatibility And State Decisions

- Omitting `--batch-size` preserves the current public behavior and output
  meaning: no more than 20 selected files per outer batch.
- Values 1, 2, 10, and 20 must behave identically across ordinary and resumable
  directory modes apart from the expected number of groups and commits/calls.
- Existing direct Python callers of `api.upload_directory` remain compatible
  because the new parameter is optional and defaulted.
- The public `atomgit_hub.upload_folder` SDK is out of scope: it does not use
  the CLI's outer 20-file batching controller, so this Issue must not add a
  misleading SDK parameter.
- A different batch size can change how many remote upload calls or commits are
  produced; documentation and CLI output must state this operational effect.
- Old projections are not destructively deleted. Incorporating the configured
  value into projection identity isolates them; existing `atomgit cache clear`
  remains the explicit cleanup mechanism.

### Required Regression Tests

1. Update `tests/cli_baseline_contract.py` with the exact new public option
   schema, including default, range, and help exposure.
2. Extend `tests/test_cli_feature_baseline.py` to prove CLI dispatch forwards
   the configured value and omission forwards/defaults to 20.
3. Extend `tests/test_upload_batching.py` to cover selected file counts that
   cross boundaries for 1, 2, 10, and 20; verify exact number, order, and content
   of ordinary and resumable groups.
4. Prove 21 selected files produce 2 batches by default, 11 batches with size 2,
   and 3 batches with size 10; the final partial batch must contain only the
   remainder.
5. Verify zero, negative, non-integer, and greater-than-20 CLI inputs exit 2 and
   cause no authentication or remote call; direct API invalid values return the
   established safe failure result before dependency invocation.
6. Update upload progress/output tests so the plan reports the configured
   maximum and all cumulative counts remain accurate on success and mid-plan
   failure.
7. For resumable mode, prove the same size reuses the projection and metadata,
   while changing 20 to 2 or 10 selects a distinct projection identity without
   corrupting either state set.
8. Cover `--batch-size` with `--ignore`, `--path-in-repo`, model/dataset,
   revision, workers, timeout, and both `--resumable` and `--no-resumable`.
9. Bind all HF calls to locked `huggingface-hub==1.1.7` signatures and prove the
   new orchestration parameter is not forwarded to dependency methods.

After implementation and every review fix, run in the `atomgit_cli` conda
environment:

```text
python tests/test_upload_batching.py
python tests/test_upload_progress.py
python tests/test_upload_validation.py
python tests/test_upload_resumable.py
python tests/test_cli_feature_baseline.py
python tests/test_cli_baseline_guard.py
python tests/test_hf_api_contract.py
python tests/run_cli_baseline.py
python -m compileall -q .
python -m pip check
git diff --check
```

### Acceptance Criteria

- `--batch-size 2` and `--batch-size 10` produce outer batches containing at
  most the requested number of selected directory files in both ordinary and
  resumable modes.
- Omitting the option produces the existing maximum of 20.
- Invalid values fail locally with no authentication, projection creation,
  child process, or remote call.
- Plan and lifecycle output shows the configured maximum, exact batch count,
  final remainder, and correct cumulative completion/failure totals.
- Ignore filtering and deterministic ordering occur before batching; no
  excluded file consumes a slot.
- Repeated runs with the same configuration reuse valid resumable state;
  changing batch size cannot bind a new group to incompatible old batch
  metadata.
- Worker concurrency and internal commit-reduction behavior remain independent
  and unchanged.
- The CLI schema, help, implementation documentation, focused regressions,
  complete baseline, compile, dependency, and diff checks pass; independent
  review returns `APPROVED`; human acceptance precedes delivery.

### Documentation Plan

- Update `README.md` upload options and examples with default 20 and examples
  for 2 and 10.
- Update `docs/cli_feature_baseline.md` with the exact public option and backward
  compatibility default.
- Update `docs/upload_command_analysis.md` to distinguish outer batch size,
  worker concurrency, HF large-folder behavior, and internal commit reduction.
- Update `.ai/PRODUCT.md` and `.ai/ARCHITECTURE.md` only when implementation and
  tests make the configurable contract true.

### Out Of Scope And Permissions

- Do not change worker defaults, retry counts, internal commit-reduction sizes,
  LFS classification, canonical pointer handling, default ignore policy,
  dependencies, SDK surface, or remote repository contents in this Issue.
- Local registration of this queued Issue in `.ai/TASK.md`: `authorized by the
  maintainer on 2026-08-12`.
- Implementation, task-branch creation, tests that modify repository files,
  commit, merge, push, PR, remote Issue transition, live AtomGit operations,
  release, and publication: `not authorized by this registration; require
  activation and the applicable explicit permissions`.
