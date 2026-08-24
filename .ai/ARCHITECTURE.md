# AtomGit CLI Architecture

This document describes the implemented architecture on `yuto`. It is a
runtime and ownership reference, not a roadmap. Observable CLI and legacy SDK
contracts remain compatibility surfaces; the native SDK parity surface is
implemented through the shared usecases below.

## Runtime Shape

```text
console script / python -m atomgit
                |
                v
       compatibility/cli facade
                |
                v
        interfaces/cli -> usecases -> domain -> core
                                      |
                                      v
                                adapters / infrastructure

python users
     |
     +--> legacy atomgit_hub facades -> sdk compatibility owners
     |
     +--> interfaces/sdk.AtomGitClient -> usecases -> adapters

Zsh completion -> lightweight CLI schema only
```

The seven responsibility directories are the target business architecture:

```text
src/atomgit/
├── core/            contracts, policies, ports, errors, parity registry
├── domain/          authentication, repository, transfer rules
├── usecases/        ordered business orchestration and final-state checks
├── interfaces/      CLI presentation and native SDK request/result mapping
├── adapters/        Hugging Face, AtomGit V5, and outbound technical ports
├── compatibility/  historical paths, identities, signatures, and seams
└── infrastructure/ config, runtime, filesystem, cache, Git, and lifecycle
```

The historical `atomgit.cli`, `atomgit.api`, and `atomgit_hub` paths remain
thin facades. Existing command names, Click objects, Python imports, function
identities, signatures, return conventions, exception behavior, entry paths,
and monkeypatch seams are tested compatibility contracts.

## Ownership And Dependency Direction

Business dependencies point inward:

```text
interfaces / compatibility -> usecases -> domain -> core
                                      -> adapters / infrastructure ports
```

`core` has no Click, Hugging Face, AtomGit V5, or concrete transport imports.
`domain` owns validation and success invariants without UI or network calls.
`usecases` own ordering, rollback/reconciliation, and final-state verification.
Interfaces translate user/API inputs and outputs but do not implement remote
business rules. Adapters and infrastructure own external calls and technical
state. `tests/structure_contract.py` and `tests/test_structure_guard.py`
fail closed on unowned modules, new forbidden edges, cycles, facade growth,
empty placeholders, stale artifact declarations, and missing parity metadata.

The extracted technical owners remain explicit and are not additional business
layers: `commands/` owns CLI command implementations, `adapters.atomgit_v5`
owns the V5 authentication/repository transport and response boundaries, and
`services/` keeps only the historical authentication/repository wrappers,
output, identities, and patch seams. `adapters.download` owns repository
enumeration, destination safety, transport, checksum, resume, manifest, and
prune behavior; `download/` keeps only historical method/export compatibility.
`adapters.upload` owns file, ordinary-directory, resumable, projection, retry,
and HF technical transfer behavior; `adapters.lfs` owns LFS protocol, pointer,
attributes, and recovery behavior; and `adapters.sdk_uploads` owns the legacy
SDK upload implementation. Historical `upload/`, `lfs/`, `lfs_pointer.py`, and
`sdk/uploads.py` paths are module aliases that retain signatures, identities,
and patch seams only. `lifecycle/` owns completion, installation provenance,
managed paths, and uninstall policy. These owners are connected through the
registered compatibility and adapter boundaries.

## Public Surfaces

- `atomgit.cli` and `atomgit.cli.__main__` preserve the Click schema, lazy
  imports, callback identities, output, prompts, progress, and exits.
- `atomgit.api.HuggingFaceAPI` and its singleton preserve the historical API
  surface and patch propagation.
- `atomgit_hub`, `atomgit.atomgit_hub`, and `atomgit` exports preserve the
  legacy HF-style SDK functions and signatures.
- `atomgit.interfaces.sdk.AtomGitClient` exposes native authentication,
  repository, upload, and download parity methods with structured
  `OperationResult` values and stable `AtomGitError` mapping.
- `core.parity.CAPABILITY_REGISTRY` classifies every general remote capability
  as `parity-required`, `cli-only`, or `sdk-only`; a parity-required row must
  name one shared usecase, CLI entry, SDK entry, result contract, and focused
  tests.

## External Boundaries And State

- Hugging Face Hub `1.1.7` calls are isolated behind the HF adapter and are
  checked against the installed signatures.
- AtomGit V5 requests, bounded response parsing, redirects, authentication
  headers, and error categories are isolated behind the V5 adapter.
- Configuration uses lazy reads, restrictive permissions, atomic writes, and
  the shared config object. Tokens, signed URLs, and secret-bearing causes do
  not enter logs, results, fixtures, or documentation.
- Runtime environment variables, Hugging Face timeout/progress state,
  temporary resources, and Git credential-helper changes are scoped and
  restored on success and failure.
- Public downloads may be anonymous. Explicit anonymous context never falls
  back to a saved token; write operations require an explicit or saved token.
- Repository IDs, repository type, visibility, revision, checksum, resume,
  prune, LFS, and final-state verification use shared policy and result
  contracts. CLI macOS metadata filtering remains an injected CLI policy.

## Transfer Invariants

- Directory uploads keep temporary projections alive through the dependent HF
  call and clean them afterward.
- Resumable uploads use revision- and destination-scoped metadata and restore
  global timeout/progress state.
- AtomGit LFS pointers are canonical ASCII bytes ending in one LF and are
  verified against the returned raw V5 blob before success is reported.
- Downloads reject unsafe paths, isolate redirect credentials, preserve
  revision in resume identity, verify optional checksums, and prune only files
  recorded by a successful manifest-scoped download.
- Non-main CLI revisions require an explicitly created and verified branch;
  unsupported SDK revision behavior remains accurately rejected.

## Packaging And Entry Paths

The project uses the explicit `src/` layout declared by both `pyproject.toml`
and `setup.py`. Source, PEP 660 editable, wheel, and sdist contracts preserve
the historical package/module set, the `atomgit` console entry point, both
Python module entry paths, and the top-level `atomgit_hub` compatibility module.
The distribution version is read from the single `version.py` authority.

## Verified Status And Residual Risk

The complete offline baseline is the mandatory gate:
`python tests/run_cli_baseline.py` currently passes 92 isolated cases. Compile,
dependency, packaging, import, security, portability, structure, and parity
contracts are included in that matrix; no live remote write is required for
the offline architecture and compatibility claims.

Controlled remote upload/download/checksum/LFS evidence is intentionally not
claimed in the local acceptance checkpoint. Multi-level namespace writes and
other remote behavior remain subject to the scoped test-repository
authorization. Black, isort, and Ruff report pre-existing repository-wide
formatting debt; new task-owned files must still be clean, and broad debt
removal is a separate authorized task.
