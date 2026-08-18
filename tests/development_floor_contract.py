"""Declarative capability and invariant ledger for the development floor."""

import re
from collections import defaultdict
from pathlib import Path


FORMAL_DEFINITION = (
    "AtomGit CLI 的所有已实现能力，都必须拥有稳定的能力登记、明确的行为不变量、"
    "可执行的离线回归测试、必要的依赖和安全契约，以及在适用时的受控远程证据。"
    "任何开发活动都必须证明受影响的旧能力未退化，并将新增能力纳入同一套基线。"
    "未通过开发底线的变更，不得进入 Issue 完成、合并、发布或继续扩展开发阶段。"
)

BASELINE_CAPABILITY_COUNT = 26
BASELINE_INVARIANT_COUNT = 102

_CAPABILITY_ID = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*$")
_INVARIANT_ID = re.compile(r"^[A-Z][A-Z0-9]*-[0-9]{3}$")
_RISKS = {"critical", "high", "medium", "low"}
_EVIDENCE_CATEGORIES = {
    "offline-contract",
    "dependency-contract",
    "security-contract",
    "packaging-smoke",
    "portability-contract",
    "controlled-remote",
}
_REMOTE_EVIDENCE = {
    "not-applicable",
    "controlled",
    "partial",
    "required-before-claim",
}
_REQUIRED_CAPABILITY_FIELDS = {
    "id",
    "name",
    "risk",
    "entrypoints",
    "invariants",
    "tests",
    "documents",
    "evidence",
    "remote_evidence",
}
_REQUIRED_INVARIANT_FIELDS = {"id", "statement", "tests"}


def _invariant(invariant_id, statement, *tests):
    return {
        "id": invariant_id,
        "statement": statement,
        "tests": tuple(tests),
    }


def _capability(
    capability_id,
    name,
    risk,
    entrypoints,
    invariants,
    tests,
    documents,
    evidence=("offline-contract",),
    remote_evidence="not-applicable",
):
    return {
        "id": capability_id,
        "name": name,
        "risk": risk,
        "entrypoints": tuple(entrypoints),
        "invariants": tuple(invariants),
        "tests": tuple(tests),
        "documents": tuple(documents),
        "evidence": tuple(evidence),
        "remote_evidence": remote_evidence,
    }


