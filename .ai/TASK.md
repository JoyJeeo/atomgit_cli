# Current Issue Contract

Status: inactive

## Handoff Snapshot

- Updated: `2026-08-19 +0800`
- Phase: `completed, accepted, committed, locally merged, pushed, and remotely
  verified`
- Base branch: `yuto`
- Base commit: `ed059a6ac732e7a5e7674d571adac0fea2afab70`
- Base synchronization: `yuto`, `github/yuto`, and `github/HEAD` all resolved
  to the base commit before branch creation`
- Task branch: `codex/download-domain-ownership` (local only; never push)
- Current HEAD: `22de8969bc2f9ed37be8c40a4baf35dc3d875180`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `clean on yuto before this final delivery record commit`
- Task commit: `25e145d617d55457c5b8812442dbac6f1b1233b2`
- Local yuto merge: `22de8969bc2f9ed37be8c40a4baf35dc3d875180`
- Verified remote yuto: `22de8969bc2f9ed37be8c40a4baf35dc3d875180`
- Last completed action: `created the cohesive task commit, merged it into
  yuto with --no-ff, pushed only yuto, fetched github/yuto, and verified local
  and remote yuto at 22de896`
- Next exact action: `none for this completed Issue; wait for an explicit new
  development request before activating another Issue`
- Blockers: `none`

Delivery evidence: task commit `25e145d`; local no-ff merge `22de896`; remote
verification resolved `github/yuto` to
`22de8969bc2f9ed37be8c40a4baf35dc3d875180`. The task branch remained local and
was never pushed. No remote Issue/PR, tag, Release, publication, live AtomGit
write, credential mutation, deletion, or upstream-main change was performed.

The predecessor authentication/repository services Issue is complete,
accepted, committed, locally merged, pushed, and remotely verified. Its task
commit is `e6525cc`, local merge is `de84281`, final delivery record is
`ed059a6`, and local/remote `yuto` both resolved to `ed059a6` before this task.

## Active Issue

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-REFACTOR-DOWNLOAD-DOMAIN-OWNERSHIP`
- Title: `Extract download ownership behind the historical API class`
- Primary type: `refactoring`
- Secondary types: `compatibility`, `testing`, `security`, `distribution`,
  `documentation`
- Priority: `P2`
- Observable objective: `move CLI API download service, transport, integrity,
  manifest, resume, and prune implementation into real download-domain modules
  while preserving historical atomgit.api symbols, class/method identities,
  signatures, module-object patch seams, CLI outcomes, artifacts, and download
  security and atomicity`
- User impact: `none by design; internal ownership migration only`

### Authorization And Delivery

- User authorization: `the maintainer approved the complete sequential
  capability-oriented structure program on 2026-08-18 and explicitly requested
  continued development on 2026-08-18; the persisted approved sequence names
  Download Domain as step 7 after authentication/repository services`
- Approved program step: `7. Download Domain`
- Accepted conditions:
  1. `download modules are created only as their real implementation moves`
  2. `atomgit.api.HuggingFaceAPI and the global atomgit.api.api object remain
     the historical concrete class and singleton surfaces`
  3. `old-path direct, private, dependency-module, and patch.object seams reach
     the same former download call sites`
  4. `authentication choice, framing, redirects, Windows/path safety, checksum,
     retry, locking, cleanup, redaction, and CLI outcomes remain unchanged`
  5. `SDK download, upload, resumable-upload, projection, LFS, CLI command,
     API facade, CLI facade, lifecycle, and distribution ownership extraction
     is excluded`
- Authorized local actions: `edit task-owned source, packaging metadata,
  tests, registries, AI and human documentation; inspect locked dependencies;
  build temporary artifacts; run offline checks; perform independent review;
  commit; and locally merge after maintainer acceptance`
- Authorized remote delivery: `after implementation, complete verification,
  independent review, and maintainer acceptance, push only the locally merged
  yuto branch and verify github/yuto; never push the task branch`
- Unauthorized actions: `remote Issue/PR creation or transition, task branch
  push, tag or Release mutation, publication, live AtomGit writes, credential
  mutation, deletion, or upstream main changes`
- Delivery mode: `local task branch -> focused and complete offline
  verification -> independent review -> human acceptance -> cohesive
  conventional commit -> local no-ff merge into yuto -> push only yuto ->
  verify github/yuto`

### Pre-Implementation And Expected Behavior

#### Pre-Implementation Baseline

- `src/atomgit/api.py` owns download endpoint/resolve construction, checksum
  policy, private resume state, managed-checkout manifest and locks, repository
  listing and path validation, POSIX/Windows pruning, redirect-safe standard
  and raw HTTP transport, framing, and `HuggingFaceAPI.download_repo` /
  `download_file` on the 5,074-line historical API module.
- Upload code later in the module owns `_download_remote_gitattributes`; it is
  an upload/LFS-policy helper and is not part of this download-domain Issue.
