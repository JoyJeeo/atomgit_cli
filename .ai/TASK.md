# Current Issue Contract

Status: inactive

## Handoff Snapshot

- Updated: `2026-08-19 +0800`
- Phase: `completed, accepted, merged, pushed, and remotely verified`
- Base branch: `yuto`
- Base commit: `7fa7c84`
- Base synchronization: `yuto`, `github/yuto`, and `github/HEAD` all resolved
  to `7fa7c84` before branch creation
- Task branch: `codex/cli-command-ownership` (local only; never push)
- Current HEAD: `bf0f8f2 on yuto before this final delivery-record commit`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `clean after the task commit, local no-ff merge, and first
  yuto-only push; this handoff update is the final delivery record`
- Last completed action: `created task commit 6d98b92, merged it locally into
  yuto as bf0f8f2, pushed only yuto, fetched github, and verified local yuto,
  github/yuto, and github/HEAD all resolved to bf0f8f2`
- Next exact action: `none; await an explicit maintainer request before
  activating another Issue`
- Blockers: `none`

The predecessor SDK Domain Issue is complete, accepted, committed, locally
merged, pushed, and remotely verified. Its task commit is `ec3476b`, local
merge is `5469383`, final delivery record is `7fa7c84`, and local and remote
`yuto` resolved to `7fa7c84` before this Issue was activated.

