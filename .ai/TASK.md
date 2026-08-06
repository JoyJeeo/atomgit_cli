# Current Issue Contract

# Issue CLI-SINGLE-FILE-DOWNLOAD

Status: `completed`

## Identity

- Local Issue: `CLI-SINGLE-FILE-DOWNLOAD`
- Title: `Expose safe single-file repository download in the CLI`
- Type: `cli`, `feature`
- Priority: `P2`
- Branch: `codex/add-download-file-cli` (local only)
- Base: `yuto`
- Previous Issue: `ANONYMOUS-HF-TOKEN-ISOLATION`, delivered by `5203c13`
  and merged by `13f493d`.
- Delivery mode: standing-authorized implementation, review, commit, local merge
  into `yuto`, and push only `yuto`; task branch remains local-only.

## User Impact And Current Behavior

The CLI can download only an entire repository, although the CLI-facing API
already provides the same safe list/resolve implementation for one file. Users
must currently write Python or download every file when they know the exact
repository path.

Expected behavior: `atomgit download-file REPO_ID FILENAME` downloads only the
requested repository file, supports an explicit destination directory,
model/dataset selection, default existing-file skip, and forced replacement.

## Scope

In scope: one root CLI command, repository and destination validation, forwarding
to `api.download_file`, anonymous/private guidance consistent with whole-repo
download, CLI integration tests, root/help coverage, and README/architecture
documentation.

Out of scope: SDK changes, checksum verification, resume, pruning, arbitrary
revision selection, repository management, and changes to the existing transfer
implementation.

## Compatibility Requirements

- Preserve current `atomgit download` behavior and all public Python signatures.
- Reuse the safe target-path, credential-isolation, retry, and atomic replacement
  behavior already enforced by `api.download_file`.
- Preserve Python 3.8+ and locked dependency versions.

## Acceptance Criteria

- Root help advertises `download-file` and command help describes its arguments
  and options.
- Valid calls forward exact repository ID, filename, destination directory,
  force flag, and repository type to `api.download_file`.
- The default destination is the current directory and nested repository paths
  retain their directories below it.
- Invalid repository IDs and file destinations fail before API access.
- API failure exits nonzero and anonymous failure provides login guidance.
- Focused and complete offline tests, compileall, and diff checks pass.
- Independent review has no open P0/P1 findings.

## Permissions And Acceptance

- Authorized: local source/tests/docs/task metadata, task branch, conventional
  commit without `czx:` prefix, local merge into `yuto`, and push only `yuto`.
- Authorized live testing remains limited to read/download operations against
  `weixin_52273949/test_model` and `weixin_52273949/test_datasets`; no remote
  mutation or token output is allowed. A small-file live CLI read may be used.
- Human acceptance: standing acceptance granted for the approved ordered plan.

## Evidence And Closure

- Implementation: root `download-file` command validates repository and local
  directory, creates the destination, reports anonymous mode, and forwards the
  exact file request to the existing safe `api.download_file` path. README and
  architecture documentation now describe the command and its shared policy.
- Regression-before-implementation: `python tests/test_cli_download_file.py`
  failed because root help and command resolution had no `download-file` entry,
  proving the missing CLI surface.
- Focused offline tests: `python tests/test_cli_download_file.py`,
  `python tests/test_cli_surface.py`, `python tests/test_download_contract.py`,
  and `python tests/test_download_path_security.py` passed 15/15, 50/50, 45/45,
  and 15/15 custom checks.
- Complete offline suite: `python -m pytest -q` passed 45/45 isolated script
  cases in 43.90 seconds in the `atomgit_cli` environment.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Live read test: actual `python -m atomgit download-file` calls exited 0 and
  created the requested files from only the authorized model and dataset test
  repositories. Model `ignore_test/config.json` was 77 bytes and dataset
  `sub/中文样本.csv` was 31 bytes; temporary local directories were removed.
- Independent review: no findings. The new command delegates transfer and
  filename containment to the already tested API, rejects invalid repositories
  and non-directory destinations before remote access, preserves exact option
  forwarding, and changes no existing interface. Offline and scoped live
  evidence cover model, dataset, anonymous guidance, nested paths, failure
  exits, and help text. Verdict: `APPROVED`.
- DoD: implementation, focused regression, full suite, documentation, live
  read-only evidence, compileall, and diff checks agree; no credential,
  generated artifact, unrelated edit, or open P0/P1 finding is present.
- Commit/merge/push: authorized; exact references will be reported from Git
  after execution.
