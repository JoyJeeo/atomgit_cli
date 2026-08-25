# Current Issue Contract

Status: active (R7 non-destructive migration complete; paused at WP-06 deletion gate)

## Handoff Snapshot

- Updated: `2026-08-25`
- Phase: `R7 WP-00 through WP-05 complete; WP-06 compatibility cutover and physical-absence proof complete; exact old-directory deletion awaits separate maintainer confirmation`
- Base branch: `yuto`
- Base commit: `23c6d7d merge: close lifecycle facade ownership`
- Task branch: `codex/r7-seven-directory-physical-closure` (pre-deletion checkpoint push explicitly authorized on `2026-08-25`)
- Historical closure: R1-R6 architecture and ownership packages were delivered; their physical source-tree outcome does not satisfy the maintainer's newly clarified seven-directory requirement
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `the pre-deletion checkpoint contains only R7 owner migration, compatibility cutover, contracts, packaging, documentation, tests, and handoff edits; no credentials or generated artifacts`
- Last completed action: `registered deletion-safe historical package aliases, proved all historical imports and python -m atomgit.cli in a temporary source copy with the nine old directories absent, and reran packaging plus the complete offline baseline`
- Next exact action: `request the separate WP-06 confirmation to delete exactly api, cli, commands, download, lfs, lifecycle, sdk, services, and upload under src/atomgit; after approval remove their on-disk owner/artifact declarations, retain runtime aliases, and run the final 92-case gate`
- Blockers: `the separate destructive old-directory deletion gate, merge into yuto, yuto push, and live remote operations remain unauthorized; the maintainer separately authorized one pre-deletion checkpoint commit and current task-branch push`
- Tests for this phase so far: `pre-change baseline 92/92; CLI ownership 13/13; CLI facade 9/9; API facade 8/8; auth/repository ownership 25/25; download ownership 20/20; upload ownership 17/17; LFS ownership 14/14; SDK ownership 20/20; lifecycle ownership 26/26; import-order 5/5; shell completion 19/19; packaging metadata 13/13; wheel/editable smoke 37/37; temporary seven-directory import/module probe passed; final complete baseline 90/92 with only the intentional physical-layout failures; python -m compileall -q ., python -m pip check, and git diff --check pass`
- Residual risk: `src/atomgit still has 16 first-level directories because the nine exact deletion targets remain present; the mandatory baseline cannot pass 92/92 until the separately authorized deletion and artifact-contract cleanup occur`

### WP-00/WP-01 Evidence

- Authorization: `the maintainer explicitly authorized implementation in the current conversation`
- Frozen canonical directories: `adapters`, `compatibility`, `core`, `domain`, `infrastructure`, `interfaces`, `usecases`
- Frozen root Python compatibility allowlist: `__init__.py`, `__main__.py`, `api.py`, `atomgit_hub.py`, `cli.py`, `cli_contracts.py`, `completion.py`, `config.py`, `exceptions.py`, `lfs_pointer.py`, `release.py`, `runtime.py`, `uninstaller.py`, `utils.py`, `version.py`
- Current physical delta: `legacy first-level directories api, cli, commands, download, lfs, lifecycle, sdk, services, and upload remain and are the only physical-layout contract failures`
- Contract changes: `tests/structure_contract.py`, `tests/test_src_layout_migration.py`, and `tests/test_structure_guard.py` now fail closed on an eighth directory or an unlisted root Python file; ARCH-004 is registered in the development-floor ledger
- Verification: `python tests/test_development_floor.py` passed 15/15; pre-change `python tests/run_cli_baseline.py` passed 92/92; focused physical-layout checks fail only on the known legacy directories

### WP-02 CLI Slice Evidence

- Canonical owner: `src/atomgit/interfaces/cli/commands/{authentication,lifecycle,repositories,transfers}.py`
- Compatibility surface: `src/atomgit/commands/*.py` dynamically aliases canonical modules and preserves historical module identities and patch seams
- Lazy boundary: `src/atomgit/interfaces/cli/__init__.py` exposes only a deferred `run`; native adapters now live in `interfaces/cli/runner.py`, keeping completion schema paths free of Hugging Face imports
- Packaging: `pyproject.toml`, `setup.py`, source-layout, structure ownership, wheel, and sdist contracts include the new nested interface package
- Remaining risk: `api`, `cli`, `download`, `lfs`, `lifecycle`, `sdk`, `services`, `upload`, and compatibility `commands` directory still physically exist until later migration slices and the separately authorized deletion gate

### WP-02 SDK And Facade Cutover Evidence

- Canonical SDK owners: `adapters.sdk_common`, `sdk_datasets`, `sdk_downloads`, `sdk_errors`, `sdk_repositories`, and `sdk_uploads`; every `sdk/*` module is a compatibility alias
- Canonical API/CLI assembly: `compatibility.api` and `compatibility.cli`; frozen root `api.py` and `cli.py` shims preserve imports and module execution, while the old package directories contain deletion-pending aliases/proxies
- Compatibility proof: SDK ownership 20/20, API facade 8/8, CLI facade 9/9, CLI command ownership 13/13, public imports 8/8, and import-order 5/5

### WP-03 Authentication And Repository Evidence

- Canonical owners: `compatibility.authentication`, `compatibility.repositories`, and `adapters.atomgit_v5`; `services/*` contains aliases only and no services ownership domain remains
- Locked dependency evidence: installed `huggingface_hub==1.1.7` `create_repo` and `HfApi.__init__` signatures match every changed call site
- Verification: authentication/repository ownership 25/25 and API facade 8/8

### WP-04 Transfer Evidence

- Canonical owners: `adapters.download`, `compatibility.download`, `adapters.upload`, `adapters.lfs`, and `adapters.sdk_uploads`; historical download/upload/LFS modules contain aliases only
- Upload defaults now have one `core.contracts` authority and are forwarded by adapter/root compatibility contracts
- Verification: download ownership 20/20, upload ownership 17/17, LFS ownership 14/14, packaging metadata 13/13, and wheel/editable smoke 37/37

### WP-05 Lifecycle Evidence

- Canonical owners: `infrastructure.completion`, `environment`, `managed_paths`, `uninstall`, and `release`; `lifecycle/*`, root completion/uninstaller, and release paths preserve identities and patch seams through compatibility forwarding
- Verification: lifecycle ownership 26/26, shell completion 19/19, uninstaller 14/14, release/update focused suites, import-order 5/5, packaging 13/13, and wheel/editable smoke 37/37

### WP-06 Non-Destructive Cutover Evidence

- `compatibility.legacy_packages` registers historical commands/download/LFS/lifecycle/SDK/services/upload packages and child modules directly against canonical owners during normal imports without loading them on completion-only paths
- A temporary source copy containing only the seven canonical directories and frozen root Python shims passed all representative historical imports and `python -m atomgit.cli --help`
- The real tree intentionally retains the nine exact old directories until separate deletion confirmation; `test_src_layout_migration.py` is 8/9 and `test_structure_guard.py` is 14/15 solely for that physical delta

