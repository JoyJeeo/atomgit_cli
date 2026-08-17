# AtomGit CLI 1.1.1

This release makes shell completion environment-owned and adds a complete,
official uninstall lifecycle for ordinary users.

## Highlights

- Zsh completion now belongs to the active conda environment. Activation loads
  that environment's live Click schema, while deactivation removes its
  `_atomgit_completion` function and `compdef` binding before another
  environment loads.
- New installs no longer write global completion under `~/.atomgit` or modify
  `.zshrc`. Existing 1.1.0 global completion is migrated only after explicit
  confirmation, with the original configuration backed up and unrelated bytes,
  mode, and final-newline state preserved.
- Added `atomgit uninstall`, which displays the interpreter, environment root,
  package version, and exact managed targets before confirmation. The official
  `uninstall.sh` curl entrypoint also works idempotently after a prior direct
  pip removal.
- Official uninstall preserves AtomGit configuration, credentials, caches,
  repositories, and unrelated conda files. Managed-path removal rejects final
  or parent symlinks and concurrent changes.
- A standalone activation hook detects non-official direct pip removal and
  prints exact cleanup guidance without deleting or rewriting anything.
- Non-conda and venv installation remain supported; automatic environment
  completion is skipped with an accurate message.
- The complete offline development floor now covers 74 scripts and 78
  invariants, including real Zsh environment switching and both uninstall
  states.

## Known Limitations

- Automatic managed completion requires conda and Zsh. Other supported Python
  environments remain usable without automatic completion.
- A child command cannot unload completion already loaded in its parent shell;
  completion removal and package uninstall therefore print an environment
  reactivation or `exec zsh` instruction.
- `install.sh` and `uninstall.sh` support POSIX/macOS/Linux. Windows users must
  follow the README procedure for the checksummed universal wheel.
- Release discovery still depends on GitHub API availability and rate limits
  and never falls back to PyPI, branch archives, or historical `v...` Releases.

See `CHANGELOG.md` for the full version history and `docs/release.md` for the
artifact and verification policy.