## Completed Issue

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-REFACTOR-CLI-COMMAND-OWNERSHIP`
- Title: `Extract CLI command ownership behind the historical Click module`
- Primary type: `refactoring`
- Secondary types: `cli`, `compatibility`, `testing`, `security`,
  `distribution`, `documentation`
- Priority: `P2`
- Approved program step: `11. CLI Command Ownership`
- Observable objective: `move authentication, repository, transfer, cache,
  completion, update, uninstall, and configuration command implementations
  into real CLI-command owner modules while preserving the atomgit.cli module,
  exact Click tree/schema/help/output/prompts/exits, lazy imports, completion,
  old-path patch seams, API calls, and all observable behavior`
- User impact: `none by design; internal ownership migration only`

### Authorization And Delivery

- User authorization: `the maintainer approved the complete sequential
  capability-oriented structure program on 2026-08-18; the persisted sequence
  identifies CLI Command Ownership as step 11 after the completed SDK Domain;
  on 2026-08-19 the maintainer explicitly requested continued development and,
  after reviewing the implementation status, authorized self-testing,
  acceptance, commit, and push`
- Accepted conditions:
  1. `command modules are created only as their real implementation moves`
  2. `atomgit.cli remains the historical module and owns Click schema,
     prompts, output, exit conversion, and service-call wiring`
  3. `the exact command/group objects, callback signatures, help, dispatch,
     import order, completion, and lazy behavior remain stable`
  4. `old-path assignment, deletion, and patch.object seams reach every former
     command implementation resolution site and restore exact identities`
  5. `API facade conversion, CLI package/facade conversion, API behavior,
     transfer/service implementation, distribution/Shell extraction, test
     layout, and public behavior changes are excluded`
- Authorized local actions: `create a local task branch; edit task-owned source,
  tests, registries, packaging contracts, and AI/human architecture documents;
  inspect locked dependencies; build temporary artifacts; run offline checks;
  perform an independent review`
- Delivery after human acceptance: `completed under the standing maintainer
  delivery rules: one cohesive conventional task commit, local --no-ff merge
  into yuto, and yuto-only push; the task branch was not pushed`
- Unauthorized actions: `remote Issue/PR creation or transition, task-branch
  push, tag or Release mutation, publication, live AtomGit writes, credential
  mutation, deletion, or upstream main changes`
- Delivery mode: `completed: local task branch -> focused and complete offline
  verification -> independent review -> human acceptance -> cohesive commit ->
  local no-ff merge into yuto -> push only yuto -> verify github/yuto`

### Evidence And Current Behavior

- `src/atomgit/cli.py` is a 908-line historical module containing the Click
  root/group/option schema and the implementations of 18 leaf commands.
- The module dispatches through a lazy `atomgit.api.api` object and lazy
  historical utility functions, while importing completion, lifecycle,
  distribution, configuration, and version objects before command execution.
- Tests patch historical `atomgit.cli` names including `api`, `config`, Git
  helpers, utility functions, `run_update`, `build_uninstall_plan`, and
  `run_uninstall`; completion derives candidates from the live Click tree.
- `tests/cli_baseline_contract.py` records the exact public tree, parameters,
  and leaf dispatch inventory; focused regressions cover deterministic stdout,
  stderr, exits, exception categories, prompts, redaction, auth, repository,
  upload, download, completion, update, uninstall, cache, configuration,
  import-order, packaging, and portability behavior.
- Locked contracts inspected in `atomgit_cli`: Click `8.4.2`,
  `huggingface-hub==1.1.7`, and `datasets==4.4.1`.
- Pre-edit complete evidence: `python tests/run_cli_baseline.py -> 88 passed in
  82.65s (0:01:22)`.

### Expected Behavior

- Real, non-placeholder CLI command owner modules contain the command
  implementations now embedded in the historical module.
- `atomgit.cli` continues to construct and export the same root/group/leaf
  Click objects with the same schema, callback signatures, help, prompt,
  output, exit, import-order, and completion behavior.
- Direct assignment, deletion, and `patch.object` at the historical module path
  propagate to every former runtime lookup site without leaking to unrelated
  owners.
- Source, default PEP 660 editable, wheel, and sdist discovery include exactly
  the delivered command package while preserving the historical `atomgit.cli`
  module and both CLI entry paths.

### Scope

#### In Scope

- Add only command-owner modules receiving real implementation in this Issue.
- Move the implementations of update/uninstall/completion, authentication,
  cache, repository, upload/download, and configuration display commands.
- Preserve the exact Click schema in `cli.py`, including decorators, command
  registration order, command/group names, parameter types/defaults/help,
  docstrings, callback signatures, root object identity, and module entrypoint.
- Preserve all historical dependency/helper patch seams, configuration and Git
  state safety, token redaction, temporary/resource behavior, output strings,
  prompts, exception categories, exit status, and API arguments/results.
- Tighten exact owner, dependency, facade debt, artifact, src-layout,
  public-import, test-inventory, development-floor, architecture, and testing
  contracts.

#### Out Of Scope

- Convert `cli.py` into `cli/__init__.py` or `cli/root.py`, or change public
  commands, options, help, prompts, output, errors, exits, or completion.
- Convert `api.py`, remove `cli -> api`, change `HuggingFaceAPI` or its global
  singleton, or move API/service/transfer/LFS/SDK business behavior.
- Change locked dependencies, release/update/uninstall semantics, Shell entry
  points, distribution policy, test layout, or source layout.
- Live AtomGit writes, credential changes, publication, remote Issue/PR work,
  broad formatting, or unrelated cleanup.

### Affected Capability IDs

- `FLOOR-REGISTRY`, `CLI-SURFACE`, `CLI-DISPATCH`, `AUTH-CONFIG`,
  `REPO-MANAGEMENT`, `REVISION`, `CACHE`, `UPLOAD-FILE`, `UPLOAD-FOLDER`,
  `UPLOAD-RESUMABLE`, `UPLOAD-LFS`, `UPLOAD-LFS-RECOVERY`,
  `DOWNLOAD-SNAPSHOT`, `DOWNLOAD-FILE`, `DOWNLOAD-INTEGRITY`,
  `DOWNLOAD-SECURITY`, `GIT-CREDENTIAL`, `REPO-ID`, `RUNTIME`,
  `ERROR-REDACTION`, `PACKAGING`, and `PORTABILITY`

### Protected Existing Invariants

- All existing `105` invariants remain protected, especially `FLOOR-005..014`,
  `CLI-001..006`, `DISPATCH-001..005`, authentication, repository, upload,
  download, repository-ID, global-state, redaction, packaging, and portability
  invariants registered by the affected capabilities.
- Exact command and parameter schema, Click object/function signatures,
  registration order, help text, deterministic output, prompts, exits,
  exception categories, redaction, old-path patches, completion, import order,
  lazy API loading, and downstream call arguments remain unchanged.
- API, service, transfer, LFS, SDK, lifecycle, infrastructure, and distribution
  observable behavior remains protected and structurally outside this Issue.

### New Or Changed Invariants

- `FLOOR-015`: CLI command implementations have exact command-domain owners
  while the historical module, Click tree/schema, callback signatures,
  completion/lazy behavior, deterministic interaction, and registered old-path
  patch seams remain stable; ownership drift, placeholders, duplicates, facade
  regrowth, or forbidden dependency directions fail closed.
- `PKG-021`: source, default PEP 660 editable, wheel, and sdist surfaces include
  exactly the delivered CLI command owner modules and historical `cli.py`
  without repository leakage.

### Focused Tests And Evidence

- Add `tests/test_cli_command_ownership.py` for exact owner modules,
  implementation provenance, Click root/group/leaf identity and callback
  signatures, complete assignment/deletion/`patch.object` propagation,
  non-owner negative cases, placeholder rejection, facade-debt tightening, and
  API/CLI-facade non-migration.
- Rerun exact CLI schema/dispatch/feature/surface, completion, update,
  uninstall, authentication, repository, upload, download, configuration,
  cache, global-state, redaction, import-order, structure, src-layout,
  packaging, development-floor, public-import, and portability scripts.
- Run final `python tests/run_cli_baseline.py`, `python -m compileall -q .`,
  `python -m pip check`, changed/new-file Black, isort, Ruff, and
  `git diff --check`.
- Controlled-remote evidence: `not applicable; observable remote behavior is
  unchanged and live writes are not authorized for this ownership refactor`.

### Acceptance Criteria

1. Every moved command implementation has one real command-domain owner; no
   placeholder, duplicate implementation, or unowned production module remains.
2. `atomgit.cli`, both executable entry paths, and the live Click command tree
   preserve exact objects, schema, signatures, registration, help, completion,
   lazy import, prompt, output, exception, redaction, and exit behavior.
3. Historical dependency/helper assignment, deletion, and `patch.object` seams
   reach all former runtime lookup sites and restore exact identities.
4. Downstream API/service/utility/lifecycle/distribution calls retain exact
   arguments and results, and API/CLI facade conversion remains excluded.
5. Structure, source/editable/wheel/sdist, public import, test inventory, and
   development-floor contracts discover the command owners and reject drift.
6. The ledger remains monotonic at `26 capabilities`, at least `108 invariants`,
   and at least `89 isolated pytest cases`.
7. Focused tests, the complete offline baseline, supporting gates, and an
   independent review pass with no open P0/P1/P2/P3 finding before acceptance.

### Verification Evidence

- Pre-edit complete baseline: `python tests/run_cli_baseline.py -> 88 passed in
  82.65s (0:01:22)`.
- Ownership regression on old implementation:
  `tests/test_cli_command_ownership.py failed as expected because the
  atomgit.commands owner package and all four owner modules were absent`.
- Implementation and focused tests: `CLI ownership 13/13, CLI baseline guard
  14/14, CLI feature/schema/dispatch 69/69, CLI surface 54/54, deterministic
  refactor behavior 6/6, structure 13/13, packaging 13/13, src layout 6/6,
  development floor 15/15, and wheel/source/editable/sdist smoke 36/36 passed.
  Focused authentication, repository, upload, download, completion, update,
  uninstall, and cache regressions also passed`.
- Complete baseline: `after the initial implementation run passed 89/89 in
  80.29s, the review-fix run passed 89/89 in 85.22s (0:01:25), and the final
  pre-delivery acceptance run passed 89/89 in 81.76s (0:01:21)`.
- Supporting gates: `python -m compileall -q ., python -m pip check,
  changed/new-file Black --check, isort --check-only, Ruff, git diff --check,
  credential-pattern scan, and artifact/status audit passed; no tracked build
  artifact or credential was found`.
- Independent review: `the first read-only review requested changes for two P2
  evidence findings: incomplete affected-capability declarations and dynamic
  historical patch propagation evidence that did not yet cover each command
  owner category. Both were fixed; a fresh read-only re-review found no open
  P0/P1/P2/P3 finding and returned APPROVED`.

### Residual Risks

- Live AtomGit behavior will not be retested because this is an ownership-only
  refactor and remote writes are not authorized.
- Python 3.9 is represented by declared tooling and portability contracts in
  the current Python 3.10 conda environment.
- Human acceptance: `the maintainer explicitly authorized self-testing,
  acceptance, commit, and push on 2026-08-19; final acceptance gates passed`.
- Delivery evidence: `task commit 6d98b92 (refactor(cli): extract command
  ownership) was merged locally into yuto with --no-ff as bf0f8f2 (merge:
  extract cli command ownership); only yuto was pushed. After fetch, local
  yuto, github/yuto, and github/HEAD all resolved to
  bf0f8f211a407bf9abb1f4130c33cc00e594241c. The local task branch was never
  pushed`.
