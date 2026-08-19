#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import importlib
import sys
from pathlib import Path
from getpass import getpass

try:
    from .runtime import configure_hf_environment
except ImportError:
    from runtime import configure_hf_environment

configure_hf_environment()

try:
    from .commands import authentication as _authentication_commands
    from .commands import lifecycle as _lifecycle_commands
    from .commands import repositories as _repositories_commands
    from .commands import transfers as _transfers_commands
    from .cli_contracts import (
        _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
        DEFAULT_UPLOAD_BATCH_SIZE,
    )
    from .completion import (
        CompletionConfigError,
        completion_script,
        install_completion,
        legacy_completion_present,
        uninstall_completion,
    )
    from .config import config
    from .release import ReleaseError, is_stable_version, run_update
    from .uninstaller import (
        UninstallError,
        build_uninstall_plan,
        run_uninstall,
    )
    from .version import __version__
except ImportError:
    from commands import authentication as _authentication_commands
    from commands import lifecycle as _lifecycle_commands
    from commands import repositories as _repositories_commands
    from commands import transfers as _transfers_commands
    from cli_contracts import (
        _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
        DEFAULT_UPLOAD_BATCH_SIZE,
    )
    from completion import (
        CompletionConfigError,
        completion_script,
        install_completion,
        legacy_completion_present,
        uninstall_completion,
    )
    from config import config
    from release import ReleaseError, is_stable_version, run_update
    from uninstaller import UninstallError, build_uninstall_plan, run_uninstall
    from version import __version__


_COMMAND_CONTEXT = sys.modules[__name__]


def _import_runtime_module(name):
    if __package__:
        return importlib.import_module(f".{name}", __package__)
    return importlib.import_module(name)


class _LazyObject:
    """Preserve patchable CLI globals without importing their runtime module."""

    def __init__(self, module_name, attribute_name):
        object.__setattr__(self, "_module_name", module_name)
        object.__setattr__(self, "_attribute_name", attribute_name)

    def _resolve(self):
        module = _import_runtime_module(object.__getattribute__(self, "_module_name"))
        return getattr(module, object.__getattribute__(self, "_attribute_name"))

    def __getattr__(self, name):
        return getattr(self._resolve(), name)

    def __setattr__(self, name, value):
        setattr(self._resolve(), name, value)

    def __delattr__(self, name):
        delattr(self._resolve(), name)


api = _LazyObject("api", "api")


def _lazy_utility(name):
    def call(*args, **kwargs):
        return getattr(_import_runtime_module("utils"), name)(*args, **kwargs)

    call.__name__ = name
    return call


for _utility_name in (
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "validate_repo_name",
    "is_supported_upload_revision",
    "format_file_size",
    "get_upload_file_stats",
    "clear_atomgit_cache",
    "is_valid_path",
    "ensure_directory",
    "setup_git_credentials",
    "clear_git_credentials",
    "check_git_available",
    "normalize_path_in_repo",
    "parse_ignore_patterns",
    "effective_cli_upload_ignore_patterns",
    "is_macos_metadata_file",
    "get_atomgit_git_helper_status",
    "validate_upload_path_no_symlinks",
):
    globals()[_utility_name] = _lazy_utility(_utility_name)


@click.group()
@click.version_option(version=__version__)
def cli():
    """AtomGit CLI - 基于Transformers和Hugging Face Hub的AtomGit平台模型文件上传下载工具"""
    pass


def _stable_version_option(ctx, param, value):
    return _lifecycle_commands.stable_version_option(
        _COMMAND_CONTEXT, ctx, param, value
    )


@cli.command()
@click.option(
    "--version",
    "target_version",
    callback=_stable_version_option,
    help="目标 GitHub Release 版本（X.Y.Z）；默认使用最高已完成稳定 Release",
)
@click.option(
    "--force-reinstall",
    is_flag=True,
    default=False,
    help="即使版本相同也重新安装已校验的 wheel",
)
def update(target_version, force_reinstall):
    """从已完成的 GitHub Release 更新当前 Python 中的 AtomGit CLI。"""
    return _lifecycle_commands.update(
        _COMMAND_CONTEXT, target_version, force_reinstall
    )


@cli.command()
@click.option(
    "--yes",
    is_flag=True,
    default=False,
    help="跳过确认（仅用于官方自动化卸载入口）",
)
def uninstall(yes):
    """卸载当前 Python 中的 AtomGit CLI，并清理当前环境补全。"""
    return _lifecycle_commands.uninstall(_COMMAND_CONTEXT, yes)


@cli.group()
def completion():
    """管理 Zsh 命令补全"""
    pass