- `src/atomgit/atomgit_hub.py` owns SDK snapshot/file/URL/dataset downloads;
  SDK ownership is approved program step 10 and remains structurally untouched.
- Existing tests patch old-path dependencies and helpers on `atomgit.api`,
  including `urllib`, `httpx`, `get_hf_file_metadata`, `hf_http_get`,
  `_atomgit_open_url`, `_atomgit_v5_get_json`, transport/integrity/manifest
  helpers, and API instance methods.
- Locked contracts inspected in `atomgit_cli`: `huggingface-hub==1.1.7`,
  `datasets==4.4.1`, Click `8.4.2`; real `HfApi`, `hf_hub_download`, and
  `snapshot_download` signatures match the current dependency tests.

#### Expected

- Real download implementations live in non-placeholder `atomgit.download`
  modules separated by service, transport, integrity, manifest, resume, and
  prune ownership without duplicate implementations.
- `atomgit.api.HuggingFaceAPI` remains the historical concrete class and gains
  its two download methods through an owner mixin; `atomgit.api.api` remains an
  instance of that class and CLI dispatch is unchanged.
- Historical download helpers, exceptions, dependency objects, method objects,
  and signatures remain available at `atomgit.api`; assignments and deletions
  at the old module path propagate only to former resolution sites.
- Source, default PEP 660 editable, wheel, and sdist discovery include exactly
  the delivered download package without repository leakage.

### Scope

#### In Scope

- Add only download-domain modules receiving real implementation now.
- Move CLI API repository/file download orchestration, resolve URL and metadata,
  strong checksum verification, raw and standard HTTP download, redirect and
  framing policy, resume cache/locks, manifest transaction/locks, repository
  filename validation, and POSIX/Windows managed-file pruning.
- Preserve exact public/private symbols, class/singleton/method identities,
  signatures, old-path patches, anonymous/token behavior, repository-type
  resolution, default skip, force, checksum, resume, prune, retry, atomic
  replacement, error redaction, and output/return outcomes.
- Retain minimal compatibility aliases needed at `atomgit.api` and keep shared
  repository V5 aliases working for unextracted upload code.
- Update exact ownership, dependency, facade debt, artifact, src-layout,
  public-import, development-floor, architecture, and testing contracts.

#### Out Of Scope

- SDK `snapshot_download`, `download_file`, `hub_download_url`, or dataset
  loading ownership.
- `_download_remote_gitattributes` and any upload, resumable-upload, projection,
  LFS pointer/policy/transfer, or upload error implementation.
- CLI command extraction, converting `api.py` or `cli.py` into packages,
  removing `cli -> api`, changing public behavior or dependency versions.
- Logging/type/format sweeps, broad test-layout changes, live AtomGit writes,
  publication, lifecycle/distribution work, or unrelated cleanup.

### Affected Capability IDs

- `FLOOR-REGISTRY`, `DOWNLOAD-SNAPSHOT`, `DOWNLOAD-FILE`,
  `DOWNLOAD-INTEGRITY`, `DOWNLOAD-SECURITY`, `REPO-ID`, `CLI-SURFACE`,
  `CLI-DISPATCH`, `PACKAGING`, `PORTABILITY`, `DEPENDENCY-CONTRACT`, and
  `ERROR-REDACTION`

### Protected Existing Invariants

- All existing `98` invariants remain protected, especially `FLOOR-005..010`,
  `CLI-001..006`, `DISPATCH-001..005`, `DLSNAP-001..003`,
  `DLFILE-001..002`, `DLINT-001..003`, `DLSEC-001..003`, `REPOID-001..002`,
  `DEP-001..003`, `PKG-003/009..017`, `PORT-001..008`, and
  `REDACT-001..002`.
- Historical imports, API class/singleton, CLI dispatch, old-path download
  helpers/dependencies, exact output and return values, private cache modes,
  credential isolation, and atomic target/manifest semantics remain unchanged.
- SDK/download, upload/resumable/LFS and lifecycle/distribution behavior remain
  protected but structurally unmodified by this Issue.

### New Or Changed Invariants

- `FLOOR-011`: CLI API download implementations have exact download-domain
  owners while historical API symbols, method identities, signatures, and
  registered patch seams remain stable; ownership drift, placeholders, facade
  regrowth beyond the tightened ceiling, and forbidden dependency directions
  fail closed.
- `PKG-018`: source, default PEP 660 editable, wheel, and sdist surfaces include
  exactly the delivered download package and historical API module without
  repository leakage.

### Focused Tests And Evidence

- Add `tests/test_download_domain_ownership.py` for implementation provenance,
  exact owner modules, historical class/singleton/method/helper identities and
  signatures, assignment/deletion and dependency-module patch seams,
  non-owner negative cases, facade-debt tightening, placeholder rejection, and
  SDK/upload/LFS boundary non-migration.
- Re-run every registered download test plus repository ID, CLI schema/dispatch,
  redaction, structure, public-import, src-layout, packaging, dependency,
  portability, and development-floor scripts.
