# Current Issue Contract

Status: active

## Handoff Snapshot

- Updated: `2026-08-19 +0800`
- Phase: `self-tested, independently reviewed, and maintainer-accepted; task
  commit next`
- Base branch: `yuto`
- Base commit: `138e1a9`
- Base synchronization: `yuto`, `github/yuto`, and `github/HEAD` all resolved to
  `138e1a9` before branch creation
- Task branch: `codex/sdk-domain-ownership` (local only; never push)
- Current HEAD: `138e1a9`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `dirty with only active-Issue source, tests, contracts, and
  documentation`
- Last completed action: `the maintainer explicitly requested self-test and
  acceptance followed by commit and push; the final acceptance run passed all
  focused gates, supporting checks, and the complete baseline`
- Next exact action: `create the cohesive task commit, merge it locally into
  yuto with --no-ff, push only yuto, and verify github/yuto`
- Blockers: `none`

The predecessor LFS Domain Issue is complete, accepted, committed, locally
merged, pushed, and remotely verified. Its task commit is `7f7074d`, local merge
is `a2275c6`, final delivery records are `79d6685` and `138e1a9`, and local and
remote `yuto` resolve to `138e1a9`.

## Active Issue

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-REFACTOR-SDK-DOMAIN-OWNERSHIP`
- Title: `Extract Python SDK ownership behind historical import paths`
- Primary type: `refactoring`
- Secondary types: `sdk`, `compatibility`, `testing`, `security`,
  `distribution`, `documentation`
- Priority: `P2`
- Approved program step: `10. SDK Domain`
- Observable objective: `move Python SDK snapshot/file/URL/dataset download,
  folder upload, repository creation, token lookup, and stable error policy
  into real SDK-domain modules while preserving atomgit_hub,
  atomgit.atomgit_hub, and atomgit public objects, signatures, old-path module
  patch seams, locked dependency calls, state restoration, temporary lifetime,
  error redaction, artifacts, and all observable SDK behavior`
- User impact: `none by design; internal ownership migration only`

### Authorization And Delivery

- User authorization: `the maintainer approved the sequential capability-owned
  structural program, the persisted predecessor contract identifies SDK Domain
  as step 10, and on 2026-08-19 explicitly requested continued development`
- Authorized local actions: `create a local task branch; edit task-owned source,
  tests, registries, packaging contracts, and AI/human architecture documents;
  inspect locked dependencies; build temporary artifacts; run offline checks;
  perform an independent review`
- Delivery after human acceptance: `under the standing maintainer delivery
  rules, create one cohesive conventional commit, merge the local task branch
  into yuto with --no-ff, push only yuto, and verify github/yuto; never push the
  task branch`
- Unauthorized actions: `remote Issue/PR creation or transition, task-branch
  push, tag or Release mutation, publication, live AtomGit repository writes,
  credential mutation, deletion, or upstream main changes`
- Delivery mode: `local task branch -> focused and complete offline verification
  -> independent review -> human acceptance -> cohesive commit -> local no-ff
  merge into yuto -> push only yuto -> verify github/yuto`

### Evidence And Current Behavior

- `src/atomgit/atomgit_hub.py` is a 734-line module that directly owns SDK token
  lookup, error classification, ID/type mapping, snapshot/file/URL/dataset
  download, folder upload, and repository creation.
- `src/atomgit_hub.py` is the historical top-level compatibility proxy and
  forwards assignment/deletion patches to `atomgit.atomgit_hub`.
- `atomgit.__init__` eagerly or lazily exports the same SDK function and
  exception objects. Existing users and tests patch dependency names on the
  historical top-level module, including `_get_token`, `hf_snapshot_download`,
  `hf_hub_download`, `hf_upload_folder`, `create_repo`, and `ds_load_dataset`.
- Existing SDK regressions cover strict dependency calls, ID normalization,
  stable exceptions, error redaction, retry behavior, dataset loading, upload
  path lifetime, timeout restoration, canonical LFS handling, repository
  creation semantics, import order, public imports, src layout, wheel/sdist
  contents, and Python/Windows portability.
- Locked contracts inspected in the `atomgit_cli` conda environment:
  `huggingface-hub==1.1.7`, `datasets==4.4.1`, Click `8.4.2`; real HfApi,
  create_repo, upload_folder, snapshot_download, and hf_hub_download signatures
  accept the current production keyword sets.

### Expected Behavior

- Non-placeholder `atomgit.sdk` modules have one exact implementation owner for
  shared policy, errors, download, upload, repository, and dataset behavior.
- `atomgit.atomgit_hub` becomes a historical facade whose public and private
  SDK function objects are exact aliases of their owners.
- The separately packaged `atomgit_hub` proxy, package facade, and `atomgit`
  exports retain imports, `__all__`, function identities, signatures, return
  values, warnings, exceptions, and cause chaining.
- Direct assignment, deletion, and `patch.object` at the historical module path
  reach every former runtime resolution site and restore exact identities.
- Source, default PEP 660 editable, wheel, and sdist discovery include exactly
  the delivered SDK package and the historical compatibility modules without
  repository leakage.

### Scope

#### In Scope

- Add only SDK-domain modules receiving real implementation now.
- Move SDK shared normalization/token/type policy, error conversion, snapshot,
  file, URL and dataset download, folder upload, and repository creation.
- Preserve exact public signatures, symbols, exceptions, aliases, import order,
  package laziness, old-path dependency/helper patching, stored/explicit token
  selection, retry policy, cache and dataset options, model/dataset route
  mapping, main-only upload, private-only creation, upload projection lifetime,
  symlink rejection, canonical LFS verification, timeout restoration, safe
  error output, and return outcomes.
- Tighten exact facade debt, dependency edges, module ownership, artifact, src
  layout, public import, test inventory, and development-floor contracts.

#### Out Of Scope

- Change SDK behavior, signatures, exceptions, supported revisions, public
  creation limitations, dependency versions, endpoint semantics, or remote
  evidence claims.
- Share CLI-specific output/service implementations with the SDK, migrate CLI
  commands, convert `api.py` or `cli.py`, or remove the `cli -> api` edge.
- Redesign LFS, upload, download, repository, infrastructure, lifecycle,
  distribution, configuration, or release behavior.
- Live AtomGit writes, credential changes, publication, broad formatting,
  unrelated cleanup, or future facade/CLI Issues.

### Affected Capability IDs

- `FLOOR-REGISTRY`, `SDK-DOWNLOAD`, `SDK-UPLOAD`, `SDK-REPO`, `REPO-ID`,
  `RUNTIME`, `DEPENDENCY-CONTRACT`, `GLOBAL-STATE`, `ERROR-REDACTION`,
  `UPLOAD-LFS`, `PACKAGING`, and `PORTABILITY`

### Protected Existing Invariants

- All existing `103` invariants remain protected, especially `SDKDL-001..002`,
  `SDKUP-001..002`, `SDKREPO-001..002`, repository-ID, locked-dependency,
  runtime/import-order, global-state, LFS pointer, redaction, packaging, and
  portability invariants.
- Historical public imports, exact callable identities and signatures, old-path
  dependency patches, authentication selection, download retry, dataset
  projection, upload lifetime/cleanup, timeout restoration, main-only upload,
  private-only creation, stable exception classes/messages, and redacted causes
  remain unchanged.

### New Or Changed Invariants

- `FLOOR-014`: Python SDK implementations have exact SDK-domain owners while
  historical top-level/package/public symbols, signatures, identities,
  assignment/deletion/module-object patch seams, locked calls, and later-owned
  CLI/API/LFS boundaries remain stable; ownership drift, placeholders, duplicate
  implementations, facade regrowth, or forbidden dependency directions fail
  closed.
- `PKG-020`: source, default PEP 660 editable, wheel, and sdist surfaces include
  exactly the delivered SDK package plus historical package/top-level facades
  without repository leakage.

### Focused Tests And Evidence

- Add `tests/test_sdk_domain_ownership.py` for exact owner modules,
  implementation provenance, historical public/private identities and
  signatures, complete assignment/deletion/`patch.object` propagation,
  non-owner negative cases, placeholder rejection, facade-debt tightening, and
  CLI API/LFS non-migration.
- Rerun SDK create/download/upload/dataset/exception/recovery/global-state/HF
  contract/import-order/public-import, repository-ID, canonical-LFS, structure,
  src-layout, packaging, development-floor, and portability scripts.
- Bind representative production keyword sets against the installed locked
  libraries; run changed/new-file Black, isort, Ruff, compileall, pip check,
  source/editable/wheel/sdist smoke checks, and `git diff --check`.
- Controlled-remote evidence: `not applicable; observable remote behavior is
  unchanged and live writes are not authorized for this ownership refactor`.

### Acceptance Criteria

1. Every moved SDK definition has one real SDK-domain owner; no placeholder,
   duplicate implementation, or unowned production module remains.
2. `atomgit_hub`, `atomgit.atomgit_hub`, and `atomgit` preserve exact public
   objects, `__all__`, signatures, warnings, errors, results, and registered
   old-path helper/dependency patch behavior.
3. Download retry/auth/cache/parameter behavior, dataset local-snapshot loading,
   repository normalization/type/privacy behavior, and upload validation,
   temporary lifetime, timeout restoration, main-only policy, canonical LFS,
   error redaction, and cause preservation retain exact offline evidence.
4. SDK owners depend only in approved directions; CLI API, CLI command, LFS,
   lifecycle, and distribution ownership remains outside the SDK package.
5. Source/editable/wheel/sdist contracts discover every delivered SDK module,
   preserve both historical import paths, reject placeholders/unowned modules,
   and tighten the historical SDK facade debt to its exact new size.
6. The ledger remains monotonic at `26 capabilities`, at least `104 invariants`,
   and at least `88 isolated pytest cases`.
7. Focused tests, the complete offline baseline, supporting gates, and
   independent review pass with no open P0/P1/P2/P3 finding before acceptance.

### Verification Evidence

- Pre-edit focused baseline: `19 selected SDK, dependency, structure, packaging,
  development-floor, LFS, and portability scripts passed`.
- Ownership regression on old implementation: `test_sdk_domain_ownership.py
  failed as expected because all seven real atomgit.sdk owner modules were
  absent`.
- Implementation and focused tests: `SDK ownership 18/18, structure 13/13,
  packaging 13/13, development floor 15/15, HF signature 16/16, public import
  8/8, src layout 6/6, predecessor download 15/15, upload 16/16, and LFS 13/13;
  SDK behavior regressions for create, exceptions, upload lifetime/parameters/
  timeout, dataset, download/recovery, repository IDs, and global state passed`.
- Complete baseline: `python tests/run_cli_baseline.py -> 88 passed in 88.80s
  (0:01:28) after the review fix; an earlier final run passed in 78.96s and
  another run
  passed 88/88 before that expansion, and the first run correctly failed three
  stale predecessor ownership assertions that still required SDK definitions
  in the historical facade; final maintainer-requested self-test -> 88 passed
  in 78.98s (0:01:18)`.
- Supporting gates: `python -m compileall -q ., python -m pip check, changed/new
  file Black --check, isort --check-only, Ruff, and git diff --check passed;
  wheel/source/editable/sdist coverage passed inside the complete baseline`.
- Independent review: `the first read-only review requested changes for one P2
  compatibility finding: atomgit_hub.Path assignment/deletion no longer reached
  the three former SDK path-conversion resolution sites. The implementation
  added the exhaustive seam and regression, reran all gates, and a fresh
  read-only review found no open P0/P1/P2/P3 finding; verdict APPROVED`.

### Residual Risks

- Live AtomGit behavior is intentionally unchanged and will not be retested for
  this ownership-only migration.
- Python 3.9 is represented by declared tooling and portability contracts in
  the current Python 3.10 conda environment.
- Human acceptance: `accepted on 2026-08-19 when the maintainer explicitly
  requested self-testing and acceptance followed by commit and push`.
- Delivery operations: `task commit, local merge, and yuto-only push are now
  authorized and pending; no remote Issue/PR, tag, release, live write,
  credential mutation, or deletion is authorized`.