## Pending Issue

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-R7-SEVEN-DIRECTORY-PHYSICAL-CLOSURE`
- Title: `Migrate the source tree to exactly seven responsibility directories without losing existing capabilities`
- Primary type: `refactoring`
- Secondary types: `architecture`, `compatibility`, `cli`, `sdk`, `testing`, `packaging`, `documentation`, `portability`
- Priority: `P1`
- Status: `active; implementation explicitly authorized by the maintainer in the current conversation`
- Delivery: `read-only inventory -> explicit implementation activation -> focused migration slices -> complete offline verification -> independent review -> human acceptance -> separately authorized old-directory deletion -> final verification -> separately authorized commit/merge/push`

### Objective

Make the physical source layout under `src/atomgit` converge to exactly these
seven first-level responsibility directories and no others:

```text
src/atomgit/
├── core/
├── domain/
├── usecases/
├── interfaces/
├── adapters/
├── compatibility/
└── infrastructure/
```

These are the permanent architecture standard for all future CLI and SDK
development. New business or technical implementation must be added under one
of these seven directories according to its layer; historical paths may remain
only as explicitly listed root-level `.py` entry shims or as runtime aliases
registered by `compatibility`, never as additional first-level directories.

The migration is behavior-preserving. Existing user-visible capabilities must
not be removed; their implementation is moved to the appropriate canonical
layer, while public CLI/SDK/API entry behavior remains available through the
new interfaces and compatibility conversion.

### Current Evidence And Problem Statement

- The current tree still has 16 first-level directories under `src/atomgit`;
  the nine noncanonical directories contain deletion-pending aliases/proxies.
- Canonical implementation ownership has moved into the seven target
  directories, and legacy services, SDK, lifecycle, transfer, command, API,
  and CLI paths no longer own business implementation.
- `tests/test_src_layout_migration.py` and `tests/test_structure_guard.py` now
  enforce the exact seven-directory allowlist and are the only failing baseline
  cases before the separately authorized physical deletion.
- The prior R1-R6 packages proved runtime ownership and compatibility slices,
  but did not satisfy this newly clarified physical layout requirement.

### User Impact

No intended loss of existing capability. Preserve the CLI schema, defaults,
Chinese output, prompts, progress, exits, public SDK/API functions, signatures,
returns, error categories, package entry paths, token safety, temporary-resource
lifetime, global-state restoration, and supported upload/download/repository/
lifecycle behavior. Physical module identity may change where required by the
strict seven-directory target; any public or tested private path that cannot be
preserved must be reported before deletion rather than silently broken.

### Affected Capability IDs

`FLOOR-REGISTRY`, `ARCHITECTURE`, `CLI-SURFACE`, `CLI-DISPATCH`, `AUTH-CONFIG`,
`GIT-CREDENTIAL`, `REPO-MANAGEMENT`, `REVISION`, `UPLOAD-FILE`, `UPLOAD-FOLDER`,
`UPLOAD-RESUMABLE`, `UPLOAD-LFS`, `UPLOAD-LFS-RECOVERY`, `DOWNLOAD-SNAPSHOT`,
`DOWNLOAD-FILE`, `DOWNLOAD-INTEGRITY`, `DOWNLOAD-SECURITY`, `SDK-DOWNLOAD`,
`SDK-UPLOAD`, `SDK-REPO`, `REPO-ID`, `RUNTIME`, `CACHE`, `PACKAGING`,
`PORTABILITY`, `DEPENDENCY-CONTRACT`, `ERROR-REDACTION`.

### Protected Existing Invariants

- CLI command names, options, defaults, output, prompts, progress behavior,
  callback identities, exit codes, and both Python/console entry paths remain
  compatible.
- Public imports and symbols from `atomgit`, `atomgit.api`, `atomgit.cli`,
  `atomgit_hub`, completion, uninstall, and legacy HF-style SDK functions keep
  their signatures, primary returns, exception mapping, and patch behavior.
- Shared usecase routing, repository/revision/type/token policies, upload/LFS
  pointer verification, download checksum/resume/prune/path safety, release and
  lifecycle state restoration, and locked HF Hub/datasets call signatures remain
  unchanged.
- No token, signed URL, secret-bearing cause, generated artifact, or real
  credential content enters source, tests, documentation, logs, or handoff.

### New Or Changed Invariants

- `src/atomgit` contains exactly seven first-level directories listed above;
  any eighth directory fails the structure gate.
- Every production `.py` file belongs to one of the seven directories or to an
  explicit, finite root-file compatibility allowlist; unlisted files fail
  source-layout, packaging, and artifact checks.
- `core`, `domain`, `usecases`, `interfaces`, `adapters`, and `infrastructure`
  contain canonical implementation only; `compatibility` contains historical
  path/signature/identity/patch conversion only and no business orchestration.
- All future CLI and SDK capability work enters through `interfaces`, shared
  `usecases`, `domain`, `core`, `adapters`, and `infrastructure`; no new
  implementation may be added to a historical root shim.
- Existing public capabilities remain reachable after physical directory
  removal; compatibility tests compare observable behavior and canonical owner
  identity rather than requiring legacy directory identity.
- Structure, source-layout, package artifact, import, and ownership tests fail
  closed on legacy directory reintroduction, duplicate implementations, stale
  artifact declarations, unowned files, forbidden edges, or facade business
  logic.

### Layer Responsibilities

- `core/`: stable contracts, ports, errors, policies, parity and shared
  low-level invariants; no Click, HF, V5, or concrete transport calls.
- `domain/`: pure authentication, repository, transfer, revision, and success
  rules; no UI, filesystem side effects, or concrete network calls.
- `usecases/`: ordered business workflows, reconciliation, rollback, and final
  state verification; no printing or process exits.
- `interfaces/`: CLI presentation/Click dispatch and native SDK request/result
  mapping; no duplicated remote business rules.
- `adapters/`: HF 1.1.7, AtomGit V5, upload/download/LFS transport, filesystem,
  checksum, manifest, cache, and other external technical boundaries.
- `compatibility/`: historical imports, signatures, defaults, returns,
  exception conversion, identities, and patch seams; no new implementation.
- `infrastructure/`: configuration, credentials persistence, runtime state,
  filesystem facilities, Git helpers, completion, installation, update,
  uninstall, and distribution/lifecycle technical facilities.

### Migration Map

The following is the required default destination map. WP-00 may refine a
specific file's destination only with a recorded owner rationale; it may not
create another first-level directory.

| Current path | Canonical destination | Required treatment |
|---|---|---|
| `commands/` | `interfaces/cli/` | Move Click command implementations and presentation; keep no business owner here. |
| `sdk/` | `interfaces/sdk/` plus `compatibility/` | Native SDK mapping belongs in `interfaces/sdk`; legacy HF-style conversion belongs in `compatibility`. |
| `download/` | `adapters/download/` plus `compatibility/` | Move technical download behavior to adapters; preserve public legacy conversion without the old directory. |
| `upload/` | `adapters/upload/` plus `compatibility/` | Move ordinary/resumable/projection/error behavior to adapters; preserve old calls through compatibility. |
| `lfs/`, `lfs_pointer.py` | `adapters/lfs/` plus `compatibility/` | Move protocol, pointer, attributes, and recovery ownership to adapters. |
| `services/` | `domain/`, `usecases/`, `adapters/`, `compatibility/` | Split rules, orchestration, V5 transport, and historical wrappers by layer; no services owner remains. |
| `lifecycle/` | `infrastructure/` | Move completion, environment, managed paths, uninstall, and installation provenance. |
| `api/` | `compatibility/` plus an approved root shim | Keep `HuggingFaceAPI` and singleton compatibility assembly only; implementation resolves to canonical owners. |
| `cli/` | `interfaces/cli/` plus an approved root shim | Keep Click schema/module execution compatibility while implementation lives in the interface layer. |
| `atomgit_hub.py` | `compatibility/` plus the top-level package shim | Keep the existing top-level SDK entry, forwarding only to canonical owners. |
| `release.py` | `infrastructure/release.py` plus an approved root shim | Preserve historical release imports and patch seams while infrastructure owns behavior. |
| root `config.py`, `runtime.py`, `utils.py`, `completion.py`, `uninstaller.py`, `version.py`, `exceptions.py`, `cli_contracts.py` | `infrastructure/`, `core/`, or `interfaces/cli/` by responsibility | Move implementation first; retain only explicitly approved root shims required by public imports. |

### Compatibility And Root-File Rules

- Public compatibility is defined by observable imports, symbols, signatures,
  returns, errors, entry paths, and documented patch seams, not by retaining an
  old directory.
- The root `.py` allowlist must be frozen during WP-00 after auditing public
  imports, console/module entry paths, packaging, and lazy-import behavior. No
  generic or unbounded shim set is permitted.
- The draft allowlist must explicitly account for `atomgit`, `python -m atomgit`,
  `python -m atomgit.cli`, the console script, `atomgit.api`, `atomgit_hub`,
  completion/uninstall/config/utils imports, and any release or pointer path
  proven public by tests or documentation.
- Private paths such as `atomgit.download.service`, `atomgit.upload.service`,
  `atomgit.lfs.service`, `atomgit.services.repositories`, `atomgit.sdk.uploads`,
  and `atomgit.cli.__main__` must be inventoried. Preserve them only when a
  strict seven-directory layout permits a real alias; otherwise report the
  exact path, callers, and break risk before deletion.
- No compatibility shim may import heavy HF dependencies on schema-only paths,
  contain a second implementation, or grow without an owner and test.

### Work Packages And Authorization Gates

Only one package may be active at a time.

1. **WP-00: read-only inventory and migration freeze**. Record every current
   file, import, public/private path, owner, caller, test, artifact, and root
   shim candidate. Produce the final seven-directory map and root-file allowlist.
   This package does not edit source and is the next action after implementation
   is explicitly activated.
2. **WP-01: executable physical-layout contract**. Add/update the exact
   first-level directory allowlist, root-file allowlist, owner map, dependency
   edges, duplicate-definition checks, and wheel/sdist expectations. Register
   every new test in the development floor and baseline inventory.
3. **WP-02: interface and compatibility migration**. Move command and SDK
   presentation/mapping code into `interfaces`; build compatibility conversion
   and patch-seam registration without changing observable behavior.
4. **WP-03: authentication and repository migration**. Split old services into
   domain rules, usecase orchestration, V5 adapters, infrastructure config/Git,
   and compatibility wrappers. Re-run focused ownership and behavior suites.
5. **WP-04: download, upload, and LFS migration**. Move all technical transfer
   code to adapters, preserve request keywords, temporary lifetimes, global
   state, checksums, resume/prune, pointer verification, and legacy conversions.
6. **WP-05: lifecycle and distribution migration**. Move completion, uninstall,
   runtime, release, and installation facilities to infrastructure and verify
   console/module entry behavior.
7. **WP-06: compatibility cutover and old-directory deletion**. First prove all
   capabilities and artifacts pass with the old directories unused. Then stop
   and request the separate destructive deletion confirmation. Delete only the
   exact old-directory targets approved by the migration map; do not use broad
   recursive deletion.
8. **WP-07: final gate and handoff**. Run the complete offline baseline and all
   structural, import, packaging, installed-entry, security, portability,
   compile, dependency, and diff checks; obtain independent review and human
   acceptance. Commit, merge, and push remain separate authorizations.

### Focused Tests And Evidence

- Add a fail-closed physical-tree test that compares actual first-level
  directories and root files with the frozen allowlists.
- Update `tests/structure_contract.py`, `tests/test_structure_guard.py`,
  `tests/test_src_layout_migration.py`, packaging contracts, and artifact tests
  so legacy directories cannot be accepted merely because they are registered.
- Add AST/import tests for one canonical owner per implementation, no duplicate
  business definitions, no direct external calls from interfaces/domain, no
  compatibility business orchestration, and no future legacy-directory growth.
- Preserve and extend CLI schema/dispatch, public import/signature/identity,
  patch/lazy-import, upload/LFS, download, lifecycle, dependency-signature,
  security, source/editable/wheel/sdist, and installed-entry regressions.
- Every new `test_*.py` must be registered exactly once in the development-floor
  ledger and `tests/run_cli_baseline.py` inventory.
- Required final offline commands, in the `atomgit_cli` environment:
  `python tests/run_cli_baseline.py`, `python -m compileall -q .`,
  `python -m pip check`, and `git diff --check`; run applicable Black, isort,
  Ruff, artifact/credential scans, and package smoke tests.
- Live repository operations, credential mutation, publication, and remote
  writes are not part of this Issue unless separately authorized.

### Out Of Scope

- New CLI/SDK product capabilities, dependency upgrades, broad formatting debt,
  publication, or unrelated roadmap work.
- Silent removal of public behavior or private paths without the WP-00 audit and
  maintainer decision.
- Remote repository creation/deletion, live upload/download, credential helper
  mutation, remote Issue/PR changes, commit, merge, or push without separate
  authorization.

### Acceptance Criteria

The Issue cannot close until all of the following are true:

1. The actual `src/atomgit` tree contains exactly the seven target directories,
   and every root `.py` file is on the approved finite allowlist.
2. All old first-level directories are removed only after the separate deletion
   gate, and no production import or package artifact depends on them.
3. Every existing capability has one canonical owner in the seven-layer model;
   compatibility contains forwarding/conversion only.
4. Public CLI, SDK/API, entry, signature, return, exception, patch, security,
   temporary-resource, global-state, packaging, and locked-dependency contracts
   pass focused regressions and the complete baseline.
5. Structure and artifact tests fail closed on an eighth directory, an unlisted
   root file, a duplicate implementation, a stale path, or a new legacy owner.
6. `.ai/ARCHITECTURE.md`, `docs/architecture.md`, the development-floor ledger,
   and this handoff describe the verified current tree rather than the former
   transitional layout.
7. Compile, dependency, diff, packaging, installed-entry, security,
   portability, independent review, and human acceptance gates pass; remaining
   unrun remote evidence is recorded explicitly.

### Authorization And Handoff

- The maintainer authorized the seven-directory target, capability-preserving
  migration, physical identity changes where necessary, replacement of stale
  structure/packaging/documentation contracts, and eventual old-directory
  removal as the scope of this Issue.
- Implementation start was explicitly authorized; WP-00 through WP-05 and the
  non-destructive WP-06 compatibility cutover are complete.
- Old-directory deletion requires a separate explicit confirmation immediately
  before WP-06; resolve the exact targets from the approved migration map.
- The maintainer explicitly authorized one pre-deletion checkpoint commit and
  push of the current task branch on `2026-08-25`. Local merge, `yuto` push,
  remote Issue/PR changes, publication, credential mutation, and live remote
  tests still require separate explicit authorization.
- A future AI taking over must read `AGENTS.md`, `.ai/README.md`, this Issue,
  `.ai/ARCHITECTURE.md`, `.ai/DEVELOPMENT_FLOOR.md`, `.ai/DEVELOPMENT_RULES.md`,
  `.ai/DOD.md`, and `.ai/WORKFLOW.md`; verify Git/worktree state; report the
  recovered objective and blockers; then request the separate deletion
  confirmation before changing any of the nine exact old-directory targets.

## Historical Completed Issue: R6 Lifecycle Facade Closure

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-R6-LIFECYCLE-FACADE-CLOSURE`
- Title: `Move release/update technical ownership behind infrastructure while preserving the historical facade`
- Primary type: `refactoring`
- Secondary types: `architecture`, `compatibility`, `cli`, `sdk`, `testing`, `packaging`, `documentation`
- Priority: `P1`
- Delivery: `local implementation -> focused/full offline verification -> independent review -> human acceptance; commit, merge, push, and remote writes remain unauthorized`

