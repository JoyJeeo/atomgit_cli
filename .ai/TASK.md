# Current Issue Contract

# Issue PYTHON-VERSION-CONTRACT

Status: `ready-for-delivery`

## Identity

- Local Issue: `PYTHON-VERSION-CONTRACT`
- Title: `Align Python support metadata with locked dependencies`
- Type: `bug`, `packaging`, `compatibility`
- Priority: `P1`
- Branch: `codex/fix-python-version-contract` (local only)
- Base: `yuto`
- Previous Issue: `WINDOWS-CLI-COMPATIBILITY`, delivered by `3db0b08`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

The package declares `python_requires='>=3.8'`, publishes a Python 3.8
classifier, and documents Python 3.8 support. Both locked runtime contracts,
`huggingface-hub==1.1.7` and `datasets==4.4.1`, declare
`Requires-Python: >=3.9.0`. A Python 3.8 installation therefore cannot satisfy
the project's required dependency set even though the AtomGit wheel claims it
is compatible.

Package installers and maintainers must receive one truthful minimum-version
contract. The AtomGit wheel, source metadata, engineering rules, review
checklist, and user documentation must all require Python 3.9 or newer.

## Scope And Acceptance

- Change package `python_requires` to `>=3.9` and remove only the Python 3.8
  classifier; retain Python 3.9-3.13 classifiers.
- Add a packaging regression that reads built wheel metadata and proves the
  wheel minimum matches the installed locked dependency metadata.
- Update all authoritative current support-policy references from 3.8 to 3.9,
  including repository development and review instructions.
- Preserve package version, dependencies, entry points, CLI/SDK interfaces,
  source layout, and existing wheel smoke coverage.
- Do not upgrade dependencies, add CI matrices, backport dependencies, change
  runtime behavior, or fix another audited issue.

## Compatibility And Risks

- Python 3.8 users will be rejected accurately by installers instead of
  receiving an unsatisfiable environment; this is an intentional packaging
  compatibility correction required by locked dependencies.
- Python 3.9 is metadata compatibility evidence, not a real local execution
  result. The current test environment is Python 3.10 and must be reported as
  such.
- Locked `huggingface-hub==1.1.7` and `datasets==4.4.1` remain unchanged.

## Permissions

- The user authorized issue-by-issue fixes for confirmed CLI defects and
  excluded new functionality.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- No live AtomGit request, repository mutation, publication, release, or
  dependency installation is required or authorized.

## Required Evidence And Closure

- [x] Previous wheel/source support metadata mismatch is reproduced.
- [x] Built wheel declares Python `>=3.9` and no Python 3.8 classifier.
- [x] Locked dependency metadata independently proves Python 3.9 minimum.
- [x] Current user, development, style, and review policies agree on 3.9+.
- [x] Existing wheel install/entry-point smoke behavior remains intact.
- [x] Focused and complete offline tests, compileall, pip, and diff checks pass.
- [x] Documentation, credential scan, scope audit, and independent review pass.
- [x] Human acceptance is covered by the standing ordered-fix authorization.
- [ ] The task is committed, merged into `yuto`, and only `yuto` is pushed.

## Verification Evidence

- Regression before implementation: the built-wheel smoke passed `19/21`;
  METADATA still declared `Requires-Python: >=3.8` and included the Python 3.8
  classifier. The same run independently found `>=3.9.0` on both locked
  dependency distributions.
- Implementation: `setup.py` now declares `python_requires='>=3.9'`, removes
  only the 3.8 classifier, and preserves 3.9-3.13, package version, dependency
  locks, entry points, package layout, and runtime source unchanged.
- Policy alignment: README system/contributor/version guidance and repository
  development, style, and review instructions now consistently require 3.9+;
  a complete hidden-file search found no stale current 3.8 policy reference.
- Focused wheel result: `21/21`, including actual wheel METADATA inspection,
  exact locked dependency metadata, temporary no-dependency install, imports,
  CLI/module entry points, all command help, and unchanged repository artifacts.
- Complete offline suite: `pytest` collected `55` items and exited `0` under
  Python `3.10.20`. `python -m compileall -q .`, `python -m pip check`, and
  `git diff --check` passed in the `atomgit_cli` environment.
- Security and scope: no dependency install, remote request, repository write,
  credential, generated diff artifact, runtime behavior change, or unrelated
  feature is present.
- Independent review: `APPROVED` with no P0-P3 findings. Residual risk is that
  Python 3.9 was not executed locally; compatibility is proven here at package
  and dependency metadata level, while complete runtime evidence is Python 3.10.
