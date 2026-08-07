# Independent Review Specification

## Purpose

After a substantial or high-risk implementation, review the change as if it
were authored by someone else. The review phase reports findings first and does
not silently edit code. Fixes require returning to implementation mode.

Review is mandatory before human acceptance for any change that affects remote
operations, credentials, Git configuration, public CLI/SDK behavior, dependency
calls, packaging, installation, or release. It is recommended for all other
non-trivial changes.

## Required Review Inputs

- Active task and acceptance criteria
- Complete diff against the task base
- Affected source and tests
- Relevant human documentation
- Locked dependency versions and real callable signatures
- Test output, including skipped tests

## Review Checklist

### Correctness

- Do CLI arguments reach the correct HF call with the correct semantics?
- Are file, directory, model, dataset, revision, and repository path cases kept
  distinct?
- Are failures converted to accurate exit codes or SDK exceptions?
- Are temporary paths still alive at the moment they are used?

### Compatibility

- Does the change work with `huggingface-hub==1.1.7`, `datasets==4.4.1`, and
  Python 3.9+?
- Are existing CLI commands, option names, imports, and public SDK signatures
  preserved unless the task authorizes a break?
- Do multi-level repository IDs behave consistently across operations?

### Security And User State

- Can tokens enter output, tracebacks, fixtures, or commits?
- Are credential-file permissions and Git helper changes safe and reversible?
- Could the change write to an unintended repository or path?
- Are global environment, timeout, and progress states restored?

### Tests

- Would the regression test fail on the previous defect?
- Are mocks strict enough to reject invalid dependency arguments?
- Are assertions proving observable behavior rather than only call count?
- Is a live test being implied by an offline mock?

### Maintainability And Documentation

- Does the change introduce CLI/SDK drift or needless duplication?
- Are comments and abstractions justified by a real constraint?
- Do README and docs describe verified current behavior and known limitations?
- Are unrelated edits or generated files included?

## Severity

- `P0 Critical`: credential exposure, destructive cross-repository action, or
  release compromise; blocks all use and delivery.
- `P1 Major`: core command failure, data corruption, or advertised capability
  broken; blocks acceptance and merge.
- `P2 Moderate`: important edge case, compatibility, maintainability, or
  testing gap; normally fix before acceptance, otherwise requires explicit
  human disposition.
- `P3 Minor`: low-risk clarity or polish issue; may be deferred explicitly.

## Review Output

1. Findings ordered by severity with file and line references.
2. Open questions and assumptions.
3. Tests or evidence missing.
4. Brief change overview only after findings.
5. Exactly one verdict: `APPROVED` or `REQUEST CHANGES`.

If there are no findings, say so explicitly and identify residual testing or
live-service risks.

Use `REQUEST CHANGES` whenever any P0 or P1 is open, required evidence is
missing, the implementation exceeds the active Issue, or mandatory tests did
not run without an accepted blocker. `APPROVED` does not authorize commit,
push, merge, Issue closure, or release.

## Long-Term Maintenance Audit

After the Issue-level verdict, a Tech Lead may perform a separate maintenance
audit for three-year risks. Findings outside the active acceptance criteria are
candidate follow-up Issues. Do not use that audit to expand the current diff.

Focus on:

- future HF Hub and datasets upgrades;
- duplicated CLI and SDK behavior;
- token format, storage, and migration;
- Python-version support cost;
- AtomGit and HF protocol semantic differences;
- installation provenance and rollback;
- release reproducibility and regression detection.
