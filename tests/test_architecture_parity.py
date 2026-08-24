#!/usr/bin/env python3
"""Executable contracts for the new core/usecase/native SDK boundary."""

import ast
import tempfile
from pathlib import Path

from atomgit.core import CAPABILITY_REGISTRY, validate_parity_registry
from atomgit.core.contracts import OperationResult
from atomgit.interfaces.sdk import AtomGitClient

results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail and not condition else ""))


class ConfigFake:
    def __init__(self, token=None):
        self.token = token
        self.saved = []

    def get_credentials(self):
        return {"token": self.token} if self.token else None

    def set_credentials(self, token, username=None):
        self.token = token
        self.saved.append((token, username))

    def clear_credentials(self):
        self.token = None


class TransferFake:
    def __init__(self):
        self.calls = []

    def upload_file(self, **kwargs):
        self.calls.append(("upload_file", kwargs))
        return "file-commit"

    def upload_folder(self, **kwargs):
        self.calls.append(("upload_folder", kwargs))
        return "folder-commit"

    def download_snapshot(self, **kwargs):
        self.calls.append(("download_snapshot", kwargs))
        return Path(kwargs["local_dir"] or ".")

    def download_file(self, **kwargs):
        self.calls.append(("download_file", kwargs))
        return "downloaded-file"


class RepositoryFake:
    def __init__(self):
        self.calls = []

    def create(self, *args):
        self.calls.append(("create", args))
        return "https://atomgit.com/user/repo"

    def list(self, token):
        self.calls.append(("list", token))
        return [{"path": "user/repo"}]

    def set_visibility(self, *args):
        self.calls.append(("visibility", args))
        return True

    def create_branch(self, *args):
        self.calls.append(("branch", args))
        return True

    def delete(self, *args):
        self.calls.append(("delete", args))
        return True


class AuthenticationFake:
    def authenticate(self, token):
        return {"login": "user"}

    def current_identity(self, token):
        return {"login": "user"}


def main():
    check("parity registry is fail-closed", not validate_parity_registry())
    check(
        "registry covers parity and explicit CLI-only classes",
        {spec.classification.value for spec in CAPABILITY_REGISTRY.values()}
        == {"parity-required", "cli-only"},
    )

    core_source = Path(__file__).parents[1] / "src" / "atomgit" / "core"
    forbidden = []
    for path in core_source.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(
                alias.name in {"click", "huggingface_hub", "httpx", "urllib"}
                for alias in node.names
            ):
                forbidden.append(path.name)
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and any(
                    name in node.module
                    for name in ("huggingface_hub", "click", "httpx")
                )
            ):
                forbidden.append(path.name)
    check("core has no concrete UI/network dependency", not forbidden, repr(forbidden))

    config = ConfigFake("saved-token")
    transfer = TransferFake()
    repository = RepositoryFake()
    client = AtomGitClient(
        config=config,
        transfer=transfer,
        repository=repository,
        authentication=AuthenticationFake(),
    )
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "file.txt"
        source.write_text("content", encoding="utf-8")
        result = client.upload_file(source, "user/repo", token="explicit-token")
        check(
            "native SDK returns structured upload result",
            isinstance(result, OperationResult) and result.ok,
        )
        call = transfer.calls[-1][1]
        check("explicit token wins over saved token", call["token"] == "explicit-token")
        result = client.download_file("user/repo", "file.txt", token=False)
        check(
            "explicit anonymous read is preserved",
            transfer.calls[-1][1]["token"] is None,
        )
        check("download result records canonical revision", result.revision == "main")
        result = client.upload_folder(
            source.parent,
            "user/repo",
            resumable=True,
            batch_size=3,
            auto_configure_lfs=True,
        )
        check(
            "resumable and batch policy reach shared transfer port",
            (transfer.calls[-1][1]["resumable"], transfer.calls[-1][1]["batch_size"])
            == (True, 3),
        )
        check(
            "LFS policy reaches the shared transfer port",
            transfer.calls[-1][1]["auto_configure_lfs"] is True,
        )

    result = client.create_branch("user/repo", "feature", token="explicit-token")
    check(
        "repository usecase verifies branch result",
        result.ok and repository.calls[-1][0] == "branch",
    )
    try:
        client.create_branch("user/repo", "main", token="explicit-token")
    except ValueError:
        check("main cannot be treated as an unverified upload branch", True)
    else:
        check("main cannot be treated as an unverified upload branch", False)

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