### Objective

Make `infrastructure.release` the canonical technical owner of release/update
validation, bounded downloads, installation, and post-install verification.
Keep historical `atomgit.release` as a compatibility facade with the exact
existing exports, identities, signatures, returns, errors, and monkeypatch
seams. The migration must preserve CLI update behavior and package artifacts.

### User Impact

No intended user-visible behavior change. Existing update/uninstall/completion
commands, release helper imports, signatures, error categories, temporary
resource lifetime, bounded network behavior, and package entry points remain
exact.

### Affected Capability IDs

`FLOOR-REGISTRY`, `ARCHITECTURE`, `CLI-DISPATCH`, `RUNTIME`, `PACKAGING`,
`PORTABILITY`, `ERROR-REDACTION`.

### Protected Existing Invariants

- CLI schema, defaults, Chinese output, exit codes, and callback identities
  remain unchanged.
- Historical `atomgit.release` imports, symbol identities, signatures, return
  values, errors, assignment/deletion patch propagation, and lazy imports
  remain unchanged.
- Release validation, bounded response/asset sizes, redirect origin policy,
  temporary wheel lifetime, subprocess ordering, and source/editable install
  detection remain unchanged.

### New Or Changed Invariants

- `infrastructure.release` is the sole technical owner of release/update
  behavior; historical `atomgit.release` contains only forwarding and seam
  registration.
- Structure and ownership tests fail closed if release business definitions or
  direct release transport calls return to the historical facade.

### In Scope

- release owner module, historical facade/export/patch-seam forwarding, owner
  and dependency contracts, packaging/artifact declarations, focused offline
  regressions, architecture documentation, complete baseline, DoD checks, and
  independent review.

### Out Of Scope

- new release features or public parameter changes;
- upload/LFS behavior, dependency upgrades, broad formatting, or publication;
- live upload, repository/branch creation or deletion, credential mutation,
  publication, remote Issue/PR actions, commit, merge, or push.

### Focused Tests And Evidence

- fail-closed release owner/facade and lifecycle tests;
- release workflow, installer, structure, packaging, and installed artifact
  suites;
- `python tests/run_cli_baseline.py`, `python -m compileall -q .`,
  `python -m pip check`, formatting/static debt audit, and `git diff --check`.

### Acceptance Criteria

1. `infrastructure.release` owns all release/update technical behavior.
2. `atomgit.release` preserves every registered identity, signature, return,
   error, lazy-import, assignment/deletion, and monkeypatch seam.
3. Lifecycle, packaging, artifact, and security contracts pass the focused and
   complete offline suites.
4. Structure gates fail closed on facade business logic, forbidden dependency
   edges, missing owners, or stale artifacts.
5. Architecture and durable task evidence match the source and Git state;
   independent review has no open blocking finding before acceptance.

### Authorization

The maintainer's explicit `继续按照本地开发 issue 进行开发` request activates
this local R6 package. Commit, merge, push, remote Issue/PR changes, live
remote operations, credential changes, release, and publication remain
unauthorized.

### Complete Baseline Evidence

`python tests/run_cli_baseline.py` passed 92/92 in 86.06s in the `atomgit_cli`
environment (offline). Compileall, pip check, diff check, packaging metadata,
source-layout, wheel/sdist, structure, import-order, completion, lifecycle and
release ownership, dependency signature, and public import checks passed. No
live release download/publication or credential mutation was run.

### Independent Review

`APPROVED` on 2026-08-25. Independent review of the R6 diff found no open
P0/P1/P2/P3 findings. Review covered release owner edges, historical module
identity and patch propagation, module execution compatibility, source/editable/
wheel/sdist artifacts, security/state behavior, and the complete offline
evidence.

### R6 Exit-Gate Evidence

- `infrastructure.release` owns release/update validation, bounded asset
  transport, installation, and post-install verification; `atomgit.release`
  is a forwarding facade with preserved identities and patch seams.
- Structure, lifecycle ownership, source-layout, packaging, release workflow,
  deploy, public import, and complete baseline checks passed.
- Residual risk: release downloads/publication and remote update behavior remain
intentionally unrun; no credentials or remote state were changed.

### Human Acceptance And Delivery

Human acceptance and explicit commit/push authorization were granted in the
current conversation. Authorized delivery is one cohesive local task commit,
local no-ff merge into `yuto`, push of `yuto`, and remote equality verification.
The task branch remains local-only; no live release operation, credential
mutation, remote Issue/PR change, or publication is authorized.

### R5 Exit-Gate Evidence

- Canonical owners: `adapters.upload`, `adapters.lfs`, and
  `adapters.sdk_uploads`; historical `upload/`, `lfs/`, `lfs_pointer.py`, and
  `sdk/uploads.py` are import aliases with preserved identity and patch seams.
- Contracts updated: structure, packaging/source artifact, HF 1.1.7 call-site
  binding, upload/LFS/SDK ownership tests, and architecture documentation.
- Installation evidence: wheel/sdist smoke passed 37/37 in isolated venvs;
  completion/import-order remains free of Hugging Face imports on schema-only
  paths.
- Residual risk: controlled remote upload, resumable recovery, and LFS remote
  state/checksum evidence remain intentionally unrun; R6 is out of scope.

### Review Disposition

Human acceptance was granted by the maintainer's explicit request to commit
and push the completed R5 work. Delivery evidence is task commit `51d7410`,
merge commit `097a5bb`, and remote `github/yuto` verified at
`097a5bb1f507adac346bfad60bcc5fb198b80e46`. The task branch was not pushed;
no remote Issue transition, credential mutation, publication, or live remote
operation was performed.

### Corrective Work Package Status

| Package | Status | Scope boundary |
|---|---|---|
| `R0` evidence recovery and acceptance re-audit | `completed` | read-only reconciliation; identified P1 gaps; no source edits |
| `R1` executable architecture and call-path contract | `completed` | importable and invocation-level route checks; deliberate legacy bypass fixture fails closed |
| `R2` CLI shared-usecase wiring | `completed` | authentication, repository, upload, and download CLI paths use shared usecases; baseline and review passed |
| `R3` authentication/repository owner migration | `completed` | adapter owner, compatibility seams, focused evidence, baseline, and independent review passed |
| `R4` download owner migration | `completed` | unify CLI/native SDK download path, integrity, resume, prune, and repo policy |
| `R5` upload/LFS owner migration | `completed` | canonical adapter ownership, compatibility seams, offline gate, review, acceptance, and delivery completed |
| `R6` lifecycle and compatibility closure | `pending` | make compatibility the sole historical facade and place technical owners correctly |
| `R7` final gate, independent review, and human acceptance | `completed` | verified original intent, updated docs/evidence, and delivered the Issue |

Only one row may become `in_progress`; a later row cannot change status until
the preceding row has an exit-gate result recorded below or in a later durable
handoff. R0 is complete because the re-audit and baseline evidence are recorded;
R1 is complete because its invocation finding was fixed and its bypass fixture
fails closed; R2 is complete because its compatibility gate and independent
review passed; R3 is complete because its owner migration, baseline, and
independent review passed; R4 is complete because its technical owner migration,
compatibility regressions, final baseline, and independent review passed. Human
acceptance was granted before delivery and Issue closure.
Human acceptance for R3 was granted on 2026-08-24 with the instruction to
continue development; R4 was accepted in the current delivery request. No new
feature Issue may start without explicit activation after this corrective Issue.

### R1 Exit-Gate Evidence

- `src/atomgit/core/parity.py` now exposes `RUNTIME_ROUTE_REGISTRY` and
  `validate_runtime_routes()`, resolving every parity-required usecase, declared
  usecase method, CLI owner, and native SDK callable.
- `tests/test_architecture_parity.py` proves the complete registry, missing-route
  rejection, non-importable-route rejection, and legacy-bypass rejection; the
  focused script passes 18/18.
- The gate is intentionally limited to executable route declarations. It does not
  claim adapter technical ownership has already migrated; CLI adapters still
  delegate to historical API owners and that migration is assigned to R3.

### R1 Independent Review And Resolution

- Initial verdict: `REQUEST CHANGES`; resolved by the R2 implementation below,
  with a fresh review still required before R2 acceptance.
- `P1` resolution: `validate_runtime_routes()` now inspects CLI callback source
  for the registered `context.run_usecase()` operation and SDK source for its
  corresponding usecase delegate; a deliberate legacy owner fixture fails closed.
- `P1` runtime resolution: production command owners call the shared bridge;
  adapters remain legacy-backed by design for R2 and are the R3 boundary.
- `P2` mitigation: route operation/delegate contracts are executable and tested;
  remaining technical-owner duplication is explicitly tracked for R3.

### R2 Exit-Gate Evidence

- CLI authentication, repository, upload, and download command owners now call
  `context.run_usecase(...)`; the bridge preserves historical context patch
  seams while routing through `AtomGitClient` and the shared usecases.
- Upload request validation preserves `message`, worker count, and whether
  `repo_type` was explicitly supplied; focused regressions pass 16/16,
  17/17, and 49/49 for file, repo-type, and resumable behavior.
- Structural and ownership gates pass: `test_structure_guard.py` 14/14,
  `test_lfs_domain_ownership.py` 13/13, and packaging metadata 13/13.
- `python tests/run_cli_baseline.py` passes 92/92 isolated cases after the
  final fix; `compileall`, `pip check`, `git diff --check`, Black, and isort
  checks also pass. No live remote write or credential mutation was run.

### R2 Independent Review

- Verdict: `APPROVED` for the R2 package.
- Findings: no open P0/P1/P2/P3 findings within the R2 scope. The historical
  API-backed adapter ownership is intentional and remains the explicit R3
  migration boundary, not an R2 acceptance gap.
- Residual review risk: technical-owner duplication and controlled remote
  behavior remain unverified until R3 and authorized remote testing.

### R3 Authentication/Repository Owner Migration Evidence

- `src/atomgit/adapters/atomgit_v5.py` now owns the direct bounded V5 JSON
  transport, identity lookup, repository list/create/visibility/delete/branch
  operations, response parsing, error classification, and Hugging Face create
  boundary. It has no import edge to `api` or `services`.
