# Current Issue Contract

# Issue V5-AMBIGUOUS-WRITE-VERIFICATION

Status: `completed`

## Identity

- Local Issue: `V5-AMBIGUOUS-WRITE-VERIFICATION`
- Title: `Verify V5 repository writes after ambiguous failures`
- Type: `bug`, `cli`, `reliability`
- Priority: `P2`
- Branch: `codex/fix-v5-ambiguous-writes` (local only)
- Base: `yuto`
- Previous Issue: `PYTHON-VERSION-CONTRACT`, delivered by `ad41df4`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

Repository visibility and branch creation send a V5 PATCH or POST and then GET
the target only when the write call returns normally. A timeout, connection
loss, or 5xx can occur after AtomGit applied the change, but the CLI catches the
write exception and reports failure without attempting its existing read-back.

For ambiguous transport/server failures, the final authenticated GET is the
best available evidence and must decide success. A matching state may recover
success; a mismatch or unverifiable GET must return nonzero with credential-safe
unknown-state guidance. Client 4xx errors remain definitive and must not be
converted into success by a pre-existing resource.

## Scope And Acceptance

- Apply the policy to existing CLI visibility mutation and branch creation.
- After timeout, network, or 5xx write failure, perform the same bounded GET
  verification used by the normal success path.
- Recover success only when GET proves the exact currently verified target
  state; otherwise report a sanitized unknown state and return false.
- Treat every HTTP 4xx write result as definitive failure and do not issue a
  recovery GET.
- Preserve endpoints, request bodies, token headers, timeouts, normal success,
  mismatch behavior, CLI arguments, and exit codes.
- Add focused regressions for recovered success, mismatch/GET failure, 4xx, and
  credential redaction on both operations.
- Do not change branch-source verification semantics in this Issue; that is a
  separately audited defect and the next selected repair.
- Do not add commands, flags, retries, or unrelated functionality.

## Compatibility And Risks

- Visibility writes are idempotent; matching read-back is sufficient recovery.
- Branch verification currently proves only the target branch name. Source
  commit verification remains an explicit residual defect outside this Issue.
- No live write is authorized or required; strict offline request sequencing
  must cover all recovery paths.

## Permissions

- The user authorized issue-by-issue fixes for confirmed CLI defects and
  excluded new functionality.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- No live visibility mutation, branch creation, upload, deletion, or other
  remote write is authorized or required.

## Required Evidence And Closure

- [x] Previous missing read-back behavior is reproduced by failing regressions.
- [x] Ambiguous visibility and branch writes recover only from matching GET.
- [x] Mismatch and unverifiable GET return credential-safe unknown state.
- [x] HTTP 4xx writes remain definitive and skip recovery reads.
- [x] Normal request bodies, paths, timeouts, CLI behavior, and locked contracts
      remain compatible.
- [x] Focused and complete offline tests, compileall, pip, and diff checks pass.
- [x] Documentation, credential scan, scope audit, and independent review pass.
- [x] Human acceptance is covered by the standing ordered-fix authorization.
- [x] The task is committed, merged into `yuto`, and only `yuto` is pushed.

## Verification Evidence

- Regression before implementation: visibility tests passed `25/28` and branch
  tests passed `11/14`; both operations returned immediately after an ambiguous
  write exception instead of performing the existing GET verification.
- Implementation: V5 visibility PATCH and branch POST classify HTTP 4xx as a
  definitive rejection. Timeout, transport, response-decoding, and 5xx failures
  continue to a bounded authenticated GET and recover success only when the
  currently supported target state matches.
- Failure semantics: mismatch and failed GET paths return false with sanitized
  unknown-state guidance; regression output contains neither transport details
  nor test credentials. HTTP 4xx regressions prove no recovery GET is sent.
- Focused results: visibility `30/30`, branch creation `16/16`, repository
  creation visibility `3/3`, creation contract `42/42`, and repository deletion
  `48/48` passed offline.
- Complete offline suite: `pytest -q` exited `0` with all `55` collected tests;
  `python -m compileall -q .`, `python -m pip check`, and `git diff --check`
  passed in the `atomgit_cli` environment.
- Security and scope: no live request, remote write, dependency change, command,
  flag, retry, credential, generated artifact, or unrelated feature is present.
- Independent review: `APPROVED` with no P0-P3 findings. Residual branch-source
  verification is explicitly deferred to its separately audited Issue.
- Delivery implementation commit: `591afb4` (`fix(repo): verify ambiguous V5
  writes`). The closure commit is merged locally through the standing delivery
  workflow; the task branch remains local-only and only `yuto` is pushed.
