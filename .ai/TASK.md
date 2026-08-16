# Current Issue Contract

Status: `completed`

## Handoff Snapshot

- Updated: `2026-08-16 +0800`
- Phase: `implementation complete; independently reviewed; accepted, committed, merged locally, and ready to push yuto`
- Base branch: `yuto`
- Task branch: `codex/standardize-release-workflow`
- Base commit: `c2dab6337370453117e0d3e3183c967c2f0ce9c2`
- Task commit: `be7956b feat(release): standardize GitHub release workflow`
- Merge commit: `873904a789f83966ff0212053bde8272bc213529 merge: standardize GitHub release workflow`
- Current HEAD: `873904a789f83966ff0212053bde8272bc213529`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `clean after local task commit and merge; this final delivery record is the only pending local documentation commit before push`
- Changed paths: `none after the final delivery-record commit`
- Last completed action: `committed be7956b and merged it into yuto as 873904a`
- Next exact action: `push only yuto to github; do not push the task branch or perform tag/Release/PyPI/AtomGit operations`
- Blockers: `none; the first version number using the new process is intentionally not selected by this Issue`
- Tests run for this phase: `python tests/run_cli_baseline.py passed 73/73 in 58.62s; focused installer/deploy/release/update contracts passed; wheel smoke passed 26/26; compileall, pip check, diff check, shell syntax, locked dependency signatures, package build, and artifact audit passed`
- Required worktree while this uncommitted handoff exists: `/Users/yutaozhang/yuto/codes/atomgit_cli`

## Active Issue

- Remote Issue: `none; local Issue only`
- ID: `LOCAL-STANDARDIZE-RELEASE-WORKFLOW`
- Title: `Standardize GitHub Release, user installation, and updates`
- Primary type: `distribution`
- Secondary types: `release`, `cli`, `documentation`, `compatibility`, `testing`
- Priority: `P1`
- Observable objective: `make yuto releases reproducible and manually authorized through a protected GitHub Actions workflow, install ordinary users only from checksummed immutable GitHub Release wheels, add safe Release-based atomgit update behavior, and document a separate Git/conda/editable source-development path`
- User impact: `users receive one verifiable installation and update channel with predictable version behavior, while developers retain a conventional source checkout that no installer or update command mutates`

## Maintainer Decisions Accepted On 2026-08-16

- `yuto` is the development mainline and the only release branch.
- A local `release/X.Y.Z` preparation branch is retained; it is merged into
  `yuto` before publication and is not pushed.
- New package versions, annotated Git tags, and GitHub Releases use only
  stable `X.Y.Z` identifiers without `v`, `yuto`, `rc`, `beta`, or `dev`
  prefixes/suffixes.
- Historical `v...` tags and Releases remain immutable history. They are not
  deleted, rewritten, or considered by the new latest-version resolver.
- A non-draft, non-prerelease GitHub Release whose tag is exactly `X.Y.Z`
  determines installability. A tag alone is not a completed release.
- GitHub Release is the only official AtomGit CLI publication channel. The
  AtomGit CLI distribution is not published to PyPI.
- Third-party dependencies may be resolved from the user's configured pip
  index, including PyPI or a mirror. This is dependency consumption, not
  publication of AtomGit CLI.
- The only official ordinary-user artifact is the checksummed wheel attached
  to GitHub Release. The sdist and license are audit/archive assets, not the
  default installation path.
- `install.sh` is ordinary-user-only. There is no `--coder`, `--developer`, or
  `--source` mode and no curl-based source checkout.
- Source development is only `git clone`/`git checkout yuto`, an isolated
  conda environment, locked dependencies, and editable installation. Source
  updates use Git, not `atomgit update`.
- Existing wheel users update with `atomgit update`; editable/source installs
  are detected and refused with Git-based instructions instead of having their
  checkout modified.
- The maintainer will manually start the Release workflow in GitHub, inspect
  its checks, and approve a protected release environment. GitHub Actions then
  creates the annotated tag and GitHub Release using its release identity.
- Required real AtomGit operations are separately authorized and never run by
  the Release workflow.

## Starting Evidence And Current Gaps

- Current Git HEAD is `c2dab63` on clean `yuto`, matching `github/yuto` before
  this handoff edit.
