# Current Issue Contract

# Issue REPO-INFO-STUB-SEMANTICS

Status: `active`

## Identity

- Local Issue: `REPO-INFO-STUB-SEMANTICS`
- Title: `Stop reporting fabricated repository information`
- Type: `bug`, `api`, `diagnostics`
- Priority: `P3`
- Branch: `codex/fix-repo-info-stub` (local only)
- Base: `yuto`
- Previous Issue: `DOWNLOAD-MANIFEST-CONCURRENCY`, delivered by `ab7bd98`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

`HuggingFaceAPI.get_repo_info` never queries AtomGit or validates its input. It
returns a truthy dictionary containing the caller's repository ID plus a fixed
"SDK support required" status. Callers can mistake this fabricated object for
verified repository metadata or repository existence.

Repository information retrieval is not an advertised CLI feature and real V5
detail support would be new functionality. The existing method must therefore
fail explicitly and safely instead of returning invented success data.

## Scope And Acceptance

- Preserve the public method name, parameters, and `Optional[Dict]` signature.
- Return `None` with one fixed actionable unsupported message.
- Do not echo caller input, exception details, repository data, or credentials.
- Do not read credentials or issue any network request.
- Add a focused regression proving no truthy/fabricated data and no side effect.
- Document the compatibility boundary for maintainers.
- Do not implement repository detail retrieval, add a command/flag, change V5
  calls, add an exception type, or modify unrelated functionality.

## Compatibility And Risks

- Callers that incorrectly treated the placeholder dictionary as verified data
  will now receive the method's existing failure sentinel, `None`.
- Method presence and type signature remain stable; no supported CLI path calls
  this method.
- No live request is needed or allowed.

## Permissions

- The user authorized fixing already audited defects one Issue at a time and
  explicitly excluded new functionality.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- No live request, repository access, remote write, credential mutation, or
  external side effect is authorized or required for this Issue.

## Required Evidence And Closure

- [x] Fabricated truthy metadata is reproduced by a failing regression.
- [x] The method returns `None` with fixed safe unsupported guidance.
- [x] Credential and network access are impossible on this path.
- [x] Public signature and all supported CLI/API behavior remain compatible.
- [x] Focused and complete offline tests, compileall, pip, and diff checks pass.
- [x] Documentation, credential scan, scope audit, and independent review pass.
- [x] Human acceptance is covered by the standing ordered-fix authorization.
- [ ] The task is committed, merged into `yuto`, and only `yuto` is pushed.

## Verification Evidence

- Regression before implementation: the focused contract passed `3/5`; the
  method returned a truthy placeholder dictionary and emitted no unsupported
  failure, even for a deliberately untrusted repository ID.
- Implementation: the existing method and `Optional[Dict[str, Any]]` signature
  remain present. Every call now returns `None` and prints one fixed, actionable
  unsupported message without interpolating input or exception details.
- Side-effect contract: credential and urllib access were replaced with
  assertion-raising spies; the focused `5/5` run proved neither was called and
  the input marker was absent from output.
- Complete offline suite: `pytest -q` exited `0` with all `55` collected tests;
  `python -m compileall -q .`, `python -m pip check`, and `git diff --check`
  passed in the `atomgit_cli` environment.
- Security and scope: no live request, repository access, remote write,
  credential access, command, flag, exception type, dependency, generated
  artifact, or repository-detail feature is present.
- Independent review: `APPROVED` with no open P0-P3 findings. The intentional
  compatibility correction affects only callers that treated explicitly
  unsupported placeholder text as verified repository metadata.
