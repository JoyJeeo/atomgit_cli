# Current Issue Contract

# Completed Issue FULL-CLI-VALIDATION

Status: `completed`

## Identity

- Local Issue: `FULL-CLI-VALIDATION`
- Title: `Exercise the complete AtomGit CLI command surface`
- Type: `testing`, `cli`, `security`
- Priority: `P1`
- Branch: `codex/full-cli-validation` (local only)
- Base: `yuto` at `c0a8f38`
- Delivery mode: add missing offline command-level regressions, run the full
  isolated and installed-wheel matrix, commit locally, merge into `yuto`, and
  push only `yuto`.

## User Impact And Evidence

Upload, download, repository creation, logout, and wheel entry points have
focused tests, but CLI `login`, `whoami`, and `config-show` lack complete
command-level coverage. A full CLI validation must prove every advertised
command without touching the maintainer's real HOME, Git configuration, or
credentials.

## Scope

In scope: root and subcommand help; version; login success/failure and helper
outcomes; logout; whoami logged-out/success/API-failure behavior; config-show
logged-out/logged-in and Git integration states; existing repo create, upload,
download, validation, credential, packaging, and installed-wheel tests; CLI
coverage documentation.

Out of scope: new CLI features, real AtomGit writes, reuse of the completed
live-write authorization, real global Git mutation, dependency upgrades,
release, or PyPI publication.

## Acceptance Criteria

- Every command listed by `atomgit --help` has a command-level success or
  expected-failure regression, including authentication and state branches.
- Login tests prove the token is never printed and Git-helper setup failures
  remain nonfatal after successful platform authentication.
- Whoami and config-show accurately distinguish logged-out, success, and
  dependency/configuration failure states.
- All tests use fakes plus temporary HOME/Git state and perform no network or
  real credential-helper mutation.
- The complete pytest matrix, isolated wheel build/install smoke, compileall,
  diff check, link check, credential scan, and independent review pass.

## Permissions

- Authorized: local test/documentation/TASK edits, temporary HOME and Git
  configuration, offline builds, local commit, local merge into `yuto`, and
  push of `yuto` only.
- Not authorized: pushing the Issue branch, AtomGit remote writes, changing
  real credentials or Git configuration, merge into `main`, release, or PyPI.

## Delivery Record

- CLI inventory: root help advertises login, logout, whoami, repo/create,
  upload, download, and config-show; root version reports `1.0.5+yuto.1`.
- Added `tests/test_cli_surface.py` with 39 passing command-level assertions:
  every root/subcommand help path, login authentication and helper outcomes,
  logout idempotency, whoami logged-out/success/API-failure states, config-show
  logged-out/logged-in/helper-present/helper-absent/inspection-failure states,
  and token-output absence.
- Existing focused suites continue to cover private model/dataset creation,
  upload file/directory/resumable/options/validation/error paths, public and
  private download selection, logout restoration failures, Git helper
  isolation, and locked dependency signatures.
- Expanded isolated wheel smoke to run all seven top-level commands plus
  `repo create --help` after installation. Wheel build/install, console/module
  entry points, imports, version, 12 help paths, and unchanged repository
  artifacts passed 17/17 checks.
- Full offline verification: `python -m pytest` passed 36/36 isolated scripts;
  `python -m compileall -q .`, `git diff --check`, local-link validation, and
  credential-pattern scanning passed in the `atomgit_cli` conda environment.
- Safety: fakes and temporary HOME/Git state were used throughout. No network,
  real AtomGit write, real credential file read, or real global Git mutation
  occurred. The separately completed live create/upload/download matrix remains
  the remote behavior evidence.
- Finding and fix: full help inspection found that `whoami` was the only command
  without descriptive help. Added `显示当前登录用户` and verified it in source
  and installed-wheel entry points.
- Independent review: initial verdict `REQUEST CHANGES` for the P3 missing
  `whoami` description. After the help text and regression assertion were
  added, re-review found no remaining findings. Final verdict: `APPROVED`.
- Residual evidence: the installed-wheel run used the project Python 3.10 conda
  environment; the declared Python 3.8-3.13 range was not rerun as a full
  interpreter matrix.
- Human acceptance: the maintainer requested full CLI validation and previously
  authorized local Issue commit, local merge into `yuto`, and push of `yuto`
  only under the per-Issue workflow.

# Completed Issue LIVE-REMOTE-ACCEPTANCE-015-019

Status: `completed`

## Identity

- Local Issue: `LIVE-REMOTE-ACCEPTANCE-015-019`
- Title: `Run controlled AtomGit repository acceptance matrix`
- Type: `testing`, `compatibility`, `security`
- Priority: `P1`
- Branch: `codex/live-atomgit-acceptance` (local only)
- Base: `yuto` at `61b4bce`
- Delivery mode: record evidence and any minimal acceptance fix in one local
  Issue branch; after verification, commit locally, merge into `yuto`, and push
  only `yuto`.

## User Impact And Evidence

Offline contracts cover repository-ID normalization, ignore forwarding,
private creation, and token selection, but the remaining roadmap acceptance
requires real AtomGit evidence. The maintainer supplied a dedicated token via
`ATOMGIT_TEST_TOKEN`, model/dataset test repositories, a large-file directory,
and explicit create/upload/download/delete authorization.

