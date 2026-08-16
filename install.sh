#!/bin/sh

set -eu

REPOSITORY="JoyJeeo/atomgit_cli"
API_URL="${ATOMGIT_RELEASE_API_URL:-https://api.github.com/repos/$REPOSITORY/releases}"
DOWNLOAD_BASE="${ATOMGIT_RELEASE_DOWNLOAD_BASE:-https://github.com/$REPOSITORY/releases/download}"

usage() {
    cat <<'EOF'
Install the AtomGit CLI from a completed, checksummed GitHub Release wheel.

Usage: install.sh [--version X.Y.Z] [--python PATH] [--force-reinstall] [--no-completion]

Options:
  --version VERSION       Exact stable Release version (X.Y.Z); default: latest completed Release
  --python PATH           Python interpreter to install into
  --force-reinstall       Pass --force-reinstall to pip
  --no-completion         Do not install Zsh completion
  -h, --help              Show this help
EOF
}

version=""
python_bin=""
force_reinstall=0
install_completion=1
while [ "$#" -gt 0 ]; do
    case "$1" in
        --version)
            [ "$#" -ge 2 ] || { echo "error: --version requires a value" >&2; exit 2; }
            version="$2"
            shift 2
            ;;
        --python)
            [ "$#" -ge 2 ] || { echo "error: --python requires a value" >&2; exit 2; }
            python_bin="$2"
            shift 2
            ;;
        --force-reinstall)
            force_reinstall=1
            shift
            ;;
        --no-completion)
            install_completion=0
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --coder|--developer|--source)
            echo "error: source development uses git checkout yuto and pip install -e .; install.sh is for ordinary users" >&2
            exit 2
            ;;
        *)
            echo "error: unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

case "$version" in
    ""|[0-9]*.[0-9]*.[0-9]*) : ;;
    *) echo "error: invalid stable version: $version" >&2; exit 2 ;;
esac

if [ -z "$python_bin" ]; then
    if [ -n "${CONDA_PREFIX:-}" ] && [ -x "$CONDA_PREFIX/bin/python" ]; then
        python_bin="$CONDA_PREFIX/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
        python_bin="$(command -v python3)"
    elif command -v python >/dev/null 2>&1; then
        python_bin="$(command -v python)"
    else
        echo "error: no supported Python interpreter found; use --python /path/to/python" >&2
        exit 1
    fi
fi

[ -x "$python_bin" ] || { echo "error: Python interpreter is not executable: $python_bin" >&2; exit 1; }
if ! "$python_bin" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
    echo "error: AtomGit CLI requires Python 3.9 or newer" >&2
    exit 1
fi
if ! "$python_bin" -m pip --version >/dev/null 2>&1; then
    echo "error: selected Python has no usable pip; create a venv/conda environment or choose another --python" >&2
    exit 1
fi
if [ -n "$version" ] && ! "$python_bin" -c 'import re, sys; raise SystemExit(0 if re.fullmatch(r"[0-9]+\\.[0-9]+\\.[0-9]+", sys.argv[1]) else 1)' "$version" >/dev/null 2>&1; then
    echo "error: invalid stable version: $version" >&2
    exit 2
fi

temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/atomgit-install.XXXXXX")
cleanup() {
    rm -rf "$temporary_dir"
}
trap cleanup EXIT HUP INT TERM

"$python_bin" - "$temporary_dir" "$version" "$API_URL" "$DOWNLOAD_BASE" "$force_reinstall" <<'PY'
import hashlib
import importlib.metadata
import json
import re
import subprocess
import sys
import sysconfig
import urllib.parse
import urllib.request
import zipfile
from email.parser import Parser
from pathlib import Path

directory = Path(sys.argv[1])
requested, api_url, download_base, force = sys.argv[2:]
max_response = 4 * 1024 * 1024
max_asset = 256 * 1024 * 1024
max_checksum = 1024 * 1024
stable = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")

def fail(message):
    raise SystemExit("error: " + message)

def get_bytes(url, limit):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        fail("release URL has a disallowed origin")
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "atomgit-cli-installer"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            initial_host = parsed.netloc.lower()
            final_host = urllib.parse.urlparse(response.geturl()).netloc.lower()
            allowed_hosts = {initial_host, "github.com", "api.github.com", "objects.githubusercontent.com"}
            if final_host not in allowed_hosts:
                fail("release download redirected to a disallowed origin")
            length = response.headers.get("Content-Length")
            if length and int(length) > limit:
                fail("release response exceeds the permitted size")
            data = response.read(limit + 1)
            if len(data) > limit:
                fail("release response exceeds the permitted size")
            return data
    except SystemExit:
        raise
    except Exception as error:
        fail(f"unable to download release data: {error}")

