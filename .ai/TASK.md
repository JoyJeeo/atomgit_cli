# Current Issue Contract

Status: `active`

This is the repository's single persistent handoff for active, multi-turn, or
cross-conversation work. It records task facts and permissions; it does not
authorize work by itself. The current user request and real Git state remain
authoritative.

This is a local Issue contract. It is not backed by, and does not require, a
remote GitHub Issue.

## Handoff Snapshot

- Updated: `2026-08-11 +0800`
- Status: `active`
- Phase: `implementation, required offline verification, DoD audit, and independent review complete; ready for authorized commit and delivery`
- Base branch: `yuto`
- Task branch: `codex/resumable-existing-repo`
- Base commit: `16600c2`
- Current HEAD: `16600c2`
- Worktree state: `dirty with authorized implementation, tests, documentation, and TASK.md evidence`
- Changed paths: `.ai/TASK.md`, `api.py`, `README.md`, `docs/faq.md`, `docs/testing.md`, `docs/upload_command_analysis.md`, `tests/test_dataset_resumable_route.py`, `tests/test_hf_api_contract.py`, `tests/test_resumable_commit_policy.py`, `tests/test_resumable_recovery.py`, `tests/test_upload_batching.py`, `tests/test_upload_error_classify.py`, `tests/test_upload_resumable.py`
- Required worktree: `continue in this same worktree while implementation is uncommitted`
- Last completed action: `resolved the review findings for total-timeout accounting and non-recursive target validation; fresh mandatory verification and independent review passed`
- Next exact action: `create the authorized cohesive task commit, merge it locally into yuto, push only yuto, and verify github/yuto`
- Blockers / open questions: `none`
- Decisions constraining the next action: `the upload target must pre-exist; resumable upload must not require namespace repository-creation permission; keep locked dependency versions and preserve existing resumable metadata`
- Tests passed: `offline in atomgit_cli: test_upload_resumable.py 47/47; test_upload_batching.py 9/9; test_upload_progress.py 28/28; test_resumable_commit_policy.py 51/51; test_upload_error_classify.py 41/41; test_hf_api_contract.py 14/14; test_resumable_recovery.py 5/5; test_dataset_resumable_route.py 9/9; final python tests/run_cli_baseline.py 65/65 isolated pytest cases in 49.01s; python -m compileall -q .; python -m pip check (no broken requirements); git diff --check`
- Tests failed or not run: `new regressions failed against the pre-fix implementation as expected for missing target validation, unsafe regular-file policy, targeted metadata refresh, and structured worker errors; no live AtomGit write was run or authorized`

## Active Issue Identity

- ID: `LOCAL-RESUMABLE-EXISTING-REPO`
- Title: `Harden resumable uploads for existing organization repositories`
- Primary type: `bug`
- Priority: `P1`
- User impact: `directory upload is unusable for an existing writable organization repository when the token cannot create repositories in that namespace; related child failures are reported only as unknown errors`
- Affected path: `cli.upload -> HuggingFaceAPI.upload_directory -> _run_resumable_upload -> HfApi.upload_large_folder -> implicit HfApi.create_repo -> metadata recovery / upload-mode / commit workers`
- Base branch: `yuto`
- Delivery mode: `standing local task-branch delivery into yuto after implementation, review, and verification`
- Permissions: `local Issue registration=yes; source/test/human-doc edits=yes; task branch=yes; offline tests=yes; commit=yes; merge into yuto=yes; push yuto=yes; task-branch push=no; PR=no; live AtomGit writes=no; remote Issue transition=no; release=no`

## Evidence And Objective

