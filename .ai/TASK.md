# Current Issue Contract

Status: completed

## Handoff Snapshot

- Updated: `2026-08-18 +0800`
- Phase: `implemented, independently reviewed, committed, merged locally into
  yuto, pushed, and remotely verified`
- Base branch: `yuto`
- Base commit: `c64e264` (`docs(ai): finalize structure compatibility
  foundation`)
- Base synchronization: `yuto`, `github/yuto`, and `github/HEAD` all resolved
  to `c64e264` before activation
- Task branch: `codex/packaging-metadata-discovery` (local only; never push the
  task branch)
- Task commit: `2a5696e` (`test(packaging): establish metadata and tooling
  gates`)
- Local yuto merge: `555b278` (`merge: establish packaging metadata gates`)
- Final remote yuto: `7aac2cf` (`docs(ai): finalize packaging metadata handoff`)
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state before activation: `clean`
- Changed paths: `.ai/ARCHITECTURE.md`, `.ai/DEVELOPMENT_FLOOR.md`,
  `.ai/TASK.md`, `.ai/TESTING.md`, `docs/architecture.md`,
  `docs/development_floor.md`, `docs/testing.md`, `pyproject.toml`,
  `pytest.ini` (removed after exact pytest-policy consolidation),
  `requirements-dev.txt`, `setup.py`, `tests/cli_baseline_contract.py`,
  `tests/development_floor_contract.py`, `tests/packaging_contract.py`,
  `tests/test_packaging_metadata.py`, and `tests/test_wheel_smoke.py`
- Last completed action: `pushed yuto at 555b278 and verified github/yuto;
  implemented the packaging metadata/tooling contract,
  fixed PEP 517 setup path resolution, removed pytest.ini after proving exact
  collection parity, tightened wheel/sdist exact artifact checks, and passed
  the complete offline baseline`
- Next exact action: `activate the next approved program Issue separately from
  the delivered yuto HEAD; do not infer or implement it from this completed
  handoff`
- Blockers: `none`
- Tests run: `focused structure 13/13, public imports 8/8, packaging metadata
  12/12, wheel/sdist/editable smoke 36/36 after review fix, development floor
  15/15, CLI baseline guard 14/14, release workflow 29/29, installer 17/17,
  updater 6/6, uninstaller 14/14; complete offline baseline 80/80 in 83.75s
  after the final review fix; compileall, pip check, Black, isort, Ruff, and
  diff check passed in the atomgit_cli environment`

