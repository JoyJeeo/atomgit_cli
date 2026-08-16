# Current Issue Contract

Status: `completed`

## Handoff Snapshot

- Updated: `2026-08-16 +0800`
- Phase: `implementation delivered locally: independently approved, committed on the local-only task branch, and merged into yuto without push`
- Base branch: `yuto`
- Task branch: `codex/development-floor`
- Base commit: `b923d7af12765bb3bcfea0ad2a963e46833ad7d2`
- Task commit: `e11adad test: establish development floor`
- Merge commit: `7dd90ed merge: establish development floor`
- Current HEAD before this completion record: `7dd90ed000e690d5d3ec9800aa2b684b12ae780f`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `dirty only for this final completion record on yuto`
- Changed paths: `.ai/TASK.md`
- Last completed action: `committed e11adad on the local-only task branch and merged it into yuto as 7dd90ed without pushing`
- Next exact action: `commit this final completion record locally; no push or remote Issue transition is authorized`
- Blockers: `none`
- Tests run: `pre-implementation python tests/test_development_floor.py failed as required because development_floor_contract was absent; final test_development_floor.py passed 15/15; test_cli_baseline_guard.py passed 14/14; test_cli_feature_baseline.py passed 52/52; pytest collection reported 70; complete python tests/run_cli_baseline.py passed 70/70 in 58.74s, after the first review fixes in 56.78s, and after the second review fix in 56.92s; python -m compileall -q ., python -m pip check, git diff --check, locked dependency version checks, document links, scope, registry mapping, and credential scans passed`

## Active Issue

- Remote Issue: `#24 https://github.com/JoyJeeo/atomgit_cli/issues/24`
- ID: `GH-24-DEVELOPMENT-FLOOR`
- Title: `Establish the development floor capability baseline`
- Primary type: `testing`
- Priority: `P1`
- Observable objective: `make every implemented and future capability part of one monotonic, executable, documented quality gate that blocks delivery and further feature expansion when any protected behavior regresses`
- User impact: `future work cannot silently remove, weaken, or stop testing an existing CLI or SDK capability`

## Formal Definition

> AtomGit CLI 的所有已实现能力，都必须拥有稳定的能力登记、明确的行为不变量、可执行的离线回归测试、必要的依赖和安全契约，以及在适用时的受控远程证据。任何开发活动都必须证明受影响的旧能力未退化，并将新增能力纳入同一套基线。未通过开发底线的变更，不得进入 Issue 完成、合并、发布或继续扩展开发阶段。

## Starting Evidence

- Before this Issue, the mandatory baseline collected 69 isolated offline test scripts.
- `tests/cli_baseline_contract.py` already locks the exact public CLI schema, leaf dispatches, and one capability group for every offline script.
- `tests/test_cli_baseline_guard.py` rejects unregistered or missing commands, parameters, tests, stale registrations, missing dispatches, and inert test entrypoints.
- `docs/testing.md` still reports 62 pytest cases while collection and the executable registry report 69.
- Existing test grouping does not provide stable capability IDs, explicit observable invariants, risk/evidence categories, documentation links, or controlled-remote evidence status.
- The AI workflow does not yet require every Issue to declare affected capability IDs and protected invariants.

## Affected Capability IDs

- `FLOOR-REGISTRY`: new meta-capability for the development-floor registry and validator.
- `CLI-SURFACE`, `CLI-DISPATCH`: preserve the existing exact CLI baseline contracts.
- `AUTH-CONFIG`, `GIT-CREDENTIAL`, `REPO-MANAGEMENT`, `REVISION`.
- `UPLOAD-FILE`, `UPLOAD-FOLDER`, `UPLOAD-RESUMABLE`, `UPLOAD-LFS`, `UPLOAD-LFS-RECOVERY`.
- `DOWNLOAD-SNAPSHOT`, `DOWNLOAD-FILE`, `DOWNLOAD-INTEGRITY`, `DOWNLOAD-SECURITY`.
- `SDK-DOWNLOAD`, `SDK-UPLOAD`, `SDK-REPO`, `REPO-ID`, `RUNTIME`, `CACHE`.
- `DEPENDENCY-CONTRACT`, `PACKAGING`, `PORTABILITY`, `ERROR-REDACTION`.

## Protected Existing Invariants

- No registered CLI command, option, argument, leaf dispatch, or offline regression script may disappear or change silently.
- Every offline test remains isolated from the real HOME, Git configuration, credentials, and network by default.
- Locked dependency, credential safety, upload/download integrity, packaging, and portability contracts remain executable.
- Existing tests may not be deleted, skipped, weakened, or reclassified to accommodate an unintended regression.

## New Or Changed Invariants

