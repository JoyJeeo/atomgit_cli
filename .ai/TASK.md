# Current Issue Contract

Status: inactive

## Handoff Snapshot

- Updated: `2026-08-18 +0800`
- Phase: `completed, accepted, committed, locally merged, pushed, and remotely
  verified`
- Base branch: `yuto`
- Base commit: `4f92e786c9a070511d15043f1b650c77c45d88e7`
- Base synchronization: `yuto`, `github/yuto`, and `github/HEAD` all resolved
  to the base commit; the worktree was clean before branch creation`
- Task branch: `codex/auth-repository-services-ownership` (local only; never
  push)
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `clean on yuto before this final delivery record commit`
- Task commit: `e6525ccb58099ffdfed56df54fdd9a94473bcc3f`
- Local yuto merge: `de842819dc726fdf2a3fd3b586b984f4a7dd670e`
- Verified remote yuto: `de842819dc726fdf2a3fd3b586b984f4a7dd670e`
- Last completed action: `created the cohesive task commit, merged it into
  yuto with --no-ff, pushed only yuto, fetched github/yuto, and verified both
  at de84281`
- Next exact action: `none for this completed Issue; wait for an explicit new
  development request before activating another Issue`
- Blockers: `none`

Delivery evidence: task commit `e6525cc`; local no-ff merge `de84281`; initial
remote verification resolved `github/yuto` to
`de842819dc726fdf2a3fd3b586b984f4a7dd670e`. The task branch remained local and
was never pushed. No remote Issue/PR, tag, Release, publication, live AtomGit
write, credential mutation, deletion, or upstream-main change was performed.

The predecessor lifecycle Issue is complete, accepted, committed, locally
merged, pushed, and remotely verified. Its task commit is `8e639b5`, local
merge is `b3f0c81`, and final delivery record is `4f92e78`. The record's
historical `b3f0c81` remote verification and the actual final synchronized HEAD
do not conflict: `4f92e78` contains only the later delivery record.

## Active Issue

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-REFACTOR-AUTH-REPOSITORY-SERVICES-OWNERSHIP`
- Title: `Extract authentication and repository service ownership behind the
  historical API class`
- Primary type: `refactoring`
- Secondary types: `compatibility`, `testing`, `security`, `distribution`,
  `documentation`
- Priority: `P2`
- Observable objective: `move authentication, bounded AtomGit V5 JSON policy,
  and repository create/list/visibility/delete/branch/info implementation into
  owned service modules while preserving atomgit.api symbols, class/method and
  singleton identities, signatures, module-object patch seams, CLI outcomes,
  artifacts, and credential/remote-state safety`
- User impact: `none by design; internal ownership migration only`

### Authorization And Delivery

- User authorization: `the maintainer approved the complete sequential
  capability-oriented structure program on 2026-08-18 and explicitly requested
  continued development on 2026-08-18; the persisted sequence identifies
  auth/repository services as step 6 after lifecycle ownership`
- Approved program step: `6. Authentication And Repository Services Ownership`
- Accepted conditions:
  1. `authentication and repository modules are created only as their real
     implementation moves`
  2. `atomgit.api.HuggingFaceAPI and the global atomgit.api.api object remain
     the historical class and singleton surfaces`
  3. `old-path direct, private, module-object, and patch.object seams remain
     effective at the same former call sites`
  4. `authentication, V5 request bounds/redaction, repository final-state
     verification, and ambiguous-write outcomes remain unchanged`
  5. `no download, upload, resumable, LFS, SDK, CLI command, API facade, CLI
     facade, lifecycle, or distribution ownership extraction is included`
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

- `src/atomgit/api.py` owns the bounded V5 JSON request and error-redaction
  helpers plus authentication and repository management methods on the
  5,496-line `HuggingFaceAPI` class.
- The same module also owns later download, upload, resumable, and LFS code;
  those paths consume selected V5 helpers and are deliberately not part of this
  Issue.
- `src/atomgit/cli.py` imports and dispatches through the historical global
  `atomgit.api.api` instance, leaving the registered `cli -> api` dependency
  debt until the later API/CLI facade program steps.
- Existing callers and tests instantiate `atomgit.api.HuggingFaceAPI`, patch
  its global `api` object, and patch old-path objects including `urllib`,
  `json`, `config`, `create_repo`, `_atomgit_open_url`, `_atomgit_v5_get_json`,
  `_atomgit_repo_exists`, and private error/normalization helpers.

#### Expected