- Current package/CLI/install/test version values are duplicated as `1.0.6` in
  `setup.py`, `__init__.py`, `cli.py`, `install.sh`, tests, and documentation.
- Current official installer requires an active conda environment, defaults to
  fixed `1.0.6`, constructs `v$version`, accepts a broader non-SemVer character
  set, and has no latest-Release resolution or target-Python option.
- Current installer already downloads the wheel and `SHA256SUMS`, verifies the
  wheel before pip, cleans its temporary directory, and enables managed Zsh
  completion by default with `--no-completion` and non-fatal setup warnings.
- No public `atomgit update` command exists.
- `deploy.sh` currently supports local build/install plus a real
  `twine upload dist/*` PyPI write path using `atomgitsdktoken`; tests and docs
  still register and advertise that legacy publication path.
- No `.github/workflows` release automation currently exists.
- `docs/release.md`, README, docs index/FAQ/architecture, changelog language,
  and tests still describe `v1.0.6`, conda-only user installation, and/or the
  legacy PyPI distinction.
- Existing packaging evidence is `tests/test_installer.py`,
  `tests/test_deploy_script.py`, `tests/test_wheel_smoke.py`, the exact CLI
  schema/dispatch ledger, and the `PACKAGING`/`PORTABILITY` development-floor
  capabilities.
- Current locked compatibility contracts remain
  `huggingface-hub==1.1.7`, `datasets==4.4.1`, Click `8.4.2`, and Python `>=3.9`.

## Current And Expected Behavior

### Current

- Users must activate conda and run a tag-pinned installer for `v1.0.6`.
- The installer does not discover the latest completed GitHub Release.
- Installing another version still assumes a `v` tag and does not enforce
  exact stable SemVer.
- Installed users have no supported in-product update command.
- Version identity can drift because it is manually repeated in several files.
- Local packaging and the live PyPI upload wrapper share `deploy.sh`.
- Release preparation, approval, artifact construction, tag creation, and
  GitHub Release publication have no executable workflow contract.

### Expected

```text
ordinary user: install.sh -> completed X.Y.Z GitHub Release -> checked wheel
ordinary update: atomgit update -> completed X.Y.Z GitHub Release -> same Python
source developer: git clone -> checkout yuto -> conda -> locked deps -> pip -e
source update: git pull --ff-only -> reinstall deps/editable package as needed
publication: local release/X.Y.Z -> merge yuto -> manual Action -> approval
             -> annotated X.Y.Z tag -> verified draft -> public GitHub Release
```

## Branch, Version, And Release Identity Contract

- `yuto` remains both the GitHub development mainline and the sole branch from
  which releases are made. `main` retains its separate upstream-sync role.
- A release starts from a local `release/X.Y.Z` branch based on an explicitly
  selected `yuto` commit. The branch contains only version, changelog, release
  notes, documentation, tests, and release metadata needed for that release.
- The release branch never contains wheel, sdist, checksums, build directories,
  virtual environments, test output, or GitHub Actions artifacts.
- The accepted release-preparation commit is merged locally into `yuto`; only
  the resulting `yuto` state is eligible for tag and Release creation.
- Stable SemVer rules are: major for incompatible public behavior, minor for
  backward-compatible capability, patch for backward-compatible repair.
- Introduce one authoritative package version source. Build metadata, package
  `__version__`, Click `--version`, tests, installer expectations, and release
  checks must derive from or mechanically verify that source.
- The first version published under this process is not chosen here. Selecting
  it is a later release decision based on the accumulated compatibility scope.
- A published version is immutable: its annotated tag never moves and its
  uploaded asset bytes/checksums are never replaced by different content. A
  product defect requires a new version.

## Historical `v` Transition Contract

- Preserve all historical `v...` tags, Releases, assets, and fixed links.
- The new resolver considers only Releases that are non-draft,
  non-prerelease, and whose tag matches `^[0-9]+\.[0-9]+\.[0-9]+$`.
- Do not treat GitHub's newest tag or a bare tag as a completed release.
- The new installer and first pure-numeric Release must be delivered as one
  cutover. Before that cutover, historical installation instructions remain
  available; after it, the default stable channel ignores legacy `v...`
  Releases while their explicit historical links continue to work.
