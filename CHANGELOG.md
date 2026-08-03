# Changelog

This project uses Git tags for immutable source history. The `yuto` line uses a
distinct package version and tag so users can distinguish it from upstream
PyPI releases.

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
