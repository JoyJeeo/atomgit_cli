# Current Issue Contract

Status: active

## Handoff Snapshot

- Updated: `2026-08-18 +0800`
- Phase: `foundation implemented, focused and complete offline verification
  passed, independent review approved, and task branch is ready for delivery`
- Base branch: `yuto`
- Base commit: `18c3f22e7469d43c2cf91eeb435a343897716b45`
- Base synchronization: `yuto`, `github/yuto`, and `github/HEAD` all
  resolved to the base commit before activation
- Task branch: `codex/structure-compatibility-foundation` (local only; never
  push the task branch)
- Current HEAD: `18c3f22e7469d43c2cf91eeb435a343897716b45`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state before this handoff edit: `clean on yuto and synchronized
  with github/yuto`
- Changed paths: `.ai/ARCHITECTURE.md`, `.ai/DEVELOPMENT_FLOOR.md`,
  `.ai/TASK.md`, `.ai/TESTING.md`, `docs/architecture.md`,
  `docs/development_floor.md`, `docs/testing.md`,
  `tests/cli_baseline_contract.py`, `tests/development_floor_contract.py`,
  `tests/structure_contract.py`, `tests/test_global_state_contract.py`,
  `tests/test_hf_api_contract.py`, `tests/test_import_order_contract.py`,
  `tests/test_installer.py`, `tests/test_public_import_contract.py`,
  `tests/test_refactor_behavior_guard.py`, `tests/test_structure_guard.py`, and
  `tests/test_wheel_smoke.py`
- Last completed action: `resolved the independent-review monotonic-debt
  finding, reran the focused structure/development-floor guards, and passed
  the post-review-fix complete 79-case offline baseline`
- Next exact action: `run final supporting checks after this TASK update,
  create the cohesive local task commit, merge it no-ff into yuto, finalize
  this handoff with exact task/merge SHA values, rerun the required final
  checks, commit the delivery record, and push only yuto`
- Blockers: `none for the active foundation Issue`
- Tests run for this Issue: `all required pre-edit focused tests passed;
  changed/new focused tests passed; complete offline baseline passed twice at
  79/79 after implementation and again after the review fix; compileall,
  pip check, and diff check passed before the final TASK update`
- Required continuation worktree while this handoff is uncommitted:
  `/Users/yutaozhang/yuto/codes/atomgit_cli`

