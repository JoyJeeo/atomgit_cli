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
