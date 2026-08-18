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

Zsh completion adapter
     |
     v
lightweight cli.py schema -> live Click candidates
```

The CLI and SDK are parallel wrappers. `atomgit_hub.py` does not call
`api.py`, so shared behavior can drift unless it is deliberately centralized
or covered by shared contract tests.

## Modules

- `__main__.py`: `python -m atomgit` entry point.
- `__init__.py`: package metadata and public exports; completion requests skip
  eager business and SDK exports while retaining runtime environment policy.
- `cli.py`: Click command tree, argument validation, user-facing output, and
  exit codes; API and utility dependencies resolve only when callbacks run.
- `cli_contracts.py`: historical path for lightweight upload constants owned by
  `upload.contracts`, preserving the completion-safe CLI import surface.
- `completion.py`: historical facade for lifecycle-owned dynamic Zsh adapter
  generation and atomic conda-environment hook management.
- `uninstaller.py`: historical facade for lifecycle-owned uninstall policy.
- `api.py`: historical CLI-facing concrete client and singleton; service,
  download, and upload methods resolve from owned mixins while LFS policy and
  transfer remain local for the later LFS Domain step.
- `atomgit_hub.py`: public HF-like Python SDK functions.
- `runtime.py`: historical facade for the owned infrastructure runtime policy.
- `version.py`: the single authoritative stable distribution version source.
- `release.py`: standard-library Release resolver, asset/checksum/wheel metadata
  validator, target-interpreter installer, post-install verification, and
  `atomgit update` policy shared with the POSIX bootstrap contract.
- `exceptions.py`: stable public SDK failure hierarchy.
- `config.py`: historical facade preserving the shared configuration class and
  singleton.
- `utils.py`: historical utility facade preserving public and patch seams.
- `infrastructure/`: owned runtime/config, validation, output, filesystem,
  cache, and Git credential-helper implementations plus one internal utility
  aggregation surface.
- `lifecycle/`: owned environment/origin policy, exact managed paths, completion
  transactions, and safe uninstall implementation.
- `services/`: owned bounded authentication and repository V5 management,
  including create/list/visibility/delete/branch final-state verification.
- `download/`: owned CLI API download service, transport, integrity, manifest,
  resume, and prune implementation; SDK downloads remain outside this package.
- `upload/`: owned CLI API upload service, ordinary transfer, resumable
  orchestration, projection, error policy, and lightweight contracts; LFS
  transfer/policy and SDK upload remain outside this package.
- `setup.py`: package metadata and `atomgit=atomgit.cli:cli` console entry.

## External Boundaries

- AtomGit user API: login identity validation.
- AtomGit HF-compatible endpoint: repository upload, download, and creation.
- User filesystem: configuration, cache, downloads, temporary upload data.
- Global Git configuration: host-specific credential helper registration.
- GitHub Releases API/assets: the only official AtomGit CLI distribution channel;
  the local build helper contains no PyPI/twine publication path. Third-party
  dependencies may still resolve from the user's configured pip index.

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
- Zsh completion queries the current Click tree on every Tab without loading
  business dependencies, reading credentials, accessing the network, or
  creating configuration. Each active conda environment owns only its adapter
  and activation/deactivation hooks; environment switches unload the previous
  Click function before loading the next. Legacy global `.zshrc` state migrates
  only after confirmation. Exact-path uninstall preserves user configuration,
  and a hook left after direct pip removal warns without mutating state.

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
  Selected files are deterministically grouped into configurable 1..20-file
  outer batches after ignore filtering, with 20 retained as the default.
  Every resumable upload uses a stable private projection keyed by source/
  repository/revision/prefix/batch size and index so HF metadata cannot drift
  across destinations or incompatible outer groupings.
  Because HF 1.1.7 has no large-folder `path_in_repo` argument, requested source
  content is placed below that prefix in the projection. Explicit ordinary mode
  uses `upload_folder` with the normalized repository prefix. Logical
  dataset resumable uploads use the same verified AtomGit model compatibility
  route as dataset creation and ordinary transfer.
- Opt-in resumable LFS configuration keeps repository policy outside the upload
  projection. After server mode selection, and again at preupload/commit for
  cached metadata, the child gates LFS work and returns only unconfirmed,
  validated extension patterns. The parent uses a private one-file buffer, an
  immutable revision SHA, and `parent_commit` to check, append, and verify root
  `.gitattributes` before retrying the same batch. Confirmed patterns are reused
  across outer batches. The wildcard is repository-wide and is printed before
  mutation. The same transaction retains the oversized-regular repair path.
- Temporary directories must remain alive until the dependent HF call returns
  and must be cleaned in `finally` or a context manager.
- All AtomGit upload paths enter a context-gated wrapper around the locked HF
  commit serializer. LFS object transfer remains unchanged, but each `lfsFile`
  metadata record is committed as an exact canonical pointer `file` payload to
  bypass the service's missing-final-LF materialization. The client then reads
  the raw V5 contents blob at the returned commit and compares exact bytes;
  resumable ambiguous commits verify reconciled paths before marking their HF
  metadata committed. The wrapper is inactive outside AtomGit upload contexts.

## Source And Packaging Layout

Production modules live in `src/atomgit` with their existing flat module shape.
The SDK implementation remains `src/atomgit/atomgit_hub.py`; the separately
packaged `src/atomgit_hub.py` compatibility proxy preserves the historical
top-level import and forwards private monkeypatch seams to that single
implementation. `pyproject.toml` and `setup.py` both declare the exact `src`
package/module mapping. No domain extraction or facade conversion is combined
with this mechanical migration.

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

## Structural Refactor Gate

The flat public modules plus the extracted infrastructure, lifecycle, services,
and download packages are the
implemented architecture. The approved
long-term dependency direction is facade/CLI/SDK to services, transfers,
lifecycle, or distribution, then to infrastructure/LFS, with only the
registered special directions. `tests/structure_contract.py` assigns every
current module an owner and records current edges, public surfaces, artifact
contents, and exact legacy size ceilings. `tests/test_structure_guard.py`
requires debt removal and declaration tightening in the same change, and
rejects new edges, new forbidden directions, facade growth, cycles, unowned
modules, and empty placeholders.

Infrastructure, lifecycle, authentication/repository service, CLI API download
extraction, and CLI API upload extraction are fail-closed through exact
nested-module, artifact, facade-debt, identity, and old-path patch-seam
contracts. The remaining forbidden-direction exception is `cli -> api`; it is
explicit migration debt, not an approved pattern for new code. Source/editable
installation detection now has one lifecycle owner shared by update and
uninstall policy, and the package-absent POSIX uninstall fallback retains
executable manifest and safety parity. `atomgit.api.HuggingFaceAPI` and its
global singleton keep their historical identities while moved methods have
service provenance and old-path module-object patches reach their former call
sites. Download and upload methods and helpers likewise retain old-path
identities and patch propagation while SDK download/upload and LFS ownership
remain pending. API and CLI facade conversion remains isolated in later Issues.
