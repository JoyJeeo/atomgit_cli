# AtomGit CLI Testing Specification

## Goals

Tests must establish observable behavior, dependency compatibility, and safe
failure handling. High assertion counts do not compensate for permissive mocks
or missing end-to-end evidence.

## Environment

All tests run after activating the `atomgit_cli` conda environment. The local
package must be importable from that environment, normally through an editable
development install.

Never read a real token from `~/.atomgit/config.json` in offline tests. Patch
configuration access with clearly fake values.

## Test Layers

### Unit

- Path and repository validation
- Ignore-pattern parsing
- Repository ID normalization
- Error classification and exit-code decisions
- Configuration serialization using an isolated home directory

### CLI Integration

- Use Click `CliRunner`.
- Replace remote operations with strict fakes or autospecced mocks.
- Verify exit code, output, and exact downstream arguments.
- Cover file and directory paths separately.

### Dependency Contract

- Inspect or bind against the actual installed `huggingface_hub==1.1.7`
  signatures.
- Test `HfApi` constructor authentication separately from method arguments.
- Prevent `**kwargs` fakes from accepting arguments the real dependency rejects.
- Verify deprecated SDK arguments intentionally rather than relying on warnings.

### Packaging Smoke

- Build a wheel in isolation.
- Install it into an isolated environment.
- Verify `atomgit --version`, `atomgit --help`, `python -m atomgit --help`,
  `python -m atomgit.cli --help`, `import atomgit`, and `import atomgit_hub`.

### Live AtomGit Tests

Live tests are opt-in and require explicit user authorization. They must use:

- a dedicated test account and token supplied through an environment variable;
- uniquely named disposable repositories, or exact dedicated repositories named
  by a scoped standing authorization;
- no production or personal repositories;
- explicit cleanup approval;
- recorded command exit codes and remote verification.

Maintainer standing authorization recorded on 2026-08-06 permits live tests
without repeated approval only against
`weixin_52273949/test_model` and
`weixin_52273949/test_datasets`, using the already supplied test login. It does
not authorize any other repository, deletion, release, or publication, and the
token must never be printed or copied into test output.

The maintainer explicitly added
`weixin_52273949/atomgit-cli-dataset-20260804-003221` on 2026-08-25 as the
positive dataset transfer target. The historical `test_datasets` repository is
read-only diagnostic evidence because it rejects writes with `BadRequestError`;
it is not a positive upload fixture.

Live coverage should separately verify model and dataset creation, privacy,
upload/download checksums, repository paths, ignore rules, revisions, resumable
interruption/restart, anonymous public download, and authenticated private
download when those operations are separately authorized. The pending R7 plan
below is narrower; its explicit exclusions control that run.

## Pending Comprehensive Acceptance Plan

This plan is recorded but must not start until the maintainer explicitly asks
to begin the comprehensive test run. That start instruction authorizes only the
operations listed here and does not broaden the standing remote permissions.

### Scope And Safety

- Activate the `atomgit_cli` conda environment and record branch, HEAD,
  worktree status, dependency versions, and the exact diff before testing.
- Use isolated HOME, Git configuration, cache, download, and temporary
  directories. Supply the dedicated test token only through an environment
  variable; never print it or read `~/.atomgit/config.json`.
- Permit remote access only when the resolved repository ID is exactly
  `weixin_52273949/test_model`, `weixin_52273949/test_datasets`, or
  `weixin_52273949/atomgit-cli-dataset-20260804-003221`. Abort before any
  request when a URL, SSH target, or normalized ID resolves elsewhere. Use the
  last repository for positive dataset writes and keep `test_datasets`
  read-only.
- Store remote fixtures under unique `e2e/<run-id>/{cli,sdk,legacy}/` prefixes.
  Do not delete or overwrite content outside that run prefix.
- Read each repository tree at most once per run and cache it. Verify known
  uploaded targets by direct resolve readback rather than refreshing the full
  tree. Run CLI, native SDK, and legacy paths serially; 429 and consecutive
  timeouts stop that repository's live rows.
- Record every command or SDK operation, exit/result status, remote commit or
  revision where available, and independent readback SHA-256 evidence. Success
  output alone is not acceptance evidence.

### Ordered Gates

1. Run source-layout, structure, architecture parity, and development-floor
   checks. Require exactly seven first-level responsibility directories, one
   owner per production module, registered dependency edges, no cycles or
   placeholders, and complete CLI/native-SDK parity routes.
2. Run `python tests/run_cli_baseline.py`, `python -m compileall -q .`,
   `python -m pip check`, and `git diff 23c6d7d --check`. Require all 92
   isolated cases, 27 capabilities, and 116 invariants to pass.
3. Run isolated source/editable/wheel/sdist packaging smoke. Verify console and
   Python module entry points, historical imports, artifact contents, and that
   installed imports never fall back to the working tree.
4. Exercise each parity-required capability through strict offline CLI and
   native-SDK paths. Compare usecase/adapter selection, arguments, token and
   revision policy, results, errors, state restoration, and cleanup. Preserve
   the explicit CLI-only classification for presentation, lifecycle, shell
   hooks, and configuration display.
5. Perform read-only live preflight against both authorized repositories.
   Record type, visibility, current revision/commit, file inventory, CLI and
   SDK identity, and repository listing without changing remote state.
6. Run the controlled live transfer matrix below independently for the model
   and dataset repositories. A failure in one row must not suppress evidence
   collection for unrelated rows when continuing is safe.
7. Rerun the complete offline baseline and diff/artifact/security checks after
   live testing. Confirm that no token, signed URL, generated package, cache,
   bytecode, or remote fixture entered the repository worktree.