## Active Issue

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-REFACTOR-STRUCTURE-COMPATIBILITY-FOUNDATION`
- Title: `Establish behavior-preserving structure and capability ownership
  gates`
- Primary type: `testing`
- Secondary types: `compatibility`, `distribution`, `documentation`,
  `refactoring`
- Priority: `P1`
- Observable objective: `make the complete current 1.1.1 behavior, public
  imports, dependency boundaries, package contents, import ordering, global
  state restoration, and architecture ownership executable blocking contracts
  before any source-layout or domain extraction work begins`
- User impact: `none by design; this Issue adds prevention and evidence so the
  approved structural program cannot silently change existing behavior`

## Authorization And Delivery

- User authorization: `on 2026-08-18 the maintainer approved the complete
  capability-oriented structure program, explicitly accepted the three
  migration conditions below, and requested that the plan be persisted as a
  local development Issue so the next conversation can start implementation`
- Accepted migration conditions:
  1. `the src migration is mechanical and retains the existing module shape`
  2. `domain implementations are extracted incrementally behind the existing
     modules`
  3. `api.py and cli.py become package facades only at the end, in separate
     independently verified Issues`
- Program authorization: `execute the approved program sequentially, one local
  Issue at a time; finish, verify, independently review, merge, and deliver
  each Issue before activating its successor`
- Current-Issue local actions: `edit AI and human development-floor documents,
  add declarative structure and behavior contracts, add or strengthen offline
  tests, update exact baseline and capability registries, inspect locked
  dependency signatures, run offline tests and packaging checks, perform
  independent review, create the cohesive local task commit, merge locally
  into yuto after verification, and push only yuto according to the standing
  maintainer delivery rules`
- Current-Issue production restrictions: `do not move source files, add src/,
  add pyproject.toml, split api.py/cli.py/utils.py, change setup.py, change
  runtime behavior, change CLI/SDK behavior, or create placeholder packages`
- Remote actions authorized for program delivery: `push only the locally
  merged yuto branch after each completed and verified Issue; never push any
  task branch`
- Remote actions not authorized: `GitHub Issue creation or transition, PR
  creation, tag or Release creation/mutation, PyPI/TestPyPI publication, live
  AtomGit repository operations, credential mutation, or upstream main
  changes`
- Delivery mode: `sequential local task branch -> focused and complete offline
  verification -> independent review -> cohesive commit -> local no-ff merge
  into yuto -> push only yuto; then activate the next approved Issue`

## Recovered Repository Facts

- AtomGit CLI version `1.1.1` is published and the source branch is clean at
  the recorded base SHA.
- The pre-Issue executable development floor contained `26` capability IDs,
  `78` observable invariants, and `74` isolated offline pytest cases; the
  implemented foundation contains `26/85/79`.
- The activation mismatch between `.ai/DEVELOPMENT_FLOOR.md`'s old 72/73
  counts and the executable ledger's pre-Issue 78/74 counts was reconciled;
  all authorities now record the delivered 85/79 counts.
- `api.py` has 5,496 lines and owns authentication, repository V5 operations,
  downloads, integrity, manifests, resume, pruning, upload, resumable transfer,
  projection, LFS policies, recovery, error classification, and the public
  `HuggingFaceAPI` facade.
- `utils.py` has 861 lines and mixes validation, output, cache, file
  statistics, download error policy, and Git credential-helper state.
- `cli.py` has 908 lines and combines the exact Click schema, user
  interaction, output/exit conversion, and command dispatch.
- `completion.py`, `uninstaller.py`, `release.py`, `install.sh`, and
  `uninstall.sh` implement the 1.1.1 environment lifecycle and distribution
  contracts.
- The package uses a root mapping in setup.py:
  `packages=['atomgit']`, `package_dir={'atomgit': '.'}`, and
  `py_modules=['atomgit_hub']`.
- The current SDK source participates in package exports and the top-level
  `atomgit_hub` compatibility import. A future src migration must preserve
  both identities without duplicating implementation logic.
- Many tests patch private names through `sys.modules['atomgit.api']` and
  `sys.modules['atomgit.utils']`. A simple re-export does not preserve
  monkeypatch propagation to a new owner module.
- Click completion starts a new process and depends on eager runtime policy plus
  lazy business imports; package or import-order changes can break completion
  without changing command definitions.
- Hugging Face request timeout and progress state are process-global and must
  be restored across success and all failure exits.
- `install.sh` runs before the package exists and `uninstall.sh` has a
  fallback after the package may have been removed. Bootstrap/fallback rules
  may exist in Shell, but they must be generated from or contract-checked
  against authoritative Python policy rather than evolve independently.

## Current And Expected Behavior

### Current

- Current CLI, SDK, lifecycle, distribution, security, dependency, and
  portability behavior is protected by the 26-capability/78-invariant ledger
  and 74-case baseline.
- Exact CLI schema and dispatch are registered, but there is no single
  cross-cutting refactor contract for public imports, deterministic observable
  output, dependency direction, facade growth, source/editable/wheel parity,
  or package discovery.
- Existing domain tests prove many call arguments and state outcomes, but the
  evidence is distributed and does not fail closed on every planned structural
  regression.
- The repository remains a flat root-mapped Python package.

### Expected After This Issue

- Human and executable development-floor counts agree.
- A declarative contract records current and target ownership, allowed
  dependency directions, forbidden imports, public compatibility surfaces,
  legacy debt, and artifact expectations.
- Focused tests fail when a public import disappears, observable CLI behavior
  changes, import order changes runtime policy, completion becomes heavy, a
  global state leaks, a real locked dependency call no longer binds, an
  artifact omits a module, or a new forbidden dependency edge appears.
- Current legacy architecture is explicitly allowed but cannot grow. The gate
  tightens monotonically as debt is removed.
- No product source, runtime behavior, package layout, command, output, SDK
  signature, script, installer, uninstaller, or remote call changes.

## Scope

### In Scope For The Active Foundation Issue

- Correct the stale development-floor count in the smallest authoritative AI
  document and verify all references to current executable counts.
- Add a declarative behavior/structure contract using the repository's
  executable-contract pattern.
- Add a structure guard for ownership, dependency direction, forbidden edges,
  facade restrictions, artifact expectations, and monotonic legacy debt.
- Add a public import contract for source and installed surfaces, including
  package exports, `atomgit_hub`, `HuggingFaceAPI`, global `api`, stable
  exceptions, version, and CLI entry object.
- Add deterministic representative CLI evidence for stdout, stderr, exit
  status, Click exception category, redaction, and downstream calls.
- Add import-order and completion-lightness evidence in clean subprocesses.
- Add or strengthen global timeout/progress/runtime-state restoration evidence.
- Strengthen real locked dependency call-site evidence without permissive
  `**kwargs` fakes.
- Strengthen POSIX installer/uninstaller syntax and fallback-policy parity
  evidence without changing their behavior.
- Register every new test exactly once and map it to affected capabilities and
  invariants.
- Update only the smallest authoritative architecture/testing/development-floor
  documents required for the permanent gate.

### Out Of Scope For The Active Foundation Issue

- `pyproject.toml`, package-discovery changes, dependency changes, or broad
  formatter adoption.
- Creating `src/`, moving production files, or creating target packages.
- Extracting implementation from any production module.
- Converting `api.py`, `cli.py`, or another file into a package.
- Broad reformatting, type-hint sweeps, or logging changes.
- Any CLI schema, output, help, exit, exception, SDK signature, call order,
  retry, timeout, progress, cache, credential, install, update, completion,
  uninstall, Release, or remote behavior change.
- Live tests, Release publication, remote Issue operations, dependency upgrade,
  or upstream integration.

## Behavior-Nonregression Contract

This contract applies to every Issue in the approved program. Each later
`TASK.md` must copy its affected clauses into `Protected Existing
Invariants`.

### CLI Contract

- `EXPECTED_PUBLIC_SCHEMA` remains exact for every command, group, option,
  argument, declaration, type, default, flag, visibility, help behavior, and
  dispatch leaf.
- Both `atomgit` and `python -m atomgit` remain usable.
- Registered deterministic scenarios preserve stdout, stderr, exit code, Click
  exception category, prompt/abort semantics, redaction, and downstream calls.
- `atomgit uninstall` continues to accept only `--yes`.
- Completion show/install/uninstall retains the exact Zsh schema.
- Existing Chinese terminology remains stable and no credential or remote body
  enters output.

### Public Import And SDK Contract

- `import atomgit`, `import atomgit_hub`, `import atomgit.api`,
  `import atomgit.cli`, and `import atomgit.utils` remain valid in source,
  editable, and isolated wheel environments.
- `atomgit.cli:cli`, `HuggingFaceAPI`, global `api`, `__version__`,
  current lazy exports, SDK functions, and public exceptions remain available
  with compatible identities and signatures.
- SDK return values, validation errors, stable exception classes, cause
  preservation, and absence of CLI-only colored output remain unchanged.
- Compatibility is provided at historical paths; no generic compatibility
  dumping-ground package is added.

### External Boundary Contract

- HF Hub, datasets, AtomGit V5, Git, pip, filesystem, subprocess, and network
  calls retain registered arguments, counts, ordering, authentication
  placement, and failure classification.
- Production calls bind against `huggingface-hub==1.1.7` and
  `datasets==4.4.1`; permissive fakes are not compatibility evidence.
- Remote writes gain no generic retry; current ambiguity recovery and
  post-write verification remain operation-specific.
- Configuration and Git helper operations preserve unrelated user state,
  modes, rollback, redaction, and exact-host isolation.

### Upload Contract

- Single-file, ordinary-folder, resumable-folder, model, and dataset routing
  preserve defaults and parameters.
- Ignore rules, macOS metadata exclusions, repo type, revision, prefix, worker,
  1..20 batch range, timeout, progress, and opt-in LFS semantics remain.
- Projection identity, file selection, metadata separation, resource lifetime,
  cleanup, batching, retry/reduction, deadline, and reconciliation remain.
- LFS attributes remain opt-in, concurrency-safe, parent-commit guarded, and
  fail closed on unverified edits.
- LFS pointer bytes remain canonical ASCII v1 ending in one LF, preserve OID
  and size, and are raw-blob verified before success.
- Timeout and progress state restore after success and all tested failures.

### Download Contract

- Anonymous/public and authenticated/private selection, repo-type resolution,
  paths, existing-file policy, force, checksum, resume, manifest, redirect,
  framing, retry, and cleanup remain.
- Traversal, unsafe redirect, credential forwarding, malformed response,
  ambiguous type, symlink/reparse-point, Unicode metadata, and concurrent
  manifest protections remain.
- Prune remains explicit and removes only regular files recorded by the last
  successful whole-repository manifest.
- Failure never replaces a valid destination with unverified partial content
  or exposes credentials.

### Runtime And Import Contract

- `HF_ENDPOINT`, `HF_HUB_DISABLE_XET`, and `HF_HOME` are configured
  idempotently before HF constants are consumed.
- Runtime import does not create the cache directory.
- Supported import orders converge on the same runtime policy.
- Completion loads the live Click schema without HF, datasets, Torch, PyArrow,
  Pandas, business APIs, credentials, network, or config creation.
- Process-global timeout/progress restores for representative CLI and SDK
  success, handled failure, propagated failure, and subprocess boundaries.

### Completion And Environment Lifecycle Contract

- New setup writes no global `~/.zshrc` block or global completion file.
- Exact managed paths remain:
  - `$CONDA_PREFIX/share/atomgit/completions/atomgit.zsh`
  - `$CONDA_PREFIX/etc/conda/activate.d/atomgit-completion.sh`
  - `$CONDA_PREFIX/etc/conda/deactivate.d/atomgit-completion.sh`
- Activation loads only the active environment and deactivation unloads it
  before another environment loads.
- Install/uninstall remains atomic, idempotent, private-mode, symlink-safe,
  exact-path-only, and concurrency-safe.
- Legacy migration requires confirmation and preserves unrelated zshrc bytes,
  mode, backup, newline state, and concurrent edits or rolls back.
- Child commands do not claim to mutate a parent shell and retain the current
  reactivation/`exec zsh` guidance.
- Post-pip activation warning remains exact and non-mutating.

### Uninstall Contract

- CLI displays interpreter, resolved prefix, version, and exact targets before
  confirmation or `--yes`.
- The plan is recomputed before mutation and must equal the displayed plan.
- Pip uses running `sys.executable -m pip uninstall --yes atomgit`.
- Source/editable installs remain rejected.
- Only exact regular files under the matching conda prefix are removed;
  symlink, non-directory, non-regular, mismatch, and concurrent changes fail.
- Configuration, credentials, cache, repositories, unrelated conda files, and
  user files are preserved.
- `uninstall.sh` remains idempotent before and after direct pip removal.
- Non-conda uninstall remains supported.

### Installation, Update, Packaging, And Release Contract

- `install.sh` and `uninstall.sh` remain POSIX `/bin/sh` entrypoints.
- Install/update select only completed strict `X.Y.Z` Releases, validate
  identity, wheel, bounds, redirects, and SHA-256 before pip, and never fall
  back to source or AtomGit on PyPI.
- Non-conda Python 3.9+ installation remains supported.
- Matching conda install/update refreshes only that environment's completion.
- Wheel preserves both CLI entries and both imports, correct metadata, and
  installed-only provenance.
- Build helpers remain build/check/install-only; publication stays manual,
  protected, checksummed, immutable, and secret-free.
- Shell bootstrap/post-removal fallback may exist only when package code is
  unavailable and must be generated from or parity-tested against Python
  policy.

### Portability And Safety Contract

- Python `>=3.9`, Click `8.4.2`, HF Hub `1.1.7`, and datasets `4.4.1`
  remain compatibility contracts.
- New syntax remains Python 3.9 parseable.
- Windows safety remains for cross-platform commands; POSIX scripts do not
  claim Windows support.
- Offline tests never access real credentials, global Git config, user startup
  files, production repositories, or live writes.

## Structure Nonregression Contract

### Ownership And Dependency Direction

Approved final direction:

```text
cli / api facade / sdk
            |
            v
