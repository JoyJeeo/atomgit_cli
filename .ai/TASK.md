# Current Issue Contract

Status: `active`

## Handoff Snapshot

- Updated: `2026-08-12 16:12:00 +0800`
- Phase: `human accepted; local commit, merge into yuto, and yuto-only push authorized and in progress`
- Base branch: `yuto`
- Task branch: `codex/proactive-lfs-attributes`
- Base commit: `45925471cac34777932eb6234d9b00e6dee43431`
- Current HEAD: `45925471cac34777932eb6234d9b00e6dee43431`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit/atomgit_cli`
- Worktree state: `dirty with only active-Issue source, focused tests, documentation, architecture, and handoff changes`
- Changed paths: `.ai/ARCHITECTURE.md`, `.ai/TASK.md`, `README.md`, `api.py`, `cli.py`, `docs/architecture.md`, `docs/faq.md`, `docs/upload_command_analysis.md`, `tests/test_auto_configure_lfs.py`
- Last completed action: `maintainer accepted the live behavior and explicitly authorized commit and push; delivery baseline passed 68/68 in 59.01s`
- Next exact action: `commit the task branch, merge it locally into yuto, push only yuto, verify github/yuto, then finalize this handoff`
- Blockers: `none`
- Tests: `pre-implementation test_auto_configure_lfs.py failed at the absent child policy arguments; final test_auto_configure_lfs.py passed 41/41; affected test_upload_resumable.py passed 49/49, test_lfs_preupload_policy.py 89/89, test_resumable_commit_policy.py 51/51, test_upload_progress.py 28/28, test_upload_validation.py 15/15, test_dataset_resumable_route.py 11/11, test_canonical_lfs_pointer.py 24/24, test_cli_feature_baseline.py 52/52, and test_cli_baseline_guard.py 14/14; mandatory python tests/run_cli_baseline.py passed 68/68 in 51.27s, 54.23s, after the P1 review fix in 57.66s, and after live evidence documentation in 50.90s; final python -m compileall -q ., python -m pip check, git diff --check, credential/generated-artifact audit, and locked callable signature inspection passed`
- Required worktree: `/Users/yutaozhang/yuto/codes/atomgit/atomgit_cli`

## Active Issue

- ID: `LOCAL-PROACTIVE-LFS-ATTRIBUTES`
- Title: `Synchronize attributes for server-selected LFS extensions`
- Primary type: `cli`
- Priority: `P2`
- Observable objective: `when an operator explicitly enables --auto-configure-lfs for a resumable directory upload, every safe file extension that AtomGit selects for LFS in that upload is checked against the target revision root .gitattributes and any missing effective LFS rule is appended before the affected file is pre-uploaded or committed`
- User impact: `AtomGit may select .bag and other large files for LFS even when the repository has no matching .gitattributes rule; the object upload succeeds but a later Git clone or checkout may not apply the expected Git LFS filter because the current option only repairs files incorrectly classified as oversized regular blobs`

## Evidence And Current Behavior

- The reported 20-file batch showed `pre-uploaded: 19/19` while the displayed remote `.gitattributes` did not contain `*.bag`.
- Current `_validate_resumable_upload_mode_items` emits patterns only when a file is both larger than 1 GB and selected as `regular`.
- Current parent coordination invokes `_configure_remote_lfs_attributes` only for the resulting `upload_mode` worker error.
- Therefore files already selected as `lfs` never trigger the option, even though their repository-wide extension rule can be absent.
- Locked runtime contracts remain `huggingface-hub==1.1.7` and `datasets==4.4.1`.

## Expected Behavior And Scope

In scope:

- Preserve `--auto-configure-lfs` as an explicit opt-in remote mutation.
- At the scoped HF 1.1.7 upload-mode boundary, derive only existing validated `*.ext` patterns from items whose server-selected mode is `lfs`.
- Before those items can enter LFS preupload or commit processing, use the existing optimistic, read/merge/write/readback `.gitattributes` transaction to verify or append missing effective rules.
- Serialize concurrent worker checks, avoid repeated remote checks for an extension during the same upload process, and retain existing cross-batch safety.
- Keep the existing oversized-regular repair and retry behavior.
- Preserve model/dataset compatibility routing, target revision, request timeout/deadline behavior, credential-safe errors, metadata recovery, and restoration of dependency globals.
- Update CLI help and authoritative upload documentation to describe proactive behavior.

Out of scope:

- No default mutation when the flag is absent.
- No automatic rules for files without a safe extension, ignored files, files selected as `regular`, or extensions not observed as LFS.
- No ordinary directory or single-file support change.
- No writes to any `OpenLET/*` repository, remote Issue creation, dependency
  changes, release, or unrelated upload refactor.

## Acceptance Criteria

1. With the option enabled, a server-selected `lfs` item with a safe extension causes the existing remote attributes transaction before `_get_upload_mode` returns and hence before LFS preupload/commit queueing.
2. An already-effective rule is checked but produces no `.gitattributes` commit; a missing or overridden rule is appended and verified.
3. Repeated files and concurrent upload-mode workers check a pattern at most once per isolated upload process; subsequent outer batches do not create duplicate rules.
4. Multiple safe extensions are handled deterministically within the existing 32-pattern and extension validation limits.
5. Without the flag, upload behavior and remote calls remain unchanged.
6. Existing oversized-regular repair, bounded LFS Batch failure behavior, resumable metadata, dataset/model routing, revision forwarding, timeout handling, and global restoration continue to pass.
7. CLI output clearly reports proactive checks/changes without exposing local paths, tokens, response bodies, signed URLs, OIDs, or trace identifiers.
8. User documentation matches the implemented behavior and limitations.

## Verification And Delivery

- Add or extend the focused executable `tests/test_auto_configure_lfs.py`; it must reproduce the missing proactive call before implementation.
- Run focused auto-configure, resumable, LFS preupload, batching, progress, validation, dataset routing, canonical pointer, and CLI surface tests as affected.
- Run mandatory `python tests/run_cli_baseline.py`, `python -m compileall -q .`, `python -m pip check`, and `git diff --check` in the `atomgit_cli` conda environment.
- Perform the independent review in `.ai/REVIEW.md` after implementation and resolve all blocking findings.
- Delivery mode: `local task branch based on yuto; stop for human acceptance after implementation, tests, and review`.
- Authorized: `create the local task branch and edit local source, tests, documentation, and TASK.md`.
- Live authorization: `after offline verification, read/write acceptance is
  authorized only against weixin_52273949/cli_demo_dataset using a unique test
  prefix; every OpenLET repository is explicitly excluded`.
- Delivery authorization: `maintainer explicitly authorized commit and push on
  2026-08-12; standing delivery rules authorize the local task commit, local
  merge into yuto, and pushing only yuto while prohibiting task-branch push`.
- Not authorized: `writes to any other remote repository, remote Issue
  transitions, task-branch push, PR, tag, release, or publication`.
- Human acceptance: `accepted on 2026-08-12 after the maintainer's OpenLET
  upload showed *.bag configuration before preupload, 20/20 LFS completion,
  fast content-addressed reuse for the first batch, and actual transfer for
  missing objects in the next batch`.

## Review Record

- First review verdict: `REQUEST CHANGES`.
- P1 finding: `the effective-rule parser tracked only later exact-pattern lines,
  so a broader later rule such as * -filter could override *.bag while the CLI
  incorrectly treated the LFS rule as effective and skipped repair`.
- Disposition: `implementation resumed; require a trailing standard LFS rule
  block and add broad-override plus multi-pattern suffix regressions before
  repeating the full verification and review`.
- Fix verification: `test_auto_configure_lfs.py passed 41/41;
  test_resumable_commit_policy.py passed 51/51;
  test_lfs_preupload_policy.py passed 89/89; mandatory baseline passed 68/68
  in 57.66s`.
- Second review verdict: `APPROVED`; no remaining findings. Residual risk is
  limited to the authorized AtomGit live write/readback acceptance.

## Live Acceptance Evidence

- Authorization boundary: `read/write only against
  weixin_52273949/cli_demo_dataset; no OpenLET repository was read or written`.
- Initial target HEAD: `08a8e134bf9518cc6fc34a1027693b002d9365b0`.
- Existing root `.gitattributes` was read exactly by immutable SHA; `*.bag` was
  already effective and the unique `*.codexlfsbag` test rule was absent.
- Uploaded one local 12 MiB fixture to
  `codex-live/proactive-lfs-attributes-20260812-155519/probe.codexlfsbag` with
  resumable dataset mode, batch size 1, and `--auto-configure-lfs`.
- The service selected the file as LFS. Before object preupload, the CLI
  reported the missing `*.codexlfsbag` rule, updated root `.gitattributes`,
  retried the batch, and completed successfully.
- Immutable post-upload HEAD was
  `e1cb1bc73c26e23e47ce0d47cb2a024c103b530e`; exact readback found one effective
  rule line and a 12,582,912-byte remote object whose SHA-256 matched the local
  fixture: `cfadd44a103cbd6d5726fa07b27d7aad2f67ed3930ff96901c486a5beaf7e723`.
- Repeating the exact command skipped the one committed file, checked the
  existing rule without updating it, and returned success with zero new files.
  HEAD remained `e1cb1bc73c26e23e47ce0d47cb2a024c103b530e` and the rule line count remained 1.
- No remote cleanup was performed; the uploaded acceptance fixture and the
  repository-wide test extension rule remain in the authorized test repository.
