# Changelog

This project uses Git tags for immutable source history. The `yuto` line uses a
distinct package version and tag so users can distinguish it from upstream
PyPI releases.

## Unreleased

## 1.1.1 - 2026-08-17

- Scope dynamic Zsh completion to the active conda environment with dedicated
  activation and deactivation hooks, exact Click function cleanup, atomic
  installation, and explicit migration from the 1.1.0 global `.zshrc` setup.
- Add confirmed `atomgit uninstall` and the official `uninstall.sh` curl
  entrypoint, preserving configuration, credentials, caches, repositories, and
  all unrelated environment files.
- Detect direct pip removal through the standalone activation hook and print an
  exact, read-only official cleanup warning until the user runs that cleanup.
- Keep non-conda and venv installation supported while accurately skipping
  conda-only completion, and refresh only a matching environment during update.
- Extend the executable development floor to 74 isolated offline scripts and
  78 registered invariants, including real Zsh environment switching, legacy
  migration safety, symlink-parent rejection, and installed/already-removed
  uninstall paths.

Known limitations:

- Environment-managed automatic completion requires conda and Zsh; other
  installations remain fully usable without automatic completion.
- Completion and uninstall child processes cannot unload functions already
  present in their parent shell, so they print reactivation or `exec zsh`
  guidance.
- `install.sh` and `uninstall.sh` support POSIX/macOS/Linux. Windows users use
  the checksummed wheel workflow and Python package tools.

## 1.1.0 - 2026-08-17

- Harden resumable model and dataset uploads with exact AtomGit endpoint and
  target validation, bounded commit retries, configurable batches, lifecycle
  progress, and recovery for persistently slow LFS flows.
- Automatically repair and synchronize repository Git LFS policy, emit
  canonical pointers, bound preupload failures, and ignore macOS metadata by
  default during directory uploads.
- Add dynamic Zsh completion with a lightweight import path and default managed
  completion setup in the checksummed ordinary-user installer.
- Establish the executable development-floor registry and mandatory complete
  offline baseline for CLI, SDK, dependency, packaging, security, and
  portability invariants.
- Standardize GitHub Release as the only official publication channel, with a
  single authoritative version source, immutable pure-numeric tags, protected
  manual publication, checksummed wheel installation, and `atomgit update`.
- Separate ordinary wheel installation and updates from the documented
  Git/conda/editable source-development workflow.

Known limitations:

- `install.sh` supports POSIX/macOS/Linux; Windows installation uses the
  checksummed universal wheel procedure documented in the README.
- Source/editable installations must update through Git and are intentionally
  refused by `atomgit update`.
- Update verification provides an exact recovery command, but arbitrary
  third-party dependency rollback is not atomic; isolated environments remain
  recommended.
- GitHub Release discovery is subject to GitHub API availability and rate
  limits and never falls back to PyPI, a branch archive, or historical `v...`
  Releases.

## 1.0.6 - 2026-08-08

- Make directory uploads resumable by default, with an explicit ordinary-upload
  opt-out and stable prefix-aware upload projections.
- Add the monotonic CLI baseline gate and complete offline contract coverage for
  authentication, repository management, uploads, downloads, packaging, and
  portability.
- Clarify ordinary large-directory upload behavior, ignore-pattern statistics,
  server-side LFS deduplication, batching guidance, and sleep/wake expectations.

## 1.0.5+yuto.1 - 2026-08-03

- Add upload progress, repository path/type/revision/ignore controls, resumable
  large-folder uploads, direct single-file uploads, and actionable errors.
- Fix resumable authentication for `huggingface-hub==1.1.7` and verify a real
  interrupted 404 MB upload through final SHA-256.
- Support AtomGit dataset transfers and local-snapshot `load_dataset` behavior.
- Restore CLI Hugging Face timeout/progress state after upload operations.
- Restrict credential directories and files to `0700` and `0600` where the
  platform supports POSIX permission bits.
- Retry interrupted downloads once and sanitize signed URLs from errors.
- Add repository AI engineering, testing, review, and release specifications.
- License the `yuto` distribution under Apache License 2.0.

Known limitations:

- AtomGit revision branch semantics and multi-level repository IDs are not
  fully verified remotely.
- Python SDK upload still has known parameter, temporary-path lifetime, and
  timeout-restoration gaps; CLI upload paths have the stronger coverage.
- The versioned `curl` installer is not yet implemented; install the checksummed
  wheel from GitHub Releases.

## 1.0.5 - 2026-07-14

- Optimize upload behavior and update the upstream package version.

## 1.0.3 - 2026-07-14

- Add configurable CLI upload timeouts.

## 1.0.2 - 2025-12-02

- Improve retry behavior for large LFS uploads and add deployment scripting.

## 1.0.1 - 2025-11-27

- Update package metadata and setup behavior.

## 1.0.0 - 2025-11-27

- Establish token login, current-user lookup, and the initial CLI/SDK release.
- Historical packaging limitation: dependency metadata is empty and the
  standalone `atomgit_hub` import is broken. This version is archived as source
  history and should not be installed as a wheel.

Version `1.0.4` does not exist in repository history.
