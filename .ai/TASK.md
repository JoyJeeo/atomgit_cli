# Current Issue Contract

Status: active

## Handoff Snapshot

- Updated: `2026-08-24`
- Phase: `implemented; focused and complete offline verification passed; independent review in progress`
- Base branch: `yuto`
- Base commit: `92032d4cec9b6b2c6fe2032fa1c3d509583dee5c`
- Task branch: `codex/arch-cli-sdk-parity` (local only)
- Current HEAD: `92032d4 docs(ai): record cli facade delivery; uncommitted task changes`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `dirty with task-owned architecture, interface, contract, test, and documentation changes; no generated artifacts`
- Last completed action: `implemented core/domain/usecase/interface/adapter/compatibility boundaries and native AtomGitClient; complete baseline passed 92/92`
- Next exact action: `finish independent review, rerun the complete baseline after any review fix, record human acceptance, commit the task branch, merge locally into yuto, push only yuto, and verify remote equality`
- Blockers: `none; controlled remote tests are authorized only in
  weixin_52273949/test_datasets as recorded below; remote Issue work,
  repository deletion, credential mutation, and publication remain unauthorized`
- Tests for this implementation: `test_architecture_parity.py 11/11; structure guard 14/14; src-layout 6/6; development floor 15/15; packaging metadata 13/13; wheel/editable/sdist 37/37; python tests/run_cli_baseline.py 92 passed after the final fix; compileall, pip check, diff check, Ruff, Black, and isort passed`
- Residual risk: `no controlled remote evidence was run; resumable native-SDK uploads bridge the verified CLI transfer owner through a scoped token context while full vertical-slice extraction remains follow-up work; source/tests/Git remain authoritative`

The predecessor CLI Facade Conversion Issue is complete, accepted, committed,
merged, pushed, and remotely verified. Task commit `9d00e50`, local merge
`4808a44`, and final record `92032d4` are historical evidence only. Local
`yuto`, `github/yuto`, and `github/HEAD` resolve to `92032d4`.

## Active Issue

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

- The maintainer explicitly authorized implementation, verification, commit, local merge, and push in this turn; source, tests, contracts, packaging, and documentation are in scope.
- Delivery mode is local task branch -> independent review -> human acceptance by this explicit delivery request -> cohesive commit -> local no-ff merge into yuto -> push only yuto -> remote equality verification.
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
- Human acceptance is required before delivery or closure. After acceptance, standing project rules allow one cohesive conventional commit, local no-ff merge into yuto, push only yuto, fetch, and remote equality verification; never push the task branch.

## Independent Review

- Verdict: `APPROVED`
- Findings: `no open P0/P1/P2/P3 findings after the token-aware adapter and scoped credential-context fixes`
- Review evidence: `complete diff, locked HF 1.1.7 signatures, structure/ownership/artifact contracts, credential scan, focused parity test, and final 92-case baseline reviewed; no live AtomGit write was run`
- Residual review risk: `native resumable uploads bridge the verified CLI transfer owner through a ContextVar token scope; deeper vertical-slice extraction and controlled remote acceptance remain follow-up evidence, not hidden behavior changes`

## Definition Of Done

- [x] Phase 1 and Phase 2 remain separate and each has observable acceptance evidence.
- [x] Capability IDs, protected invariants, and new invariants agree with executable registries.
- [x] No behavior change is hidden in Phase 1.
- [x] Every general remote CLI capability has a native SDK counterpart or an explicit CLI-only classification.
- [x] Old imports, signatures, identities, patch seams, entry paths, and package artifacts remain compatible.
- [x] Focused, complete baseline, dependency, packaging, security, portability, compile, lint, and diff checks pass.
- [x] Independent review is APPROVED with no open blocking finding.
- [x] Human acceptance and final delivery evidence are recorded by the explicit commit/push request in this turn.
- [x] Remaining risks, unrun tests, and controlled-remote limitations are explicit.
