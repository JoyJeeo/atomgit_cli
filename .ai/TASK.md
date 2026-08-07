# Current Issue Contract

# Issue UPLOAD-SYMLINK-SAFETY

Status: `active`

## Identity

- Local Issue: `UPLOAD-SYMLINK-SAFETY`
- Title: `Reject symlinks before upload content can escape the selected path`
- Type: `security`, `bug`, `cli`, `sdk`
- Priority: `P1`
- Branch: `codex/fix-upload-symlink-safety` (local only)
- Base: `yuto`
- Previous Issue: `REPO-DELETE`, delivered on `yuto` by `7b98b90`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

The locked `huggingface-hub==1.1.7` folder upload implementation enumerates
entries with `Path.glob("**/*")` and accepts every `path.is_file()`. A symlink
to a regular file therefore becomes a commit operation whose source path reads
the target contents, including when that target is outside the selected upload
directory. The same enumeration is used by `upload_large_folder`.

An offline reproduction created an upload directory containing
`linked.txt -> ../outside.txt`. The real locked dependency selected one upload
operation, retained the symlink as its source path, resolved it outside the
upload root, and read the outside sentinel content. Current CLI and SDK paths
perform no symlink validation before delegating to the dependency.

Uploads must fail closed before credential access, worker creation, or any
remote request when the selected file/directory is itself a symlink or a
directory tree contains a file, directory, or broken symlink. Ordinary regular
files and directories must retain their existing behavior.

## Scope And Acceptance

- Add one shared Python 3.8-compatible upload-path scanner that does not follow
  directory symlinks and raises rather than silently skipping traversal errors.
- Reject a symlink selected as a CLI single-file or directory upload root.
- Reject nested regular-file, directory, and broken symlinks for ordinary and
  resumable CLI directory uploads before credentials or HF calls are used.
- Apply the same directory contract to public `atomgit_hub.upload_folder` so
  CLI and SDK do not drift on the shared upload behavior.
- Return nonzero with concise credential-safe CLI guidance; retain the SDK's
  existing validation-error convention and public function signature.
- Do not add a follow-symlink option, copy/stage trees, alter ignore semantics,
  change repository contents, or implement another audited defect or feature.
- Add focused regressions that bind the behavior to the real locked dependency
  evidence and prove all upload routes avoid their downstream calls.
- Update the smallest authoritative user and architecture documentation.
- Run focused and complete offline tests, compileall, diff checks, credential
  and scope audits, and the independent review required for security changes.

## Compatibility And Risks

- Existing uploads containing symlinks will now fail instead of dereferencing
  them. This is an intentional security compatibility change.
- No live upload is required: acceptance is observable before any network
  boundary and must be established with the real locked dependency plus strict
  offline fakes.
- A hostile local process that can mutate an upload tree after validation is a
  residual time-of-check/time-of-use risk in the dependency API; eliminating
  it would require staging or dependency-level descriptor support and is out of
  scope for this smallest safe fix.

## Permissions

- The user explicitly authorized issue-by-issue fixes for the currently
  confirmed defects and excluded new feature development.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- No live AtomGit write, Git credential mutation, repository creation,
  deletion, visibility change, release, or publication is authorized or
  required for this Issue.

## Required Evidence And Closure

- [x] Regression fails against the previous behavior and covers root, nested
      file, nested directory, and broken symlinks.
- [x] CLI single-file, ordinary directory, and resumable directory paths fail
      before credential/HF/worker access.
- [x] SDK folder upload fails with its documented validation-error convention.
- [x] Regular upload paths retain existing exact HF 1.1.7 call contracts.
- [x] Focused tests and the complete isolated pytest suite pass in the
      `atomgit_cli` conda environment.
- [x] `python -m compileall -q .` and `git diff --check` pass.
- [x] Documentation, credential scan, final scope, and clean-artifact audit
      pass.
- [x] Independent review records no open P0/P1/P2/P3 finding and returns
      `APPROVED`.
- [x] Human acceptance is covered by the user's standing ordered-fix approval.
- [ ] The completed task branch is committed, merged locally into `yuto`, and
      only `yuto` is pushed.

## Implementation Evidence

- Previous-behavior regression: before the implementation,
  `python tests/test_upload_symlink_safety.py` passed only 4/28 checks. The real
  locked HF folder preparation read the outside sentinel, while CLI/API/SDK
  symlink cases reached credentials or transfer paths and lacked actionable
  symlink output.
- Implementation: `validate_upload_path_no_symlinks` performs a non-following,
  fail-closed tree walk and reports only the lexical relative entry. CLI runs
  it before login-state access; CLI API methods repeat the check at their own
  boundary before stored credentials; the public SDK validates before token
  resolution. File, directory, broken, ignored, and resumable symlink paths are
  rejected without starting a transfer or worker.
- Locked dependency evidence: the regression invokes the installed
  `HfApi._prepare_upload_folder_additions` from `huggingface-hub==1.1.7` and
  proves that it selects the escaping symlink source and reads its target.
  `python tests/test_hf_api_contract.py` also passed 12/12 installed-signature
  checks.
- Focused offline evidence: `python tests/test_upload_symlink_safety.py` passed
  34/34; upload file, fallback, ignore, resumable, SDK lifetime/parameters,
  validation, and HF contract scripts all passed.
- Complete offline evidence: `python -m pytest -ra` collected and passed 53/53
  isolated scripts on macOS with Python 3.10.20. `python -m compileall -q .`
  and `git diff --check` passed.
- Documentation: README, architecture, and upload analysis now state the
  fail-closed symlink policy and that ignore patterns cannot bypass it.
- Security and scope: changed tests use only fake tokens and temporary files;
  credential scan found no real secret. No live request, remote write, Git
  credential mutation, new feature, dependency change, or generated artifact
  is part of the diff.
- Residual risk: a concurrently mutating local process can replace an entry
  after validation and before the locked dependency reads it. Preventing that
  race requires staging or dependency-level descriptor support and remains
  explicitly outside this Issue.
- Independent review: no P0/P1/P2/P3 finding remains open. The review confirmed
  early rejection at CLI, CLI API, SDK, resumable-worker, and locked-dependency
  boundaries; exact ordinary upload contracts, Python 3.8 syntax, safe relative
  output, documentation, tests, and scope agree. Live upload was correctly not
  run because the defect and fix are fully observable offline. Symlink fixtures
  may be skipped only when the host cannot create them; the current macOS run
  exercised every fixture. Verdict: `APPROVED`.
