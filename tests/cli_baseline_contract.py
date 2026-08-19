"""Declarative, exact contract for the monotonically growing CLI baseline."""

import ast
from collections import Counter

import click


UNSET = None


def _parameter(
    kind,
    name,
    declarations=(),
    required=False,
    default=UNSET,
    parameter_type=("string",),
    nargs=1,
    is_flag=False,
    multiple=False,
    metavar=None,
    show_default=False,
    hidden=False,
    flag_value=None,
):
    return {
        "kind": kind,
        "name": name,
        "declarations": tuple(declarations),
        "required": required,
        "default": default,
        "type": tuple(parameter_type),
        "nargs": nargs,
        "is_flag": is_flag,
        "multiple": multiple,
        "metavar": metavar,
        "show_default": show_default,
        "hidden": hidden,
        "flag_value": flag_value,
    }


def _argument(
    name,
    *,
    required=True,
    default=UNSET,
    parameter_type=("string",),
    nargs=1,
):
    return _parameter(
        "argument",
        name,
        required=required,
        default=default,
        parameter_type=parameter_type,
        nargs=nargs,
    )


def _option(
    name,
    *declarations,
    required=False,
    default=UNSET,
    parameter_type=("string",),
    nargs=1,
    is_flag=False,
    multiple=False,
    metavar=None,
    show_default=False,
    hidden=False,
    flag_value=None,
):
    if is_flag and flag_value is None:
        flag_value = True
    return _parameter(
        "option",
        name,
        declarations=declarations,
        required=required,
        default=default,
        parameter_type=parameter_type,
        nargs=nargs,
        is_flag=is_flag,
        multiple=multiple,
        metavar=metavar,
        show_default=show_default,
        hidden=hidden,
        flag_value=flag_value,
    )


MODEL_DATASET_CHOICE = ("choice", ("model", "dataset"), True)
VISIBILITY_CHOICE = ("choice", ("public", "private"), True)
ZSH_CHOICE = ("choice", ("zsh",), False)
EXISTING_PATH = (
    "path", True, True, True, True, False, False, False, False, None,
)
PATH = (
    "path", False, True, True, True, False, False, False, False, None,
)
UPLOAD_BATCH_RANGE = ("int_range", 1, 20)