@completion.command(name="show")
@click.argument("shell", type=click.Choice(["zsh"], case_sensitive=False))
def show_completion(shell):
    """输出指定 shell 的补全脚本"""
    return _lifecycle_commands.show_completion(_COMMAND_CONTEXT, shell)


@completion.command(name="install")
@click.option(
    "--shell",
    type=click.Choice(["zsh"], case_sensitive=False),
    default="zsh",
    show_default=True,
)
def install_shell_completion(shell):
    """安装并启用指定 shell 的补全"""
    return _lifecycle_commands.install_shell_completion(
        _COMMAND_CONTEXT, shell
    )


@completion.command(name="uninstall")
@click.option(
    "--shell",
    type=click.Choice(["zsh"], case_sensitive=False),
    default="zsh",
    show_default=True,
)
def uninstall_shell_completion(shell):
    """移除 AtomGit 管理的 shell 补全"""
    return _lifecycle_commands.uninstall_shell_completion(
        _COMMAND_CONTEXT, shell
    )


@cli.command()
@click.option(
    '--token', '-t',
    help='AtomGit访问令牌（可能进入 shell 历史；优先使用交互输入或 --token-stdin）',
)
@click.option(
    '--token-stdin', is_flag=True,
    help='从标准输入读取一行访问令牌（适用于管道或重定向）',
)
def login(token, token_stdin):
    """登录到AtomGit平台"""
    return _authentication_commands.login(
        _COMMAND_CONTEXT, token, token_stdin
    )


@cli.command()
def logout():
    """退出登录"""
    return _authentication_commands.logout(_COMMAND_CONTEXT)


@cli.command()
def whoami():
    """显示当前登录用户"""
    return _authentication_commands.whoami(_COMMAND_CONTEXT)


@cli.group()
def repo():
    """仓库管理命令"""
    pass


@cli.group()
def cache():
    """AtomGit 本地缓存管理命令"""
    pass


@cache.command(name='clear')
def clear_cache():
    """清理 AtomGit 工具产生的本地缓存"""
    return _repositories_commands.clear_cache(_COMMAND_CONTEXT)


@repo.command()
@click.argument('repo_name')
@click.option('--type', 'repo_type', type=click.Choice(['model', 'dataset']), 
              required=True, help='仓库类型 (model/dataset)')
@click.option('--private', is_flag=True, help='明确创建私有仓库')
@click.option('--public', 'public_repo', is_flag=True, help='明确创建公开仓库')
@click.option('--exist-ok', is_flag=True,
              help='仓库已存在时仍返回成功（用于幂等自动化）')
def create(repo_name, repo_type, private, public_repo, exist_ok):
    """创建新仓库"""
    return _repositories_commands.create(
        _COMMAND_CONTEXT,
        repo_name,
        repo_type,
        private,
        public_repo,
        exist_ok,
    )


@repo.command(name='list')
def list_repositories():
    """列出当前用户可访问的仓库"""
    return _repositories_commands.list_repositories(_COMMAND_CONTEXT)


@repo.command(name='visibility')
@click.argument('repo_id')
@click.argument('visibility', type=click.Choice(['public', 'private']))
def set_repository_visibility(repo_id, visibility):
    """修改并验证仓库可见性"""
    return _repositories_commands.set_repository_visibility(
        _COMMAND_CONTEXT, repo_id, visibility
    )


@repo.command(name='delete')
@click.argument('repo_id')
@click.option(
    '--confirm', required=True, metavar='REPO_ID',
    help='必须原样重复仓库 ID，确认永久删除',
)
def delete_repository(repo_id, confirm):
    """永久删除仓库并验证远端已不存在"""
    return _repositories_commands.delete_repository(
        _COMMAND_CONTEXT, repo_id, confirm
    )


@repo.group(name='branch')
def branch_commands():
    """仓库分支管理"""
    pass


@branch_commands.command(name='create')
@click.argument('repo_id')
@click.argument('branch_name')
@click.option('--from', 'source', default='main', show_default=True,
              help='新分支的来源分支、标签或提交')
def create_branch(repo_id, branch_name, source):
    """显式创建并验证一个分支"""
    return _repositories_commands.create_branch(
        _COMMAND_CONTEXT, repo_id, branch_name, source
    )


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--repo-id', required=True, help='目标仓库ID (username/repo-name)')
@click.option('--message', '-m', default='', help='上传说明')
@click.option('--timeout', '-t', 'timeout_sec', default=None, type=float,
              help='单次网络请求超时（秒）；resumable 目录同时作为总时限。'
                   '省略时请求默认 300 秒且总时长不限')