- If no completed pure-numeric Release exists, the new resolver fails clearly;
  it never falls back to a legacy tag, branch archive, or `yuto` source.

## Ordinary User Installation Contract

### Public commands

```text
install.sh
install.sh --version X.Y.Z
install.sh --python /absolute/path/to/python
install.sh --force-reinstall
install.sh --no-completion
```

- `--version`, `--python`, `--force-reinstall`, and `--no-completion` compose
  where meaningful; help works without a usable target Python.
- Remove/reject `--coder`, `--developer`, and `--source` explicitly if present
  in future input; source installation is never an installer fallback.

### Python selection and destination

- Prefer explicit `--python`; otherwise use the active environment Python when
  it is unambiguous, then a supported `python3` on PATH.
- Ordinary installation does not require conda and does not reject a system
  Python merely for being system-owned.
- The selected interpreter must satisfy Python `>=3.9` and provide pip.
- Never use `sudo`, silently add `--user`, or bypass PEP 668 with
  `--break-system-packages`. If the target cannot be written safely, fail with
  venv/conda/explicit-`--python` guidance.
- The wheel installs into the selected interpreter's site-packages and its
  `atomgit` entry point installs into that interpreter's scripts directory.
  Report the interpreter, package location, command path, PATH visibility, and
  installed version.

### Resolution, download, and validation

- Default installation resolves the highest completed pure-numeric GitHub
  Release, not the latest Git tag and not a mutable branch artifact.
- Explicit `--version` accepts only exact `X.Y.Z` and resolves that completed
  Release, including an intentional older version.
- Parse GitHub Release JSON with a structured parser (Python standard library
  is sufficient); do not parse JSON with grep/sed/regular expressions and do
  not require `jq` merely for installation.
- Download only the expected universal wheel and `SHA256SUMS` into a unique
  `mktemp` directory. The temporary directory is removed on success, failure,
  signal, and validation rejection.
- Require exactly one valid checksum entry for the expected wheel. Reject
  missing Release, missing wheel, missing checksum file, duplicate/ambiguous
  checksum entries, malformed checksum, name mismatch, digest mismatch,
  redirects to disallowed origins, oversized metadata/checksum responses, and
  wheel metadata whose distribution/version does not equal `atomgit==X.Y.Z`.
- Do not invoke pip until Release identity, asset identity, checksum, and wheel
  metadata validation have all succeeded.
- Pip may resolve declared third-party dependencies from the user's configured
  index. The installer must not hard-code official PyPI or claim those
  dependency downloads are AtomGit publication.
- After pip succeeds, verify with the exact target interpreter: distribution
  version, `atomgit --version`, `python -m atomgit --help`, `import atomgit`,
  and `import atomgit_hub`. Installation is not successful until verification
  passes.
- Preserve current Zsh completion behavior: official installation enables the
  AtomGit-owned completion by default for Zsh, `--no-completion` opts out, and
  a completion setup failure is a visible non-fatal warning only after package
  installation itself has fully verified.

### Platform boundary

- `install.sh` remains the POSIX/macOS/Linux bootstrap. Do not claim it is a
  native Windows shell installer.
- The wheel and `atomgit update` remain cross-platform. README must give
  Windows users a checksummed fixed-Release wheel procedure using an explicit
  supported Python; a PowerShell installer is out of scope for this Issue.

## `atomgit update` Contract

### Public CLI

```text
atomgit update
atomgit update --version X.Y.Z
atomgit update --force-reinstall
atomgit update --version X.Y.Z --force-reinstall
```

- Add `update` to the exact Click schema, leaf-dispatch ledger, Zsh completion,
  installed-wheel help smoke, human CLI documentation, and development floor.
- Update always targets the interpreter running the command (`sys.executable`)
  and never guesses or switches to a different Python environment.
- A source/editable installation is detected through packaging provenance and
  source location. It is refused without any Git mutation and prints the exact
  `git checkout yuto`, `git pull --ff-only`, dependency, and editable reinstall
  guidance.

### Version decisions

- With no `--version`, resolve the highest completed pure-numeric Release.
- If target equals installed version, skip without pip by default.
- `--force-reinstall` permits a checksum-verified reinstall of the same target.
- If the latest completed Release is lower than the installed stable version,
  refuse implicit downgrade.
