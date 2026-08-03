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