EXPECTED_PUBLIC_SCHEMA = {
    (): {
        "kind": "group",
        "params": (
            _option(
                "version",
                "--version",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
        ),
    },
    ("update",): {
        "kind": "command",
        "params": (
            _option(
                "target_version",
                "--version",
                default=None,
            ),
            _option(
                "force_reinstall",
                "--force-reinstall",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
        ),
    },
    ("uninstall",): {
        "kind": "command",
        "params": (
            _option(
                "yes",
                "--yes",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
        ),
    },
    ("login",): {
        "kind": "command",
        "params": (
            _option("token", "--token", "-t"),
            _option(
                "token_stdin",
                "--token-stdin",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
        ),
    },
    ("logout",): {"kind": "command", "params": ()},
    ("whoami",): {"kind": "command", "params": ()},
    ("repo",): {"kind": "group", "params": ()},
    ("cache",): {"kind": "group", "params": ()},
    ("cache", "clear"): {"kind": "command", "params": ()},
    ("repo", "create"): {
        "kind": "command",
        "params": (
            _argument("repo_name"),
            _option(
                "repo_type",
                "--type",
                required=True,
                parameter_type=MODEL_DATASET_CHOICE,
            ),
            _option(
                "private",
                "--private",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
            _option(
                "public_repo",
                "--public",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
            _option(
                "exist_ok",
                "--exist-ok",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
        ),
    },
    ("repo", "list"): {"kind": "command", "params": ()},
    ("repo", "visibility"): {
        "kind": "command",
        "params": (
            _argument("repo_id"),
            _argument("visibility", parameter_type=VISIBILITY_CHOICE),
        ),
    },
    ("repo", "delete"): {
        "kind": "command",
        "params": (
            _argument("repo_id"),
            _option(
                "confirm", "--confirm", required=True, metavar="REPO_ID",
            ),
        ),
    },
    ("repo", "branch"): {"kind": "group", "params": ()},
    ("repo", "branch", "create"): {
        "kind": "command",
        "params": (
            _argument("repo_id"),
            _argument("branch_name"),
            _option(
                "source", "--from", default="main", show_default=True,
            ),
        ),
    },
    ("upload",): {
        "kind": "command",
        "params": (
            _argument("path", parameter_type=EXISTING_PATH),
            _option("repo_id", "--repo-id", required=True),
            _option("message", "--message", "-m", default=""),
            _option(
                "timeout_sec",
                "--timeout",
                "-t",
                default=None,
                parameter_type=("float",),
            ),
            _option(
                "no_progress_bar",
                "--no-progress-bar",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
            _option(
                "path_in_repo",
                "--path-in-repo",
                "-p",
                default=None,
            ),
            _option(
                "repo_type",
                "--repo-type",
                "-r",
                default=None,
                parameter_type=MODEL_DATASET_CHOICE,
            ),
            _option("revision", "--revision", default=None),
            _option("ignore", "--ignore", "-i", default=None),
            _option(
                "resumable",
                "--resumable",
                "--no-resumable",
                default=None,
                parameter_type=("bool",),
                is_flag=True,
            ),
            _option(
                "num_workers",
                "--num-workers",
                default=5,
                parameter_type=("int",),
            ),
            _option(
                "batch_size",
                "--batch-size",
                default=20,
                parameter_type=UPLOAD_BATCH_RANGE,
                show_default=True,
            ),
            _option(
                "auto_configure_lfs",
                "--auto-configure-lfs",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
        ),
    },
    ("download",): {
        "kind": "command",
        "params": (
            _argument("repo_id"),
            _option(
                "directory",
                "--directory",
                "-d",
                parameter_type=PATH,
            ),
            _option(
                "force",
                "--force",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
            _option(
                "verify_checksum",
                "--verify-checksum",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
            _option(
                "resume_download",
                "--resume",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
            _option(
                "prune",
                "--prune",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
            _option(
                "repo_type",
                "--repo-type",
                "-r",
                default=None,
                parameter_type=MODEL_DATASET_CHOICE,
            ),
        ),
    },
    ("download-file",): {
        "kind": "command",
        "params": (
            _argument("repo_id"),
            _argument("filename"),
            _option(
                "directory",
                "--directory",
                "-d",
                parameter_type=PATH,
            ),
            _option(
                "force",
                "--force",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
            _option(
                "verify_checksum",
                "--verify-checksum",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
            _option(
                "resume_download",
                "--resume",
                default=False,
                parameter_type=("bool",),
                is_flag=True,
            ),
            _option(
                "repo_type",
                "--repo-type",
                "-r",
                default=None,
                parameter_type=MODEL_DATASET_CHOICE,
            ),
        ),
    },
    ("completion",): {"kind": "group", "params": ()},
    ("completion", "show"): {
        "kind": "command",
        "params": (
            _argument("shell", parameter_type=ZSH_CHOICE),
        ),
    },
    ("completion", "install"): {
        "kind": "command",
        "params": (
            _option(
                "shell",
                "--shell",
                default="zsh",
                parameter_type=ZSH_CHOICE,
                show_default=True,
            ),
        ),
    },
    ("completion", "uninstall"): {
        "kind": "command",
        "params": (
            _option(
                "shell",
                "--shell",
                default="zsh",
                parameter_type=ZSH_CHOICE,
                show_default=True,
            ),
        ),
    },
    ("config-show",): {"kind": "command", "params": ()},
}

for _command_spec in EXPECTED_PUBLIC_SCHEMA.values():
    _is_group = _command_spec["kind"] == "group"
    _command_spec.update(
        hidden=False,
        deprecated=False,
        no_args_is_help=_is_group,
        chain=False if _is_group else None,
        invoke_without_command=False if _is_group else None,
    )


LEAF_DISPATCH_PATHS = (
    ("update",),
    ("uninstall",),
    ("login",),
    ("logout",),
    ("whoami",),
    ("config-show",),
    ("cache", "clear"),
    ("repo", "create"),
    ("repo", "list"),
    ("repo", "visibility"),
    ("repo", "delete"),
    ("repo", "branch", "create"),
    ("upload",),
    ("download",),
    ("download-file",),
    ("completion", "show"),
    ("completion", "install"),
    ("completion", "uninstall"),
)


BASELINE_TEST_GROUPS = {
    "development-floor": (
        "test_auth_repository_services_ownership.py",
        "test_api_facade_conversion.py",
        "test_cli_facade_conversion.py",
        "test_cli_command_ownership.py",
        "test_development_floor.py",
        "test_environment_lifecycle_ownership.py",
        "test_infrastructure_utils_ownership.py",
        "test_lfs_domain_ownership.py",
        "test_sdk_domain_ownership.py",
        "test_packaging_metadata.py",
        "test_src_layout_migration.py",
        "test_structure_guard.py",
    ),
    "cli-interface-and-redaction": (
        "test_cli_baseline_guard.py",
        "test_cli_error_redaction.py",
        "test_cli_feature_baseline.py",
        "test_refactor_behavior_guard.py",
        "test_cli_surface.py",
        "test_shell_completion.py",
        "test_update.py",
        "test_uninstaller.py",
    ),
    "cache": (
        "test_cache_clear.py",
    ),
    "authentication-configuration-and-git": (
        "test_anonymous_token_isolation.py",
        "test_auth_status_semantics.py",
        "test_config_permissions.py",
        "test_git_credentials_isolation.py",
        "test_git_helper_identity.py",
        "test_login_config.py",
        "test_login_error_semantics.py",
        "test_login_response_bound.py",
    ),
    "repository-and-revision-management": (
        "test_api_revision_guard.py",
        "test_branch_create.py",
        "test_create_contract.py",
        "test_create_visibility.py",
        "test_repo_delete.py",
        "test_repo_id_contract.py",
        "test_repo_info_stub.py",
        "test_repo_list.py",
        "test_repo_visibility.py",
        "test_revision_rejection.py",
    ),
    "upload": (
        "test_upload_domain_ownership.py",
        "test_auto_configure_lfs.py",
        "test_canonical_lfs_pointer.py",
        "test_lfs_slow_flow_recovery.py",
        "test_lfs_preupload_policy.py",
        "test_upload_batching.py",
        "test_resumable_commit_policy.py",
        "test_dataset_resumable_route.py",
        "test_resumable_recovery.py",
        "test_resumable_stats.py",
        "test_sdk_upload_lifetime.py",
        "test_sdk_upload_parameters.py",
        "test_sdk_upload_timeout.py",
        "test_upload_error_classify.py",
        "test_upload_error_handling.py",
        "test_upload_fallback_temp.py",
        "test_upload_file_no_copy.py",
        "test_upload_ignore.py",
        "test_upload_path_in_repo.py",
        "test_upload_progress.py",
        "test_upload_repo_type.py",
        "test_upload_resumable.py",
        "test_upload_symlink_safety.py",
        "test_upload_validation.py",
    ),
    "download-and-data-integrity": (
        "test_cli_download_file.py",
        "test_download_domain_ownership.py",
        "test_download_checksum.py",
        "test_download_contract.py",
        "test_download_existing_file_policy.py",
        "test_download_manifest_concurrency.py",
        "test_download_path_security.py",
        "test_download_prune.py",
        "test_download_raw_integrity.py",
        "test_download_recovery.py",
        "test_download_redirect_security.py",
        "test_download_repo_type_resolution.py",
        "test_download_resume_cli.py",
        "test_download_standard_cleanup.py",
        "test_download_unicode_metadata.py",
    ),
    "sdk-dependency-and-runtime": (
        "test_global_state_contract.py",
        "test_hf_api_contract.py",
        "test_import_order_contract.py",
        "test_load_dataset.py",
        "test_public_import_contract.py",
        "test_runtime_policy.py",
        "test_sdk_create_contract.py",
        "test_sdk_exceptions.py",
    ),
    "distribution-and-portability": (
        "test_deploy_script.py",
        "test_installer.py",
        "test_release_workflow.py",
        "test_wheel_smoke.py",
        "test_windows_compatibility.py",
    ),
}


BASELINE_PUBLIC_COMMAND_COUNT = 23
BASELINE_PUBLIC_PARAMETER_COUNT = 48
BASELINE_LEAF_COMMAND_COUNT = 18
BASELINE_TEST_SCRIPT_COUNT = 91


def _normalize_default(value):
    if value.__class__.__name__ == "Sentinel" and str(value) == "Sentinel.UNSET":
        return UNSET
    return value


def _normalize_type(parameter_type):
    if isinstance(parameter_type, click.IntRange):
        return ("int_range", parameter_type.min, parameter_type.max)
    if isinstance(parameter_type, click.Choice):
        return (
            "choice",
            tuple(parameter_type.choices),
            parameter_type.case_sensitive,
        )
    if isinstance(parameter_type, click.Path):
        path_type = parameter_type.type
        path_type_name = None if path_type is None else path_type.__name__
        return (
            "path",
            parameter_type.exists,
            parameter_type.file_okay,
            parameter_type.dir_okay,
            parameter_type.readable,
            parameter_type.writable,
            parameter_type.executable,
            parameter_type.resolve_path,
            parameter_type.allow_dash,
            path_type_name,
        )
    if isinstance(parameter_type, click.types.BoolParamType):
        return ("bool",)
    if isinstance(parameter_type, click.types.FloatParamType):
        return ("float",)
    if isinstance(parameter_type, click.types.IntParamType):
        return ("int",)
    if isinstance(parameter_type, click.types.StringParamType):
        return ("string",)
    return (parameter_type.__class__.__name__,)


def _discover_parameter(parameter):
    declarations = ()
    is_flag = False
    multiple = False
    if isinstance(parameter, click.Option):
        declarations = tuple(parameter.opts) + tuple(parameter.secondary_opts)
        is_flag = parameter.is_flag
        multiple = parameter.multiple
    return {
        "kind": "argument" if isinstance(parameter, click.Argument) else "option",
        "name": parameter.name,
        "declarations": declarations,
        "required": parameter.required,
        "default": _normalize_default(parameter.default),
        "type": _normalize_type(parameter.type),
        "nargs": parameter.nargs,
        "is_flag": is_flag,
        "multiple": multiple,
        "metavar": parameter.metavar,
        "show_default": bool(getattr(parameter, "show_default", False)),
        "hidden": getattr(parameter, "hidden", False),
        "flag_value": getattr(parameter, "flag_value", None),
    }


def discover_public_schema(root_command):
    schema = {}

    def visit(command, path):
        is_group = isinstance(command, click.Group)
        schema[path] = {
            "kind": "group" if is_group else "command",
            "params": tuple(
                _discover_parameter(parameter) for parameter in command.params
            ),
            "hidden": command.hidden,
            "deprecated": bool(command.deprecated),
            "no_args_is_help": command.no_args_is_help,
            "chain": command.chain if is_group else None,
            "invoke_without_command": (
                command.invoke_without_command if is_group else None
            ),
        }
        if is_group:
            for name, child in command.commands.items():
                visit(child, path + (name,))

    visit(root_command, ())
    return schema


def _format_path(path):
    return "<root>" if not path else " ".join(path)


def validate_public_schema(actual_schema):
    errors = []
    expected_paths = set(EXPECTED_PUBLIC_SCHEMA)
    actual_paths = set(actual_schema)
    expected_parameter_count = sum(
        len(spec["params"]) for spec in EXPECTED_PUBLIC_SCHEMA.values()
    )
    actual_parameter_count = sum(
        len(spec["params"]) for spec in actual_schema.values()
    )
    if len(expected_paths) != BASELINE_PUBLIC_COMMAND_COUNT:
        errors.append(
            "registered public command count does not match the monotonic "
            f"ledger: {len(expected_paths)} != {BASELINE_PUBLIC_COMMAND_COUNT}"
        )
    if len(actual_paths) != BASELINE_PUBLIC_COMMAND_COUNT:
        errors.append(
            "actual public command count does not match the monotonic ledger: "
            f"{len(actual_paths)} != {BASELINE_PUBLIC_COMMAND_COUNT}"
        )
    if expected_parameter_count != BASELINE_PUBLIC_PARAMETER_COUNT:
        errors.append(
            "registered public parameter count does not match the monotonic "
            f"ledger: {expected_parameter_count} != "
            f"{BASELINE_PUBLIC_PARAMETER_COUNT}"
        )
    if actual_parameter_count != BASELINE_PUBLIC_PARAMETER_COUNT:
        errors.append(
            "actual public parameter count does not match the monotonic ledger: "
            f"{actual_parameter_count} != {BASELINE_PUBLIC_PARAMETER_COUNT}"
        )
    for path in sorted(actual_paths - expected_paths):
        errors.append(f"unregistered command: {_format_path(path)}")
    for path in sorted(expected_paths - actual_paths):
        errors.append(f"missing registered command: {_format_path(path)}")
    for path in sorted(expected_paths & actual_paths):
        expected = EXPECTED_PUBLIC_SCHEMA[path]
        actual = actual_schema[path]
        expected_command_attributes = {
            key: value for key, value in expected.items() if key != "params"
        }
        actual_command_attributes = {
            key: value for key, value in actual.items() if key != "params"
        }
        if actual_command_attributes != expected_command_attributes:
            errors.append(
                f"schema mismatch for {_format_path(path)}: "
                f"expected command attributes={expected_command_attributes!r}, "
                f"actual={actual_command_attributes!r}"
            )
        expected_params = expected["params"]
        actual_params = actual["params"]
        for index in range(max(len(expected_params), len(actual_params))):
            expected_parameter = (
                expected_params[index] if index < len(expected_params) else None
            )
            actual_parameter = (
                actual_params[index] if index < len(actual_params) else None
            )
            if actual_parameter != expected_parameter:
                errors.append(
                    f"schema mismatch for {_format_path(path)} "
                    f"parameter {index}: expected={expected_parameter!r}, "
                    f"actual={actual_parameter!r}"
                )
    return errors


def validate_leaf_dispatches(dispatch_paths, public_schema):
    errors = []
    if len(dispatch_paths) != BASELINE_LEAF_COMMAND_COUNT:
        errors.append(
            "leaf dispatch count does not match the monotonic ledger: "
            f"{len(dispatch_paths)} != {BASELINE_LEAF_COMMAND_COUNT}"
        )
    counts = Counter(dispatch_paths)
    duplicates = sorted(path for path, count in counts.items() if count != 1)
    for path in duplicates:
        errors.append(f"leaf dispatch registered more than once: {_format_path(path)}")

    actual_leaves = {
        path
        for path, spec in public_schema.items()
        if path and spec["kind"] == "command"
    }
    registered = set(dispatch_paths)
    for path in sorted(actual_leaves - registered):
        errors.append(f"missing leaf dispatch: {_format_path(path)}")
    for path in sorted(registered - actual_leaves):
        errors.append(f"stale leaf dispatch: {_format_path(path)}")
    return errors


def validate_test_registry(discovered_scripts):
    errors = []
    registered_entries = [
        script
        for scripts in BASELINE_TEST_GROUPS.values()
        for script in scripts
    ]
    counts = Counter(registered_entries)
    if len(registered_entries) != BASELINE_TEST_SCRIPT_COUNT:
        errors.append(
            "registered test count does not match the monotonic ledger: "
            f"{len(registered_entries)} != {BASELINE_TEST_SCRIPT_COUNT}"
        )
    if len(discovered_scripts) != BASELINE_TEST_SCRIPT_COUNT:
        errors.append(
            "discovered test count does not match the monotonic ledger: "
            f"{len(discovered_scripts)} != {BASELINE_TEST_SCRIPT_COUNT}"
        )
    for script in sorted(name for name, count in counts.items() if count > 1):
        errors.append(f"test registered more than once: {script}")
    for group, scripts in sorted(BASELINE_TEST_GROUPS.items()):
        if not scripts:
            errors.append(f"empty baseline test group: {group}")

    registered = set(registered_entries)
    discovered = set(discovered_scripts)
    for script in sorted(discovered - registered):
        errors.append(f"unregistered test script: {script}")
    for script in sorted(registered - discovered):
        errors.append(f"registered test script is missing: {script}")
    return errors


def _main_guard_calls_main(node):
    if not isinstance(node, ast.If):
        return False
    comparison = node.test
    if not (
        isinstance(comparison, ast.Compare)
        and len(comparison.ops) == 1
        and isinstance(comparison.ops[0], ast.Eq)
        and len(comparison.comparators) == 1
    ):
        return False
    operands = (comparison.left, comparison.comparators[0])
    has_name = any(
        isinstance(operand, ast.Name) and operand.id == "__name__"
        for operand in operands
    )
    has_main = any(
        isinstance(operand, ast.Constant) and operand.value == "__main__"
        for operand in operands
    )
    calls_main = any(
        isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id == "main"
        for child in ast.walk(node)
    )
    return has_name and has_main and calls_main


def validate_test_entrypoints(script_sources):
    errors = []
    for script, source in sorted(script_sources.items()):
        try:
            tree = ast.parse(source, filename=script)
        except SyntaxError as error:
            errors.append(f"test script cannot be parsed: {script}: {error.msg}")
            continue
        has_main_function = any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "main"
            for node in tree.body
        )
        has_executable_guard = any(
            _main_guard_calls_main(node) for node in tree.body
        )
        if not has_main_function or not has_executable_guard:
            errors.append(
                f"test script is not self-executing through main(): {script}"
            )
    return errors