- Explicit `--version` permits an intentional upgrade or downgrade.
- Missing Release, wheel, or checksum stops. No failure ever falls back to
  `yuto`, a branch archive, source checkout, PyPI AtomGit, or an older release.
- Apply the same Release, checksum, metadata, redirect, response-bound, and
  pre-pip validation rules as first installation. Centralize the Python
  release-resolution/install core so installer and updater cannot drift; the
  shell bootstrap should only select/validate Python and invoke that core.

### Verification and recovery

- Before mutation, record the installed version, interpreter, command path,
  and immutable old Release recovery URL/command without recording credentials
  or signed URLs.
- After pip, launch fresh subprocess verification for distribution identity,
  CLI version/help, module entry point, and both imports. The running updater
  must not claim its already-imported module state proves the new install.
- A verification failure returns nonzero, states that the update failed, and
  prints an exact recovery command using the same interpreter, old `X.Y.Z`,
  and `--force-reinstall`.
- Best-effort recovery guidance is guaranteed; atomic restoration of arbitrary
  third-party dependency state in every system Python is explicitly not
  guaranteed. Recommend isolated venv/conda and fixed versions for production.
- Preserve completion state rather than silently opting users in or out during
  update. If an AtomGit-owned managed Zsh completion is already installed,
  refresh it idempotently after package verification; otherwise leave startup
  files unchanged.

## Source Development Contract

- Source development is not an install-script mode and does not create an
  installer-managed checkout.
- README and `docs/development.md` must provide a complete copy-paste path:

```text
git clone https://github.com/JoyJeeo/atomgit_cli.git
cd atomgit_cli
git checkout yuto
create/activate isolated atomgit_cli conda environment
install locked runtime and development/test dependencies
python -m pip install -e .
verify which atomgit, version/help, python -m entry, and both imports
run focused tests and python tests/run_cli_baseline.py as appropriate
```

- Document the exact supported Python range, why development requires an
  isolated conda environment, locked HF/datasets/Click versions, editable
  installation semantics, PATH/environment troubleshooting, focused and full
  test commands, local build/smoke commands, and how to avoid mixing a Release
  wheel and editable source in one Python environment.
- Source updates are explicitly:

```text
git checkout yuto
git status (must understand/preserve local changes)
git pull --ff-only
activate atomgit_cli conda
reinstall changed locked requirements as needed
python -m pip install -e .
rerun entry/import checks and affected tests
```

- `atomgit update` never runs `git pull`, reset, checkout, stash, merge, rebase,
  or any other Git mutation for a source/editable install.

## GitHub Actions Release Contract

### Trigger and authority

- Add a manually triggered `workflow_dispatch` Release workflow on `yuto`.
- Required inputs are exact `version` (`X.Y.Z`) and full `expected_sha`.
- The maintainer opens GitHub Actions, selects the Release workflow and
  `yuto`, enters both inputs, reviews pre-publish results, and approves a
  protected `release` Environment.
- Before the protected approval, jobs have read-only repository permissions and
  may create only temporary GitHub Actions artifacts.
- The publish job alone receives minimal `contents: write`; no PyPI token,
  AtomGit credential, or unrelated secret is present.
- Use workflow concurrency to prevent overlapping releases. Pin third-party
  Actions to reviewed immutable commit SHAs and pass user inputs through
  validated environment variables rather than shell interpolation.

### Pre-approval validation and build

- Revalidate that `expected_sha` is the intended committed `yuto` release
  state and that code/CLI/docs/changelog/tests agree with `version`.
- Confirm the version is a valid stable SemVer, is ordered above the latest
  completed pure-numeric Release, and has no conflicting tag or Release.
- Run the complete offline baseline, compileall, pip check, diff check, locked
  dependency signature checks, packaging checks, credential/artifact audit,
  wheel and sdist builds, and clean-environment CLI/SDK smoke tests.
- Build from the exact expected SHA in a clean runner; never upload local
  workstation `dist/` contents.
- Produce only `atomgit-X.Y.Z-py3-none-any.whl`, the matching sdist,
  `LICENSE`, release notes, and `SHA256SUMS`. Checksums cover every uploaded
  immutable asset except the checksum file itself.
