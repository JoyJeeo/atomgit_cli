# Current Issue Contract

Status: `completed`

## Identity

- Planning Issue: `ROADMAP-008`
- Title: `Replace shared single-file upload fallback directory`
- Type: `bug`, `security`
- Priority: `P2`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `bbce9ff`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

When single-file upload falls back to `upload_folder`, it creates the fixed
`.tmp_upload` directory in the caller's working directory. Concurrent commands
can overwrite or delete each other's content, and interrupted processes can
leave user-visible artifacts.

## Scope

In scope: use a unique system temporary directory for every fallback call,
preserve upload layout and cleanup on success/failure, and add offline
regression coverage.

Out of scope: default direct `upload_file`, SDK upload behavior, ignore
semantics, remote writes, and dependency upgrades.

## Acceptance Criteria

- Every fallback invocation uses a unique directory outside the working tree.
- The source content and `path_in_repo` layout exist during the HF call.
- Temporary directories are removed after success and failure.
- Existing direct-upload behavior and complete offline tests remain green.

## Permissions

- Authorized: local implementation, tests, affected documentation,
  cohesive commit, and push of the current branch.
- Not authorized: AtomGit remote writes, real credential changes, merge,
  release, or PyPI publication.

## Delivery Record

- Replaced the fixed working-directory `.tmp_upload` fallback with a unique
  `TemporaryDirectory` per call while preserving repository layout and HF
  arguments.
- Regression test passed 12/12 and proves content lifetime, uniqueness,
  cleanup after success/failure, and absence of a working-tree fallback.
  Existing direct-file and ignore suites passed 14/14 and 22/22.
- Updated API, architecture, and upload-analysis documentation to describe
  the unique temporary-resource contract.
- All 26 offline scripts, `python -m compileall -q .`, and
  `git diff --check` passed with isolated user state.
- Independent review found no blocking implementation issue and identified
  stale architecture text, which was corrected before re-review. Residual
  abrupt-process cleanup is limited to normal operating-system temporary-file
  semantics. Verdict: `APPROVED`.

# Completed Issue SDK-CREATE-VISIBILITY

Status: `completed`

## Identity

- Local Issue: `SDK-CREATE-VISIBILITY`
- Title: `Align SDK repository creation with verified AtomGit semantics`
- Type: `bug`, `sdk`, `compatibility`
- Priority: `P1`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `d92fa76`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

The CLI rejects public creation because AtomGit public semantics cannot be
reliably verified, but `atomgit_hub.create_repository` still defaults to a
public call and can report false success. It also accepts Space-only options
that the AtomGit product does not support and silently drops them.

## Scope

In scope: require private model/dataset creation in the SDK, explicitly reject
unsupported public, repository-type, and Space semantics before a remote call,
bind valid calls to the HF 1.1.7 signature, and update the SDK docstring.

Out of scope: remote verification, repo ID normalization, exception hierarchy,
CLI changes, and dependency upgrades.

## Acceptance Criteria

- Public SDK creation fails clearly without invoking HF.
- Private model and dataset creation forwards token, type, privacy, and
  `exist_ok` through a strict HF signature fake.
- Invalid repository types and every Space-only option fail before HF.
- Existing public function parameters remain present for compatibility.
- Focused and complete offline tests, compileall, and diff checks pass.

## Permissions

- Authorized: local implementation, tests, affected SDK documentation,
  cohesive commit, and push of the current branch.
- Not authorized: AtomGit remote writes, real credential changes, merge,
  release, or PyPI publication.

## Delivery Record

- SDK creation now matches the CLI's verified service boundary: only private
  model/dataset repositories are allowed; public and Space semantics are
  rejected before token lookup or HF invocation.
- `tests/test_sdk_create_contract.py` binds valid calls to the installed HF
  1.1.7 signature and covers public creation, both supported types, invalid
  types, all six retained Space parameters, token, privacy, and `exist_ok`.
- Focused test passed 21/21; the existing CLI visibility regression remained
  green. All 25 offline scripts, `python -m compileall -q .`, and
  `git diff --check` passed with isolated user state.
