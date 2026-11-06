#!/usr/bin/env python3
"""Verify deterministic model/dataset selection for CLI downloads."""

import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import atomgit  # noqa: F401

api_mod = sys.modules["atomgit.api"]
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


class FakeHfApi:
    responses = {}
    calls = []

    def __init__(self, token=None, endpoint=None):
        self.token = token

    def list_repo_files(self, repo_id, repo_type=None):
        self.calls.append(repo_type)
        response = self.responses[repo_type]
        if isinstance(response, Exception):
            raise response
        return list(response)


def resolve(responses, repo_type=None):
    FakeHfApi.responses = responses
    FakeHfApi.calls = []
    try:
        result = api_mod._atomgit_list_repo_files("user/repo", "fake-token", repo_type)
        return result, None, list(FakeHfApi.calls)
    except Exception as error:
        return None, error, list(FakeHfApi.calls)


def file_probe_checks():
    import hashlib
    import urllib.error

    from click.testing import CliRunner

    from atomgit.adapters.download import service
    from atomgit.adapters.download.integrity import DownloadChecksumMetadataError
    from atomgit.compatibility.cli import cli
    from atomgit.interfaces.sdk import AtomGitClient

    content = b"probe payload"
    metadata = (
        ("sha256", hashlib.sha256(content).hexdigest(), len(content)),
        "https://fixture.invalid/object",
    )

    class Config:
        def get_credentials(self):
            return None

    def fetch(repo_id, repo_type, filename, destination, token, **kwargs):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    for repo_type in ("model", "dataset"):
        for entry in ("native", "cli"):
            with (
                tempfile.TemporaryDirectory() as directory,
                patch.object(
                    service.integrity,
                    "_atomgit_file_download_metadata",
                    return_value=metadata,
                    create=True,
                ) as probe,
                patch.object(
                    service,
                    "_atomgit_list_repo_files",
                    side_effect=AssertionError("unexpected listing"),
                ) as listing,
                patch.object(service, "_download_atomgit_file", side_effect=fetch),
                patch.object(api_mod.config, "get_credentials", return_value=None),
            ):
                if entry == "native":
                    result = AtomGitClient(config=Config()).download_file(
                        "user/repo",
                        "子目录/file.bin",
                        repo_type=repo_type,
                        revision="feature",
                        local_dir=directory,
                        checksum=True,
                    )
                    ok = result.ok
                else:
                    result = CliRunner().invoke(
                        cli,
                        [
                            "download-file",
                            "user/repo",
                            "子目录/file.bin",
                            "--repo-type",
                            repo_type,
                            "--revision",
                            "feature",
                            "--directory",
                            directory,
                            "--verify-checksum",
                        ],
                    )
                    ok = result.exit_code == 0
                check(
                    f"{entry} explicit {repo_type} downloads without listing",
                    ok
                    and not listing.called
                    and probe.call_count == 1
                    and (Path(directory) / "子目录/file.bin").read_bytes() == content,
                )
                check(
                    f"{entry} probe keeps selected type and revision",
                    probe.called
                    and probe.call_args.args[1] == repo_type
                    and probe.call_args.args[-1] == "feature",
                )

    from atomgit.adapters.download import resume as resume_adapter

    for mode in ("resume", "existing", "ordinary"):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(
                service.integrity,
                "_atomgit_file_download_metadata",
                return_value=metadata,
            ) as probe,
            patch.object(
                service,
                "_atomgit_list_repo_files",
                side_effect=AssertionError("unexpected listing"),
            ),
            patch.object(
                service,
                "_atomgit_file_checksum",
                side_effect=AssertionError("duplicate metadata"),
            ),
            patch.object(
                service, "_download_atomgit_file", side_effect=fetch
            ) as download,
            patch.object(
                resume_adapter,
                "_atomgit_file_download_metadata",
                side_effect=AssertionError("duplicate resume metadata"),
            ),
            patch.object(
                resume_adapter,
                "_resume_cache_root",
                return_value=Path(directory) / "cache",
            ),
            patch.object(
                resume_adapter,
                "hf_http_get",
                side_effect=lambda url, stream, **kw: stream.write(
                    content[kw["resume_size"] :]
                ),
            ) as transfer,
        ):
            (Path(directory) / "cache").mkdir()
            destination = Path(directory) / "file.bin"
            if mode == "existing":
                destination.write_bytes(content)
            result = AtomGitClient(config=Config()).download_file(
                "user/repo",
                "file.bin",
                repo_type="model",
                revision="main",
                local_dir=directory,
                checksum=mode == "existing",
                resume=mode == "resume",
            )
            check(
                f"{mode} reuses one metadata probe without changing bytes",
                result.ok
                and probe.call_count == 1
                and destination.read_bytes() == content,
            )
            if mode == "existing":
                check(
                    "verified existing file avoids content transfer",
                    not transfer.called and not download.called,
                )
            if mode == "ordinary":
                check(
                    "ordinary download does not acquire mandatory checksum verification",
                    "checksum" not in download.call_args.kwargs,
                )

    with (
        tempfile.TemporaryDirectory() as directory,
        patch.object(
            service.integrity,
            "_atomgit_file_download_metadata",
            side_effect=AssertionError("unexpected metadata"),
        ) as probe,
        patch.object(
            service, "_atomgit_list_repo_files", return_value=("dataset", ["file.bin"])
        ) as listing,
        patch.object(service, "_download_atomgit_file", side_effect=fetch),
    ):
        result = AtomGitClient(config=Config()).download_file(
            "user/repo", "file.bin", revision="main", local_dir=directory
        )
        check(
            "automatic repository type retains enumeration",
            result.ok and listing.call_count == 1 and not probe.called,
        )

    for code in (401, 403, 429, 500):
        error = urllib.error.HTTPError(
            "https://fixture.invalid", code, "fixture", {}, None
        )
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(
                service.integrity,
                "_atomgit_file_download_metadata",
                side_effect=error,
                create=True,
            ),
            patch.object(
                service,
                "_atomgit_list_repo_files",
                side_effect=AssertionError("unexpected fallback"),
            ) as listing,
        ):
            result = AtomGitClient(config=Config()).download_file(
                "user/repo",
                "file.bin",
                repo_type="model",
                revision="main",
                local_dir=directory,
            )
            check(
                f"metadata HTTP {code} never triggers listing fallback",
                not result.ok
                and not listing.called
                and result.metadata.get("download_diagnostic", {}).get("status_code")
                == code,
            )

    for failure in (
        DownloadChecksumMetadataError("unsupported"),
        *(
            urllib.error.HTTPError("https://fixture.invalid", code, "fixture", {}, None)
            for code in (404, 405, 501)
        ),
    ):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(
                service.integrity,
                "_atomgit_file_download_metadata",
                side_effect=failure,
                create=True,
            ),
            patch.object(
                service,
                "_atomgit_list_repo_files",
                return_value=("dataset", ["file.bin"]),
            ) as listing,
            patch.object(service, "_download_atomgit_file", side_effect=fetch),
        ):
            result = AtomGitClient(config=Config()).download_file(
                "user/repo",
                "file.bin",
                repo_type="dataset",
                revision="main",
                local_dir=directory,
            )
            check(
                "unsupported or ambiguous metadata retains ordinary-download fallback",
                result.ok
                and listing.call_count == 1
                and (Path(directory) / "file.bin").read_bytes() == content,
            )


