# AtomGit CLI Development Floor

## Formal Definition

> AtomGit CLI 的所有已实现能力，都必须拥有稳定的能力登记、明确的行为不变量、可执行的离线回归测试、必要的依赖和安全契约，以及在适用时的受控远程证据。任何开发活动都必须证明受影响的旧能力未退化，并将新增能力纳入同一套基线。未通过开发底线的变更，不得进入 Issue 完成、合并、发布或继续扩展开发阶段。

The development floor is a permanent compatibility and quality contract. It
does not freeze internal implementation, but it does freeze registered public
behavior and safety outcomes unless the maintainer explicitly authorizes a
compatibility migration.

## Sources Of Truth

- `tests/development_floor_contract.py` is the executable capability and
  invariant ledger.
- `tests/test_development_floor.py` proves that the ledger, its evidence, and
  the workflow documents fail closed when incomplete or stale.
- `tests/cli_baseline_contract.py` remains authoritative for the exact public
  CLI schema, leaf dispatches, and offline test-script inventory.
- `python tests/run_cli_baseline.py` is the one complete offline gate.
- `docs/development_floor.md` is the human-facing explanation of the same
  contract.

The current ledger contains 26 capability IDs, 93 observable invariants, and
82 isolated offline pytest cases. Counts are monotonic ledgers: an authorized
migration may replace evidence, but it must not silently remove a capability,
invariant, or regression.

## Capability Contract

Every implemented or newly added capability must register:

- one stable uppercase capability ID;
- a user- or maintainer-observable name and entrypoint;
- its risk class;
- one or more explicit behavior or safety invariants;
- executable offline tests for the capability and for every invariant;
- authoritative human or AI documentation;
- required evidence categories: offline, dependency, security, packaging,
  portability, or controlled remote;
- controlled-remote evidence status: not applicable, controlled, partial, or
  required before claiming support.

Capability IDs describe behavior, not files. Refactoring a module does not
create a new capability. Adding a user-observable behavior either extends an
existing capability with a new invariant or introduces a new stable ID.

## Invariant Contract

Each invariant has a unique stable ID, a concrete observable statement, and at
least one mapped offline regression. Statements must describe outcomes such as
arguments forwarded, exit status, bytes preserved, state restored, or secrets
redacted. Implementation details alone are not invariants.

Every `tests/test_*.py` script must be registered exactly once in the CLI
baseline inventory and mapped to at least one capability. A capability may use
multiple tests, and one cross-cutting test may support multiple capabilities.
An invariant may reference only executable tests already assigned to its
capability.

## Structure Refactor Contract

`tests/structure_contract.py` declares current module ownership, approved
dependency directions, stable public imports and symbols, artifact contents,
and exact legacy facade and dependency debt. `tests/test_structure_guard.py`
fails when a production module has no owner, an empty placeholder appears, a
new dependency edge is introduced, a forbidden direction grows, or a legacy
facade grows before its behavior is extracted.

The contract requires current edges and debt ceilings to match exactly, so a
structural Issue must tighten the declaration in the same change that removes
debt. This prevents removed debt from silently returning below an obsolete
upper bound. The contract reads production modules from `src/atomgit` and
separately checks the top-level SDK compatibility proxy. It does not authorize
placeholder domain packages or public behavior changes.

## Packaging And Tooling Contract

`pyproject.toml` declares the setuptools build backend, the explicit `src`
package mapping, the top-level `atomgit_hub` compatibility module, the
Python 3.9 tool target, and pytest collection policy. `setup.py` remains the
transition-period project-metadata authority and must agree with the declared
package layout and must remain exact with `setup.py`.

`tests/packaging_contract.py` records the exact normalized Black, isort, and
Ruff debt produced by the pinned development-tool versions.
`tests/test_packaging_metadata.py` requires that debt to match exactly, so
removing debt requires the declaration to tighten in the same change and new
violations cannot hide below a ceiling. Issue-owned new files use the clean
policy immediately; broad formatting remains a separate authorized change.

## Issue Impact Contract

Before implementation, every development Issue records:

- `Affected Capability IDs`;
- `Protected Existing Invariants`;
- `New Or Changed Invariants`;
- focused offline tests and evidence categories;
- whether controlled-remote evidence is required;
- the mandatory complete-baseline command;
- tests not run and residual risks.

The Issue must add a new capability or invariant to the executable ledger in
the same change that implements it. Documentation or internal-only work still
declares which capabilities are affected, or explicitly records that only the
development-floor meta-capability is affected.

## Blocking Rule

Every development Issue, including testing, documentation, refactoring,
compatibility, distribution, and release work, must run:

```bash
python tests/run_cli_baseline.py
```

A failed or unrun complete baseline blocks Issue completion, human acceptance,
delivery commit, merge, push, tag, release, publication, and further feature
expansion. The Issue remains active and returns to implementation until the
regression is fixed and the complete baseline passes.

Focused tests are required for fast feedback and direct evidence, but they
never replace the complete gate. A passing mock is not remote evidence, and a
passing remote operation is not a substitute for deterministic offline
regressions.

Tests and registry entries may not be removed, skipped, weakened, or relabeled
to accommodate an unintended regression. A regression must be fixed in the
affected implementation or test infrastructure before work continues.

## Compatibility Migration

An intentional public or safety-contract change requires all of the following:

1. explicit maintainer authorization in the active Issue;
2. the old and new behavior, user impact, and migration path;
3. affected capability and invariant IDs;
4. replacement offline evidence that fails on the unintended intermediate
   states;
5. matching user and AI documentation;
6. a final passing complete baseline;
7. an independent review of whether the migration hides an unrelated
   regression.

The migration may update a registered invariant, but it must preserve history
in the Issue and Git record. Decreasing monotonic ledger counts requires an
explicit rationale that identifies every retired ID and its replacement; a
routine implementation Issue cannot authorize that reduction implicitly.

## Maintenance Procedure

For each new capability or behavior:

1. register affected IDs and protected invariants in `TASK.md`;
2. add a failing focused test at the observable boundary;
3. implement the behavior;
4. add or update the capability and invariant ledger;
5. update the smallest authoritative human documentation;
6. run focused tests and the complete baseline;
7. record exact evidence in `TASK.md`;
8. review the diff against this document before delivery.

If the ledger, documentation, test inventory, or collected pytest count
disagrees with the repository, the executable repository state is investigated
first and all authorities are reconciled in the active testing Issue.