- A 0-byte single-file CLI upload to the existing organization repository succeeded with the current token.
- A 711,256,710-byte `.bag` single-file CLI upload succeeded and the remote Git object is a valid LFS pointer with the expected size.
- The same repository's resumable directory upload fails immediately after outer batch start and before `Recovering from metadata files`.
- Locked `huggingface-hub==1.1.7` calls `create_repo(exist_ok=True)` before metadata recovery in `upload_large_folder`; write access to an existing organization repository does not imply namespace repository-creation permission.
- A separate personal-repository probe reached metadata recovery but classified GiB-scale `.bag` files as `regular`, then failed during commit; cached metadata records the unsafe mode.
- Current child-process error transport flattens structured causes into a generic runtime error, producing `[unknown error]` guidance.
- Objective: make resumable upload operate safely against pre-existing repositories without implicit creation, reject unsafe oversized regular-file commits before reading content, preserve resumable state, and report actionable credential-safe failures.

## Scope And Acceptance

- Treat upload targets as pre-existing; explicit `atomgit repo create` remains the only repository-creation workflow.
- Perform one non-mutating target repository/revision validation before starting resumable batches.
- Prevent locked HF large-folder startup from sending its implicit repository-creation request while retaining later preupload and commit authorization checks.
- Preserve remote validation for fully skipped resumable content.
- Reject oversized files classified as `regular` before file reads, Base64 encoding, commit, retry, reconciliation, or batch reduction; give an actionable `.gitattributes` LFS hint.
- Refresh only unsafe, uncommitted cached upload-mode fields after repository LFS policy changes; preserve hashes and committed state.
- Carry bounded structured error categories across the child-process boundary for authentication, permission, repository/revision absence, payload size, rate limit, service availability, timeout, connection, upload mode, and client resource failures.
- Preserve ordered outer-batch lifecycle reporting, resumable checkpoint guidance, final summaries, CLI exit behavior, and credential redaction.

## Compatibility And Non-Goals

- Preserve Python 3.9 compatibility, `huggingface-hub==1.1.7`, and `datasets==4.4.1`.
- Preserve default resumable directory routing, outer maximum batch size 20, worker default 5, retries, reconciliation, reduction, path prefixes, ignore patterns, model/dataset compatibility routing, single-file upload, normal directory upload, and public SDK signatures.
- Do not add a public CLI option, silently force server-selected `regular` operations to LFS, automatically modify remote `.gitattributes`, clear the whole upload cache, upgrade dependencies, or perform unrelated refactoring.
- Do not run live uploads, repository creation/deletion, push, release, or remote Issue transitions without separate exact authorization.

## Required Verification

- Add a regression proving an existing organization repository can enter metadata recovery without a remote create request.
- Verify nonexistent repositories fail before hashing and are not implicitly created.
- Verify fully skipped content still performs one read-only target validation.
- Verify oversized `regular` operations fail before reading content and do not enter retry, reconciliation, or reduction; verify large LFS and safe small regular operations remain supported.
- Verify unsafe uncommitted metadata refresh preserves SHA-256 and committed metadata is untouched.
- Verify structured child failures produce correct actionable categories without credentials, raw response bodies, signed URLs, or full sensitive paths.
- Run affected upload resumable, batching, progress, commit-policy, error classification, and locked HF contract tests.
- Run `python tests/run_cli_baseline.py`, `python -m compileall -q .`, `python -m pip check`, and `git diff --check` in the `atomgit_cli` conda environment.
- Apply `.ai/DOD.md` and perform the independent review in `.ai/REVIEW.md` before human acceptance.

## Administrative Note

- GitHub Issue #23 was created on `2026-08-11` due to a mistaken interpretation of "register Issue". It was permanently deleted the same day after explicit user authorization; the deleted page was verified on GitHub.
- The local Issue contract in this file remains the sole task authority, and no code work was started from the mistaken remote Issue.

## Delivery Status

- Definition of done: `passed; final diff is task-scoped, required offline checks pass, locked signatures were inspected, documentation agrees, and no credential or generated-artifact finding remains`
- Independent review: `APPROVED after resolving P1 total-timeout accounting and P2 recursive target-enumeration findings; no open P0/P1/P2 finding`
- Human authorization: `the maintainer explicitly requested the full development, testing, commit, local merge, and push workflow on 2026-08-11`
- Live verification: `not run; this task did not authorize a live AtomGit upload or repository mutation`