def main():
    file_probe_checks()
    from atomgit.adapters.download import service

    with patch.object(
        service, "_atomgit_v5_get_json", return_value={"default_branch": "develop"}
    ) as metadata:
        revision = service._resolve_default_revision(
            "user/repo", "dataset", "fake-token"
        )
        check(
            "authenticated default revision uses repository metadata",
            revision == "develop",
        )
        check(
            "authenticated metadata uses supplied credential",
            metadata.call_args.args[1] == "fake-token",
        )
    with patch.object(service, "HfApi") as api:
        api.return_value.repo_info.return_value = SimpleNamespace(
            default_branch="master"
        )
        revision = service._resolve_default_revision("user/repo", "model", None)
        check("anonymous default revision uses Hub metadata", revision == "master")
        check(
            "anonymous metadata excludes ambient token",
            api.call_args.kwargs["token"] is False,
        )
    import urllib.error

    with patch.object(service, "HfApi") as api:
        missing = urllib.error.HTTPError(
            "https://example.invalid", 404, "missing", {}, None
        )
        api.return_value.repo_info.side_effect = [
            missing,
            SimpleNamespace(default_branch="dataset-branch"),
        ]
        revision = service._resolve_default_revision("user/repo", None, None)
        check(
            "anonymous dataset default is discovered after model 404",
            revision == "dataset-branch",
        )
    with patch.object(service, "HfApi") as api:
        api.return_value.repo_info.side_effect = [
            SimpleNamespace(default_branch="one"),
            SimpleNamespace(default_branch="two"),
        ]
        try:
            service._resolve_default_revision("user/repo", None, None)
        except ValueError:
            check("ambiguous repository default requires an explicit type", True)
        else:
            check("ambiguous repository default requires an explicit type", False)
    with patch.object(service, "_atomgit_v5_get_json", return_value={}):
        try:
            service._resolve_default_revision("user/repo", "dataset", "fake-token")
        except RuntimeError:
            check("missing default revision fails safely", True)
        else:
            check("missing default revision fails safely", False)

    unauthorized = urllib.error.HTTPError(
        "https://example.invalid", 401, "unauthorized", {}, None
    )
    with (
        patch.object(service, "_atomgit_v5_get_json", side_effect=unauthorized),
        patch.object(service, "HfApi") as anonymous_api,
    ):
        try:
            service._resolve_default_revision("user/repo", "model", "fake-token")
        except urllib.error.HTTPError as error:
            check(
                "invalid token never falls back to anonymous metadata",
                error.code == 401 and not anonymous_api.called,
            )
        else:
            check("invalid token never falls back to anonymous metadata", False)

    with tempfile.TemporaryDirectory() as directory:
        with (
            patch.object(service, "_resolve_default_revision", return_value="develop"),
            patch.object(service, "_probe_download_file_metadata", return_value=None),
            patch.object(
                service,
                "_atomgit_list_repo_files",
                return_value=("model", ["data.txt"]),
            ) as listing,
            patch.object(service, "_download_atomgit_file") as download,
        ):
            service.AtomGitDownloadAdapter().download_file(
                repo_id="user/repo",
                filename="data.txt",
                repo_type="model",
                revision=None,
                token=None,
                local_dir=directory,
                force=False,
                checksum=False,
                resume=False,
            )
            check(
                "default revision reaches listing",
                listing.call_args.args[-1] == "develop",
            )
            check(
                "default revision reaches downloaded content",
                download.call_args.kwargs.get("revision") == "develop",
            )

    with tempfile.TemporaryDirectory() as directory:
        with (
            patch.object(service, "_resolve_default_revision") as resolve_default,
            patch.object(
                service,
                "_atomgit_list_repo_files",
                return_value=("model", ["data.txt"]),
            ) as listing,
            patch.object(service, "_download_atomgit_file") as download,
        ):
            service.AtomGitDownloadAdapter().download_snapshot(
                repo_id="user/repo",
                repo_type="model",
                revision="feature",
                token=None,
                local_dir=directory,
                force=False,
                checksum=False,
                resume=False,
                prune=False,
                allow_patterns=None,
                ignore_patterns=None,
            )
            check("explicit revision skips default lookup", not resolve_default.called)
            check(
                "explicit revision reaches snapshot listing",
                listing.call_args.args[-1] == "feature",
            )
            check(
                "explicit revision reaches snapshot content",
                download.call_args.kwargs.get("revision") == "feature",
            )

    original_hf_api = api_mod.HfApi
    original_open = api_mod._atomgit_open_url
    api_mod.HfApi = FakeHfApi
    try:
        result, error, calls = resolve(
            {None: [], "dataset": RuntimeError("404 dataset missing")}
        )
        check(
            "successful empty model survives later dataset 404",
            error is None and result == ("model", []),
            f"result={result!r} error={error!r}",
        )

        result, error, calls = resolve(
            {
                None: RuntimeError("401 Unauthorized"),
                "dataset": RuntimeError("404 Not Found"),
            }
        )
        check(
            "authentication failure is not hidden by later 404",
            error is not None and "401" in str(error),
            repr(error),
        )

        result, error, calls = resolve({None: ["same.bin"], "dataset": ["same.bin"]})
        check(
            "identical compatibility listings remain usable",
            error is None
            and result == ("model", ["same.bin"])
            and calls == [None, "dataset"],
            f"result={result!r} calls={calls!r}",
        )

        result, error, calls = resolve(
            {None: ["model.bin"], "dataset": ["dataset.csv"]}
        )
        check(
            "different listings require explicit repository type",
            error is not None and "repo-type" in str(error),
            repr(error),
        )
        check(
            "repository type ambiguity remains actionable after sanitizing",
            api_mod.sanitized_download_error(error)
            == "仓库类型不明确，请使用 --repo-type model 或 dataset",
        )

        result, error, calls = resolve(
            {None: ["model.bin"], "dataset": ["dataset.csv"]},
            repo_type="dataset",
        )
        check(
            "explicit dataset uses only dataset route",
            error is None
            and result == ("dataset", ["dataset.csv"])
            and calls == ["dataset"],
            f"result={result!r} calls={calls!r}",
        )

        opened_urls = []

        def always_missing(request, timeout=60):
            opened_urls.append(request.full_url)
            raise api_mod.urllib.error.HTTPError(
                request.full_url, 404, "Not Found", {}, None
            )

        api_mod._atomgit_open_url = always_missing
        with tempfile.TemporaryDirectory() as temporary_dir:
            try:
                api_mod._download_atomgit_file(
                    "user/repo",
                    "model",
                    "missing.bin",
                    Path(temporary_dir) / "missing.bin",
                    "fake-token",
                )
            except Exception:
                pass
        check(
            "resolve does not fall back to another repository type",
            len(opened_urls) == 1 and "/datasets/" not in opened_urls[0],
            repr(opened_urls),
        )
    finally:
        api_mod.HfApi = original_hf_api
        api_mod._atomgit_open_url = original_open

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
