# AtomGit CLI Product Specification

## Product

- Distribution name: `atomgit`
- CLI command: `atomgit`
- Python imports: `atomgit` and compatibility module `atomgit_hub`
- Development mainline: `yuto`
- Current package version: `1.0.5+yuto.1`

## Users

- Model and dataset developers using AtomGit from a terminal
- CI jobs transferring repository artifacts
- Python applications using AtomGit through an HF-like SDK
- Git users who want token reuse for AtomGit HTTPS operations

## Current Interface Surface

The items below are exposed by the current code. Exposure is not proof that
every remote path is verified; known status follows the interface list.

### CLI

- Login, logout, and current-user lookup
- Git credential-helper setup and cleanup
- Model or dataset repository creation
- Single-file and directory upload
- Upload target path, repository type, revision, ignore patterns, timeout, and
  progress-bar control
- Large-folder resumable mode and worker selection
- Repository download to a default or explicit directory
- Configuration-state display

### Python SDK

- Snapshot and single-file download
- Direct download URL construction
- Folder upload
- Repository creation
- Optional dataset loading

## Verification Status

- Verified by the available remote report: login state, model directory upload
  with download comparison, single-file upload with comparison, and a
  single-file repository subdirectory.
- Implemented and covered mainly by offline mocks: progress control, ignore
  parsing, repository type, revision forwarding, and upload error categories.
- Verified remotely: resumable upload authentication and interruption recovery,
  dataset transfer through the AtomGit-compatible model route, credential
  permissions, `load_dataset`, and interrupted-download recovery.
- Not yet established by valid remote tests: revision branch behavior and
  multi-level repository ID consistency.
- Known SDK defects: non-root upload temporary-directory lifetime, ignored
  upload parameters, and leaked timeout state.

## Product Contracts

- CLI and SDK share credentials from `~/.atomgit/config.json`.
- Public downloads should work without login; private operations use explicit
  or stored credentials.
- The HF API endpoint is `https://hub.atomgit.com`.
- Login identity is verified through `https://atomgit.com/api/v5/user`.
- Model and dataset repository types must remain distinguishable.
- User-facing failures should identify authentication, permission, repository,
  revision, request, timeout, or network causes when evidence allows it.
- Existing command names and Python imports are compatibility surfaces.

## Boundaries

This project is not:

- a replacement implementation of the Hugging Face transfer protocol;
- a general Git client;
- a model-training or dataset-processing framework;
- an automatic production-repository test harness;
- authorized to manage credentials outside the explicit AtomGit integration.

## Current Quality Priorities

- Make advertised upload modes work with the locked HF Hub version.
- Remove behavior drift between the CLI API and public Python SDK.
- Replace permissive mocks with realistic contract tests.
- Provide a distinguishable and verifiable installation path for `yuto`.
- Improve credential-file and global-state safety without breaking users.