## Scope

In scope: controlled live model/dataset repository probes; multi-level logical
repository create/upload/download behavior; isolated ignore-pattern absence;
anonymous public success, anonymous private failure, and authenticated private
success; checksums where files are transferred; cleanup of objects created by
this run; minimal code/test/documentation fixes only if live evidence exposes a
task-bound defect.

Out of scope: non-`main` revision support, release/PyPI operations, unrelated
roadmap work, reading the maintainer's real AtomGit config, or deleting any
repository outside the two fixed test names and failed multi-level probes.

## Authorized Live Resources

- Credential source: process environment variable `ATOMGIT_TEST_TOKEN`; never
  print, persist in the repository, or place it in command arguments.
- Fixed model repository: `weixin_52273949/test_model`; explicitly designated
  disposable for delete/recreate/cleanup in this run.
- Fixed dataset repository: `weixin_52273949/test_datasets`; explicitly
  designated disposable for delete/recreate/cleanup in this run.
- Multi-level logical test names may use a unique run suffix below the
  `weixin_52273949/test_model/` or `weixin_52273949/test_datasets/` prefixes;
  record the normalized physical ID before any write.
- Large-file source directory:
  `/Users/yutaozhang/yuto/codes/atomgit/atomgit_cli/tmp`.
- Explicitly authorized operations: create, upload, download, and cleanup
  deletion for this acceptance run.

## Acceptance Criteria

- Every remote operation records repo type, logical and physical ID, auth mode,
  exit/result status, and observable remote state without exposing credentials.
- A multi-level model or dataset ID has create and upload evidence, or a
  precisely classified service limitation with no false success.
- An ignored sentinel is absent remotely and after download while retained
  control files are present.
- Anonymous public download succeeds; anonymous private download fails; the
  same private content downloads successfully with the supplied token.
- Downloaded content checksums match uploaded content where applicable.
- Both fixed disposable repositories and every other object created by the run
  are cleaned and cleanup is independently verified.
- Offline pytest, compileall, diff check, credential scan, and independent
  review pass before delivery.

## Permissions

- Authorized: isolated local test assets and credential HOME, AtomGit live
  create/upload/download/delete within the resources above, local source/test/
  documentation/TASK edits, local commit, local merge into `yuto`, and push of
  `yuto` only.
- Not authorized: pushing the Issue branch, changing real user credentials or
  Git configuration, deleting unrelated/pre-existing repositories, merge into
  `main`, release, or PyPI publication.

## Delivery Record

- Credential safety: every live process read the dedicated token only from
  `ATOMGIT_TEST_TOKEN`, used an isolated temporary HOME, suppressed raw request
  output, and never read the maintainer's real AtomGit configuration.
- Baseline: the supplied token matched `weixin_52273949`. Both fixed test
  repositories were initially public, empty, and visible through AtomGit's
  dataset metadata route. Random missing-repository controls returned 404.
- Multi-level evidence: logical model and dataset IDs normalized respectively
  to `weixin_52273949-test_model/live-accept-20260804-01` and
  `weixin_52273949-test_datasets/live-accept-20260804-01`. Create and upload
  returned 401/nonzero because the account lacks those physical namespaces;
  both IDs remained 404 on model and dataset routes, so no false success or
  residue occurred.
- Public-create evidence: HF `private=False` returned success but the resulting
  repository was actually private. The client therefore continues to reject
  unverified public creation. A controlled native visibility update supplied a
  genuinely public download sample.
- Path/ignore evidence: CLI directory upload exited 0. Git refs, native
  contents, Hub file listing, and resolve URLs confirmed retained files under
  `acceptance/run-20260804-01`; `*.tmp` and `logs/*` sentinels were absent.
  Anonymous public download exited 0 and its control-file SHA-256 matched.
- Private matrix: anonymous private download exited 1 with no control file;
  authenticated download exited 0 and its SHA-256 matched the upload source.
- Live defect and fix: AtomGit's HF dataset create route returned 401 while its
  shared model route created a writable private AI repository. CLI API and SDK
  creation now map logical dataset requests to that compatible route, matching
  existing dataset upload behavior. Strict API and SDK contract tests require
  the mapped call while preserving the public dataset interface.
- Post-fix live regression: CLI private dataset create exited 0; readiness and
  private state were verified; the first CLI upload exited 0; anonymous
  download exited 1; authenticated download exited 0 with matching SHA-256;
  cleanup returned 204.
- Cleanup: both fixed repositories and both normalized multi-level physical IDs
  ended as 404 on model and dataset Hub routes; fixed repositories also returned
  404 through the native repository API. No remote test object remains.
- Focused offline verification: API create contract 22/22, SDK create contract
  21/21, visibility contract, and locked HF signature contract passed.
- Full offline verification: `python -m pytest` passed 35/35 tests;
  `python -m compileall -q .`, `git diff --check`, and the credential-pattern
  scan passed in the `atomgit_cli` conda environment.
- Large-file rerun was not needed: this Issue's new model/private/ignore/matrix
  evidence used checksum controls, while the existing authorized 399/404 MB
  resumable interruption and recovery evidence remains applicable. The supplied
  `tmp` files were not modified.