services / transfers / lifecycle / distribution
            |
            v
infrastructure / lfs
```

Allowed special directions:

```text
transfers -> lfs
distribution -> lifecycle
```

Forbidden directions:

```text
services -> cli/api/sdk
transfers -> cli/sdk
lifecycle -> distribution
infrastructure -> services
lfs -> transfers
sdk -> cli
```

- CLI owns Click schema, prompts, output, exit conversion, and service calls.
- SDK owns public parameters, return values, exception conversion, and service
  calls.
- Domain modules do not import Click.
- Infrastructure does not import services, CLI, SDK, or domain orchestration.
- `services` is limited to auth and repository use cases; transfer, LFS,
  lifecycle, and distribution remain explicit vertical domains.
- New modules require a capability owner, immediate production responsibility,
  and executable tests. Empty placeholders are prohibited.
- Shared cross-domain code requires at least two real production callers and a
  shared contract; otherwise it remains in its owner domain.

### Facade Rules

- `atomgit.api`, `atomgit.cli`, `atomgit.utils`, and top-level
  `atomgit_hub` are stable compatibility paths.
- Existing modules remain facades during extraction. No generic
  `compatibility/` package is created.
- Final facades contain only export/dispatch/lazy-import compatibility logic,
  not network, filesystem, retry, transfer, Release, or environment rules.
- Current facade-sized modules are recorded legacy debt. The gate allows the
  baseline but rejects new unowned functions or growth and tightens as debt is
  removed.
- `api.py -> api/__init__.py` and `cli.py -> cli/__init__.py` are separate
  final Issues and never combined with domain extraction.

### Monkeypatch And Test-Seam Rules

- Inventory every affected production import and test patch before extraction.
- Re-export is not proof that assignment through the old module reaches the
  new owner.
- Each patch seam must use an old-path proxy, explicit dependency injection,
  equivalent owner-bound evidence before test migration, or remain unmoved.
- Migrating a private patch target cannot reduce behavior, parameter, call
  order, cleanup, or failure assertions.

### Package Discovery Rules

- Future setuptools discovery includes every intended
  `src/atomgit/**/__init__.py` package.
- A guard compares source modules, build metadata, wheel, and sdist; omitted
  source is blocking.
- Installed smoke runs outside the repo with isolated `PYTHONPATH`.
- Src migration retains flat module identities; domain packages appear only
  when implementation moves.
- Preserving package SDK exports and top-level `atomgit_hub` may require one
  minimal shim in the src Issue. It contains no duplicated SDK logic and is
  proven in source/editable/wheel environments.

### Shell/Python Boundary Rules

- Shell owns environment discovery, forwarding, bootstrap setup, and simple
  orchestration.
- Python owns Release, checksum/wheel validation, environment matching,
  managed-path policy, state planning, and other complex rules when available.
- Pre-install/post-removal fallbacks are explicit exceptions because package
  code may be unavailable; they are generated or parity-tested, not
  independently maintained.
- Root install/uninstall/deploy entrypaths remain stable.

## Affected Capability IDs

- `FLOOR-REGISTRY`
- `CLI-SURFACE`
- `CLI-DISPATCH`
- `RUNTIME`
- `DEPENDENCY-CONTRACT`
- `PACKAGING`
- `PORTABILITY`
- `ERROR-REDACTION`
- Every other capability remains protected by the complete baseline.

## Protected Existing Invariants

- All actual pre-Issue `FLOOR-001` through `FLOOR-003`; the activation
  handoff's reference to a current `FLOOR-004` was reconciled against the
  executable registry, where that ID does not exist.
- All current `CLI-001` through `CLI-005`.
- All current `DISPATCH-001` through `DISPATCH-004`.
- All current `RUNTIME-001` through `RUNTIME-003`.
- Current `DEP-001` and `DEP-002`.
- All current `PKG-001` through `PKG-011`.
- All current `PORT-001` through `PORT-004`.
- All current error-redaction invariants.
- Every remaining invariant in the 78-invariant ledger through the mandatory
  complete baseline. None may be removed, weakened, skipped, or relabeled.

## Proposed New Or Strengthened Invariants

Exact wording may tighten during test-first investigation, but the IDs and
observable intent are approved:

- `FLOOR-005`: refactor Issues cannot change/remove/weaken/skip/relabel
  registered behavior; legacy structure may shrink but new violations fail.
- `CLI-006`: deterministic CLI scenarios preserve exact stdout, stderr, exit,
  exception category, prompt behavior, and redaction.
- `DISPATCH-005`: covered leaves preserve exact target, arguments, count, and
  ordering.
- `RUNTIME-004`: fresh import permutations and completion converge on the
  same light, idempotent HF policy.
- `DEP-003`: representative production call sites bind real locked
  signatures or strict autospecs.
- `PKG-012`: source, editable, wheel, and sdist preserve public imports and
  intended discovered modules without repository leakage.
- `PORT-005`: installer/uninstaller remain POSIX and fallback decisions stay
  aligned with Python policy.
- Strengthen `RUNTIME-002` evidence for representative CLI/SDK success and
  every failure boundary without changing its meaning.

## Focused Test Design

Inspect existing evidence first and avoid duplicate tests. Approved candidates:

- `tests/structure_contract.py`: declarative current/target ownership, public
  surfaces, dependency edges, legacy debt, facade and artifact expectations.
- `tests/test_structure_guard.py`: ownership, forbidden edges/cycles, legacy
  growth, empty/undiscovered packages, and negative mutation evidence.
- `tests/test_refactor_behavior_guard.py`: deterministic CLI
  output/exit/exception/dispatch scenarios.
- `tests/test_public_import_contract.py`: imports, symbols, signatures, lazy
  exports, facade identities, and installed provenance.
- `tests/test_import_order_contract.py`: fresh import permutations and
  completion lightness with isolated HOME/no network.
- `tests/test_global_state_contract.py`: timeout/progress/runtime state around
  representative CLI/SDK success/failure.
- Extend `tests/test_hf_api_contract.py` for production call-site binding.
- Extend installer/uninstaller/portability evidence for POSIX and policy parity
  when possible without script behavior changes.

Five new `test_*.py` scripts move 74 to 79 cases; seven new invariants move 78
to 85. These final exact counts agree in the executable registries and all
authoritative development-floor/testing documents.

## Active-Issue Implementation Sequence

1. Reconcile this contract with exact Git state and executable registries.
2. Run relevant existing focused tests before edits.
3. Correct the pre-Issue stale development-floor counts.
4. Add `tests/structure_contract.py`.
5. Add structure guard and negative mutation evidence first.
6. Add public import and deterministic behavior guards.
7. Add import-order/completion and global-state contracts.
8. Extend locked-signature and POSIX/fallback evidence.
9. Register tests/invariants and update minimal authoritative documents.
10. Run focused tests, full baseline, compileall, pip check, and diff check.
11. Audit credentials, artifacts, behavior, assertions, and unrelated churn.
12. Perform independent review, fix findings, rerun gates, update handoff, and
    deliver under standing rules.

## Acceptance Criteria For The Active Issue

1. Human/executable counts agree and the prior stale statement is removed.
2. Every current module has an owner and the target map is persisted without
   source placeholders.
3. The guard passes legacy state, rejects growth, and proves negative cases.
4. Public imports, symbols, signatures, facade objects, CLI entry, and
   installed provenance are blocking evidence.
5. Deterministic CLI behavior is blocking without duplicated secrets or weaker
   domain tests.
6. Import ordering and completion preserve runtime policy/lightness.
7. Timeout/progress/global state restore across representative boundaries.
8. Production dependency calls bind real locked libraries.
9. POSIX scripts and Shell/Python fallback parity are covered unchanged.
10. New tests are registered once and invariants have evidence/docs.
11. No production, package layout, dependency, CLI/SDK, script, or remote
    behavior changes.
12. Focused/full tests, supporting checks, audits, and review pass with no open
    P0/P1 finding.

## Required Verification For The Active Issue

- Pre-edit focused:
  - `python tests/test_cli_baseline_guard.py`
  - `python tests/test_cli_feature_baseline.py`
  - `python tests/test_development_floor.py`
  - `python tests/test_runtime_policy.py`
  - `python tests/test_hf_api_contract.py`
  - `python tests/test_shell_completion.py`
  - `python tests/test_wheel_smoke.py`
  - `python tests/test_installer.py`
  - `python tests/test_uninstaller.py`
- Post-edit: every new/changed test and all existing evidence it composes.
- Mandatory after final edit and every review fix:
  `python tests/run_cli_baseline.py`.
- Supporting:
  - `python -m compileall -q .`
  - `python -m pip check`
  - `git diff --check`
- Temporary packaging must not alter repository build artifacts.
- Inspect real Click 8.4.2, HF Hub 1.1.7, and datasets 4.4.1 signatures.
- Live AtomGit evidence: `not applicable; no remote behavior changes`.

## Approved Sequential Architecture Program

The program is approved, but only one Issue may be active. Complete, verify,
review, merge, and deliver each before activating its successor from new yuto.

### 1. Structure/Behavior Compatibility Foundation (active)

- Deliver the active Issue above.

### 2. Packaging Metadata And Discovery Foundation

- Add `pyproject.toml` with setuptools backend and deliberate Black/isort/Ruff/
  pytest/package-discovery configuration.
- Retain setup.py and requirements files during migration.
- Record legacy tool debt; block new/changed violations.
- No dependency upgrade, formatter sweep, src tree, or production moves.

### 3. Mechanical Src Layout Migration

- Move current modules to `src/atomgit/` retaining flat module identities.
- Make only required packaging/import adjustments.
- Preserve package SDK exports and top-level `atomgit_hub` with one
  implementation and minimal shim.
- Verify source/editable/wheel/sdist/entrypoints/provenance/import order/
  completion/installer/updater/uninstaller.
- No domain extraction.

### 4. Infrastructure And Utils Ownership

- Extract validation, output, cache, runtime/config support, and Git credential
  ownership.
- Keep `atomgit.utils` as historical facade.
- Preserve patch seams explicitly; no logging/type/format sweep.

### 5. Environment Lifecycle Ownership

- Establish environment, managed paths, completion, and uninstall modules only
  as implementation moves.
- Centralize Python policy and parity-test package-absent Shell fallback.
- Preserve PKG-009..011 paths, migration, concurrency, guidance, confirmation,
  and user-data safety.

### 6. Authentication And Repository Services

- Extract auth and repository use cases.
- Preserve `HuggingFaceAPI` signatures, CLI/SDK differences, V5 size/status/
  ambiguity recovery, visibility, branch, delete, and repo-ID behavior.

### 7. Download Domain

- Create download package with service, transport, integrity, manifest, resume,
  and prune as real code moves.
- Preserve auth, framing, redirects, Windows/path safety, checksum, retry,
  locking, cleanup, and redaction.

### 8. Upload Domain

- Create upload package with service, ordinary, resumable, projection, and
  error policy as real code moves.
- Preserve batching, timeout, progress, lifetime, projection, reconciliation,
  retry/reduction, and CLI/SDK calls.

### 9. LFS Domain

- Establish pointer, policy, and transfer modules.
- Preserve canonical bytes, verification, opt-in attributes, preupload,
  slow-flow recovery, commit reconciliation, concurrency, and scoped behavior.
- Enforce `transfers -> lfs`, never `lfs -> transfers`.

### 10. SDK Ownership

- Establish SDK download/upload/repository/dataset modules.
- Keep top-level `atomgit_hub` thin and preserve exact public behavior.

### 11. CLI Command Ownership

- Extract auth/repository/transfer/lifecycle commands behind existing cli.py.
- Keep only schema, prompt, output, exit conversion, and service calls.
- Preserve completion/lazy import. Do not convert cli.py yet.

### 12. API Facade Conversion

- Convert api.py to api/__init__.py only after domain extraction.
- Preserve symbols, objects, signatures, runtime, module identity, and seams.
- Leave no network/filesystem/retry/transfer/state business implementation.

### 13. CLI Facade Conversion

- Convert cli.py to cli/__init__.py and cli/root.py only after extraction.
- Preserve imports, entrypoint, module execution, completion, schema, dispatch,
  help, output, and seams.

### 14. Distribution Ownership And Shell Thinning

- Establish distribution release/installation ownership.
- Keep root install/uninstall/deploy entrypaths.
- POSIX for install/uninstall; Bash strict mode for deploy only with evidence.
- Generate or parity-test necessary bootstrap/fallback duplication.

### 15. Test Layout Organization

- Move tests into contract/CLI/SDK/auth/repository/upload/download/lifecycle/
  distribution/packaging/Shell areas only after runner/registries support it.
- Preserve self-executing isolated evidence until a separate approved migration.
- Never move production and tests together in one high-risk Issue.

### 16. Documentation And Final Architecture Audit

- Synchronize AI/human architecture, testing, development, ownership, and
  contributor guidance with delivered source.
- Remove transitional statements only after executable proof.
- Audit dependency direction, surfaces, artifacts, credentials, generated
  files, and compatibility debt.
- Never remove a facade/export without a separate authorized migration.

## Approved Final Target Tree

This is a target, not permission for empty packages:

```text
project-root/
|-- pyproject.toml
|-- setup.py
|-- install.sh
|-- uninstall.sh
|-- deploy.sh
|-- scripts/
|   |-- lib/common.sh             # only with two justified callers
|   `-- release_checks.py         # only with real shared policy
|-- src/
|   |-- atomgit/
|   |   |-- __init__.py
|   |   |-- __main__.py
|   |   |-- version.py
|   |   |-- exceptions.py
|   |   |-- cli_contracts.py
|   |   |-- utils.py              # historical facade
|   |   |-- cli/
|   |   |   |-- __init__.py
|   |   |   |-- root.py
|   |   |   |-- auth.py
|   |   |   |-- repository.py
|   |   |   |-- transfer.py
|   |   |   `-- lifecycle.py
|   |   |-- api/
|   |   |   `-- __init__.py
|   |   |-- services/
|   |   |   |-- auth.py
|   |   |   `-- repository.py
|   |   |-- transfers/
|   |   |   |-- download/
|   |   |   |   |-- service.py
|   |   |   |   |-- transport.py
|   |   |   |   |-- integrity.py
|   |   |   |   |-- manifest.py
|   |   |   |   |-- resume.py
|   |   |   |   `-- prune.py
|   |   |   `-- upload/
|   |   |       |-- service.py
|   |   |       |-- ordinary.py
|   |   |       |-- resumable.py
|   |   |       |-- projection.py
|   |   |       `-- errors.py
|   |   |-- lfs/
|   |   |   |-- pointer.py
|   |   |   |-- policy.py
|   |   |   `-- transfer.py
|   |   |-- lifecycle/
|   |   |   |-- environment.py
|   |   |   |-- managed_paths.py
|   |   |   |-- completion.py
|   |   |   `-- uninstall.py
|   |   |-- distribution/
|   |   |   |-- release.py
|   |   |   `-- installation.py
|   |   |-- infrastructure/
|   |   |   |-- runtime.py
|   |   |   |-- config.py
|   |   |   |-- cache.py
|   |   |   |-- output.py
|   |   |   `-- git_credentials.py
|   |   `-- sdk/
|   |       |-- download.py
|   |       |-- upload.py
|   |       |-- repository.py
|   |       `-- dataset.py
|   `-- atomgit_hub.py
|-- tests/
|   |-- contracts/
|   |-- cli/
|   |-- sdk/
|   |-- auth/
|   |-- repository/
|   |-- upload/
|   |-- download/
|   |-- lifecycle/
|   |-- distribution/
|   |-- packaging/
|   `-- shell/
`-- docs/
```

## Future Capability Development Protocol

Every future feature must:

1. classify new versus extended capability;
2. declare affected/protected IDs before editing;
3. select an owner domain;
4. keep CLI/SDK/Shell as adapters rather than duplicate owners;
5. decide whether existing structure can accept it;
6. if not, complete a behavior-neutral preparation Issue first;
7. add failing evidence at the observable boundary;
8. implement in the owner and expose through adapters;
9. update ledger and minimal documentation;
10. pass focused/full tests, review, and delivery gates.

A feature may include only a small local extraction when it affects one domain,
changes no public import/package surface, moves no shared global state, is fully
covered, and is explicitly recorded. Broad moves and behavior never share an
Issue.

## Program-Wide Stop Conditions

Stop and return to implementation when:

- CLI schema/help/output/exit/exception/prompt/dispatch changes;
- a public import/export/signature/facade/entrypoint changes incompatibly;
- artifacts or discovery omit source, or installed smoke leaks repository code;
- a forbidden import edge or cycle appears;
- a facade gains unowned business logic;
- a patch seam no longer reaches the real dependency without equal evidence;
- completion becomes heavy or runtime depends on import order;
- global/environment/cache/credential/temp/Git state leaks;
- locked signatures reject a production call;
- POSIX or Shell/Python parity fails;
- behavior evidence must be weakened to pass;
- focused/full tests, supporting gates, packaging, audit, or review fails.

If existing behavior is wrong, pause refactoring and activate a separate bug or
authorized compatibility-migration Issue.

## Implementation And Verification Evidence

- Implementation: `added the declarative current/target ownership,
  dependency, public-surface, artifact, and exact legacy-debt contract; added
  five focused self-executing guards; strengthened real locked-signature,
  POSIX, wheel, sdist, and PEP 660 editable evidence; changed no production
  module, script behavior, setup metadata, dependency, or package layout`
- Final ledger: `26 stable capabilities, 85 observable invariants, and 79
  isolated offline pytest cases`
- Pre-edit focused evidence: `test_cli_baseline_guard.py 14/14,
  test_cli_feature_baseline.py 69/69, test_development_floor.py 15/15,
  test_runtime_policy.py 9/9, test_hf_api_contract.py 13/13,
  test_shell_completion.py 19/19, test_wheel_smoke.py 28/28,
  test_installer.py passed, and test_uninstaller.py 14/14`
- Post-edit focused evidence: `test_structure_guard.py 13/13,
  test_public_import_contract.py 8/8, test_refactor_behavior_guard.py 6/6,
  test_import_order_contract.py 5/5, test_global_state_contract.py 7/7,
  test_hf_api_contract.py 16/16, test_runtime_policy.py 9/9,
  test_shell_completion.py 19/19, test_installer.py passed,
  test_uninstaller.py 14/14, test_wheel_smoke.py 35/35, and
  test_development_floor.py 15/15`
- Complete offline gate: `python tests/run_cli_baseline.py` passed `79/79` in
  `67.63s` after implementation and `79/79` in `71.26s` after the review fix,
  both in the `atomgit_cli` conda environment`
