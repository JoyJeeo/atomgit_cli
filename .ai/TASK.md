# Current Issue Contract

Status: `active`

## Handoff Snapshot

- Updated: `2026-08-17 +0800`
- Phase: `implementation, verification, and independent review approved; ready for authorized release commit`
- Base branch: `yuto`
- Task branch: `release/1.1.0` (local only; never push)
- Base commit: `241ae7ab5a6b15a739f68848ceb2bf8ea6d1ed0c`
- Current HEAD: `241ae7ab5a6b15a739f68848ceb2bf8ea6d1ed0c`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `dirty only with release-owned source, tests, workflow, documentation, and TASK.md; generated build artifacts were moved outside the worktree after audit`
- Changed paths: `.ai/DEVELOPMENT_FLOOR.md`, `.ai/TASK.md`, `.github/workflows/release.yml`, `CHANGELOG.md`, `README.md`, `RELEASE_NOTES.md`, `deploy.sh`, `docs/architecture.md`, `docs/release.md`, `docs/upload_command_analysis.md`, `setup.py`, `tests/development_floor_contract.py`, `tests/test_cli_feature_baseline.py`, `tests/test_cli_surface.py`, `tests/test_deploy_script.py`, `tests/test_release_workflow.py`, `tests/test_update.py`, `tests/test_wheel_smoke.py`, `version.py`
- Last completed action: `final independent read-only review returned APPROVED with no open findings after all implementation and evidence corrections`
- Next exact action: `create the conventional release preparation commit, merge it locally into yuto, and push only yuto`
- Blockers: `publication is blocked until the release-approval GitHub environment is configured with a required maintainer reviewer; GitHub currently reports zero environments`
- Tests run for this phase: `after review fixes, python tests/run_cli_baseline.py passed 73/73 in 103.28s; focused release workflow passed 25/25, development-floor passed 15/15, and wheel smoke passed 27/27 with atomgit 1.1.0 and Production/Stable metadata; compileall, bash/sh syntax, pip check, locked dependency versions/signatures, git diff --check, secret-pattern audit, exact four-asset inventory, all three SHA-256 entries, wheel/sdist content audit, and LICENSE identity passed`
- Required worktree while uncommitted changes exist: `/Users/yutaozhang/yuto/codes/atomgit_cli`

## Active Issue

- Remote Issue: `none; local release Issue only`
- ID: `LOCAL-RELEASE-1.1.0`
- Title: `Publish AtomGit CLI 1.1.0 stable release`
- Primary type: `release`
- Secondary types: `distribution`, `documentation`, `testing`
- Priority: `P1`
- Observable objective: `publish an immutable, checksummed, pure-numeric GitHub Release 1.1.0 from the exact accepted yuto source after all release, development-floor, packaging, review, and protected-approval gates pass`
- User impact: `ordinary users receive the first completed pure-numeric Release selected by the official installer and updater, containing the accumulated post-1.0.6 upload, completion, distribution, and safety work`

## Authorization And Acceptance

- Version selection: `the maintainer explicitly selected stable version 1.1.0 on 2026-08-17`
- Authorized local actions: `edit release-owned version, changelog, documentation, tests, TASK.md, and release metadata; build temporary local artifacts; run offline tests and independent review; create release preparation commits; merge locally into yuto`
- Authorized remote actions: `push only the merged yuto branch; configure the release-approval environment needed by the accepted workflow contract; manually dispatch .github/workflows/release.yml for version 1.1.0 and the exact merged yuto SHA; approve the protected deployment only through the configured maintainer review; create the annotated 1.1.0 tag and public GitHub Release through that workflow`
- Prohibited actions: `push release/1.1.0 or any task branch; publish AtomGit CLI to PyPI/TestPyPI; create or mutate AtomGit repositories; alter historical tags/Releases; move or replace published 1.1.0 bytes; expose credentials; merge yuto into main`
- Human acceptance: `the maintainer explicitly requested end-to-end development, testing, verification, commit, push, and publication of 1.1.0; final publication still requires the workflow's protected environment approval and all technical gates`
- Delivery mode: `local release branch -> verified release commit -> local no-ff merge into yuto -> push only yuto -> protected manual workflow -> post-publication install verification`

## Evidence And Release Decision

- The repository was clean on `yuto` at `241ae7a`, synchronized with
  `github/yuto`, before this Issue was activated.
- At activation, `version.py` and current-version documentation reported
  `1.0.6`; the prepared release now derives and verifies `1.1.0` from that
  authoritative version source.
- GitHub contains only historical `v...` tags/Releases; no pure-numeric tag or
  completed Release exists, so `1.1.0` is available and is the channel cutover.
