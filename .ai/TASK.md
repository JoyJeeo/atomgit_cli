# Current Issue Contract

Status: inactive

## Handoff Snapshot

- Updated: `2026-08-19 +0800`
- Phase: `completed, accepted, committed, locally merged, pushed, and remotely
  verified`
- Base branch: `yuto`
- Base commit: `d6c692d`
- Base synchronization: `yuto`, `github/yuto`, and `github/HEAD` all resolved
  to the base commit before branch creation`
- Task branch: `codex/lfs-domain-ownership` (local only; never push)
- Current HEAD: `yuto merge a2275c6; final delivery record is included in this
  handoff update`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `clean on yuto before the final delivery record commit`
- Last completed action: `created task commit 7f7074d, merged it into yuto as
  a2275c6 with --no-ff, pushed only yuto through the configured github remote,
  fetched, and verified local yuto, github/yuto, and github/HEAD`
- Next exact action: `none for this completed Issue; wait for an explicit new
  development request before activating another Issue`
- Blockers: `none`

The predecessor Upload Domain Issue is complete, accepted, committed, locally
merged, pushed, and remotely verified at `d6c692d`. Its task branch remained
local and was never pushed.

The predecessor Download Domain Issue is complete, accepted, committed, locally
merged, pushed, and remotely verified. Its task commit is `25e145d`, local
merge is `22de896`, final delivery record is `ddab1db`, and local/remote `yuto`
both resolved to `ddab1db` before this task branch was created.

## Previous Completed Issue

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-REFACTOR-UPLOAD-DOMAIN-OWNERSHIP`
- Title: `Extract upload ownership behind the historical API class`
- Primary type: `refactoring`
- Secondary types: `compatibility`, `testing`, `security`, `distribution`,
  `documentation`
- Priority: `P2`
- Observable objective: `move CLI API upload service, ordinary transfer,
  resumable orchestration, projection, and error policy into real upload-domain
  modules while preserving historical atomgit.api symbols, concrete class and
  singleton surfaces, method identities and signatures, module-object patch
  seams, CLI outcomes, artifacts, and upload safety and recovery behavior`
- User impact: `none by design; internal ownership migration only`

### Authorization And Delivery

- User authorization: `the maintainer approved the complete sequential
  capability-oriented structure program on 2026-08-18 and explicitly requested
  continued development in this conversation on 2026-08-19; the persisted
  approved sequence names Upload Domain as step 8 after Download Domain. On
  2026-08-19 the maintainer explicitly requested final self-testing and
  acceptance followed by commit and push, satisfying human acceptance and the
  recorded delivery authorization`
- Approved program step: `8. Upload Domain`
- Accepted conditions:
  1. `upload modules are created only as their real implementation moves`
  2. `atomgit.api.HuggingFaceAPI and atomgit.api.api remain the historical
     concrete class and singleton surfaces`
  3. `old-path direct, private, dependency-module, assignment, deletion, and
     patch.object seams reach the same former upload resolution sites`
  4. `batching, timeout, progress, temporary lifetime, projection, target
     preflight, reconciliation, retry/reduction, error redaction, and CLI/SDK
     calls remain unchanged`
  5. `LFS transfer, slow-flow, attributes, pointer ownership, SDK ownership,
     CLI command ownership, API/CLI facade conversion, lifecycle, and
     distribution ownership extraction is excluded`
- Authorized local actions: `edit task-owned source, packaging metadata,
  tests, registries, AI and human documentation; inspect locked dependencies;
  build temporary artifacts; run offline checks; perform independent review`
- Authorized delivery after acceptance: `create one cohesive conventional
  commit, merge the local task branch into yuto with --no-ff, push only yuto,
  and verify github/yuto; never push the task branch`
- Unauthorized actions: `remote Issue/PR creation or transition, task branch
  push, tag or Release mutation, publication, live AtomGit writes, credential
  mutation, deletion, or upstream main changes`
- Delivery mode: `local task branch -> focused and complete offline
  verification -> independent review -> human acceptance -> cohesive
  conventional commit -> local no-ff merge into yuto -> push only yuto ->
  verify github/yuto`

### Pre-Implementation And Expected Behavior

#### Pre-Implementation Baseline

- `src/atomgit/api.py` owns upload progress state, ordinary and resumable
  transfer orchestration, target validation, stable projection cache, file
  selection and batching, child-process isolation, commit reconciliation,
  error classification, and `HuggingFaceAPI.upload_folder` /
  `upload_directory` on the remaining 3,715-line historical API module.
