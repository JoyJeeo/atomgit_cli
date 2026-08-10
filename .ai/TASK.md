# Current Issue Contract

Status: `active`

This is the repository's single persistent handoff for active, multi-turn, or
cross-conversation work. It records task facts and permissions; it does not
authorize work by itself. When inactive, the current user request and real Git
state determine what may happen next.

The active remote Issue is GitHub #21:
`https://github.com/JoyJeeo/atomgit_cli/issues/21`.

## Handoff Snapshot

- Updated: `2026-08-10 +0800`
- Status: `active`
- Phase: `human accepted; authorized local commit, merge into yuto, and push yuto`
- Base branch: `yuto`
- Task branch: `codex/issue-21-resumable-commit-retries`
- Base commit: `3b86179`
- Current HEAD: `3b86179`
- Worktree state: `modified; preserves the uncommitted upload follow-up implementation on which Issue #21 depends`
- Changed paths: `.ai/TASK.md`, `api.py`, `cli.py`, `utils.py`, `README.md`, `docs/architecture.md`, `docs/faq.md`, `docs/upload_command_analysis.md`, `tests/cli_baseline_contract.py`, `tests/test_upload_ignore.py`, `tests/test_upload_validation.py`, `tests/test_cache_clear.py`, `tests/test_resumable_commit_policy.py`, `tests/test_upload_batching.py`
- Required worktree: `continue in this same worktree; preserve all existing task-related changes`
- Last completed action: `completed implementation, final offline verification, and independent review with APPROVED verdict`
- Next exact action: `commit the task branch, merge it locally into yuto, push only yuto, and record delivery evidence; do not close the remote Issue or run a live upload`
- Blockers / open questions: `no implementation blocker; live AtomGit verification is not authorized for this phase`
- Decisions constraining the next action: `keep huggingface-hub 1.1.7, resumable directory uploads by default, outer batches of at most 20 files, default workers of 5, and the dataset-to-model compatibility write route`
- Tests passed: `python tests/test_resumable_commit_policy.py -> 36/36; complete upload capability group passed; python tests/run_cli_baseline.py -> 65 passed in 46.29s; python -m compileall -q ., python -m pip check, and git diff --check passed`
- Tests failed or not run: `no known offline failures; live AtomGit upload intentionally not run because this phase has no live-write authorization`

## Active Issue Identity

- ID: `GH-21`
- Title: `Fix resumable upload commit timeouts and 429 retry loops`
- Primary type: `bug`
- Priority: `P1`
- Base branch: `yuto`
- Delivery mode: `standing local task-branch delivery into yuto`
- Permissions: `local edits=yes; offline tests=yes; commit=yes; merge into yuto=yes; push yuto=yes; task-branch push=no; PR=no; Issue transition=no; live AtomGit writes=no; release=no`

## Evidence And Objective

- User impact: a 700-file, 622.5 GB resumable dataset upload pre-uploaded the first 20-file batch but remained at zero committed files after a commit read timeout and repeated HTTP 429 responses.
- Pre-fix behavior: omitting the CLI timeout removed the parent wall-clock limit while the locked HF client retained its 10-second request timeout; HF 1.1.7 requeued commit failures but its minimum target chunk was 20, so an outer 20-file batch did not actually shrink.
- Ambiguity: a commit read timeout does not prove the server rejected the commit, so blind retries can create duplicate commits and trigger rate limiting.
- Objective: make resumable commit attempts use explicit request-timeout semantics, error-specific backoff, remote reconciliation after ambiguous outcomes, real batch reduction, and bounded failure while preserving resumable progress.
- Affected path: `cli.upload -> HuggingFaceAPI.upload_directory -> _run_resumable_upload -> HfApi.upload_large_folder -> HfApi.create_commit`.

## Scope And Acceptance

- Keep the omitted overall upload deadline unlimited while applying a documented bounded HTTP request timeout in the child process.
- Recreate the locked HF HTTP client after applying request-timeout policy so cached process-global state cannot retain the old value.
- Honor `Retry-After` for HTTP 429; otherwise use capped exponential backoff with jitter. Do not split batches for rate limiting.
- Retry connection failures, read timeouts, and HTTP 502/503/504 with bounded attempts; fail actionable non-retryable 400/401/403/404 responses.
- Reconcile remote paths and object identities after an ambiguous commit timeout before retrying.
- Reduce genuine persistent commit failures as `20 -> 10 -> 5 -> 2 -> 1` without changing the outer maximum batch size of 20.
- Preserve stable projection and HF resumable metadata when a batch ultimately fails, return a nonzero CLI result, and avoid an infinite retry loop.
- Detect or clearly warn about escaped glob stars that HF would interpret literally.
- Add focused offline regression coverage at the real locked-library boundary and update affected documentation.
- Run the complete offline CLI baseline, `python -m compileall -q .`, `python -m pip check`, and `git diff --check`.

## Compatibility And Non-Goals

- Preserve Python 3.9 compatibility and the public CLI surface unless a new option is explicitly approved.
- Keep `huggingface-hub==1.1.7` and `datasets==4.4.1` unchanged.
- Preserve default resumable directory routing, worker default 5, path prefixes, and the AtomGit dataset compatibility write route.
- Do not perform live uploads, repository creation or deletion, dependency upgrades, unrelated refactoring, release work, or remote Issue transitions.

## Verification Evidence

- Planning evidence: locked `huggingface-hub==1.1.7` exposes `set_client_factory`, `get_session`, and `close_session`; its default HTTP request timeout is 10 seconds and its large-folder commit scale has a minimum of 20.
- Pre-change remote evidence: first batch data transfer completed, commit responses timed out, and subsequent commit attempts returned HTTP 429.
- Post-change evidence: `HTTP request timeout, Retry-After, 429/413/5xx/network classification, ambiguous remote reconciliation, persistent sub-batch metadata, real 20/10/5/2/1 reduction, shared overall deadline, child termination, and escaped glob rejection are covered offline; complete CLI baseline passed`.

## Closure

- Status: `accepted; delivery in progress`
- Human acceptance: `accepted by explicit user instruction on 2026-08-10`
- Independent review: `APPROVED after resolving partial sub-batch metadata persistence, Retry-After truncation, actionable error classification, shared deadline, HTTP 413 reduction, and non-reducible connection failure findings`
- Delivery: `task-branch commit, local yuto merge, and yuto push authorized; pending execution`
