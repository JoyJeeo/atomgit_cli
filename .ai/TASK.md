# Current Issue Contract

Status: active

## Handoff Snapshot

- Updated: `2026-08-18 +0800`
- Phase: `implementation complete; final self-acceptance and complete offline
  verification passed; ready for authorized commit, local merge, push, and
  remote verification`
- Base branch: `yuto`
- Base commit: `a09c38075ff74578acf6255a602cd5ef408d230e`
- Base synchronization before activation: `yuto`, `github/yuto`, and
  `github/HEAD` resolved to `a09c38075ff74578acf6255a602cd5ef408d230e`
- Task branch: `codex/environment-lifecycle-ownership` (local only; never push)
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `dirty with task-owned lifecycle source, tests, contracts,
  documentation, packaging metadata, and this handoff; resume in this same
  worktree`
- Last completed action: `resolved the review finding by completing and
  narrowing historical module-object patch forwarding, reran the final full
  baseline and supporting gates, and completed the clean re-review`
- Next exact action: `create the cohesive conventional task commit, merge it
  locally into yuto with --no-ff, push only yuto, and verify github/yuto`
- Blockers: `none`

## Predecessor Reconciliation

The structure/behavior foundation, packaging metadata/discovery foundation,
mechanical src-layout migration, and infrastructure/utils ownership Issues are
complete, accepted, merged, pushed, and remotely verified. The actual clean
delivery baseline is `a09c380`; the predecessor record's earlier
`41cdbd7`/`a67bb8f` intermediate references are historical rather than the
current repository identity. No predecessor source defect or user change was
found.

Predecessor delivery: task commit `dc32679`, local no-ff merge `a67bb8f`, final
delivery record `a09c380`, and verified `github/yuto` at `a09c380`.