- `services.authentication` and `services.repositories` retain only historical
  method signatures, output/return conventions, API class provenance, and
  patchable helper aliases; their methods delegate technical work to the
  canonical adapter. Old API helper assignments now propagate to the adapter.
- Repository creation preserves the logical (un-normalized) ID for the legacy
  visibility callback while using the normalized ID for the remote create call.
  Ambiguous visibility, deletion, and branch writes retain the old verified or
  unknown-state diagnostics.
- Focused evidence: authentication/repository ownership 24/24; login response
  bound 5/5; login error semantics 11/11; repository list 24/24; visibility
  30/30; deletion 48/48; branch 28/28; repository ID 68/68; structure 14/14;
  packaging metadata 13/13.
- Baseline: `python tests/run_cli_baseline.py` 92 passed in 80.22s in the
  `atomgit_cli` environment (offline). Compileall, dependency, and diff checks
  passed; no live remote writes or credential mutations were run.
- Review status: `APPROVED`. Initial review found a P1 compatibility gap where
  legacy direct branch calls could reach transport before revision validation;
  `AtomGitV5Adapter.create_branch` now rejects unsafe branch/source values before
  any request, with a focused regression. Final review found no open P0/P1/P2/P3
  findings.

### Audit Evidence And Decision

- Former implementation commit: `e927a4b refactor(architecture): align CLI and native SDK capabilities`
- Historical delivery records: `bc7b9ed`, `398beb1`, and `8d9490d` remain evidence of what was previously declared, not proof that the objective is currently satisfied.
- Re-audit decision: `REQUEST CHANGES`; the closed Issue's offline tests are green, but its final seven-directory runtime ownership and shared CLI/SDK usecase requirements are not met by the actual call graph.
- Blocking findings: `P1` CLI bypasses shared usecases; `P1` adapters depend on legacy business owners; `P1` parity registry does not verify runtime routing; `P2` compatibility ownership remains distributed.
- Remote evidence: `no live remote tests were run; controlled remote authorization remains limited to the dedicated test repositories`

The predecessor CLI Facade Conversion Issue and the architecture/parity Issue
remain historical records. Their prior completion claims are superseded for
acceptance purposes by this corrective Issue. The authoritative source state at
audit entry was clean `yuto` at `8d9490d`, equal to `github/yuto`; the current
task branch contains only this TASK activation change.

## Historical Completed Issue: R1-R5 Architecture Recovery

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-ARCH-CLI-SDK-PARITY-RECOVERY`
- Title: `Reopen architecture/parity delivery and drive runtime ownership to the seven-directory contract`
- Primary type: `refactoring`
- Secondary types: `architecture`, `compatibility`, `cli`, `sdk`, `testing`, `packaging`, `documentation`
- Priority: `P1`
- Delivery: `local task branch -> focused tests -> complete offline baseline -> independent review -> human acceptance -> cohesive commit 2056237 -> local no-ff merge 17ebd5a -> github/yuto push and equality verification`

### Objective

Reconcile the delivered architecture/parity Issue with its original intent. The
seven directories must become the actual canonical runtime ownership model, not
a parallel SDK facade over legacy business owners. CLI and native SDK entries for
every general remote capability must call one registered shared usecase, while
all existing CLI, legacy SDK, import, identity, signature, return, exception,
patch-seam, packaging, security, and state-restoration contracts remain stable.

This Issue is corrective and may not add unrelated product capabilities. It is
executed one work package at a time. A package is not complete because its
metadata exists; its exit gate must prove the real source/runtime behavior.

### Reproducible Evidence

- `python tests/run_cli_baseline.py` passes 92 isolated cases, so the current
  offline behavior is not showing an immediate regression.
- `python -m compileall -q .`, `python -m pip check`, `git diff --check`, and
  `python tests/test_structure_guard.py` pass.
- Production CLI command owners call `context.run_usecase`; the R2 bridge
  assembles `AtomGitClient` with context-preserving adapters.
- `adapters.atomgit_v5` and the HF adapter remain legacy-backed technical
  adapters by explicit R2 scope; R3 migrates those owners.
- The parity registry now resolves runtime symbols and checks CLI/SDK source
  delegation to the registered shared usecases, with a bypass fixture that
  fails closed.
- The `compatibility` package is a registry alias, while historical facade and
  patch logic remains distributed across multiple old paths.

### In Scope

- executable architecture and real call-path contracts;
- CLI-to-usecase wiring with exact presentation/exit compatibility;
- vertical migration of authentication, repositories, download, upload/LFS,
  and lifecycle owners;
- compatibility facade consolidation and patch-seam preservation;
- packaging/artifact declarations, structure tests, parity registry, and
  architecture documentation required by the migration;
- focused regressions, complete offline verification, independent review, and
  final human acceptance against the original objective.

### Out Of Scope

- new user-facing product capabilities unrelated to architecture compliance;
- intentional changes to existing CLI/SDK behavior without explicit migration
  authorization;
- dependency upgrades, broad formatting debt removal, or release work;
- live remote writes, repository creation/deletion, credential mutation, push,
  publication, or Issue state changes on a remote tracker without explicit
  authorization.

### Affected Capability IDs

`FLOOR-REGISTRY`, `ARCHITECTURE`, `CLI-SURFACE`, `CLI-DISPATCH`,
`AUTH-CONFIG`, `GIT-CREDENTIAL`, `REPO-MANAGEMENT`, `REVISION`, `UPLOAD-FILE`,
`UPLOAD-FOLDER`, `UPLOAD-RESUMABLE`, `UPLOAD-LFS`, `UPLOAD-LFS-RECOVERY`,
`DOWNLOAD-SNAPSHOT`, `DOWNLOAD-FILE`, `DOWNLOAD-INTEGRITY`,
`DOWNLOAD-SECURITY`, `SDK-DOWNLOAD`, `SDK-UPLOAD`, `SDK-REPO`, `REPO-ID`,
`RUNTIME`, `CACHE`, `DEPENDENCY-CONTRACT`, `PACKAGING`, `PORTABILITY`,
`ERROR-REDACTION`.

### Protected Existing Invariants

Existing command names, options, defaults, output, prompts, progress, exit
codes, public imports, object/class/function identities, signatures, return
values, exception categories, monkeypatch seams, locked HF/datasets calls,
package entry paths, token redaction, temporary-resource lifetime, global-state
restoration, installation/uninstallation behavior, and public/anonymous token
semantics remain unchanged. Existing legacy HF-style SDK functions remain
available with their compatibility semantics.

### New Or Changed Invariants

- Each parity-required capability has one executable shared usecase and both a
  CLI and native SDK route to that same usecase.
- Canonical `interfaces/usecases/domain/core/adapters/infrastructure` code has
  no dependency on legacy facades or legacy business owners.
- `compatibility` is the only owner of historical path/signature/identity/patch
  adaptation and contains no new business orchestration.
- The parity registry and structure guard fail closed on missing runtime routes,
  one-sided capabilities, new legacy dependencies, facade growth, unowned
  modules, cycles, stale artifacts, and missing focused evidence.
- New development work cannot add product behavior while this Issue has an open
  P1 exit gate.

### Focused Tests And Evidence

- Add a failing test for each real CLI/SDK/usecase route before changing it.
- Add structural tests that inspect import edges and runtime route identity,
  not only registry strings.
- Preserve and extend ownership, compatibility, dependency-signature,
  packaging, security, portability, and parity suites for each vertical slice.
- Run the complete `python tests/run_cli_baseline.py` after every corrective
  package and after the final review fix.
- Before closure also run `python -m compileall -q .`, `python -m pip check`,
  and `git diff --check`.
- Controlled remote evidence remains optional unless a package explicitly
  needs it; no live support claim may be made without authorized remote proof.

### Acceptance Criteria

The Issue cannot close until all of the following are true:

1. The actual CLI and native SDK call paths share the registered usecases for
   authentication, repositories, upload, download, revision, repo type, token,
   checksum, resume, prune, LFS, and final-state verification.
2. The seven-directory architecture is the canonical implementation location;
   old `services/download/upload/lfs/sdk` modules are compatibility or technical
   adapters only and do not receive new business logic.
3. Existing public and safety contracts listed above pass focused regressions
   and the complete baseline.
4. Structure/parity tests fail closed when a future contributor bypasses the
   canonical route or adds a one-sided CLI/SDK capability.
5. Architecture and development-floor documentation describe verified current
   behavior, and `TASK.md` evidence agrees with the real Git/source state.
6. All corrective packages have recorded exit-gate evidence, independent review
   returns `APPROVED`, and the human maintainer accepts the result against the
   original development intent.

## Historical Completed Issue

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-ARCH-CLI-SDK-PARITY`
- Title: `Reorganize business architecture and align CLI and SDK capabilities`
- Primary type: `refactoring`
- Secondary types: `architecture`, `compatibility`, `cli`, `sdk`, `testing`, `dependency`, `packaging`, `documentation`
- Priority: `P1`
- Delivery: `local implementation -> focused/full offline verification -> independent review -> human acceptance -> authorized delivery`

### Objective

Complete two separate phases. Phase 1 establishes the final seven-directory responsibility
architecture with no observable behavior change. Phase 2 gives the native SDK
every CLI general remote/business capability while preserving old HF-style SDK
functions. An executable parity registry and structural gates prevent future
one-sided CLI/SDK capability debt.

Parity-required capabilities are authentication, repositories, upload, download,
revision, repo type, token, checksum, resume, prune, LFS, and final-state
verification. Completion, update, uninstall, Shell hooks, interactive config
display, and presentation remain CLI-only. CLI default macOS metadata filtering
is also CLI policy, not an SDK parity requirement; SDK ignore behavior remains
caller-controlled.

### User Impact

- Phase 1: no change to commands, options, defaults, output, prompts, exits, SDK signatures, returns, exceptions, imports, identities, entry paths, remote calls, credentials, installation, or uninstallation.
- Phase 2: new native SDK capabilities and structured results; old HF-style functions remain available with their compatibility semantics.
- A new general remote capability is incomplete until both CLI and native SDK interfaces exist.

### Affected Capability IDs

`FLOOR-REGISTRY`, `ARCHITECTURE`, `CLI-SURFACE`, `CLI-DISPATCH`,
`AUTH-CONFIG`, `GIT-CREDENTIAL`, `REPO-MANAGEMENT`, `REVISION`,
`UPLOAD-FILE`, `UPLOAD-FOLDER`, `UPLOAD-RESUMABLE`, `UPLOAD-LFS`,
`UPLOAD-LFS-RECOVERY`, `DOWNLOAD-SNAPSHOT`, `DOWNLOAD-FILE`,
`DOWNLOAD-INTEGRITY`, `DOWNLOAD-SECURITY`, `SDK-DOWNLOAD`, `SDK-UPLOAD`,
`SDK-REPO`, `REPO-ID`, `RUNTIME`, `CACHE`, `DEPENDENCY-CONTRACT`,
`PACKAGING`, `PORTABILITY`, and `ERROR-REDACTION`.

