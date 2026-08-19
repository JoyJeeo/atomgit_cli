# Current Issue Contract

Status: inactive

## Handoff Snapshot

- Updated: `2026-08-19 +0800`
- Phase: `completed, accepted, committed, merged, pushed, and remotely verified`
- Base branch: `yuto`
- Base commit: `7338c99`
- Base synchronization: `yuto`, `github/yuto`, and `github/HEAD` all resolved
  to `7338c99` before branch creation
- Task branch: `codex/api-facade-conversion` (local only; never pushed)
- Current HEAD: `78e6bc9 on yuto before this final delivery-record commit`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `clean after task commit, local no-ff merge, yuto-only pushes,
  and this final delivery-record update`
- Last completed action: `created task commit 4044fdc, merged it locally into
  yuto as 78e6bc9, pushed only yuto, fetched github, and verified local yuto,
  github/yuto, and github/HEAD all resolved to 78e6bc9`
- Next exact action: `none; await an explicit maintainer request before
  activating another Issue`
- Blockers: `none`
- Tests run: `focused API facade 8/8; ownership/structure/src-layout/public
  import/import-order/packaging/artifact gates passed; complete
  python tests/run_cli_baseline.py -> 90 passed in 86.77s (0:01:26); compileall,
  pip check, Black, isort, Ruff, and git diff --check passed`

The predecessor CLI Command Ownership Issue is complete, accepted, committed,
locally merged, pushed, and remotely verified. Its task commit is `6d98b92`,
local merge is `bf0f8f2`, final delivery record is `7338c99`, and local and
remote `yuto` resolved to `7338c99` before this Issue was activated.