- Independent review found no blocking correctness, compatibility, security,
  or scope issue. Public function parameter names remain available while
  unsupported behavior is explicit. Verdict: `APPROVED`.

# Completed Issue ROADMAP-006

Status: `completed`

## Identity

- Planning Issue: `ROADMAP-006`
- Title: `Restore SDK Hugging Face timeout state`
- Type: `bug`, `sdk`, `compatibility`
- Priority: `P1`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `e5fe541`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

`atomgit_hub.upload_folder` overwrites HF's process-global
`DEFAULT_REQUEST_TIMEOUT` but never restores it. One SDK upload therefore
changes unrelated later HF operations in the same Python process.

## Scope

In scope: restore the exact prior timeout after successful and failed SDK
uploads, add focused offline coverage, and preserve existing parameter and
temporary-resource behavior.

Out of scope: CLI progress behavior, a concurrency architecture redesign,
stable exception classes, remote writes, and dependency upgrades.

## Acceptance Criteria

- The requested timeout is visible during the HF upload call.
- The previous timeout is restored after success and HF failure.
- Existing SDK upload lifetime and parameter tests remain green.
- Complete offline tests, compileall, and diff checks pass.

## Permissions

- Authorized: local implementation, tests, affected documentation,
  cohesive commit, and push of the current branch.
- Not authorized: AtomGit remote writes, real credential changes, merge,
  release, or PyPI publication.

## Delivery Record

- Regression coverage observes the requested SDK timeout during both success
  and failure and proves the previous process-global value is restored.
- Implementation restores `DEFAULT_REQUEST_TIMEOUT` in the outer `finally`
  before temporary-resource cleanup; preflight failures do not mutate it.
- Focused timeout test passed 7/7, and the affected SDK lifetime/parameter
  suites passed 11/11 and 14/14. All 24 offline scripts,
  `python -m compileall -q .`, and `git diff --check` passed with isolated
  user state.
- Independent review found no blocking issue. Concurrent SDK uploads still
  share HF's process-global timeout by dependency design; this documented
  architectural limitation is not a state-leak regression. Verdict:
  `APPROVED`.

# Completed Issue ROADMAP-005

Status: `completed`

## Identity

- Planning Issue: `ROADMAP-005`
- Title: `Honor supported SDK upload parameters`
- Type: `bug`, `sdk`, `compatibility`
- Priority: `P1`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `de612ab`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

The public SDK accepts `repo_type`, `revision`, `commit_description`, and
`ignore_patterns` but silently drops all four. This creates behavior drift
from the CLI and makes supported-looking calls behave differently from their
documented contract.

## Scope

In scope: pass supported arguments to the locked HF upload API; map dataset
uploads to AtomGit's verified model transfer route; reject non-main revisions
consistently with the CLI; update the SDK docstring and add strict offline
regression coverage.

Out of scope: timeout restoration, stable exception classes, repo ID
normalization redesign, CLI changes, remote writes, and dependency upgrades.

## Acceptance Criteria

- Model/dataset type, main revision, commit description, and ignore patterns
  have explicit tested behavior at the HF boundary.
- Unsupported non-main revisions fail before any HF call.
- The fake binds received arguments to the real HF 1.1.7 signature.
- Existing public parameter names remain compatible.
- Focused and complete offline tests, compileall, and diff checks pass.

## Permissions

- Authorized: local implementation, tests, affected SDK documentation,
  cohesive commit, and push of the current branch.
- Not authorized: AtomGit remote writes, real credential changes, merge,
  release, or PyPI publication.

## Delivery Record

- Regression coverage proves the SDK previously dropped public upload
  parameters; the strict fake now binds every call to HF 1.1.7's real
  `upload_folder` signature.
- Implementation forwards model type, main revision, commit description, and
  ignore patterns; dataset transfers use AtomGit's verified model route.
  Unsupported repo types and non-main revisions fail before any HF call.
- The SDK docstring now states supported repository/revision values and the
  correct 300-second timeout default.