- Independent review: initial verdict `REQUEST CHANGES` for a P2 SDK docstring
  placed on `hub_download_url` instead of `create_repository`. The text was
  moved, checks reran, and re-review found no remaining issues. Final verdict:
  `APPROVED`.
- Human acceptance: the maintainer explicitly authorized the named test
  repositories, environment token, create/upload/download/delete operations,
  cleanup, local Issue delivery, merge into `yuto`, and push of `yuto` only.

# Completed Issue BACKLOG-STATE-CLOSEOUT

Status: `completed`

## Identity

- Local Issue: `BACKLOG-STATE-CLOSEOUT`
- Title: `Synchronize development status and remove dead surfaces`
- Type: `documentation`, `testing`, `maintainability`
- Priority: `P2`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `3302b48`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

The roadmap still presents completed local work as wholly pending, testing and
architecture documents retain several pre-fix statements, README says wheel
smoke is absent, and `cli.py` contains a fully commented-out repository-info
command that has no task-owned behavior or tests.

## Scope

In scope: add an evidence-based roadmap status summary; correct remaining
development-line documentation; delete commented dead CLI code; scan links,
markers, generated artifacts, credentials, and final diff; do not rewrite
immutable release notes.

Out of scope: implementing repository info, remote acceptance, Python-version
matrix execution, merging, releasing, and dependency upgrades.

## Acceptance Criteria

- Roadmap clearly distinguishes completed local work from permission-gated
  remote acceptance without renumbering candidate Issues.
- Current documentation has no known stale claims for implemented fixes.
- Commented-out replacement/feature code is absent from CLI source.
- Link, marker, credential, artifact, pytest, compileall, and diff checks pass.

## Permissions

- Authorized: local documentation/dead-code cleanup, read-only audits,
  cohesive commit, and branch push.
- Not authorized: runtime feature work, remote operations, merge, release, or
  PyPI publication.

## Delivery Record

- Roadmap status now distinguishes locally completed work, existing live
  evidence, and acceptance that still requires exact remote-write permission.
- README and architecture/testing guidance now match the automated wheel
  smoke, revision rejection, and remaining remote-test boundaries.
- Removed the fully commented-out and unregistered `repo info` implementation;
  no public command or runtime behavior changed.
- Full offline verification: `python -m pytest` passed 35/35 tests in the
  `atomgit_cli` conda environment; `python -m compileall -q .` and
  `git diff --check` passed.
- Repository audit: local Markdown links resolve, the changed diff contains no
  credential pattern, and no task-unrelated generated artifact was added.
- Independent review: no findings. The complete closeout diff stays within the
  Issue scope and does not overstate live-service evidence. Verdict: `APPROVED`.
- Residual evidence: the declared Python 3.8-3.13 range has not been exercised
  as a full version matrix. Disposable live create/upload/download acceptance
  remains blocked on exact AtomGit credential, repository, operation, and
  cleanup authorization.
- Human acceptance: the user's instruction explicitly authorizes sequential
  development, verification, commit, and push. Merge, release, publication,
  and live AtomGit writes remain unauthorized.

# Completed Issue DEPLOY-TOOLING-SAFETY

Status: `completed`

## Identity

- Local Issue: `DEPLOY-TOOLING-SAFETY`
- Title: `Make deployment tooling conda-explicit and token-safe`
- Type: `distribution`, `security`
- Priority: `P2`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `993a5f7`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

`deploy.sh` uses ambiguous bare `python`/`pip`, uninstalls packages through the
PATH-selected pip, passes the PyPI token as a visible command argument, and
suggests persisting it in shell startup files. These conflict with repository
environment and credential-safety rules.

## Scope

In scope: require an active conda Python for mutating deployment commands; use
`python -m pip/build/twine`; pass twine credentials through process environment;
remove persistence guidance; add offline temporary-directory tests for help,
environment rejection, build, and install command construction.

Out of scope: actual build publication, real installation, release changes,
remote upload, and replacing the legacy shell interface.

## Acceptance Criteria

- Build/install/twine fail clearly without an active conda Python.
- All Python tooling is invoked through `$CONDA_PREFIX/bin/python -m ...`.
- The token is absent from twine command arguments and no documentation
  recommends shell startup persistence.
- Offline fakes prove build/install command construction without changing the
  real environment or repository artifacts.
- Pytest, shell syntax, compileall, and diff checks pass.

## Permissions

- Authorized: local deployment script/tests/docs, temporary fake environments,
  cohesive commit, and branch push.
- Not authorized: actual install/upload/publication, remote operations, merge,
  release, or PyPI publication.

## Delivery Record

- Deployment commands now require `$CONDA_PREFIX/bin/python` and invoke build,
  pip, and twine through `python -m`; help remains available without conda.
- Twine receives credentials through `TWINE_USERNAME`/`TWINE_PASSWORD`, not
  process arguments, and shell-startup token persistence guidance was removed.
- The script changes to its own repository directory before dist cleanup,
  preventing caller-directory deletion.
- Offline temporary fake-environment test passed 13/13 for missing conda,
  install, build, twine, argument/token behavior, and cleanup confinement.