- Real authentication and repository implementations live in non-placeholder
  `atomgit.services` modules with exact service ownership.
- `atomgit.api.HuggingFaceAPI` remains the historical concrete class and gains
  the exact moved methods through owner mixins; `atomgit.api.api` remains an
  instance of that class and CLI dispatch is unchanged.
- Historical method objects resolve to their service owners with unchanged
  signatures, while direct assignment, deletion/restoration, and module-object
  patches at `atomgit.api` reach only the former resolution sites.
- Shared V5 request/repository helpers have one service owner and remain
  available at their historical private paths for unextracted transfer code.
- Source, default PEP 660 editable, wheel, and sdist discovery include every
  delivered services module exactly without repository leakage.

### Scope

#### In Scope

- Add only authentication and repository service modules that receive real
  implementation in this Issue; no placeholders.
- Move login validation/user lookup, stored-user lookup, bounded V5 JSON
  exchange, credential-safe V5 error policy, repository ID path/private-state
  parsing, existence probe, create classification, repository list,
  visibility, deletion, branch creation, create, and unsupported info behavior
  to explicit owners.
- Preserve historical public/private symbols, class/singleton/method identities,
  signatures, direct and `patch.object` behavior, exact CLI output/exit and
  error categories, response bounds, private credential persistence, normalized
  IDs, ambiguous-write reconciliation, and final-state verification.
- Keep the minimal compatibility aliases needed by unextracted download/upload
  code at `atomgit.api` without moving those transfer implementations.
- Update exact ownership, dependency, facade debt, artifact, src-layout,
  public-import, development-floor, architecture, and testing contracts.

#### Out Of Scope

- Download, upload, resumable, projection, LFS, SDK, or CLI command ownership.
- Converting `api.py` or `cli.py` into a package/facade, removing `cli -> api`,
  changing the `HuggingFaceAPI` public shape, or moving the global singleton.
- Public behavior changes, dependency upgrades, exception redesign,
  logging/type/format sweeps, broad test-layout changes, live operations,
  publication, lifecycle/distribution work, and unrelated debt cleanup.

### Affected Capability IDs

- `FLOOR-REGISTRY`, `AUTH-CONFIG`, `REPO-MANAGEMENT`, `REVISION`, `REPO-ID`,
  `CLI-SURFACE`, `CLI-DISPATCH`, `PACKAGING`, `PORTABILITY`,
  `DEPENDENCY-CONTRACT`, and `ERROR-REDACTION`

### Protected Existing Invariants

- All existing `96` invariants remain protected, especially `FLOOR-005..009`,
  `CLI-001..006`, `DISPATCH-001..005`, `AUTH-001..003`, `REPO-001..003`,
  `REV-001..002`, `REPOID-001..002`, `DEP-001..003`, `PKG-003/009..016`,
  `PORT-001..008`, and `REDACT-001..002`.
- Historical `atomgit.api` imports, `HuggingFaceAPI`, global `api`, CLI
  dispatch, old-path private helpers/module objects, exact login/repository
  output, response bounds, redaction, repository normalization, and verified
  remote-state semantics remain unchanged.
- Every download/upload/resumable/LFS/SDK behavior and its patch seams remain
  protected but structurally unmodified by this Issue.

### New Or Changed Invariants

- `FLOOR-010`: authentication and repository service implementations have
  exact owners while the historical API class/singleton and registered old-path
  symbols, method identities, signatures, and patch seams remain stable;
  ownership drift, placeholders, API facade regrowth beyond the tightened
  ceiling, and forbidden dependency directions fail closed.
- `PKG-017`: source, default PEP 660 editable, wheel, and sdist surfaces include
  exactly the delivered services package and historical API module without
  repository leakage.

### Focused Tests And Evidence

- Add `tests/test_auth_repository_services_ownership.py` for implementation
  provenance, exact ownership, historical class/singleton/method identities and
  signatures, direct/private/module-object patch seams, non-owner negative
  cases, facade-debt tightening, placeholder rejection, and transfer-boundary
  non-migration.
- Re-run authentication, login/config, create, list, visibility, delete,
  branch, repo-info, repo-ID, CLI schema/dispatch, redaction, structure,
  public-import, src-layout, packaging, dependency, portability, and
  development-floor scripts.
- Run the mandatory final `python tests/run_cli_baseline.py`,
  `python -m compileall -q .`, `python -m pip check`, changed/new-file Black,
  isort, and Ruff checks, and `git diff --check`.