- The same module also owns LFS mode validation, preupload policy,
  `.gitattributes` synchronization, canonical pointer coordination, and slow
  LFS-flow replacement. Those definitions are approved program step 9 and
  remain structurally in `atomgit.api` during this Issue; moved upload code may
  consume them only through explicit compatibility seams.
- `src/atomgit/lfs/service.py` now owns LFS policy, transfer recovery,
  attributes, and error/event orchestration; `src/atomgit/lfs_pointer.py`
  remains the canonical pointer owner.
  `src/atomgit/atomgit_hub.py` owns SDK upload/download/repository/dataset
  behavior and is approved program step 10.
- Existing tests assign old-path dependencies and helpers on `atomgit.api`,
  including `HfApi`, `upload_folder`, `hf_upload_file`,
  `read_upload_metadata`, `close_hf_session`, projection and resumable process
  helpers, V5 helpers, LFS helpers, progress functions, and locked HF modules.
- Locked contracts inspected in `atomgit_cli`: `huggingface-hub==1.1.7`,
  `datasets==4.4.1`, Click `8.4.2`; real `HfApi`, `HfApi.upload_file`,
  `HfApi.upload_folder`, `HfApi.upload_large_folder`, module `upload_file`, and
  module `upload_folder` signatures match the current dependency tests.
- Pre-edit focused evidence: all 30 selected upload, resumable, LFS-boundary,
  global-state, predecessor-ownership, structure, public-import, src-layout,
  packaging, development-floor, and CLI-baseline scripts passed.

#### Expected

- Real implementations live in non-placeholder `atomgit.upload` modules
  separated by service, ordinary, resumable, projection, and error ownership,
  without duplicate implementations.
- `atomgit.api.HuggingFaceAPI` remains the historical concrete class and gains
  its upload methods through an owner mixin; `atomgit.api.api` remains an exact
  instance of that class and CLI dispatch remains unchanged.
- Historical upload helpers, exceptions, dependency objects, method objects,
  and signatures remain available at `atomgit.api`; assignments and deletions
  at the old module path propagate only to former resolution sites.
- Source, default PEP 660 editable, wheel, and sdist discovery include exactly
  the delivered upload package without repository leakage.

### Scope

#### In Scope

- Add only upload-domain modules receiving real implementation now.
- Move CLI API ordinary upload, upload progress state, resumable worker/process
  orchestration, target validation, batching, projection cache/synchronization,
  commit reconciliation and retry/reduction coordination, and upload error
  classification.
- Preserve exact public/private symbols, class/singleton/method identities,
  signatures, old-path patches, file/directory behavior, repo type/revision,
  ignore/prefix/worker/batch/timeout/progress behavior, target preflight,
  deterministic projections, metadata reuse, temporary lifetime, cleanup,
  state restoration, safe error output, and return outcomes.
- Retain explicit compatibility aliases needed at `atomgit.api` and explicit
  upload-to-LFS dependency seams while LFS remains the later owner.
- Update exact ownership, dependency, facade debt, artifact, src-layout,
  public-import, development-floor, architecture, and testing contracts.

#### Out Of Scope

- Move or redesign LFS source identity, transfer controller, slow-flow policy,
  upload-mode validation, preupload classification/retry, remote
  `.gitattributes` policy, or canonical pointer implementation.
- Move SDK `upload_folder`, snapshot/file/URL/dataset downloads, repository
  creation, dataset loading, or stable SDK exception conversion.
- Extract CLI commands, convert `api.py` or `cli.py` into packages, remove
  `cli -> api`, change public behavior or dependency versions.
- Logging/type/format sweeps, broad test-layout changes, live AtomGit writes,
  publication, lifecycle/distribution work, or unrelated cleanup.

### Affected Capability IDs

- `FLOOR-REGISTRY`, `UPLOAD-FILE`, `UPLOAD-FOLDER`, `UPLOAD-RESUMABLE`,
  `UPLOAD-LFS`, `UPLOAD-LFS-RECOVERY`, `REPO-ID`, `CLI-SURFACE`,
  `CLI-DISPATCH`, `PACKAGING`, `PORTABILITY`, `DEPENDENCY-CONTRACT`,
  `GLOBAL-STATE`, and `ERROR-REDACTION`

### Protected Existing Invariants

- All existing `100` invariants remain protected, especially `FLOOR-005..011`,
  `CLI-001..006`, `DISPATCH-001..005`, upload file/folder/resumable/LFS,
  repository-ID, dependency, packaging, portability, global-state, and
  redaction invariants registered by those capability IDs.