- Supporting evidence before final handoff edit: `python -m compileall -q .`,
  `python -m pip check`, and `git diff --check` passed; pip reported no broken
  requirements`
- Locked dependency evidence: `huggingface-hub==1.1.7` and
  `datasets==4.4.1` versions and real signatures were inspected; extracted
  CLI/SDK production keyword sets bind successfully and an unsupported kwarg
  fails closed`
- Packaging evidence: `temporary source built one wheel and one sdist; every
  intended runtime module was present; isolated wheel and explicit PEP 660
  editable installs resolved outside the repository and left no build
  artifact in the worktree`
- Live AtomGit evidence: `not run and not applicable because this Issue changes
  no production or remote behavior`
- Human acceptance: `accepted through the maintainer's 2026-08-18 request to
  begin the persisted Issue and perform development, verification, commit, and
  push under the standing delivery rules`

## Review Record

- Design review: `accepted by the maintainer through the 2026-08-17 to
  2026-08-18 discussion, including the target tree, ownership model,
  nonregression contract, anti-degradation gates, Shell fallback exception,
  sequential Issue program, and three mandatory migration conditions`
- Implementation review: `APPROVED after complete-diff review against the
  active Issue, locked signatures, source/tests/docs, supporting checks, and
  the post-fix 79-case complete baseline`
