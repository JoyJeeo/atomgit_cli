# AtomGit CLI Engineering Style

## Python Baseline

- Support Python 3.9 and newer as declared by packaging metadata.
- Follow the existing module layout unless the task justifies a migration.
- Use four-space indentation, `snake_case` functions and variables,
  `PascalCase` classes, and `UPPER_CASE` constants.
- Add type hints to new or changed public interfaces where they improve the
  contract without forcing unrelated rewrites.
- Prefer `pathlib.Path` for filesystem paths.
- Use structured library arguments instead of constructing protocol payloads
  or URLs manually when an authoritative API exists.

## Implementation

- Do not catch `Exception` unless the boundary must convert it into a stable
  CLI or SDK result. Preserve the original cause and useful context.
- Restore changed global state in `finally`.
- Use unique system temporary directories; do not use a shared
  working-directory `.tmp_upload` for new code.
- Avoid mutable module-global state beyond established singletons.
- Validate external input at the boundary and avoid duplicate validation that
  can disagree.
- Do not add an abstraction solely to make a small function look cleaner.

## CLI

- Click owns argument parsing and choice validation.
- Successful commands exit `0`; rejected input and failed requested operations
  exit nonzero.
- Keep output concise and actionable. Never print tokens.
- Existing Chinese user-facing terminology should remain consistent.
- Warnings must describe whether an option was ignored, unsupported, or
  partially applied.

## SDK

- Public function parameters are compatibility contracts.
- Do not silently ignore supported-looking parameters.
- Prefer standard exception types or a documented AtomGit exception hierarchy
  over generic `Exception` for new interfaces.
- CLI-only printing must not leak into SDK operations.

## Documentation

- Keep README examples executable against the current CLI.
- Update architecture documentation when runtime relationships change.
- State limitations as limitations; do not document intended behavior as if it
  were verified.
- Comments should explain non-obvious constraints, not narrate straightforward
  assignments.

## Change Discipline

- Preserve unrelated formatting and metadata.
- Keep version values synchronized when a release task changes the version.
- Do not combine dependency upgrades, behavior changes, and broad refactors in
  one task unless the task explicitly requires that migration.