- Historical imports, API class/singleton, CLI dispatch, old-path upload
  helpers/dependencies, exact output and return values, projection identity and
  modes, child-process isolation, resumable metadata and reconciliation,
  credential isolation, and global timeout/progress restoration remain
  unchanged.
- Download, service, SDK, LFS, lifecycle, and distribution behavior remain
  protected; only the upload-to-LFS call boundary is made explicit.

### New Or Changed Invariants

- `FLOOR-012`: CLI API upload implementations have exact upload-domain owners
  while historical API symbols, method identities, signatures, registered
  patch seams, and the later-owned LFS boundary remain stable; ownership drift,
  placeholders, facade regrowth beyond the tightened ceiling, and forbidden
  dependency directions fail closed.
- `PKG-019`: source, default PEP 660 editable, wheel, and sdist surfaces include
  exactly the delivered upload package and historical API module without
  repository leakage.

### Focused Tests And Evidence

- Add `tests/test_upload_domain_ownership.py` for implementation provenance,
  exact owner modules, historical class/singleton/method/helper identities and
  signatures, full assignment/deletion/module-object patch seams, non-owner
  negative cases, facade-debt tightening, placeholder rejection, and LFS/SDK
  boundary non-migration.
- Re-run every registered upload, resumable, LFS-boundary, repository ID, CLI
  schema/dispatch, redaction, global-state, structure, public-import,
  src-layout, packaging, dependency, portability, and development-floor script.
- Run final `python tests/run_cli_baseline.py`, `python -m compileall -q .`,
  `python -m pip check`, changed/new-file Black, isort, Ruff, and
  `git diff --check`.
- Controlled-remote evidence: `not applicable; no remote behavior changes and
  live writes are not authorized for this refactor`.

### Acceptance Criteria

1. Every moved CLI API upload function, class, exception, or method has one
   real upload-domain owner; no placeholder or duplicate implementation remains.
2. `atomgit.api.HuggingFaceAPI`, its moved upload method objects/signatures,
  global `api`, CLI dispatch, and registered historical helper/dependency patch
  seams remain executable and unchanged.
3. File/directory routing, repo type/revision, ignore/prefix/worker/batch,
   timeout/progress/state restoration, projection, target preflight, child
   process, retry/reduction/reconciliation, cleanup, and error behavior retain
   exact offline evidence.
4. LFS ownership remains outside the upload package; upload invokes its existing
   policy through the intended transfer-to-LFS direction, and SDK implementation
   remains structurally untouched.
5. Structure and artifact contracts discover every nested upload module,
   reject placeholders/unowned code, tighten API debt, and agree across source,
   editable, wheel, and sdist surfaces.
6. The ledger remains monotonic at `26 capabilities`, at least `102 invariants`,
   and at least `86 isolated pytest cases`.
7. Focused tests, complete offline baseline, supporting gates, and independent
   review pass with no open P0/P1/P2/P3 finding before acceptance or delivery.

### Verification Evidence

- Pre-edit focused matrix: `30/30 selected scripts passed, including every
  upload/resumable/LFS-boundary regression plus structure 13/13, public import
  8/8, src layout 6/6, packaging 13/13, development floor 15/15, CLI baseline
  guard 14/14, predecessor download ownership 15/15, and predecessor service
  ownership 20/20`.
- Locked dependencies: `huggingface-hub 1.1.7, datasets 4.4.1, Click 8.4.2;
  installed upload signatures inspected and consistent`.
- Implementation evidence: `tests/test_upload_domain_ownership.py initially
  failed because all upload owner modules were absent, then passed 16/16 after
  adding the real upload contracts, errors, ordinary, projection, resumable,
  and service owners. Every selected ordinary/resumable/LFS-boundary/global-
  state/SDK regression passed. One focused compatibility failure showed that
  the initial patch map omitted upload.service as a consumer of the moved
  _execute_resumable_upload_process helper; the accepted full consumer map and
  AST regression fixed it, and test_auto_configure_lfs.py passed 41/41. The
  first complete baseline exposed four stale/real structural contracts:
  predecessor service ownership and HF AST provenance still named api.py, and
  eager upload.__init__ loaded huggingface_hub during completion. The accepted
  fix made upload.__init__ lightweight and updated both exact owner/signature
  contracts; all four scripts then passed`
