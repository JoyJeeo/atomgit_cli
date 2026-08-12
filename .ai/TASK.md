# Current Issue Contract

Status: `completed`

## Handoff Snapshot

- Updated: `2026-08-12 19:51:00 +0800`
- Phase: `implementation completed, independently approved, committed on the local task branch, and merged locally into yuto; preparing the authorized yuto-only push`
- Base branch: `yuto`
- Task branch: `codex/recover-slow-lfs-flows`
- Base commit: `3fbe795437b8f18574ca2299e084c140b9edaa82`
- Task commit: `2f1ad01 fix(upload): recover slow LFS flows`
- Merge commit: `dbf6a74 merge: recover slow LFS flows`
- Current HEAD before this delivery record: `dbf6a74b6ff7a9b114d677942cb1ecaa77352216`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit/atomgit_cli`
- Worktree state: `dirty only for this delivery record on yuto`
- Changed paths: `.ai/TASK.md`
- Last completed action: `merged local-only task commit 2f1ad01 into yuto as dbf6a74 without pushing the task branch`
- Next exact action: `commit this delivery record, push only yuto, verify the remote branch, then add the final completion checkpoint`
- Blockers: `none`
- Tests run: `pre-implementation test_lfs_slow_flow_recovery.py failed at the absent policy entry point; final focused test passed 28/28; affected LFS preupload 89/89, resumable recovery 5/5, commit policy 51/51, canonical pointer 24/24, dataset route 11/11, auto-configure 41/41, upload progress 28/28, validation 15/15, resumable 49/49, CLI feature baseline 52/52, and baseline guard 14/14 passed; mandatory python tests/run_cli_baseline.py passed 69/69 in 50.36s, after the stable-window correction in 49.36s, and after review fixes in 50.32s; python -m compileall -q ., python -m pip check, and git diff --check passed`
- Required worktree: `/Users/yutaozhang/yuto/codes/atomgit/atomgit_cli`

## Active Issue

- ID: `LOCAL-RECOVER-SLOW-LFS-FLOWS`
- Title: `Recover pathological resumable LFS upload flows`
- Primary type: `bug`
- Priority: `P2`
- Observable objective: `during resumable directory uploads, detect a persistently degraded individual LFS PUT or multipart part using application-level payload progress and replace only that object's request when a bounded time-benefit policy predicts a material improvement`
- User impact: `a single non-failing LFS connection can retain one worker for hours at hundreds of KiB/s even while reconnecting the same object restores tens of MiB/s`

## Starting Evidence And Dependency Contract

- Controlled live diagnosis reproduced one 256 MiB object below 0.3 MiB/s with one worker; reconnecting the same object to the same host and IP completed near 20-30 MiB/s.
- Concurrent flows to the same destination diverged materially while CPU and disk remained unsaturated; Mihomo routed them `DIRECT`, rejecting a shared proxy-node bottleneck.
- The narrowest supported cause is a pathological individual TCP/HTTPS PUT flow; the exact upstream backend or transit trigger needs platform telemetry.
- Locked `huggingface-hub==1.1.7` uses `_commit_api._upload_lfs_files -> lfs_upload`; basic LFS is one `http_backoff` PUT from byte zero, multipart uploads parts iteratively and completes with collected ETags.
- HF 1.1.7 retries errors but has no sustained-low-throughput watchdog. Its large-folder worker catches preupload exceptions and requeues items, so AtomGit must bound recovery and fail closed at its existing isolated-child boundary.
- Locked `datasets==4.4.1` remains unchanged.

## Scope

In scope:

- Apply recovery only inside the existing isolated resumable upload child and restore every patched HF symbol on exit.
- Measure application-level payload reads without persisting source paths, OIDs, URLs, headers, tokens, or response bodies.
- Use deterministic 30-second windows built from 5-second samples, stable peer and self baselines, and the accepted time-benefit calculation.
- Replace only the slow object's current request; healthy objects continue unchanged.
- Basic PUT restarts the complete object. Multipart retains only server-confirmed ETag parts within the same verified action and retries the current unconfirmed part.
- Limit each object to three replacements with 2-8 second jitter, then 60 and 180 second cooldowns, fresh observation windows, improvement checks, total-deadline enforcement, and one probe during peer-wide slowdown.
- Preserve source identity, upload checksum, LFS action validation, verify semantics, resumable metadata, canonical pointer checks, timeout behavior, error redaction, model/dataset routing, and existing public CLI/SDK signatures.
- Add focused offline regressions, update authoritative upload documentation, and run the mandatory CLI baseline.

Out of scope:

- No dependency upgrade, new public CLI option, persisted multipart manifest, arbitrary byte-offset resume, parallel parts within one object, or changes to ordinary uploads.
- No remote repository creation, deletion, cleanup, Issue transition, PR, tag, release, publication, credential mutation, proxy mutation, or access to any `OpenLET/*` repository.
- No live writes are required for implementation acceptance; prior diagnostic evidence is the behavioral basis.
- Do not claim a specific AtomGit backend, object-storage node, or transit provider as the proven upstream root cause.

