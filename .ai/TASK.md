# Current Issue Contract

Status: completed

## Handoff Snapshot

- Updated: `2026-08-18 +0800`
- Phase: `implemented, independently reviewed, committed, merged locally into
  yuto, pushed, and remotely verified`
- Base branch: `yuto`
- Base commit: `e665d62` (`docs(ai): record final packaging delivery sha`)
- Base synchronization before activation: `yuto` and `github/yuto` both
  resolved to `e665d62`
- Task branch: `codex/src-layout-migration` (local only; never push)
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `clean on yuto after delivery`
- Task commit: `1a32130` (`refactor(packaging): migrate modules to src layout`)
- Local yuto merge: `e8b9c54` (`merge: establish src layout migration`)
- Final remote yuto: `pending finalization push`
- Last completed action: `merged the reviewed task commit into yuto; the
  finalization record is being committed before pushing yuto`
- Next exact action: `commit this completed handoff, push yuto, and verify the
  remote SHA`
- Blockers: `none`

## Predecessor Reconciliation

The packaging metadata/discovery Issue was complete before this Issue began.
The previous handoff incorrectly retained `7aac2cf` as its final remote SHA;
the actual synchronized delivery baseline is `e665d62`. No predecessor source
defect was found.

## Active Issue

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
