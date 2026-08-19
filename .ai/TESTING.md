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
  `import atomgit`, and `import atomgit_hub`.

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

Live coverage should separately verify model and dataset creation, privacy,
upload/download checksums, repository paths, ignore rules, revisions, resumable
interruption/restart, anonymous public download, and authenticated private
download.

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

The current monotonic ledger has 26 capabilities, 105 invariants, and 88
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
