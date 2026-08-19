# Current Issue Contract

Status: active

## Handoff Snapshot

- Updated: `2026-08-19 13:23 +0800`
- Phase: `self-tested and accepted by maintainer; preparing cohesive task
  commit`
- Base branch: `yuto`
- Base commit: `2c1ef67579bd759ffff6f4c05aeff588a701caab`
- Base synchronization: `yuto`, `github/yuto`, and `github/HEAD` all resolved
  to `2c1ef67` before branch creation
- Task branch: `codex/cli-facade-conversion` (local only; never push)
- Current HEAD: `2c1ef67 on codex/cli-facade-conversion; no task commit yet`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `dirty with this active Issue implementation, tests,
  contracts, packaging declarations, and documentation; continuation must use
  this worktree`
- Last completed action: `maintainer explicitly requested self-test acceptance,
  commit, and push; the final 91/91 baseline, supporting gates, installed
  artifact evidence, and corrected source identity/entry-path acceptance probe
  all pass`
- Next exact action: `create one cohesive conventional task commit, merge it
  locally into yuto with --no-ff, push only yuto, fetch github, and verify all
  yuto pointers`
- Blockers: `none`
- Tests run: `focused CLI facade 7/7; command ownership 13/13; API facade 8/8;
  structure 13/13; src layout 6/6; public imports 8/8; import order 5/5;
  packaging 13/13; SDK ownership 18/18; wheel/source/editable/sdist smoke
  37/37; final static python tests/run_cli_baseline.py -> 91 passed in 78.09s;
  compileall, pip check, Black, isort, Ruff, credential/artifact scans, and git
  diff --check passed`

The predecessor API Facade Conversion Issue is complete, accepted, committed,
locally merged, pushed, and remotely verified. Its task commit is `4044fdc`,
local merge is `78e6bc9`, final delivery record is `2c1ef67`, and local and
remote `yuto` resolved to `2c1ef67` before this Issue was activated.