- Store candidates as temporary Actions artifacts for maintainer inspection.

### Approval, tag, draft, verification, publication

- After explicit protected-environment approval, recheck version/SHA identity,
  absence or safe resumability of tag/Release, and candidate checksums.
- GitHub Actions creates an annotated `X.Y.Z` tag pointing exactly to
  `expected_sha` using its configured release identity. It never creates or
  moves a `vX.Y.Z` tag.
- Create a draft, non-prerelease GitHub Release first. Upload assets, download
  them back through GitHub, revalidate checksums, and install the uploaded wheel
  in a new supported Python environment.
- Verify distribution version, CLI version/help, module help, both imports, and
  expected Release asset inventory before changing the draft to public.
- Only the final transition to non-draft makes the version installable by the
  default installer/updater.

### Partial-failure recovery

- If a workflow fails before tag creation, rerun after fixing the workflow or
  release-preparation state; no public identity exists.
- If the annotated tag exists, a rerun may reuse it only when it resolves to
  the exact `expected_sha`; it is never moved or recreated at another commit.
- If a draft Release or matching assets already exist, a rerun may resume only
  after proving every existing byte/checksum matches. Never overwrite a
  mismatched asset under the same version.
- A failed upload/verification leaves the Release draft and therefore absent
  from the stable resolver. Infrastructure failure may be retried against the
  same tag/SHA. A source/product defect after tag creation requires a new
  version rather than tag movement.
- If final public verification ever fails after publication, report failure
  without deleting/moving history; stop default promotion decisions and prepare
  a corrective version under explicit maintainer direction.

## PyPI And Local Build Contract

- Remove AtomGit CLI's live `deploy.sh twine` publication path, token interface,
  tests, and user documentation from the official repository workflow.
- Retain safe local build and local artifact-install helpers only when they add
  value beyond the new release-check/build scripts; they remain conda-explicit
  developer tooling.
- `python -m build` remains the standard wheel/sdist builder.
- README must not present `python -m pip install atomgit` as installation of
  this repository. If historical upstream PyPI context is retained, label it
  unambiguously as non-official history rather than a current alternative.
- This decision does not block pip from downloading third-party dependencies
  from the user's configured PyPI/mirror.

## Affected Call Paths

```text
install.sh -> select target Python -> Release resolver -> GitHub Release JSON
           -> bounded asset download -> checksum + wheel metadata validation
           -> target Python -m pip -> fresh CLI/SDK verification -> completion

atomgit update -> installation provenance -> Release resolver/version policy
               -> same validated install core with sys.executable
               -> fresh verification -> completion-state preservation/recovery

release/X.Y.Z -> merge yuto -> workflow_dispatch(version, expected_sha)
              -> clean checks/build -> protected approval -> annotated tag
              -> draft Release/upload/readback/install -> publish Release

source developer -> git clone/checkout yuto -> conda -> locked dependencies
                 -> pip install -e . -> Git-managed pull --ff-only updates
```

## Affected Capability IDs

- `FLOOR-REGISTRY`: register the new release/update invariants and every new
  focused test in the monotonic ledger and complete baseline.
- `CLI-SURFACE`: add the public `update` command/options and installed help.
- `CLI-DISPATCH`: cover update success, skip, refusal, and failure dispatch.
- `PACKAGING`: migrate version identity, installer, local build tooling,
  Release assets, checksums, and GitHub Actions publication.
- `PORTABILITY`: preserve Python 3.9+ and Windows wheel/update behavior while
  documenting the POSIX-only shell bootstrap.
- `DEPENDENCY-CONTRACT`: preserve locked runtime dependency compatibility and
  distinguish dependency-index use from project publication.
- `RUNTIME`: ensure installer/update version/help/import verification does not
  violate endpoint-before-HF-import ordering or persist runtime side effects.

## Protected Existing Invariants

- `CLI-001`, `CLI-002`, `DISPATCH-001`, and `DISPATCH-002`: every existing
  command and parameter remains exact while update is added monotonically.
- `CLI-003` and `RUNTIME-003`: completion remains lightweight, offline, and
  independent of credentials/business imports.
- `RUNTIME-001`: real package imports still configure AtomGit/HF runtime policy
  before HF imports.
