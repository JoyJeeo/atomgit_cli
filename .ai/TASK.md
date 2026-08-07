# Current Issue Contract

# Issue WINDOWS-CLI-COMPATIBILITY

Status: `ready-for-delivery`

## Identity

- Local Issue: `WINDOWS-CLI-COMPATIBILITY`
- Title: `Restore advertised Windows CLI compatibility safely`
- Type: `bug`, `compatibility`, `security`, `cli`
- Priority: `P1`
- Branch: `codex/fix-windows-cli-compatibility` (local only)
- Base: `yuto`
- Previous Issue: `UNICODE-DOWNLOAD-METADATA`, delivered by `7aebd21`.
- Delivery mode: standing-authorized implementation, review, commit, local
  merge into `yuto`, and push only `yuto`; task branch remains local-only.

## Evidence And Expected Behavior

The package advertises Windows, macOS, and Linux support, but three existing
CLI paths depend on Unix behavior:

- Python 3.8-3.12 on Windows has no `os.fchmod`, so credential saving and
  download-manifest writes fail before atomic replacement.
- `--prune` requires `O_DIRECTORY`, `O_NOFOLLOW`, and descriptor-relative
  unlink, so it always rejects Windows even for a safe managed regular file.
- the Git helper is configured as an unquoted `!<path>` shell command; Windows
  backslashes and paths containing spaces do not identify the helper reliably.

Existing login, Git credential integration, default downloads, and explicit
manifest-scoped pruning must work on supported Windows Python versions without
weakening credential handling or allowing prune to follow reparse points or
delete outside the selected download root.

## Scope And Acceptance

- Use descriptor permission setting where available and a path-based chmod
  fallback where `os.fchmod` is unavailable, preserving atomic writes.
- Build the managed Git helper command from the running Python interpreter and
  helper script with shell-safe quoting and Windows separator normalization;
  preserve backup, rollback, repeated login, status, and legacy cleanup.
- Keep the existing POSIX descriptor-relative prune implementation unchanged.
- On Windows, open root and target through Win32 handles, reject directories and
  reparse points, compare fully resolved handle paths, and mark only the opened
  in-root regular file for deletion by handle.
- Treat missing managed files as already clean and fail closed on every Windows
  API, path-containment, type, or reparse-point uncertainty.
- Add strict platform regressions with an injected fake Windows API, plus an
  executable helper test from paths containing spaces.
- Update only affected compatibility/security documentation; do not add CLI
  commands, flags, or unrelated functionality.

## Compatibility And Risks

- Preserve Python 3.8 syntax and the locked HF/datasets contracts.
- Windows file-mode bits have platform-defined semantics; the fix prevents the
  current crash and retains inherited Windows ACLs rather than claiming POSIX
  ACL equivalence.
- Win32 deletion must use `CreateFileW` with reparse-point handling,
  `GetFinalPathNameByHandleW`, attribute inspection, and
  `SetFileInformationByHandle(FileDispositionInfo)` with DELETE access.
- No Windows runtime is installed locally. Pure policy/dispatch tests and a
  fake Win32 handle backend are required; absence of a real Windows acceptance
  run must be reported as residual risk, not hidden.

## Permissions

- The user authorized issue-by-issue fixes for confirmed CLI defects and
  excluded new functionality.
- Standing local development, commit, merge, and `yuto` push permissions apply.
- The task branch must remain local and must not be pushed.
- No live AtomGit request or remote repository mutation is required or allowed.
- Git helper tests must isolate HOME and global Git configuration and must not
  modify the user's real credential helper state.

## Required Evidence And Closure

- [x] Previous behavior is reproduced by strict platform regressions.
- [x] Credential and manifest atomic writes tolerate missing `os.fchmod`.
- [x] Managed Git helper commands are executable and reversible with Windows or
      space-containing paths.
- [x] Windows prune deletes only an opened in-root regular file and rejects
      reparse points, directories, escaped final paths, and API uncertainty.
- [x] Existing POSIX prune and Git credential isolation behavior remains intact.
- [x] Focused and complete offline tests, compileall, pip, and diff checks pass.
- [x] Documentation, credential scan, scope audit, and independent review pass.
- [x] Human acceptance is covered by the standing ordered-fix authorization.
- [ ] The task is committed, merged into `yuto`, and only `yuto` is pushed.

## Verification Evidence

- Regression before implementation: `tests/test_windows_compatibility.py`
  passed `0/8`; credential and manifest saves failed without `os.fchmod`, the
  helper command builder and Windows prune backend did not exist, and an actual
  isolated Git fill failed from a helper path containing spaces.
- Persistence: both credential and manifest atomic writes pass when `os.fchmod`
  is unavailable, while existing mode, replacement-failure, memory-state, and
  cleanup checks remain `15/15`.
- Git integration: the managed command explicitly invokes the current Python
  interpreter with shell-safe paths; an isolated helper under a space-containing
  HOME executes successfully. Old/current managed values are removed from
  legacy backup/cleanup, while user values, repeated setup, rollback, recovery,
  status, and identity behavior remain intact.
- Windows prune: injected-handle tests cover regular deletion, missing paths,
  parent traversal, platform dispatch, directory/reparse rejection, escaped
  final paths, and API uncertainty. Production uses Win32 CreateFileW handles,
  attribute and final-path queries, and FileDispositionInfo; root, parent, and
  target handles remain held without DELETE sharing until disposition completes.
- Focused offline results: Windows compatibility `11/11`, POSIX prune `49/49`,
  Git isolation `33/33`, Git identity `6/6`, CLI surface `50/50`, and config
  permissions `15/15` passed.
- Complete offline suite: `pytest` collected `55` items and exited `0`.
  `python -m compileall -q .`, `python -m pip check`, and `git diff --check`
  passed in the `atomgit_cli` environment.
- Security and scope: all Git tests used isolated HOME/global config; the diff
  contains no real credential, generated artifact, remote request, or unrelated
  feature. No user Git configuration or remote repository state changed.
- Independent review: `APPROVED` with no P0-P3 findings. Residual risk is the
  absence of a real Windows runtime acceptance run; Win32 calls were checked
  against official Microsoft contracts and exercised through a strict injected
  backend, but this is not presented as live Windows evidence.