- Complete baseline: `the initial post-implementation matrix reported 82
  passed / 4 failed in 75.84s for the four exact structural contracts above.
  After their implementation/test fixes and complete supporting verification,
  python tests/run_cli_baseline.py passed 86/86 in 74.31s. After the maintainer
  requested self-acceptance and delivery, the unchanged implementation passed
  a fresh final run 86/86 in 75.89s`
- Supporting gates: `test_upload_domain_ownership.py 16/16, structure 13/13,
  packaging 13/13, src layout 6/6, development floor 15/15, CLI baseline guard
  14/14, public import 8/8, predecessor services ownership 20/20, locked HF
  dependency contract 16/16, import order 5/5, completion 19/19, and wheel/
  sdist/default PEP 660 editable smoke 36/36 passed. python -m compileall -q .,
  python -m pip check, changed/new Black 24.10.0, isort 5.13.2, Ruff 0.12.12,
  git diff --check, artifact and credential-pattern scans passed. api.py
  tightened from 3,715 lines / 60 functions / 17 classes to 2,086 / 26 / 12;
  exact legacy tool debt tightened from Black 85/571, isort 87/105, Ruff
  19/196 to Black 84/532, isort 86/104, Ruff 18/195`
- Review: `independent read-only review inspected the complete diff, exact
  active Issue, locked signatures, child-process and Windows spawn import
  path, completion lightness, historical patch propagation, all 39 removed AST
  definitions, LFS/SDK non-migration, dependency directions, artifacts,
  documentation, final test evidence, and credential scan. No P0/P1/P2/P3
  finding remains; verdict APPROVED`
- Human acceptance: `accepted on 2026-08-19 through the maintainer's explicit
  request to self-test and accept the change, then commit and push`.
- Residual risks: `live AtomGit exercise is not authorized or required for an
  ownership-only refactor; Python 3.9 remains represented by declared/tooling
  contracts in the current Python 3.10 environment`.

### Review Record

- Review phase: `complete after final implementation and verification`
- Verdict: `APPROVED`
- Open findings: `none. The implementation phase fixed one complete-map
  compatibility gap and the first full baseline fixed three stale contracts
  plus the eager upload package import that violated completion lightness`

## Maintainer Test Authorization

- Scope: `the ongoing code-structure development work only`
- Sole authorized test repository: `weixin_52273949/test_datasets`
- Web URL: `https://ai.atomgit.com/weixin_52273949/test_datasets`
- Git URL: `git@atomgit.com:weixin_52273949/test_datasets.git`
- Boundary: `do not use any other repository for development testing; do not
  delete, publish, or perform unrelated remote writes; keep credentials out of
  logs and commits`