- `bash -n deploy.sh` passed. `python -m pytest` collected and passed 35/35
  cases in 23.27 seconds; compileall and diff checks passed.
- Independent review identified caller-dependent cleanup scope; script-root
  anchoring and a regression were added. Re-review found no blocking token,
  environment, deletion, compatibility, or scope issue. Verdict: `APPROVED`.

# Completed Issue API-REVISION-GUARD

Status: `completed`

## Identity

- Local Issue: `API-REVISION-GUARD`
- Title: `Enforce main-only upload revision at every API boundary`
- Type: `bug`, `cli`, `sdk`, `compatibility`
- Priority: `P1`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `f039a24`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

The Click command and SDK reject non-main revisions, but the exported
`HuggingFaceAPI.upload_folder` and `upload_directory` methods still forward
them directly. Python callers can bypass the safety guard and receive false
success after AtomGit writes to main.

## Scope

In scope: one shared revision-support predicate used by CLI, CLI-facing API,
and SDK upload boundaries; direct API file/directory regression tests; preserve
each layer's existing error contract.

Out of scope: implementing remote branches, download revisions, remote writes,
exception redesign, and dependency upgrades.

## Acceptance Criteria

- Non-main revision is rejected before credentials, temporary resources, or HF
  calls through CLI, API file, API directory, and SDK upload entry points.
- Empty/None/main remain accepted according to each existing interface.
- CLI exits 2, API returns false, and SDK raises `AtomGitUnsupportedError`.
- Pytest, focused tests, compileall, and diff checks pass.

## Permissions

- Authorized: local implementation/tests/docs, cohesive commit, and branch
  push.
- Not authorized: remote operations, merge, release, or PyPI publication.

## Delivery Record

- Added shared `is_supported_upload_revision` and applied it to Click, direct
  API file/directory, and SDK upload boundaries.
- Non-main values now fail before credentials, temporary resources, or HF:
  Click exits 2, API returns false, and SDK raises the backward-compatible
  `AtomGitUnsupportedError`/`ValueError` type.
- Focused direct-boundary test passed 11/11 and existing CLI rejection test
  passed. `python -m pytest` collected and passed 34/34 cases in 22.28 seconds;
  compileall and diff checks passed.
- Independent review found no blocking ordering, compatibility, side-effect,
  output, or scope issue. Remote non-main support remains intentionally
  unavailable until AtomGit service semantics change. Verdict: `APPROVED`.

# Completed Issue DOC-CURRENT-BEHAVIOR

Status: `completed`

## Identity

- Local Issue: `DOC-CURRENT-BEHAVIOR`
- Title: `Align user documentation and tests with current behavior`
- Type: `documentation`, `testing`
- Priority: `P1`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `05e0664`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

README and maintainer documents still advertise non-main revisions, public
creation, and SDK single-file use of a directory-only function, although the
current code rejects or cannot perform those examples. The revision test also
returns before a large retained block of obsolete assertions, so the source
looks covered when it is unreachable.

## Scope

In scope: audit README/docs/current help against implementation; correct
examples and limitations; remove unreachable historical revision test code;
retain current regression coverage; update roadmap status facts without
rewriting immutable release notes.

Out of scope: new runtime behavior, remote acceptance, old tagged release
contents, dependency upgrades, and release publication.

## Acceptance Criteria

- README examples execute against current directory-only SDK upload and
  private-only creation contracts.
- Revision documentation consistently states only main is supported.
- Planned, implemented, and remotely verified behavior remain distinct.
- No unreachable historical test implementation remains.
- Pytest, compileall, document link/reference checks, and diff checks pass.

## Permissions

- Authorized: local documentation/test cleanup, cohesive commit, and branch
  push.
- Not authorized: runtime feature changes, remote operations, merge, release,
  or PyPI publication.

## Delivery Record

- Corrected README upload/create/error/full-workflow examples for directory-
  only SDK upload, private-only creation, dataset type, and main-only revision.
- Updated FAQ, upload analysis, architecture, CLI help, and API docstrings to
  state that non-main revisions are rejected before remote calls and that the
  previously known SDK upload defects are fixed on the development line.
- Deleted unreachable historical forwarding code in
  `tests/test_upload_revision.py`; the dedicated current regression remains
  `tests/test_revision_rejection.py` and passed.
- Local Markdown link audit reported zero missing targets. `python -m pytest`
  passed 33/33, compileall and diff checks passed.
- Independent review found stale CLI help/API docstrings and a README import
  mismatch; all were corrected. Immutable tagged release notes were left
  unchanged. Re-review found no blocking documentation, test, or scope issue.
  Verdict: `APPROVED`.

# Completed Issue ROADMAP-025

Status: `completed`

## Identity

- Planning Issue: `ROADMAP-025`
- Title: `Define stable AtomGit SDK exception contracts`
- Type: `sdk`, `compatibility`
- Priority: `P2`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `2486610`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

SDK functions currently wrap most failures in undifferentiated `Exception`,
often remove `__cause__`, and sometimes include raw dependency messages that
may contain signed URLs. Applications cannot reliably handle authentication,
repository, revision, timeout, or network failures.

