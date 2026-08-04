import os
import sys
import subprocess
import json
import tempfile
from pathlib import Path
from typing import Optional, List
from colorama import Fore, Style, init
import urllib.parse

# 初始化colorama
init(autoreset=True)


_GIT_CREDENTIAL_HOSTS = ("atomgit.com", "hub.atomgit.com")
_GIT_HELPER_STATE_VERSION = 1
_GIT_HELPER_STATE_FILENAME = "git-helper-state.json"


def is_auth_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(marker in message for marker in (
        "401", "403", "unauthorized", "forbidden", "no scopes",
    ))


def is_retryable_download_error(error: Exception) -> bool:
    error_name = type(error).__name__
    message = str(error).lower()
    return error_name in {
        "ChunkedEncodingError",
        "ConnectError",
        "ConnectionError",
        "ReadError",
        "ReadTimeout",
        "RemoteProtocolError",
    } or any(marker in message for marker in (
        "incomplete message body",
        "peer closed connection",
        "connection reset",
        "connection aborted",
        "read timed out",
    ))


def run_download_with_retry(operation):
    """Retry once when an interrupted response can reuse HF partial state."""
    try:
        return operation()
    except Exception as error:
        if not is_retryable_download_error(error):
            raise
    return operation()


def sanitized_download_error(error: Exception) -> str:
    """Return an actionable category without exposing remote or signed URLs."""
    if is_auth_error(error):
        return "认证失败或权限不足，请检查登录状态和仓库权限"
    if is_retryable_download_error(error):
        return "下载连接中断，自动重试后仍失败，请重新执行下载命令"
    message = str(error).lower()
    if "404" in message or "not found" in message:
        return "仓库、文件或 revision 不存在"
    if "timeout" in message or "timed out" in message:
        return "下载请求超时，请检查网络后重试"
    return f"下载失败（{type(error).__name__}）"


def print_success(message: str) -> None:
    """打印成功信息"""
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def print_error(message: str) -> None:
    """打印错误信息"""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")


def print_warning(message: str) -> None:
    """打印警告信息"""
    print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


