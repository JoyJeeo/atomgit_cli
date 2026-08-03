#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import click
import sys
from pathlib import Path
from getpass import getpass

# 设置Hugging Face Hub的API端点为AtomGit
os.environ["HF_ENDPOINT"] = "https://hub.atomgit.com"
# 禁用Xet协议，避免 xet-write-token 请求
os.environ["HF_HUB_DISABLE_XET"] = "1"
# 设置缓存目录
cache_dir = os.path.expanduser("~/.cache/atomgit")
os.makedirs(cache_dir, exist_ok=True)
os.environ["HF_HOME"] = cache_dir

try:
    from .config import config
    from .api import api
    from .utils import (
        print_success, print_error, print_warning, print_info,
        validate_repo_name, validate_repo_type, get_directory_size,
        format_file_size, count_files_in_directory, confirm_action,
        is_valid_path, ensure_directory, setup_git_credentials,
        clear_git_credentials, check_git_available, normalize_path_in_repo,
        parse_ignore_patterns
    )
except ImportError:
    from config import config
    from api import api
    from utils import (
        print_success, print_error, print_warning, print_info,
        validate_repo_name, validate_repo_type, get_directory_size,
        format_file_size, count_files_in_directory, confirm_action,
        is_valid_path, ensure_directory, setup_git_credentials,
        clear_git_credentials, check_git_available, normalize_path_in_repo,
        parse_ignore_patterns
    )


@click.group()
@click.version_option(version='1.0.5+yuto.1')
def cli():
    """AtomGit CLI - 基于Transformers和Hugging Face Hub的AtomGit平台模型文件上传下载工具"""
    pass


@cli.command()
@click.option('--token', '-t', help='AtomGit访问令牌')
def login(token):
    """登录到AtomGit平台"""
    if not token:
        token = getpass('请输入访问令牌: ')
    
    if not token:
        print_error("令牌不能为空")
        sys.exit(1)
    
    print_info("正在验证登录信息...")
    
    if api.login(token):
        print_success(f"登录成功！")
        
        # 配置Git凭证助手
        if check_git_available():
            if setup_git_credentials(token):
                print_info("✨ Git凭证已配置，现在可以直接使用git命令访问AtomGit仓库")
            else:
                print_warning("Git凭证配置失败，请手动配置或使用完整URL")
        else:
            print_warning("未检测到Git，跳过Git凭证配置")
    else:
        print_error("登录失败，请检查令牌是否正确")
        sys.exit(1)


@cli.command()
def logout():
    """退出登录"""
    was_logged_in = config.is_logged_in()
    config_dir = Path.home() / '.atomgit'
    has_git_state = any(
        (config_dir / filename).exists()
        for filename in ('git-helper-state.json', 'git-credential-atomgit')
    )

    if was_logged_in:
        config.clear_credentials()

    # A prior failed logout can leave helper state after the token is gone.
    if (was_logged_in or has_git_state) and check_git_available():
        if not clear_git_credentials():
            print_error(
                "登录 token 已清除，但 Git 凭证配置恢复失败；"
                "请修复 Git 配置后重新运行 'atomgit logout'"
            )
            sys.exit(1)

    if was_logged_in:
        print_success("已退出登录")
    else:
        print_info("当前未登录")


@cli.command()
def whoami():
    if not config.is_logged_in():
        print_warning("请先登录：atomgit login")
        sys.exit(1)
    # 调用API获取用户信息
    user_info = api.get_login_user()
    if user_info:
        print_success(f"当前登录用户: {user_info['login']}")
    else:
        print_error("获取用户信息失败")
        sys.exit(1)


@cli.group()
def repo():
    """仓库管理命令"""
    pass


@repo.command()
@click.argument('repo_name')
@click.option('--type', 'repo_type', type=click.Choice(['model', 'dataset']), 
              required=True, help='仓库类型 (model/dataset)')
@click.option('--private', is_flag=True, help='创建私有仓库')
def create(repo_name, repo_type, private):
    """创建新仓库"""
    if not config.is_logged_in():
        print_error("请先登录：atomgit login")
        sys.exit(1)
    
    if not validate_repo_name(repo_name):
        print_error("仓库名称格式不正确，应为: username/repo-name")
        sys.exit(1)
    
    print_info(f"正在创建{repo_type}仓库: {repo_name}")
    if api.create_repo(repo_name, repo_type, private):
        print_success(f"仓库 {repo_name} 创建成功")
    else:
        print_error(f"仓库 {repo_name} 创建失败")
        sys.exit(1)


