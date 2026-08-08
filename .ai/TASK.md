# Current Issue Contract

Status: `inactive`

This is the repository's single persistent handoff for active, multi-turn, or
cross-conversation work. It records task facts and permissions; it does not
authorize work by itself. When inactive, the current user request and real Git
state determine what may happen next.

The most recently delivered Issue was `CLI-UPLOAD-DEFAULT-RESUME`, merged into
`yuto` by `36d9d11`. Its complete contract and evidence remain available in Git
history.

## Handoff Snapshot

Populate this section when an Issue becomes active and refresh it at meaningful
workflow checkpoints. Use repository-relative paths and never include tokens,
credential contents, signed URLs, or raw secret-bearing logs.

- Updated: `not applicable while inactive`
- Status: `inactive`
- Phase: `idle`
- Base branch: `not assigned`
- Task branch: `not assigned`
- Base commit: `not assigned`
- Current HEAD: `verify from Git before activation`
- Worktree state: `verify from Git before activation`
- Changed paths: `none assigned to an active Issue`
- Required worktree: `not assigned`
- Last completed action: `previous Issue delivered; see Git history`
- Next exact action: `await an explicit user request or approved Issue`
- Blockers / open questions: `none`
- Decisions constraining the next action: `none`
- Tests passed: `none for an active Issue`
- Tests failed or not run: `none for an active Issue`

## Active Issue Identity

No Issue is active. On activation, record:

- stable local or remote Issue ID and title;
- primary type and priority;
- base and task branch;
- delivery mode;
- individual permissions for commit, push, PR, merge, Issue transition,
  release, live requests, credentials, and remote writes.

## Evidence And Objective

For an active Issue, record the user impact, reproducible evidence, current
behavior, expected behavior, affected call path, and one observable objective.

## Scope And Acceptance

For an active Issue, record in-scope work, explicit non-goals, compatibility
requirements, observable acceptance criteria, required offline tests, and any
separately authorized live tests.

## Decisions And Rationale

Record only decisions that affect the active Issue, including rejected options
when their rejection prevents the next conversation from repeating unsafe or
invalid work. Move stable product or architectural decisions into the relevant
authoritative `.ai` or `docs` document.

## Verification Evidence

Record exact commands, environment, exit status or test count, offline or live
classification, review findings and dispositions, residual risk, and checks not
run. A statement such as "tests pass" is not sufficient.

## Closure

After authorized delivery, record commit or PR references, final evidence,
review verdict, human acceptance, and remaining follow-ups. Set the status to
`completed` only after the Issue contract is satisfied, then reset this file to
`inactive` before selecting another Issue. Git history retains the completed
contract.
