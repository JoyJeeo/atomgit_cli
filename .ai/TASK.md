# Current Issue Contract

Status: inactive (local scope accepted; Windows follow-up deferred)
ID: LOCAL-RELIABILITY-MAINTENANCE-20261106
Phase: local scope accepted for commit and push; Windows acceptance deferred

## Objective and authorization

The maintainer approved the four-stage repair plan and requested development
on 2026-11-06. The same dirty main worktree at
4260d70f4948459746b374b82e34075ab7c1191b is retained, including every prior
upload repair and production checkpoint. Implementation made no branch, commit,
push, release, credential change or remote write. The maintainer subsequently
requested a local commit and then explicitly requested pushing the code after
completion. Delivery covers the verified accumulated transfer changes and their
history, from this existing main worktree to github/main only. No release,
credential mutation or live AtomGit write is authorized.
The maintainer explicitly answered that no Windows test environment is
available and Windows acceptance should remain pending.

The previous handoff, including its then-uncommitted work and acceptance status,
is preserved byte-for-byte in
[the historical record](archive/TASK-20261106-before-reliability.md).
Archive SHA-256: 50716e18bf3904dc04bcb1a3fa483fdcaec1d008765a22355ccb61e6d3abeb8c.
Archived statuses and permissions are historical, not current instructions.
There is no new active development work; do not start another Issue automatically.

## Affected Capability IDs

DOWNLOAD-FILE, DOWNLOAD-INTEGRITY, DOWNLOAD-PRUNE, PORTABILITY,
UPLOAD-RESUMABLE, UPLOAD-OBSERVABILITY, FLOOR-REGISTRY.

## Protected Existing Invariants

Public CLI/SDK parameters, compatibility imports and patch seams; cache
identities and partial bytes; atomic replacement, checksum, path and credential
isolation; type ambiguity/default revision handling and bounded retries;
upload fairness, independent commits, recovery state and process isolation;
huggingface-hub==1.1.7 and datasets==4.4.1 remain unchanged.

## New Or Changed Invariants

- DLINT-004: persistent OS resume locks exclude competing writers and release
  on process death. Windows PID queries never terminate the queried process.
- PORT-010: Windows CLI pipes use UTF-8; offline subprocesses isolate native
  home and inherited TLS settings; monitor persistence closes descriptors even
  when permission setup fails or fchmod is unavailable.
- DLFILE-007: explicit-type single-file metadata success avoids enumeration,
  reuses metadata for checksum/resume and preserves unsupported/404 fallback;
  authentication and transient failures never trigger enumeration fallback.
- DLFILE-006 now names metadata plus fallback listing as revision consumers.
- Persistent lock files replace deletion. Stop old download processes before
  upgrade or rollback; never mix PID and OS lock versions on the same cache.
  Existing partial downloads need not be deleted.

## Implementation

1. Download resume and manifests share the existing POSIX/Windows lock backend.
   File identity/type checks fail closed, and no live lock file is unlinked.
   Legacy PID helper remains callable using non-destructive Windows handles.
2. Fixed Windows-related cp1252 CLI output, offline HOME/USERPROFILE isolation,
   host TLS contamination and the monitor temporary-descriptor leak. Native
   Windows ACL assertions, POSIX shell fixtures and file-sharing behavior still
   require a Windows runner and may need further changes; they are not accepted.
3. Explicit model/dataset single-file downloads probe metadata directly.
   Missing/unsupported metadata retains listing fallback; unspecified type
   retains automatic discovery. Canonical integrity patch seams remain intact.
4. Extracted target-validation retries and atomic RetryState failure recording;
   existing upload scheduling, state format and logs are preserved. Historical
   task text is archived without alteration and README routes current context.

## Verification evidence

- Pre-change audit: 94/94 offline cases in 102.24s; stale-lock overlap reproduced.
- Lock phase: regression red first, focused real-process/fake-Windows tests
  pass; complete baseline 94/94 in 87.72s.
- Portability phase: regressions first demonstrated fchmod absence, descriptor
  leakage, environment isolation and cp1252 output failures; after fixes, local
  complete baseline 94/94 in 89.06s.
- Download phase: new CLI/native metadata regressions failed before the change;
  fallback, auth/rate-limit, revision, existing-file, resume and metadata-reuse
  checks pass; complete baseline 94/94 in 89.76s.
- Upload extraction: five focused scripts passed in 26.22s, covering batching,
  pending commits, recovery, cross-process monitoring and structure.
- Final complete offline baseline: 94/94 in 86.43s on macOS/Python 3.10.20,
  log /tmp/atomgit-reliability-final-baseline.log. compileall, pip check,
  git diff --check and changed-production Ruff pass. Packaging baseline verifies
  Black/isort clean files and exact legacy debt: Black 69 files/382 hunks,
  isort 65/71, Ruff 15/44. Locked metadata/http_get signatures bind correctly.
- Ledger: 28 capabilities, 163 invariants, 94 offline scripts. No test removed
  or skipped to obtain passing results. No high-confidence secrets found in
  task-added text; no tracked generated bytecode or removed pre-existing files.
- Offline preparation benchmark: 100/10,000/100,000 names required one complete
  listing before, zero listings/names after; checksum metadata remains one
  query. /tmp/atomgit-download-preparation-benchmark.json. CPU-only fake-transport
  timings do not establish live network speed or throughput.

## Review and residual limits

Distinct review phase inspected the task-only diff against the pre-task
worktree, compatibility/locked signatures, OS lock lifetime and descriptor
ownership, metadata/error fallback, upload state ordering, documentation and
regression evidence. Local-scope verdict: APPROVED; no open local blocking
finding. This does not assert Windows or live-service acceptance and does not
authorize delivery operations.

No new Windows/Linux execution or live AtomGit transfer was performed. Historical
Windows CI 40074257545 had 37 passed / 57 failed; it is not current evidence.
Windows acceptance and any remaining ACL/shell/OS-specific fixes are deferred
by the maintainer because there is no available Windows runner. Mixed old/new
lock processes are unsupported. The maintainer accepted the local result by
requesting commit and push while retaining the Windows disposition. The commit
containing this record is the accepted local delivery; verify github/main
matches local main after its authorized push. Do not start the deferred Windows
work, run production transfers or publish a release automatically.

## Authorized delivery verification

The github remote was verified as git@github.com:JoyJeeo/atomgit_cli.git;
fetch found no divergence from the main base 4260d70. The working tree contains
the previously reviewed upload/default-revision changes plus the current
reliability repairs; no unrelated untracked files are included. Archive content
still matches its recorded SHA-256. Compileall, pip check and diff checks pass.
Fresh delivery baseline: python tests/run_cli_baseline.py passed 94/94 in
87.16s, log /tmp/atomgit-delivery-20261106-baseline.log. The full staged diff
passed diff/artifact/credential review; no open local blocking finding remains.
Windows acceptance remains explicitly deferred.
