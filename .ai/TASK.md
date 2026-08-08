# Current Issue Contract

Status: `completed`

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

- Updated: `2026-08-08 16:55:00 +0800`
- Status: `completed`
- Phase: `1.0.6 GitHub Release delivered and verified`
- Base branch: `yuto`
- Task branch: `none; release changes on yuto`
- Base commit: `01d9669`
- Current HEAD: `5a41e6a`
- Worktree state: `clean before this closure update`
- Changed paths: `.ai/TASK.md closure record only`
- Required worktree: `none after closure commit`
- Last completed action: `published and post-download verified GitHub Release v1.0.6`
- Next exact action: `await next explicit user request`
- Blockers / open questions: `none; PyPI publication remains out of scope`
- Decisions constraining the next action: `package version and Git tag are both 1.0.6/v1.0.6; GitHub Release publication is authorized by the direct user request; no PyPI or AtomGit remote writes`
- Tests passed: `CLI surface 50/50; installer 14/14; wheel smoke 21/21; deploy script 13/13; complete CLI baseline 62/62; compileall, pip check, and git diff --check; final wheel/sdist/LICENSE checksums; post-publication download checksum verification`
- Tests failed or not run: `no failures; PyPI publication intentionally not run`

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

- Release commit: `5a41e6a release: publish atomgit 1.0.6`
- Annotated tag: `v1.0.6`, peeled commit `5a41e6a`
- GitHub Release: `https://github.com/JoyJeeo/atomgit_cli/releases/tag/v1.0.6`
- Assets: `atomgit-1.0.6-py3-none-any.whl`, `atomgit-1.0.6.tar.gz`, `LICENSE`, `SHA256SUMS`
- Review: `APPROVED after correcting mutable yuto installer URLs to v1.0.6`
- Human acceptance: `explicit publication request received`
- Excluded actions: `no PyPI publication, AtomGit remote write, Issue transition, deletion, or history rewrite`