- Run final `python tests/run_cli_baseline.py`, `python -m compileall -q .`,
  `python -m pip check`, changed/new-file Black, isort, Ruff, and
  `git diff --check`.
- Controlled-remote evidence: `not applicable; no remote behavior changes and
  live writes are not authorized for this refactor`.

### Acceptance Criteria

1. Every moved CLI API download function, class, exception, or method has one
   real download-domain owner; no placeholder or duplicate implementation
   remains.
2. `atomgit.api.HuggingFaceAPI`, its two moved method objects/signatures, global
   `api`, CLI dispatch, and registered historical helper/dependency patch seams
   remain executable and unchanged.
3. Repository type/listing, safe destination, redirect credential isolation,
   raw HTTP framing, checksum, resume, retry, atomic replacement, manifest lock,
   and prune behavior retain exact offline evidence.
4. SDK downloads and upload/resumable/LFS implementation remain outside the
   download package and their contracts pass unchanged.
5. Structure and artifact contracts discover every nested download module,
   reject placeholders/unowned code, tighten API debt, and agree across source,
   editable, wheel, and sdist surfaces.
6. The ledger remains monotonic at `26 capabilities`, at least `100 invariants`,
   and at least `85 isolated pytest cases`.
7. Focused tests, complete offline baseline, supporting gates, and independent
   review pass with no open P0/P1/P2/P3 finding before acceptance or delivery.

### Verification Evidence

- Pre-edit focused evidence: `all 15 download/anonymous isolation scripts plus
  structure 13/13, public import 8/8, src layout 6/6, packaging 13/13,
  development floor 15/15, and predecessor ownership 20/20 passed. Direct
  pytest selection collected no tests because these are self-executing scripts;
  the run was correctly repeated by executing each script under the repository
  test policy. Locked versions and signatures were inspected and python -m pip
  check passed`
- Implementation evidence: `tests/test_download_domain_ownership.py 15/15,
  including full-map initial identity, assignment, deletion, and restoration;
  every existing download script passed; structure 13/13, packaging 13/13,
  public import 8/8, src layout 6/6, development floor 15/15, CLI baseline guard
  14/14, predecessor service ownership 20/20, infrastructure ownership 17/17,
  lifecycle ownership 23/23, and wheel smoke 36/36 passed. Ten focused
  upload/LFS/SDK boundary scripts passed, and an AST audit confirmed that only
  the exact planned download definitions left api.py. The API facade tightened
  from 5,074 lines / 110 top-level functions / 21 classes to 3,715 / 60 / 17;
  exact legacy tool debt tightened from Black 85/608, isort 88/108, and Ruff
  19/197 to Black 85/571, isort 87/105, and Ruff 19/196`
- Complete baseline: `an initial post-implementation run failed 84/85 only
  because the historical _windows_file_lock_module patch did not reach the new
  manifest owner. After registering the Windows manifest and prune seams,
  tests/test_windows_compatibility.py passed 12/12 and the final
  python tests/run_cli_baseline.py passed 85/85 in 85.71s. After the initial
  review P2 compatibility fix, the final run passed 85/85 in 89.87s`
- Supporting gates: `python -m compileall -q ., python -m pip check, changed/new
  Black 24.10.0, isort 5.13.2, Ruff 0.12.12, and git diff --check passed;
  source/default PEP 660 editable/wheel/sdist discovery contains the download
  package exactly and temporary packaging left no repository artifacts`
- Review: `initial verdict REQUEST CHANGES for one P2 old-path patch coverage
  gap; the full-map fix and complete re-verification passed, and the independent
  read-only re-review found no P0/P1/P2/P3 findings and returned APPROVED`
- Human acceptance: `accepted on 2026-08-19 +0800 after rerunning the complete
  85-case baseline (85 passed in 86.76s), wheel/editable smoke (36/36), and
  all final static/dependency gates; maintainer explicitly authorized commit,
  local merge, and push`
- Residual risks: `live AtomGit exercise is not authorized or required for an
  ownership-only refactor; Python 3.9 remains represented by declared/tooling
  contracts in the current Python 3.10 environment`

### Review Record

- Review phase: `complete after implementation fix and final verification`
- Verdict: `APPROVED`
- Open findings: `none. The initial P2 found that _PATCH_TARGETS covered only a
  subset of migrated helpers and dependencies. The accepted fix registers
  every former download resolution site, preserves overlaps with authentication
  and repository services through a deduplicated union, initializes exact
  shared identities before facade activation, and exhaustively tests
  assignment, deletion, and restoration for the complete download map`

## Maintainer Test Authorization

- Scope: `the ongoing code-structure development work only`
- Sole authorized test repository: `weixin_52273949/test_datasets`
- Web URL: `https://ai.atomgit.com/weixin_52273949/test_datasets`
- Git URL: `git@atomgit.com:weixin_52273949/test_datasets.git`
- Boundary: `do not use any other repository for development testing; do not
  delete, publish, or perform unrelated remote writes; keep credentials out of
  logs and commits`
