"""Release-channel installation and update policy.

This module intentionally uses only the Python standard library.  The POSIX
bootstrap can therefore use the same validation rules before the target
environment has AtomGit installed.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
import subprocess
import sys
import sysconfig
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from email.parser import Parser
from pathlib import Path

try:
    from .lifecycle.environment import is_source_or_editable_install
except ImportError:
    from lifecycle.environment import is_source_or_editable_install


PROJECT = "JoyJeeo/atomgit_cli"
DEFAULT_API_URL = f"https://api.github.com/repos/{PROJECT}/releases"
DEFAULT_DOWNLOAD_BASE = f"https://github.com/{PROJECT}/releases/download"
STABLE_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_ASSET_BYTES = 256 * 1024 * 1024
MAX_CHECKSUM_BYTES = 1024 * 1024
REQUEST_TIMEOUT = 20


class ReleaseError(RuntimeError):
    """Actionable, user-safe release-channel failure."""


class ReleaseValidationError(ReleaseError):
    """An untrusted release response or asset failed validation."""


def is_stable_version(value):
    return isinstance(value, str) and bool(STABLE_VERSION_RE.fullmatch(value))


def version_tuple(value):
    if not is_stable_version(value):
        raise ReleaseValidationError(f"invalid stable version: {value!r}")
    return tuple(int(part) for part in value.split("."))


def select_release(releases, version=None):
    """Select a completed pure-numeric release from parsed GitHub JSON."""
    if not isinstance(releases, list):
        raise ReleaseValidationError("GitHub Releases response is not a list")
    candidates = []
    for release in releases:
        if not isinstance(release, dict):
            continue
        tag = release.get("tag_name")
        if release.get("draft") or release.get("prerelease") or not is_stable_version(tag):
            continue
        if version is not None and tag != version:
            continue
        candidates.append((version_tuple(tag), release))
    if version is not None:
        return candidates[0][1] if candidates else None
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def _bounded_read(response, limit):
    content_length = response.headers.get("Content-Length")
    if content_length:
        try:
            too_large = int(content_length) > limit
        except ValueError as error:
            raise ReleaseValidationError("release response has an invalid size") from error
        if too_large:
            raise ReleaseValidationError("release response exceeds the permitted size")
    data = response.read(limit + 1)
    if len(data) > limit:
        raise ReleaseValidationError("release response exceeds the permitted size")
    return data


def _allowed_origin(url, allowed_origins):
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme == "https" and parsed.netloc.lower() in allowed_origins


class _BoundedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_origins):
        super().__init__()
        self.allowed_origins = allowed_origins

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _allowed_origin(newurl, self.allowed_origins):
            raise ReleaseValidationError("release download redirected to a disallowed origin")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_bytes(url, *, limit=MAX_RESPONSE_BYTES, timeout=REQUEST_TIMEOUT, allowed_origins=None):
    parsed = urllib.parse.urlparse(url)
    if allowed_origins is None:
        allowed_origins = {parsed.netloc.lower()}
    if not _allowed_origin(url, allowed_origins):
        raise ReleaseValidationError("release URL has a disallowed origin")
    opener = urllib.request.build_opener(_BoundedRedirectHandler(allowed_origins))
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "atomgit-cli-installer"},
    )
    try:
        with opener.open(request, timeout=timeout) as response:
            final_url = response.geturl()
            if not _allowed_origin(final_url, allowed_origins):
                raise ReleaseValidationError("release response ended at a disallowed origin")
            return _bounded_read(response, limit)
    except ReleaseError:
        raise
    except (OSError, urllib.error.URLError) as error:
        raise ReleaseError(f"unable to download release data: {error}") from error


def fetch_releases(api_url=None):
    api_url = api_url or os.environ.get("ATOMGIT_RELEASE_API_URL", DEFAULT_API_URL)
    if "per_page=" not in api_url:
        api_url += "&per_page=100" if "?" in api_url else "?per_page=100"
    parsed = urllib.parse.urlparse(api_url)
    allowed = {parsed.netloc.lower()}
    payload = fetch_bytes(api_url, allowed_origins=allowed)
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseValidationError("GitHub Releases response is not valid JSON") from error
    return value


def resolve_release(version=None, *, api_url=None):
    if version is not None and not is_stable_version(version):
        raise ReleaseValidationError(f"invalid stable version: {version!r}")
    release = select_release(fetch_releases(api_url), version)
    if release is None:
        requested = version or "a completed stable release"
        raise ReleaseError(f"no completed GitHub Release found for {requested}")
    return release


def _release_assets(release, version, download_base=None):
    wheel_name = f"atomgit-{version}-py3-none-any.whl"
    checksum_name = "SHA256SUMS"
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise ReleaseValidationError("GitHub Release has no valid asset list")
    matches = {}
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = asset.get("name")
        if name in (wheel_name, checksum_name):
            matches.setdefault(name, []).append(asset)
    if len(matches.get(wheel_name, [])) != 1 or len(matches.get(checksum_name, [])) != 1:
        raise ReleaseValidationError("Release must contain exactly one expected wheel and checksum asset")
    base = download_base or os.environ.get("ATOMGIT_RELEASE_DOWNLOAD_BASE", DEFAULT_DOWNLOAD_BASE)
    urls = {}
    for name in (wheel_name, checksum_name):
        urls[name] = matches[name][0].get("browser_download_url") or f"{base.rstrip('/')}/{version}/{name}"
    return wheel_name, urls


def validate_checksum(checksum_text, wheel_name):
    if not isinstance(checksum_text, str) or len(checksum_text.encode("utf-8")) > MAX_CHECKSUM_BYTES:
        raise ReleaseValidationError("SHA256SUMS is missing or oversized")
    found = []
    for raw_line in checksum_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+(\*?\S+)", line)
        if not match:
            raise ReleaseValidationError("SHA256SUMS contains a malformed entry")
        digest, name = match.groups()
        name = name[1:] if name.startswith("*") else name
        if name == wheel_name:
            found.append(digest.lower())
    if len(found) != 1:
        raise ReleaseValidationError("SHA256SUMS must contain exactly one wheel entry")
    return found[0]


def validate_wheel_metadata(wheel_path, expected_version):
    expected_version = version_tuple(expected_version)
    try:
        with zipfile.ZipFile(wheel_path) as archive:
            metadata_names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
            if len(metadata_names) != 1:
                raise ReleaseValidationError("wheel has ambiguous or missing metadata")
            metadata = Parser().parsestr(archive.read(metadata_names[0]).decode("utf-8"))
    except (OSError, zipfile.BadZipFile, KeyError, UnicodeDecodeError) as error:
        raise ReleaseValidationError("wheel is not a valid readable archive") from error
    if metadata.get("Name", "").lower() != "atomgit":
        raise ReleaseValidationError("wheel distribution name is not atomgit")
    if version_tuple(metadata.get("Version", "")) != expected_version:
        raise ReleaseValidationError("wheel metadata version does not match the Release")
    return True


def validate_release_assets(wheel_path, checksum_text, expected_version):
    wheel_name = Path(wheel_path).name
    expected_name = f"atomgit-{expected_version}-py3-none-any.whl"
    if wheel_name != expected_name:
        raise ReleaseValidationError("wheel filename does not match the Release version")
    expected_digest = validate_checksum(checksum_text, wheel_name)
    actual_digest = hashlib.sha256(Path(wheel_path).read_bytes()).hexdigest()
    if actual_digest != expected_digest:
        raise ReleaseValidationError("wheel checksum does not match SHA256SUMS")
    validate_wheel_metadata(wheel_path, expected_version)
    return True


def _download_asset(url, target, *, limit=MAX_RESPONSE_BYTES, allowed_origins=None):
    parsed = urllib.parse.urlparse(url)
    allowed = set(allowed_origins or ())
    allowed.update({parsed.netloc.lower(), "github.com", "api.github.com", "objects.githubusercontent.com"})
    data = fetch_bytes(url, limit=limit, allowed_origins=allowed)
    Path(target).write_bytes(data)


def _installed_version(python):
    code = "import importlib.metadata; print(importlib.metadata.version('atomgit'))"
    result = subprocess.run([python, "-c", code], check=False, capture_output=True, text=True)
    if result.returncode:
        raise ReleaseError("installed AtomGit distribution could not be verified")
    value = result.stdout.strip()
    if not is_stable_version(value):
        raise ReleaseError("installed AtomGit version is not a stable release")
    return value


def verify_installation(python, expected_version):
    actual = _installed_version(python)
    if actual != expected_version:
        raise ReleaseError(f"installation reported {actual}, expected {expected_version}")
    checks = [
        [python, "-m", "atomgit", "--help"],
        [python, "-m", "atomgit", "--version"],
        [python, "-c", "import atomgit, atomgit_hub"],
    ]
    for command in checks:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        if result.returncode:
            raise ReleaseError(f"post-install verification failed: {' '.join(command[1:])}")
    return actual


_is_source_or_editable_install = is_source_or_editable_install


def install_release(version=None, *, python=sys.executable, force_reinstall=False, api_url=None, download_base=None):
    release = resolve_release(version, api_url=api_url)
    target_version = release["tag_name"]
    wheel_name, urls = _release_assets(release, target_version, download_base)
    download_origin = urllib.parse.urlparse(
        download_base or os.environ.get("ATOMGIT_RELEASE_DOWNLOAD_BASE", DEFAULT_DOWNLOAD_BASE)
    ).netloc.lower()
    with tempfile.TemporaryDirectory(prefix="atomgit-release-") as directory:
        wheel_path = Path(directory) / wheel_name
        checksum_path = Path(directory) / "SHA256SUMS"
        _download_asset(
            urls[wheel_name],
            wheel_path,
            limit=MAX_ASSET_BYTES,
            allowed_origins={download_origin},
        )
        _download_asset(
            urls["SHA256SUMS"],
            checksum_path,
            limit=MAX_CHECKSUM_BYTES,
            allowed_origins={download_origin},
        )
        validate_release_assets(wheel_path, checksum_path.read_text(encoding="utf-8"), target_version)
        command = [python, "-m", "pip", "install"]
        if force_reinstall:
            command.append("--force-reinstall")
        command.append(str(wheel_path))
        result = subprocess.run(command, check=False, text=True)
        if result.returncode:
            raise ReleaseError("pip failed to install the verified AtomGit wheel")
    verify_installation(python, target_version)
    target_scripts = subprocess.run(
        [python, "-c", "import sysconfig; print(sysconfig.get_path('scripts'))"],
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    scripts = target_scripts or "the target interpreter's scripts directory"
    package_location = subprocess.run(
        [python, "-c", "import importlib.metadata; print(importlib.metadata.distribution('atomgit').locate_file(''))"],
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    candidate_command = Path(scripts) / ("atomgit.exe" if os.name == "nt" else "atomgit")
    command_path = str(candidate_command) if candidate_command.exists() else "not visible on PATH"
    return {
        "status": "installed",
        "version": target_version,
        "python": python,
        "package": package_location,
        "scripts": scripts,
        "command": command_path,
    }


def run_update(*, version=None, force_reinstall=False, python=sys.executable, api_url=None, download_base=None):
    if _is_source_or_editable_install():
        return {"status": "source", "version": None, "python": python}
    try:
        installed = _installed_version(python)
    except ReleaseError:
        installed = None
    release = resolve_release(version, api_url=api_url)
    target = release["tag_name"]
    if version is None and installed and version_tuple(target) < version_tuple(installed):
        raise ReleaseError("latest completed Release is older than the installed version; use --version to downgrade")
    if installed == target and not force_reinstall:
        return {"status": "skipped", "version": target, "python": python}
    try:
        result = install_release(
            target,
            python=python,
            force_reinstall=force_reinstall,
            api_url=api_url,
            download_base=download_base,
        )
        prefix_result = subprocess.run(
            [python, "-c", "import pathlib, sys; print(pathlib.Path(sys.prefix).resolve())"],
            check=False,
            capture_output=True,
            text=True,
        )
        conda_prefix = os.environ.get("CONDA_PREFIX")
        matching_prefix = None
        if conda_prefix and prefix_result.returncode == 0:
            try:
                candidate = Path(conda_prefix).resolve(strict=True)
                if candidate == Path(prefix_result.stdout.strip()):
                    matching_prefix = candidate
            except OSError:
                matching_prefix = None
        activation_hook = (
            matching_prefix / "etc/conda/activate.d/atomgit-completion.sh"
            if matching_prefix
            else None
        )
        if activation_hook and activation_hook.is_file():
            completion_result = subprocess.run(
                [python, "-m", "atomgit", "completion", "install", "--shell", "zsh"],
                check=False,
                capture_output=True,
                text=True,
            )
            if completion_result.returncode:
                result["completion_warning"] = "managed Zsh completion refresh failed"
        return result
    except ReleaseError as error:
        recovery = (
            f"recovery: rerun install.sh --version {installed} --python {python} "
            "or reinstall that exact checked Release wheel"
            if installed
            else "recovery: rerun the installer for a known completed Release"
        )
        raise ReleaseError(f"{error}; {recovery}") from error


def _main(argv=None):
    parser = argparse.ArgumentParser(description="AtomGit Release installer core")
    parser.add_argument("--version")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--force-reinstall", action="store_true")
    args = parser.parse_args(argv)
    result = install_release(args.version, python=args.python, force_reinstall=args.force_reinstall)
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
