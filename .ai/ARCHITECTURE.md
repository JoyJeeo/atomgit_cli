# AtomGit CLI Architecture

## Runtime Shape

```text
console script / python -m atomgit
                |
                v
             cli.py
                |
                v
             api.py --------------------+
                |                       |
                v                       v
        huggingface_hub          config.py / utils.py

Python users
     |
     v
atomgit_hub.py -------------------------+
     |
     v
huggingface_hub / datasets
```

The CLI and SDK are parallel wrappers. `atomgit_hub.py` does not call
`api.py`, so shared behavior can drift unless it is deliberately centralized
or covered by shared contract tests.

## Modules

- `__main__.py`: `python -m atomgit` entry point.
- `__init__.py`: package metadata and public exports.
- `cli.py`: Click command tree, argument validation, user-facing output, and
  exit codes.
- `api.py`: CLI-facing authentication and repository operations.
- `atomgit_hub.py`: public HF-like Python SDK functions.
- `config.py`: in-memory configuration plus persistence to
  `~/.atomgit/config.json`.
- `utils.py`: validation, formatting, filesystem helpers, and Git credential
  helper installation/removal.
- `setup.py`: package metadata and `atomgit=atomgit.cli:cli` console entry.

## External Boundaries

- AtomGit user API: login identity validation.
- AtomGit HF-compatible endpoint: repository upload, download, and creation.
- User filesystem: configuration, cache, downloads, temporary upload data.
- Global Git configuration: host-specific credential helper registration.
- PyPI and GitHub: distribution channels, only when explicitly invoked.

## Important State

- `HF_ENDPOINT`, `HF_HUB_DISABLE_XET`, and `HF_HOME` are currently set during
  module import.
- Hugging Face progress-bar control and request timeout are process-global.
- Git credential-helper installation modifies user-global Git configuration.
- Git helper setup stores the previous host-specific values in the restrictive
  `~/.atomgit/git-helper-state.json` without writing the current login token,
  installs an empty reset plus the AtomGit helper for each AtomGit host, and
  restores the previous values on logout.
- Tokens are persisted locally and must never enter logs or fixtures.

## Repository ID Rules

The project accepts standard `owner/repo` IDs and advertises selected
multi-level AtomGit names. Normalization must be consistent across create,
upload, download, URL generation, and dataset loading. A validator accepting an
ID is not sufficient if downstream operations transform it differently.

## Upload Paths

- Single file: prefer HF `upload_file` with a full remote filename.
- Directory: use HF `upload_folder` with a normalized repository prefix.
- Large directory: use `HfApi.upload_large_folder`; authenticate through the
  `HfApi` instance according to the locked library signature.
- Temporary directories must remain alive until the dependent HF call returns
  and must be cleaned in `finally` or a context manager.

## Architectural Risks To Preserve In Task Context

- CLI and SDK duplicate endpoint, normalization, upload, and error behavior.
- Global timeout changes are unsafe unless restored.
- Mock upload objects can hide real HF signature incompatibilities.
- Remote branch semantics differ from Hugging Face Hub expectations; current
  upload interfaces reject non-main revisions.
- Multi-level ID normalization is shared, but write behavior still needs
  explicitly authorized remote acceptance evidence.
- Configuration and credential-helper operations affect user-owned state.

Do not perform a broad architectural rewrite as incidental work. Address these
risks through focused tasks and compatibility tests.