## Scope

In scope: public backward-compatible `Exception` subclasses; one sanitized
classifier; apply it to SDK snapshot/file download, upload, create, and dataset
loading; preserve causes; retain existing validation exceptions and `exist_ok`
behavior; add offline tests and SDK documentation.

Out of scope: changing CLI boolean/error contracts, retry policy, remote
operations, dependency upgrades, and a broad API rewrite.

## Acceptance Criteria

- Stable public exception types distinguish auth, not-found, exists, revision,
  timeout, network, unsupported, and fallback SDK failures.
- All remain subclasses of `Exception` and are exported by both import paths.
- Converted failures preserve the original exception as `__cause__`.
- Public messages are actionable and do not echo signed URLs/tokens.
- Validation errors such as bad paths/types/revisions retain their standard
  Python exception types.
- Pytest, focused tests, wheel smoke, compileall, and diff checks pass.

## Permissions

- Authorized: local implementation/tests/SDK docs, cohesive commit, and push
  of the current branch.
- Not authorized: remote operations, real credential/Git changes, merge,
  release, or PyPI publication.

## Delivery Record

- Added public `AtomGitError` subclasses for authentication, repository
  not-found/exists, revision, timeout, network, and unsupported behavior;
  package and standalone SDK imports export the same classes.
- Snapshot/file download, upload, create, and dataset paths now classify and
  chain failures. Sensitive cause messages are redacted before chaining so
  full tracebacks cannot restore signed URLs or token-like content.
- Existing `Exception`, `TimeoutError`, `ConnectionError`, and validation
  `ValueError` catch compatibility is preserved where applicable; create
  `exist_ok` behavior remains unchanged.
- Focused exception suite passed 35/35; download recovery passed 12/12 and
  affected upload/create suites passed. `python -m pytest` collected and
  passed 34/34 cases in 21.34 seconds; compileall and diff checks passed.
- Updated README error examples, product contract, architecture, wheel smoke
  inputs, and module documentation.
- Independent review found a traceback disclosure through raw `__cause__` and
  a broken README import example; both were fixed. Re-review found no blocking
  security, compatibility, exception, packaging, or scope issue. Verdict:
  `APPROVED`.

# Completed Issue ROADMAP-024

Status: `completed`

## Identity

- Planning Issue: `ROADMAP-024`
- Title: `Centralize endpoint and normalization policy`
- Type: `compatibility`, `sdk`
- Priority: `P2`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `13ac77a`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

Normalization is now shared, but `cli.py`, `api.py`, and `atomgit_hub.py`
still duplicate import-time endpoint, XET, cache-directory, and environment
mutation policy. Future changes can drift across CLI/package/standalone SDK
imports.

## Scope

In scope: introduce one idempotent runtime policy module for endpoint/cache
constants and environment setup; use it before HF imports in all entry paths;
preserve current values and standalone compatibility; add offline tests and
update architecture/package smoke inputs.

Out of scope: removing all import-time side effects, changing endpoint/cache
values, dependency upgrades, remote operations, and exception redesign.

## Acceptance Criteria

- Endpoint, XET setting, and cache path have one authoritative definition.
- CLI, API, package SDK, and standalone SDK imports apply identical policy
  before Hugging Face imports.
- Repeated setup is idempotent and cache creation remains supported.
- Wheel smoke proves the new module is packaged.
- Pytest, focused tests, compileall, and diff checks pass.

## Permissions

- Authorized: local implementation/tests/docs, temporary HOME tests, cohesive
  commit, and push of the current branch.
- Not authorized: remote operations, real credential/Git changes, merge,
  release, or PyPI publication.

## Delivery Record

- Added `runtime.py` as the single endpoint, XET, HF cache, and cache-creation
  policy; CLI, API, package SDK, and standalone SDK apply it before HF imports.
- Existing values and import-time behavior are preserved while repeated setup
  is idempotent. The shared multi-level normalization from ROADMAP-007 remains
  the single repository-ID policy.
- Focused runtime test passed 8/8 and wheel smoke passed 9/9, proving the new
  module is packaged and both import surfaces work from the wheel.
- `python -m pytest` collected and passed 33/33 cases in 21.75 seconds;
  `python -m compileall -q .` and `git diff --check` passed.
- Updated AI architecture, human architecture, and README module descriptions.
- Independent review found no blocking import-order, standalone compatibility,
  packaging, state, or scope issue. Removing all import-time mutation remains
  a possible future architecture change, not required here. Verdict:
  `APPROVED`.

# Completed Issue ROADMAP-007

Status: `completed`

## Identity

- Planning Issue: `ROADMAP-007`
- Title: `Unify multi-level repository ID behavior`
- Type: `bug`, `cli`, `sdk`, `compatibility`
- Priority: `P2`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `f56fe4d`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

Validation accepts IDs such as `hf_mirrors/Qwen/repo`, but downloads/SDK
convert them to `hf_mirrors-Qwen/repo` while CLI create/upload pass the
unconverted ID. Anonymous read-only probes on 2026-08-04 returned 404 for the
raw public example and 200 for the converted form, confirming the advertised
mapping without a remote write.

## Scope

