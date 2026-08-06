# Current Issue Contract

# Issue CLI-DOCUMENTATION-CONSISTENCY

Status: `completed`

## Identity

- Local Issue: `CLI-DOCUMENTATION-CONSISTENCY`
- Title: `Maintainer documentation describes retired CLI behavior`
- Type: `documentation`, `maintenance`
- Priority: `P2`
- Branch: `codex/final-cli-consistency-audit` (local only)
- Base: `yuto`
- Delivery mode: local acceptance, authorized commit, local merge into `yuto`,
  and push only `yuto`; task branch remains local-only.

## Previous Issue (Closed)

- `DOWNLOAD-STANDARD-PART-CLEANUP` was delivered by `b012a82` and merged by
  `41cc174`.

## User Impact And Evidence

The final CLI audit found no new reproducible implementation defect, but three
maintainer documents still describe behavior retired by completed Issues:
architecture says repository download uses `snapshot_download`, upload analysis
says invalid option combinations warn and continue, and testing guidance calls
the now-strict resumable contract fake permissive. These statements can cause
future changes and tests to target the wrong contract.

## Scope

In scope: align architecture, upload analysis, testing guidance, and roadmap
status with the verified current implementation and the maintainer's scoped
standing live-test authorization; run documentation/source consistency
searches, the complete offline suite, and live read/download acceptance against
only the two supplied test repositories.

Out of scope: new CLI/SDK behavior, any other remote repository, remote deletion,
dependency/version changes, release artifacts, and new roadmap feature work.

## Acceptance Criteria

- Download documentation describes list-files plus safe per-file resolve flow,
  default existing-file skip, explicit force replacement, and unique temporary
  cleanup.
- Upload option conflicts are documented as preflight errors with exit code 2.
- Testing guidance no longer reports the resolved permissive-fake risk and
  reflects the current complete suite.
- Roadmap status records the completed CLI hardening/audit tranche without
  creating or transitioning remote Issues.
- Authenticated live probes reach both authorized repositories; small-file
  download, default skip, force replacement, neighboring-file preservation, and
  whole-repository CLI skip behavior pass without remote mutation.
- Full offline tests, compileall, `git diff --check`, and consistency searches
  pass.

## Permissions And Acceptance

- Authorized: local documentation edits, tests, commits, local merge into
  `yuto`, and push only `yuto`; no task-branch push.
- Authorized live scope is limited to read/download tests against
  `weixin_52273949/test_model` and `weixin_52273949/test_datasets` using the
  already supplied login; no token value may be printed.
- Human acceptance: standing acceptance granted for the approved full plan.
- Documentation: architecture now describes list-files plus safe per-file
  resolve downloads, default skip/force semantics, retry behavior, and CLI/SDK
  differences. Upload analysis records all preflight option conflicts and API-
  only fallback behavior. Testing and roadmap documents record the strict
  dependency contracts, 43-case suite, completed hardening tranche, and exact
  standing live-test boundary.
- Consistency evidence: searches for the retired warning/ignore behavior,
  permissive resumable fake, snapshot-based CLI flow, anonymous-first CLI API
  file download, and per-run authorization wording returned no stale matches.
- Complete offline command: `python -m pytest -q` passed 43/43 pytest cases in
  45.00 seconds in the `atomgit_cli` environment with local-loopback permission.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Live authentication/repository evidence: `python -m atomgit whoami` exited 0
  as `weixin_52273949`; authenticated listings returned model 62 files and
  dataset 14 files from only the two authorized repositories.
- Live small-file evidence: model `ignore_test/config.json` and dataset
  `sub/中文样本.csv` both passed initial download, default local-content skip,
  forced remote-content replacement, neighboring `.part` preservation, and
  unique-temporary cleanup. Observed SHA-256 prefixes were `789192e81c76` and
  `19391604546c` respectively.
- Live CLI evidence: actual `atomgit download` invocations exited 0 and skipped
  62/62 model files and 14/14 dataset files pre-populated with sentinels; every
  sentinel remained unchanged, so no large transfer or remote mutation occurred.
- Dependency compatibility: no source or dependency changed; the locked HF and
  datasets signature contracts passed in the complete suite.
- Independent review: first review found contradictory fixed-repository and
  no-remote wording (`REQUEST CHANGES`). The authorization exception and Issue
  evidence were corrected; a fresh review found no open findings (`APPROVED`).
- DoD/security: live commands did not print the token, used temporary local
  directories, accessed no other repository, and performed no remote write,
  deletion, release, or publication. No residual code risk was introduced by
  this documentation-only Issue.
- Commit/merge/push: authorized and pending.