# @repo.command()
# @click.argument('repo_id')
# def info(repo_id):
#     """显示仓库信息"""
#     if not config.is_logged_in():
#         print_error("请先登录：atomgit login")
#         sys.exit(1)
    
#     if not validate_repo_name(repo_id):
#         print_error("仓库ID格式不正确，应为: username/repo-name")
#         sys.exit(1)
    
#     repo_info = api.get_repo_info(repo_id)
#     if repo_info:
#         print_info(f"仓库名称: {repo_info.get('name', '未知')}")
#         print_info(f"仓库类型: {repo_info.get('type', '未知')}")
#         print_info(f"描述: {repo_info.get('description', '无')}")
#         print_info(f"是否私有: {'是' if repo_info.get('private', False) else '否'}")
#         print_info(f"创建时间: {repo_info.get('created_at', '未知')}")
#     else:
#         print_error(f"无法获取仓库 {repo_id} 的信息")
#         sys.exit(1)


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--repo-id', required=True, help='目标仓库ID (username/repo-name)')
@click.option('--message', '-m', default='', help='上传说明')
@click.option('--timeout', '-t', 'timeout_sec', default=300, type=float,
              help='上传超时时间（秒），默认300秒（5分钟）。大数据集建议增大此值')
@click.option('--no-progress-bar', is_flag=True, default=False,
              help='禁用上传进度条（适用于日志/CI等非交互场景）')
@click.option('--path-in-repo', '-p', 'path_in_repo', default=None,
              help='仓库内目标目录前缀（如 "sub/" 或 "sub/extra/"），默认上传到仓库根目录')
@click.option('--repo-type', '-r', 'repo_type',
              type=click.Choice(['model', 'dataset']), default=None,
              help='仓库类型 (model/dataset)，默认按 model 处理')
@click.option('--revision', 'revision', default=None,
              help='上传目标分支/版本（如 "dev" 或 "v1.0"），默认提交到默认分支(通常为main)')
@click.option('--ignore', '-i', 'ignore', default=None,
              help='忽略的文件模式（逗号分隔，如 "*.tmp,logs/,**/.DS_Store"），'
                   '仅对目录上传有意义')
@click.option('--resumable', is_flag=True, default=False,
              help='启用断点续传/分块上传模式（仅目录上传有效，走 HF upload_large_folder，'
                   '中断后可自动续传；注意此模式下 path_in_repo 与 message 不生效）')
@click.option('--num-workers', 'num_workers', default=None, type=int,
              help='断点续传模式的并发 worker 数（仅 --resumable 生效）')
def upload(path, repo_id, message, timeout_sec, no_progress_bar, path_in_repo, repo_type, revision, ignore, resumable, num_workers):
    """上传文件或目录到仓库"""
    if not config.is_logged_in():
        print_error("请先登录：atomgit login")
        sys.exit(1)

    if not validate_repo_name(repo_id):
        print_error("仓库ID格式不正确，应为: username/repo-name")
        sys.exit(1)

    path = Path(path)
    if not path.exists():
        print_error(f"路径不存在: {path}")
        sys.exit(1)

    # 进度条默认开启；--no-progress-bar 时关闭
    show_progress = not no_progress_bar

    # 规范化并校验仓库内路径（含路径穿越防护）
    try:
        pipr = normalize_path_in_repo(path_in_repo)
    except ValueError as e:
        print_error(str(e))
        sys.exit(1)

    # 解析忽略模式（逗号分隔 → 列表；空 → None）
    ignore_patterns = parse_ignore_patterns(ignore)

    if path.is_file():
        # 断点续传仅对目录上传有效
        if resumable:
            print_warning("--resumable 仅对目录上传有效，对单文件上传已忽略")
        print_info(f"正在上传文件: {path}")
        file_size = format_file_size(path.stat().st_size)
        print_info(f"文件大小: {file_size}")
        if pipr:
            print_info(f"仓库内路径: {pipr}/")
        if repo_type:
            print_info(f"仓库类型: {repo_type}")
        if revision:
            print_info(f"目标分支: {revision}")
        if ignore_patterns:
            print_warning("注意：--ignore 对单文件上传几乎不生效（仅匹配文件名），主要对目录上传有意义")

        if api.upload_folder(path, repo_id, message=message, upload_timeout=timeout_sec,
                             progress_bar=show_progress, path_in_repo=path_in_repo,
                             repo_type=repo_type, revision=revision,
                             ignore_patterns=ignore_patterns):
            print_success(f"文件上传成功: {path.name}")
        else:
            print_error(f"文件上传失败: {path.name}")
            sys.exit(1)

    elif path.is_dir():
        file_count = count_files_in_directory(path)
        dir_size = format_file_size(get_directory_size(path))

        print_info(f"正在上传目录: {path}")
        print_info(f"文件数量: {file_count}")
        print_info(f"目录大小: {dir_size}")
        print_info(f"超时设置: {timeout_sec}秒")
        if pipr:
            print_info(f"仓库内路径: {pipr}/")
        if repo_type:
            print_info(f"仓库类型: {repo_type}")
        if revision:
            print_info(f"目标分支: {revision}")
        if ignore_patterns:
            print_info(f"忽略模式: {', '.join(ignore_patterns)}")
        if resumable:
            print_info("上传模式: 断点续传/分块 (resumable)")
            if num_workers:
                print_info(f"并发 worker: {num_workers}")
            if not repo_type:
                print_info("提示：未指定 --repo-type，断点续传模式下默认按 model 处理")
        if not show_progress:
            print_info("进度条已禁用")

        if api.upload_directory(path, repo_id, message=message, upload_timeout=timeout_sec,
                                progress_bar=show_progress, path_in_repo=path_in_repo,
                                repo_type=repo_type, revision=revision,
                                ignore_patterns=ignore_patterns,
                                resumable=resumable, num_workers=num_workers):
            print_success(f"目录上传成功: {path}")
        else:
            print_error(f"目录上传失败: {path}")
            sys.exit(1)

    else:
        print_error(f"不支持的路径类型: {path}")
        sys.exit(1)


