# AtomGit CLI Issue Roadmap

This roadmap is a candidate backlog, not authorization to implement or create
remote GitHub Issues. The human maintainer selects one Issue at a time and
activates it in `TASK.md`. Issue numbers below are planning identifiers until
the corresponding remote Issues are explicitly created.

## Ordering Principles

1. Fix confirmed user-facing defects before refactoring architecture.
2. Establish strict dependency and regression tests before relying on mocks.
3. Separate offline correctness from AtomGit remote verification.
4. Stabilize behavior before building an independent `yuto` distribution.
5. Treat credentials, global Git configuration, and releases as high risk.

## Current Development Status

This summary describes `yuto` after local implementation, offline review, and
the explicitly authorized 2026-08-04 AtomGit acceptance run. It does not grant
permission by itself for future remote writes, release, or Issue transitions.
Separate maintainer authorization recorded on 2026-08-06 permits tests only on
`weixin_52273949/test_model` and `weixin_52273949/test_datasets` without repeated
approval; it grants no access to other repositories, deletion, or publication.

- Completed with local regression/contract evidence: #001-#014, #018, and
  #020-#026. The development line includes strict HF contracts, SDK parity,
  shared repo-ID/runtime policy, isolated pytest, wheel smoke, credential
  safety, stable SDK exceptions, release artifacts, and a checksummed
  installer.
- Controlled remote evidence now covers #015-#019: model and private-dataset
  lifecycle, path placement, ignore absence, model and dataset resumable
  interruption/recovery with 399,300,506-byte SHA-256 readback, anonymous
  public success, anonymous private failure, authenticated private success,
  and verified cleanup.
- Multi-level create/upload accurately normalized the logical IDs, returned
  nonzero on the service's 401 response, and left no repository behind. The
  supplied account lacks the normalized `weixin_52273949-test_model` and
  `weixin_52273949-test_datasets` namespaces, so a successful multi-level write
  remains conditional on membership in the mapped physical namespace rather
  than an unverified client capability.
- Live evidence confirmed that AtomGit's HF `private=False` create request can
  report success while producing a private repository. CLI public creation now
  creates privately, applies the V5 visibility update, and GET-verifies public
  state before success; the Python SDK remains intentionally private-only.
- CLI non-main revision uses explicit V5 branch creation and verification before
  HF upload forwarding; SDK upload remains intentionally main-only.
- The authorized 2026-08-05 to 2026-08-06 CLI hardening tranche is complete:
  redirect credential isolation, download path/framing/type/skip/error safety,
  stdin login, lazy atomic configuration, strict repo IDs and upload conflicts,
  create preflight semantics, partial Git status, cached Git identity, and
  collision-safe transfer temporaries all have focused regressions and
  independent review. The final complete offline matrix passed 43/43 pytest
  cases; no additional reproducible CLI implementation defect was found in the
  closing consistency audit.

## Milestone A: v1.0.5-yuto Stability

### Issue #001 - Fix resumable upload authentication

- Type: `bug`, `compatibility`
- Priority: `P1`
- Evidence: HF 1.1.7 rejects `token` passed to
  `HfApi.upload_large_folder()`.
- Dependency: none.
- Minimum outcome: authenticate through the `HfApi` instance and add a strict
  signature regression test.

### Issue #002 - Add locked HF API contract tests

- Type: `testing`, `compatibility`
- Priority: `P1`
- Dependency: none; should precede Issue #001 when practical, but remains a
  separate active Issue and review unit.
- Minimum outcome: real signatures prevent permissive fakes from accepting
  invalid arguments for upload, download, create, and large-folder APIs.

### Issue #003 - Investigate and define revision behavior

- Type: `bug`, `compatibility`
- Priority: `P1`
- Evidence: CLI reported success, but AtomGit Git remote exposed no `dev` branch.
- Dependency: authorized live test design.
- Minimum outcome: document supported semantics and either implement correct
  behavior or reject unsupported revision usage accurately.

### Issue #004 - Fix SDK subdirectory upload lifetime

- Type: `bug`, `sdk`
- Priority: `P1`
- Evidence: the temporary directory exits before the HF upload call.
- Dependency: strict SDK upload test.
- Minimum outcome: upload path exists for the complete call and is cleaned
  afterward.

### Issue #005 - Forward all supported SDK upload parameters

- Type: `bug`, `sdk`
- Priority: `P1`
- Evidence: `repo_type`, `revision`, `commit_description`, and
  `ignore_patterns` are accepted but ignored.
- Dependency: Issue #002 contract approach.
- Minimum outcome: every public parameter is forwarded or explicitly removed
  through an authorized compatibility change.

### Issue #006 - Restore Hugging Face process-global state

- Type: `bug`, `compatibility`
- Priority: `P1`
- Evidence: upload timeout remains changed after the operation.
- Dependency: none.
- Minimum outcome: timeout and progress state are restored on success and all
  failures.

### Issue #007 - Unify multi-level repository ID behavior

- Type: `bug`, `cli`, `sdk`
- Priority: `P2`
- Evidence: validation accepts multi-level IDs, but operations normalize them
  inconsistently.
- Dependency: define intended AtomGit mapping and obtain remote evidence if
  needed.
- Minimum outcome: create, upload, download, URL generation, and dataset loading
  share an explicit contract.

### Issue #008 - Replace shared `.tmp_upload` fallback

- Type: `bug`, `security`
- Priority: `P2`
- Evidence: single-file fallback uses a shared working-directory path.
- Dependency: single-file fallback regression tests.
- Minimum outcome: unique temporary resources, correct lifetime, and cleanup on
  error.

