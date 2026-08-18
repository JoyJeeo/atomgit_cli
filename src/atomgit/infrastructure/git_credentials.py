"""Transactional AtomGit Git credential-helper ownership."""

import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List

from .output import print_error, print_success


_GIT_CREDENTIAL_HOSTS = ("atomgit.com", "hub.atomgit.com")
_GIT_HELPER_STATE_VERSION = 1
_GIT_HELPER_STATE_FILENAME = "git-helper-state.json"


def _git_helper_key(host: str) -> str:
    return f"credential.https://{host}.helper"


def _git_helper_command(
    helper_path,
    python_executable=None,
    windows: bool = None,
) -> str:
    """Build one shell-safe Git helper command for POSIX or Windows Git."""
    if python_executable is None:
        python_executable = sys.executable
    if windows is None:
        windows = os.name == "nt"
    executable = os.fspath(python_executable)
    helper = os.fspath(helper_path)
    if windows:
        executable = executable.replace("\\", "/")
        helper = helper.replace("\\", "/")
    return f"!{shlex.quote(executable)} {shlex.quote(helper)}"


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


def get_atomgit_git_helper_status():
    """Return managed-helper presence for each supported AtomGit host."""
    return {
        host: any(
            'git-credential-atomgit' in value
            for value in _get_global_git_values(_git_helper_key(host))
        )
        for host in _GIT_CREDENTIAL_HOSTS
    }


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


def _legacy_cleanup_values(values: List[str], helper_values) -> List[str]:
    helper_values = set(helper_values)
    cleaned = []
    for value in values:
        if value in helper_values:
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
使用登录时验证并保存的用户名和token提供Git认证
"""

import sys
import json
from pathlib import Path

def is_safe_credential_value(value):
    return (
        isinstance(value, str)
        and bool(value)
        and not any(ord(character) < 32 or ord(character) == 127 for character in value)
    )

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
                    username = config.get('username')
                    if is_safe_credential_value(token) and is_safe_credential_value(username):
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
            owned_helper_values = {
                f"!{credential_helper_path}",
                _git_helper_command(credential_helper_path),
            }
            original_values = {
                host: _legacy_cleanup_values(values, owned_helper_values)
                for host, values in previous_values.items()
            }
            _write_helper_state(state_path, original_values)
            created_state = True

        _write_bytes_atomic(
            credential_helper_path, helper_script.encode("utf-8"), 0o755
        )
        managed_values = ["", _git_helper_command(credential_helper_path)]
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
            helper_values = {
                f"!{credential_helper_path}",
                _git_helper_command(credential_helper_path),
            }
            restored_values = {
                host: _legacy_cleanup_values(values, helper_values)
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
