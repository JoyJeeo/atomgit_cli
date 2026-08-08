# AtomGit CLI AI Development Instructions

This repository uses repository-level instructions plus task-scoped work.

## Startup And Context Recovery

At the start of every new conversation or resumed task:

1. Read `.ai/README.md` for the task-specific document map.
2. Read `.ai/TASK.md` for the single persistent task handoff.
3. Inspect the real repository state: Git root, current branch and HEAD,
   worktree list, status, recent log, and relevant diff.
4. Read the source, tests, and human documentation related to the request.
5. Before editing, summarize the recovered objective, phase, repository state,
   next action, and any mismatch that requires reconciliation.

Do not assume another conversation's transcript is available. Do not read every
`.ai` document by default; load the references selected by `.ai/README.md` for
the current task and phase so irrelevant roadmap or review context does not
crowd out the affected code and tests.

The current user request has higher priority than `.ai/TASK.md`. `TASK.md` is a
persistent handoff for autonomous or multi-turn work; it is not permission to
start roadmap items on its own. Git, source, tests, and locked dependency
signatures are the authority for actual state. If they disagree with the
handoff, report and reconcile the mismatch before editing.

Only one Issue may be active in `.ai/TASK.md` at a time. Do not create remote
Issues, change milestones, or transition Issue state without explicit user
authorization.

## Environment

All repository commands must run inside the `atomgit_cli` conda environment.
For every new shell session, initialize conda and activate the environment
before running Python, tests, builds, installs, or project scripts:

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate atomgit_cli
```

Do not silently fall back to the system Python. Use `python -m pip` rather than
an ambiguous standalone `pip` when installing or inspecting packages.

## Branches

- `yuto` is the GitHub development mainline and the default base for feature
  and bug-fix work.
- `main` mirrors `atomgit/main`. Do not develop features directly on `main`.
- Upstream changes flow `atomgit/main -> main -> yuto`.
- Do not merge `yuto` back into `main` unless the user explicitly requests an
  upstream contribution.
- Use a task branch based on `yuto` for substantial work. Do not push, merge,
  tag, or publish without explicit authorization.

### Maintainer Standing Delivery Rules (authorized 2026-08-04)

- Develop one Issue at a time; merge into `yuto` only after that Issue is
  complete and verified. Never develop multiple Issues simultaneously.
- Use a concise conventional commit subject without the retired `czx:` prefix
  (for example `fix(upload): validate upload timeout`).
- Task branches are local-only: never push a development branch to the remote.
- After implementation and tests pass, merge the task branch into `yuto`
  locally and push only the `yuto` branch.

## Scope And Safety

- Inspect the worktree before editing and preserve user changes.
- Make the smallest coherent change that satisfies the active task.
- Do not implement unrelated roadmap items.
- Never print, copy, commit, or expose AtomGit tokens or the contents of
  `~/.atomgit/config.json`.
- Do not run live repository creation, upload, delete, push, credential-helper
  mutation, PyPI publication, or other remote write operations unless the user
  explicitly authorizes that exact operation.
- Local tests must be offline by default. Live tests require dedicated test
  credentials and disposable repository names.
- Treat `huggingface-hub==1.1.7` and `datasets==4.4.1` as explicit compatibility
  contracts until dependency policy is intentionally changed.

## Completion And Review

Apply `.ai/DOD.md` before declaring a change complete. For substantial or
high-risk changes, perform the independent review defined in `.ai/REVIEW.md`
after implementation and tests. Review findings must be resolved or explicitly
accepted before merge.

At minimum, a change is complete only when:

- behavior and compatibility requirements are clear;
- implementation, focused regression tests, and affected documentation agree;
- relevant offline tests pass in the `atomgit_cli` environment;
- dependency calls are checked against the real locked-library signatures;
- `python -m compileall -q .` and `git diff --check` pass;
- the final diff contains no credentials, generated artifacts, or unrelated
  changes;
- remaining risks and tests not run are reported explicitly.