- The Stability Release Gate has recorded controlled remote evidence for model
  and dataset lifecycles, public/private behavior, and resumable interruption,
  resume, checksum readback, and cleanup. Revision behavior is implemented or
  explicitly rejected at the documented CLI/SDK boundaries.
- The accumulated post-`v1.0.6` scope includes upload retry and target
  hardening, batch lifecycle and sizing, Git LFS policy/pointer/preupload/slow
  flow recovery, macOS metadata filtering, fast Zsh completion, the executable
  development floor, and the protected GitHub Release/installer/updater path.
- GitHub reports no configured environments. The workflow references
  `release-approval`, so dispatch before adding a required reviewer would
  silently create an unprotected environment and violate the accepted release
  contract.
- Local artifact verification exposed that both checksum generators emitted a
  `dist/` path prefix that the strict installer correctly rejects; this Issue
  now includes the generator-side basename fix and executable regression.
- A second artifact simulation found that a wildcard included the redirected
  `SHA256SUMS` file in its own contents. The workflow now checks for exactly one
  wheel and sdist and hashes only the explicit wheel, sdist, and LICENSE assets.

## Current And Expected Behavior

### Prepared Local State

- Source, build metadata, CLI, tests, and current-version documentation identify
  as `1.1.0`.
- Accumulated post-1.0.6 changes and known limitations are recorded under dated
  `1.1.0` changelog and Release notes.
- The official resolver finds no completed pure-numeric Release and therefore
  fails safely instead of falling back to historical `v...` Releases.
- The GitHub `release-approval` environment has no configured protection.

### Expected

- All authoritative and mechanically checked version identities report
  `1.1.0`; current-version documentation agrees.
- `CHANGELOG.md` contains a dated `1.1.0` entry with the delivered scope and
  honest known limitations, and `Unreleased` remains available for future work.
- Focused release contracts, the complete baseline, isolated wheel smoke,
  compileall, pip check, dependency signatures, diff checks, and artifact and
  credential audits pass in the `atomgit_cli` environment.
- Independent review has no open P0/P1 finding.
- Only the merged `yuto` commit is pushed. The protected workflow creates an
  annotated `1.1.0` tag, exact assets and checksums, and a non-draft,
  non-prerelease Release whose tag resolves to that commit.
- A fresh user-view installation from the published checksummed wheel verifies
  distribution version, both CLI entry paths, and both Python imports.

## Scope

### In Scope

- Update the authoritative version to `1.1.0`.
- Add the dated 1.1.0 changelog/release notes and known limitations.
- Synchronize versioned README and technical-document statements.
- Replace current-version test literals with the authoritative version where
  this prevents future release drift; preserve scenario-specific SemVer values.
- Run all required offline, packaging, consistency, dependency, artifact, and
  credential checks.
- Perform independent review, commit, merge, push only `yuto`, configure the
  protected environment, dispatch the workflow, and verify publication.

### Out Of Scope

- New product features or unrelated defect fixes.
- Dependency upgrades or changes to the locked compatibility contracts.
- Historical tag/Release mutation or a `v1.1.0` alias.
- PyPI/TestPyPI publication, upstream `main` changes, or live AtomGit writes.

## Compatibility Requirements

- Preserve Python `>=3.9`, Click `8.4.2`, `huggingface-hub==1.1.7`, and
  `datasets==4.4.1` contracts.
- Preserve all public CLI/SDK schemas and existing development-floor
  invariants; this release changes version identity and distribution metadata,
  not runtime behavior.
- Preserve historical `v...` artifacts and ensure stable resolution considers
  only completed pure-numeric Releases.
- The official user artifact remains the checksummed universal wheel; sdist and
  LICENSE remain audit/archive assets.

## Affected Capability IDs

- `FLOOR-REGISTRY`: the release-notes publication guarantee is added to the
  monotonic executable invariant ledger.
- `CLI-SURFACE`: root `--version` must report the authoritative 1.1.0 identity
  without changing the command schema.
- `PACKAGING`: version metadata, wheel identity, installer/updater Release
  selection, local build checks, workflow assets, and checksums are release
  critical.
- `PORTABILITY`: the published universal wheel and supported Python boundary
  must remain valid across the registered platforms.

## Protected Existing Invariants

- `FLOOR-001` through `FLOOR-004`: the capability registry and mandatory gate
  remain complete, monotonic, isolated, and blocking.
- `CLI-001`: every public command and parameter remains in the exact schema.
- `PKG-001`: the isolated wheel provides the console entry point, module entry
  point, `import atomgit`, and `import atomgit_hub` without repository leakage.