### Protected Existing Invariants

Existing CLI commands, options, defaults, output, prompts, exit codes, public
imports, function/class identities, signatures, return values, exception
categories, patch seams, locked Hugging Face/datasets calls, package entry
paths, credential redaction, temporary-resource lifetime, and process-global
state restoration remain unchanged unless explicitly listed as a new native SDK
surface. No remote write or credential mutation is required for offline
acceptance.

### New Or Changed Invariants

General remote capabilities have one registered shared usecase and both CLI and
native SDK entries. Native SDK operations return structured results and stable
redacted `AtomGitError` subclasses. Shared token, repository ID/type, revision,
checksum, resume, prune, LFS, and final-state policies are used by both entry
surfaces. CLI presentation and macOS metadata filtering remain CLI-only.

### Focused Tests And Evidence

Architecture/parity, structure, SDK result/error/token, compatibility, locked
dependency, packaging, security, portability, compile, and import contracts
are included in the complete offline baseline. The required command is
`python tests/run_cli_baseline.py` in the `atomgit_cli` environment, followed by
`python -m compileall -q .`, `python -m pip check`, and `git diff --check`.
Black/isort/Ruff are audited against the existing repository debt; broad debt
removal is outside this Issue.

### Complete Baseline Evidence

Final revalidation on 2026-08-24: `python tests/run_cli_baseline.py` passed 92
isolated cases in 92.32s; compileall, pip check, and git diff --check passed.

### Residual Risks

No live AtomGit upload/download/checksum/LFS tests were run. Controlled remote
authorization remains limited to the dedicated test repositories. Black,
isort, and Ruff still report pre-existing repository-wide formatting debt.

## Final Architecture

```text
src/atomgit/
├── core/
├── domain/
├── usecases/
├── interfaces/
├── adapters/
├── compatibility/
└── infrastructure/
```

Historical paths remain as thin facades, not additional business layers:

```text
atomgit/cli/   -> historical CLI, Click, console/module entry surface
atomgit/api/   -> historical HuggingFaceAPI and api singleton surface
atomgit_hub.py -> historical top-level SDK surface
```

Responsibilities:

- `core/`: Request/Result contracts, stable errors, ports, and shared policies; no Click, HF, V5, or concrete network imports.
- `domain/`: authentication, repository, upload, download, and LFS rules and success invariants; no UI or concrete external calls.
- `usecases/`: ordered create/list/visibility/branch/delete/upload/download operations and final-state verification; no printing or `sys.exit`.
- `interfaces/`: user layer. `interfaces/cli` owns Click, prompts, output, progress, exits. `interfaces/sdk` owns native Python methods, parameter mapping, Results, and public errors. Neither owns remote business logic.
- `adapters/`: outbound HF 1.1.7, AtomGit V5, filesystem/cache/manifest, and transport boundaries.
- `compatibility/`: old paths, signatures, defaults, returns, exception mapping, identities, and patch seams; no new business logic.
- `infrastructure/`: config, token persistence, runtime, cache, Git helper, completion, update, uninstall, and technical lifecycle facilities.

Dependency direction:

```text
interfaces / compatibility -> usecases -> domain -> core -> outbound adapters
```

Forbid new SDK-to-CLI dependencies, domain-to-HF/V5 imports, interface business
implementations, Shell copies of core rules, compatibility growth, cycles,
unowned modules, and direct external calls that bypass usecases/adapters.

## Execution Runbook

The Issue is executed as numbered work packages. Only one package may be
`in_progress`; later packages remain pending until the current package exit
gate is recorded. Each package has a bounded scope, focused evidence, a
checkpoint, and a defined next action. A failed gate keeps the same package
active; it never authorizes skipping forward. Phase 2 is locked until the Phase
1 gate is accepted. If a conversation ends mid-package, resume the same
worktree and package rather than creating a parallel branch.

### Package Rules

- Before editing: record entry HEAD, worktree state, changed-path scope,
  capability IDs, invariants, and the package gate.
- After editing: run focused checks, `git diff --check`, and the required
  baseline slice; record exact results and changed paths in this Issue.
- Do not mix Phase 1 behavior-preserving migration with Phase 2 new SDK APIs.
- A behavior difference in Phase 1 is a blocking regression, not a migration
  choice. Stop and repair the package-owned change.
- The historical implementation backup branch is read-only reference material;
  it is not evidence for the reopened implementation and must not be
  cherry-picked as a substitute for current tests.

### Phase 1 Work Packages

#### WP-00: Recovery, Scope, and Baseline Freeze

Entry: no source edits for this Issue. Read `AGENTS.md`, `.ai/README.md`, this
Issue, and required references (`MASTER_PROMPT.md`, `DEVELOPMENT_RULES.md`,
`DOD.md`, `ARCHITECTURE.md`, `STYLE_GUIDE.md`, `TESTING.md`,
`DEVELOPMENT_FLOOR.md`, `WORKFLOW.md`, `REVIEW.md`). Reconcile Git root,
branch, HEAD, worktrees, status, recent log, current source/tests/docs, owner
registries, and locked HF/datasets signatures.

Actions: run the pre-change `python tests/run_cli_baseline.py`; inventory CLI
commands/schema/dispatch, SDK exports/signatures, API/CLI identities and
patch seams, external calls, package/entry paths, global-state contracts, and
current owners. Do not classify the former implementation as current evidence.

Outputs: baseline result, reconciled entry snapshot, capability inventory,
file-level migration map, and confirmed worktree. Exit gate: no unresolved
state mismatch and baseline result recorded. Checkpoint before WP-01.

#### WP-01: Executable Architecture Contracts

Entry: WP-00 passed. Define real owner maps for `core`, `domain`, `usecases`,
`interfaces`, `adapters`, `compatibility`, and `infrastructure`; allowed and
forbidden edges; facade debt limits; compatibility seam registry; source and
installed package expectations; and the Phase 2 parity-registry schema.

Add focused fail-closed tests for unowned modules, cycles, forbidden edges,
facade business definitions, missing seams, stale paths, and missing parity
metadata. Do not add empty packages or new business behavior. Exit gate:
contracts pass against the unchanged tree or fail only on explicitly registered
target-state assertions, and the complete baseline still passes.

#### WP-02: Core Contracts and External Boundaries

Entry: WP-01 passed. Add only immediately used Request/Result/error/port
contracts. Define HF 1.1.7, AtomGit V5, filesystem/cache, and config/runtime
boundaries without moving business callers. Add strict installed-signature tests
and verify `core` has no Click/HF/V5/concrete transport import. Exit gate:
compile/import/order/contract tests and complete baseline pass.

#### WP-03: Infrastructure and Outbound Adapter Ownership

Entry: WP-02 passed. Move or wrap config, runtime, cache/manifest, filesystem,
Git-helper, HF, and V5 implementations behind their target owners while
preserving lazy imports, credential safety, global-state restoration, and
installed provenance. Do not migrate authentication/repository/upload/download
orchestration in this package. Exit gate: runtime, dependency, security,
ownership, packaging, and complete baseline tests pass.

#### WP-04: Authentication Vertical Slice

Entry: WP-03 passed. Move authentication rules into domain/usecase boundaries
and connect existing CLI/API facades through interfaces, without adding new SDK
public methods. Preserve login, logout, whoami, Git-helper, config, redaction,
and all error categories. Cover 401/403/429/5xx/network/timeout/malformed
responses and config permissions. Exit gate: focused auth/security/seam tests,
installed imports, and complete baseline pass.

#### WP-05: Repository Vertical Slice

Entry: WP-04 passed. Migrate create/list/visibility/branch/delete into one
repository usecase family. Preserve CLI output, API bool results, validation,
confirmation, visibility convergence, source-commit resolution, target-commit
verification, and delete absence verification. Do not add native SDK methods.
Exit gate: repository/revision/redaction/ownership/import/packaging tests and
complete baseline pass.

#### WP-06: Download Vertical Slice

Entry: WP-05 passed. Migrate CLI/API download orchestration, transport,
integrity, resume, manifest, prune, repo-type resolution, redirect/token
isolation, and path safety behind usecase/adapters. Preserve existing HF-style
SDK behavior and signatures. Exit gate: all download/security/global-state/
dependency/ownership/packaging tests and complete baseline pass.

#### WP-07: Upload and LFS Vertical Slice

Entry: WP-06 passed. Migrate CLI/API file, folder, ordinary, resumable,
projection, worker, batch, timeout/progress, revision, ignore, LFS policy,
canonical pointer, and raw-blob verification ownership. Keep macOS metadata
filtering as injected CLI policy; do not change SDK defaults in Phase 1. Exit
gate: upload/LFS/global-state/dependency/security/ownership/packaging tests and
complete baseline pass.

#### WP-08: Lifecycle, Distribution, and Facade Closure

Entry: WP-07 passed. Place lifecycle/distribution technical implementations
behind infrastructure/interfaces. Shrink `atomgit.cli`, `atomgit.api`, and
`atomgit_hub` to compatibility conversion and seam registration only. Preserve
Click callback/module identities, lazy imports, console and both Python module
entry paths, old signatures/returns/exceptions, and patch behavior. Exit gate:
facade AST/debt, seam, CLI schema/dispatch, public import, source/editable/
wheel/sdist, installed-entry, completion, and complete baseline tests pass.

#### WP-09: Phase 1 Architecture Gate

Entry: WP-08 passed. Compare WP-00 inventory to the post-migration inventory.
Run full baseline, compileall, pip check, Black, isort, Ruff, credential and
artifact scans, package smoke, diff check, and independent review. Record exact
evidence and residual risk. Output: an accepted Phase 1 checkpoint and explicit
permission to begin Phase 2. If rejected, remain in Phase 1 and fix only
architecture regressions.

### Phase 2 Work Packages

#### WP-10: Parity Registry and Native SDK Contract

Entry: WP-09 accepted and Phase 1 source/tests are frozen except parity-owned
changes. Register every CLI general capability as `parity-required` or a
documented CLI-only exception. Define `AtomGitClient`, Request/Result types,
token priority, repo ID/type, visibility, revision, error, and final-state
contracts. Freeze old HF-style signatures. Exit gate: no CLI business capability
is unclassified, native SDK contracts have tests, and baseline still passes.

#### WP-11: Native SDK Authentication and Repository Parity

Entry: WP-10 passed. Add native SDK login/logout/whoami/create/list/visibility/
branch/delete methods with structured Results and stable `AtomGitError` mapping.
Preserve confirmation and final-state checks. Add canonical-request comparison
tests and keep old API/SDK functions thin. Exit gate: auth/repository parity,
compatibility, CLI contracts, security, locked signatures, and baseline pass.

#### WP-12: Native SDK Upload Parity

