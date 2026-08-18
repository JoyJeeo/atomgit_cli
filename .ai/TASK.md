# Current Issue Contract

Status: inactive

## Handoff Snapshot

- Updated: `2026-08-18 +0800`
- Phase: `completed, accepted, locally merged, pushed, and remotely verified`
- Base branch: `yuto`
- Base commit: `41cdbd76d0ac` (`docs(ai): record src layout delivery`)
- Base synchronization before activation: `yuto` and `github/yuto` both
  resolved to `41cdbd76d0ac`
- Task branch: `codex/infrastructure-utils-ownership` at `dc32679` (local only;
  never pushed)
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `clean on yuto after the final delivery record commit`
- Last completed action: `merged dc32679 into yuto with --no-ff as a67bb8f,
  pushed only yuto, and verified github/yuto at the same merge commit`
- Next exact action: `none for this completed Issue; inspect this handoff and
  activate exactly one approved Issue on the next explicit development request`
- Blockers: `none`

Delivery evidence: task commit `dc32679`; local no-ff merge `a67bb8f`; initial
remote verification resolved `github/yuto` to
`a67bb8f72a051fa3dd0758ca43376813072169f1`. No task branch, tag, release, or
publication was pushed, and no live AtomGit write was performed.

## Predecessor Reconciliation

The compatibility foundation, packaging metadata/discovery, and mechanical
src-layout migration Issues were complete before this Issue began. The current
synchronized delivery baseline is `41cdbd7`; no predecessor source defect was
found.