## Active Issue

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-REFACTOR-PACKAGING-METADATA-DISCOVERY`
- Title: `Establish packaging metadata, discovery, and tooling gates`
- Primary type: `distribution`
- Secondary types: `compatibility`, `testing`, `refactoring`, `documentation`
- Priority: `P1`
- Observable objective: `make the build backend, current root package mapping,
  artifact discovery, Python target, pytest collection, and incremental
  formatting/lint policy explicit and executable before the mechanical src
  layout migration`
- User impact: `none by design; runtime, CLI, SDK, import, artifact, installer,
  updater, uninstaller, and remote behavior remain unchanged`

## Authorization And Delivery

- User authorization: `the maintainer approved the complete capability-oriented
  structure program on 2026-08-18 and opened this new conversation to begin the
  next development step`
- Accepted migration conditions:
  1. `the src migration is mechanical and retains the existing module shape`
  2. `domain implementations are extracted incrementally behind the existing
     modules`
  3. `api.py and cli.py become package facades only at the end, in separate
     independently verified Issues`
- Program rule: `execute one local Issue at a time; finish, verify,
  independently review, merge, and deliver it before activating its successor`
- Authorized local actions: `edit packaging/tool configuration, tests,
  development-floor registries, AI/human documentation, and the persistent
  handoff; inspect installed tools and locked dependencies; add required
  development-only tooling with bounded versions; build temporary artifacts;
  run offline tests; review; commit; and merge locally`
- Authorized remote delivery: `after completion and review, push only the
  locally merged yuto branch; never push the task branch`
- Unauthorized remote actions: `remote Issue/PR creation or transition, task
  branch push, tag or Release mutation, PyPI/TestPyPI publication, live AtomGit
  writes, credential mutation, or upstream main changes`
- Delivery mode: `local task branch -> focused and complete offline
  verification -> independent review -> cohesive conventional commit -> local
  no-ff merge into yuto -> push only yuto -> verify github/yuto`

## Recovered Repository Facts

- The predecessor delivered a clean behavior/structure foundation with `26`
  capabilities, `85` invariants, and `79` isolated offline pytest cases.
- Packaging currently depends on `setup.py` with
  `packages=['atomgit']`, `package_dir={'atomgit': '.'}`, and
  `py_modules=['atomgit_hub']`; there is no `pyproject.toml`.
- `pytest.ini` currently declares `testpaths=tests`,
  `python_files=pytest_*.py`, and `addopts=-ra`.
- `requirements-dev.txt` contains build, pytest, tomli-for-Python-below-3.11,
  and wheel requirements; Black, isort, and Ruff are not installed or declared.
- The active environment has setuptools `81.0.0`, build `1.5.0`, wheel
  `0.47.0`, pytest `8.3.5`, Click `8.4.2`, huggingface-hub `1.1.7`, and
  datasets `4.4.1`.
- Existing source and tests contain formatting/lint debt. This Issue must
  declare that debt monotonically without a formatter sweep or weakening the
  future default for new files.
- The explicit PEP 660 editable smoke currently needs `--use-pep517` because
  the repository lacks a build-system declaration.

## Current And Expected Behavior

### Current

- setuptools is selected implicitly through `setup.py`.
- The unusual root-to-`atomgit` package mapping is executable but not declared
  in modern build metadata.
- pytest collection policy lives only in `pytest.ini`.
- Black/isort/Ruff have no repository policy or executable debt ceiling.
- Wheel, sdist, editable, imports, entrypoints, and installed provenance pass
  the existing isolated packaging smoke.

### Expected

- `pyproject.toml` explicitly selects `setuptools.build_meta`, the supported
  Python target, current root package mapping, top-level `atomgit_hub`, and
  exact artifact discovery policy without moving source.
- Pytest configuration is centralized without changing isolated test
  inventory or the repository's self-executing test convention.
- Black, isort, and Ruff use deliberate Python 3.9-compatible configuration.
- Existing tool debt is recorded as an exact monotonic baseline: it may shrink
  only with a same-change contract update and may never grow silently.
- Default `pip install -e .` uses PEP 517/660 from the declared build system.
- `setup.py`, requirements files, root source layout, metadata values,
  artifacts, public imports, entrypoints, and all observable behavior remain.

## Scope

### In Scope

- Add `pyproject.toml` with setuptools build-system and current explicit
  package/module selection.
- Configure Black, isort, Ruff, and pytest for Python 3.9 and the repository's
  intentional test naming/inventory convention.
- Add bounded development-only tool requirements required by executable gates.
- Add a focused self-executing contract for metadata consistency, default
  editable installation, discovery fail-closed behavior, and exact legacy
  formatting/lint debt.
- Strengthen wheel/sdist/editable evidence where needed to prove the new
  default path and setup.py/pyproject agreement.
- Register every new test exactly once and map new invariants to affected
  capabilities.
- Update only the smallest authoritative packaging/testing/architecture docs.

### Out Of Scope

- Creating `src/`, moving or renaming any production module, or changing public
  module identity.
- Domain extraction or changes to `api.py`, `cli.py`, `utils.py`, lifecycle,
  transfer, LFS, SDK, or Shell implementation.
- Removing `setup.py`, requirements files, `pytest.ini`, or compatibility
  entrypoints unless an exact no-behavior-change consolidation is proven.
- Runtime dependency upgrades or changes to locked HF/datasets contracts.
- Whole-file or repository-wide Black/isort/Ruff rewrites.
- CLI/SDK schema, output, exit, signature, exception, call ordering, global
  state, installer, updater, uninstaller, Release, or remote behavior changes.
- Live tests, remote writes, publication, or upstream integration.

## Affected Capability IDs

- `FLOOR-REGISTRY`: register and fail closed on the new permanent metadata and
  tool-debt evidence.
- `PACKAGING`: build backend, package/module selection, artifact contents,
  editable installation, entrypoints, and provenance.
- `PORTABILITY`: Python 3.9 target and tool parsing/configuration.
- `CLI-SURFACE`: installed console and module entrypoints must remain exact.

## Protected Existing Invariants

- `FLOOR-001..005`
- `PKG-001..012`
- `PORT-001..005`
- `CLI-001..003`
- All remaining registered invariants remain protected by the mandatory
  complete offline gate; none may be removed, skipped, weakened, or relabeled.

## New Or Changed Invariants

- `FLOOR-006` (new): `Build/tool metadata and exact legacy debt are executable,
  internally consistent, and fail closed when configuration or debt drifts.`
- `PKG-013` (new): `The declared setuptools backend and explicit current
  package/module selection produce identical source, default editable, wheel,
  and sdist surfaces without repository leakage.`
- `PORT-006` (new): `Black, isort, Ruff, setuptools, and pytest configuration
  share the Python 3.9 floor; legacy violations cannot grow and new files use
  the clean default.`
- No existing invariant statement changes.

## Focused Test Design

- Pre-edit evidence already passed:
  - `python tests/test_structure_guard.py`
  - `python tests/test_public_import_contract.py`
  - `python tests/test_wheel_smoke.py`
  - `python tests/test_development_floor.py`
- Add `tests/test_packaging_metadata.py` as a self-executing focused contract.
- The first focused run must fail because `pyproject.toml` and tool policy do
  not yet exist.
- Prove exact build backend, package/module selection, setup.py agreement,
  Python target, pytest collection, tool configuration, debt non-growth,
  negative discovery cases, default editable installation, and no repository
  artifact change.
- Post-edit rerun the new test plus structure, public-import, wheel,
  development-floor, release workflow, installer, updater, and uninstaller
  evidence affected by packaging.
- Mandatory after the final edit and every review fix:
  `python tests/run_cli_baseline.py`.
- Supporting: `python -m compileall -q .`, `python -m pip check`, tool checks,
  and `git diff --check`.
- Live AtomGit evidence: `not applicable; no runtime or remote behavior change`.

## Acceptance Criteria

1. `pyproject.toml` is valid on Python 3.9+ and explicitly declares the
   setuptools backend and exact current package/module selection.
2. Setup metadata and pyproject declarations cannot drift silently.
3. Default offline wheel, sdist, and PEP 660 editable builds retain all
   historical imports, symbols, entrypoints, metadata, and installed-only
   provenance.
4. Package discovery excludes tests, `.ai`, docs, temporary/build output, and
   any accidental new root directory.
5. Black/isort/Ruff/pytest policies are deliberate, Python 3.9-compatible, and
   executable; exact legacy debt cannot grow.
6. No source module, dependency behavior, CLI/SDK behavior, script behavior,
   or public compatibility surface changes.
7. Development-floor counts, mappings, inventories, and authoritative docs
   agree; focused and complete offline gates pass.
8. Independent review has no open P0/P1/P2/P3 finding before delivery.

## Remaining Approved Program

This Issue is step 2 of the approved sequential program. Later steps remain
inactive and are not authorized concurrently: mechanical src layout migration;
infrastructure/utils ownership; lifecycle ownership; auth/repository services;
download; upload; LFS; SDK ownership; CLI command ownership; API facade
conversion; CLI facade conversion; distribution/Shell ownership; test layout;
and final documentation/architecture audit.

## Implementation And Verification Evidence

- Implementation: `added pyproject.toml build/project/tool/test policy,
  bounded development tools, exact metadata/discovery and debt contracts,
  setup.py PEP 517 path safety, pytest consolidation, and exact artifact checks`
- Final ledger: `26 capabilities, 88 invariants, and 80 isolated offline cases`
- Focused evidence: `packaging metadata 12/12; wheel/sdist/editable smoke
  36/36; structure 13/13; public imports 8/8; development floor 15/15; CLI
  baseline guard 14/14; release workflow, installer, updater, and uninstaller
  all passed`
- Complete offline gate: `python tests/run_cli_baseline.py -> 80 passed in
  83.75s after the independent-review fix`
- Supporting evidence: `python -m compileall -q ., python -m pip check,
  Black/isort/Ruff clean-policy checks, and git diff --check passed`
- Locked dependency evidence: `huggingface-hub==1.1.7 and datasets==4.4.1
  remain installed and production signatures are unchanged`
- Packaging evidence: `temporary wheel and sdist build; exact runtime Python
  module sets; no atomgit/setup.py leakage; isolated wheel CLI/import smoke;
  default PEP 660 editable smoke; sdist includes pyproject.toml; repository
  artifacts unchanged by the smoke`
- Live AtomGit evidence: `not run and not applicable`
- Human acceptance: `the maintainer's 2026-08-18 request to begin the next
  approved program Issue and deliver it under the standing local merge/push
  rules authorizes this completed, reviewed delivery`

## Review Record

- Review phase: `independent read-only review completed after one focused fix`
- Verdict: `APPROVED`
- Findings: `P2 sdist metadata evidence gap fixed by asserting MANIFEST.in,
  pyproject.toml, and setup.py presence; all required gates reran and passed`
- Delivery: `task branch remained local-only; yuto was merged no-ff and pushed;
  github/yuto matched 555b278 before this finalization commit`
- Residual risks to assess:
  - `setuptools behavior for the unusual root package mapping`
  - `setup.py and pyproject metadata drift during the later src migration`
  - `tool-version changes altering the exact legacy-debt baseline`
  - `new files escaping formatting/lint coverage through exclusions`
  - `editable imports accidentally resolving from the repository or base
    environment instead of the isolated source`