- Focused test passed 14/14. All 23 offline test scripts,
  `python -m compileall -q .`, and `git diff --check` passed with isolated
  user state.
- Independent review found one P2 input-boundary gap for arbitrary repo types;
  validation and regression coverage were added. Re-review found no blocking
  issues. Verdict: `APPROVED`.

# Completed Issue ROADMAP-004

Status: `completed`

## Identity

- Planning Issue: `ROADMAP-004`
- Title: `Fix SDK subdirectory upload lifetime`
- Type: `bug`, `sdk`
- Priority: `P1`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `ad05141`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

For a non-root `path_in_repo`, `atomgit_hub.upload_folder` creates a temporary
directory inside a context manager but calls HF only after that context has
already deleted the directory. The advertised SDK subdirectory upload cannot
reliably read its upload source.

## Scope

In scope: keep the reorganized upload directory alive for the complete HF
call, clean it on success and failure, and add an offline regression test.

Out of scope: SDK parameter forwarding, timeout restoration, exception API
redesign, CLI upload behavior, remote writes, and dependency changes.

## Acceptance Criteria

- The non-root temporary upload tree exists and contains the source content
  while `hf_upload_folder` executes.
- The temporary tree is removed after both success and HF failure.
- Root uploads continue using the original directory without a copy.
- Focused and complete offline tests, compileall, and diff checks pass.

## Permissions

- Authorized: local implementation, tests, documentation if affected,
  cohesive commit, and push of the current branch.
- Not authorized: AtomGit remote writes, real credential changes, merge,
  release, or PyPI publication.

## Delivery Record

- Regression: the previous implementation deleted a non-root temporary tree
  before the HF call. `tests/test_sdk_upload_lifetime.py` now verifies the
  tree and nested content exist during use.
- Implementation: the SDK holds the temporary directory through the complete
  upload and deterministically cleans it after success, HF failure, and local
  preparation failure; root uploads continue using the source directory.
- Focused verification passed 11/11. All 22 offline test scripts,
  `python -m compileall -q .`, and `git diff --check` passed in the required
  conda environment with isolated user state.
- Independent review initially found cleanup depended on object destruction
  when `copytree` failed. The preparation path was moved under `finally` and a
  regression case was added. Re-review found no blocking issues. The known
  SDK timeout leak remains explicitly out of scope for the next Issue.
  Verdict: `APPROVED`.

# Completed Issue ROADMAP-002

Status: `completed`

## Identity

- Planning Issue: `ROADMAP-002`
- Title: `Add locked Hugging Face API contract tests`
- Type: `testing`, `compatibility`
- Priority: `P1`
- Branch: `codex/close-development-backlog`
- Base: `yuto` at `0c05cb7`
- Delivery mode: sequential backlog delivery authorized by the maintainer;
  cohesive local commit and branch push are authorized after verification.

## User Impact And Evidence

Permissive `**kwargs` fakes previously accepted arguments rejected by the
locked `huggingface-hub==1.1.7`, including `token` passed directly to
`HfApi.upload_large_folder`. Existing tests cover that repaired path but do
not provide one authoritative contract check for upload, download, create,
and large-folder call signatures.

## Scope

In scope: offline tests binding representative AtomGit calls against the real
installed HF 1.1.7 signatures, including a negative large-folder token case;
test documentation and evidence.

Out of scope: production behavior changes, dependency upgrades, remote
AtomGit operations, pytest migration, and other roadmap items.

## Acceptance Criteria

- The test asserts the locked HF Hub and datasets versions.
- Representative upload-file, upload-folder, snapshot-download,
  file-download, create-repo, HfApi authentication, and large-folder calls
  bind to the installed callable signatures.
- Passing `token` to `upload_large_folder` is proven invalid while passing it
  to `HfApi` construction is valid.
- Focused and complete offline tests, compileall, and diff checks pass.

## Permissions

- Authorized: local source/test/documentation changes, isolated offline
  tests, cohesive commit, and push of the current branch.