## Accepted Recovery Policy

- Sample payload bytes every 5 seconds and form effective-speed windows every 30 seconds; exclude time without locally available payload.
- A peer baseline requires at least two peers stable for three windows: median movement at most 20%, with two peers between 70% and 130% of the median.
- Mark an object slow after three consecutive windows at no more than 30% of the stable peer baseline and no more than 50% of its own preceding stable median.
- Without peers, compare three subsequent windows to the preceding three stable self windows; an object slow from its first window is not replaced for low throughput alone.
- Replace only when `continue_time >= 2 * replace_time`. Basic retransmit bytes are the whole object; multipart retransmit starts at the unconfirmed part.
- When all active peers slow together, allow at most one conservative probe replacement instead of a reconnect storm.
- Replacement waits are random 2-8 seconds, then at least 60 and 180 seconds. Each replacement needs three fresh windows before another low-speed decision.
- Stop after three replacements, failure to improve speed by at least 2x, insufficient estimated benefit, insufficient remaining deadline, or any non-retryable/session-integrity failure.
- Only the newest attempt generation may publish progress; ambiguous verify or completion results reconcile before retransmission.

## Acceptance Criteria

1. One slow object among healthy peers replaces only itself; healthy object state and progress remain untouched.
2. Peer-wide slowdown cannot create a reconnect storm and permits no more than one probe concurrently.
3. The 30% slow threshold, 50% self drop, 20% peer stability, three-window persistence, and boundary values are deterministic.
4. Replacement is skipped unless its estimated duration is less than or equal to half the continuing duration.
5. Basic PUT replacement starts from byte zero and never reports offset resume.
6. Multipart retains only confirmed ETag parts for the same action, retries the unconfirmed part, and never reuses ETags across an unverified new action.
7. Cooldowns, fresh windows, improvement checks, and a three-replacement cap prevent immediate or infinite replacement loops.
8. Ambiguous completion or verify state is reconciled before retransmission; confirmed remote content is not uploaded twice.
9. Source mutation, stale attempt results, action expiry, permission, quota, malformed protocol responses, and local resource failures stop safely without credential disclosure.
10. Parent total timeout still terminates the isolated child and all requests without false success; existing upload, commit, pointer, and resumable regressions remain green.
11. Documentation describes the recovery behavior and its conservative limitations without overstating the diagnosed upstream cause.

## Verification And Delivery

- Add and register focused executable `tests/test_lfs_slow_flow_recovery.py`; demonstrate failure before implementation.
- Run the new focused test plus affected LFS preupload, resumable recovery, commit, batching, progress, dataset routing, canonical pointer, auto-configure, validation, and CLI surface tests.
- Run `python tests/run_cli_baseline.py`, `python -m compileall -q .`, `python -m pip check`, and `git diff --check` in the `atomgit_cli` conda environment.
- Inspect real locked dependency signatures after implementation and audit the final diff for credentials, generated artifacts, and unrelated changes.
- Perform the independent review in `.ai/REVIEW.md`; resolve every P0/P1 finding and record the verdict.
- Delivery mode: `local task branch based on yuto, then local merge into yuto and push only yuto after implementation, tests, review, and maintainer authorization`.
- Authorized by maintainer on `2026-08-12`: `start the accepted implementation and complete development, testing, commit, and push`.
- Standing delivery rules authorize a concise conventional task commit, local merge into `yuto`, and push of only `yuto`; the task branch remains local-only.
- Not authorized: `task-branch push, PR, remote Issue transition, tag, release, publication, deletion, or any remote write outside the standing delivery action`.
- Human acceptance: `the maintainer's explicit start-through-push instruction is recorded as delivery authorization; final implementation evidence and review must still satisfy this contract before delivery`.

## Review Record

- First verdict: `REQUEST CHANGES`
- P1 finding: `the object's stable self baseline was initialized once instead of rolling with later stable windows, so a connection that first accelerated and then collapsed could be compared to an obsolete low baseline and escape recovery`.
- P2 finding: `the payload wrapper yielded 4 MiB chunks, making one application-level sample take about 40 seconds at the diagnosed 0.1 MiB/s tail instead of approximating the accepted 5-second sampling cadence`.
- Additional conformance finding: `a replacement was accepted after 2x improvement even when it remained below 70% of a current stable peer baseline`.
- Disposition: `resolved by rolling the self baseline, using bounded 512 KiB request chunks, and requiring both 2x improvement and 70% peer recovery when peers are available; focused and mandatory verification were repeated`.
- Second verdict: `APPROVED`; no remaining findings.
- Residual risk: `offline tests cannot reproduce the live object-storage TCP and flow-control timing; the prior controlled diagnosis supplies the behavior evidence, and this implementation Issue performed no additional remote write`.