CAPABILITY_REGISTRY = {
    "FLOOR-REGISTRY": _capability(
        "FLOOR-REGISTRY",
        "Development-floor registry and mandatory gate",
        "critical",
        ("tests/run_cli_baseline.py", ".ai/DEVELOPMENT_FLOOR.md"),
        (
            _invariant(
                "FLOOR-001",
                "Every implemented capability has a stable, complete registry entry.",
                "test_development_floor.py",
            ),
            _invariant(
                "FLOOR-002",
                "Every offline regression maps to at least one capability and every invariant has executable evidence.",
                "test_development_floor.py",
                "test_cli_baseline_guard.py",
            ),
            _invariant(
                "FLOOR-003",
                "A failed or unrun complete baseline blocks delivery and further feature expansion.",
                "test_development_floor.py",
                "test_cli_feature_baseline.py",
            ),
            _invariant(
                "FLOOR-005",
                "Structural refactors preserve registered behavior while legacy ownership and dependency debt may shrink but never grow.",
                "test_structure_guard.py",
            ),
            _invariant(
                "FLOOR-006",
                "Build and tool metadata plus exact legacy debt remain executable and fail closed when configuration or debt drifts.",
                "test_packaging_metadata.py",
            ),
            _invariant(
                "FLOOR-007",
                "The src-layout migration fails closed when a production module, compatibility shim, artifact path, or source provenance drifts.",
                "test_src_layout_migration.py",
            ),
            _invariant(
                "FLOOR-008",
                "Infrastructure implementations have exact owners while historical utility, config, and runtime facades preserve symbols, identities, patch seams, and monotonic debt.",
                "test_infrastructure_utils_ownership.py",
                "test_structure_guard.py",
            ),
            _invariant(
                "FLOOR-009",
                "Lifecycle implementations have exact owners while historical completion and uninstaller facades preserve symbols, identities, patch seams, and monotonic debt.",
                "test_environment_lifecycle_ownership.py",
                "test_structure_guard.py",
            ),
            _invariant(
                "FLOOR-010",
                "Authentication and repository implementations have exact service owners while the historical API class, singleton, methods, helpers, signatures, and patch seams remain stable.",
                "test_auth_repository_services_ownership.py",
                "test_structure_guard.py",
            ),
            _invariant(
                "FLOOR-011",
                "CLI API download implementations have exact transfer owners while historical API symbols, methods, signatures, patch seams, and structural debt remain stable.",
                "test_download_domain_ownership.py",
                "test_structure_guard.py",
            ),
            _invariant(
                "FLOOR-012",
                "CLI API upload implementations have exact transfer owners while historical API symbols, methods, signatures, patch seams, LFS boundaries, and structural debt remain stable.",
                "test_upload_domain_ownership.py",
                "test_structure_guard.py",
            ),
        ),
        (
            "test_auth_repository_services_ownership.py",
            "test_development_floor.py",
            "test_download_domain_ownership.py",
            "test_environment_lifecycle_ownership.py",
            "test_cli_baseline_guard.py",
            "test_cli_feature_baseline.py",
            "test_packaging_metadata.py",
            "test_src_layout_migration.py",
            "test_infrastructure_utils_ownership.py",
            "test_structure_guard.py",
            "test_upload_domain_ownership.py",
        ),
        ("docs/development_floor.md", ".ai/DEVELOPMENT_FLOOR.md"),
    ),
    "CLI-SURFACE": _capability(
        "CLI-SURFACE",
        "Exact public CLI command and parameter surface",
        "high",
        ("atomgit", "python -m atomgit"),
        (
            _invariant(
                "CLI-001",
                "Public commands, groups, options, arguments, defaults, types, and flags match the registered schema.",
                "test_cli_feature_baseline.py",
                "test_cli_baseline_guard.py",
            ),
            _invariant(
                "CLI-002",
                "Every public command has usable help and remains installable through both entry points.",
                "test_cli_feature_baseline.py",
                "test_wheel_smoke.py",
            ),
            _invariant(
                "CLI-003",
                "Zsh completion is derived from the live Click schema without executing callbacks or importing business dependencies.",
                "test_shell_completion.py",
            ),
            _invariant(
                "CLI-004",
                "The Release-based update command exposes strict version and force-reinstall options without changing existing command schemas.",
                "test_update.py",
                "test_cli_feature_baseline.py",
            ),
            _invariant(
                "CLI-005",
                "The public uninstall command shows interpreter, environment, version, and exact managed targets before confirmation or automated dispatch.",
                "test_uninstaller.py",
                "test_cli_feature_baseline.py",
            ),
            _invariant(
                "CLI-006",
                "Representative deterministic CLI scenarios preserve exact stdout, stderr, exit status, Click exception category, prompts, and redaction.",
                "test_refactor_behavior_guard.py",
            ),
        ),
        (
            "test_cli_feature_baseline.py",
            "test_refactor_behavior_guard.py",
            "test_cli_baseline_guard.py",
            "test_cli_surface.py",
            "test_shell_completion.py",
            "test_wheel_smoke.py",
            "test_update.py",
            "test_uninstaller.py",
        ),
        ("docs/cli_feature_baseline.md", "docs/testing.md"),
        ("offline-contract", "packaging-smoke"),
    ),
    "CLI-DISPATCH": _capability(
        "CLI-DISPATCH",
        "CLI leaf-command dispatch and exit semantics",
        "high",
        ("cli.py:cli",),
        (
            _invariant(
                "DISPATCH-001",
                "Every public leaf command reaches an isolated successful dispatch.",
                "test_cli_feature_baseline.py",
                "test_cli_surface.py",
            ),
            _invariant(
                "DISPATCH-002",
                "Missing, duplicate, or stale leaf dispatch registration fails the baseline.",
                "test_cli_baseline_guard.py",
            ),
            _invariant(
                "DISPATCH-003",
                "Update dispatch targets the running interpreter and refuses source installations without Git mutation.",
                "test_update.py",
            ),
            _invariant(
                "DISPATCH-004",
                "Uninstall dispatch confirms by default and passes only the displayed current-interpreter plan to package removal.",
                "test_uninstaller.py",
                "test_cli_feature_baseline.py",
            ),
            _invariant(
                "DISPATCH-005",
                "Covered refactor-sensitive leaves preserve their exact target, arguments, call count, and ordering.",
                "test_refactor_behavior_guard.py",
            ),
        ),
        (
            "test_cli_feature_baseline.py",
            "test_refactor_behavior_guard.py",
            "test_cli_surface.py",
            "test_cli_baseline_guard.py",
            "test_update.py",
            "test_uninstaller.py",
        ),
        ("docs/cli_feature_baseline.md",),
    ),
    "AUTH-CONFIG": _capability(
        "AUTH-CONFIG",
        "Authentication and private local configuration",
        "critical",
        ("atomgit login", "atomgit logout", "atomgit whoami", "atomgit config-show"),
        (
            _invariant(
                "AUTH-001",
                "Credentials are persisted only after bounded remote validation and are never printed.",
                "test_login_config.py",
                "test_login_error_semantics.py",
                "test_login_response_bound.py",
            ),
            _invariant(
                "AUTH-002",
                "Configuration reads are lazy and writes are private, atomic, and recover safely from corrupt state.",
                "test_config_permissions.py",
                "test_login_config.py",
            ),
            _invariant(
                "AUTH-003",
                "Authentication, permission, rate-limit, server, network, and malformed responses retain distinct exit semantics.",
                "test_auth_status_semantics.py",
                "test_login_error_semantics.py",
            ),
        ),
        (
            "test_auth_repository_services_ownership.py",
            "test_auth_status_semantics.py",
            "test_config_permissions.py",
            "test_login_config.py",
            "test_login_error_semantics.py",
            "test_login_response_bound.py",
            "test_cli_surface.py",
        ),
        ("docs/architecture.md", "docs/cli_feature_baseline.md"),
        ("offline-contract", "security-contract", "controlled-remote"),
        "partial",
    ),
    "GIT-CREDENTIAL": _capability(
        "GIT-CREDENTIAL",
        "Scoped Git credential-helper integration",
        "critical",
        ("atomgit login", "atomgit logout", "atomgit config-show"),
        (
            _invariant(
                "GITCRED-001",
                "AtomGit host helpers are installed without destroying unrelated global Git configuration.",
                "test_git_credentials_isolation.py",
            ),
            _invariant(
                "GITCRED-002",
                "Logout restores the prior helper chain transactionally and the helper uses cached verified identity without network access.",
                "test_git_credentials_isolation.py",
                "test_git_helper_identity.py",
            ),
        ),
        ("test_git_credentials_isolation.py", "test_git_helper_identity.py"),
        ("docs/architecture.md", "docs/cli_feature_baseline.md"),
        ("offline-contract", "security-contract", "portability-contract"),
    ),
    "REPO-MANAGEMENT": _capability(
        "REPO-MANAGEMENT",
        "Repository create, list, visibility, information, and delete",
        "critical",
        (
            "atomgit repo create",
            "atomgit repo list",
            "atomgit repo visibility",
            "atomgit repo delete",
        ),
        (
            _invariant(
                "REPO-001",
                "Repository creation uses explicit type and visibility, supports explicit idempotency, and verifies final visibility.",
                "test_create_contract.py",
                "test_create_visibility.py",
            ),
            _invariant(
                "REPO-002",
                "List and repository information distinguish empty, missing, authentication, permission, and malformed responses.",
                "test_repo_list.py",
                "test_repo_info_stub.py",
            ),
            _invariant(
                "REPO-003",
                "Visibility changes and permanent deletion require explicit input and verify the final remote state before success.",
                "test_repo_visibility.py",
                "test_repo_delete.py",
            ),
        ),
        (
            "test_auth_repository_services_ownership.py",
            "test_create_contract.py",
            "test_create_visibility.py",
            "test_repo_delete.py",
            "test_repo_info_stub.py",
            "test_repo_list.py",
            "test_repo_visibility.py",
        ),
        ("docs/cli_feature_baseline.md", "docs/architecture.md"),
        ("offline-contract", "security-contract", "controlled-remote"),
        "controlled",
    ),
    "REVISION": _capability(
        "REVISION",
        "Branch creation and upload revision protection",
        "high",
        ("atomgit repo branch create", "atomgit upload --revision"),
        (
            _invariant(
                "REV-001",
                "Branch creation resolves the source commit and verifies the created branch before success.",
                "test_branch_create.py",
            ),
            _invariant(
                "REV-002",
                "Unsupported or unverified upload revisions fail before upload and SDK upload remains main-only.",
                "test_api_revision_guard.py",
                "test_revision_rejection.py",
            ),
        ),
        (
            "test_api_revision_guard.py",
            "test_auth_repository_services_ownership.py",
            "test_branch_create.py",
            "test_revision_rejection.py",
        ),
        ("docs/cli_feature_baseline.md", "docs/upload_command_analysis.md"),
        ("offline-contract", "controlled-remote"),
        "controlled",
    ),
    "UPLOAD-FILE": _capability(
        "UPLOAD-FILE",
        "Single-file upload",
        "high",
        ("atomgit upload FILE", "AtomGitAPI.upload_folder"),
        (
            _invariant(
                "UPFILE-001",
                "A normal single file is streamed from its source without a full local copy and reaches the exact remote path.",
                "test_upload_file_no_copy.py",
                "test_upload_path_in_repo.py",
            ),
            _invariant(
                "UPFILE-002",
                "Compatibility fallback uses a unique temporary directory that survives the call and is always cleaned.",
                "test_upload_fallback_temp.py",
            ),
            _invariant(
                "UPFILE-003",
                "Invalid types, option conflicts, metadata files, and symlinks fail before credentials or remote calls.",
                "test_upload_validation.py",
                "test_upload_symlink_safety.py",
            ),
        ),
        (
            "test_upload_file_no_copy.py",
            "test_upload_fallback_temp.py",
            "test_upload_path_in_repo.py",
            "test_upload_repo_type.py",
            "test_upload_symlink_safety.py",
            "test_upload_validation.py",
        ),
        ("docs/cli_feature_baseline.md", "docs/upload_command_analysis.md"),
        ("offline-contract", "security-contract", "controlled-remote"),
        "controlled",
    ),
    "UPLOAD-FOLDER": _capability(
        "UPLOAD-FOLDER",
        "Ordinary directory upload",
        "high",
        ("atomgit upload DIRECTORY --no-resumable", "AtomGitAPI.upload_directory"),
        (
            _invariant(
                "UPFOLDER-001",
                "Ignore rules, repository prefixes, type, workers, batches, and progress settings reach the ordinary upload boundary exactly.",
                "test_upload_ignore.py",
                "test_upload_path_in_repo.py",
                "test_upload_batching.py",
                "test_upload_progress.py",
                "test_upload_repo_type.py",
            ),
            _invariant(
                "UPFOLDER-002",
                "Directory upload rejects unsafe trees and classifies failures without false success.",
                "test_upload_symlink_safety.py",
                "test_upload_error_handling.py",
                "test_upload_error_classify.py",
            ),
        ),
        (
            "test_upload_batching.py",
            "test_upload_error_classify.py",
            "test_upload_error_handling.py",
            "test_upload_ignore.py",
            "test_upload_path_in_repo.py",
            "test_upload_progress.py",
            "test_upload_repo_type.py",
            "test_upload_symlink_safety.py",
            "test_upload_validation.py",
        ),
        ("docs/cli_feature_baseline.md", "docs/upload_command_analysis.md"),
        ("offline-contract", "security-contract", "controlled-remote"),
        "controlled",
    ),
    "UPLOAD-RESUMABLE": _capability(
        "UPLOAD-RESUMABLE",
        "Isolated resumable directory upload",
        "critical",
        ("atomgit upload DIRECTORY --resumable", "AtomGitAPI.upload_directory"),
        (
            _invariant(
                "RESUMEUP-001",
                "Stable private projections isolate metadata by source, repository, revision, prefix, batch size, and batch index.",
                "test_upload_resumable.py",
                "test_upload_path_in_repo.py",
            ),
            _invariant(
                "RESUMEUP-002",
                "Timeout, retry, batch reduction, reconciliation, and parent termination never publish false success or stale progress.",
                "test_resumable_commit_policy.py",
                "test_resumable_recovery.py",
                "test_upload_progress.py",
            ),
            _invariant(
                "RESUMEUP-003",
                "Model and dataset routes, worker statistics, and resumable metadata remain distinct and deterministic.",
                "test_dataset_resumable_route.py",
                "test_resumable_stats.py",
                "test_upload_resumable.py",
            ),
        ),
        (
            "test_dataset_resumable_route.py",
            "test_resumable_commit_policy.py",
            "test_resumable_recovery.py",
            "test_resumable_stats.py",
            "test_upload_batching.py",
            "test_upload_path_in_repo.py",
            "test_upload_progress.py",
            "test_upload_resumable.py",
        ),
        ("docs/architecture.md", "docs/upload_command_analysis.md"),
        ("offline-contract", "security-contract", "controlled-remote"),
        "controlled",
    ),
    "UPLOAD-LFS": _capability(
        "UPLOAD-LFS",
        "LFS preupload, canonical pointer, and repository attributes",
        "critical",
        ("resumable LFS preupload", "atomgit upload --auto-configure-lfs"),
        (
            _invariant(
                "LFS-001",
                "LFS batch responses are validated and only bounded retryable failures return to preupload.",
                "test_lfs_preupload_policy.py",
            ),
            _invariant(
                "LFS-002",
                "Committed LFS metadata is serialized and remotely reconciled as the exact canonical pointer payload.",
                "test_canonical_lfs_pointer.py",
                "test_resumable_commit_policy.py",
            ),
            _invariant(
                "LFS-003",
                "Automatic attributes are opt-in, action-scoped, concurrency-safe, and preserve existing repository content.",
                "test_auto_configure_lfs.py",
            ),
        ),
        (
            "test_auto_configure_lfs.py",
            "test_canonical_lfs_pointer.py",
            "test_lfs_preupload_policy.py",
            "test_resumable_commit_policy.py",
        ),
        ("docs/architecture.md", "docs/upload_command_analysis.md"),
        ("offline-contract", "security-contract", "controlled-remote"),
        "partial",
    ),
    "UPLOAD-LFS-RECOVERY": _capability(
        "UPLOAD-LFS-RECOVERY",
        "Pathological LFS flow recovery",
        "high",
        ("isolated resumable LFS PUT",),
        (
            _invariant(
                "LFSREC-001",
                "Only a persistently degraded object is replaced after stable peer or self evidence and a material time benefit.",
                "test_lfs_slow_flow_recovery.py",
            ),
            _invariant(
                "LFSREC-002",
                "Replacement caps, cooldowns, improvement checks, generations, and the peer-wide probe prevent loops and reconnect storms.",
                "test_lfs_slow_flow_recovery.py",
            ),
        ),
        ("test_lfs_slow_flow_recovery.py",),
        ("docs/architecture.md", "docs/upload_command_analysis.md"),
        ("offline-contract", "controlled-remote"),
        "partial",
    ),
    "DOWNLOAD-SNAPSHOT": _capability(
        "DOWNLOAD-SNAPSHOT",
        "Whole-repository download and managed checkout",
        "critical",
        ("atomgit download", "AtomGitAPI.download_repo"),
        (
            _invariant(
                "DLSNAP-001",
                "Repository type resolution and complete remote file listing precede any local mutation.",
                "test_download_contract.py",
                "test_download_repo_type_resolution.py",
            ),
            _invariant(
                "DLSNAP-002",
                "Existing-file, force, retry, and cleanup policies preserve the original target until a complete replacement is ready.",
                "test_download_existing_file_policy.py",
                "test_download_recovery.py",
                "test_download_standard_cleanup.py",
            ),
            _invariant(
                "DLSNAP-003",
                "Prune removes only previously managed files after a complete successful download and advances its manifest atomically.",
                "test_download_prune.py",
                "test_download_manifest_concurrency.py",
            ),
        ),
        (
            "test_download_contract.py",
            "test_download_existing_file_policy.py",
            "test_download_manifest_concurrency.py",
            "test_download_prune.py",
            "test_download_recovery.py",
            "test_download_repo_type_resolution.py",
            "test_download_standard_cleanup.py",
        ),
        ("docs/architecture.md", "docs/cli_feature_baseline.md"),
        ("offline-contract", "security-contract", "controlled-remote"),
        "controlled",
    ),
    "DOWNLOAD-FILE": _capability(
        "DOWNLOAD-FILE",
        "Single-file CLI and SDK download",
        "critical",
        ("atomgit download-file", "AtomGitAPI.download_file", "atomgit_hub.download_file"),
        (
            _invariant(
                "DLFILE-001",
                "Single-file download uses the exact requested repository type, filename, and destination policy.",
                "test_cli_download_file.py",
                "test_download_contract.py",
            ),
            _invariant(
                "DLFILE-002",
                "Force, checksum, resume, Unicode, and failure cleanup retain atomic target replacement semantics.",
                "test_download_resume_cli.py",
                "test_download_unicode_metadata.py",
                "test_download_standard_cleanup.py",
            ),
        ),
        (
            "test_cli_download_file.py",
            "test_download_contract.py",
            "test_download_resume_cli.py",
            "test_download_standard_cleanup.py",
            "test_download_unicode_metadata.py",
        ),
        ("docs/architecture.md", "docs/cli_feature_baseline.md"),
        ("offline-contract", "security-contract", "controlled-remote"),
        "controlled",
    ),
    "DOWNLOAD-INTEGRITY": _capability(
        "DOWNLOAD-INTEGRITY",
        "Download framing, checksum, resume, and atomic replacement",
        "critical",
        ("atomgit download --verify-checksum", "atomgit download --resume"),
        (
            _invariant(
                "DLINT-001",
                "Strong metadata, expected size, response framing, and final digest must agree before target replacement.",
                "test_download_checksum.py",
                "test_download_raw_integrity.py",
            ),
            _invariant(
                "DLINT-002",
                "Resumed transfers validate range semantics, keep private partial state, and revalidate complete bytes.",
                "test_download_resume_cli.py",
            ),
            _invariant(
                "DLINT-003",
                "Incomplete or retry-exhausted downloads clean temporary output and preserve any pre-existing target.",
                "test_download_recovery.py",
                "test_download_standard_cleanup.py",
            ),
        ),
        (
            "test_download_checksum.py",
            "test_download_raw_integrity.py",
            "test_download_recovery.py",
            "test_download_resume_cli.py",
            "test_download_standard_cleanup.py",
            "test_download_unicode_metadata.py",
        ),
        ("docs/architecture.md", "docs/cli_feature_baseline.md"),
        ("offline-contract", "security-contract", "controlled-remote"),
        "controlled",
    ),
    "DOWNLOAD-SECURITY": _capability(
        "DOWNLOAD-SECURITY",
        "Download path, redirect, credential, and prune safety",
        "critical",
        ("atomgit download", "atomgit download-file"),
        (
            _invariant(
                "DLSEC-001",
                "Absolute, traversal, control-character, symlink, reparse-point, and out-of-root targets fail before writes.",
                "test_download_path_security.py",
                "test_download_prune.py",
            ),
            _invariant(
                "DLSEC-002",
                "Credentials never cross an untrusted redirect or leak from unrelated HF environment state.",
                "test_download_redirect_security.py",
                "test_anonymous_token_isolation.py",
            ),
            _invariant(
                "DLSEC-003",
                "Managed-checkout locking serializes one checkout without blocking independent identities.",
                "test_download_manifest_concurrency.py",
            ),
        ),
        (
            "test_anonymous_token_isolation.py",
            "test_download_manifest_concurrency.py",
            "test_download_path_security.py",
            "test_download_prune.py",
            "test_download_redirect_security.py",
        ),
        ("docs/architecture.md", "docs/cli_feature_baseline.md"),
        (
            "offline-contract",
            "security-contract",
            "portability-contract",
            "controlled-remote",
        ),
        "controlled",
    ),
    "SDK-DOWNLOAD": _capability(
        "SDK-DOWNLOAD",
        "Python SDK snapshot, file, URL, and dataset download",
        "high",
        (
            "atomgit_hub.snapshot_download",
            "atomgit_hub.download_file",
            "atomgit_hub.hub_download_url",
            "atomgit_hub.load_dataset",
        ),
        (
            _invariant(
                "SDKDL-001",
                "SDK download functions normalize IDs, isolate AtomGit authentication, and pass only locked-library parameters.",
                "test_hf_api_contract.py",
                "test_repo_id_contract.py",
            ),
            _invariant(
                "SDKDL-002",
                "Dataset loading uses the AtomGit endpoint and cache policy while stable SDK errors preserve actionable categories.",
                "test_load_dataset.py",
                "test_sdk_exceptions.py",
            ),
        ),
        (
            "test_hf_api_contract.py",
            "test_load_dataset.py",
            "test_repo_id_contract.py",
            "test_sdk_exceptions.py",
        ),
        ("docs/architecture.md", "README.md"),
        ("offline-contract", "dependency-contract", "controlled-remote"),
        "partial",
    ),
    "SDK-UPLOAD": _capability(
        "SDK-UPLOAD",
        "Python SDK folder upload",
        "high",
        ("atomgit_hub.upload_folder",),
        (
            _invariant(
                "SDKUP-001",
                "Public upload parameters are forwarded or explicitly rejected according to the locked dependency contract.",
                "test_sdk_upload_parameters.py",
            ),
            _invariant(
                "SDKUP-002",
                "Prefix projections survive the complete upload call, clean afterward, and restore timeout and progress state on all exits.",
                "test_sdk_upload_lifetime.py",
                "test_sdk_upload_timeout.py",
            ),
        ),
        (
            "test_sdk_upload_lifetime.py",
            "test_sdk_upload_parameters.py",
            "test_sdk_upload_timeout.py",
        ),
        ("docs/architecture.md", "README.md"),
        ("offline-contract", "dependency-contract", "controlled-remote"),
        "partial",
    ),
    "SDK-REPO": _capability(
        "SDK-REPO",
        "Python SDK repository creation and stable exceptions",
        "high",
        ("atomgit_hub.create_repository",),
        (
            _invariant(
                "SDKREPO-001",
                "SDK repository creation normalizes IDs, preserves model/dataset semantics, and rejects unsupported public creation.",
                "test_sdk_create_contract.py",
                "test_repo_id_contract.py",
            ),
            _invariant(
                "SDKREPO-002",
                "SDK failures use the public AtomGit exception hierarchy with redacted causes.",
                "test_sdk_exceptions.py",
            ),
        ),
        (
            "test_repo_id_contract.py",
            "test_sdk_create_contract.py",
            "test_sdk_exceptions.py",
        ),
        ("docs/architecture.md", "README.md"),
        ("offline-contract", "controlled-remote"),
        "partial",
    ),
    "REPO-ID": _capability(
        "REPO-ID",
        "Repository ID validation and normalization",
        "critical",
        ("all CLI and SDK repository boundaries",),
        (
            _invariant(
                "REPOID-001",
                "Every public boundary accepts and rejects the same repository ID grammar before transport.",
                "test_repo_id_contract.py",
            ),
            _invariant(
                "REPOID-002",
                "Multi-level logical IDs map consistently across create, upload, download, URL, and dataset routes.",
                "test_repo_id_contract.py",
                "test_create_contract.py",
                "test_upload_repo_type.py",
                "test_load_dataset.py",
            ),
        ),
        (
            "test_auth_repository_services_ownership.py",
            "test_create_contract.py",
            "test_load_dataset.py",
            "test_repo_id_contract.py",
            "test_upload_repo_type.py",
        ),
        ("docs/architecture.md", "docs/cli_feature_baseline.md"),
        ("offline-contract", "security-contract", "controlled-remote"),
        "partial",
    ),
    "RUNTIME": _capability(
        "RUNTIME",
        "Shared endpoint, cache, timeout, and progress runtime policy",
        "high",
        ("runtime.configure_hf_environment", "upload runtime contexts"),
        (
            _invariant(
                "RUNTIME-001",
                "AtomGit endpoint, XET disablement, and cache policy are configured idempotently before HF imports.",
                "test_runtime_policy.py",
            ),
            _invariant(
                "RUNTIME-002",
                "Process-global timeout and progress state is restored after success and every failure path.",
                "test_global_state_contract.py",
                "test_sdk_upload_timeout.py",
                "test_upload_progress.py",
            ),
            _invariant(
                "RUNTIME-003",
                "Completion does not load HF or dataset runtimes, read credentials, access the network, or create configuration state.",
                "test_shell_completion.py",
            ),
            _invariant(
                "RUNTIME-004",
                "Fresh supported import permutations and completion converge on the same light, idempotent Hugging Face policy.",
                "test_import_order_contract.py",
            ),
        ),
        (
            "test_global_state_contract.py",
            "test_import_order_contract.py",
            "test_runtime_policy.py",
            "test_sdk_upload_timeout.py",
            "test_shell_completion.py",
            "test_upload_progress.py",
        ),
        ("docs/architecture.md",),
        ("offline-contract", "dependency-contract"),
    ),
    "CACHE": _capability(
        "CACHE",
        "AtomGit-owned cache cleanup",
        "medium",
        ("atomgit cache clear",),
        (
            _invariant(
                "CACHE-001",
                "Cache cleanup removes only AtomGit-owned cache content and reports the result.",
                "test_cache_clear.py",
            ),
            _invariant(
                "CACHE-002",
                "Cache cleanup failures return nonzero without touching credentials or unrelated user state.",
                "test_cache_clear.py",
            ),
        ),
        ("test_cache_clear.py",),
        ("docs/cli_feature_baseline.md", "docs/architecture.md"),
    ),
    "DEPENDENCY-CONTRACT": _capability(
        "DEPENDENCY-CONTRACT",
        "Locked Hugging Face Hub and datasets compatibility",
        "critical",
        ("huggingface-hub==1.1.7", "datasets==4.4.1"),
        (
            _invariant(
                "DEP-001",
                "HF constructors and upload, download, create, and large-folder calls bind to real locked signatures.",
                "test_hf_api_contract.py",
            ),
            _invariant(
                "DEP-002",
                "Deprecated or removed SDK arguments are handled deliberately instead of being accepted by permissive fakes.",
                "test_sdk_upload_parameters.py",
                "test_load_dataset.py",
            ),
            _invariant(
                "DEP-003",
                "Representative production dependency call sites bind their extracted arguments against the real locked signatures.",
                "test_hf_api_contract.py",
            ),
        ),
        (
            "test_hf_api_contract.py",
            "test_load_dataset.py",
            "test_sdk_upload_parameters.py",
        ),
        ("docs/testing.md", ".ai/TESTING.md"),
        ("offline-contract", "dependency-contract"),
    ),
    "PACKAGING": _capability(
        "PACKAGING",
        "Wheel, installer, deploy, imports, and entry points",
        "high",
        ("wheel", "install.sh", "deploy.sh"),
        (
            _invariant(
                "PKG-001",
                "An isolated wheel installs both CLI entry points and both Python imports without repository artifacts.",
                "test_wheel_smoke.py",
            ),
            _invariant(
                "PKG-002",
                "Installer and deploy scripts pin, verify, and invoke the intended distribution safely.",
                "test_installer.py",
                "test_deploy_script.py",
            ),
            _invariant(
                "PKG-003",
                "Official installation enables managed Zsh completion by default with opt-out, idempotent removal, and non-fatal setup failure.",
                "test_installer.py",
                "test_shell_completion.py",
            ),
            _invariant(
                "PKG-004",
                "Release installation accepts only completed pure-numeric Releases and validates wheel identity and checksums before pip.",
                "test_release_workflow.py",
                "test_installer.py",
            ),
            _invariant(
                "PKG-005",
                "Local packaging helpers contain no AtomGit PyPI or twine publication path; publication is manual protected workflow only.",
                "test_release_workflow.py",
                "test_deploy_script.py",
            ),
            _invariant(
                "PKG-006",
                "The protected publication job checks out the exact release source, publishes version-matched notes, rejects public-release mutation, and verifies the exact remote asset set and bytes before publication.",
                "test_release_workflow.py",
            ),
            _invariant(
                "PKG-007",
                "Annotated release tags use a repository-local GitHub Actions bot identity without mutating global Git configuration.",
                "test_release_workflow.py",
            ),
            _invariant(
                "PKG-008",
                "A complete draft Release is resumed only from its downloaded, checksummed, wheel-and-sdist-metadata-validated original assets, without rebuilding or replacing them.",
                "test_release_workflow.py",
            ),
            _invariant(
                "PKG-009",
                "Conda activation and deactivation hooks load and unload only the active environment's Click-derived Zsh completion.",
                "test_shell_completion.py",
            ),
            _invariant(
                "PKG-010",
                "Official CLI and curl uninstall paths are idempotent, remove only exact package-managed environment files, and preserve user data.",
                "test_uninstaller.py",
            ),
            _invariant(
                "PKG-011",
                "An activation hook left after direct pip removal emits the exact recovery warning without filesystem mutation.",
                "test_shell_completion.py",
            ),
            _invariant(
                "PKG-012",
                "Source, PEP 660 editable, wheel, and sdist surfaces preserve public imports and every intended runtime module without repository leakage.",
                "test_public_import_contract.py",
                "test_structure_guard.py",
                "test_wheel_smoke.py",
            ),
            _invariant(
                "PKG-013",
                "The declared setuptools backend and explicit package selection preserve default editable, wheel, and sdist surfaces without repository leakage.",
                "test_packaging_metadata.py",
                "test_wheel_smoke.py",
            ),
            _invariant(
                "PKG-014",
                "The declared src layout discovers exactly the package modules and one top-level SDK compatibility shim across source, editable, wheel, and sdist surfaces.",
                "test_src_layout_migration.py",
                "test_wheel_smoke.py",
            ),
            _invariant(
                "PKG-015",
                "Source, editable, wheel, and sdist surfaces include the exact nested infrastructure package and historical facades without repository leakage.",
                "test_infrastructure_utils_ownership.py",
                "test_src_layout_migration.py",
                "test_wheel_smoke.py",
            ),
            _invariant(
                "PKG-016",
                "Source, editable, wheel, and sdist surfaces include the exact nested lifecycle package and historical facades without repository leakage.",
                "test_environment_lifecycle_ownership.py",
                "test_src_layout_migration.py",
                "test_wheel_smoke.py",
            ),
            _invariant(
                "PKG-017",
                "Source, editable, wheel, and sdist surfaces include the exact nested services package and historical API surface without repository leakage.",
                "test_auth_repository_services_ownership.py",
                "test_src_layout_migration.py",
                "test_wheel_smoke.py",
            ),
            _invariant(
                "PKG-018",
                "Source, editable, wheel, and sdist surfaces include the exact nested download package and historical API surface without repository leakage.",
                "test_download_domain_ownership.py",
                "test_src_layout_migration.py",
                "test_wheel_smoke.py",
            ),
            _invariant(
                "PKG-019",
                "Source, editable, wheel, and sdist surfaces include the exact nested upload package and historical API surface without repository leakage.",
                "test_upload_domain_ownership.py",
                "test_src_layout_migration.py",
                "test_wheel_smoke.py",
            ),
        ),
        (
            "test_auth_repository_services_ownership.py",
            "test_deploy_script.py",
            "test_download_domain_ownership.py",
            "test_environment_lifecycle_ownership.py",
            "test_installer.py",
            "test_infrastructure_utils_ownership.py",
            "test_packaging_metadata.py",
            "test_shell_completion.py",
            "test_public_import_contract.py",
            "test_release_workflow.py",
            "test_src_layout_migration.py",
            "test_structure_guard.py",
            "test_wheel_smoke.py",
            "test_uninstaller.py",
            "test_upload_domain_ownership.py",
        ),
        ("docs/release.md", "docs/testing.md"),
        ("offline-contract", "packaging-smoke"),
    ),
    "PORTABILITY": _capability(
        "PORTABILITY",
        "Python and operating-system portability",
        "high",
        ("Python 3.9+", "Windows", "POSIX"),
        (
            _invariant(
                "PORT-001",
                "Supported Python versions avoid newer-only syntax and platform assumptions.",
                "test_windows_compatibility.py",
                "test_wheel_smoke.py",
            ),
            _invariant(
                "PORT-002",
                "Windows permissions, paths, helper commands, locking, and deletion preserve the same safety outcomes as POSIX.",
                "test_windows_compatibility.py",
                "test_git_credentials_isolation.py",
                "test_download_prune.py",
            ),
            _invariant(
                "PORT-003",
                "The bootstrap selects an explicit or supported Python 3.9+ interpreter without requiring conda, while update uses sys.executable.",
                "test_installer.py",
                "test_update.py",
            ),
            _invariant(
                "PORT-004",
                "Non-conda installation remains supported and skips conda-only completion with accurate guidance.",
                "test_installer.py",
            ),
            _invariant(
                "PORT-005",
                "Official installer and uninstaller entrypoints remain POSIX syntax valid and package-present/fallback decisions stay aligned with Python policy.",
                "test_installer.py",
                "test_uninstaller.py",
            ),
            _invariant(
                "PORT-006",
                "Black, isort, Ruff, setuptools, and pytest share the Python 3.9 floor while exact legacy violations cannot grow.",
                "test_packaging_metadata.py",
            ),
            _invariant(
                "PORT-007",
                "Supported source import orders and completion resolve the same lightweight runtime policy from the src package without root-module fallback.",
                "test_import_order_contract.py",
                "test_src_layout_migration.py",
            ),
            _invariant(
                "PORT-008",
                "Installed Python lifecycle policy and the package-absent POSIX uninstall fallback share the exact managed manifest and safety outcomes.",
                "test_environment_lifecycle_ownership.py",
                "test_uninstaller.py",
            ),
        ),
        (
            "test_auth_repository_services_ownership.py",
            "test_download_prune.py",
            "test_environment_lifecycle_ownership.py",
            "test_git_credentials_isolation.py",
            "test_installer.py",
            "test_import_order_contract.py",
            "test_packaging_metadata.py",
            "test_src_layout_migration.py",
            "test_uninstaller.py",
            "test_update.py",
            "test_wheel_smoke.py",
            "test_windows_compatibility.py",
        ),
        ("docs/testing.md", "docs/architecture.md"),
        ("offline-contract", "portability-contract", "packaging-smoke"),
    ),
    "ERROR-REDACTION": _capability(
        "ERROR-REDACTION",
        "Credential-safe CLI and SDK errors",
        "critical",
        ("all CLI error output", "AtomGitError hierarchy"),
        (
            _invariant(
                "REDACT-001",
                "CLI errors never expose tokens, signed URLs, response bodies, or sensitive remote exception text.",
                "test_cli_error_redaction.py",
                "test_login_error_semantics.py",
                "test_refactor_behavior_guard.py",
            ),
            _invariant(
                "REDACT-002",
                "Upload, download, authentication, and SDK failures retain actionable categories after redaction.",
                "test_upload_error_classify.py",
                "test_download_redirect_security.py",
                "test_sdk_exceptions.py",
            ),
        ),
        (
            "test_cli_error_redaction.py",
            "test_download_redirect_security.py",
            "test_login_error_semantics.py",
            "test_refactor_behavior_guard.py",
            "test_sdk_exceptions.py",
            "test_upload_error_classify.py",
        ),
        ("docs/testing.md", "docs/architecture.md"),
        ("offline-contract", "security-contract"),
    ),
}