@cli.command()
@click.argument('repo_id')
@click.option('--directory', '-d', type=click.Path(), 
              help='下载到指定目录')
@click.option('--force', is_flag=True, help='强制覆盖已存在的文件')
def download(repo_id, directory, force):
    """下载仓库到本地（公开仓库无需登录）"""
    if not validate_repo_name(repo_id):
        print_error("仓库ID格式不正确，应为: username/repo-name")
        sys.exit(1)
    
    # 确定下载目录
    if directory:
        local_path = Path(directory)
        if not is_valid_path(directory):
            print_error(f"无效的目录路径: {directory}")
            sys.exit(1)
    else:
        local_path = Path.cwd() / repo_id.split('/')[-1]
    
    # 检查目录是否存在
    if local_path.exists():
        if local_path.is_file():
            print_error(f"目标路径是文件，不是目录: {local_path}")
            sys.exit(1)
        elif local_path.is_dir() and any(local_path.iterdir()):
            if force:
                print_info("强制覆盖模式，将重新下载所有文件")
            else:
                print_info("目录已存在，启用断点续传模式")
    
    # 确保目录存在
    if not ensure_directory(local_path):
        print_error(f"无法创建目录: {local_path}")
        sys.exit(1)
    
    print_info(f"正在下载仓库: {repo_id}")
    print_info(f"下载到: {local_path}")
    
    # 如果未登录，提示用户这是公开仓库下载模式
    if not config.is_logged_in():
        print_info("当前未登录，尝试下载公开仓库...")
    
    if api.download_repo(repo_id, local_path, force_download=force):
        print_success(f"仓库下载成功: {local_path}")
    else:
        print_error(f"仓库下载失败: {repo_id}")
        if not config.is_logged_in():
            print_info("提示：如果这是私有仓库，请先使用 'atomgit login' 登录")
        sys.exit(1)


@cli.command()
def config_show():
    """显示配置信息"""
    if config.is_logged_in():
        credentials = config.get_credentials()
        print_info(f"登录状态: 已登录")
        print_info(f"配置文件: {config.config_file}")
        
        # 简单检查Git集成状态
        if check_git_available():
            try:
                import subprocess
                # 检查任一域名的凭证助手配置
                result1 = subprocess.run(['git', 'config', '--global', '--get', 'credential.https://atomgit.com.helper'], 
                                       capture_output=True, text=True)
                result2 = subprocess.run(['git', 'config', '--global', '--get', 'credential.https://hub.atomgit.com.helper'], 
                                       capture_output=True, text=True)
                
                if ((result1.returncode == 0 and 'git-credential-atomgit' in result1.stdout) or 
                    (result2.returncode == 0 and 'git-credential-atomgit' in result2.stdout)):
                    print_info("Git集成: 已启用")
                else:
                    print_info("Git集成: 未启用")
            except Exception:
                print_info("Git集成: 检查失败")
    else:
        print_warning("当前未登录")
        print_info(f"配置文件: {config.config_file}")



if __name__ == '__main__':
    cli()