### Controlled Live Transfer Matrix

For both authorized repositories, verify CLI and native SDK single-file upload,
ordinary folder upload, `path_in_repo`, ignore rules, resumable upload with an
intentional interruption/restart, single-file download, whole-repository
download, checksum validation, resumable download, and manifest-scoped local
prune. Validate every transferred payload by remote readback and SHA-256.

Also verify these cross-surface and compatibility paths:

- CLI upload followed by native SDK download, and native SDK upload followed
  by CLI download, with identical bytes and metadata.
- Canonical LFS pointer bytes, OID, size, and final LF for applicable uploaded
  content, without changing repository-level `.gitattributes`.
- The historical `atomgit_hub` download, folder-upload, direct-URL, and dataset
  loading surfaces against their applicable authorized repository.
- Anonymous download for an authorized repository that is already public, and
  authenticated download for one that is already private. Do not change
  visibility to manufacture either condition.

### Explicit Exclusions

The pending run does not create or delete repositories, verify post-deletion
absence, change repository visibility, create or delete remote branches, run
`--auto-configure-lfs`, change repository-level `.gitattributes`, publish or
release artifacts, uninstall the real environment, clean remote fixtures, or
touch any repository outside the two-item allowlist. These exclusions are
reported as `not run by scope`, not as failures and not as passing remote
evidence.

### Acceptance Report

Report results in three groups: passed, failed, and not run by scope. For each
live row include the interface, repository, operation, exit code or structured
SDK result, revision/commit, and readback checksum. Offline mocks may support a
capability but must never be reported as live evidence. Acceptance requires all
in-scope offline, packaging, parity, and controlled live rows to pass; any
remaining limitation or test not run must be explicit.

## Current Repository Tests

The existing `tests/test_*.py` files retain their self-executing custom
assertions for compatibility. `tests/pytest_offline_scripts.py` collects each
script as a separate pytest case and runs it in an isolated subprocess with a
temporary HOME and Git configuration. Report the collected pytest case count,
not internal custom assertion totals, as the pytest test count.

`tests/cli_baseline_contract.py` is the authoritative monotonic inventory. It
locks the exact public CLI schema, leaf dispatch coverage, and an explicit
capability grouping for every offline script. `tests/test_cli_baseline_guard.py`
proves that unregistered commands, parameters, tests, stale registrations,
missing dispatches, and inert non-executing scripts fail the gate.

## Development Floor

`tests/development_floor_contract.py` is the executable ledger for stable
capability IDs, observable invariant IDs, risk and evidence categories,
offline regressions, documentation, and controlled-remote evidence status.
`tests/test_development_floor.py` fails closed when a capability, invariant,
test, document, or required workflow marker is missing, duplicate, stale, or
incomplete.

The current monotonic ledger has 28 capabilities, 127 invariants, and 93
isolated offline pytest cases. Every offline test maps to at least one
capability; every invariant maps to executable evidence assigned to that
capability. New behavior updates the ledger in the same Issue.

Structural work additionally uses `tests/structure_contract.py` and
`tests/test_structure_guard.py` for ownership, dependency direction, legacy
debt, public surfaces, and artifact expectations. Public import and packaging
evidence covers source, explicit PEP 660 editable installation, wheel, and
sdist in isolated temporary locations. Import-order and completion probes run
in clean subprocesses, and production dependency keyword sets are extracted
from call sites before binding against the locked real signatures.

Packaging work uses `pyproject.toml` as the explicit build-backend, `src`
package-layout, Python-target, and pytest-policy declaration while `setup.py`
remains the transition-period project-metadata authority. The pinned Black,
isort, and Ruff versions produce an exact normalized legacy-debt fingerprint;
new Issue-owned files must be clean and debt removal must tighten the contract
in the same change. The wheel smoke uses the default declared PEP 517/660
editable path rather than passing a legacy opt-in flag.

Every Issue records `Affected Capability IDs`, `Protected Existing Invariants`,
`New Or Changed Invariants`, focused evidence, full-baseline evidence, and
residual risks before delivery. See `DEVELOPMENT_FLOOR.md` for compatibility
migration and blocking rules.

## Required Checks

For a focused change, run the affected test scripts first. Before completion,
delivery, merge, push, release, or further feature expansion, run the mandatory
comprehensive baseline plus:

```bash
python tests/run_cli_baseline.py
python -m compileall -q .
git diff --check
```

The baseline runner invokes the complete isolated pytest matrix. It applies to
every development Issue, including testing, documentation, refactoring,
compatibility, distribution, and release work. A new feature
must add or update a focused self-executing regression, register every new test
script, update the exact CLI schema and leaf dispatch inventory when public
surface changes, and update matching documentation. A baseline failure must be
fixed in implementation code and rerun; do not weaken an established contract
unless the active Issue records explicit maintainer authorization for that
compatibility change.

A failed or unrun complete baseline leaves the Issue active and blocks all
delivery. It cannot be waived as not applicable. Tests and ledger entries may
not be weakened to fit an unintended regression.

If a required check cannot run, state the exact blocker and residual risk.

## Regression Rule

Every defect fix must include a test that reproduces the defect at the same
boundary where it occurred. For external API mismatches, the regression test
must enforce the real dependency signature, not only the expected dictionary
of mocked arguments.

## Issue Evidence Record

Test success must be recorded in `TASK.md` with the command, environment,
result, and whether it is offline or live. A summarized statement such as
"tests pass" is insufficient when multiple test layers are required.

For live validation, record command exit codes plus remote state or content
evidence. CLI success text alone is not evidence of a successful upload,
revision, repository creation, privacy setting, or resumable recovery.