## Active Issue

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-REFACTOR-ENVIRONMENT-LIFECYCLE-OWNERSHIP`
- Title: `Extract environment lifecycle ownership behind historical paths`
- Primary type: `refactoring`
- Secondary types: `compatibility`, `testing`, `security`, `distribution`,
  `documentation`
- Priority: `P2`
- Observable objective: `move conda environment policy, managed completion
  paths, completion installation/migration, and uninstall implementation into
  owned lifecycle modules while preserving historical imports, symbols,
  identities, signatures, module-object patch seams, CLI and Shell outcomes,
  artifacts, and user-data safety`
- User impact: `none by design; internal ownership migration only`

### Authorization And Delivery

- User authorization: `the maintainer approved the complete sequential
  capability-oriented structure program on 2026-08-18 and explicitly requested
  continued development in this new conversation`
- Approved program step: `5. Environment Lifecycle Ownership`
- Accepted conditions:
  1. `environment, managed-path, completion, and uninstall modules are created
     only as their real implementation moves`
  2. `Python lifecycle policy is centralized and the package-absent POSIX Shell
     fallback remains parity-tested`
  3. `atomgit.completion and atomgit.uninstaller remain historical facades`
  4. `old-path direct and module-object patch seams remain effective`
  5. `no authentication, repository, download, upload, LFS, SDK, CLI command,
     API facade, CLI facade, or distribution ownership extraction is included`
- Authorized local actions: `edit task-owned source, packaging metadata,
  tests, registries, AI and human documentation; inspect locked dependencies;
  build temporary artifacts; run offline checks; review; commit; and locally
  merge`
- Authorized remote delivery: `after implementation, complete verification,
  independent review, and maintainer acceptance, push only the locally merged
  yuto branch and verify github/yuto; never push the task branch`
- Unauthorized actions: `remote Issue/PR creation or transition, task branch
  push, tag or Release mutation, publication, live AtomGit writes, credential
  mutation, deletion, or upstream main changes`
- Delivery mode: `local task branch -> focused and complete offline
  verification -> independent review -> human acceptance -> cohesive
  conventional commit -> local no-ff merge into yuto -> push only yuto ->
  verify github/yuto`

### Pre-Implementation And Expected Behavior

#### Pre-Implementation Baseline

- `src/atomgit/completion.py` owns Click-derived Zsh adapters, conda activation
  and deactivation hooks, legacy `.zshrc` migration, atomic writes, concurrent
  modification checks, rollback, and completion removal.
- `src/atomgit/uninstaller.py` owns conda-prefix validation, the exact managed
  completion manifest, safe removal, uninstall planning, and pip dispatch.
- `src/atomgit/uninstaller.py` imports source/editable-install policy from
  `src/atomgit/release.py`, leaving the registered legacy forbidden dependency
  edge `uninstaller -> release`.
- `uninstall.sh` contains the package-absent fallback for the exact managed
  manifest and safe removal rules.
- Existing callers and tests import and patch historical completion and
  uninstaller module objects, including private helpers and `subprocess`.

#### Expected

- Real implementation lives in non-placeholder `atomgit.lifecycle` modules
  for environment policy, managed paths, completion, and uninstall.
- `atomgit.completion` and `atomgit.uninstaller` contain compatibility-only
  forwarding logic with exact debt ceilings and preserve historical symbols,
  callable identities, signatures, and patch seams.
- Source/editable-install detection has one lifecycle owner shared by update
  and uninstall policy; the `uninstaller -> release` forbidden edge is removed
  and the structure contract tightens in the same change.
- Source, default PEP 660 editable, wheel, and sdist discovery include every
  delivered lifecycle module exactly and continue to exclude repository files.
- CLI schema, completion lightness, conda paths, legacy migration, rollback,
  concurrency rejection, post-pip guidance, confirmation, uninstall commands,
  and preservation of user configuration, credentials, cache, and unrelated
  files remain unchanged.

### Scope

#### In Scope

- Add only lifecycle modules that receive real implementation in this Issue.
- Move conda-prefix/environment policy, managed completion-path and removal
  policy, completion implementation, uninstall planning and execution, and the
  shared source/editable-install detector to explicit lifecycle owners.
- Preserve historical public/private names, signatures, identities, direct
  patches, `patch.object` behavior, lazy completion imports, exact CLI output,
  error types, rollback, file modes, symlink protections, concurrent-change
  rejection, idempotence, and POSIX/Windows outcomes.
- Strengthen package-absent `uninstall.sh` parity evidence against the Python
  owner without making the Shell fallback depend on the installed package.
- Update exact ownership, dependency, facade debt, artifact, source-layout,
  import, development-floor, architecture, and testing contracts.

#### Out Of Scope

- Authentication, repository service, download, upload, resumable, LFS, SDK,
  or CLI command extraction.
- `api.py` or `cli.py` package/facade conversion; public behavior, dependency
  upgrades, exception redesign, logging/type/format sweeps, broad test-layout
  changes, live operations, publication, and unrelated debt cleanup.
- Distribution release/installer ownership beyond moving the single shared
  source/editable-install policy and preserving all current update behavior.

### Affected Capability IDs

- `FLOOR-REGISTRY`, `CLI-SURFACE`, `CLI-DISPATCH`, `RUNTIME`, `PACKAGING`,
  `PORTABILITY`, `AUTH-CONFIG`, and `GIT-CREDENTIAL`

### Protected Existing Invariants

- All existing `93` invariants remain protected, especially `FLOOR-005..008`,
  `CLI-003/005/006`, `DISPATCH-004..005`, `RUNTIME-003..004`,
  `PKG-003/009..015`, `PORT-001/003..007`, `AUTH-002`, and `GITCRED-001..002`.
- Historical imports and symbols at `atomgit.completion` and
  `atomgit.uninstaller`, CLI schema/dispatch, `sys.modules` access, completion
  lightness, runtime idempotence, exact conda paths, migration confirmation,
  atomicity, rollback, concurrency detection, update source-install behavior,
  uninstall confirmation/pip dispatch, user-data preservation, and
  package-absent fallback remain unchanged.

### New Or Changed Invariants

- `FLOOR-009`: lifecycle implementations have exact owners while historical
  completion/uninstaller paths remain thin and preserve registered symbols,
  identities, signatures, and patch seams; ownership drift, facade regrowth,
  placeholders, and reintroduced forbidden dependency edges fail closed.
- `PKG-016`: source, default PEP 660 editable, wheel, and sdist surfaces include
  exactly the delivered lifecycle modules and historical facades without
  repository leakage.
- `PORT-008`: installed Python lifecycle policy and the package-absent POSIX
  uninstall fallback share an executable manifest and safety/outcome contract.

### Focused Tests And Evidence

- Add `tests/test_environment_lifecycle_ownership.py` for implementation
  provenance, exact ownership/facade negative cases, historical symbols and
  identities, direct/private/module-object patch seams, centralized policy,
  forbidden-edge removal, placeholder rejection, and Shell parity.
- Update structure, src-layout, public-import, packaging, and wheel contracts
  for recursive lifecycle discovery and installed provenance.
- Re-run shell completion, uninstaller, installer, updater, import-order,
  runtime, Windows, CLI behavior/dispatch, public import, structure, packaging,
  and development-floor scripts.
- Run the mandatory final `python tests/run_cli_baseline.py`,
  `python -m compileall -q .`, `python -m pip check`, changed/new-file Black,
  isort, and Ruff checks, and `git diff --check`.
- Controlled-remote evidence: `not applicable; no remote behavior changes`

### Acceptance Criteria

1. Every moved function has one real lifecycle owner and historical paths
   contain compatibility-only logic with exact, non-growing debt ceilings.
2. Historical symbols, identities, signatures, module-object patch seams, CLI
   behavior, completion lightness, paths, migration, rollback, concurrency,
   uninstall planning/confirmation, pip command, and user-data safety remain
   executable and unchanged.
3. Source/editable-install policy has one owner used by update and uninstall;
   `uninstaller -> release` is removed and cannot return.
4. Python and package-absent Shell cleanup agree on the exact managed manifest,
   regular-file/symlink/concurrency safety, idempotence, and guidance.
5. Structure and artifact contracts discover every nested lifecycle module,
   reject placeholders/unowned code, and agree across source/editable/wheel/
   sdist surfaces.
6. The ledger remains monotonic at `26 capabilities`, at least `96 invariants`,
   and at least `83 isolated pytest cases`.
7. Focused tests, complete offline baseline, supporting gates, and independent
   review pass with no open P0/P1/P2/P3 finding before acceptance or delivery.

### Verification Evidence

- Pre-edit focused evidence: `shell completion 19/19; uninstaller 14/14;
  update 6/6; import order 5/5; structure 13/13; public imports 8/8; src
  layout 6/6; CLI feature baseline 69/69; Windows 12/12; development floor
  15/15; all run offline in atomgit_cli before edits`
- Implementation evidence: `test_environment_lifecycle_ownership.py 18/18;
  shell completion 19/19; uninstaller 14/14; update 6/6; Release workflow
  29/29; installer 17/17; import order 5/5; runtime 9/9; Windows 12/12;
  CLI feature baseline 69/69; public imports 8/8; structure 13/13; src layout
  6/6; development floor 15/15; CLI baseline guard 14/14; packaging metadata
  13/13; wheel/sdist/editable smoke 36/36`
- Complete baseline: `source ... && conda activate atomgit_cli && python
  tests/run_cli_baseline.py -> 83 passed in 85.62s before review, 83 passed in
  86.60s after the review fix, and 83 passed in 88.02s in final maintainer
  self-acceptance (offline isolated pytest matrix)`
- Supporting gates: `python -m compileall -q .`, `python -m pip check`,
  changed/new-file Black, isort, Ruff, and `git diff --check` passed; exact
  legacy tool debt tightened to Black 85 files/627 changes, isort 88/109, Ruff
  19/205; locked huggingface-hub==1.1.7, datasets==4.4.1, Click 8.4.2,
  setuptools 81.0.0 unchanged`
