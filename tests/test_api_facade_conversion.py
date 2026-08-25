#!/usr/bin/env python3
"""Lock the historical API paths to one canonical compatibility facade."""

import ast
import importlib
import inspect
import sys
from pathlib import Path
from unittest.mock import patch

TESTS_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = TESTS_DIRECTORY.parent
SRC_DIRECTORY = REPOSITORY_ROOT / "src"
PACKAGE_DIRECTORY = SRC_DIRECTORY / "atomgit"
if str(SRC_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SRC_DIRECTORY))


EXPECTED_BASES = (
    "AuthenticationServiceMixin",
    "RepositoryServiceMixin",
    "DownloadServiceMixin",
    "UploadServiceMixin",
)
EXPECTED_METHOD_SIGNATURES = {
    "login": "(self, token: str) -> bool",
    "create_repo": "(self, repo_name: str, repo_type: str = 'model', private: bool = False, exist_ok: bool = False) -> bool",
    "download_repo": "(self, repo_id: str, local_path: pathlib.Path = None, force_download: bool = False, repo_type: str = None, verify_checksum: bool = False, resume_download: bool = False, prune: bool = False) -> bool",
    "download_file": "(self, repo_id: str, filename: str, local_path: pathlib.Path = None, force_download: bool = False, repo_type: str = None, verify_checksum: bool = False, resume_download: bool = False) -> bool",
    "upload_folder": "(self, file_path: pathlib.Path, repo_id: str, remote_path: str = None, message: str = None, upload_timeout: Optional[float] = None, progress_bar: bool = True, path_in_repo: str = None, repo_type: str = None, revision: str = None, ignore_patterns=None, num_workers: int = 5) -> bool",
    "upload_directory": "(self, dir_path: pathlib.Path, repo_id: str, message: str = None, progress_callback=None, upload_timeout: Optional[float] = None, progress_bar: bool = True, path_in_repo: str = None, repo_type: str = None, revision: str = None, ignore_patterns=None, resumable: bool = False, num_workers: int = 5, auto_configure_lfs: bool = False, batch_size: int = 20) -> bool",
}
FORBIDDEN_FACADE_CALLS = {
    "open",
    "urlopen",
    "request",
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "mkdtemp",
    "TemporaryDirectory",
    "sleep",
}

results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def _class_node(tree, name):
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == name
    )


def main():
    flat_path = PACKAGE_DIRECTORY / "api.py"
    facade_path = PACKAGE_DIRECTORY / "api" / "__init__.py"
    owner_path = PACKAGE_DIRECTORY / "compatibility" / "api.py"
    check(
        "root and package API paths resolve one canonical facade",
        facade_path.is_file() and flat_path.is_file() and owner_path.is_file(),
        repr(
            {
                "flat": flat_path.exists(),
                "facade": facade_path.is_file(),
                "owner": owner_path.is_file(),
            }
        ),
    )
    if not owner_path.is_file():
        return 1

    source = owner_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(owner_path))
    api_module = importlib.import_module("atomgit.api")
    atomgit_package = importlib.import_module("atomgit")
    cli_module = importlib.import_module("atomgit.cli")

    check(
        "historical API import resolves the canonical owner",
        api_module.__name__ == "atomgit.compatibility.api"
        and Path(api_module.__file__).resolve() == owner_path.resolve()
        and api_module.__package__ == "atomgit.compatibility",
        repr(
            {
                "name": api_module.__name__,
                "file": api_module.__file__,
                "package": api_module.__package__,
            }
        ),
    )

    class_node = _class_node(tree, "HuggingFaceAPI")
    bases = tuple(ast.unparse(base) for base in class_node.bases)
    class_methods = {
        node.name
        for node in class_node.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    check(
        "the facade owns only historical class composition and singleton identity",
        bases == EXPECTED_BASES
        and class_methods == {"__init__"}
        and api_module.HuggingFaceAPI.__module__ == "atomgit.compatibility.api"
        and type(api_module.api) is api_module.HuggingFaceAPI
        and atomgit_package.api is api_module.api,
        repr(
            {
                "bases": bases,
                "methods": sorted(class_methods),
                "module": api_module.HuggingFaceAPI.__module__,
            }
        ),
    )

    signatures = {
        name: str(inspect.signature(getattr(api_module.HuggingFaceAPI, name)))
        for name in EXPECTED_METHOD_SIGNATURES
    }
    check(
        "historical API method signatures remain exact",
        signatures == EXPECTED_METHOD_SIGNATURES,
        repr(signatures),
    )

    owner_modules = {
        importlib.import_module("atomgit.compatibility.authentication"),
        importlib.import_module("atomgit.compatibility.download"),
        importlib.import_module("atomgit.compatibility.repositories"),
        importlib.import_module("atomgit.download.service"),
        importlib.import_module("atomgit.upload.service"),
    }
    check(
        "all API methods retain domain-owner provenance",
        all(
            getattr(api_module.HuggingFaceAPI, name).__module__
            in {module.__name__ for module in owner_modules}
            for name in EXPECTED_METHOD_SIGNATURES
        ),
    )

    top_level_definitions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    check(
        "the API facade contains compatibility assembly rather than business work",
        top_level_definitions == {"HuggingFaceAPI"}
        and not (called_names & FORBIDDEN_FACADE_CALLS),
        repr(
            {
                "definitions": sorted(top_level_definitions),
                "forbidden_calls": sorted(called_names & FORBIDDEN_FACADE_CALLS),
            }
        ),
    )

    patch_cases = {
        "service": ("config", "atomgit.compatibility.authentication"),
        "download": ("hf_http_get", "atomgit.adapters.download.resume"),
        "upload": ("hf_upload_file", "atomgit.upload.service"),
        "lfs": ("math", "atomgit.lfs.service"),
    }
    patch_errors = []
    for category, (name, owner_name) in patch_cases.items():
        owner = importlib.import_module(owner_name)
        original = getattr(api_module, name)
        replacement = object()
        with patch.object(api_module, name, replacement):
            if getattr(owner, name, None) is not replacement:
                patch_errors.append(f"{category}: patch did not propagate")
        if (
            getattr(api_module, name) is not original
            or getattr(owner, name) is not original
        ):
            patch_errors.append(f"{category}: patch did not restore")

        setattr(api_module, name, replacement)
        if getattr(owner, name, None) is not replacement:
            patch_errors.append(f"{category}: assignment did not propagate")
        delattr(api_module, name)
        if hasattr(owner, name):
            patch_errors.append(f"{category}: deletion did not propagate")
        setattr(api_module, name, original)
        if getattr(owner, name, None) is not original:
            patch_errors.append(f"{category}: assignment did not restore")
    check(
        "historical assignment deletion and patch seams reach every owner category",
        not patch_errors,
        repr(patch_errors),
    )

    check(
        "the separate CLI facade remains compatible after its own conversion",
        (PACKAGE_DIRECTORY / "cli" / "__init__.py").is_file()
        and (PACKAGE_DIRECTORY / "cli.py").is_file()
        and (PACKAGE_DIRECTORY / "compatibility" / "cli.py").is_file()
        and cli_module.api._module_name == "api"
        and cli_module.api._attribute_name == "api",
    )

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