Entry: WP-11 passed. Expose file, ordinary folder, resumable, prefix, ignore,
workers, batches, timeout/progress restoration, revision, and LFS verification
through native SDK methods and shared usecases. Keep CLI metadata filtering a
CLI policy and old `upload_folder` compatibility. Exit gate: upload/LFS/result/
error/token/temp-lifetime/global-state/pointer/cross-entry tests and baseline.

#### WP-13: Native SDK Download Parity

Entry: WP-12 passed. Expose repository/file download, model/dataset resolution,
anonymous access, token, revision, force, checksum, persistent resume, and
manifest-scoped prune. Preserve `snapshot_download` and legacy `download_file`
semantics. Exit gate: download/security/checksum/resume/prune/cross-entry/
packaging tests and baseline pass.

#### WP-14: Parity Closure and Future-Debt Gate

Entry: WP-13 passed. Verify every parity-required item has one usecase, CLI
entry, native SDK entry, and cross-entry evidence; verify CLI-only exceptions;
add structure tests that fail on one-sided business paths, bypassed usecases,
missing registry entries, or facade growth. Update architecture/API/testing and
user documentation. Exit gate: Phase 2 acceptance, full baseline, package
smoke, independent review, and human acceptance pass.

### Checkpoint Format

At every package boundary record: current package/status, entry HEAD and
worktree state, changed paths, capabilities/invariants, focused commands and
exact results, complete baseline result, review status, last completed action,
next exact action, blockers, and residual risks. Never mark a later package
started before its predecessor exit gate is recorded.

### Package Evidence Ledger

The implementation turn must append one compact record per completed package;
do not replace earlier records with a summary:

```text
WP-XX: completed | HEAD=<commit> | changed=<paths>
Focused evidence: <commands and pass counts>
Baseline: <exact command/result>
Review: <not started/request changes/approved>
Residual risk: <none or explicit limitation>
Next: WP-YY <first action>
```

For a failed package, record the failure and keep the package `in_progress`:

```text
WP-XX: blocked by <contract/test>
Repair scope: <task-owned paths only>
Next: reproduce, fix, rerun the same gate
```

WP-00: completed | HEAD=bcd679d | changed=.ai/TASK.md
Focused evidence: `huggingface-hub==1.1.7`, `datasets==4.4.1`; 61 production
modules, 122 registered internal edges, 23 CLI schema nodes, 5 compatibility
facades, and the locked public HF-style signatures were inventoried.
Baseline: `python tests/run_cli_baseline.py` in `atomgit_cli`: 91 passed in
93.60s (offline).
Review: not started
Residual risk: local `yuto` remains divergent from `github/yuto`; remote history
contains the historical implementation and will not be force-pushed.
Next: WP-01 add executable target architecture contracts.

WP-01: completed | HEAD=bcd679d | changed=tests/structure_contract.py, tests/test_structure_guard.py, tests/test_architecture_parity.py, src/atomgit/{core,domain,usecases,interfaces,adapters,compatibility}
Focused evidence: architecture parity 14/14; structure guard 14/14; src-layout 6/6.
Baseline: `python tests/run_cli_baseline.py` 92 passed (offline).
Review: approved in final independent review.
Residual risk: remote behavior remains unverified by design.
Next: WP-02 through WP-08 completed in the same behavior-preserving migration.

WP-02: completed | HEAD=bcd679d | changed=src/atomgit/core, src/atomgit/adapters
Focused evidence: core dependency guard passed; locked HF/datasets signatures verified; compileall passed.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: locked dependency upgrades remain a future task.
Next: WP-03.

WP-03: completed | HEAD=bcd679d | changed=src/atomgit/adapters, src/atomgit/infrastructure, packaging contracts
Focused evidence: pip check, packaging metadata 13/13, source/editable/wheel/sdist contracts in baseline.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: no live installation or publication performed.
Next: WP-04.

WP-04: completed | HEAD=bcd679d | changed=authentication usecase/interface wiring
Focused evidence: authentication and credential-safety scripts in complete baseline; no token-like content scan hits.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: controlled remote auth evidence not required for this offline gate.
Next: WP-05.

WP-05: completed | HEAD=bcd679d | changed=repository usecase/interface wiring
Focused evidence: repository, revision, normalized-ID, and final-state scripts in complete baseline; parity branch verification 14/14.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: no remote repository mutation performed.
Next: WP-06.

WP-06: completed | HEAD=bcd679d | changed=download revision/filter context and transfer boundaries
Focused evidence: download contract 45/45, path security 15/15, recovery 12/12, repo-type resolution 7/7, checksum 23/23.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: remote checksum/resume evidence remains intentionally unrun.
Next: WP-07.

WP-07: completed | HEAD=bcd679d | changed=upload/LFS shared transfer boundaries
Focused evidence: upload/LFS, progress, batching, pointer, timeout, and global-state scripts in complete baseline.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: no live upload or LFS mutation performed.
Next: WP-08.

WP-08: completed | HEAD=bcd679d | changed=historical API/CLI/SDK facades and packaging ownership
Focused evidence: facade conversion, seam, import identity, CLI schema, entrypoint, and packaging contracts passed.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: task branch is local-only and remote yuto remains divergent.
Next: WP-09.

WP-09: completed | HEAD=bcd679d | changed=architecture/parity gate evidence
Focused evidence: compileall, pip check, git diff --check, Ruff, Black/isort, focused contracts, and complete baseline passed.
Baseline: 92 passed in `atomgit_cli` (offline).
Review: APPROVED; no open P0/P1/P2/P3 findings.
Residual risk: human acceptance and delivery history reconciliation remain.
Next: WP-10.

WP-10: completed | HEAD=bcd679d | changed=core/parity.py, interfaces/sdk, architecture parity registry
Focused evidence: registry fail-closed checks and native request/result contracts 14/14.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: no controlled remote evidence claimed.
Next: WP-11.

WP-11: completed | HEAD=bcd679d | changed=AtomGitClient authentication/repository methods
Focused evidence: explicit token precedence, repository final-state/branch checks, and compatibility baseline passed.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: no remote write authorization exercised.
Next: WP-12.

WP-12: completed | HEAD=bcd679d | changed=AtomGitClient upload methods and shared transfer port
Focused evidence: structured upload result, resumable/batch/LFS policy forwarding, upload/LFS baseline passed.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: live upload and LFS verification not run.
Next: WP-13.

WP-13: completed | HEAD=bcd679d | changed=AtomGitClient download methods and revision-safe transport
Focused evidence: revision/filter forwarding, explicit anonymous context, revision-scoped resume identity, and download suites passed.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: remote checksum/resume/prune evidence not claimed.
Next: WP-14.

WP-14: completed | HEAD=bcd679d | changed=parity registry, docs, tests, packaging, and TASK evidence
Focused evidence: all registry/structure/packaging checks plus final 92-case baseline passed; no credential/artifact scan hits.
Baseline: `python tests/run_cli_baseline.py` 92 passed in 89.66s (offline).
Review: APPROVED.
Residual risk: no live remote write or checksum/LFS test was run; no force-push was performed.
Next: final closure revalidation and documentation reconciliation.

Final closure revalidation: completed | HEAD=398beb1 before documentation reconciliation | changed=.ai/ARCHITECTURE.md, .ai/TESTING.md, .ai/TASK.md
Focused evidence: final complete offline baseline 92 passed in 93.49s; compileall, pip check, and git diff --check passed.
Review: APPROVED; final diff review found no P0/P1/P2/P3 findings.
Residual risk: Black/isort/Ruff retain pre-existing repository-wide debt; no live remote tests were run.
Next: record accepted closure and await the next authorized Issue.

Corrective R2: completed | HEAD=8d9490d (working tree) | changed=.ai/TASK.md, docs/architecture.md, src/atomgit/{adapters/huggingface.py,cli,commands,core,domain/transfers.py,interfaces,usecases/transfers.py}, tests/{development_floor_contract.py,structure_contract.py,test_architecture_parity.py}
Focused evidence: architecture 18/18; upload file 16/16; repo type 17/17;
resumable upload 49/49; structure 14/14; LFS ownership 13/13; packaging
metadata 13/13; compileall, pip check, diff check, Black, and isort passed.
Baseline: `python tests/run_cli_baseline.py` 92 passed in 84.03s (offline).
Review: APPROVED for R2; no open P0/P1/P2/P3 findings.
Residual risk: adapters remain historical-API-backed by design for R2; R3
technical-owner migration and live remote behavior are not complete.
Next: R3 only after human acceptance and explicit authorization.

Corrective R4: completed | HEAD=2056237 (task commit; merged as 17ebd5a) | changed=.ai/TASK.md, .ai/ARCHITECTURE.md, docs/architecture.md, pyproject.toml, setup.py, src/atomgit/{adapters/download,adapters/__init__.py,adapters/atomgit_v5.py,adapters/huggingface.py,api/__init__.py,cli,commands,core,domain,download,interfaces,services,upload,usecases}, tests/{development_floor_contract.py,structure_contract.py,packaging_contract.py,test_download_domain_ownership.py,test_architecture_parity.py,test_api_facade_conversion.py,test_auth_repository_services_ownership.py,test_packaging_metadata.py,test_src_layout_migration.py}
Focused evidence: download ownership 18/18 then 21/21 after final compatibility regressions; download contract 45/45; checksum 23/23; resume 17/17; prune 49/49; path security 15/15; raw integrity 12/12; redirect security 9/9; manifest concurrency 9/9; Windows compatibility 12/12; structure 14/14; packaging metadata 13/13; wheel/sdist smoke 37/37.
Baseline: `python tests/run_cli_baseline.py` passed 92/92 in 81.33s in `atomgit_cli` (offline) after the final review repairs; compileall, pip check, git diff --check, Black, isort, and Ruff passed.
Review: APPROVED after resolving P1 compatibility findings for local missing-source exceptions, remote missing-file classification, CLI diagnostic presentation, and context-managed anonymous download credentials.
Residual risk: upload/LFS technical-owner migration remains R5; no controlled remote download/checksum/resume/prune evidence was run; no remote writes or credential mutations were performed.
Next: delivery completed; activate a new Issue explicitly before further development.

Corrective R5: completed | HEAD=51d7410 (task commit; merged as 097a5bb) | changed=.ai/TASK.md, .ai/ARCHITECTURE.md, docs/architecture.md, pyproject.toml, setup.py, src/atomgit/{adapters,lfs,lfs_pointer.py,sdk,upload,api,atomgit_hub.py}, tests/{structure_contract.py,packaging_contract.py,test_upload_domain_ownership.py,test_lfs_domain_ownership.py,test_sdk_domain_ownership.py,test_hf_api_contract.py,test_src_layout_migration.py,test_download_domain_ownership.py,test_auth_repository_services_ownership.py}
Focused evidence: upload ownership 17/17; LFS ownership 14/14; SDK ownership 19/19; repository ownership 24/24; download ownership 18/18; structure 14/14; HF contract 16/16; packaging 13/13; src-layout 6/6; import-order 5/5; completion 19/19; wheel/sdist smoke 37/37.
Baseline: `python tests/run_cli_baseline.py` passed 92/92 in 81.03s in `atomgit_cli` (offline); compileall, pip check, and git diff --check passed.
Review: APPROVED; no open P0/P1/P2/P3 findings. Human acceptance granted; task commit 51d7410, merge 097a5bb, and github/yuto equality verified.
Residual risk: controlled remote upload, resumable recovery, and LFS remote state/checksum evidence remain intentionally unrun; R6 is out of scope.
Next: activate a new Issue explicitly before further development.

