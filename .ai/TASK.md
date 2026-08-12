# Current Issue Contract

Status: `active`

This is the repository's single persistent handoff for active, multi-turn, or
cross-conversation work. It records task facts and permissions; it does not
authorize work by itself. The current user request and real Git state remain
authoritative.

This is a local Issue contract. It is not backed by, and does not require, a
remote GitHub Issue.

## Handoff Snapshot

- Updated: `2026-08-12 09:46:51 +0800`
- Status: `active`
- Phase: `maintainer accepted the implementation and authorized local commit, local merge into yuto, and push of yuto; delivery in progress`
- Base branch: `yuto`
- Task branch: `codex/fix-lfs-pointer-newline` based on `yuto`
- Base commit / current HEAD: `cebb453623988a0b5df449df6e035cec3fb31c5a`
- Remote base: `github/yuto` at `cebb453623988a0b5df449df6e035cec3fb31c5a`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit/atomgit_cli`
- Worktree state: `dirty with the task-scoped implementation, tests, documentation, and this handoff; no commit is authorized`
- Changed paths: `.ai/ARCHITECTURE.md`, `.ai/PRODUCT.md`, `.ai/TASK.md`, `README.md`, `api.py`, `atomgit_hub.py`, `docs/architecture.md`, `docs/faq.md`, `docs/upload_command_analysis.md`, `lfs_pointer.py`, `tests/cli_baseline_contract.py`, `tests/test_canonical_lfs_pointer.py`, `tests/test_runtime_policy.py`
- Last completed action: `maintainer accepted the implementation and explicitly authorized commit, merge, and push on 2026-08-12`
- Next exact action: `commit the cohesive Issue diff on the local task branch, merge it locally into yuto, push only yuto, then record exact delivery references and close this task`
- Required worktree: `this worktree while .ai/TASK.md is uncommitted; no checkpoint commit was authorized merely for handoff`
- Remaining boundary: `the latest user request is scoped to all repositories using this CLI; this repository implements and verifies that repository-independent boundary. The unavailable AtomGit service serializer itself remains unfixed, so non-CLI clients remain an explicit external-service risk rather than an advertised client fix`
- Regression evidence: `python tests/test_canonical_lfs_pointer.py failed before implementation with ModuleNotFoundError; the added V5 transport regression then failed by leaking HTTPError out of verification; both now pass in a 24/24 suite. Real git-lfs 3.7.1 returns 0 for the canonical pointer and 2 for the missing-final-LF form. python tests/test_runtime_policy.py failed before the import-order fix because a fresh process bound https://huggingface.co and now passes 9/9 with https://hub.atomgit.com`
- Focused offline tests: `test_upload_file_no_copy.py 16/16; test_upload_batching.py 9/9; test_upload_resumable.py 47/47; test_resumable_commit_policy.py 51/51; test_resumable_recovery.py 5/5; test_dataset_resumable_route.py 11/11; test_sdk_upload_parameters.py 14/14; test_sdk_upload_lifetime.py 11/11; test_sdk_upload_timeout.py 7/7; test_hf_api_contract.py 13/13`
- Complete offline gate: `post-fix python tests/run_cli_baseline.py passed 67/67 in 48.73s; python -m compileall -q . passed; python -m pip check reported no broken requirements; git diff --check passed. Additional post-fix checks passed: test_runtime_policy.py 9/9, test_upload_error_classify.py 42/42, test_sdk_exceptions.py 34/34`
- Live acceptance: `authorized test repository weixin_52273949/test_datasets; initial exact-payload probe committed a53ea672a1c6a4ad089db542e82916a0e011a6aa after an ambiguous timeout and was reconciled byte-exact; real atomgit CLI dataset upload committed f3401611dda69d631be460778b194d3d6cbfe7f8; its 127-byte pointer ended in one LF, strict check returned 0, the 61-byte smudged object SHA-256 was ae7b084c55701dda9b87462c595896daae3b1aa7b3e968e75523e40d344b2144, and clean round-trip matched the committed pointer`
- Tests not run: `no service test because service source is unavailable; no full normal clone because the only authorized repository contains large historical LFS objects; no claim that its whole worktree is clean because 111 pre-existing noncanonical pointers remain; no existing-pointer repair, deletion, separate model-repository live acceptance, or history rewrite was authorized or performed. Model and dataset CLI behavior share the tested transfer boundary and are covered offline; only the authorized dataset repository was used live. Python 3.9 syntax compatibility was reviewed, but the complete baseline ran in the locked Python 3.10 environment rather than a separate Python 3.9 runtime`

