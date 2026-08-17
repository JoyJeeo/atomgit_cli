#!/bin/sh

set -eu

usage() {
    cat <<'EOF'
Uninstall AtomGit CLI from the selected Python and clean its current conda environment hooks.

Usage: uninstall.sh [--python PATH]

Options:
  --python PATH  Python interpreter to uninstall from
  -h, --help     Show this help
EOF
}

python_bin=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --python)
            [ "$#" -ge 2 ] || { echo "error: --python requires a value" >&2; exit 2; }
            python_bin="$2"
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

if [ -z "$python_bin" ]; then
    if [ -n "${CONDA_PREFIX:-}" ] && [ -x "$CONDA_PREFIX/bin/python" ]; then
        python_bin="$CONDA_PREFIX/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
        python_bin=$(command -v python3)
    elif command -v python >/dev/null 2>&1; then
        python_bin=$(command -v python)
    else
        echo "error: no Python interpreter found; use --python PATH" >&2
        exit 1
    fi
fi

[ -x "$python_bin" ] || { echo "error: Python interpreter is not executable: $python_bin" >&2; exit 1; }

if "$python_bin" -c 'import importlib.metadata as m; m.distribution("atomgit")' >/dev/null 2>&1; then
    exec "$python_bin" -m atomgit uninstall --yes
fi

"$python_bin" - "${CONDA_PREFIX:-}" <<'PY'
import os
import stat
import sys
from pathlib import Path

raw_conda_prefix = sys.argv[1]
python_prefix = Path(sys.prefix).resolve()
print(f"Python 解释器: {sys.executable}")
print(f"环境根目录: {python_prefix}")
print("AtomGit 状态: 当前 Python 中已不存在该包")

if not raw_conda_prefix:
    print("环境补全文件: 无（当前解释器不属于活动 conda 环境）")
    raise SystemExit(0)

conda_prefix = Path(raw_conda_prefix).expanduser()
if not conda_prefix.is_absolute():
    raise SystemExit("error: CONDA_PREFIX must be absolute")
try:
    conda_prefix = conda_prefix.resolve(strict=True)
except OSError as error:
    raise SystemExit(f"error: unable to resolve CONDA_PREFIX: {error}")
if conda_prefix != python_prefix:
    raise SystemExit("error: CONDA_PREFIX does not match the selected Python environment")

relative_paths = (
    Path("share/atomgit/completions/atomgit.zsh"),
    Path("etc/conda/activate.d/atomgit-completion.sh"),
    Path("etc/conda/deactivate.d/atomgit-completion.sh"),
)
targets = tuple(conda_prefix / relative for relative in relative_paths)
print("将删除的环境补全文件:")
for target in targets:
    print(f"  {target}")

snapshots = []

def managed_parent_exists(target):
    current = conda_prefix
    for component in target.relative_to(conda_prefix).parts[:-1]:
        current = current / component
        try:
            parent_stat = current.lstat()
        except FileNotFoundError:
            return False
        if stat.S_ISLNK(parent_stat.st_mode) or not stat.S_ISDIR(parent_stat.st_mode):
            raise SystemExit(
                f"error: refusing to remove through non-directory managed parent: {current}"
            )
    return True

for target in targets:
    if not managed_parent_exists(target):
        continue
    try:
        file_stat = target.lstat()
    except FileNotFoundError:
        continue
    if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
        raise SystemExit(f"error: refusing to remove non-regular managed file: {target}")
    snapshots.append(
        (
            target,
            file_stat.st_dev,
            file_stat.st_ino,
            file_stat.st_mode,
            file_stat.st_size,
            file_stat.st_mtime_ns,
        )
    )

for target, device, inode, mode, size, mtime_ns in snapshots:
    try:
        current = target.lstat()
    except FileNotFoundError:
        raise SystemExit(f"error: managed file disappeared concurrently: {target}")
    if (
        current.st_dev,
        current.st_ino,
        current.st_mode,
        current.st_size,
        current.st_mtime_ns,
    ) != (device, inode, mode, size, mtime_ns):
        raise SystemExit(f"error: managed file changed concurrently: {target}")
    target.unlink()

print("AtomGit 环境补全已清理。")
print("当前 shell 可能仍加载旧补全；请执行 conda deactivate/activate 或 exec zsh。")
PY