- `PKG-002`: local packaging helpers build, install, inspect, and checksum only;
  they contain no PyPI/twine publication path.
- `PKG-003`: official installation preserves managed Zsh completion behavior.
- `PKG-004`: installation/update accepts only completed pure-numeric Releases
  and validates wheel identity/checksum before pip.
- `PKG-005`: publication occurs only through the manually dispatched protected
  workflow.
- `PORT-001` and `PORT-002`: Python 3.9+ syntax and cross-platform safety
  outcomes remain unchanged.

## New Or Changed Invariants

- `REL-110-001`: authoritative package, build metadata, CLI output, wheel
  metadata, tests, and current-version documentation agree on `1.1.0`.
- `REL-110-002`: the release branch is never pushed; the annotated `1.1.0` tag
  resolves to the exact merged and pushed `yuto` commit.
- `REL-110-003`: publication cannot enter the write job without a required
  maintainer review on the `release-approval` environment.
- `REL-110-004`: the public Release is non-draft, non-prerelease, has exact
  wheel/sdist/LICENSE/SHA256SUMS assets, and every checksum verifies.
- `REL-110-005`: a fresh isolated installation from the public checksummed
  Release passes all user entry-point and import checks.
- `PKG-006`: the protected publish job checks out the exact source before
  downloading reviewed assets, publishes version-matched notes, rejects
  public-Release mutation, and verifies the exact remote asset set and bytes.
- `REL-110-006`: generated `SHA256SUMS` entries use exact downloadable asset
  basenames, so strict installer validation accepts the published wheel.

## Acceptance Criteria

1. `version.py`, build metadata, package `__version__`, CLI `--version`, test
   contracts, and versioned docs consistently identify `1.1.0`.
2. `CHANGELOG.md` accurately describes the accumulated release scope and known
   limitations without claiming unverified behavior.
3. Focused release/version tests, `python tests/run_cli_baseline.py`, isolated
   wheel smoke, compileall, pip check, diff check, locked signatures, and final
   artifact/credential audit all pass after the last edit.
4. Independent review returns `APPROVED` with no open P0/P1 finding.
5. The release commit is merged locally into `yuto`; only `yuto` is pushed.
6. `release-approval` requires the maintainer reviewer before publish runs.
7. Workflow run succeeds for `version=1.1.0` and the exact merged `yuto` SHA.
8. Annotated tag and completed GitHub Release identities match the exact SHA;
   exact assets and checksums verify remotely and after download.
9. Fresh isolated installation of the published wheel passes version, CLI,
   module, and import smoke checks.

## Required Verification

- Focused: `tests/test_release_workflow.py`, `tests/test_cli_surface.py`,
  `tests/test_cli_feature_baseline.py`, `tests/test_update.py`,
  `tests/test_deploy_script.py`, and `tests/test_wheel_smoke.py`.
- Mandatory: `python tests/run_cli_baseline.py` after the final implementation
  edit and after any subsequent review fix.
- Packaging: clean wheel/sdist build, exact artifact inventory and SHA-256,
  isolated wheel smoke, `python -m compileall -q .`, `python -m pip check`, and
  locked dependency signature inspection.
- Audit: `git diff --check`, release-branch ancestry/status, no generated
  artifact or credential path in the commit, no secret-like diff content, and
  no unrelated change.
- Publication: environment protection API state, workflow run conclusion,
  annotated-tag target, Release draft/prerelease state, exact asset inventory,
  downloaded checksum verification, and isolated post-release installation.
- Live AtomGit evidence: `not rerun; this release changes no AtomGit remote
  behavior and relies on the accepted Stability Release Gate evidence already
  recorded in the roadmap and prior Issue delivery records`.

## Review Record

- Review status: `APPROVED in the final independent review after two REQUEST
  CHANGES rounds were fully corrected and reverified`.
- Review findings: `P1 .github/workflows/release.yml did not reject an existing
  public Release before asset mutation and did not verify the exact remote asset
  set and every post-upload digest before publication; P1 setup.py retained the
  Beta classifier despite the selected stable 1.1.0 identity; P2 workflow resume
  did not synchronize reviewed Release notes on an existing draft; second review
  found P2 TASK.md evidence drift because setup.py and test_wheel_smoke.py were
  absent from the changed-path list and PKG-006 retained its pre-fix wording`.
- Open findings: `none`.
- Residual risks to inspect: `GitHub environment protection availability and
  self-review rules; partial workflow failure after immutable tag creation;
  unauthenticated installer API rate limits; platform-specific PEP 668 behavior;
  updater recovery is guidance rather than atomic dependency rollback`.
