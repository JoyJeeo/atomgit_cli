# Issue-Driven AI Development Workflow

## Team Roles

- Human maintainer: selects Issues, grants permissions, performs product
  acceptance, and authorizes commit, push, PR, merge, close, and release.
- AI Tech Lead: prepares the Issue contract, keeps scope coherent, verifies
  evidence, coordinates implementation and review, and reports status.
- AI implementer: changes only the active Issue, adds tests, and records
  technical decisions and evidence.
- AI reviewer: assumes it did not write the change, reports findings without
  editing, and returns `APPROVED` or `REQUEST CHANGES`.

The same AI session may perform multiple roles only through explicit phase
changes. Reviewer reasoning must start from the diff and evidence, not memory of
implementation intent.

## Lifecycle

```text
Evidence / user request / approved GitHub Issue
                    |
                    v
             Activate TASK.md
                    |
                    v
       Create task branch from yuto if needed
                    |
                    v
     Investigate call path and dependency contract
                    |
                    v
          Regression test + implementation
                    |
                    v
          Focused and full offline tests
                    |
                    v
                DoD audit
                    |
                    v
          Independent AI code review
                    |
          +---------+----------+
          |                    |
   REQUEST CHANGES          APPROVED
          |                    |
          v                    v
 Fix findings and retest    Human acceptance
          |                    |
          +--------------------+
                    |
                    v
      Authorized commit / push / PR / merge
                    |
                    v
           Close task and select next Issue
```

## Conversation Continuity

Conversation transcripts are task-local context, not repository memory. The
repository handoff is `TASK.md`, verified against Git and the affected code.

### Recover In A New Conversation

Before editing, the new conversation must:

1. Read `AGENTS.md`, `.ai/README.md`, and `.ai/TASK.md`.
2. Resolve the repository root, branch, HEAD, worktree list, status, recent
   commits, and relevant staged and unstaged diff.
3. Compare that evidence with the `TASK.md` handoff snapshot.
4. Read the task-specific `.ai` references selected by `.ai/README.md`, then
   inspect the affected source, tests, and human documentation.
5. Report the recovered objective, current phase, repository state, next exact
   action, tests already evidenced, and any mismatch before continuing.

Git, source, tests, and locked dependency signatures override stale handoff or
design prose. A mismatch must be explained and reconciled; it must not be
silently rewritten to match a previous conversation's intent. Ignored build,
cache, log, download, and temporary directories are not task context unless the
active Issue explicitly concerns them.

### Create A Handoff Checkpoint

Update the `TASK.md` handoff snapshot at meaningful boundaries: after
investigation, after a reproducing failure, after implementation, after a test
or review phase, before intentionally switching conversations, and when work
becomes blocked. Do not rewrite it after every command.

The snapshot records only durable facts:

- updated time, Issue status, and current phase;
- base branch, task branch, base commit, and current HEAD;
- clean or dirty worktree state and changed paths;
- last completed action and next exact action;
- blockers, open questions, and decisions that constrain the next action;
- exact tests passed, failed, or not run;
- whether uncommitted work requires resuming the same worktree.

Do not paste long command output, credentials, signed URLs, token-bearing error
text, or a transcript summary into the handoff. Put stable product or
architecture decisions in their authoritative document and retain only the
task-specific consequence and rationale in `TASK.md`.

### Worktree Boundary

A new conversation using the same worktree can inspect its uncommitted changes.
An isolated worktree reliably starts only from committed Git state and cannot
inherit another worktree's staged or unstaged files, including an uncommitted
`TASK.md` update.

When an active task is dirty, resume it in the same worktree. Move it to an
isolated worktree only from a clean state or an explicitly authorized checkpoint
commit. Do not create a commit merely to make conversation switching convenient;
the normal commit authorization and delivery rules still apply. Record the
required worktree in the handoff whenever uncommitted work exists.

## Issue Contract

Every Issue selected for implementation must provide:

- stable ID and title;
- primary type and priority;
- user impact;
- reproducible evidence;
- current and expected behavior;
- affected CLI/SDK call path;
- in-scope and out-of-scope work;
- compatibility requirements;
- observable acceptance criteria;
- required offline tests and separately authorized live tests;
- delivery mode and individual Git/remote permissions;
- DoD and human acceptance checklist.

The Issue contract also contains these development-floor sections before any
implementation edit:

- `Affected Capability IDs`: every existing or new capability touched;
- `Protected Existing Invariants`: observable old behavior that must remain;
- `New Or Changed Invariants`: new behavior or an explicitly authorized
  compatibility migration;
- `Focused Tests And Evidence`: executable regressions plus dependency,
  security, packaging, portability, or controlled-remote evidence;
- `Complete Baseline Evidence`: the final
  `python tests/run_cli_baseline.py` result after the last change;
- `Residual Risks`: tests not run, partial remote evidence, and accepted
  limitations.

An Issue is not ready for implementation when affected capability IDs or
protected invariants are unknown. An Issue is not ready for completion when
the complete baseline is failed or unrun.

An Issue is not ready when the expected remote behavior is guessed, the test
repository is not safe, or success cannot be observed.

## Priority

- `P0`: credential exposure, destructive cross-repository behavior, or release
  compromise; stop other work.
- `P1`: core command broken, data integrity risk, or advertised capability
  unusable; blocks release.
- `P2`: important compatibility, edge-case, testing, or maintainability gap.
- `P3`: low-risk documentation, clarity, or polish work.

Priority does not grant permission to perform destructive or remote actions.

## Reusable Implementation Prompt

```text
You are implementing the single active Issue in .ai/TASK.md.

Read AGENTS.md, every required file under .ai/, and the affected source and
tests. Confirm the atomgit_cli conda environment, yuto-based branch, cleanly
understood worktree, locked dependency signatures, evidence, scope, and
acceptance criteria.

Implement only this Issue. Add a regression or contract test at the boundary
where the problem occurs. Keep CLI and SDK compatibility in scope only when the
Issue contract requires it. Do not perform live AtomGit writes, modify real Git
credentials, commit, push, open a PR, merge, or release unless TASK.md grants
that exact permission.

Before finishing, run focused tests, all required offline tests, compileall,
git diff --check, and the applicable DOD.md checklist. Record decisions,
commands, results, and remaining risk in TASK.md. Do not implement future
Issues.
```

## Reusable Review Prompt

```text
Switch to the independent reviewer role. Assume you did not write this change.
Review the active Issue contract, complete diff, tests, documentation, locked
dependency signatures, and test output. Do not edit code.

Focus on AtomGit CLI/SDK correctness, HF Hub 1.1.7 compatibility, model/dataset
semantics, revision and repository ID behavior, token and Git-helper safety,
temporary-resource lifetime, global-state restoration, exit codes, SDK
exceptions, strictness of mocks, backward compatibility, and documentation
claims.

List findings first with P0/P1/P2/P3 severity and file/line references. Then
list open questions and missing evidence. End with exactly one verdict:
APPROVED or REQUEST CHANGES.
```

## Reusable Fix Prompt

```text
Return to implementation mode. Fix every accepted blocking review finding for
the active Issue. Do not add features, broaden scope, change public APIs unless
the Issue authorizes it, or address unrelated roadmap items. Add or update
regression tests where findings expose missing coverage. Rerun all affected and
required checks, update TASK.md evidence, and request a fresh independent
review.
```

## Long-Term Maintenance Acceptance Prompt

```text
Assume this AtomGit CLI/SDK will be maintained for at least three years and
used in automated environments. Do not praise the implementation. Identify
concrete future risks involving dependency upgrades, duplicated CLI/SDK logic,
credential migration, Python support, AtomGit/HF semantic differences,
installation provenance, release safety, and regression detection.

Separate current blocking defects from follow-up Issue candidates. Do not edit
code or silently expand the active Issue.
```

## Human Acceptance

The human maintainer checks observable product behavior, not only unit tests:

- the Issue outcome matches the original need;
- command output and failure guidance are understandable;
- compatibility and known limitations are acceptable;
- any authorized live test uses safe repositories and has remote evidence;
- blocking review findings are resolved or consciously accepted;
- the proposed commit/PR scope is appropriate.

Human acceptance does not replace tests or review, and AI approval does not
replace human acceptance.

## Closing An Issue

After authorized delivery:

1. Record commit or PR references and final evidence.
2. Set `TASK.md` status to `completed` only after acceptance criteria are met.
3. Do not delete unresolved risks; convert approved follow-ups into candidate
   roadmap entries or remote Issues only with authorization.
4. Reset `TASK.md` to `inactive` before selecting the next Issue.