## Active Issue

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-REFACTOR-API-FACADE-CONVERSION`
- Title: `Convert the historical API module into a compatibility facade package`
- Primary type: `refactoring`
- Secondary types: `compatibility`, `cli`, `sdk`, `testing`, `security`,
  `distribution`, `documentation`
- Priority: `P2`
- Approved program step: `12. API Facade Conversion`
- Observable objective: `replace src/atomgit/api.py with
  src/atomgit/api/__init__.py as the historical atomgit.api compatibility
  facade after all API business implementations have moved to their owners,
  while preserving every public/private symbol, HuggingFaceAPI and global api
  identity, signature, import order, dependency patch seam, executable entry
  path, artifact surface, and observable CLI/API behavior`
- User impact: `none by design; historical imports and behavior remain stable`

### Authorization And Delivery

- User authorization: `the maintainer approved the complete sequential
  capability-oriented structure program on 2026-08-18; that persisted program
  names API Facade Conversion as step 12 after CLI Command Ownership; on
  2026-08-19 the maintainer explicitly requested continued development`
- Accepted program conditions:
  1. `api.py becomes api/__init__.py only after domain extraction`
  2. `symbols, objects, signatures, runtime behavior, module identity, and old
     patch seams remain stable`
  3. `the facade contains no network, filesystem, retry, transfer, or mutable
     state business implementation`
  4. `CLI facade conversion remains a separate later Issue`
- Authorized local actions: `create a local task branch; edit task-owned
  source, tests, exact registries, packaging contracts, and AI/human
  architecture/testing documents; inspect locked dependencies; build temporary
  artifacts; run offline checks; perform an independent review`
- Standing delivery after completion and acceptance: `one cohesive conventional
  task commit, local --no-ff merge into yuto, and push only yuto; never push
  the task branch`
- Unauthorized actions: `remote Issue/PR creation or transition, task-branch
  push, tag or Release mutation, publication, live AtomGit writes, credential
  mutation, deletion, or upstream main changes`
- Delivery mode: `local task branch -> focused and complete offline
  verification -> independent review -> human acceptance -> cohesive commit ->
  local no-ff merge into yuto -> push only yuto -> verify github/yuto`

### Evidence And Current Behavior

- `src/atomgit/api.py` is an 853-line historical module. Its one concrete
  `HuggingFaceAPI` class is already composed only from authentication,
  repository, download, and upload owner mixins; the global `api` singleton
  retains the historical concrete type and identity.
- Authentication/repository, download, upload, and LFS implementations already
  live in `atomgit.services`, `atomgit.download`, `atomgit.upload`, and
  `atomgit.lfs`. The remaining API module code is compatibility import/export,
  dependency initialization, owner aliasing, and assignment/deletion forwarding.
- Tests patch many historical `atomgit.api` names through direct assignment,
  deletion, and `patch.object`; owner methods must continue resolving those
  exact module-object seams and restoring exact identities.
- `src/atomgit/cli.py` lazily resolves `atomgit.api.api`; `atomgit.__init__`
  exports the same singleton. Completion import lightness and import-order
  behavior are protected.
- `tests/structure_contract.py` currently registers flat `api`, exact
  `atomgit/api.py` wheel/sdist paths, an 853-line facade ceiling, and the
  existing `cli -> api` compatibility edge. These declarations must migrate
  atomically to the package facade and cannot retain stale regrowth room.
- Locked contracts inspected in `atomgit_cli`: Click `8.4.2`,
  `huggingface-hub==1.1.7`, and `datasets==4.4.1`.

### Expected Behavior

- `import atomgit.api`, `from atomgit.api import HuggingFaceAPI, api`, package
  exports, CLI lazy resolution, and clean import permutations resolve the same
  historical module name and exact stable objects.
- `HuggingFaceAPI` remains declared at `atomgit.api`, keeps its exact bases,
  method signatures, behavior, and concrete singleton type; global `api`
  remains the one shared object exported by `atomgit` and used by the CLI.
- Every registered public and private historical symbol remains available with
  the same identity, and assignment/deletion/`patch.object` propagation reaches
  every former owner resolution site and restores exact values.
- Source, default PEP 660 editable, wheel, and sdist discovery contain exactly
  `atomgit/api/__init__.py` and no stale `atomgit/api.py`.
- The API package facade contains only compatibility imports, aliases,
  forwarding metadata/module behavior, the historical class composition, and
  singleton construction; no domain business implementation is introduced.

### Scope

#### In Scope

- Replace the flat API module with the historical API package facade.
- Add focused executable evidence for exact path/provenance, class/singleton
  identity and signatures, symbol inventory, imports, patch propagation,
  facade-only content, artifact discovery, and non-migration boundaries.
- Migrate exact module-owner, dependency-edge, facade-debt, source-layout,
  wheel/sdist, public-import, test-inventory, and development-floor contracts.
- Update the smallest authoritative AI and human architecture/testing
  documentation to describe the delivered package facade.

#### Out Of Scope

- Convert `cli.py`, remove or redesign the CLI's historical `atomgit.api.api`
  dispatch, or change Click schema, commands, callbacks, completion, output,
  prompts, exits, errors, or lazy behavior.
- Move or redesign authentication/repository, download, upload, LFS, SDK,
  infrastructure, lifecycle, distribution, or Shell implementations.
- Change public/private API symbols, method signatures, singleton semantics,
  dependency versions, remote behavior, tokens, Git state, release policy, or
  test layout.
- Add placeholder packages, generic compatibility layers, formatter sweeps,
  live writes, publication, remote Issue/PR work, or upstream changes.

### Affected Capability IDs

- `FLOOR-REGISTRY`, `CLI-SURFACE`, `CLI-DISPATCH`, `AUTH-CONFIG`,
  `REPO-MANAGEMENT`, `REVISION`, `UPLOAD-FILE`, `UPLOAD-FOLDER`,
  `UPLOAD-RESUMABLE`, `UPLOAD-LFS`, `UPLOAD-LFS-RECOVERY`,
  `DOWNLOAD-SNAPSHOT`, `DOWNLOAD-FILE`, `DOWNLOAD-INTEGRITY`,
  `DOWNLOAD-SECURITY`, `REPO-ID`, `RUNTIME`, `CACHE`,
  `DEPENDENCY-CONTRACT`, `PACKAGING`, `PORTABILITY`, and `ERROR-REDACTION`

### Protected Existing Invariants

- All existing `110` invariants remain protected, especially `FLOOR-005..016`,
  `CLI-001..007`, `DISPATCH-001..005`, authentication, repository, revision,
  upload, LFS, download, repository-ID, runtime/global-state, dependency,
  packaging, portability, and redaction invariants.
- Exact imports, symbols, object identities, method/helper signatures, CLI
  dispatch, deterministic interaction, lazy completion, runtime initialization,
  old-path patches, API arguments/results, temporary/state safety, exception
  categories, output, and exit behavior remain unchanged.
- CLI, SDK, service, transfer, LFS, lifecycle, infrastructure, distribution,
  and Shell ownership and observable behavior remain structurally outside this
  Issue.

### New Or Changed Invariants

- `FLOOR-016`: the historical `atomgit.api` path is a package facade with exact
  class, singleton, symbols, signatures, import behavior, owner aliases, and
  assignment/deletion/patch propagation; it contains no business implementation
  and its structure/artifact debt cannot regress to the flat module.
- `PKG-022`: source, default PEP 660 editable, wheel, and sdist surfaces include
  exactly `atomgit/api/__init__.py`, exclude stale `atomgit/api.py`, and retain
  installed-only provenance and both CLI/import entry paths.

### Focused Tests And Evidence

- Add `tests/test_api_facade_conversion.py` for package path/provenance,
  facade-only AST content, exact class/singleton identity and signatures,
  historical symbol inventory, representative assignment/deletion/patch
  propagation across services/download/upload/LFS, CLI lazy use, and CLI facade
  non-migration.
- Update the prior ownership contracts only where their explicit
  `api.py`-must-remain assertions become the newly authorized package facade.
- Rerun exact ownership, structure, source-layout, public-import, import-order,
  CLI schema/dispatch/behavior, packaging, artifact, development-floor,
  dependency, security, global-state, and portability evidence.
- Run final `python tests/run_cli_baseline.py`, `python -m compileall -q .`,
  `python -m pip check`, changed/new-file Black, isort, Ruff, credential scan,
  artifact audit, and `git diff --check`.
- Controlled-remote evidence: `not applicable; observable remote behavior is
  unchanged and live writes are not authorized for this structural migration`.

### Acceptance Criteria

1. The flat `src/atomgit/api.py` is absent and the real
   `src/atomgit/api/__init__.py` compatibility facade is the sole historical
   `atomgit.api` implementation.
2. Historical imports, module/class/singleton identities, public/private
   symbols, method/helper signatures, and package/CLI references remain exact.
3. Direct assignment, deletion, and `patch.object` at `atomgit.api` propagate
   to representative and complete registered owner consumers and restore exact
   identities.
4. The facade contains no network/filesystem/retry/transfer/state business
   implementation; all domain owners and the separate flat CLI module remain
   unchanged except for required compatibility declarations.
5. Structure, source/editable/wheel/sdist, public import, import order,
   completion, exact inventory, and development-floor contracts fail closed on
   stale flat paths, missing package artifacts, regrowth, or seam drift.
6. The ledger remains monotonic at `26 capabilities`, at least `110 invariants`,
   and at least `90 isolated pytest cases`.
7. Focused tests, the complete offline baseline, supporting gates, and an
   independent review pass with no open P0/P1/P2/P3 finding before acceptance.

### Verification Evidence

- Pre-edit complete baseline: `not rerun for this Issue yet; predecessor final
  evidence is 89/89 and this Issue must produce a fresh post-change run`.
- Failing pre-implementation contract: `tests/test_api_facade_conversion.py`
  failed as expected because the flat `api.py` path and package facade were
  absent; the failure established the migration boundary before edits.
- Implementation and focused tests: `API facade 8/8; auth/repository 20/20;
  download 15/15; upload 16/16; LFS 13/13; SDK 18/18; CLI ownership 13/13;
  structure 13/13; src layout 6/6; public imports 8/8; import order 5/5;
  packaging metadata 13/13; wheel/source/editable/sdist smoke 36/36`.
- Complete baseline: `python tests/run_cli_baseline.py -> 90 passed in 86.77s
  (0:01:26) after the final tooling-debt contract fix`.
- Supporting gates: `python -m compileall -q ., python -m pip check, focused
  Black --check, isort --check-only, Ruff, and git diff --check passed; wheel
  and sdist contain the exact API package; no credential or tracked artifact
  found`.
- Independent review: `APPROVED after read-only review of the complete diff,
  package/import/artifact contracts, historical symbol and patch seams,
  locked dependencies, source and human documentation, and final 90-case
  baseline. Review requested stale api.py/108-count documentation corrections;
  those were fixed and the final 90/90 baseline reran successfully. No open
  P0/P1/P2/P3 finding remains`.

### Residual Risks

- Import-system differences between a module and package can affect
  `__spec__`, `__path__`, relative imports, source provenance, and monkeypatch
  behavior even when ordinary imports pass; focused source and installed
  subprocess evidence is required.
- The large historical private-symbol/patch surface is intentional compatibility
  debt; this Issue preserves and makes it fail-closed rather than removing it.
- Live AtomGit behavior will not be retested because the task is a
  behavior-preserving facade migration and remote writes are not authorized.
- Python 3.9 is represented by declared tooling and portability contracts in
  the current Python 3.10 conda environment.
- Human acceptance: `accepted on 2026-08-19 after the final self-test; the
  complete 90-case baseline and all supporting gates passed, authorizing task
  commit, local merge, and yuto-only push`.
- Delivery evidence: `task commit 4044fdc (refactor(api): convert historical
  module to facade package) was merged locally into yuto with --no-ff as
  78e6bc9 (merge: convert api to facade package); only yuto was pushed. After
  fetch, local yuto, github/yuto, and github/HEAD all resolved to 78e6bc9. The
  task branch was never pushed`.
