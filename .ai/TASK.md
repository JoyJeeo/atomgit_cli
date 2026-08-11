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
- Phase: `implementation, post-fix verification, DoD audit, and final independent review approved; ready for authorized local delivery`
- Base branch: `yuto`
- Task branch: `codex/auto-configure-lfs`
- Base commit: `030db6c`
- Current HEAD: `030db6c` (uncommitted authorized Issue diff)
- Worktree state: `dirty authorized task work on codex/auto-configure-lfs`
- Changed paths: `.ai/ARCHITECTURE.md`, `.ai/PRODUCT.md`, `.ai/TASK.md`, `README.md`, `api.py`, `cli.py`, `docs/architecture.md`, `docs/faq.md`, `docs/upload_command_analysis.md`, `tests/cli_baseline_contract.py`, `tests/test_auto_configure_lfs.py`
- Required worktree: `/Users/yutaozhang/yuto/codes/atomgit/atomgit_cli`
- Last completed action: `preserved exact extension case, verified distinct case variants, passed focused 26/26 and the final 66-case gate, and received an APPROVED final independent review with no findings`
- Next exact action: `commit the cohesive Issue diff, merge it locally into yuto, record final delivery identity, and push only yuto`
- Blockers / open questions: `live AtomGit write verification is intentionally not authorized and must remain unperformed`
- Decisions constraining the next action: `remote mutation requires explicit --auto-configure-lfs; inferred rules are validated extension patterns and the CLI warns that they affect the whole repository; use an isolated private buffer, exact revision, optimistic parent commit, bounded verification/retry, and preserve resumable metadata`
- Tests passed: `offline in atomgit_cli: final python tests/test_auto_configure_lfs.py 26/26; earlier affected suites test_upload_resumable.py 47/47, test_resumable_commit_policy.py 51/51, test_resumable_recovery.py 5/5, test_upload_batching.py 9/9, test_dataset_resumable_route.py 11/11, test_upload_error_classify.py 42/42, test_hf_api_contract.py 13/13, test_cli_surface.py 50/50, test_cli_feature_baseline.py 51/51; final python tests/run_cli_baseline.py 66/66 isolated pytest cases in 53.26s; python -m compileall -q .; python -m pip check (no broken requirements); git diff --check`
- Tests failed or not run: `the new focused regression failed at the expected pre-fix boundary before implementation; no post-fix offline failure remains; live AtomGit writes and real service acceptance were not run because they are not authorized`

## Active Issue Identity

- ID: `LOCAL-AUTO-CONFIGURE-LFS`
- Title: `Add explicit resumable LFS policy repair`
- Primary type: `cli`
- Priority: `P1`
- User impact: `large resumable uploads stop after hashing when AtomGit classifies a file above the regular-commit limit as regular; users without a local checkout must manually edit the remote .gitattributes before resuming`
- Affected path: `cli.upload -> HuggingFaceAPI.upload_directory -> resumable child upload-mode validation -> bounded worker failure -> parent-side .gitattributes transaction -> retry current outer batch`
- Base branch: `yuto`
- Delivery mode: `standing local task-branch delivery into yuto after implementation, verification, independent review, and acceptance`
- Permissions: `local Issue registration=yes; source/test/human-doc edits=yes; task branch=yes; offline tests=yes; independent review=yes; commit=yes; local merge into yuto=yes; push yuto=yes; task-branch push=no; PR=no; live AtomGit writes=no; remote Issue transition=no; release=no`
- Explicit remote prohibition: `do not write to any openlet dataset; do not perform any live repository write during this Issue unless the maintainer separately names and authorizes an exact test repository and operation`

## Evidence And Objective

- The accepted resumable flow already rejects files above 1,000,000,000 bytes when the server selects `regular`, before content reads or Base64 commit serialization.
- The worker currently returns only the `upload_mode` category, so the parent cannot identify a bounded safe LFS rule or repair the policy.
- The CLI currently offers no explicit remote-policy repair option and tells the user only to modify `.gitattributes` manually.
- Locked `huggingface-hub==1.1.7` exposes `HfApi.upload_file(..., revision=..., parent_commit=...)` and `HfApi.create_commit(..., parent_commit=...)`.
- AtomGit's normal HF download path cannot use `repo_info`; the existing direct resolve transport is the relevant read boundary and must address the exact target revision.
- Objective: add an explicit `--auto-configure-lfs` directory-resumable option that safely creates or appends remote `.gitattributes`, visibly reports the repository-wide rule, and retries the failed batch without losing resumable state.