- `DEP-001` and `DEP-002`: locked dependency versions/signatures remain real.
- `PKG-001`: the wheel continues to install both CLI entry paths and both
  imports without mutating repository artifacts.
- `PKG-003`: official Zsh completion remains default, optional, idempotent, and
  non-fatal only after successful verified package installation.
- `PORT-001` and `PORT-002`: Python 3.9+ and platform safety remain covered.
- Existing credentials, Git helper, upload, download, repository, SDK, error
  redaction, and user-state invariants are unaffected and must remain green in
  the complete baseline.

## New Or Changed Invariants

- Replace `PKG-002` with explicit executable invariants for single-source
  stable version identity, pure-numeric completed-Release selection,
  pre-pip checksum/metadata validation, arbitrary supported target Python,
  stable update policy, source-install refusal, and manually approved
  reproducible GitHub Release publication.
- Add an update-specific invariant under `CLI-SURFACE`/`CLI-DISPATCH` or a new
  stable capability if ledger design shows update has independent ownership.
- Add packaging invariants proving legacy `v...` history is ignored by the new
  default resolver without deletion and that absence never falls back to source.
- Add release-safety invariants proving the workflow is manual, protected,
  least-privilege, annotated-tagged, draft-before-verify, resumable only for
  byte-identical partial state, and contains no PyPI or AtomGit secret path.
- Add portability evidence for venv/conda/explicit Python, PEP 668 refusal,
  POSIX installer scope, Windows wheel/update support, and PATH reporting.
- Ledger counts may only increase unless the authorized `PKG-002` migration
  records its replacement history explicitly; no unrelated invariant is retired.

## Scope

### In scope

- Establish a single authoritative stable version source and consistency gate.
- Implement completed pure-numeric GitHub Release discovery and exact-version
  selection with structured JSON parsing and bounded safe downloads.
- Refactor `install.sh` into ordinary-user-only Release-wheel installation for
  supported target Python without a conda-only requirement.
- Add `--python`, `--force-reinstall`, strict `X.Y.Z`, post-install verification,
  path reporting, recovery guidance, and retained completion behavior.
- Add cross-platform `atomgit update` with the accepted version decisions,
  current-interpreter targeting, source/editable refusal, verification, and
  recovery output.
- Centralize the Python Release/version/download/check/install policy used by
  installer and updater, keeping shell behavior minimal and contract-tested.
- Remove the official PyPI upload path while preserving third-party dependency
  resolution through configured pip indexes.
- Add local release checks and a protected manually triggered GitHub Actions
  release workflow with partial-failure recovery.
- Add focused offline tests, update the exact CLI and development-floor ledgers,
  and comprehensively update README/release/development/architecture/FAQ/index
  documentation and examples.
- Document Windows manual fixed-wheel installation without adding PowerShell.

### Out of scope

- No version is selected or published as part of implementation acceptance.
- No tag, GitHub Release, PyPI publication, workflow publish execution, or
  external release asset upload is performed.
- No `--coder`, `--developer`, `--source`, curl-based source install, managed
  source checkout, self-modifying Git source update, PowerShell installer,
  auto-update daemon, background update, or automatic rollback guarantee.
- No dependency upgrade, package rename, CLI/SDK removal, unrelated refactor,
  upstream merge, remote Issue creation/transition, or live AtomGit operation.
- No real token, credential config, Git helper, shell startup file, user Python
  environment, or existing Git checkout is mutated during tests.

## Compatibility Requirements

- Preserve Python `>=3.9`, Click `8.4.2`, `huggingface-hub==1.1.7`, and
  `datasets==4.4.1` until a separate dependency-policy Issue changes them.
- Preserve distribution name `atomgit`, console entry `atomgit`,
  `python -m atomgit`, `import atomgit`, and `import atomgit_hub`.
- Preserve existing public CLI/SDK behavior except the explicitly authorized
  addition of `atomgit update` and migration away from the legacy PyPI release
  command/documentation.
- Preserve installer Zsh-completion semantics and all credential/error redaction.
- All tests use isolated HOME/config/PATH/Python/Release mirrors and forbid real
  network, pip environment mutation, GitHub writes, AtomGit writes, and startup
  file changes unless an exact later authorization says otherwise.

## Focused Tests And Evidence

