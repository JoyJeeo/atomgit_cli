# Current Issue Contract

Status: `completed`

This is the repository's single persistent handoff for active, multi-turn, or
cross-conversation work. It records task facts and permissions; it does not
authorize work by itself. The current user request and real Git state remain
authoritative.

The completed implementation corresponds to the still-open GitHub Issue #22:
`https://github.com/JoyJeeo/atomgit_cli/issues/22`.

## Handoff Snapshot

- Updated: `2026-08-10 +0800`
- Status: `completed`
- Phase: `delivered to github/yuto; remote Issue remains open pending explicit transition authorization`
- Base branch: `yuto`
- Task branch: `codex/issue-22-upload-batch-lifecycle-logs`
- Base commit: `f7ba22f`
- Task commit: `6af29c8 feat(upload): add batch lifecycle logs`
- Merge commit: `4f1ae52 merge: add upload batch lifecycle logs`
- Current feature HEAD: `4f1ae52`
- Remote delivery: `github/yuto verified at 4f1ae52d4a8f59d0ed7cff7505718da9b073994d`
- Worktree state: `clean and synchronized with github/yuto after this delivery record is committed and pushed`
- Changed paths: `.ai/TASK.md`, `api.py`, `docs/upload_command_analysis.md`, `tests/test_resumable_commit_policy.py`, `tests/test_upload_batching.py`, `tests/test_upload_progress.py`
- Required worktree: `none; implementation is delivered`
- Last completed action: `committed the local task branch, merged it into yuto, pushed only yuto, and verified the remote feature merge hash`
- Next exact action: `none for implementation; close or otherwise transition GitHub Issue #22 only after explicit user authorization`
- Blockers / open questions: `none`
- Tests passed: `final offline: python tests/test_upload_progress.py (28/28); python tests/test_upload_resumable.py (46/46); python tests/test_upload_batching.py (8/8); python tests/test_resumable_commit_policy.py (43/43); python tests/run_cli_baseline.py (65/65 isolated pytest cases, 55.95s); python tests/test_hf_api_contract.py (13/13); python -m compileall -q .; python -m pip check (no broken requirements); git diff --check`
- Tests failed or not run: `pre-implementation regressions failed as expected for missing lifecycle output and event_callback; no live AtomGit write was run or authorized`

## Active Issue Identity

- ID: `GH-22`
- Title: `Add observable batch lifecycle logs for directory uploads`
- Primary type: `cli`
- Priority: `P2`
- User impact: `users cannot see the planned batch count, determine whether the previous batch committed, or identify when processing advances to the next batch`
- Affected path: `cli.upload -> HuggingFaceAPI.upload_directory -> outer 20-file batch loop -> child _run_resumable_upload -> HfApi.upload_large_folder -> _ResumableCommitController`
- Delivery mode: `standing local task-branch delivery into yuto after implementation, review, and human acceptance`
- Permissions: `Issue creation=yes; local task branch=yes; local edits=yes; offline tests=yes; commit=yes; merge into yuto=yes; push yuto=yes; live AtomGit writes=no; task-branch push=no; PR=no; Issue transition=no; release=no`

## Objective And Evidence

- Current behavior: the CLI prints selected file count and size, but the outer 20-file loop has no batch lifecycle logs. HF progress belongs to the current child process and can reset between batches.
- Example: 700 selected files imply 35 planned outer batches, but this plan and the boundary between successful commits are not visible.
- Objective: add deterministic batch lifecycle reporting without changing upload, retry, reconciliation, reduction, or resumable metadata semantics.

## Scope And Acceptance

- Print total selected files, planned outer batches, and maximum files per batch before upload.
- Print ordered outer-batch start, success, resumed-skip, failure, and cumulative progress events.
- Do not announce batch `N+1` until batch `N` is confirmed complete.
- Identify retry, rate-limit waiting, ambiguous remote reconciliation, and `20 -> 10 -> 5 -> 2 -> 1` reduction against the correct outer batch.
- Mark an outer batch successful only after all reduced child groups succeed or remote reconciliation confirms the operations.
- Report already completed resumable content as skipped, not as a new commit.
- On failure, report the failed batch, confirmed cumulative completion, remaining work, and retained checkpoint guidance.
- Print a final internally consistent summary of planned, newly submitted, skipped, and completed work.
- Keep lifecycle logs visible with `--no-progress-bar` and exclude credentials or sensitive request data.

## Compatibility And Non-Goals

- Preserve Python 3.9, `huggingface-hub==1.1.7`, and `datasets==4.4.1`.
- Preserve the outer maximum of 20, retries, backoff, timeout, reconciliation, metadata, model/dataset routing, path prefix, ignore, workers, SDK results, and CLI exit codes.
- Do not add a public CLI option, per-file verbose logging, dependency upgrade, live upload, unrelated refactor, release, or remote Issue transition.

## Required Verification

- Add focused offline tests for 21-file and 700-file plans.
- Verify `batch N success -> batch N+1 start` ordering.
- Verify reduction, reconciliation, resumable skip, terminal failure, and final summary output.
- Verify lifecycle output with progress enabled and `--no-progress-bar`.
- Run existing upload batching and resumable commit-policy tests.
- Run `python tests/run_cli_baseline.py`, `python -m compileall -q .`, `python -m pip check`, and `git diff --check`.
- Apply `.ai/DOD.md` and perform the independent review in `.ai/REVIEW.md` before human acceptance.

## Closure

- Status: `completed and delivered`
- Human acceptance: `accepted by explicit user instruction on 2026-08-10`
- Independent review: `APPROVED after resolving deterministic output flushing, full outer-batch event attribution coverage, preserved remote validation for fully skipped batches, and non-fatal metadata observation findings`
- Delivery: `task commit 6af29c8 merged by 4f1ae52; github/yuto feature merge verified at 4f1ae52d4a8f59d0ed7cff7505718da9b073994d`
- Remote Issue: `GitHub #22 remains open because Issue transition was not authorized`
- Live verification: `not run; no live AtomGit write was authorized`