@click.option('--no-progress-bar', is_flag=True, default=False,
              help='禁用上传进度条（适用于日志/CI等非交互场景）')
@click.option('--path-in-repo', '-p', 'path_in_repo', default=None,
              help='仓库内目标目录前缀（如 "sub/" 或 "sub/extra/"），默认上传到仓库根目录')
@click.option('--repo-type', '-r', 'repo_type',
              type=click.Choice(['model', 'dataset']), default=None,
              help='仓库类型 (model/dataset)，默认按 model 处理')
@click.option('--revision', 'revision', default=None,
              help='上传到已存在的 revision；非 main 分支需先用 repo branch create 创建')
@click.option('--ignore', '-i', 'ignore', default=None,
              help='额外忽略的文件模式（逗号分隔，如 "*.tmp,logs/"），'
                   '仅对目录上传有意义')
@click.option('--resumable/--no-resumable', default=None,
              help='目录上传默认启用断点续传/分块模式；--no-resumable 改用普通上传。'
                   '--resumable 不能与 --message 同用')
@click.option('--num-workers', 'num_workers', default=5, type=int,
              help='上传并发 worker 数，默认 5；目录普通/resumable 模式均可使用')
@click.option(
    '--batch-size', 'batch_size',
    default=DEFAULT_UPLOAD_BATCH_SIZE,
    type=click.IntRange(min=1, max=DEFAULT_UPLOAD_BATCH_SIZE),
    show_default=True,
    help='每个目录上传外层批次的最大文件数（仅目录有效）',
)
@click.option('--auto-configure-lfs', 'auto_configure_lfs', is_flag=True,
              default=False,
              help='resumable 为服务端判定的 LFS 扩展名检查并补齐仓库级 Git LFS 配置')
def upload(path, repo_id, message, timeout_sec, no_progress_bar, path_in_repo,
           repo_type, revision, ignore, resumable, num_workers,
           batch_size, auto_configure_lfs):
    """上传文件或目录到仓库"""
    return _transfers_commands.upload(
        _COMMAND_CONTEXT,
        path,
        repo_id,
        message,
        timeout_sec,
        no_progress_bar,
        path_in_repo,
        repo_type,
        revision,
        ignore,
        resumable,
        num_workers,
        batch_size,
        auto_configure_lfs,
    )

@cli.command()
@click.argument('repo_id')
@click.option('--directory', '-d', type=click.Path(), 
              help='下载到指定目录')
@click.option('--force', is_flag=True, help='强制覆盖已存在的文件')
@click.option('--verify-checksum', is_flag=True,
              help='使用仓库 checksum 校验已有文件和下载内容')
@click.option('--resume', 'resume_download', is_flag=True,
              help='保留未完成数据，并从中断位置继续下载')
@click.option('--prune', is_flag=True,
              help='清理 manifest 记录且远端已删除的本地文件')
@click.option('--repo-type', '-r', 'repo_type',
              type=click.Choice(['model', 'dataset']), default=None,
              help='明确仓库类型；不指定时自动探测 model/dataset')
def download(
    repo_id, directory, force, verify_checksum, resume_download, prune,
    repo_type,
):
    """下载仓库到本地（公开仓库无需登录）"""
    return _transfers_commands.download(
        _COMMAND_CONTEXT,
        repo_id,
        directory,
        force,
        verify_checksum,
        resume_download,
        prune,
        repo_type,
    )


@cli.command()
@click.argument('repo_id')
@click.argument('filename')
@click.option('--directory', '-d', type=click.Path(),
              help='下载到指定目录，默认当前目录')
@click.option('--force', is_flag=True, help='强制覆盖已存在的文件')
@click.option('--verify-checksum', is_flag=True,
              help='使用仓库 checksum 校验已有文件和下载内容')
@click.option('--resume', 'resume_download', is_flag=True,
              help='保留未完成数据，并从中断位置继续下载')
@click.option('--repo-type', '-r', 'repo_type',
              type=click.Choice(['model', 'dataset']), default=None,
              help='明确仓库类型；不指定时自动探测 model/dataset')
def download_file(
    repo_id, filename, directory, force, verify_checksum, resume_download,
    repo_type,
):
    """下载仓库中的单个文件（公开仓库无需登录）"""
    return _transfers_commands.download_file(
        _COMMAND_CONTEXT,
        repo_id,
        filename,
        directory,
        force,
        verify_checksum,
        resume_download,
        repo_type,
    )


@cli.command()
def config_show():
    """显示配置信息"""
    return _authentication_commands.config_show(_COMMAND_CONTEXT)



if __name__ == '__main__':
    cli()