- Add a version-contract test that fails on current duplicated/drifting version
  values and validates strict stable SemVer plus historical `v` exclusion.
- Replace/extend `tests/test_installer.py` with offline fake GitHub Release JSON,
  local assets, multiple Python targets, venv/conda/system-like cases, PEP 668
  refusal, latest/explicit selection, force reinstall, completion behavior,
  every missing/malformed/oversized/redirect/checksum/metadata failure, no-pip
  before validation, cleanup, path reporting, and post-install verification.
- Add a focused update test covering CLI schema/dispatch, latest/equal/newer/
  lower/explicit-downgrade decisions, force reinstall, `sys.executable`, source
  refusal, shared validation, fresh verification, recovery output, completion
  preservation, and credential-safe failures.
- Replace/extend deploy tests to prove local build confinement and absence of a
  live PyPI/twine/token path.
- Extend wheel smoke to cover single-source version, installed update help and
  provenance behavior, both entry points/imports, no source checkout mutation,
  and repository-artifact cleanliness.
- Add a release-workflow contract test for `workflow_dispatch`, validated
  inputs, read-only preapproval permissions, protected environment, minimal
  publish permissions, pinned Actions, concurrency, exact SHA/tag behavior,
  draft verification, immutable/resumable state, asset allowlist/checksums, and
  absence of PyPI/AtomGit secrets or automatic live operations.
- Register every new test exactly once in `tests/cli_baseline_contract.py` and
  map it to every affected development-floor capability/invariant.
- Demonstrate focused failure on the pre-change repository before implementation.
- Inspect real locked dependency and packaging signatures rather than relying
  on permissive fakes.

## Acceptance Criteria

1. All package, CLI, test, installer, documentation, and workflow checks use
   one stable `X.Y.Z` version authority with no unnoticed drift.
2. Historical `v...` releases remain untouched but cannot win new latest
   selection; a tag without a completed matching Release is never installable.
3. Ordinary users can install latest or explicit completed Release wheel using
   a supported explicit/active/PATH Python without a mandatory conda check.
4. Release, asset, checksum, response, redirect, and wheel identity failures
   stop before pip and never fall back to source, branch archives, or PyPI
   AtomGit; temporary content is always cleaned.
5. Install success is reported only after fresh target-interpreter CLI/module/
   import verification, with clear Python/package/command/PATH output and
   preserved completion behavior.
6. `atomgit update` correctly skips equal versions, force-reinstalls when asked,
   upgrades latest, refuses implicit downgrade, permits explicit downgrade,
   uses `sys.executable`, and shares the same validation policy.
7. Editable/source installations are never modified by update and receive
   complete Git/conda/editable reinstall guidance.
8. Failed update verification is nonzero and provides an exact old-version
   recovery command without claiming universal atomic dependency rollback.
9. README clearly separates ordinary Release installation/update from detailed
   `git clone yuto` + isolated conda + locked dependencies + editable source
   development/update, including Windows and environment-mixing limitations.
10. The release workflow runs only by manual dispatch, builds the exact yuto
    SHA in a clean runner, pauses for protected approval, creates an annotated
    pure-numeric tag with Actions identity, verifies a draft Release, and only
    then publishes it.
11. Partial workflow reruns never move tags or overwrite mismatched assets;
    incomplete drafts stay outside the stable resolver.
12. GitHub Release is the sole AtomGit CLI publication channel; the live
    PyPI/twine/token path is absent while dependency installation from user
    indexes remains supported and accurately documented.
13. Focused tests, affected regressions, wheel smoke, exact schema/dispatch,
    development-floor ledger, complete baseline, compileall, pip check, diff
    check, dependency signatures, credential/artifact audit, and independent
    review all pass with no open P0/P1 findings.
14. No actual version publication, tag, Release, PyPI upload, live AtomGit write,
    real environment installation, or user checkout/startup-file mutation occurs
    during implementation acceptance.

## Complete Baseline Evidence

- Mandatory final gate: `python tests/run_cli_baseline.py` in the
  `atomgit_cli` conda environment after the last implementation or review fix.
- Supporting mandatory checks: `python -m compileall -q .`,
  `python -m pip check`, `git diff --check`, locked Click/HF/datasets and
  packaging signature inspection, credential/generated-artifact audit, wheel
  plus sdist build in temporary storage, and isolated installed-artifact smoke.
