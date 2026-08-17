# AtomGit CLI 1.1.0

This is the first stable pure-numeric AtomGit CLI Release and the cutover to
the checksummed GitHub Release installation and update channel.

## Highlights

- Hardened resumable model and dataset uploads with exact AtomGit endpoint and
  target validation, bounded commit retries, configurable batches, lifecycle
  progress, and recovery for persistently slow LFS flows.
- Added automatic Git LFS policy repair and synchronization, canonical pointer
  generation, bounded preupload failure handling, and default macOS metadata
  filtering for directory uploads.
- Added dynamic Zsh completion through a lightweight import path, with managed
  completion enabled by default in the official installer.
- Added `atomgit update` for checksum-verified updates of wheel installations;
  source and editable installations remain Git-managed.
- Established the executable development floor and mandatory complete offline
  baseline across CLI, SDK, dependency, packaging, security, and portability
  contracts.
- Standardized protected GitHub Release publication with an authoritative
  version source, immutable `X.Y.Z` tags, checksummed assets, and no AtomGit CLI
  publication to PyPI.

## Known Limitations

- `install.sh` supports POSIX/macOS/Linux. Windows users must follow the README
  procedure to verify and install the universal wheel.
- `atomgit update` refuses source/editable installations and directs developers
  to update the `yuto` checkout with Git.
- Failed update verification prints an exact recovery command, but dependency
  rollback is not atomic; use an isolated venv or conda environment for
  production installations.
- Release discovery depends on GitHub API availability and rate limits. It does
  not fall back to PyPI, branch archives, or historical `v...` Releases.

See `CHANGELOG.md` for the full version history and `docs/release.md` for the
artifact and verification policy.
