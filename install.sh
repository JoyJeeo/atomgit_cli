#!/bin/sh

set -eu

DEFAULT_VERSION="1.0.5-yuto.1"
RELEASE_BASE_URL="${ATOMGIT_INSTALL_BASE_URL:-https://github.com/JoyJeeo/atomgit_cli/releases/download}"

usage() {
    cat <<'EOF'
Install a checksummed AtomGit CLI yuto wheel into the active conda environment.

Usage: install.sh [--version VERSION]

Options:
  --version VERSION  Release version, default: 1.0.5-yuto.1
  -h, --help         Show this help
EOF
}

version="$DEFAULT_VERSION"
while [ "$#" -gt 0 ]; do
    case "$1" in
        --version)
            [ "$#" -ge 2 ] || { echo "error: --version requires a value" >&2; exit 2; }
            version="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "error: unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

case "$version" in
    ""|*[!0-9A-Za-z._-]*)
        echo "error: invalid version: $version" >&2
        exit 2
        ;;
esac

if [ -z "${CONDA_PREFIX:-}" ]; then
    echo "error: activate the target conda environment before installing" >&2
    exit 1
fi

python_bin="$CONDA_PREFIX/bin/python"
if [ ! -x "$python_bin" ]; then
    echo "error: active conda Python not found: $python_bin" >&2
    exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
    echo "error: curl is required" >&2
    exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
    checksum_command="sha256sum"
elif command -v shasum >/dev/null 2>&1; then
    checksum_command="shasum -a 256"
else
    echo "error: sha256sum or shasum is required" >&2
    exit 1
fi

package_version=$(printf '%s' "$version" | sed 's/-yuto\./+yuto./')
encoded_package_version=$(printf '%s' "$package_version" | sed 's/+/%2B/g')
tag="v$version"
wheel_name="atomgit-$package_version-py3-none-any.whl"
wheel_url="$RELEASE_BASE_URL/$tag/atomgit-$encoded_package_version-py3-none-any.whl"
checksums_url="$RELEASE_BASE_URL/$tag/SHA256SUMS"

temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/atomgit-install.XXXXXX")
cleanup() {
    rm -rf "$temporary_dir"
}
trap cleanup EXIT HUP INT TERM

echo "Downloading AtomGit CLI $version..."
curl -fsSL "$wheel_url" -o "$temporary_dir/$wheel_name"
curl -fsSL "$checksums_url" -o "$temporary_dir/SHA256SUMS"

checksum_line=$(awk -v name="$wheel_name" '$2 == name || $2 == "*" name { print; exit }' "$temporary_dir/SHA256SUMS")
if [ -z "$checksum_line" ]; then
    echo "error: SHA256SUMS has no entry for $wheel_name" >&2
    exit 1
fi
printf '%s\n' "$checksum_line" > "$temporary_dir/WHEEL.SHA256"

if ! (cd "$temporary_dir" && $checksum_command -c WHEEL.SHA256 >/dev/null); then
    echo "error: checksum verification failed for $wheel_name" >&2
    exit 1
fi

echo "Checksum verified. Installing into $CONDA_PREFIX..."
"$python_bin" -m pip install "$temporary_dir/$wheel_name"
echo "AtomGit CLI $version installed successfully."