In scope: define one shared multi-level normalization helper; apply it to CLI
API create/upload/download and every SDK create/upload/download/URL/dataset
boundary; remove diagnostic printing; add strict offline cross-operation
contract tests and update behavior documentation.

Out of scope: changing two-level IDs, remote writes, renaming existing remote
repositories, endpoint centralization, and dependency upgrades.

## Acceptance Criteria

- One/two-level IDs remain unchanged; three-or-more-level IDs merge only the
  first two components (`a/b/c/d -> a-b/c/d`).
- Create, file upload, directory upload, snapshot/file download, URL creation,
  and dataset loading all use the same normalized ID.
- Normalization emits no CLI/SDK stdout noise.
- Calls continue to bind to HF 1.1.7 signatures and existing tests stay green.
- Pytest, focused scripts, compileall, and diff checks pass.

## Permissions

- Authorized: anonymous read-only evidence, local implementation/tests/docs,
  cohesive commit, and push of the current branch.
- Not authorized: AtomGit remote writes, repository mutation, real credential
  changes, merge, release, or PyPI publication.

## Delivery Record

- Anonymous read-only evidence: the documented raw public multi-level file URL
  returned HTTP 404, while `hf_mirrors-Qwen/...` returned HTTP 200, confirming
  the first-two-components mapping without credentials or mutation.
- Added `utils.normalize_repo_id`; CLI API create/file upload/directory upload/
  download and SDK snapshot/file/upload/create/URL/dataset boundaries now use
  the same silent mapping.
- Focused cross-operation test passed 23/23. `python -m pytest` collected and
  passed 32/32 cases in 22.00 seconds; `python -m compileall -q .` and
  `git diff --check` passed.
- Updated product, AI architecture, human architecture, upload analysis, and
  project vision to distinguish verified read mapping, offline consistency,
  and still-unverified remote writes.
- Independent review found no blocking target-selection, compatibility,
  stdout, documentation, or scope issue. Remote create/upload acceptance
  remains permission-gated. Verdict: `APPROVED`.

# Completed Issue ROADMAP-022

Status: `completed`

## Identity

- Planning Issue: `ROADMAP-022`
- Title: `Add a versioned checksummed installer`
- Type: `distribution`, `security`
- Priority: `P1`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `e5d422f`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

The yuto Release provides wheel and SHA256SUMS assets, but users must download,
verify, and install them manually. There is no safe fixed-version installer,
and a naïve script could silently target system Python or skip integrity
verification.

## Scope

In scope: POSIX installer with fixed/default version selection, exact Release
asset URLs, SHA-256 verification, active-conda detection, `python -m pip`,
temporary cleanup, actionable failures, offline fake-Release tests, and user
documentation.

Out of scope: publishing a new Release asset, PyPI, Windows PowerShell,
automatic conda creation, remote AtomGit operations, and dependency upgrades.

## Acceptance Criteria

- Default and explicit valid versions resolve immutable Release assets.
- Wheel installation occurs only after the exact asset checksum passes.
- Missing conda, downloader, checksum tool, asset, or valid checksum fails
  without invoking pip.
- The installer uses the active conda Python and cleans temporary files.
- Offline tests cover success, corrupt checksum, invalid version, and missing
  conda without network or installation.
- Pytest, shell syntax, compileall, and diff checks pass.

## Permissions

- Authorized: local installer/tests/documentation changes, offline local-file
  simulations, cohesive commit, and push of the current branch.
- Not authorized: Release modification/publication, real package installation
  by the test, remote writes, merge, or PyPI upload.

## Delivery Record

- Added executable `install.sh` with default/explicit version selection,
  immutable GitHub Release asset paths, exact SHA-256 entry verification,
  active-conda Python enforcement, `python -m pip`, and trap-based cleanup.
- Added the installer to the source manifest and documented the curl/local
  invocation, security behavior, and default release.
- Offline local-Release tests passed 14/14, covering default/explicit success,
  exact pip target, corrupt checksum, invalid version, missing conda, and help;
  no real installation or network was used.
- Wheel smoke remained 9/9. `python -m pytest` passed 31/31,
  `sh -n install.sh`, `python -m compileall -q .`, and `git diff --check`
  passed. ShellCheck was not installed and therefore not run.
- Independent review requested source-manifest inclusion and explicit valid
  version success coverage; both were added. Re-review found no blocking
  integrity, environment, cleanup, or scope issue. Verdict: `APPROVED`.

# Completed Issue ROADMAP-014

Status: `completed`

## Identity

- Planning Issue: `ROADMAP-014`
- Title: `Automate wheel installation smoke testing`
- Type: `testing`, `distribution`
- Priority: `P1`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `dcfc810`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

The release wheel was manually verified, but the repository lacks a repeatable
offline test that catches broken package layout, console entry points, module
entry points, or top-level compatibility imports before a future release.

## Scope

In scope: build a wheel from a temporary source copy without isolation/network,
install it into a temporary venv, verify version/help/import contracts, keep
the repository free of artifacts, and integrate it into pytest.

Out of scope: publication, release creation, dependency upgrades, sdist
reproducibility, and live AtomGit operations.

## Acceptance Criteria

