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
- uniquely named disposable repositories;
- no production or personal repositories;
- explicit cleanup approval;
- recorded command exit codes and remote verification.

Live coverage should separately verify model and dataset creation, privacy,
upload/download checksums, repository paths, ignore rules, revisions, resumable
interruption/restart, anonymous public download, and authenticated private
download.

## Current Repository Tests

The existing `tests/test_upload_*.py` files are executable scripts with custom
assertions, not standard pytest tests. Until migration, run every script and
honor its exit code. Do not report `pytest` coverage for tests pytest did not
collect.

## Required Checks

For a focused change, run the affected test scripts first. Before completion,
run all available offline tests plus:

```bash
python -m compileall -q .
git diff --check
```

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