## Scope And Acceptance

- Add the exact public CLI flag `--auto-configure-lfs`, default off.
- Reject the flag for single-file or ordinary directory uploads instead of silently ignoring it.
- Without the flag, preserve safe failure and add an actionable hint to retry with `--auto-configure-lfs` when the user authorizes a remote configuration commit.
- On unsafe regular mode, carry only bounded validated extension patterns such as `*.bag` across the child boundary; do not carry a token, URL, response body, or local full path.
- With the flag, print the detected rules and explicitly warn that each rule applies to the whole target repository.
- Read only the target revision's root `.gitattributes`; if absent, create it in an isolated private cache transaction; if present, preserve its bytes and append only the required lines.
- Commit only `.gitattributes` with a concise fixed message, explicit AtomGit endpoint, normalized repo ID, effective transfer repo type, exact revision, and optimistic `parent_commit`.
- Bound configuration attempts and reconcile ambiguous results by re-reading remote state; do not overwrite concurrent changes or loop indefinitely.
- Retry the same outer batch after confirmed configuration; retain hashes, committed metadata, batch ordering, timeouts, summaries, and error classification.
- Preserve all existing CLI and SDK behavior when the option is absent.
- Update exact CLI schema, focused regressions, README, FAQ, architecture, and upload analysis.

## Compatibility And Non-Goals

- Preserve Python 3.9+, `huggingface-hub==1.1.7`, and `datasets==4.4.1`.
- Do not change locked dependencies, package version, SDK public signatures, normal upload routing, repository creation, or Git credential configuration.
- Do not clone repositories or require local Git/Git LFS for the automatic transaction.
- Do not infer wildcard rules for files without one safe extension; retain the manual failure path instead.
- Do not delete, reorder, normalize, or broadly rewrite existing `.gitattributes` content.
- Do not add a hard-coded product restriction for a user namespace; the `openlet` prohibition constrains development and live verification only.
- Do not perform live uploads, configuration commits, repository/branch creation, deletion, or other AtomGit writes without a separate exact authorization.

## Required Verification

- Prove the previous implementation rejects the new public option or cannot repair an upload-mode failure.
- Verify exact CLI schema, help, invalid file/ordinary-mode use, and downstream forwarding.
- Verify missing and existing `.gitattributes`, missing final newline, existing final rule, multiple safe patterns, unsafe/no-extension paths, size bounds, private cache permissions, and one-file-only upload arguments.
- Verify exact revision reads/writes, dataset compatibility routing, `parent_commit`, concurrent conflict re-read, ambiguous write verification, bounded retry, and no duplicate/empty commits.
- Verify detection output shows the rule and repository-wide impact; verify the no-flag error recommends `--auto-configure-lfs`.
- Verify the failed outer batch resumes, already attempted rules do not loop, hashes remain reusable, and ordinary error summaries remain intact.
- Verify child envelopes and CLI output cannot contain fake tokens, signed URLs, raw response bodies, or local full paths.
- Inspect the locked dependency signatures used by implementation.
- Run focused upload/configuration tests, affected existing upload suites, `python tests/run_cli_baseline.py`, `python -m compileall -q .`, `python -m pip check`, and `git diff --check` in the `atomgit_cli` conda environment.
- Apply `.ai/DOD.md` and perform the distinct no-edit independent review in `.ai/REVIEW.md`.

## Delivery Status

- Definition of done: `passed: exactly one Issue active; diff is task-scoped; public CLI schema, focused regression, affected suites, full baseline, compile, dependency and diff checks pass; locked signatures inspected; buffer lifetime and global state are bounded; docs match; no credential or generated-artifact finding; unrun live test is explicitly disclosed`
- Independent review: `APPROVED on the final fresh review after resolving all earlier P1/P2 findings; no open P0/P1/P2/P3 finding`
- Human acceptance: `accepted through the maintainer's explicit authorization to implement, verify, independently review, commit, locally merge, and push yuto once the requested behavior and gates pass`
- Delivery: `pending`
- Live verification: `not authorized; no AtomGit repository may be written during this Issue, and openlet datasets are explicitly prohibited`