- The test builds and installs the current wheel entirely in temporary paths.
- `atomgit --version`, `atomgit --help`, `python -m atomgit --help`,
  `import atomgit`, and `import atomgit_hub` succeed from the installed wheel.
- Reported package/module versions match `1.0.5+yuto.1`.
- No build artifacts appear in the repository.
- Pytest, focused smoke, compileall, and diff checks pass.

## Permissions

- Authorized: local tests/tooling/documentation changes, temporary build and
  venv creation, cohesive commit, and push of the current branch.
- Not authorized: publication, release/tag changes, remote writes, merge, or
  PyPI upload.

## Delivery Record

- Added an offline smoke that copies release inputs to a temporary source,
  builds one wheel without build isolation, installs it without dependencies
  into a temporary venv, and verifies both CLI entry points and imports.
- The import check proves `atomgit` and `atomgit_hub` resolve inside the venv,
  reports version `1.0.5+yuto.1`, and snapshots existing ignored artifact
  state to prove the test does not modify the repository.
- Added Python-3.8-compatible build, wheel, and conditional tomli development
  dependencies. The first focused run exposed missing conda-local tomli; after
  declaring/installing it, final focused smoke passed 9/9.
- `python -m pytest` collected and passed 30/30 cases in 22.11 seconds;
  `python -m compileall -q .` and `git diff --check` passed.
- Independent review requested installed-module provenance verification; it
  was added and re-reviewed with no blocking findings. Verdict: `APPROVED`.

# Completed Issue ROADMAP-012

Status: `completed`

## Identity

- Planning Issue: `ROADMAP-012`
- Title: `Complete repository creation contract tests`
- Type: `testing`, `cli`, `sdk`
- Priority: `P2`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `250bf64`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

Visibility and SDK safety regressions exist, but the complete creation path
lacks strict coverage for both repository types, stored tokens, `exist_ok`,
missing login, invalid names/types, HF failures, and CLI exit codes.

## Scope

In scope: offline strict fakes and Click integration tests for supported
private model/dataset creation and deterministic failure paths across API,
CLI, and existing SDK contracts.

Out of scope: live creation, public semantics changes, repo ID normalization,
new create features, and dependency upgrades.

## Acceptance Criteria

- Valid private model/dataset calls bind to HF 1.1.7 with exact arguments.
- Missing credentials and dependency failures produce failure without false
  success.
- CLI login, repository-name/type validation, privacy, success, and failure
  exit codes are tested.
- Existing CLI visibility and SDK creation suites remain green.
- Pytest, focused scripts, compileall, and diff checks pass.

## Permissions

- Authorized: local tests and affected documentation, cohesive commit, and
  push of the current branch.
- Not authorized: live AtomGit creation, real credential/Git changes, merge,
  release, or PyPI publication.

## Delivery Record

- Added strict API and Click coverage for private model/dataset creation,
  stored token, privacy, `exist_ok`, missing credentials, dependency failure,
  login requirement, invalid names/types, public rejection, and CLI success/
  failure exit codes.
- Focused contract passed 22/22; existing CLI visibility and SDK creation
  suites remained green at 1/1 and 21/21.
- `python -m pytest` collected and passed 29/29 cases in 960.49 seconds;
  `python -m compileall -q .` and `git diff --check` passed.
- Independent review found no blocking strictness, token, type, exit-code,
  compatibility, or scope issue. Live creation/type/privacy evidence remains
  separately authorized work. Verdict: `APPROVED`.

# Completed Issue ROADMAP-011

Status: `completed`

## Identity

- Planning Issue: `ROADMAP-011`
- Title: `Add strict CLI and SDK download contract coverage`
- Type: `testing`, `cli`, `sdk`, `compatibility`
- Priority: `P2`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `49796e3`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

Download interruption recovery is tested, but token selection, CLI directory
and force behavior, SDK argument forwarding, and HF 1.1.7 signature binding
are not. The SDK snapshot wrapper still forwards removed legacy HF arguments
through a compatibility decorator, hiding drift from the real signature.

## Scope

In scope: strict offline download tests for CLI/API/SDK public/private token
selection, local directories, force, revision/pattern options, errors, and
legacy snapshot option handling; stop passing removed options to HF while
preserving public compatibility parameters with warnings when meaningful.

Out of scope: live public/private repositories, multi-level repo ID policy,
new download features, stable exception hierarchy, and dependency upgrades.

## Acceptance Criteria

- Anonymous calls omit tokens and authenticated calls use explicit/stored
  tokens at the correct boundary.
- CLI default/explicit directories and `--force` are observable and tested.
- SDK snapshot/file calls bind to real HF 1.1.7 signatures.
- Removed legacy snapshot options are not forwarded; non-default use warns.
- Deterministic failures remain nonzero/actionable and existing recovery tests
  stay green.
- Pytest, focused scripts, compileall, and diff checks pass.

## Permissions

- Authorized: local implementation, tests, affected documentation, cohesive
  commit, and push of the current branch.
- Not authorized: live AtomGit requests, real credential/Git changes, merge,
  release, or PyPI publication.

## Delivery Record