## Active Issue Identity

- ID: `LOCAL-CANONICAL-LFS-POINTER`
- Title: `Ensure CLI-uploaded Git LFS pointers are canonical`
- Primary type: `bug`
- Priority: `P1`
- Observable objective: `every future LFS file uploaded through this AtomGit CLI/SDK path, independent of repository identity and model/dataset logical type, must be committed as a canonical Git LFS pointer ending in exactly one LF and must fail closed if the returned commit cannot be verified byte-exact`
- User impact: `CLI-uploaded LFS files can make a fresh clone immediately dirty even when the user did not modify data; automation and users see false modified entries across many large files`
- Current behavior: `Git upload produces a canonical pointer and a clean clone; atomgit upload can produce a pointer whose size line has no terminating LF, after which git-lfs clean canonicalizes it and git status reports modified`
- Expected behavior: `Git and CLI uploads produce byte-equivalent canonical pointers; downloaded real files and skip-smudge pointer checkouts both round-trip through git-lfs clean without a diff`
- Affected end-to-end path: `atomgit upload -> huggingface_hub upload_file/upload_folder/upload_large_folder -> HfApi.create_commit -> NDJSON lfsFile(path, algo, oid, size) -> AtomGit service commit handler -> Git pointer blob -> clone/checkout -> git-lfs clean/status`

## Reproducible Evidence

- The affected repository diff showed only the missing terminal newline:

  ```diff
   version https://git-lfs.github.com/spec/v1
   oid sha256:97c6e33a80d71b6494c722cfa6d1c38039581fbbca14fb306266aa9140b51b63
  -size 711256710
  \ No newline at end of file
  +size 711256710
  ```

- The affected commit was identified as `9bbbe4d Upload folder using atomgit client`.
- A fresh clone was already dirty before user edits, excluding ordinary local
  data modification as the cause.
- A Git/Git-LFS upload of equivalent files does not reproduce the dirty clone.
- The working tree can contain the real 711,256,710-byte object after smudge;
  the object data, SHA-256, and size are not the defect. The Git pointer blob is.
- `git lfs pointer --check` accepts the missing-LF pointer, but
  `git lfs pointer --check --strict` returns `2`; the canonical pointer returns
  `0` for both checks.

## Confirmed Technical Boundary

- Current `atomgit_cli` source contains no Git LFS pointer template and does
  not serialize the three pointer lines.
- Single-file upload uses `huggingface_hub.upload_file`; ordinary directory
  upload uses `upload_folder`; resumable directory upload uses
  `upload_large_folder`. All LFS paths converge on `HfApi.create_commit`.
- Locked `huggingface-hub==1.1.7` sends an LFS commit operation as:

  ```json
  {
    "key": "lfsFile",
    "value": {
      "path": "sample.bag",
      "algo": "sha256",
      "oid": "<sha256>",
      "size": 711256710
    }
  }
  ```

- The dependency's NDJSON record ends in LF, but the request contains no LFS
  pointer text. The NDJSON delimiter is unrelated to the final LF inside the
  Git pointer blob.
- Therefore the demonstrated missing LF is introduced after the client
  request, at the AtomGit service boundary that converts `lfsFile` metadata
  into a Git blob, unless that service has since received an unobserved hotfix.
- The canonical pointer must be exact ASCII bytes:

  ```text
  version https://git-lfs.github.com/spec/v1\n
  oid sha256:<64-lowercase-hex>\n
  size <non-negative-decimal>\n
  ```

## Scope And Work Packages

The Issue has one end-to-end outcome, but the root fix and defenses cross an
external service boundary. Keep each work package explicit and do not pretend
the current repository contains the service implementation.

### A. Root Service Fix — External Boundary, Not Available In This Repository

The latest user request requires a root, repository-independent fix for future
users of this CLI, and explicitly authorizes live testing only against the
provided dataset repository. The client delivery below satisfies that CLI
boundary without repository-specific cases. The following service work remains
the preferred platform-wide follow-up for non-CLI clients, but cannot be part of
this repository's acceptance because the service source was not provided or
found:

- Locate the AtomGit service handler for commit API `lfsFile` operations,
  including the dataset route and any separate model route.
- Add a failing exact-byte regression before the fix.
- Serialize a canonical pointer ending in exactly one ASCII LF (`0x0A`).
- Use fixed LF, never platform-dependent line endings.
- Validate SHA-256 as 64 hexadecimal characters and size as a non-negative
  decimal integer before materializing the blob.
- Prefer one shared canonical pointer serializer for every repository type and
  commit route.