def stable_tuple(value):
    if not stable.fullmatch(value):
        fail(f"invalid stable Release tag: {value!r}")
    return tuple(int(part) for part in value.split("."))

try:
    releases = json.loads(get_bytes(api_url, max_response).decode("utf-8"))
except (UnicodeDecodeError, json.JSONDecodeError):
    fail("GitHub Releases response is not valid JSON")
if not isinstance(releases, list):
    fail("GitHub Releases response is not a list")
candidates = [item for item in releases if isinstance(item, dict) and not item.get("draft") and not item.get("prerelease") and stable.fullmatch(item.get("tag_name", ""))]
if requested:
    candidates = [item for item in candidates if item.get("tag_name") == requested]
if not candidates:
    fail("no completed GitHub Release found for " + (requested or "latest stable version"))
release = max(candidates, key=lambda item: stable_tuple(item["tag_name"]))
target = release["tag_name"]
wheel_name = f"atomgit-{target}-py3-none-any.whl"
assets = release.get("assets")
if not isinstance(assets, list):
    fail("GitHub Release has no valid asset list")
named = {}
for asset in assets:
    if isinstance(asset, dict) and asset.get("name") in (wheel_name, "SHA256SUMS"):
        named.setdefault(asset["name"], []).append(asset)
if len(named.get(wheel_name, [])) != 1 or len(named.get("SHA256SUMS", [])) != 1:
    fail("Release must contain exactly one expected wheel and SHA256SUMS asset")
urls = {
    name: named[name][0].get("browser_download_url") or f"{download_base.rstrip('/')}/{target}/{name}"
    for name in (wheel_name, "SHA256SUMS")
}
wheel = directory / wheel_name
checksums = directory / "SHA256SUMS"
wheel.write_bytes(get_bytes(urls[wheel_name], max_asset))
checksums.write_bytes(get_bytes(urls["SHA256SUMS"], max_checksum))
text = checksums.read_text(encoding="utf-8")
entries = []
for raw in text.splitlines():
    line = raw.strip()
    if not line:
        continue
    match = re.fullmatch(r"([0-9a-fA-F]{64})\s+(\*?\S+)", line)
    if not match:
        fail("SHA256SUMS contains a malformed entry")
    digest, name = match.groups()
    entries.append((digest.lower(), name.lstrip("*")))
matches = [digest for digest, name in entries if name == wheel_name]
if len(matches) != 1:
    fail("SHA256SUMS must contain exactly one wheel entry")
if hashlib.sha256(wheel.read_bytes()).hexdigest() != matches[0]:
    fail("wheel checksum does not match SHA256SUMS")
try:
    with zipfile.ZipFile(wheel) as archive:
        metadata_names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(metadata_names) != 1:
            fail("wheel has ambiguous or missing metadata")
        metadata = Parser().parsestr(archive.read(metadata_names[0]).decode("utf-8"))
except Exception as error:
    if isinstance(error, SystemExit):
        raise
    fail("wheel is not a valid readable archive")
if metadata.get("Name", "").lower() != "atomgit" or metadata.get("Version") != target:
    fail("wheel metadata does not match atomgit " + target)
command = [sys.executable, "-m", "pip", "install"]
if force == "1":
    command.append("--force-reinstall")
command.append(str(wheel))
if subprocess.run(command, check=False).returncode:
    fail("pip failed; use a venv/conda environment or an explicit writable --python")
checks = [
    [sys.executable, "-m", "atomgit", "--help"],
    [sys.executable, "-m", "atomgit", "--version"],
    [sys.executable, "-c", "import atomgit, atomgit_hub"],
]
for check in checks:
    if subprocess.run(check, check=False).returncode:
        fail("post-install verification failed")
print(f"AtomGit CLI {target} installed into {sys.executable}")
print("Package location: " + str(importlib.metadata.distribution('atomgit').locate_file('')))
print("Command directory: " + sysconfig.get_path('scripts'))
print("Command visibility: " + ("visible" if Path(sysconfig.get_path('scripts'), 'atomgit').exists() else "not visible on PATH"))
print("Package and command verification passed.")
PY

if [ "$install_completion" -eq 1 ]; then
    case "${SHELL:-}" in
        */zsh)
            if "$python_bin" -m atomgit completion install --shell zsh; then
                echo "Zsh completion installed successfully."
            else
                echo "warning: AtomGit CLI was installed, but Zsh completion setup failed" >&2
                echo "warning: retry with: $python_bin -m atomgit completion install --shell zsh" >&2
            fi
            ;;
        *)
            echo "Shell is not Zsh; completion setup skipped."
            ;;
    esac
fi