## Active Issue

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-REFACTOR-CLI-FACADE-CONVERSION`
- Title: `Convert the historical CLI module into a compatibility facade package`
- Primary type: `refactoring`
- Secondary types: `compatibility`, `cli`, `testing`, `distribution`,
  `documentation`
- Priority: `P2`
- Approved program step: `13. CLI Facade Conversion, immediately after step
  12 API Facade Conversion`
- Observable objective: `replace src/atomgit/cli.py with
  src/atomgit/cli/__init__.py as the historical atomgit.cli compatibility
  facade after all command implementations have moved to atomgit.commands,
  while preserving the exact Click tree, callbacks, symbols, module identity,
  lazy dependency and patch seams, completion/import behavior, console and
  Python module entry paths, artifact surface, and observable CLI behavior`
- User impact: `none by design; commands, options, output, exits, completion,
  imports, and executable entry paths remain stable`

### Authorization And Delivery

- User authorization: `the maintainer approved the complete sequential
  capability-oriented structure program on 2026-08-18; the delivered API
  Facade Conversion contract records CLI facade conversion as a separate later
  Issue; on 2026-08-19 the maintainer explicitly requested continued
  development`
- Accepted program conditions:
  1. `cli.py becomes cli/__init__.py only after command ownership extraction`
  2. `Click schema, callbacks, signatures, symbols, objects, runtime behavior,
     module identity, lazy imports, and old patch seams remain stable`
  3. `the facade contains only Click schema, compatibility assembly, thin owner
     delegation, and lazy dependency adapters, not command business work`
  4. `the existing cli -> api compatibility debt is removed without changing
     command behavior; runtime API access stays lazy through the historical
     module object`
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

- `src/atomgit/cli.py` is a 452-line historical module that owns the exact
  Click command/group/option schema, command callbacks, `_COMMAND_CONTEXT`,
  `_LazyObject`, and lazy utility adapters; all real command implementations
  already live in `atomgit.commands`.
- `atomgit.cli.api` is a lazy proxy to `atomgit.api.api`, and utility adapters
  lazily resolve `atomgit.utils`. Becoming a subpackage changes relative import
  depth and would incorrectly resolve `atomgit.cli.api` or
  `atomgit.cli.utils` unless the parent-package resolution is migrated
  explicitly.
- Tests patch many historical `atomgit.cli` names through direct assignment,
  deletion, `patch.object`, and `sys.modules["atomgit.cli"]`; owner callbacks
  must continue receiving that exact module object.
- `setup.py` exposes `atomgit=atomgit.cli:cli`; `atomgit.__main__` and package
  exports import the same Click root. The current flat module is also directly
  executable as `python -m atomgit.cli`, so the package needs an executable
  `cli/__main__.py` adapter to preserve that path.
- `tests/structure_contract.py` registers flat `cli`, exact `atomgit/cli.py`
  wheel/sdist paths, a 452-line facade ceiling, and the remaining forbidden
  `cli -> api.__init__` edge. All must migrate and tighten atomically.
- Locked contracts inspected in `atomgit_cli`: Click `8.4.2`,
  `huggingface-hub==1.1.7`, and `datasets==4.4.1`.

### Expected Behavior

- `import atomgit.cli`, `from atomgit.cli import cli`, package exports, console
  scripts, `python -m atomgit`, and `python -m atomgit.cli` resolve the same
  historical module name and exact Click root object.
- The Click command tree, option order/types/defaults/flags/choices, callback
  identities/signatures, help, completion, dispatch arguments, output, prompts,
  error redaction, and exit codes remain exact.
- `_COMMAND_CONTEXT` remains the `atomgit.cli` package module, owner functions
  resolve historical assignment/deletion/patch seams there, and lazy API and
  utility resolution continues to target `atomgit.api` and `atomgit.utils`.
- Clean import permutations and completion remain lightweight and offline with
  no credential reads, network requests, or eager business imports.
- Source, default PEP 660 editable, wheel, and sdist discovery contain
  `atomgit/cli/__init__.py` and the executable adapter, and exclude stale
  `atomgit/cli.py`.
- The CLI package facade contains only Click schema, compatibility imports,
  lazy adapters, and thin calls to command owners; no authentication,
  repository, transfer, lifecycle, filesystem, network, retry, or mutable-state
  business implementation is introduced.

### Scope

#### In Scope

- Replace the flat CLI module with the historical CLI package facade and retain
  direct module execution through a minimal package `__main__` adapter.
- Add focused executable evidence for exact path/provenance, Click and callback
  identity/signatures, lazy parent resolution, old-path patch seams, facade-only
  content, import/completion behavior, entry paths, and artifact discovery.
- Migrate exact module-owner, dependency-edge, forbidden-edge, facade-debt,
  source-layout, wheel/sdist, public-import, test-inventory, tool-policy, and
  development-floor contracts.
- Update the smallest authoritative AI and human architecture/testing/release
  documentation to describe the delivered package facade.

#### Out Of Scope

- Change Click commands, groups, arguments, options, defaults, output, prompts,
  exits, errors, completion candidates, command owner implementations, or CLI
  API behavior.
- Move or redesign command owners, API/services, transfers, SDK, LFS,
  infrastructure, lifecycle, distribution, configuration, or Shell code.
- Change public/private symbols, callback or SDK signatures, dependency
  versions, remote behavior, tokens, Git state, release policy, or test layout.
- Add placeholder packages, generic compatibility layers, formatter sweeps,
  live writes, publication, remote Issue/PR work, or upstream changes.

### Affected Capability IDs

- `FLOOR-REGISTRY`, `CLI-SURFACE`, `CLI-DISPATCH`, `AUTH-CONFIG`,
  `REPO-MANAGEMENT`, `REVISION`, `UPLOAD-FILE`, `UPLOAD-FOLDER`,
  `UPLOAD-RESUMABLE`, `DOWNLOAD-SNAPSHOT`, `DOWNLOAD-FILE`, `RUNTIME`,
  `DEPENDENCY-CONTRACT`, `PACKAGING`, `PORTABILITY`, and `ERROR-REDACTION`

### Protected Existing Invariants

- All existing `110` invariants remain protected, especially `FLOOR-005..016`,
  `CLI-001..007`, `DISPATCH-001..005`, authentication, repository, revision,
  upload, download, runtime/global-state, dependency, packaging, portability,
  and redaction invariants.
- Exact imports, Click schema, symbols, object identities, callback/helper
  signatures, dispatch, completion, runtime initialization, old-path patches,
  API arguments/results, exception categories, output, and exit behavior remain
  unchanged.
- API, SDK, service, transfer, LFS, lifecycle, infrastructure, distribution,
  Shell, and command-owner boundaries remain structurally outside this Issue.

### New Or Changed Invariants

- `FLOOR-017`: `the historical atomgit.cli path is a package facade with exact
  Click/schema/callback identities, signatures, imports, lazy parent resolution,
  patch seams, and executable entry paths; it contains no business
  implementation and cannot regress to the flat module`
- `PKG-023`: `source, default editable, wheel, and sdist surfaces include the
  exact CLI package facade and executable adapter, exclude stale cli.py, retain
  installed-only provenance, and preserve console plus both Python module entry
  paths`

### Focused Tests And Evidence

- Add `tests/test_cli_facade_conversion.py` for package path/provenance,
  facade-only AST content, exact Click/callback/module identities, lazy API and
  utility parent resolution, historical context and patch seams, console/module
  entries, and API facade non-migration.
- Update prior ownership and API facade contracts only where their explicit
  `cli.py`-must-remain assertions become the newly authorized package facade.
- Rerun exact command ownership, structure, source-layout, public-import,
  import-order, CLI schema/dispatch/behavior, completion, packaging, artifact,
  development-floor, dependency, security, global-state, and portability
  evidence.
- Run final `python tests/run_cli_baseline.py`, `python -m compileall -q .`,
  `python -m pip check`, changed/new-file Black, isort, Ruff, credential scan,
  artifact audit, and `git diff --check`.
- Controlled-remote evidence: `not applicable; observable remote behavior is
  unchanged and live writes are not authorized for this structural migration`.

### Acceptance Criteria

1. The flat `src/atomgit/cli.py` is absent and the real
   `src/atomgit/cli/__init__.py` compatibility facade is the sole historical
   `atomgit.cli` implementation, with a minimal package execution adapter.
2. Historical imports, module/Click/callback identities, symbols, signatures,
   schema, completion, lazy behavior, and package/entry references remain exact.
3. Direct assignment, deletion, and `patch.object` at `atomgit.cli` reach every
   owner category, restore exact values, and lazy API/utility resolution targets
   the parent `atomgit` package rather than nonexistent CLI children.
4. The facade contains no command business implementation; all command owners
   and other domains remain unchanged except required compatibility declarations.
5. Structure, source/editable/wheel/sdist, public import, import order,
   completion, exact inventory, and development-floor contracts fail closed on
   stale flat paths, missing package artifacts, regrowth, or seam drift.
6. The remaining forbidden `cli -> api` structural debt is removed, while the
   runtime API proxy remains lazy and behavior-compatible.
7. The ledger remains monotonic at `26 capabilities`, at least `112 invariants`,
   and at least `91 isolated pytest cases`.
8. Focused tests, the complete offline baseline, supporting gates, and an
   independent review pass with no open P0/P1/P2/P3 finding before acceptance.

### Verification Evidence

- Pre-edit complete baseline: `not rerun for this Issue yet; predecessor final
  evidence is 90/90 and this Issue must produce a fresh post-change run`.
- Failing pre-implementation contract: `tests/test_cli_facade_conversion.py`
  failed as expected because the flat `cli.py` path remained and the package
  facade plus executable adapter were absent.
- Implementation and focused tests: `CLI facade 7/7; command ownership 13/13;
  API facade 8/8; structure 13/13; src layout 6/6; public imports 8/8; import
  order 5/5; packaging metadata 13/13; SDK ownership 18/18; wheel/source/
  editable/sdist smoke 37/37`.
- Complete baseline: `the first full run exposed one stale
  source_texts["cli"] assertion in SDK ownership after 90 other cases passed;
  the assertion was migrated to cli.__init__, its focused 18/18 test passed,
  independent review then found an unregistered cli.__main__ package-self edge;
  the resolver and guard were tightened, and the final static
  python tests/run_cli_baseline.py passed 91/91 in 78.09s`.
- Supporting gates: `python -m compileall -q ., python -m pip check, focused
  Black --check, isort --check-only, Ruff, credential scan, tracked-artifact
  audit, and git diff --check passed; wheel and sdist contain the exact CLI
  package and all three installed entry paths passed`.
- Independent review: `APPROVED after one P2 finding was resolved. The first
  read-only pass found that from . import cli in cli/__main__.py executed
  correctly but was not represented by the structural edge parser. The parser
  now distinguishes package attributes from registered child modules, the
  cli.__main__ -> cli.__init__ edge and fail-closed assertion are exact, and
  focused structure plus the complete baseline passed afterward. The fresh
  review found no open P0/P1/P2/P3 issue`.

### Residual Risks

- Import-system differences between a module and package affect `__spec__`,
  `__path__`, relative imports, `python -m`, source provenance, and monkeypatch
  behavior even when ordinary imports pass; focused source and installed
  subprocess evidence is required.
- Click decorators retain callback objects at import time, so package migration
  must preserve exact schema and callback identities rather than recreate a
  superficially equal command tree elsewhere.
- `python -m atomgit.cli` requires a package `__main__` adapter even though the
  documented entry paths are the console script and `python -m atomgit`.
- Live AtomGit behavior will not be retested because the task is a
  behavior-preserving facade migration and remote writes are not authorized.
- Python 3.9 is represented by declared tooling and portability contracts in
  the current Python 3.10 conda environment.
- Human acceptance: `accepted on 2026-08-19 after the final self-test; the
  maintainer explicitly authorized commit and push`.
- Delivery evidence: `pending`.