def print_info(message: str) -> None:
    """打印信息"""
    print(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")


def validate_repo_name(repo_name: str) -> bool:
    """验证仓库名称格式"""
    if not repo_name:
        return False
    
    # 先解码URL编码
    decoded_name = urllib.parse.unquote(repo_name)
    
    # 检查是否包含至少一个斜杠（在解码后的名称中）
    if '/' not in decoded_name:
        return False
    
    parts = decoded_name.split('/')
    # 支持多层次仓库名称，至少需要2个部分，但可以有更多
    # 允许hf_mirrors/Qwen/Qwen3-Reranker-0.6B这样的格式
    if len(parts) < 2:
        return False
    
    # 检查每个部分都不为空
    for part in parts:
        if not part:
            return False
    
    # 检查字符是否合法（字母、数字、下划线、短横线、点号、斜杠）
    # 对于原始名称，也允许%字符用于URL编码
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.%/')
    
    # 验证原始名称的字符
    for char in repo_name:
        if char not in allowed_chars:
            return False
    
    return True


def validate_repo_type(repo_type: str) -> bool:
    """验证仓库类型"""
    return repo_type in ['model', 'dataset']


def is_supported_upload_revision(revision: Optional[str]) -> bool:
    """Return whether AtomGit can safely target the requested upload revision."""
    return revision in (None, "", "main")


def normalize_repo_id(repo_id: str) -> str:
    """Map AtomGit multi-level names to its HF-compatible repository ID."""
    parts = repo_id.split('/')
    if len(parts) < 3:
        return repo_id
    return f"{parts[0]}-{parts[1]}/{'/'.join(parts[2:])}"


def normalize_path_in_repo(path_in_repo: Optional[str]) -> Optional[str]:
    """规范化和校验仓库内路径前缀（用于 upload 的 --path-in-repo）。

    - 去除首尾的 ``./`` ``/`` 及空片段，统一为 ``a/b/c`` 形式
    - 拒绝包含 ``..`` 的路径（防止路径穿越，保护仓库其它目录）
    - 返回规范化后的字符串；空或仅 ``./`` 时返回 None（表示仓库根目录）

    Raises:
        ValueError: 当路径包含 ``..`` 片段时。
    """
    if not path_in_repo:
        return None
    # 统一斜杠并拆分，丢弃空片段与当前目录标记 "."
    parts = [p for p in path_in_repo.replace("\\", "/").split("/") if p and p != "."]
    if ".." in parts:
        raise ValueError("path_in_repo 不能包含 '..'（禁止路径穿越）")
    return "/".join(parts) if parts else None


def parse_ignore_patterns(raw: Optional[str]) -> Optional[List[str]]:
    """解析 ``--ignore`` 选项的逗号分隔字符串为 HF ignore_patterns 列表。

    - 输入可为 None / 空字符串 / 空白 → 返回 None（表示不忽略任何文件）
    - 按逗号拆分，去空白与首尾空格，丢弃空片段
    - 去重后保持顺序；返回 None 以便调用方仅在不忽略时不向 HF 传该参数

    HF 的 ignore_patterns 支持 fnmatch/glob 风格，如 ``*.tmp``、``logs/``、
    ``**/.DS_Store`` 等。
    """
    if not raw:
        return None
    seen = set()
    patterns = []
    for p in raw.split(","):
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            patterns.append(p)
    return patterns or None


def get_file_size(file_path: Path) -> int:
    """获取文件大小"""
    try:
        return file_path.stat().st_size
    except OSError:
        return 0


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def _is_resumable_metadata(path: Path, root: Path) -> bool:
    """Return whether a file belongs to HF's resumable metadata subtree."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    parts = relative.parts
    return len(parts) >= 2 and parts[0] == ".cache" and parts[1] == "huggingface"


def get_directory_size(dir_path: Path, exclude_resumable_metadata: bool = False) -> int:
    """获取目录大小"""
    total_size = 0
    try:
        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and not (exclude_resumable_metadata and _is_resumable_metadata(file_path, dir_path)):
                total_size += get_file_size(file_path)
    except OSError:
        pass
    return total_size


def count_files_in_directory(dir_path: Path, exclude_resumable_metadata: bool = False) -> int:
    """统计目录中的文件数量"""
    count = 0
    try:
        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and not (exclude_resumable_metadata and _is_resumable_metadata(file_path, dir_path)):
                count += 1
    except OSError:
        pass
    return count


def confirm_action(message: str, default: bool = False) -> bool:
    """确认操作"""
    suffix = " [Y/n]" if default else " [y/N]"
    while True:
        response = input(f"{message}{suffix}: ").strip().lower()
        if response == '':
            return default
        elif response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("请输入 y/yes 或 n/no")


def is_valid_path(path_str: str) -> bool:
    """检查路径是否有效"""
    try:
        Path(path_str)
        return True
    except (ValueError, OSError):
        return False


def ensure_directory(dir_path: Path) -> bool:
    """确保目录存在"""
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False


def get_relative_path(file_path: Path, base_path: Path) -> str:
    """获取相对路径"""
    try:
        return str(file_path.relative_to(base_path))
    except ValueError:
        return str(file_path)


def _git_helper_key(host: str) -> str:
    return f"credential.https://{host}.helper"


def _get_global_git_values(key: str) -> List[str]:
    result = subprocess.run(
        ["git", "config", "--global", "--get-all", key],
        capture_output=True,
        text=True,
    )
    if result.returncode == 1:
        return []
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"无法读取 Git 配置: {key}")
    return result.stdout.splitlines()


def _set_global_git_values(key: str, values: List[str]) -> None:
    if values:
        commands = [
            ["git", "config", "--global", "--replace-all", key, values[0]],
            *(
                ["git", "config", "--global", "--add", key, value]
                for value in values[1:]
            ),
        ]
    else:
        commands = [["git", "config", "--global", "--unset-all", key]]

    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            if not values and not _get_global_git_values(key):
                return
            raise RuntimeError(
                result.stderr.strip() or f"无法更新 Git 配置: {key}"
            )


def _restore_global_git_values(values_by_host) -> None:
    failures = []
    for host in _GIT_CREDENTIAL_HOSTS:
        try:
            _set_global_git_values(
                _git_helper_key(host), list(values_by_host.get(host, []))
            )
        except Exception as error:
            failures.append(f"{host}: {error}")
    if failures:
        raise RuntimeError("; ".join(failures))


def _write_bytes_atomic(path: Path, content: bytes, mode: int) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
        os.replace(temporary_path, path)
        path.chmod(mode)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        temporary_path.unlink(missing_ok=True)
        raise


def _write_helper_state(path: Path, values_by_host) -> None:
    payload = {
        "version": _GIT_HELPER_STATE_VERSION,
        "hosts": {
            host: list(values_by_host.get(host, []))
            for host in _GIT_CREDENTIAL_HOSTS
        },
    }
    content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    _write_bytes_atomic(path, content, 0o600)


def _load_helper_state(path: Path):
    if not path.exists():
        return None
    path.chmod(0o600)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Git 凭证配置备份无法读取: {error}") from error

    hosts = payload.get("hosts")
    if (
        payload.get("version") != _GIT_HELPER_STATE_VERSION
        or not isinstance(hosts, dict)
    ):
        raise RuntimeError("Git 凭证配置备份格式不受支持")
    for host in _GIT_CREDENTIAL_HOSTS:
        values = hosts.get(host)
        if not isinstance(values, list) or not all(
            isinstance(value, str) for value in values
        ):
            raise RuntimeError("Git 凭证配置备份内容无效")
    return {host: list(hosts[host]) for host in _GIT_CREDENTIAL_HOSTS}


def _legacy_cleanup_values(values: List[str], helper_value: str) -> List[str]:
    cleaned = []
    for value in values:
        if value == helper_value:
            if cleaned and cleaned[-1] == "":
                cleaned.pop()
            continue
        cleaned.append(value)
    return cleaned


def setup_git_credentials(token: str) -> bool:
    """配置Git凭证助手，使用保存的token"""
    config_dir = Path.home() / '.atomgit'
    credential_helper_path = config_dir / 'git-credential-atomgit'
    state_path = config_dir / _GIT_HELPER_STATE_FILENAME
    previous_values = None
    previous_helper = None
    previous_helper_mode = None
    created_state = False
    try:
        # 获取配置目录
        config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        config_dir.chmod(0o700)
        
        # 创建凭证助手脚本
        if credential_helper_path.exists():
            previous_helper = credential_helper_path.read_bytes()
            previous_helper_mode = credential_helper_path.stat().st_mode & 0o777

        # 创建凭证助手脚本内容
        helper_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AtomGit Git Credential Helper
自动提供保存的AtomGit token用于Git认证，并从API获取真实用户名
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

def get_atomgit_username(token):
    """通过AtomGit API获取用户名"""
    try:
        # 调用AtomGit API获取用户信息
        api_url = 'https://atomgit.com/api/v5/user'
        req = urllib.request.Request(
            api_url,
            headers={
                'Authorization': token,
                'User-Agent': 'atomgit-cli',
                'Accept': 'application/json'
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                login = data.get('login')
                if login:
                    return login
    except Exception:
        return None
    return None

def main():
    operation = sys.argv[1] if len(sys.argv) > 1 else 'get'
    
    if operation == 'get':
        # 读取Git传递的信息
        input_data = {}
        for line in sys.stdin:
            line = line.strip()
            if not line:
                break
            key, value = line.split('=', 1)
            input_data[key] = value
        
        # 检查是否为AtomGit主机（支持多个域名）
        host = input_data.get('host', '')
        if host in ['atomgit.com', 'hub.atomgit.com']:
            # 读取保存的token
            config_file = Path.home() / '.atomgit' / 'config.json'
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    token = config.get('token')
                    if token:
                        # 获取真实的AtomGit用户名
                        username = get_atomgit_username(token)
                        if username:
                            print(f'username={username}')
                            print(f'password={token}')
                            return
                except Exception:
                    pass
    
    # 对于store和erase操作，什么都不做
    elif operation in ['store', 'erase']:
        # 读取并忽略输入
        for line in sys.stdin:
            if not line.strip():
                break

if __name__ == '__main__':
    main()
'''

        previous_values = {
            host: _get_global_git_values(_git_helper_key(host))
            for host in _GIT_CREDENTIAL_HOSTS
        }
        original_values = _load_helper_state(state_path)
        if original_values is None:
            _write_helper_state(state_path, previous_values)
            created_state = True

        _write_bytes_atomic(
            credential_helper_path, helper_script.encode("utf-8"), 0o755
        )
        managed_values = ["", f"!{credential_helper_path}"]
        for host in _GIT_CREDENTIAL_HOSTS:
            _set_global_git_values(_git_helper_key(host), managed_values)
        
        print_success(f"Git凭证助手配置成功，现在可以直接使用git命令访问AtomGit仓库")
        return True
        
    except Exception as e:
        configuration_restored = True
        if previous_values is not None:
            try:
                _restore_global_git_values(previous_values)
            except Exception as rollback_error:
                configuration_restored = False
                print_error(f"Git凭证配置回滚失败: {rollback_error}")
        if configuration_restored:
            try:
                if previous_helper is None:
                    credential_helper_path.unlink(missing_ok=True)
                else:
                    _write_bytes_atomic(
                        credential_helper_path,
                        previous_helper,
                        previous_helper_mode or 0o755,
                    )
                if created_state:
                    state_path.unlink(missing_ok=True)
            except Exception as rollback_error:
                print_error(f"Git凭证文件回滚失败: {rollback_error}")
        print_error(f"配置Git凭证助手失败: {e}")
        return False


def clear_git_credentials() -> bool:
    """清除Git凭证配置"""
    config_dir = Path.home() / '.atomgit'
    credential_helper_path = config_dir / 'git-credential-atomgit'
    state_path = config_dir / _GIT_HELPER_STATE_FILENAME
    current_values = None
    try:
        current_values = {
            host: _get_global_git_values(_git_helper_key(host))
            for host in _GIT_CREDENTIAL_HOSTS
        }
        restored_values = _load_helper_state(state_path)
        if restored_values is None:
            helper_value = f"!{credential_helper_path}"
            restored_values = {
                host: _legacy_cleanup_values(values, helper_value)
                for host, values in current_values.items()
            }

        _restore_global_git_values(restored_values)
        current_values = None

        if credential_helper_path.exists():
            credential_helper_path.unlink()
        state_path.unlink(missing_ok=True)

        print_success(f"Git凭证配置已清除")
        return True
        
    except Exception as e:
        if current_values is not None:
            try:
                _restore_global_git_values(current_values)
            except Exception as rollback_error:
                print_error(f"Git凭证清理回滚失败: {rollback_error}")
        print_error(f"清除Git凭证配置失败: {e}")
        return False


def check_git_available() -> bool:
    """检查Git是否可用"""
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_git_user_info() -> dict:
    """获取Git用户信息"""
    info = {}
    try:
        # 获取用户名
        result = subprocess.run(['git', 'config', '--global', 'user.name'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            info['name'] = result.stdout.strip()
        
        # 获取邮箱
        result = subprocess.run(['git', 'config', '--global', 'user.email'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            info['email'] = result.stdout.strip()
            
    except FileNotFoundError:
        pass
    
    return info