## Detailed Package Specifications

The summaries above define ordering. This section defines the minimum work
that must be completed inside each package; it is the implementation checklist,
not a suggestion to broaden scope.

### WP-00 Detail: establish the starting truth

Investigate before editing:

- the real Git state and branch ancestry, including whether `yuto` is clean and
  whether the local task branch is based on the recorded base commit;
- the actual command tree and every public option from `cli/__init__.py` and
  `tests/cli_baseline_contract.py`;
- every public SDK import, signature, identity, and patch target from
  `atomgit_hub`, `atomgit.atomgit_hub`, `atomgit`, and the SDK ownership tests;
- current owners and dependency edges from `tests/structure_contract.py`,
  `tests/test_structure_guard.py`, and the source tree;
- real `huggingface-hub==1.1.7` and `datasets==4.4.1` signatures at every
  production call site;
- packaging discovery in `setup.py` and `pyproject.toml`, including source,
  editable, wheel, sdist, console, and both Python module entry paths;
- global timeout/progress/runtime/config/Git-helper state and all credential
  redaction boundaries.

The required output is a checked-in-Issue inventory, not a new source package:

```text
capability -> current owner -> current CLI path -> current SDK path
            -> protected tests -> target work package
```

The baseline must run before any new contract is interpreted. A failure is
triaged as pre-existing, environment-related, or caused by this planning state;
the implementation cannot silently inherit an unexplained failure.

### WP-01 Detail: make architecture rules executable

Produce four maps before moving implementation:

1. **Owner map**: every production module has exactly one target owner among
   the seven responsibility directories; historical facades are marked as
   compatibility surfaces, not business owners.
2. **Edge map**: every current import edge is classified as allowed, temporary
   migration edge, or forbidden; temporary edges have a removal package.
3. **Seam map**: every historical patchable symbol records its canonical owner,
   consumers, assignment/deletion propagation, and restoration behavior.
4. **Parity map**: every current CLI capability is classified
   `parity-required`, `cli-only`, or `sdk-only`, with no new SDK method claimed.

Add fail-closed tests for these maps. The tests must prove that a deliberately
introduced unowned module, forbidden edge, facade function, missing seam, or
unregistered parity capability fails. Do not use a generic compatibility layer
or empty package to make the map pass.

### WP-02 Detail: define contracts without moving behavior

Define only contracts needed by the first migration slice:

- request objects for authentication, repository, upload, and download inputs;
- result objects or internal result protocols for operations whose old callers
  currently receive `bool` or `str`;
- error categories and cause/redaction rules;
- ports for HF calls, V5 calls, filesystem/cache, configuration, and time/retry
  behavior where a usecase needs substitution;
- shared policy interfaces for repo ID, repo type, revision, token, and file
  selection.

Every contract must state who owns validation, who owns side effects, and who
converts the result for CLI, native SDK, and compatibility callers. Do not
create a speculative `core` abstraction merely because a future capability may
need it. Contract tests must bind the real locked dependency signatures where
the port represents an HF call.

### WP-03 Detail: isolate technical boundaries

Move or wrap technical implementation one boundary at a time:

1. configuration and token persistence, preserving lazy reads, permissions,
   atomic writes, and no token leakage;
2. runtime environment and HF global-state setup/restoration;
3. filesystem, temporary resources, cache, manifest, checksum, and locks;
4. Git credential helper and lifecycle filesystem transactions;
5. HF Hub construction and calls using the real installed signatures;
6. AtomGit V5 request, response-size, redirect, authentication-header, and
   error handling.

After each boundary, prove the old caller still reaches the same behavior. No
authentication/repository/upload/download flow is redesigned here. The exit
condition is one technical owner per boundary and no interface/domain direct
external import, not merely the existence of new directories.

### WP-04 Detail: authentication slice

Trace and migrate the complete authentication flow:

```text
login input -> token validation -> identity request -> config persistence
            -> optional Git-helper setup -> CLI/legacy result
logout      -> config clear -> helper restoration -> result
whoami      -> saved-login check -> identity request -> result
```

Domain owns token/identity rules and error categories. The usecase owns ordering
and rollback semantics. Outbound adapters own the identity endpoint, config,
and Git calls. Interfaces preserve Chinese output, prompts, exits, and old API
boolean behavior. Tests must cover no-credential paths, all existing HTTP
categories, bounded malformed responses, redaction, config permissions, and
Git-helper preservation. Do not add native SDK methods until Phase 2 WP-11.

### WP-05 Detail: repository slice

Migrate each operation as a separately testable usecase, not one large
repository service:

- create: validate type/ID/visibility, create through the compatible route,
  converge visibility, and verify final state;
- list: authenticate, fetch bounded collection, validate response shape, and
  expose the existing CLI/API form;
- visibility: issue the update, recover only from allowed uncertain failures,
  and GET-verify the requested state;
- branch: resolve the source to an immutable commit, create, and verify target
  name plus commit;
- delete: require exact confirmation, GET before and after DELETE, and only
  report success after verified absence.

The shared result may be richer internally, but Phase 1 adapters must preserve
existing CLI output and API `bool`/error semantics. Add no native SDK public
surface in this package; that belongs to WP-11 after Phase 1.

### WP-06 Detail: download slice

Separate the download usecase into repository enumeration, destination safety,
transport, integrity, resume, manifest, and prune responsibilities. Preserve:

- public anonymous access and private token selection;
- model/dataset detection and explicit type forwarding;
- existing-file skip/force behavior;
- checksum handling for existing and new files;
- persistent resume identity and cleanup;
- manifest-scoped prune safety;
- redirect credential isolation and path traversal rejection;
- old SDK HF parameter warnings/forwarding and return values.

The usecase decides when a repository download is complete; filesystem and HTTP
adapters only perform bounded operations. Tests must verify each failure before
moving the next concern, so a checksum or prune regression cannot hide behind a
successful transport mock.

### WP-07 Detail: upload and LFS slice

Migrate upload by path/mode, keeping the following sequence explicit:

```text
validate path/symlinks -> normalize request -> select files by policy
  -> choose ordinary/resumable mode -> prepare projection if needed
  -> transfer -> commit -> verify pointer/raw blob -> return result
```

The slice must preserve direct single-file behavior, folder lifetime, path
prefix projection, ignore parsing, resumable batching/workers, timeout and
progress restoration, revision forwarding/rejection, retry/fatal categories,
LFS attribute transaction, canonical pointer bytes, and ambiguous-commit
reconciliation. CLI macOS metadata filtering is passed as a CLI policy; SDK
defaults are not changed in Phase 1. A fake that accepts invalid HF keywords is
not sufficient: each call binds to the real 1.1.7 signature.

### WP-08 Detail: lifecycle and facade closure

Keep lifecycle and distribution concerns separate from repository transfer
usecases. Verify completion install/uninstall transactions, update provenance,
package-absent fallback, exact managed paths, and user-state preservation.

Then shrink historical surfaces in dependency order:

1. move Click schema/context assembly behind `interfaces/cli` while keeping
   `atomgit.cli` as the observed module object;
2. move `HuggingFaceAPI` method resolution behind `compatibility/api` while
   preserving class and singleton identity;
3. move top-level and package SDK exports behind `compatibility/sdk` while
   preserving function identity/signatures and patch propagation;
4. verify `python -m atomgit`, `python -m atomgit.cli`, console script,
   completion-only imports, source provenance, and all artifact surfaces.

No facade may retain a second implementation “temporarily” without a named
owner and removal checkpoint. If a seam cannot be preserved, stop this package
and redesign the forwarding mechanism before changing behavior.

### WP-09 Detail: architecture release gate

Compare the WP-00 inventory field by field: command schema, SDK signatures,
object identities, call keywords, output/exit behavior, global-state snapshots,
package file set, and import side effects. Run the full offline matrix only
after focused failures are resolved. Independent review must inspect the whole
Phase 1 diff and test evidence as a structural refactor, not only new files.

The gate produces a decision: `Phase 1 accepted` or `Phase 1 rejected`. Only
`accepted` unlocks WP-10. A passing subset or a favorable code review cannot
unlock Phase 2 when the complete baseline is missing.

### WP-10 Detail: define the native SDK parity product

Create the parity registry from the actual CLI capability inventory, not from a
wish list. For every item define:

- native SDK method name and signature;
- whether it uses stored, explicit, or anonymous credentials;
- request normalization and repo type/revision rules;
- structured Result fields and guaranteed versus optional fields;
- `AtomGitError` mapping and preserved cause policy;
- CLI presentation differences;
- compatibility function(s) that must remain unchanged;
- focused, cross-entry, dependency, package, and (if authorized) remote tests.

The native API must not be designed by adding arbitrary CLI flags to old
HF-style functions. Old signatures are frozen; new AtomGit semantics belong to
`AtomGitClient` or explicitly named native functions.

### WP-11 Detail: authentication and repository parity

Implement native SDK adapters only after the shared usecases already pass.
Return structured identity/repository/visibility/branch/deletion results. Keep
delete confirmation and final absence verification in the SDK API, not in a
hidden interactive prompt. Compare CLI and SDK canonical requests using the
same fake transport, then separately test CLI output/exit and SDK return/error.

Remote validation, when used, is restricted to the authorized
`weixin_52273949/test_datasets` repository and must record pre-state, result,
checksum or final state, and cleanup. No repository deletion is authorized.

### WP-12 Detail: upload parity

Expose native SDK upload methods in capability increments: file, ordinary
folder, resumable folder, path prefix, ignore, workers/batches, timeout/progress,
revision, and LFS verification. For each increment, compare the SDK request
with the CLI request at the shared boundary before adding the next option.

Preserve old `upload_folder` result/signature semantics through compatibility.
Do not silently add CLI macOS metadata exclusions to SDK defaults. Use offline
strict fakes first, then the authorized remote repository only for separately
identified upload/recovery/LFS evidence.

### WP-13 Detail: download parity

Expose native repository/file download in increments: repo type, token/anonymous
selection, revision, force, checksum, resume, and prune. Define which fields in
`DownloadResult` are guaranteed and ensure partial failures never claim complete
success. Keep `snapshot_download` HF warnings/parameters and legacy
`download_file` return behavior through compatibility.