- Current state: `python tests/run_cli_baseline.py passed 73/73 in 58.62s after the final documentation sync`.
- Controlled remote evidence: `not required for implementation because this
  Issue must not publish or change AtomGit remote behavior; the future first
  real release requires a separate explicit authorization and release record`.

## Implementation Sequence

1. Recover this contract against real Git/source/tests/docs and create the local
   task branch from `yuto` if the recorded base remains valid.
2. Add focused failing version, installer, update, deploy, workflow, schema, and
   development-floor contracts without weakening existing evidence.
3. Introduce the single version authority and shared Python Release/install core.
4. Implement strict latest/explicit Release resolution, bounded downloads,
   checksum/wheel validation, target-Python installation, verification, and
   completion preservation in the ordinary-user installer.
5. Add the public update command and source/editable refusal.
6. Replace the PyPI publication wrapper with safe local build/release-check
   tooling and implement the manual protected GitHub Actions workflow.
7. Update README and all affected human/AI documentation, including the complete
   source-development path and historical transition.
8. Run focused and affected tests, then the complete baseline and packaging
   gates; audit final diff and artifacts.
9. Perform mandatory independent review, resolve every accepted finding, rerun
   all affected and complete checks, and update this handoff.
10. Stop for human acceptance and separate delivery authorization. Do not tag,
    publish, or execute the release workflow as implementation verification.

## Residual Risks To Review Explicitly

- Arbitrary system Python and PEP 668 behavior varies by platform/vendor; the
  installer can fail safely but cannot guarantee write access or universal
  dependency rollback.
- An unauthenticated GitHub API resolver is subject to rate limits and transient
  network failures; these must be bounded and actionable without unsafe fallback.
- POSIX `install.sh` cannot be presented as native Windows support; Windows
  relies on the cross-platform wheel/update path and documented manual bootstrap.
- `atomgit update` replaces the package containing the running command; only a
  fresh subprocess can validate the new installation.
- GitHub Actions can fail after annotated tag creation. Draft-first publication
  and exact-SHA/byte-identical reruns prevent an incomplete version from becoming
  latest but do not make published history mutable.
- The first pure-numeric release is a channel cutover; timing and documentation
  must avoid exposing the new default installer before a matching completed
  Release exists.
- Removing the legacy PyPI wrapper is an intentional distribution-policy
  migration; review must ensure no current official GitHub build capability is
  accidentally removed with it.

## Verification And Delivery Permissions

- Authorized now: `activate this local Issue; create a local task branch from
  yuto; edit required source, tests, workflows, installer, build helpers, AI
  documents, and human documentation; create only temporary local build
  artifacts; run offline tests/checks; perform independent review; update
  TASK.md handoffs`.
- Not yet authorized: `delivery commit, push, PR, merge, remote Issue creation
  or transition, annotated tag creation, GitHub Release creation/publication,
  execution of the publish workflow, PyPI/TestPyPI upload, live AtomGit
  operation, real credential access, real user-environment install/update,
  shell startup-file mutation, upstream sync, deletion, or cleanup`.
- Human acceptance: `accepted by the maintainer on 2026-08-17 through the
  explicit request to continue development, complete validation, commit, and
  push; this authorizes local delivery commit, merge into yuto, and push only
  yuto. It does not authorize tag, Release, PyPI, or live AtomGit operations`.
- Delivery mode when later authorized: `local task branch, mandatory tests and
  independent review, human acceptance, local merge into yuto, push only yuto;
  an actual version/tag/Release requires a separate release authorization and
  protected-workflow approval`.

## Review Record

- Design review: `accepted by the maintainer through the 2026-08-16 discussion`.
- Implementation review: `APPROVED after independent read-only review; review
  rounds found and fixed asset redirect/size handling, managed completion
  refresh, exact tag/asset immutability, wheel smoke version-source coverage,
  and partial workflow recovery when a tag exists before its draft Release`.
- Open findings: `none; residual risks are bounded GitHub API rate limits,
  platform-specific PEP 668/write behavior, and the documented limitation that
  arbitrary third-party dependency rollback is not atomic`.