WORKFLOW_DOCUMENT_MARKERS = {
    ".ai/DEVELOPMENT_FLOOR.md": (
        FORMAL_DEFINITION,
        "## Capability Contract",
        "## Blocking Rule",
        "## Compatibility Migration",
    ),
    ".ai/MASTER_PROMPT.md": ("development floor",),
    ".ai/DEVELOPMENT_RULES.md": ("Affected Capability IDs",),
    ".ai/TESTING.md": ("Development Floor", "python tests/run_cli_baseline.py"),
    ".ai/DOD.md": ("Affected Capability IDs", "further feature expansion"),
    ".ai/REVIEW.md": ("Development Floor Review",),
    ".ai/WORKFLOW.md": (
        "Affected Capability IDs",
        "Protected Existing Invariants",
        "New Or Changed Invariants",
    ),
    "docs/development_floor.md": (
        FORMAL_DEFINITION,
        "26 个稳定能力 ID",
        "102 条可观察行为不变量",
        "86 个隔离 pytest case",
    ),
    "docs/testing.md": ("86 个 pytest case", "development_floor.md"),
    "docs/development.md": ("开发底线", "python tests/run_cli_baseline.py"),
}


def capability_test_map(registry):
    mapping = defaultdict(list)
    for capability_id, capability in registry.items():
        for test in capability.get("tests", ()):
            mapping[test].append(capability_id)
    return {
        test: tuple(sorted(capability_ids))
        for test, capability_ids in sorted(mapping.items())
    }


