# AtomGit CLI Development Rules

## Task Model

- One active task must represent one independently verifiable outcome.
- A task may touch multiple modules when the behavior crosses a real boundary,
  such as `cli.py -> api.py`, but unrelated refactoring is prohibited.
- Roadmap entries are not active work. Only an explicit user request or an
  approved active `TASK.md` authorizes implementation.
- Define acceptance criteria before editing. If the intended remote behavior is
  unknown, the task must include investigation or an opt-in live test rather
  than guessing.
- Exactly one Issue may have `Status: active` in `TASK.md`. Candidate roadmap
  entries and review follow-ups remain separate until explicitly selected.
- Do not create a remote GitHub Issue merely because a roadmap entry exists.

## Issue Types

Use the smallest applicable primary type:

- `bug`: demonstrated incorrect behavior;
- `compatibility`: HF Hub, datasets, Python, OS, or packaging compatibility;
- `testing`: missing or unreliable automated verification;
- `cli`: Click parsing, output, command behavior, or exit codes;
- `sdk`: native `AtomGitClient` or public legacy `atomgit_hub` behavior and API
  contracts;
- `security`: token, configuration, credential helper, or user-state safety;
- `distribution`: installation, version identity, wheel, or release artifact;
- `documentation`: user or maintainer documentation only;
- `upstream-sync`: controlled `atomgit/main -> main -> yuto` integration;
- `release`: an explicitly authorized version release.

Labels help triage but do not define scope. Scope and acceptance criteria in
the Issue contract remain authoritative.

## Change Contents

Every behavior change includes, as applicable:

- implementation;
- regression or contract tests;
- user documentation for externally visible behavior;
- SDK documentation for public Python API changes;
- release notes only when a release process or changelog exists and the change
  is intended for release.

Do not mechanically edit README, examples, and every document for an internal
refactor with no external effect. Update the smallest authoritative document.

## Development Floor Impact

Before editing, every active Issue must contain these explicit sections:

- `Affected Capability IDs`;
- `Protected Existing Invariants`;
- `New Or Changed Invariants`;
- focused tests and required evidence categories;
- complete-baseline evidence and residual risks.

New behavior must update `tests/development_floor_contract.py`, add or update a
focused executable regression, and update the smallest authoritative document.
Every new `test_*.py` must join both the exact test inventory and at least one
capability mapping. Internal-only and documentation work still identifies the
affected capability, including `FLOOR-REGISTRY` when only the gate changes.

Do not delete, skip, weaken, or relabel a test or invariant to accommodate an
unintended regression. An intentional compatibility migration requires the
maintainer's explicit authorization, old and new behavior, affected IDs,
replacement evidence, documentation, independent review, and a final passing
complete baseline.

## Maintainability

- Do not leave taskless TODOs, commented-out replacement implementations, dead
  code, or duplicate helpers.
- Do not create empty source trees or placeholder modules to reserve a future
  architecture. New files must have an immediate task-owned responsibility.
- Reuse code only when the shared contract is genuinely the same. Do not force
  CLI output concerns into SDK code merely to remove duplication.
- Preserve Python 3.9 compatibility as required by the locked dependencies.
- Validate all Hugging Face calls against the locked dependency, not memory or
  current online documentation.

## Phased Implementation And Verification

- One development Issue may deliver one complete feature, but implementation
  must be divided into explicit, independently verifiable phases. A phase is a
  delivery checkpoint within the same Issue, not an untracked half-feature or
  a new parallel Issue.
- Each phase must have a concrete boundary, focused tests, and an observable
  entry and exit condition recorded in the active Issue. Implement only the
  current phase, run its focused tests immediately, and proceed automatically
  to the next phase only after those tests pass.
- Do not implement the entire feature first and postpone all testing until the
  end. A failed phase gate returns the Issue to that phase for repair; later
  phases must not conceal or work around the failure.
- The phase gates do not normally require a separate user approval. Pause and
  report only when a test exposes a blocker, the approved scope or contract
  must change, new authority is required, or an external operation needs
  explicit authorization.
- After all phase gates pass, run the mandatory complete offline baseline and
  the applicable compile, dependency, diff, security, packaging, portability,
  and controlled-remote checks before declaring the Issue complete.
- The active Issue handoff must record the current phase, the last focused test
  result, the next exact phase action, and any blocker whenever work pauses or
  crosses a conversation boundary.

## Git Discipline

- Start substantial work from `yuto`, normally on a focused task branch.
- Keep commits cohesive: one issue or one inseparable behavior change per
  commit. A commit may include its tests and documentation.
- Do not mix upstream synchronization, dependency upgrades, formatting sweeps,
  and feature work in one commit.
- Never push, merge, tag, publish, amend, or rewrite history without explicit
  authorization.
- Preserve user changes in a dirty worktree.

Two delivery modes are valid:

- Local acceptance: implementation -> review -> fixes -> final tests -> human
  acceptance -> authorized local commit.
- Pull request: implementation -> authorized local commit -> authorized push
  and PR -> review -> fix commits -> CI -> human acceptance -> authorized
  merge.

Do not require human acceptance before the first commit in PR mode, because a
remote PR needs commits. The active task must state which mode applies.

## Remote And Credential Safety

- Offline tests are the default.
- Live repository creation, upload, push, delete, privacy changes, and release
  publication require explicit authorization for the exact action.
- Never use a user's production or personal repository as disposable test data.
- Never read or display a real token during tests or review.
- Git credential-helper tests must isolate `HOME` and Git config unless the user
  explicitly requests a real integration change.

## Documentation-Only Tasks

When the task is documentation-only:

- do not modify Python source, tests, dependencies, packaging, or runtime state;
- verify claims against source and locked dependency signatures;
- distinguish implemented, advertised, verified, broken, and planned behavior;
- run document consistency checks and `git diff --check`;
- do not run live operations merely to enrich documentation.