- Review: `APPROVED after one P2 compatibility finding was fixed and the full
  diff was re-reviewed; no open P0/P1/P2/P3 findings`
- Human acceptance: `accepted by the maintainer request on 2026-08-18 to
  self-test, accept, commit, merge, push, and verify when no issues remain`
- Residual risks: `live AtomGit behavior is not exercised because runtime and
  remote semantics are intentionally unchanged; Python 3.9 execution is
  represented by declared/tooling contracts in this Python 3.10 environment;
  package-absent Shell parity is contract-tested but not executed on a second
  POSIX implementation`

### Review Record

- Initial verdict: `REQUEST CHANGES`
- Resolved P2: `the first historical facades forwarded primary callable seams
  but omitted module-object dependencies such as Path/stat/shlex/tempfile and
  spread a few temporary patches beyond their former call sites`
- Resolution: `registered every former module-object dependency, preserved
  direct and patch.object set/delete/restore semantics, and narrowed shared
  policy forwarding to the original completion or uninstall resolution site`
- Re-review verdict: `APPROVED`
- Open findings: `none`

## Maintainer Test Authorization

- Scope: `the ongoing code-structure development work only`
- Sole authorized test repository: `weixin_52273949/test_datasets`
- Web URL: `https://ai.atomgit.com/weixin_52273949/test_datasets`
- Git URL: `git@atomgit.com:weixin_52273949/test_datasets.git`
- Boundary: `do not use any other repository for development testing; do not
  delete, publish, or perform unrelated remote writes; keep credentials out of
  logs and commits`
