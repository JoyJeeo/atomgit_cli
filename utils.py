import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
from colorama import Fore, Style, init
import urllib.parse

# 初始化colorama
init(autoreset=True)


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


def get_directory_size(dir_path: Path) -> int:
    """获取目录大小"""
    total_size = 0
    try:
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                total_size += get_file_size(file_path)
    except OSError:
        pass
    return total_size


def count_files_in_directory(dir_path: Path) -> int:
    """统计目录中的文件数量"""
    count = 0
    try:
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
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


def setup_git_credentials(token: str) -> bool:
    """配置Git凭证助手，使用保存的token"""
    try:
        # 获取配置目录
        config_dir = Path.home() / '.atomgit'
        config_dir.mkdir(exist_ok=True)
        
        # 创建凭证助手脚本
        credential_helper_path = config_dir / 'git-credential-atomgit'
        
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
                'Authorization': f'token {token}',
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
        pass
    
    # API调用失败时返回默认用户名
    return 'atomgit-user'

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
                        
                        # 输出认证信息
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
        
        # 写入脚本文件
        with open(credential_helper_path, 'w', encoding='utf-8') as f:
            f.write(helper_script)
        
        # 设置脚本为可执行
        credential_helper_path.chmod(0o755)
        
        # 配置Git使用我们的凭证助手（为两个域名都配置）
        git_hosts = ['atomgit.com', 'hub.atomgit.com']
        commands = []
        
        for host in git_hosts:
            commands.append(['git', 'config', '--global', f'credential.https://{host}.helper', f'!{credential_helper_path}'])
        
        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print_warning(f"配置Git命令失败: {' '.join(cmd)}")
                print_warning(f"错误信息: {result.stderr}")
                return False
        
        print_success(f"Git凭证助手配置成功，现在可以直接使用git命令访问AtomGit仓库")
        return True
        
    except Exception as e:
        print_error(f"配置Git凭证助手失败: {e}")
        return False


def clear_git_credentials() -> bool:
    """清除Git凭证配置"""
    try:
        # 移除Git配置（清除两个域名的配置）
        git_hosts = ['atomgit.com', 'hub.atomgit.com']
        commands = []
        
        for host in git_hosts:
            commands.append(['git', 'config', '--global', '--unset', f'credential.https://{host}.helper'])
        
        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            # 忽略不存在的配置项错误
            if result.returncode != 0 and "not found" not in result.stderr:
                print_warning(f"清除Git配置命令失败: {' '.join(cmd)}")
                print_warning(f"错误信息: {result.stderr}")
        
        # 删除凭证助手脚本
        config_dir = Path.home() / '.atomgit'
        credential_helper_path = config_dir / 'git-credential-atomgit'
        if credential_helper_path.exists():
            credential_helper_path.unlink()
        
        print_success(f"Git凭证配置已清除")
        return True
        
    except Exception as e:
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