- Preserve LFS object OID, size, path, file mode, and existing commit semantics.

### B. Generic CLI/SDK Commit Contract — Current Delivery Scope

- Determine whether AtomGit exposes a raw Git blob/tree API that returns the
  pointer blob rather than resolving it to the large LFS object.
- If such a stable API exists, add a bounded post-commit check for newly
  committed LFS paths: version, OID, size, and terminal LF must match.
- If the service returns a noncanonical pointer, do not report an unconditional
  upload success; emit a credential-safe actionable error that identifies the
  service-generated pointer contract violation.
- Do not download the large LFS object merely to validate its pointer.
- Preserve the locked client's LFS object preupload and server-selected upload
  mode, then replace only the final `lfsFile` commit record with exact canonical
  pointer bytes for every LFS path.
- Verify the raw blob through the confirmed, authenticated V5 contents contract
  at the exact returned commit. Treat noncanonical bytes, malformed responses,
  transport failures, and unverifiable no-op/reconciled commits as failures,
  without exposing token, URL, response body, or path details.
- Apply this shared mechanism to single-file, ordinary-folder, resumable-folder,
  CLI, SDK, model-route, dataset-route, revision, and normalized multi-level-ID
  paths without any repository-name, object-ID, or fixture-specific branch.

### C. Existing Repository Repair — Planned, Remote Authorization Required

- Deploy and verify the root service fix before repairing old branches, so new
  CLI uploads cannot reintroduce the defect.
- Repair active branch tips with a dedicated normalization commit; do not
  rewrite published history by default.
- For large repositories, use a dedicated `GIT_LFS_SKIP_SMUDGE=1` clone or a
  server-side tree repair so hundreds of GB of LFS objects are not downloaded.
- Before committing, prove for every staged path that the new blob equals the
  old pointer plus exactly one LF and that path, OID, size, and mode are
  unchanged.
- Do not stage unrelated AppleDouble `._*` deletions or user worktree changes.
- Existing historical commits and tags remain noncanonical unless history is
  explicitly and separately authorized for rewriting.

## Out Of Scope

- Treating cache clear, `.gitattributes`, worker count, batching, timeout, OS,
  filesystem, or `GIT_LFS_SKIP_SMUDGE` as the root fix.
- Re-uploading unchanged LFS binary objects merely to normalize pointer blobs.
- Changing locked dependencies without a separate dependency-policy decision.
- Rewriting public Git history, force-pushing, deploying a service, or repairing
  a live repository without exact authorization.
- Any write to an `openlet` dataset.
- Broad upload refactoring unrelated to pointer canonicalization.

## Acceptance Criteria

- The CLI/SDK commit serializer ends the size line in exactly one LF for every
  LFS operation after the normal LFS object upload completes.
- Canonical output passes `git lfs pointer --check --strict` with exit code `0`.
- Missing-final-LF input or output is covered by a regression that fails before
  the fix.
- CLI single-file, ordinary-folder, and resumable LFS uploads all reach the
  corrected commit contract without changing their public options.
- Dataset and model logical types are covered by offline routing tests and the
  documented shared AtomGit transfer route; the separately authorized live
  fixture covers that shared route in the provided dataset repository.
- The committed pointer OID and size equal the original file SHA-256 and byte
  count; the LFS object is unchanged.
- A newly uploaded pointer passes strict Git LFS validation, and smudge/clean
  round-trip reproduces the exact committed bytes and original object digest.
  Whole-worktree cleanliness is not asserted for the provided repository
  because its pre-existing history contains 111 unrelated malformed pointers.
- Git-native LFS upload behavior remains unchanged and clean.
- Any client-side verification uses raw pointer bytes, never the resolved large
  object, and produces no token, signed URL, response body, or local path leak.
- Existing-repository normalization is separately authorized and stages only
  the intended pointer-byte changes.

## Required Offline Verification

- Exact-byte unit test for canonical pointer serialization.
- Negative regression for a pointer lacking the final LF.
- `git lfs pointer --check --strict` integration check when git-lfs is present.
- Contract test proving the locked HF client sends only `lfsFile` metadata and
  does not own pointer formatting.
- Routing tests for upload_file, upload_folder, and upload_large_folder.
- Dataset/model route coverage at the shared client transfer boundary.
- Client raw-blob verification tests if that defense is implementable.
- Existing affected upload suites and `python tests/run_cli_baseline.py` in the
  `atomgit_cli` conda environment for any client change.
