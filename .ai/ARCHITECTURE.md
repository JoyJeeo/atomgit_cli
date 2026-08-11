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
- `runtime.py`: shared AtomGit endpoint, XET, and HF cache environment policy.
- `exceptions.py`: stable public SDK failure hierarchy.
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

- `HF_ENDPOINT`, `HF_HUB_DISABLE_XET`, and `HF_HOME` are set through the shared
  idempotent runtime policy before HF imports.
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
ID is not sufficient if downstream operations transform it differently. A
multi-level write also requires permission on the normalized physical
`owner-namespace/repo` namespace; the client must surface authorization failure
and must not report creation or upload success.

## Upload Paths

- Single file: prefer HF `upload_file` with a full remote filename.
- Directory: the CLI defaults to `HfApi.upload_large_folder`; authenticate
  through the `HfApi` instance according to the locked library signature.
  Every resumable upload uses a stable private projection keyed by source/
  repository/revision/prefix so HF metadata cannot drift across destinations.
  Because HF 1.1.7 has no large-folder `path_in_repo` argument, requested source
  content is placed below that prefix in the projection. Explicit ordinary mode
  uses `upload_folder` with the normalized repository prefix. Logical
  dataset resumable uploads use the same verified AtomGit model compatibility
  route as dataset creation and ordinary transfer.
- Opt-in resumable LFS repair keeps repository policy outside the upload
  projection: the child returns only validated extension patterns, while the
  parent uses a private one-file buffer, an immutable revision SHA, and
  `parent_commit` to append and verify root `.gitattributes` before retrying the
  same batch. The wildcard is repository-wide and is printed before mutation.
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