def validate_development_floor(registry, baseline_scripts, repository_root):
    errors = []
    root = Path(repository_root)
    baseline_scripts = set(baseline_scripts)

    if len(registry) != BASELINE_CAPABILITY_COUNT:
        errors.append(
            "capability count does not match the monotonic ledger: "
            f"{len(registry)} != {BASELINE_CAPABILITY_COUNT}"
        )

    capability_ids = []
    invariant_ids = []
    invariant_count = 0
    for key, capability in registry.items():
        missing_fields = _REQUIRED_CAPABILITY_FIELDS - set(capability)
        extra_fields = set(capability) - _REQUIRED_CAPABILITY_FIELDS
        if missing_fields or extra_fields:
            errors.append(
                f"capability {key} fields mismatch: missing={sorted(missing_fields)}, "
                f"extra={sorted(extra_fields)}"
            )
            continue

        capability_id = capability["id"]
        capability_ids.append(capability_id)
        if key != capability_id or not _CAPABILITY_ID.fullmatch(capability_id):
            errors.append(f"invalid capability identity: key={key!r}, id={capability_id!r}")
        if not isinstance(capability["name"], str) or not capability["name"].strip():
            errors.append(f"capability {key} has no name")
        if capability["risk"] not in _RISKS:
            errors.append(f"capability {key} has invalid risk: {capability['risk']!r}")

        for field in ("entrypoints", "invariants", "tests", "documents", "evidence"):
            value = capability[field]
            if not isinstance(value, tuple) or not value:
                errors.append(f"capability {key} has empty or non-tuple {field}")
        if len(set(capability["tests"])) != len(capability["tests"]):
            errors.append(f"capability {key} registers duplicate tests")
        if len(set(capability["documents"])) != len(capability["documents"]):
            errors.append(f"capability {key} registers duplicate documents")
        if not set(capability["evidence"]) <= _EVIDENCE_CATEGORIES:
            errors.append(f"capability {key} has invalid evidence categories")
        if capability["remote_evidence"] not in _REMOTE_EVIDENCE:
            errors.append(
                f"capability {key} has invalid remote evidence: "
                f"{capability['remote_evidence']!r}"
            )
        if capability["remote_evidence"] in {"controlled", "partial"} and (
            "controlled-remote" not in capability["evidence"]
        ):
            errors.append(
                f"capability {key} claims remote evidence without its evidence category"
            )

        capability_tests = set(capability["tests"])
        for test in capability["tests"]:
            if test not in baseline_scripts:
                errors.append(f"capability {key} references stale baseline test: {test}")
            if not (root / "tests" / test).is_file():
                errors.append(f"capability {key} references missing test: {test}")
        for document in capability["documents"]:
            if not isinstance(document, str) or not document:
                errors.append(f"capability {key} has invalid document reference")
            elif not (root / document).is_file():
                errors.append(f"capability {key} references missing document: {document}")

        invariant_count += len(capability["invariants"])
        for invariant in capability["invariants"]:
            if not isinstance(invariant, dict):
                errors.append(f"capability {key} has a non-dict invariant")
                continue
            if set(invariant) != _REQUIRED_INVARIANT_FIELDS:
                errors.append(f"capability {key} has incomplete invariant metadata")
                continue
            invariant_id = invariant["id"]
            invariant_ids.append(invariant_id)
            if not isinstance(invariant_id, str) or not _INVARIANT_ID.fullmatch(
                invariant_id
            ):
                errors.append(f"capability {key} has invalid invariant ID: {invariant_id!r}")
            if not isinstance(invariant["statement"], str) or not invariant[
                "statement"
            ].strip():
                errors.append(f"invariant {invariant_id!r} has no observable statement")
            invariant_tests = invariant["tests"]
            if not isinstance(invariant_tests, tuple) or not invariant_tests:
                errors.append(f"invariant {invariant_id!r} has no executable evidence")
            elif not set(invariant_tests) <= capability_tests:
                errors.append(
                    f"invariant {invariant_id!r} references tests outside capability {key}"
                )

    if len(set(capability_ids)) != len(capability_ids):
        errors.append("duplicate capability IDs")
    if len(set(invariant_ids)) != len(invariant_ids):
        errors.append("duplicate invariant IDs")
    if invariant_count != BASELINE_INVARIANT_COUNT:
        errors.append(
            "invariant count does not match the monotonic ledger: "
            f"{invariant_count} != {BASELINE_INVARIANT_COUNT}"
        )

    mapped_tests = set(capability_test_map(registry))
    for test in sorted(baseline_scripts - mapped_tests):
        errors.append(f"offline baseline test has no capability: {test}")
    for test in sorted(mapped_tests - baseline_scripts):
        errors.append(f"capability registry has stale test evidence: {test}")
    return errors


def validate_workflow_documents(repository_root):
    root = Path(repository_root)
    errors = []
    for relative_path, markers in WORKFLOW_DOCUMENT_MARKERS.items():
        path = root / relative_path
        if not path.is_file():
            errors.append(f"missing development-floor document: {relative_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(
                    f"development-floor marker missing from {relative_path}: {marker!r}"
                )
        if relative_path == "docs/development_floor.md":
            for capability_id in CAPABILITY_REGISTRY:
                if f"`{capability_id}`" not in text:
                    errors.append(
                        "human capability ledger is missing registered ID: "
                        f"{capability_id}"
                    )
    return errors
