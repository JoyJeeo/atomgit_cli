# Definition Of Done

Use the checklist that matches the change. A skipped item must be marked not
applicable or reported with its residual risk; silence is not a pass.

## All Changes

- [ ] When operating in the Issue implementation workflow, exactly one approved
      Issue is active and `TASK.md` contains its evidence, scope, acceptance
      criteria, delivery mode, and permissions. A direct user-authorized
      planning or documentation task may leave `TASK.md` inactive.
- [ ] The task has one observable objective and explicit scope.
- [ ] The final diff contains only task-related changes.
- [ ] No token, credential file content, generated artifact, or test repository
      secret is present.
- [ ] Current behavior, limitations, and planned behavior are not conflated.
- [ ] `git diff --check` passes.
- [ ] Tests or checks not run are reported.
- [ ] Remaining risks are reported.
- [ ] The independent review verdict is recorded for substantial or high-risk
      changes.
- [ ] No P0 or P1 review finding remains open.
- [ ] Human acceptance is recorded before Issue delivery or merge. Direct
      planning and documentation requests are accepted through the normal user
      review of the delivered result.

## Python Behavior Changes

- [ ] A focused regression test covers the changed boundary.
- [ ] Relevant offline tests pass in the `atomgit_cli` conda environment.
- [ ] Calls into locked dependencies match their real installed signatures.
- [ ] CLI success/failure exit codes and actionable output are verified.
- [ ] SDK parameters are forwarded or explicitly documented as unsupported.
- [ ] Temporary resources survive until use and are cleaned afterward.
- [ ] Modified global state is restored.
- [ ] `python -m compileall -q .` passes.
- [ ] Externally visible behavior has matching documentation.

## Mandatory CLI Feature Baseline Gate

This gate applies to every feature and bug-fix Issue, including changes that
are not expected to affect the CLI. It is not optional and may not be reported
as not applicable. Run it after implementation and after every subsequent fix,
before human acceptance, Issue completion, delivery, or merge:

```bash
python tests/test_cli_feature_baseline.py
```

- [ ] The command ran in the `atomgit_cli` conda environment and every baseline
      check passed.
- [ ] The command and passing result are recorded in `TASK.md` verification
      evidence.
- [ ] If the gate failed at any point, the Issue remained active, returned to
      implementation, and the regression was fixed before the gate was rerun.
- [ ] A failing gate blocks acceptance, completion, commit for delivery, merge,
      and push; repeat the repair-and-test loop until every check passes.
- [ ] The baseline was not removed, skipped, or weakened to make a regression
      pass. An intentional public compatibility break requires explicit
      maintainer authorization in the active Issue, matching documentation and
      baseline updates, and a final passing gate.

## Documentation-Only Changes

- [ ] Claims were checked against source, tests, and dependency versions.
- [ ] Links and referenced repository files exist.
- [ ] AI rules and human documentation do not conflict.
- [ ] No source or runtime behavior changed.

## Issue Closure

- [ ] Every acceptance criterion has evidence.
- [ ] Review findings and their disposition are recorded.
- [ ] Human acceptance is `accepted`.
- [ ] Commit, push, PR, merge, Issue transition, and release actions stayed
      within their individual permissions.
- [ ] Approved follow-up work is recorded without silently implementing it.
- [ ] `TASK.md` will return to `inactive` before the next Issue starts.

## Packaging Or Release Changes

- [ ] Version values and distribution identity are consistent.
- [ ] Wheel build and isolated installation smoke tests pass.
- [ ] `atomgit --help`, `python -m atomgit --help`, `import atomgit`, and
      `import atomgit_hub` pass after installation.
- [ ] Release artifacts have checksums and no credentials.
- [ ] Publication was explicitly authorized.

## Live AtomGit Changes

- [ ] The exact live operations were explicitly authorized.
- [ ] Dedicated credentials and uniquely named disposable repositories were
      used.
- [ ] Results include command exit codes and remote state or checksum evidence.
- [ ] Cleanup was performed only with explicit authorization and recorded.