- Added strict SDK snapshot/file, CLI-facing API, and Click command coverage
  for stored/explicit/anonymous token selection, revision, patterns, local
  directories, force behavior, result propagation, and failure guidance.
- Removed legacy `local_dir_use_symlinks`, `proxies`, and `resume_download`
  from calls into HF 1.1.7 while preserving public compatibility parameters;
  non-default legacy use emits one actionable `FutureWarning`.
- Focused download contract passed 24/24 and interruption recovery remained
  12/12. `python -m pytest` collected and passed 28/28 cases;
  `python -m compileall -q .` and `git diff --check` passed.
- Architecture documentation now describes current legacy-option behavior.
- Independent review found no blocking compatibility, token, path, error, or
  scope issue. Live public/private access remains a separately authorized
  acceptance matrix. Verdict: `APPROVED`.

# Completed Issue ROADMAP-010

Status: `completed`

## Identity

- Planning Issue: `ROADMAP-010`
- Title: `Complete offline login and configuration tests`
- Type: `testing`, `security`
- Priority: `P2`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `498d16f`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

Permission and Git-helper tests exist, but token validation, login persistence,
identity rejection, corrupt JSON recovery, and ordinary logout credential
clearing lack one isolated offline contract suite.

## Scope

In scope: add offline coverage using temporary HOME/config paths and network
fakes for validation, persistence/reload, corrupt config, login failure, and
logout clearing while preserving existing permission/helper tests.

Out of scope: live identity requests, real HOME/Git changes, new login
features, exception redesign, and remote writes.

## Acceptance Criteria

- Short/invalid and identity-failed tokens are not persisted.
- A verified token persists, reloads, and clears without appearing in output.
- Corrupt JSON loads as logged out and can be repaired by a later save.
- CLI logout clears credentials without requiring Git when no helper state
  exists.
- Pytest, focused scripts, compileall, and diff checks pass.

## Permissions

- Authorized: local tests and affected documentation, cohesive commit, and
  push of the current branch.
- Not authorized: live AtomGit requests, real credential/Git changes, merge,
  release, or PyPI publication.

## Delivery Record

- Added an isolated lifecycle test covering fresh state, persistence/reload,
  logout, corrupt JSON recovery, short tokens, identity rejection, verified
  login, output redaction, and CLI logout without Git.
- Focused login/config test passed 11/11 and existing permission coverage
  passed 6/6. `python -m pytest` collected and passed 27/27 cases;
  `python -m compileall -q .` and `git diff --check` passed.
- Documentation now distinguishes complete offline login/config coverage from
  separately authorized live identity verification.
- Independent review found no blocking security, isolation, compatibility, or
  scope issue. No real token, HOME, Git config, or network endpoint was used.
  Verdict: `APPROVED`.

# Completed Issue ROADMAP-009

Status: `completed`

## Identity

- Planning Issue: `ROADMAP-009`
- Title: `Provide a standard isolated pytest suite`
- Type: `testing`
- Priority: `P1`
- Branch: `codex/close-development-backlog`
- Base: previous verified backlog commit `7554857`
- Delivery mode: sequential backlog delivery; cohesive commit and branch push
  are authorized after verification.

## User Impact And Evidence

The repository's self-executing test scripts are not collected by pytest and
several patch process-global objects at import time. Maintainers must run a
custom shell loop, and naïve pytest collection could allow tests to contaminate
one another.

## Scope

In scope: add a Python-3.8-compatible development test dependency, configure
pytest to collect an isolated subprocess matrix, preserve every existing
script and exit assertion, isolate HOME/Git state per case, and document one
standard offline command.

Out of scope: rewriting every legacy assertion into native pytest functions,
behavior changes, remote tests, and dependency upgrades outside test tooling.

## Acceptance Criteria

- `python -m pytest` collects one case for every self-executing test script.
- Each case runs in a separate process with isolated HOME and Git config.
- A failing script exposes captured stdout/stderr and fails pytest.
- The development dependency remains compatible with Python 3.8.
- Pytest, direct-script compatibility, compileall, and diff checks pass.

## Permissions

- Authorized: local test/tooling/documentation changes, installation of the
  declared test dependency in `atomgit_cli`, cohesive commit, and branch push.
- Not authorized: AtomGit remote writes, real credential changes, merge,
  release, or PyPI publication.

## Delivery Record

- Added `requirements-dev.txt` with `pytest>=7.4,<8.4`, preserving Python 3.8
  compatibility, plus explicit pytest configuration and a dynamic subprocess
  matrix for every `tests/test_*.py` script.
- Every case receives an isolated HOME, global Git config path, disabled
  system Git config, separate Python process, captured diagnostics, and a
  bounded timeout. Legacy direct-script execution remains available.
- Installed pytest 8.3.5 in the required conda environment.
- `python -m pytest` collected and passed 26/26 cases in 917.01 seconds.
  `python -m compileall -q .` and `git diff --check` passed.
- Updated AI testing rules, maintainer testing guidance, README, and
  architecture facts to make pytest the standard complete offline command.
- Independent review found no blocking collection, isolation, credential, or
  compatibility issue. The suite reports pytest case counts separately from
  legacy internal assertion totals. Verdict: `APPROVED`.

# Completed Issue ROADMAP-008

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