Cross-entry tests must compare canonical normalized requests, destination
policy, transport headers, checksum decisions, manifest mutations, and final
result status. Remote tests must use checksums or explicit remote state, not CLI
success text.

### WP-14 Detail: close the future-debt loop

Prove every parity registry row has one shared usecase, one CLI interface, one
native SDK interface, compatibility coverage where applicable, and tests at all
required layers. Add a deliberately incomplete one-sided fixture to prove the
parity gate fails closed, then remove only the fixture and keep the guard.

Update the authoritative architecture, testing, API, and user documentation
with current behavior and intentional CLI-only exceptions. Run the final full
baseline and independent review. The package is complete only after human
acceptance; a passing implementation without acceptance remains active.

## Phase 1: Behavior-Preserving Architecture

### Steps

1. Freeze CLI schema/dispatch/output/exits, SDK signatures/returns/errors,
   public imports/identities, patch seams, locked dependency signatures,
   global-state restoration, package surfaces, and the complete baseline.
2. Add executable owner, edge, facade-debt, packaging, import, behavior, and
   compatibility-seam contracts before moving implementation.
3. Establish core contracts, domain owners, usecase boundaries, interfaces,
   outbound adapters, compatibility registry, and infrastructure ownership.
4. Migrate complete vertical slices: infrastructure/ports, authentication,
   repositories, downloads, uploads, LFS, then lifecycle/distribution.
5. Keep historical paths stable; shrink their facades only after new owners and
   usecases are stable and tested. Remove duplicate implementations last.

### Non-goals

No CLI or SDK behavior change, new SDK capability, dependency upgrade, live
AtomGit write, credential mutation, publication, broad formatting, or unrelated
roadmap work.

### Invariants

- `ARCH-001`: every production module has one owner and registered edges; no new unowned module, cycle, forbidden edge, or facade business definition.
- `ARCH-002`: existing CLI/SDK/API behavior and locked-library calls remain exact.
- `ARCH-003`: historical module/object/callback/function/signature/entry/patch identities remain stable.
- `ARCH-004`: interfaces translate, usecases orchestrate, domains define rules, outbound adapters call external systems.
- `ARCH-005`: compatibility contains translation and seams only.
- `ARCH-006`: source/editable/wheel/sdist preserve historical entries and exclude stale duplicate implementations.

### Evidence

Run focused owner/edge/facade/import/patch/lazy tests for every slice and the
full `python tests/run_cli_baseline.py` after each slice and at the end. Also
run compileall, pip check, Black, isort, Ruff, credential/artifact scans, and
git diff check. No live evidence is required; live writes remain unauthorized.

## Phase 2: CLI/SDK Capability Alignment

### Steps

1. Freeze Phase 1 evidence.
2. Create a fail-closed registry classifying each capability as `parity-required`, `cli-only`, or `sdk-only`.
3. Define shared Request, Result, error, token, repo ID, repo type, visibility, revision, checksum, resume, prune, LFS, and final-state contracts.
4. Implement one shared usecase and outbound adapter per general capability.
5. Add native `interfaces/sdk` `AtomGitClient` methods and structured Results.
6. Keep `snapshot_download`, `upload_folder`, `download_file`, `create_repository`, `hub_download_url`, and `load_dataset` through compatibility with existing signatures and primary semantics.
7. Keep CLI output/prompts/progress/exits in the CLI interface and SDK Results/AtomGitError mapping in the SDK interface.
8. Add cross-entry tests comparing canonical requests and remote result invariants.

### SDK parity inventory

- Authentication: login validation, logout state, whoami.
- Repositories: create model/dataset, list, visibility, branch creation, safe delete with post-delete absence verification.
- Upload: file, ordinary folder, resumable, path prefix, ignore, workers, batches, timeout/progress restoration, revision, canonical LFS pointer/commit verification.
- Download: repository, file, model/dataset resolution, anonymous public access, token, revision, force, checksum, persistent resume, manifest-scoped prune.
- Shared policies: repo ID, repo type, visibility, revision, token priority, redaction, errors, final-state verification.

### Invariants

- `PARITY-001`: each parity-required capability has one shared usecase and both CLI/native SDK interfaces before completion.
- `PARITY-002`: CLI and SDK use one repo ID, repo type, revision, visibility, and token contract.
- `PARITY-003`: CLI and SDK agree on remote success/failure and final verification; only presentation, wrapping, and exit behavior differ.
- `PARITY-004`: SDK remote failures use stable redacted `AtomGitError` subclasses; local parameter failures remain standard exceptions.
- `PARITY-005`: old HF-style functions preserve signatures, defaults, paths, primary behavior, and compatibility returns.
- `PARITY-006`: no one-sided general capability can merge without registry and cross-entry evidence.
- `PARITY-007`: CLI macOS filtering remains explicit CLI policy and is not silently imposed on SDK callers.

## Shared Rules

Token priority:

```text
explicit non-empty token > explicit token=False > saved config token > anonymous read > auth error for writes
```

Explicit credentials never silently fall back. Validate repo ID before credentials
or network; normalize once; preserve logical model/dataset semantics; default
revision is `main`; non-main upload requires an explicitly created and verified
branch. Missing revisions map to `AtomGitRevisionNotFoundError`.

Shared usecases return structured results or classified internal errors. CLI
converts them to established output/exits. Native SDK returns structured Results
and stable `AtomGitError` subclasses. Compatibility converts them to historical
contracts. Tokens, signed URLs, response bodies, and secret-bearing causes never
enter results, logs, fixtures, or messages.

## Parity Delivery Gate

Every future feature records:

```text
capability ID, classification, shared usecase, CLI entry, SDK entry,
parameter mapping, shared remote result, CLI presentation, SDK result/error,
focused tests, documentation
```

Every parity-required capability must have core/domain/usecase, outbound adapter,
CLI interface, SDK interface, compatibility coverage, shared result tests, CLI
output/exit tests, SDK result/error tests, registry/documentation updates, and a
passing complete baseline. A one-sided implementation may remain on a branch
while work continues, but cannot be complete, merged, released, or used as the
basis for further feature expansion. Structure tests must fail closed when a
new business path bypasses the shared owner or lacks parity registration.

## Acceptance Criteria

### Phase 1

1. The seven responsibility directories and dependency direction are implemented without moving user behavior into domain or adding another business layer.
2. Existing CLI, SDK, API, packaging, entry, dependency, global-state, credential-safety, and remote-call behavior remains exact.
3. All migrated capabilities have one owner; historical facades contain no new business implementation and preserve identities/seams.
4. Architecture, ownership, edge, facade, import, packaging, and behavior contracts fail closed.
5. Focused tests, complete baseline, compileall, pip check, lint, security, artifact, and installed smoke pass.

### Phase 2

1. Native SDK interfaces cover every CLI general remote/business capability in the parity inventory.
2. CLI and SDK share usecases, domain rules, outbound adapters, remote result invariants, and stable errors.
3. Existing HF-style SDK functions remain compatible through thin facades.
4. CLI-only capabilities and macOS policy are explicit exceptions, not accidental SDK gaps.
5. Every parity capability has both-entry tests, cross-entry evidence, documentation, and complete baseline evidence.
6. Future one-sided business additions fail parity and structure gates.
7. Independent review has no open P0/P1/P2/P3 finding before human acceptance.

## Required Verification

All commands run in `atomgit_cli`:

```bash
python tests/run_cli_baseline.py
python -m compileall -q .
python -m pip check
git diff --check
```

Also run applicable focused architecture/ownership/import/compatibility,
CLI schema/dispatch/output, SDK signature/result/error/token, locked HF/datasets,
packaging, source/editable/wheel/sdist, security, portability, Black, isort,
Ruff, credential/artifact, and installed-entry tests. Independent review uses
`.ai/REVIEW.md`. Controlled remote tests require separate explicit authorization.

## Authorization And Delivery

- The maintainer explicitly authorized R5 implementation and verification by requesting continued development, then authorized committing and pushing the completed work in the current request. Source, tests, contracts, packaging, and documentation were in scope.
- Delivery mode is local task branch -> focused/full offline verification -> independent review -> human acceptance -> cohesive commit -> local no-ff merge into yuto -> push only yuto -> remote equality verification.
- Controlled remote test authorization: the maintainer explicitly authorizes
  authenticated upload and download, test-branch creation, repository
  visibility changes, deletion of test files or test branches, Git push, and
  necessary test-data cleanup only in
  `weixin_52273949/test_datasets` (`git@atomgit.com:weixin_52273949/test_datasets.git`).
  Record pre-test state, keep fixtures clearly test-owned, verify final remote
  state/checksums, and restore visibility or other mutable state after the
  applicable scenario. Never display credentials.
- Repository deletion, use of any other remote repository, remote repository
  creation, remote Issue/PR operations, task-branch push to the development
  repository, credential mutation, publication, tags/releases, and upstream
  changes remain unauthorized.
- Human acceptance was granted by the maintainer's explicit request to commit and push the completed R5 work. Standing project rules allowed one cohesive conventional commit, local no-ff merge into yuto, push only yuto, fetch, and remote equality verification; the task branch was not pushed.
- Delivery evidence: task commit `51d7410`, merge commit `097a5bb`, and remote `github/yuto` verified at `097a5bb1f507adac346bfad60bcc5fb198b80e46` with `git fetch`, `git rev-parse`, and `git ls-remote`.

## Independent Review

- Verdict: `APPROVED`
- Findings: `R4 review initially REQUEST CHANGES for local FileNotFoundError compatibility, remote missing-file classification, lost CLI diagnostics, and context-managed credential handling; all were repaired with focused regressions before the final APPROVED review`
- Review evidence: `final diff reviewed against the active Issue, locked huggingface-hub==1.1.7 and datasets==4.4.1 signatures, structure/parity contracts, download ownership and security suites, packaging/source/wheel/sdist contracts, compileall, pip check, Ruff, Black/isort, diff check, and the complete 92-case offline baseline`
- Residual review risk: `controlled remote upload/download/checksum/LFS evidence was not run; no credential mutation or live repository test was performed`

## Definition Of Done

- [x] Phase 1 and Phase 2 remain separate and each has observable acceptance evidence.
- [x] Capability IDs, protected invariants, and new invariants agree with executable registries.
- [x] No behavior change is hidden in Phase 1.
- [x] Every general remote CLI capability has a native SDK counterpart or an explicit CLI-only classification.
- [x] Old imports, signatures, identities, patch seams, entry paths, and package artifacts remain compatible.
- [x] Focused, complete baseline, dependency, packaging, security, portability, compile, and diff checks pass.
- [x] Black/isort/Ruff were audited; their pre-existing repository-wide debt is recorded as residual risk and is outside this closure scope.
- [x] Independent review is APPROVED with no open blocking finding.
- [x] Human acceptance of R5 was granted by the maintainer; commit, merge, push, and remote equality verification are complete.
- [x] Remaining risks, unrun tests, and controlled-remote limitations are explicit.