## Milestone B: Reliable Offline Verification

### Issue #009 - Migrate upload scripts to pytest

- Type: `testing`
- Priority: `P1`
- Dependency: preserve current assertions and exit behavior.
- Minimum outcome: standard collection, fixtures, isolated state, and a single
  reliable offline test command.

### Issue #010 - Add login and configuration tests

- Type: `testing`, `security`
- Priority: `P2`
- Dependency: isolated HOME and network fakes.
- Minimum outcome: token validation, persistence, logout, corrupt config, and
  file-permission behavior.

### Issue #011 - Add download tests

- Type: `testing`, `cli`, `sdk`
- Priority: `P2`
- Dependency: strict snapshot and file-download fakes.
- Minimum outcome: public/private token selection, default/explicit directory,
  force behavior, error exits, and CLI/SDK differences.

### Issue #012 - Add repository creation tests

- Type: `testing`, `cli`, `sdk`
- Priority: `P2`
- Dependency: strict create-repo contract.
- Minimum outcome: model/dataset, private/public, existing repository, invalid
  input, and error evidence.

### Issue #013 - Isolate Git credential-helper tests

- Type: `testing`, `security`
- Priority: `P1`
- Dependency: isolated HOME and Git config.
- Minimum outcome: setup, lookup, cleanup, malformed input, and preservation of
  unrelated user configuration without touching the real global config.

### Issue #014 - Add wheel installation smoke tests

- Type: `testing`, `distribution`
- Priority: `P1`
- Dependency: build tooling available in the conda environment.
- Minimum outcome: isolated wheel install verifies both CLI entry points and
  both Python imports.

## Milestone C: Controlled AtomGit Remote Acceptance

### Issue #015 - Verify model repository lifecycle

- Type: `testing`, `cli`
- Priority: `P1`
- Dependency: explicit live-write and cleanup authorization.
- Minimum outcome: unique model repository creation, upload, download, checksum,
  and recorded cleanup.

### Issue #016 - Verify private dataset lifecycle

- Type: `testing`, `cli`, `sdk`
- Priority: `P1`
- Dependency: Issue #015 harness and explicit authorization.
- Minimum outcome: valid private dataset repository, authenticated upload and
  download, privacy evidence, and checksums.

### Issue #017 - Verify path, ignore, and revision independently

- Type: `testing`, `compatibility`
- Priority: `P1`
- Dependency: Issue #003 decision and disposable repositories.
- Minimum outcome: each option has isolated remote evidence, so one failure does
  not invalidate the other capabilities.

### Issue #018 - Verify resumable interruption and recovery

- Type: `testing`, `compatibility`
- Priority: `P1`
- Dependency: Issues #001 and #002.
- Minimum outcome: interrupted first run, resumed second run, final checksum,
  and documented metadata behavior.

### Issue #019 - Verify public/private download matrix

- Type: `testing`, `security`
- Priority: `P1`
- Dependency: Issues #015 and #016.
- Minimum outcome: anonymous public success, anonymous private failure, and
  authenticated private success.

## Milestone D: yuto Distribution

### Issue #020 - Define yuto version and provenance policy

- Type: `distribution`
- Priority: `P1`
- Dependency: stability milestone accepted.
- Minimum outcome: unambiguous version, upstream relationship, upgrade and
  rollback policy.

### Issue #021 - Add checksummed GitHub Release artifacts

- Type: `distribution`, `release`
- Priority: `P1`
- Dependency: Issues #014 and #020, explicit release authorization.
- Minimum outcome: reproducible wheel/source artifacts, SHA256, release notes,
  and installation verification.

### Issue #022 - Add versioned `curl | bash` installer

- Type: `distribution`, `security`
- Priority: `P1`
- Dependency: Issue #021.
- Minimum outcome: fixed-version download, checksum verification, current conda
  environment detection, clear failure output, and no silent system install.

### Issue #023 - Complete license and release documentation

- Type: `documentation`, `release`
- Priority: `P1`
- Dependency: human confirmation of copyright and license.
- Minimum outcome: repository `LICENSE`, installation/uninstallation guidance,
  security notes, and support boundaries.

## Milestone E: Maintainability And Security

### Issue #024 - Centralize endpoint and normalization policy

- Type: `compatibility`, `sdk`
- Priority: `P2`
- Dependency: Issues #003 and #007 define behavior first.
- Minimum outcome: reduce CLI/SDK drift without mixing user-facing output into
  SDK code.

### Issue #025 - Define stable AtomGit exception contracts

- Type: `sdk`, `compatibility`
- Priority: `P2`
- Dependency: download, create, and upload tests.
- Minimum outcome: preserve causes and provide documented SDK exception types.

### Issue #026 - Harden credential storage and helper reversibility

- Type: `security`
- Priority: `P1`
- Dependency: Issues #010 and #013.
- Minimum outcome: restrictive credential permissions and no overwrite/removal
  of unrelated user Git configuration.

## Stability Release Gate

A `yuto` stability release is eligible only when:

- Issues #001-#014 required for the chosen release scope are accepted;
- model and dataset remote lifecycles have valid evidence;
- revision support is implemented and verified or clearly rejected;
- resumable recovery has real interruption/resume evidence;
- CLI and SDK critical contracts are tested;
- the complete offline suite and wheel smoke test pass;
- no open P0 Critical or P1 Major review finding exists;
- version origin is distinguishable from upstream;
- README does not advertise a known-broken capability as available;
- credential and Git helper risks are accepted or fixed;
- release artifacts and publication are explicitly authorized.