- Not authorized: AtomGit remote writes, real credential changes, merge,
  release, or PyPI publication.

## Delivery Record

- Added `tests/test_hf_api_contract.py`, which binds ten positive and negative
  checks to the installed `huggingface-hub==1.1.7` and `datasets==4.4.1`
  contracts without network access.
- Focused verification: `python tests/test_hf_api_contract.py` passed 10/10.
- Complete verification: all 21 `tests/test_*.py` scripts passed in an
  isolated HOME; `python -m compileall -q .` and `git diff --check` passed.
- Documentation now records the offline dependency-contract command and its
  no-network boundary.
- Independent review found no blocking correctness, compatibility, security,
  or scope issue. Residual risk: signature binding does not prove AtomGit
  remote semantics. Verdict: `APPROVED`.

# Delivery History

Status: `completed`

## Identity

- GitHub Issue: `#1`
- Title: `[P1] Resumable upload timeout must cancel worker and report failure`
- Type: `bug`, `compatibility`
- Priority: `P1`
- Branch: `codex/issue-1-resumable-recovery`
- Base: `yuto` at `0f8a678`
- Delivery mode: authorized self-accepted branch delivery

## User Impact And Evidence

The resumable directory upload called `upload_large_folder` directly. When
the underlying worker exceeded `upload_timeout`, the CLI waited for it and
could return success even though the requested timeout had elapsed. The new
regression test reproduced a 0.25s worker completing after a 0.05s timeout.

## Current And Expected Behavior

- Current: resumable uploads can block beyond the configured timeout and report
  success after the worker finishes.
- Expected: the upload is bounded by `upload_timeout`; an expired transfer is
  terminated and reported as failure, while successful transfers preserve
  authentication and upload options.

## Scope

In scope: resumable upload execution, timeout cancellation, worker result
propagation, and offline regression coverage.

Out of scope: HF transfer protocol changes, ordinary uploads, remote writes,
or release work.

## Acceptance Criteria

- A slow resumable worker returns failure within the configured timeout.
- The worker is terminated after timeout and cannot later turn the operation
  into success.
- A successful worker returns success and keeps the existing token/API path.
- Existing resumable CLI options and all offline tests remain green.

## Required Tests

- `python tests/test_resumable_recovery.py`
- `python tests/test_upload_resumable.py`
- all `tests/test_*.py`, `python -m compileall -q .`, and `git diff --check`.

## Permissions

Authorized: local implementation/tests, commit, push, PR merge, and Issue #1
closure. No release or PyPI publication.

## Delivery Record

- Regression: focused test failed before the fix (5 checks, timeout returned
  success and exceeded the bound).
- Implementation: resumable upload now runs in an isolated multiprocessing
  worker, joins for the requested timeout, terminates expired workers, and
  propagates worker failures without exposing token data.
- Verification: focused test 5/5; resumable CLI test 13/13; all offline test
  scripts passed; compileall and diff check passed.
- Review: independent diff review found no blocking correctness, security,
  compatibility, or scope findings. Residual risk is limited to platform
  multiprocessing behavior and requires future live validation.
- Delivery: commit `57bb20d` pushed; PR #15 merged into `yuto` as merge commit
  `949e8c9`; Issue #1 was already closed remotely and no release was created.

## Active Issue #11

- Title: `[P1] Validate positive timeout and worker counts before starting uploads`
- Type: `bug`, `cli`; Priority: `P1`
- Branch: `codex/issue-11-upload-validation`; Base: `yuto` at `cedbc80`
- Scope: validate `--timeout` and `--num-workers` before upload execution;
  add offline CLI regression coverage. No remote writes or release.
- Acceptance: non-positive values exit 2 with actionable output; positive
  values remain accepted; existing offline suite remains green.
- Regression: new `tests/test_upload_validation.py` covers four invalid cases
  and one valid case; pre-fix invalid timeout cases reached upload execution.
- Implementation: `cli.upload` rejects timeout <= 0 and worker counts <= 0.
- Verification: focused test 5/5; all `tests/test_*.py`, compileall, and diff
  check passed.