## Completed Issue Record

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-REFACTOR-LFS-DOMAIN-OWNERSHIP`
- Title: `Extract LFS ownership behind the historical API and upload paths`
- Primary type: `refactoring`
- Secondary types: `compatibility`, `testing`, `security`, `distribution`,
  `documentation`
- Priority: `P2`
- Observable objective: `move LFS transfer/recovery, preupload policy, safe
  pattern validation, remote .gitattributes transaction, canonical pointer,
  and LFS error/event policy into real lfs-domain modules while preserving
  historical atomgit.api symbols, concrete class and singleton surfaces,
  method behavior, module-object patch seams, CLI outcomes, SDK boundary, and
  locked huggingface-hub behavior`
- User impact: `none by design; internal ownership migration only`

### Authorization And Delivery

- User authorization: `the maintainer explicitly requested continued
  development after the accepted Upload Domain delivery; the persisted
  approved capability sequence names LFS Domain as step 9; on 2026-08-19 the
  maintainer explicitly requested self-testing, acceptance, commit, and push`
- Approved program step: `9. LFS Domain`
- Accepted conditions:
  1. `LFS modules are created only as their real implementation moves`
  2. `atomgit.api.HuggingFaceAPI and atomgit.api.api remain the historical
     concrete class and singleton surfaces`
  3. `old-path direct, private, dependency-module, assignment, deletion, and
     patch.object seams reach the same former LFS resolution sites`
  4. `LFS mode selection, bounded preupload retry, attributes safety and
     concurrency, slow-flow recovery, canonical pointer bytes, reconciliation,
     cleanup, timeout/progress state, error redaction, and CLI/SDK outcomes
     remain unchanged`
  5. `SDK upload implementation, CLI command ownership, API/CLI facade
     conversion, lifecycle, distribution, and unrelated upload/download
     behavior remain outside this Issue`
- Authorized local actions: `edit task-owned source, packaging metadata,
  tests, registries, AI and human documentation; inspect locked dependencies;
  build temporary artifacts; run offline checks; perform independent review`
- Unauthorized actions: `remote Issue/PR creation or transition, task branch
  push, tag or Release mutation, publication, live AtomGit writes, credential
  mutation, deletion, or upstream main changes`
- Delivery mode: `local task branch -> focused and complete offline
  verification -> independent review -> human acceptance -> cohesive
  conventional commit -> local no-ff merge into yuto -> push only yuto ->
  remote verification`

### Scope And Compatibility

- In scope: `extract every LFS definition currently owned by api.py or
  lfs_pointer.py into non-placeholder lfs modules; preserve exact historical
  names, signatures, identities, imports, dependency signatures, child-process
  isolation, global-state restoration, pointer verification, and error
  redaction; update structure, artifact, public-import, development-floor, and
  architecture/testing contracts`
- Out of scope: `move SDK upload/download, change HF or AtomGit dependency
  versions, redesign LFS behavior, perform live writes, convert api.py or cli.py
  into packages, or remove the cli -> api compatibility edge`
- Affected Capability IDs: `FLOOR-REGISTRY`, `UPLOAD-LFS`,
  `UPLOAD-LFS-RECOVERY`, `UPLOAD-RESUMABLE`, `UPLOAD-FOLDER`, `UPLOAD-FILE`,
  `GLOBAL-STATE`, `ERROR-REDACTION`, `DEPENDENCY-CONTRACT`, `PACKAGING`,
  `PORTABILITY`
- Protected Existing Invariants: `all existing 103 invariants, especially
  FLOOR-005..012, LFS-001..003, LFSREC-001..002, resumable commit/recovery,
  dependency, global-state, redaction, packaging, portability, and historical
  API/upload patch-surface invariants`
- New Or Changed Invariants: `FLOOR-013: LFS implementations have exact
  domain owners while historical API, pointer, upload, SDK, dependency-module,
  assignment, deletion, and patch seams remain stable; ownership drift,
  placeholders, duplicate implementations, forbidden dependency directions,
  or facade regrowth fail closed`
- Focused tests and evidence: `add test_lfs_domain_ownership.py covering
  exact owner modules, implementation provenance, historical symbols and
  signatures, full assignment/deletion/module-object patch seams, negative
  ownership cases, LFS/SDK non-migration, structure and artifact discovery;
  rerun all registered LFS, resumable, upload-boundary, global-state,
  redaction, dependency, portability, packaging, and development-floor tests`
- Complete-baseline evidence: `python tests/run_cli_baseline.py is mandatory
  after implementation and every fix; also run compileall, pip check,
  git diff --check, changed-file Black/isort/Ruff, and source/editable/wheel/
  sdist smoke checks`
- Residual risks: `live AtomGit behavior remains unchanged and is not required
  for this ownership-only migration; Python 3.9 portability remains covered
  by declared/tooling contracts in the current Python 3.10 environment`

### Verification Evidence

- Focused LFS regressions: `test_auto_configure_lfs.py 41/41,
  test_lfs_preupload_policy.py 89/89, test_lfs_slow_flow_recovery.py 28/28,
  test_canonical_lfs_pointer.py 24/24, test_resumable_commit_policy.py 51/51,
  test_lfs_domain_ownership.py 13/13`
- Ownership and supporting contracts: `download ownership 15/15, upload
  ownership 16/16, structure 13/13, src layout 6/6, packaging 13/13,
  development floor 15/15, CLI baseline guard 14/14`
- Complete baseline: `python tests/run_cli_baseline.py -> 87 passed in
  78.13s (0:01:18)`
- Supporting gates: `python -m compileall -q ., python -m pip check, changed
  file Black/isort/Ruff, and git diff --check passed`
- Independent review: `read-only review confirmed one real LFS owner,
  removed duplicate API definitions, exact patch seams, no SDK or upload
  ownership regression, registered dependency/artifact surfaces, and no open
  P0/P1/P2/P3 finding; verdict APPROVED`

### Delivery Evidence

- Task commit: `7f7074d refactor(lfs): extract lfs domain ownership`
- Local merge: `a2275c6 merge: extract lfs domain ownership`
- Push remote: `github` remote, branch `yuto`; task branch was never pushed
- Remote verification before this final record: `local yuto`, `github/yuto`,
  and `github/HEAD` all resolved to `a2275c6`
- No remote Issue/PR, tag, Release, publication, live AtomGit write,
  credential mutation, deletion, or upstream-main change was performed
