# AtomGit CLI AI Development Framework

This directory contains durable project context for AI-assisted development.
It complements the source code and tests; it does not replace reading them.

## Documents

- `MASTER_PROMPT.md`: engineering role, decision rules, and execution loop.
- `PRODUCT.md`: product scope, users, supported capabilities, and boundaries.
- `ARCHITECTURE.md`: current runtime structure, data flow, and design risks.
- `DEVELOPMENT_RULES.md`: task scope, change discipline, Git, and safety rules.
- `WORKFLOW.md`: Issue lifecycle, templates, prompts, and human acceptance.
- `STYLE_GUIDE.md`: repository-specific Python, CLI, API, and documentation
  conventions.
- `TESTING.md`: offline, contract, packaging, and optional live-test policy.
- `DOD.md`: change-type-specific definition of done.
- `REVIEW.md`: independent review procedure and severity model.
- `ROADMAP.md`: prioritized direction; roadmap entries are not active tasks.
- `TASK.md`: the single persistent task handoff for autonomous work.

## Conversation Startup

After reading this routing file, every new conversation reads `TASK.md` before
the task-specific references, reconciles it with the current Git worktree, and
then loads only the references needed for the requested task:

| Task or phase | Required references |
|---|---|
| Any repository change | `MASTER_PROMPT.md`, `DEVELOPMENT_RULES.md`, `DOD.md` |
| Product behavior or scope | `PRODUCT.md` |
| Runtime or structural change | `ARCHITECTURE.md` |
| Python, CLI, SDK, or documentation implementation | `STYLE_GUIDE.md` |
| Tests or verification | `TESTING.md` |
| Issue activation, handoff, delivery, or closure | `WORKFLOW.md` |
| Independent review | `REVIEW.md` |
| Planning or selecting future work | `ROADMAP.md` |

Do not load `ROADMAP.md` during ordinary implementation unless the current
request needs it. A new conversation must not infer an active task from a
completed task, a local branch name, or roadmap priority.

## Authority

Use this order when instructions conflict:

1. Explicit user request
2. `AGENTS.md`
3. `.ai/TASK.md`
4. Other `.ai` documents
5. Existing source and local conventions

Source code and tests remain the authority for current behavior. If a design
document is stale, report the discrepancy and update it as part of an
authorized change.

Do not read only `.ai/` and assume the implementation matches it. Always inspect
the affected source, tests, dependency signatures, and relevant human-facing
documentation.