## Predecessor Issue Record

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-REFACTOR-SRC-LAYOUT-MIGRATION`
- Title: `Mechanical Src Layout Migration`
- Primary type: `compatibility`
- Secondary types: `refactoring`, `distribution`, `testing`, `documentation`
- Priority: `P2`
- Observable objective: `move the existing flat production modules into
  src/atomgit while preserving module shape, public identities, entrypoints,
  runtime behavior, and installed provenance`
- User impact: `no intentional CLI, SDK, dependency, or remote behavior change;
  package discovery is now standard and fail-closed`

### Authorization And Delivery

- User authorization: `the maintainer approved the sequential capability
  program and explicitly opened this next development step on 2026-08-18`
- Accepted migration conditions:
  1. `the move is mechanical and retains the existing monolithic modules`
  2. `atomgit_hub has one implementation under src/atomgit and one minimal
     top-level compatibility proxy`
  3. `api.py and cli.py remain monolithic; no domain extraction or facade
     conversion is included`
- Program rule: `one local Issue at a time; complete, verify, review, merge,
  and deliver it before activating its successor`
- Authorized local actions: `edit source paths, packaging metadata, tests,
  development-floor registries, AI/human architecture/testing docs, build
  temporary artifacts, run offline checks, review, commit, locally merge, and
  push only the merged yuto branch`
- Unauthorized actions: `remote Issue/PR creation or transition, task branch
  push, tag or Release mutation, publication, live AtomGit writes, credential
  mutation, or upstream main changes`
- Delivery mode: `local task branch -> focused offline verification ->
  independent review -> human acceptance -> cohesive commit -> local no-ff
  merge into yuto -> push only yuto -> verify github/yuto`

### Scope

#### In Scope

- Move all current production modules from the repository root into
  `src/atomgit/` without splitting or renaming them.
- Keep the SDK implementation at `src/atomgit/atomgit_hub.py` and retain
  `src/atomgit_hub.py` as a minimal read/write compatibility proxy for the
  historical top-level import.
- Update setuptools package/module discovery, source/sdist artifact checks,
  import-order/completion probes, and installed provenance checks.
- Preserve public imports, signatures, exceptions, globals, Click entrypoints,
  installer/update/uninstaller behavior, and direct and `patch.object`
  monkeypatch seams.
- Register migration-specific structure and packaging invariants and update
  authoritative architecture/testing documentation.

#### Out Of Scope

- Domain/service extraction, module splitting, or package/facade conversion.
- CLI/SDK schema, runtime behavior, dependency, exception, global-state, or
  remote operation changes.
- Dependency upgrades, formatter/lint sweeps, placeholder packages, broad
  test-layout changes, live writes, credential changes, or publication.

### Affected Capability IDs

- `FLOOR-REGISTRY`
- `PACKAGING`
- `PORTABILITY`
- `CLI-SURFACE`
- `RUNTIME`

### Protected Existing Invariants

- `FLOOR-001..006`, `PKG-001..013`, `PORT-001..006`, `CLI-001..006`, and all
  remaining registered invariants remain protected by the complete offline
  gate.
- `import atomgit`, `atomgit.api`, `atomgit.cli`, `atomgit.utils`,
  `atomgit_hub`, and `atomgit.atomgit_hub` remain available with historical
  symbols, signatures, identities, and exception hierarchy.
- Existing `sys.modules` seams, lazy completion imports, global-state
  restoration, installer/update/uninstaller behavior, and exact artifact
  contents remain unchanged except for the intended source prefix.

### New Or Changed Invariants

- `FLOOR-007`: the migration contract fails closed when a production module,
  compatibility proxy, artifact path, or source provenance assertion drifts.
- `PKG-014`: the declared `src` layout discovers exactly the registered package
  modules and one top-level SDK proxy across source, default PEP 660 editable,
  wheel, and sdist surfaces without repository leakage.
- `PORT-007`: supported import orders and completion resolve the same runtime
  policy from the `src` package without heavy imports, user-state creation, or
  root-module fallback.

### Verification Evidence

- Migration contract: `python tests/test_src_layout_migration.py -> 6/6`
- Structure/public imports: `test_structure_guard.py -> 13/13`,
  `test_public_import_contract.py -> 8/8`
- Packaging: `test_packaging_metadata.py -> 13/13`,
  `test_wheel_smoke.py -> 36/36` (source, editable, wheel, sdist, entrypoints,
  provenance, exact module sets)
- Runtime and state: `test_import_order_contract.py -> 5/5`,
  `test_global_state_contract.py -> 7/7`, `test_sdk_upload_timeout.py -> 7/7`
- Workflow and portability: development floor `15/15`, CLI baseline guard
  `14/14`, release workflow `29/29`, installer `17/17`, updater `6/6`,
  uninstaller `14/14`, HF signature contract `16/16`
- Complete mandatory gate: `source ... && conda activate atomgit_cli &&
  python tests/run_cli_baseline.py -> 81 passed in 82.13s`
- Supporting gates: `python -m compileall -q .`, `python -m pip check`, and
  `git diff --check` passed; locked `huggingface-hub==1.1.7` and
  `datasets==4.4.1` remain unchanged
- Controlled-remote evidence: `not applicable; runtime and remote behavior
  were intentionally unchanged; no live AtomGit operation was run`

### Acceptance Criteria

1. All registered production modules live under `src/atomgit`; the root has no
   runtime Python modules and no accidental artifact leakage.
2. `atomgit_hub` has one implementation and one minimal proxy; both historical
   paths preserve symbols, signatures, exceptions, and monkeypatch cleanup.
3. Setuptools source, editable, wheel, and sdist discovery agree exactly and
   exclude tests, docs, `.ai`, build output, and repository leakage.
4. CLI/module entrypoints, completion, installer, updater, and uninstaller
   remain green under the full offline matrix.
5. Development-floor counts remain monotonic at `26 capabilities`, `91
   invariants`, and `81 isolated pytest cases`; no unrelated debt cleanup is
   included.
6. Independent review has no open P0/P1/P2/P3 finding.

### Review Record

- Review phase: `independent read-only review completed; one P2 compatibility
  finding in proxy deletion cleanup was fixed, retested, and re-reviewed`
- Verdict: `APPROVED`
- Residual risks: `Python 3.9 execution is represented by the declared target
  and compatibility contracts; this environment's isolated evidence ran on
  the atomgit_cli interpreter. Live AtomGit behavior is not exercised because
  runtime behavior is intentionally unchanged.`

## Maintainer Test Authorization

- Scope: `the ongoing code-structure development work only`
- Sole authorized test repository: `weixin_52273949/test_datasets`
- Web URL: `https://ai.atomgit.com/weixin_52273949/test_datasets`
- Git URL: `git@atomgit.com:weixin_52273949/test_datasets.git`
- Boundary: `do not use any other repository for development testing; do not
  delete, publish, or perform unrelated remote writes; keep credentials out of
  logs and commits`

## Conversation Handoff

- Current phase: `completed Issue; conversation ending after recording the
  maintainer's repository-only test authorization`
- Worktree: `same shared yuto worktree; dirty only in .ai/TASK.md`
- Uncommitted change: `authorization metadata only; no source, test, packaging,
  or runtime change; no checkpoint commit was created`
- Next action: `on the next explicit development request, resume in this same
  worktree, inspect this handoff, and activate exactly one approved Issue`
- Tests since the last code delivery: `none; authorization metadata only`