- Resolved finding: `P2 monotonic-debt gap: the first guard allowed removed
  dependency/facade debt to regrow below the original ceiling and did not
  explicitly assert cycle/artifact cross-checks; fixed by requiring exact
  current edges and debt metrics, same-change declaration tightening, and
  dedicated negative cycle, debt-removal, facade-shrink, and wheel-omission
  evidence`
- Open findings: `none; no P0, P1, P2, or P3 finding remains`
- Residual risks:
  - `the exact root-module/artifact registry must be deliberately migrated in
    future approved layout Issues`
  - `representative output snapshots cover selected high-risk branches rather
    than every existing CLI outcome; the complete domain baseline remains the
    broader evidence`
  - `AST analysis recognizes current relative imports and registered lazy
    import helpers, so a new dynamic mechanism requires an explicit guard
    update`
  - `re-export identity and monkeypatch propagation across owner moves`
  - `dual atomgit_hub identities during src migration`
  - `legacy setup.py develop cannot express the current root package mapping
    in a clean environment; isolated editable evidence therefore uses explicit
    setuptools PEP 517/660 until the packaging-metadata Issue modernizes the
    default path`
  - `future import-order and global-state paths beyond the registered
    permutations/failure boundaries require new evidence when introduced`
  - `Shell bootstrap/fallback drift while package code is unavailable`
  - `tool adoption causing unrelated churn`
  - `over-fragmentation, empty packages, generic services, or premature
    abstractions`
