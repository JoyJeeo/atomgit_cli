# Current Issue Contract

Status: `active`

This is the repository's single persistent handoff for active, multi-turn, or
cross-conversation work. It records task facts and permissions; it does not
authorize work by itself. When inactive, the current user request and real Git
state determine what may happen next.

The most recently delivered Issue was `CLI-UPLOAD-DEFAULT-RESUME`, merged into
`yuto` by `36d9d11`. Its complete contract and evidence remain available in Git
history.

## Handoff Snapshot

Populate this section when an Issue becomes active and refresh it at meaningful
workflow checkpoints. Use repository-relative paths and never include tokens,
credential contents, signed URLs, or raw secret-bearing logs.

- Updated: `2026-08-08 16:45:00 +0800`
- Status: `active`
- Phase: `release implementation verified; awaiting commit and tag`
- Base branch: `yuto`
- Task branch: `none; release changes on yuto`
- Base commit: `01d9669`
- Current HEAD: `01d9669`
- Worktree state: `dirty with uncommitted release-version changes`
- Changed paths: `version metadata, installer, changelog, release docs, version tests`
- Required worktree: `continue in this root worktree while release changes are uncommitted`
- Last completed action: `verified version-specific CLI, installer, wheel, baseline, compile, and diff checks; fixed release installer URLs`
- Next exact action: `commit release changes, rebuild artifacts from commit, then create tag and GitHub Release`
- Blockers / open questions: `none; PyPI publication remains out of scope`
- Decisions constraining the next action: `package version and Git tag are both 1.0.6/v1.0.6; GitHub Release publication is authorized by the direct user request; no PyPI or AtomGit remote writes`
- Tests passed: `CLI surface 50/50; installer 14/14; wheel smoke 21/21; deploy script 13/13; complete CLI baseline 62/62; compileall, pip check, and git diff --check passed`
- Tests failed or not run: `post-publication artifact download verification pending; final artifacts will be rebuilt after commit`

## Active Issue Identity

- ID: `RELEASE-1.0.6`
- Title: `Publish AtomGit CLI 1.0.6`
- Primary type: `release`
- Priority: `P1`
- Base branch: `yuto`
- Delivery mode: `local commit, annotated tag, GitHub Release`
- Permissions: `commit=yes; tag=yes; push=yes; GitHub Release=yes; PyPI=no; AtomGit remote writes=no; Issue transitions=no`

## Evidence And Objective

- Objective: publish a reproducible `1.0.6` wheel/source release whose installed CLI and SDK report the same version.
- Scope: version metadata, installer defaults, release notes, packaging tests, artifacts, checksum file, annotated tag, and GitHub Release.
- Non-goals: PyPI publication, AtomGit operations, dependency upgrades, and unrelated refactoring.

## Scope And Acceptance

- `setup.py`, `__init__.py`, CLI version output, installer, tests, and release documentation agree on `1.0.6`.
- Complete offline baseline and packaging smoke checks pass.
- Wheel, source archive, and `SHA256SUMS` contain no credentials or generated repository state.
- Tag `v1.0.6` points at the release commit and GitHub Release assets are downloadable and checksum-verifiable.

## Evidence And Objective

For an active Issue, record the user impact, reproducible evidence, current
behavior, expected behavior, affected call path, and one observable objective.

## Scope And Acceptance

For an active Issue, record in-scope work, explicit non-goals, compatibility
requirements, observable acceptance criteria, required offline tests, and any
separately authorized live tests.

## Decisions And Rationale

Record only decisions that affect the active Issue, including rejected options
when their rejection prevents the next conversation from repeating unsafe or
invalid work. Move stable product or architectural decisions into the relevant
authoritative `.ai` or `docs` document.

## Verification Evidence

Record exact commands, environment, exit status or test count, offline or live
classification, review findings and dispositions, residual risk, and checks not
run. A statement such as "tests pass" is not sufficient.

## Closure

After authorized delivery, record commit or PR references, final evidence,
review verdict, human acceptance, and remaining follow-ups. Set the status to
`completed` only after the Issue contract is satisfied, then reset this file to
`inactive` before selecting another Issue. Git history retains the completed
contract.
