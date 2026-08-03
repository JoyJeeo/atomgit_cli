# Current Release Contract

Status: `completed`

## Release Identity

- ID: maintainer-authorized release task, 2026-08-03
- Package version: `1.0.5+yuto.1`
- Current tag: `v1.0.5-yuto.1`
- Historical tags: `v1.0.0`, `v1.0.1`, `v1.0.2`, `v1.0.3`, `v1.0.5`
- Channel: GitHub Release on `JoyJeeo/atomgit_cli`
- Release type: formal GitHub Release, package status remains Beta
- Human owner and copyright holder: JoyJeeo
- License: Apache License 2.0

## Scope

- Add the approved license and align package metadata with the `yuto` source.
- Give the current package an identity distinguishable from upstream PyPI.
- Correct release-facing documentation that describes already fixed defects.
- Build wheel and source artifacts for every installable version node and
  generate SHA-256 checksums. Preserve `v1.0.0` as a source-only archive
  because its immutable packaging cannot pass the installation contract.
- Verify every published wheel in an isolated environment before publication.
- Create annotated tags at the exact historical version commits and the release
  commit, then create GitHub Releases with assets and notes.
- Verify the current release again from downloaded public artifacts.

## Historical Mapping

- `v1.0.0`: `61a28a51e8e145bb2ea821d2acf408d6af00d40e`
- `v1.0.1`: `1c499d51e4eec5636e51a2c2ba387bbae002cd6b`
- `v1.0.2`: `08ba91dfadf0a0f95192618256871a33d8a67d52`
- `v1.0.3`: `4e1e093f6b31cafa1034778a7d5c12180f2a3c2d`
- `v1.0.5`: `86fc7096810df27baff5a0a8b03ff752b6dec181`

## Permissions

- The maintainer explicitly authorized Apache-2.0 licensing, version changes,
  annotated tags, tag pushes, and formal GitHub Releases.
- The maintainer explicitly required all existing Issues to remain open and
  otherwise unchanged.
- PyPI publication, AtomGit repository publication, Issue transitions, remote
  deletion, and history rewriting are not authorized.

## Required Evidence

- Three public version values and package metadata agree.
- Complete offline suite, compileall, and diff checks pass.
- Each publishable wheel reports the expected version and passes CLI/module
  import smoke tests after isolated installation. Historical versions that
  cannot pass remain source-only archives with the failure documented.
- Every installable release includes wheel, source archive, and `SHA256SUMS`;
  the documented `v1.0.0` source-only exception includes its source archive,
  license, dependency reference, and checksums but no supported wheel.
- The current release artifact is downloaded and reverified after publication.
- Independent release review returns `APPROVED` before tags or Releases are
  created.

## Delivery Record

- Implementation: license, version identity, metadata, changelog, and current
  behavior documentation updated on the release branch.
- Offline validation: all 12 test scripts, compileall, and diff checks passed.
- Current build: `1.0.5+yuto.1` wheel and sdist built; a clean virtual
  environment passed `atomgit --version`, both help entry points, and imports
  for `atomgit` and `atomgit_hub`. The wheel contains the Apache-2.0 license.
- Historical builds: `v1.0.1`, `v1.0.2`, `v1.0.3`, and `v1.0.5` built and
  passed the same isolated wheel smoke tests.
- Reproducibility: all published wheels were reproduced byte-for-byte with the
  same full build pipeline and commit epoch. Deterministic `git archive` source
  packages were generated twice and compared byte-for-byte for every tag;
  setuptools sdists were excluded because their archive timestamps varied.
- `v1.0.0` exception: its committed package metadata contains no dependencies,
  and top-level `import atomgit_hub` fails even after installing the intended
  dependencies. Preserve the tag but publish it only as a clearly marked
  source-history archive; do not attach a wheel as a supported artifact.
- Independent review: initial `REQUEST CHANGES` for the `v1.0.0` artifact
  contract and README checksum instructions; both findings were corrected.
  Re-review found no blocking issues and returned `APPROVED`.
- Tags: annotated `v1.0.0`, `v1.0.1`, `v1.0.2`, `v1.0.3`, `v1.0.5`, and
  `v1.0.5-yuto.1` tags were pushed and verified against their contracted
  commits. No existing tag was moved or rewritten.
- Releases: all six GitHub Releases were created. Historical Releases are not
  Latest; `v1.0.5-yuto.1` is the formal Latest Release and is neither Draft nor
  Pre-release: https://github.com/JoyJeeo/atomgit_cli/releases/tag/v1.0.5-yuto.1
- Post-release verification: all four public assets were downloaded from
  GitHub, `SHA256SUMS` passed, and the downloaded wheel passed the version,
  both CLI help entry points, and both import checks in a new virtual
  environment.
- Issue state: Issues #1, #3, #4, #5, #6, and #7 were checked after release and
  remain Open as explicitly required by the maintainer.
- PyPI, AtomGit publication, Issue transitions, remote deletion, and history
  rewriting were not performed.