- Review: independent review found no blocking findings; validation is
  side-effect free and preserves existing interfaces.
- Delivery: commit `91fc12a` pushed; PR #17 merged into `yuto`; Issue #11 was
  already closed remotely. No release was created.

## Issue #8 Delivery

- Fixed generated Git helper identity authentication to use the raw token
  header shared by login; failed identity lookup now returns no credential
  instead of `atomgit-user`.
- Added `tests/test_git_helper_identity.py`; focused test and all offline test
  scripts passed, as did compileall and diff check.
- Review found no blocking findings. Commit/PR delivery is authorized; no
  release or PyPI publication.

<!-- Previous Issue #13 delivery record retained below for historical context. -->

## Historical Issue #13

After `atomgit login`, Git combines the AtomGit host-specific helper with an
inherited generic helper. A live private `git ls-remote` invoked the macOS
`osxkeychain` store path and emitted `failed to store: -60006`. A normal user
environment could therefore copy the AtomGit token into an unrelated helper.

The current logout implementation also unsets the complete host-specific key,
so it cannot preserve values that existed before AtomGit login.

## Current And Expected Behavior

- Current: setup writes one host-specific helper value for each AtomGit host;
  inherited generic helpers remain active.
- Current: logout deletes the host-specific helper key rather than restoring
  the user's prior values.
- Expected: AtomGit hosts use an exclusive helper chain owned by AtomGit while
  logged in, unrelated hosts remain unchanged, and logout restores the exact
  prior user-global values.
- Expected: a partial setup failure rolls back both AtomGit host keys.

## Scope

In scope:

- `utils.py` Git credential-helper setup and cleanup behavior;
- `cli.py` logout failure propagation and retry of residual helper state;
- restrictive persistence of the prior host-specific helper state without
  writing the current login token;
- rollback for partial setup failure;
- isolated offline tests using temporary HOME and Git config files;
- affected Git-integration documentation.

Out of scope:

- Issue #8 username lookup authentication and fallback behavior;
- token/config storage policy outside helper-chain state;
- upload, download, repository, SDK, dependency, version, or release changes;
- changes to the user's real Git configuration or keychain.

## Compatibility

- Preserve the `setup_git_credentials(token) -> bool` and
  `clear_git_credentials() -> bool` interfaces.
- Support Python 3.8+ and the installed Git configuration semantics.
- Preserve unrelated Git configuration and all pre-existing multi-valued
  AtomGit host helper entries in order.
- Never persist or print the token in helper-state metadata or test fixtures.

## Acceptance Criteria

- An inherited generic helper is not invoked for AtomGit lookup, store, or
  erase after setup.
- The inherited helper remains active for an unrelated host.
- Setup installs an empty reset entry followed by the AtomGit-owned helper for
  both `atomgit.com` and `hub.atomgit.com`.
- Logout restores exact pre-existing user-global helper values for both hosts.
- A partial two-host setup failure restores the pre-operation state.
- Repeated login does not replace the original backup with AtomGit-owned state.
- Helper state is stored with restrictive permissions and contains no token.
- Logout returns nonzero on helper restoration failure and can retry residual
  state after the login token has already been cleared.
- Existing offline tests, `python -m compileall -q .`, and `git diff --check`
  pass in the `atomgit_cli` conda environment.

## Required Tests

- Focused offline credential-helper integration script with isolated `HOME`
  and `GIT_CONFIG_GLOBAL`, with the real system config explicitly disabled.
- Existing 12 offline test scripts.
- No live AtomGit request is required for implementation acceptance; the
  previously authorized private-repository evidence remains the live baseline.

## Permissions

- Authorized: local source, test, documentation, and `TASK.md` edits; isolated
  temporary Git configuration; local task branch creation; cohesive commit and
  push of this task branch after self-verification; pull request creation,
  merge into `yuto`, and closure of Issue #13 after successful delivery.
- Not authorized: real global Git/keychain mutation, AtomGit remote writes, tag,
  release, or PyPI.

## Delivery Record

