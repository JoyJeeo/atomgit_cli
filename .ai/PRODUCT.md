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
- Default large-folder resumable directory uploads, repository prefixes, and
  worker selection, with an explicit ordinary-upload opt-out
- Repository download to a default or explicit directory
- Single-file CLI download
- Opt-in checksum verification for existing and newly downloaded CLI files
- Opt-in persistent resume for interrupted CLI downloads
- Opt-in manifest-scoped pruning for remotely removed repository files
- Authenticated repository list, verified visibility changes, and confirmed
  repository deletion with absence verification
- Explicit private creation and verified public creation
- Explicit branch creation and CLI upload to existing non-main branches
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
- Verified remotely: model and dataset resumable interruption/recovery with
  399,300,506-byte checksum readback, dataset creation and transfer through the
  AtomGit-compatible model route, credential permissions, `load_dataset`, and
  interrupted-download recovery.
- Non-default revision behavior is explicitly rejected because AtomGit does
  not expose the requested branch. Multi-level ID mapping is shared across
  operations; live create/upload returned 401 without false success when the
  test account lacked the mapped physical namespaces.
- The previously known SDK upload lifetime, parameter-forwarding, and timeout
  state defects are covered by offline regressions on the yuto development
  line.

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
- Repository pruning is explicit and may delete only regular files previously
  written and recorded by successful whole-repository CLI downloads; it must
  not scan or adopt unrelated local content.
- Remote repository deletion is CLI-only, requires an exact repeated repository
  ID, and may report success only after a post-delete detail request proves the
  target is no longer accessible.
- SDK failures expose stable `AtomGitError` subclasses while remaining
  compatible with callers that catch `Exception` or validation `ValueError`.

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