- `python -m compileall -q .`, `python -m pip check`, and `git diff --check`.
- Independent no-edit review under `.ai/REVIEW.md` before acceptance.

## Separately Authorized Live Acceptance

The maintainer authorized `weixin_52273949/test_datasets` on 2026-08-11 as the
exact test repository for this Issue. Authorization covers read-only Git/API
inspection plus upload of uniquely named small LFS fixtures needed to reproduce
and verify the future CLI behavior. Test fixtures may be retained; deletion,
history rewriting, repair of existing pointers, or unrelated repository changes
remain unauthorized. The acceptance sequence is:

1. Upload one small LFS-classified fixture through the corrected CLI/service
   path; no production-scale object is required.
2. Read the committed raw Git blob and verify its final byte is `0x0A`.
3. Run strict pointer validation.
4. Prove the newly committed pointer is stable under Git LFS clean and that
   smudge returns the original fixture bytes. Do not use unrelated historical
   malformed pointers as evidence about the new upload.
5. Verify downloaded object SHA-256 and size.
6. Delete or retain the disposable repository only according to the explicit
   cleanup authorization.

## Compatibility

- Preserve Python 3.9+, `huggingface-hub==1.1.7`, and `datasets==4.4.1` in this
  client repository unless dependency policy is separately changed.
- Preserve current CLI flags, SDK signatures, repo type handling, revision
  handling, resumable metadata, and LFS object transfer behavior.
- A final LF is the canonical Git LFS representation and must be identical on
  all operating systems.

## Permissions And Delivery

- Local Issue activation and `.ai/TASK.md` handoff update: `authorized`.
- Local source, focused tests, and affected documentation necessary for this
  Issue: `authorized for the next implementation conversation`.
- Focused task branch based on `yuto`: `authorized`; use
  `codex/fix-lfs-pointer-newline` unless a repository-specific service branch
  convention requires another name.
- Offline validation and independent review: `authorized`.
- Local commit: `authorized by the maintainer on 2026-08-12`.
- Merge into `yuto`: `authorized by the maintainer on 2026-08-12`.
- Push: `authorized for yuto only on 2026-08-12`; the local task branch must not
  be pushed under the standing delivery rules.
- PR, remote Issue transition, release, and service deployment: `not authorized`.
- Live AtomGit reads and uniquely named small LFS fixture uploads to
  `weixin_52273949/test_datasets`: `authorized for this Issue`.
- Live repository creation, existing-pointer repair, Git push, history rewrite,
  or deletion: `not authorized`.
- Writes to any `openlet` dataset: `explicitly prohibited`.
- Service-source edits: `not possible until the correct service repository is
  provided or found and its repository instructions and permissions are read`.

## Next-Conversation Recovery Checklist

1. Read `AGENTS.md`, `.ai/README.md`, and this complete file.
2. Inspect repository root, branch, HEAD, worktrees, status, recent log, and
   diff; reconcile against the snapshot above.
3. Read `.ai/MASTER_PROMPT.md`, `.ai/DEVELOPMENT_RULES.md`, `.ai/DOD.md`,
   `.ai/TESTING.md`, `.ai/STYLE_GUIDE.md`, `.ai/ARCHITECTURE.md`, and the
   relevant service repository instructions once that repository is known.
4. Confirm `atomgit_cli` conda activation and locked dependency versions.
5. Continue on `codex/fix-lfs-pointer-newline` in this exact worktree; preserve
   all uncommitted task changes and do not make an unauthorized checkpoint.
6. Reconcile the generic CLI/SDK implementation and its tests against the
   current handoff; do not reopen unavailable service-source work without new
   source and explicit scope.
7. Run focused and required offline tests, update this handoff, perform the DoD
   audit and independent review, then request human acceptance and any further
   Git or live-test authorization.

## Human Acceptance And Delivery Status

- Human acceptance: `accepted by the maintainer on 2026-08-12; commit, local merge into yuto, and push of yuto explicitly authorized`.
- Definition of done: `all implementation, automated, live-client, documentation, security, compatibility-signature, review, and human-acceptance gates passed; authorized Git delivery is in progress`.
- Independent review: `the first final review returned REQUEST CHANGES for missing git-lfs strict integration, V5 transport misclassification, and stale service/live-clone scope. The executable findings were reproduced and fixed, the contract was reconciled to the latest user request, and the fresh post-fix review found no P0-P3 issues and returned APPROVED`.
- Delivery: `authorized and in progress; task branch remains local-only`.
- Live verification: `passed for two uniquely named small LFS fixtures in the authorized dataset test repository; existing history was not repaired`.