- Regression evidence: `python tests/test_git_credentials_isolation.py`
  failed on the previous implementation because setup could not replace
  existing multi-valued helpers and installed neither a reset nor backup.
- Implementation: setup now stores the original two-host values in a `0600`
  state file without writing the current login token, installs an empty reset
  plus the owned helper,
  preserves the original backup on repeated login, and rolls back partial
  configuration failures. Cleanup transactionally restores the original
  values and includes a legacy owned-helper cleanup path.
- Documentation: README, FAQ, human architecture/testing guidance, and the AI
  architecture specification describe helper isolation and restoration.
- Focused offline test: `python tests/test_git_credentials_isolation.py` passed
  33/33 assertions using temporary HOME/global config and a fake inherited
  helper. The real system config is explicitly disabled. Coverage includes
  repeated setup, lookup/store/erase isolation, exact restoration, partial
  setup failure, failed rollback recovery, cleanup-file failure recovery, and
  CLI logout failure/retry behavior.
- Full offline tests: all 13 `tests/test_*.py` scripts passed with zero
  failures in the `atomgit_cli` conda environment after review fixes.
- Static checks: `python -m compileall -q .` and `git diff --check` passed.
- Credential scan: no real token pattern or `ATOMGIT_TEST_TOKEN` reference was
  found in changed implementation, test, or documentation files.
- Live test: the pre-fix evidence was followed by an authorized post-fix
  private `git ls-remote`. Login,
  private remote read, and logout exited 0; the inherited generic helper
  remained configured but produced no keychain/store diagnostic, and owned
  helper/state files were removed.
- DoD audit: implementation, focused regression, documentation, complete
  offline suite, compileall, diff check, credential scan, and scope checks
  passed. Human acceptance remains pending.
- Independent review: initial verdict `REQUEST CHANGES`. It found that setup
  could discard recovery files after a failed rollback and that cleanup could
  restore managed config after deleting the helper. Both findings were fixed
  with persistent-failure tests. Re-review then found a Unix-only `os.fchmod`
  call in the atomic writer; it was removed while retaining private `mkstemp`
  creation and post-replace `chmod`. The final review checked the complete
  diff, failure paths, test isolation, documentation, live evidence, and
  credential scan; no blocking findings remained. Verdict: `APPROVED`.
- Delivery: commit `581545d` was pushed on the task branch; PR #14 was merged
  into `yuto` as merge commit `429f16a9a45b33b873c019ffcaaf26756ddfac04`.
  Issue #13 was closed after merge. No tag or Release was created.
- Human acceptance: maintainer waived manual acceptance and authorized
  self-accepted commit/push, PR merge, and Issue closure after the recorded
  tests and review.

## Issue #12 Delivery

- Resumable upload statistics exclude only the root `.cache/huggingface`
  metadata subtree; user-created nested `.cache` files remain counted.
- Added `tests/test_resumable_stats.py`; focused/full offline tests, compileall,
  and diff check passed.

## Issue #10 Delivery

- AtomGit currently ignores non-default branch refs; CLI now rejects any
  non-empty revision other than `main` before upload, preventing silent writes
  to the default branch.
- Added `tests/test_revision_rejection.py`; updated revision contract coverage.
- Focused and full offline tests, compileall, and diff check passed.

## Issue #9 Delivery

- AtomGit public repository semantics are not reliable in the observed remote
  service; `create_repo(private=False)` now rejects instead of reporting false
  success. Private creation remains supported and forwards the requested type.
- Added `tests/test_create_visibility.py`; focused/full offline tests,
  compileall, and diff check passed.

## Issue #3 Delivery

- Remote evidence shows AtomGit dataset LFS batch uploads return 404. Dataset
  resumable uploads are now rejected before any remote call with an actionable
  ordinary-upload alternative; existing small-file dataset compatibility is
  preserved.
- Added `tests/test_dataset_lfs_guard.py`; updated resumable contract coverage.
- Full offline tests, compileall, and diff check passed. No live write was
  required because the service limitation was already established remotely.