- Controlled-remote evidence: `not applicable; no remote behavior changes and
  live writes are not authorized for this refactor`

### Acceptance Criteria

1. Every moved authentication/repository function or method has one real
   service owner; no placeholder or duplicate implementation remains.
2. `atomgit.api.HuggingFaceAPI`, its moved method objects and signatures, the
   global `api`, CLI dispatch, and all registered historical patch seams remain
   executable and unchanged.
3. Bounded identity/V5 JSON parsing, credential safety/redaction, repository
   normalization, create/list/visibility/delete/branch/info outcomes, and
   ambiguous-write final-state verification retain exact offline evidence.
4. Download/upload/resumable/LFS and SDK implementation remains outside the
   services package and its behavior contracts pass unchanged.
5. Structure and artifact contracts discover every nested services module,
   reject placeholders/unowned code, tighten API debt, and agree across
   source/editable/wheel/sdist surfaces.
6. The ledger remains monotonic at `26 capabilities`, at least `98 invariants`,
   and at least `84 isolated pytest cases`.
7. Focused tests, complete offline baseline, supporting gates, and independent
   review pass with no open P0/P1/P2/P3 finding before acceptance or delivery.

### Verification Evidence

- Pre-edit focused evidence: `the authentication, login/config, repository
  management, branch, repo-ID, API import, CLI dispatch, structure, packaging,
  and development-floor scripts passed before extraction; dependency
  inspection confirmed huggingface-hub==1.1.7, datasets==4.4.1, Click 8.4.2,
  and setuptools 81.0.0. The pre-edit run was recorded per script rather than
  as one aggregate count`
- Implementation evidence: `tests/test_auth_repository_services_ownership.py
  20/20; tests/test_structure_guard.py 13/13;
  tests/test_packaging_metadata.py 13/13; new services and ownership files
  pass pinned Black 24.10.0, isort 5.13.2, and Ruff 0.12.12. The executable
  ledger is 26 capabilities, 98 invariants, and 84 isolated cases. The API
  facade tightened from 5,496 lines / 121 top-level functions / 21 classes to
  5,074 / 110 / 21. Exact legacy tool debt tightened from Black 85/627,
  isort 88/109, and Ruff 19/205 to Black 85/608, isort 88/108, and Ruff
  19/197`
- Complete baseline: `final delivery python tests/run_cli_baseline.py passed:
  84 passed in 85.44s on 2026-08-18 +0800. An earlier implementation run
  failed 83/84 because the exact API facade-body contract still held the
  pre-extraction count; after synchronizing the exact contract, the next run
  passed 84/84. The baseline was rerun after both review fixes and once more
  immediately before delivery`
- Supporting gates: `final tests/test_wheel_smoke.py 36/36 and
  tests/test_src_layout_migration.py 6/6 passed; python -m compileall -q .,
  python -m pip check (No broken requirements found), and git diff --check
  passed. Source/default PEP 660 editable/wheel/sdist discovery contains the
  services package exactly and leaves no build artifacts`
- Review: `initial independent review requested changes for two P2 findings:
  the historical _is_not_found_error patch did not reach repository existence
  probing, and this Issue's import aliases grew isort/Ruff debt. Both were
  fixed with regression coverage and explicit compatibility re-exports;
  the final read-only re-review found no P0/P1/P2/P3 findings and returned
  APPROVED`
- Human acceptance: `accepted on 2026-08-18 +0800 through the maintainer's
  explicit instruction to self-test, accept, commit, and push; the condition
  was satisfied by the final 84/84 baseline and all supporting delivery gates`
- Residual risks: `no live AtomGit exercise was run because observable remote
  behavior did not change and live writes were not authorized; Python 3.9 is
  represented by declared/tooling/signature contracts in the current Python
  3.10 environment`

### Review Record

- Review phase: `complete after implementation fixes and final verification`
- Verdict: `APPROVED`
- Open findings: `none; the prior P2 old-path not-found policy forwarding gap
  is fixed and covered, and the prior P2 isort/Ruff debt growth is reversed
  below the pre-Issue baseline`

## Maintainer Test Authorization

- Scope: `the ongoing code-structure development work only`
- Sole authorized test repository: `weixin_52273949/test_datasets`
- Web URL: `https://ai.atomgit.com/weixin_52273949/test_datasets`
- Git URL: `git@atomgit.com:weixin_52273949/test_datasets.git`
- Boundary: `do not use any other repository for development testing; do not
  delete, publish, or perform unrelated remote writes; keep credentials out of
  logs and commits`