## Active Issue

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-REFACTOR-INFRASTRUCTURE-UTILS-OWNERSHIP`
- Title: `Extract infrastructure ownership behind historical utility paths`
- Primary type: `refactoring`
- Secondary types: `compatibility`, `testing`, `security`, `distribution`,
  `documentation`
- Priority: `P2`
- Observable objective: `move validation, output, cache, runtime/config support,
  filesystem support, and Git credential-helper implementation into owned
  infrastructure modules while preserving historical imports, symbols,
  identities, signatures, patch seams, CLI/SDK outcomes, and artifacts`
- User impact: `none by design; internal ownership migration only`

### Authorization And Delivery

- User authorization: `the maintainer approved the sequential capability
  program and explicitly requested continued development and verification on
  2026-08-18`
- Approved program step: `4. Infrastructure And Utils Ownership`
- Accepted conditions:
  1. `implementation moves incrementally into real owner modules`
  2. `atomgit.utils remains the historical compatibility facade`
  3. `old-path direct and module-object patch seams remain effective`
  4. `no lifecycle, service, transfer, LFS, SDK, or CLI domain extraction and no
     api.py or cli.py facade conversion`
- Authorized local actions: `edit task-owned source, tests, registries, AI and
  human docs; inspect locked dependencies; run offline checks and temporary
  package builds; review; commit; and locally merge`
- Authorized remote delivery: `after completion and review, push only the
  locally merged yuto branch and verify github/yuto; never push the task branch`
- Unauthorized actions: `remote Issue/PR creation or transition, task branch
  push, tag or Release mutation, publication, live AtomGit writes, credential
  mutation, deletion, or upstream main changes`
- Delivery mode: `local task branch -> focused and complete offline verification
  -> independent review -> human acceptance -> cohesive conventional commit ->
  local no-ff merge into yuto -> push only yuto -> verify github/yuto`

### Pre-Implementation And Expected Behavior

#### Pre-Implementation Baseline

- `src/atomgit/utils.py` owns validation, output, error categorization, file
  statistics, cache cleanup, prompts, path support, and Git credential helpers.
- `src/atomgit/config.py` and `src/atomgit/runtime.py` own configuration and HF
  runtime policy at historical package paths.
- `api.py`, `atomgit_hub.py`, and lazy CLI callbacks consume these paths; tests
  patch `atomgit.utils.os.walk`, `atomgit.utils.subprocess.run`, private helper
  names, `atomgit.config.os`, and the shared `config` object.

#### Expected

- Real implementation lives in non-placeholder `atomgit.infrastructure`
  modules for validation, output, filesystem, cache, Git credentials, config,
  and runtime.
- `atomgit.utils`, `atomgit.config`, and `atomgit.runtime` remain thin historical
  facades with compatible symbols, signatures, identities, and patch seams.
- Source, default editable, wheel, and sdist discovery include every delivered
  nested module exactly without repository leakage; structure debt tightens in
  the same change.

### Scope

#### In Scope

- Add only infrastructure modules that receive real implementation in this
  Issue; no placeholders.
- Move utility validation/error policy, output/prompt, filesystem/statistics,
  cache cleanup, Git credential/helper functions, config, and runtime policy to
  explicit owners.
- Preserve old-path imports, shared `os`/`subprocess` patching, private helper
  compatibility tests, CLI lazy resolution, config singleton state, import
  order, completion lightness, rollback, file modes, and Windows/POSIX outcomes.
- Extend exact ownership, dependency, artifact, source-layout, import, and
  development-floor contracts and update the smallest authoritative docs.

#### Out Of Scope

- Environment lifecycle, completion, uninstall, authentication, repository
  service, download, upload, LFS, SDK, or CLI command extraction.
- `api.py`/`cli.py` package or facade conversion; public behavior, dependencies,
  exceptions, logging/type/format sweeps, test-layout changes, live operations,
  publication, and unrelated debt cleanup.

### Affected Capability IDs

- `FLOOR-REGISTRY`, `CLI-SURFACE`, `AUTH-CONFIG`, `GIT-CREDENTIAL`,
  `UPLOAD-FILE`, `UPLOAD-FOLDER`, `DOWNLOAD-SNAPSHOT`, `REPO-ID`, `RUNTIME`,
  `CACHE`, `PACKAGING`, `PORTABILITY`, `ERROR-REDACTION`

### Protected Existing Invariants

- All predecessor `91` invariants remain protected, especially `FLOOR-005..007`,
  `CLI-003/006`, `AUTH-001..003`, `GITCRED-001..002`, `UPFILE-003`,
  `UPFOLDER-001..002`, `DLSNAP-001..003`, `REPOID-001..002`, `RUNTIME-001..004`,
  `CACHE-001..002`, `PKG-001/012..014`, `PORT-001/002/007`, and `REDACT-001..002`.
- Historical imports/symbols at `atomgit.utils`, `atomgit.config`, and
  `atomgit.runtime`, `sys.modules` access, lazy callbacks, shared singleton,
  cache/credential safety, error redaction, and locked HF/datasets/Click
  contracts remain unchanged.

### New Or Changed Invariants

- `FLOOR-008`: infrastructure implementations have exact owners while
  historical utility/config/runtime paths remain thin and preserve registered
  symbols, identities, and patch seams; ownership drift, facade regrowth, and
  placeholders fail closed.
- `PKG-015`: source, default PEP 660 editable, wheel, and sdist surfaces include
  exactly the delivered nested infrastructure modules and historical facades
  without repository leakage.

### Focused Tests And Evidence

- New `tests/test_infrastructure_utils_ownership.py` covers implementation
  provenance, ownership/facade negative cases, historical symbols and
  identities, direct/private patch seams, config/runtime behavior, and
  placeholder rejection.
- Update structure, src-layout, public-import, packaging, and wheel contracts
  for nested module discovery and installed provenance.
- Re-run existing auth/config, Git credential, cache, repo-ID, upload
  validation, output, import-order, runtime, Windows, and global-state scripts.
- Mandatory final `python tests/run_cli_baseline.py`, `python -m compileall -q .`,
  `python -m pip check`, changed/new-file tool checks, and `git diff --check`.
- Controlled-remote evidence: `not applicable; no remote behavior changes`

### Pre-Edit Evidence

- `test_structure_guard.py -> 13/13`; `test_public_import_contract.py -> 8/8`;
  `test_global_state_contract.py -> 7/7`
- `python tests/run_cli_baseline.py -> 81 passed in 85.67s`
- Installed: `huggingface-hub 1.1.7`, `datasets 4.4.1`, Click `8.4.2`,
  setuptools `81.0.0`

### Acceptance Criteria

1. Every moved function has one real infrastructure owner and historical paths
   contain compatibility-only logic with exact debt ceilings.
2. Historical symbols, signatures, shared objects, patch seams, CLI/SDK
   behavior, config/runtime policy, rollback, cache safety, and redaction remain
   executable and unchanged.
3. Structure and artifact contracts discover every nested module, reject
   placeholders/unowned code, and agree across source/editable/wheel/sdist.
4. The ledger remains monotonic at `26 capabilities`, at least `93 invariants`,
   and at least `82 isolated pytest cases`.
5. Focused tests, complete offline baseline, supporting gates, and independent
   review pass with no open P0/P1/P2/P3 finding.

### Verification Evidence

- Implementation: `src/atomgit/infrastructure/{validation,output,filesystem,cache,git_credentials,config,runtime,utils}.py` with thin historical `atomgit.utils`, `atomgit.config`, and `atomgit.runtime` facades; setup metadata and exact recursive contracts updated.
- Focused tests: `test_infrastructure_utils_ownership.py -> 17/17`, `test_structure_guard.py -> 13/13`, `test_src_layout_migration.py -> 6/6`, `test_public_import_contract.py -> 8/8`, `test_import_order_contract.py -> 5/5`, `test_packaging_metadata.py -> 13/13`, `test_wheel_smoke.py -> 36/36`, `test_git_credentials_isolation.py -> 33/33`, `test_windows_compatibility.py -> 12/12`, `test_config_permissions.py -> 15/15`, `test_runtime_policy.py -> 9/9`, and `test_repo_id_contract.py -> 68/68`.
- Complete baseline: `source ... && conda activate atomgit_cli && python tests/run_cli_baseline.py -> 82 passed in 87.76s` in the final maintainer-authorized acceptance run after the module-object patch-seam, exact facade debt, and tightened Black debt-contract fixes. A preceding post-whitespace-cleanup run failed at `81 passed, 1 failed` because the exact Black debt digest was stale; the Issue remained active, the debt contract was monotonically tightened from 637 to 633 changes, and the complete gate then passed.
- Supporting gates: `python -m compileall -q .`, `python -m pip check`, changed/new-file Black/isort/Ruff checks, and `git diff --check` passed; locked `huggingface-hub==1.1.7`, `datasets==4.4.1`, and Click `8.4.2` remain unchanged.
- Review: `completed read-only review; no P0/P1/P2/P3 findings`
- Human acceptance: `accepted on 2026-08-18; maintainer explicitly requested
  self-testing, acceptance, commit, and push after the verified result`

## Review Record

- Review phase: `independent read-only review completed after final fix`
- Verdict: `APPROVED`
- Open findings: `none recorded`
- Residual risks: `Python 3.9 is represented by declared/tooling contracts in
  this environment; live AtomGit behavior is not exercised because runtime and
  remote semantics are intentionally unchanged.`