- Every implemented capability has one stable ID and complete risk, entrypoint, invariant, offline-test, documentation, evidence-category, and controlled-remote-status metadata.
- Capability IDs and invariant IDs are unique and monotonic.
- Every registered offline test maps to at least one capability, and every capability maps to executable offline evidence.
- Every referenced test and document exists; test references remain part of the exact baseline registry.
- New Issues declare affected capability IDs, protected existing invariants, new or changed invariants, focused tests, complete-baseline evidence, and residual risks.
- A failing or unrun complete baseline blocks Issue completion, delivery commit, merge, push, release, and further feature expansion.
- Intentional compatibility changes require explicit maintainer authorization and a recorded contract migration.

## Scope

In scope:

- Add an authoritative development-floor AI document and matching human testing documentation.
- Add a declarative capability/invariant registry covering all currently implemented capabilities.
- Add a focused self-executing offline contract test and register it in the complete baseline.
- Calibrate test counts and baseline descriptions to the executable repository state.
- Update AI master rules, development rules, testing rules, DoD, review, workflow, and task evidence fields.
- Update only tests and testing/development documentation.

Out of scope:

- No changes to `cli.py`, `api.py`, `atomgit_hub.py`, configuration, runtime, upload, download, authentication, repository, LFS, installer, packaging, or dependency behavior.
- No dependency upgrade or public compatibility change.
- No live AtomGit tests, repository writes, credential-helper mutation, release, tag, publication, or access to user credentials.
- No task-branch push.

## Acceptance Criteria

1. The formal definition is authoritative in the AI framework and human testing documentation.
2. All current implemented capabilities have stable IDs, explicit observable invariants, risk/evidence metadata, offline tests, documentation, and controlled-remote evidence status.
3. A focused executable test rejects missing, duplicate, stale, or incomplete capability and invariant registrations.
4. Every offline test script maps to at least one capability while the exact test registry remains monotonic.
5. Future Issue contracts contain affected capability IDs, protected and changed invariants, focused tests, baseline evidence, and residual risk.
6. The full baseline is mandatory for every development Issue and blocks completion, delivery, merge, push, release, and further feature expansion when failed or unrun.
7. Compatibility migrations require explicit maintainer authorization and may not hide unintended regressions by weakening tests.
8. Human and AI documentation agrees with actual collected tests and commands.
9. Focused tests, the full offline baseline, compileall, pip check, and diff check pass.
10. The final diff contains only tests and testing/development documentation, with no functional source or dependency changes.

## Verification And Delivery

- Demonstrate focused contract failure before adding the registry and required documentation.
- Run `python tests/test_development_floor.py` after implementation.
- Run `python tests/test_cli_baseline_guard.py` and `python tests/test_cli_feature_baseline.py`.
- Run `python tests/run_cli_baseline.py`, `python -m compileall -q .`, `python -m pip check`, and `git diff --check` in the `atomgit_cli` conda environment.
- Audit the diff for credentials, generated artifacts, unrelated changes, functional source changes, and dependency changes.
- Perform the independent review in `.ai/REVIEW.md`; resolve all findings before delivery.
- Delivery mode: `local-only task branch based on yuto, conventional task commit, and local merge into yuto; no push is authorized by this request`.
- Authorized: `create GitHub Issue #24; modify tests and testing/development documentation; create the local task branch; test; review; commit; merge locally into yuto`.
- Not authorized: `task-branch or yuto push, PR, remote Issue closure or other state transition, tag, release, publication, live AtomGit operation, credential mutation, or functional source/dependency change`.
- Human acceptance: `the maintainer explicitly authorized Issue registration and the complete development, testing, commit, and local merge workflow in the current request, contingent on the development floor and review passing`.
- Delivery: `task commit e11adad; local merge 7dd90ed; yuto is intentionally ahead of github/yuto and neither branch was pushed; GitHub Issue #24 remains open; no PR, tag, release, publication, live AtomGit operation, credential mutation, functional source change, or dependency change occurred`.

## Review Record

- First verdict: `REQUEST CHANGES`
- P2 finding: `the starting evidence used the word currently for the pre-change 69-test inventory, which would become stale as soon as the new test joined the baseline`.
- P1 process finding: `TASK.md inferred yuto push authorization from prior standing instructions even though the current user explicitly retired the previous AGENTS instructions and requested Issue registration, development, testing, commit, and merge without explicitly requesting push`.
- Disposition: `returning to implementation to make the 69-test evidence explicitly historical and restrict delivery to local commit and merge`.
- Second verdict: `REQUEST CHANGES`.
- P2 finding: `the human document listed all 26 capabilities, but the executable workflow-document validator checked only the document, formal definition, and a loose 70 marker, so one capability row or the 26/61 counts could later disappear without failing the floor`.
- Disposition: `returning to implementation to bind every capability ID and the exact 26/61/70 ledger counts to docs/development_floor.md`.
- Final verdict: `APPROVED`; no open findings.
- Residual risk: `the registry and offline regressions cannot create new live-service evidence; controlled and partial remote statuses preserve existing evidence boundaries, and this Issue performed no live AtomGit operation`.
