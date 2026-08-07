# Current Issue Contract

# Issue PRIVATE-EXIST-OK-VERIFY

Status: `ready-for-delivery`

## Identity

- Local Issue: `PRIVATE-EXIST-OK-VERIFY`
- Title: `Converge and verify private visibility for idempotent CLI creation`
- Type: `security`, `bug`, `cli`
- Priority: `P1`
- Branch: `codex/fix-private-exist-ok-verify` (local only)
- Base: `yuto`
- Previous Issue: `UPLOAD-SYMLINK-SAFETY`, delivered by `708d47f`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

The CLI accepts `atomgit repo create REPO --type TYPE --private --exist-ok` and
reports that the repository exists or was created. The current implementation
passes `private=True, exist_ok=True` to locked HF `create_repo` but verifies
visibility only when public was requested.

The installed `huggingface-hub==1.1.7` implementation treats an HTTP 409 with
`exist_ok=True` as success and returns the existing repository response; it
does not update that repository's visibility. An existing public repository can
therefore remain public while the CLI reports success for an explicit private
request.

Every successful CLI create must converge the repository to the explicitly
requested visibility and GET-verify the final state. A mismatch or unverifiable
state must return nonzero and explain that the remote visibility may be
unknown; it must never claim private success based only on the HF create call.

## Scope And Acceptance

- Preserve the existing safe sequence that asks HF to create privately.
- After HF returns, use the existing V5 visibility update and verification for
  both requested private and public states, including `--exist-ok`.
- Report success only after the verified V5 state matches the explicit CLI
  request; retain credential-safe unknown-state guidance on failure.
- Keep non-`--exist-ok` preflight behavior, model/dataset compatibility route,
  CLI arguments, and exit codes unchanged except for correcting false success.
- Add a regression proving private `exist_ok` invokes verified visibility and
  fails when convergence cannot be verified.
- Confirm public, new private, dataset, existing-default rejection, locked HF
  signature, and CLI forwarding compatibility.
- Update the smallest authoritative CLI/architecture documentation.
- Do not change the public Python SDK `create_repository` contract in this CLI
  Issue, implement another audited defect, or add any new feature.

## Compatibility And Risks

- Private creation now performs the same authenticated V5 PATCH/GET verification
  already required for public creation. A transient verification failure may
  turn a previously successful exit into an accurate nonzero unknown-state
  result even when HF created the repository.
- No live visibility mutation is authorized or required. Strict offline tests
  must prove request sequencing and false-success prevention.
- The public Python SDK remains private-only and outside this CLI Issue; its
  idempotent visibility semantics require a separately selected SDK Issue if
  the maintainer later includes SDK defects in the repair scope.

## Permissions

- The user authorized issue-by-issue fixes for confirmed CLI defects and
  excluded new functionality.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- No live repository creation, upload, visibility mutation, deletion, Git
  credential change, release, or publication is authorized or required.

## Required Evidence And Closure

- [x] Previous behavior is reproduced by a failing regression.
- [x] Private and public create paths both call verified visibility convergence.
- [x] `--private --exist-ok` cannot succeed when visibility verification fails.
- [x] Model/dataset routing, preflight, CLI forwarding, and HF 1.1.7 signatures
      remain compatible.
- [x] Focused and complete offline tests, compileall, and diff checks pass.
- [x] Documentation, credential scan, scope audit, and independent review pass.
- [x] Human acceptance is covered by the standing ordered-fix authorization.
- [ ] The task is committed, merged into `yuto`, and only `yuto` is pushed.

## Verification Evidence

- Previous behavior: the new regression passed only the public-failure case
  (`1/3`); private creation and private `exist_ok` did not request verified V5
  convergence.
- Focused offline scripts: create visibility `3/3`, create contract `42/42`,
  repository visibility `22/22`, and repository ID contract `68/68`.
- Complete offline suite: `pytest` collected `53` items and exited `0`.
- Compatibility: installed `huggingface-hub==1.1.7`; the real `create_repo`
  signature accepts the exact keyword set used by the implementation.
- Static checks: `python -m compileall -q .`, `python -m pip check`, and
  `git diff --check` passed.
- Security and scope: credential-pattern scan found no secret material; no live
  request or remote repository mutation ran; only this Issue's CLI create
  convergence, regression coverage, and authoritative docs changed.
- Independent review: initial `REQUEST CHANGES` for one stale code comment;
  after correction and complete revalidation, `APPROVED` with no P0-P3
  findings. Residual risk is limited to the intentionally unrun live visibility
  mutation test.
