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
    from .cli_contracts import (
        _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
        DEFAULT_UPLOAD_BATCH_SIZE,
    )
    from .completion import (
        CompletionConfigError,
        completion_script,
        install_completion,
        uninstall_completion,
    )
    from .config import config
    from .release import ReleaseError, is_stable_version, run_update
    from .version import __version__
except ImportError:
    from cli_contracts import (
        _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
        DEFAULT_UPLOAD_BATCH_SIZE,
    )
    from completion import (
        CompletionConfigError,
        completion_script,
        install_completion,
        uninstall_completion,
    )
    from config import config
    from release import ReleaseError, is_stable_version, run_update
    from version import __version__


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
    if value is not None and not is_stable_version(value):
        raise click.BadParameter("must be an exact stable X.Y.Z version")
    return value


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
    try:
        result = run_update(
            version=target_version,
            force_reinstall=force_reinstall,
            python=sys.executable,
        )
    except ReleaseError as error:
        raise click.ClickException(str(error)) from error

    status = result.get("status")
    if status == "source":
        click.echo(
            "检测到 Git/可编辑源码安装；atomgit update 不会修改源码。请执行 "
            "git checkout yuto、git pull --ff-only，在隔离 conda 环境中安装锁定依赖，"
            "然后重新执行 python -m pip install -e .。",
            err=True,
        )
        raise click.exceptions.Exit(1)
    if status == "skipped":
        click.echo(f"AtomGit CLI 已是 {result['version']}，跳过更新。")
        return
    click.echo(
        f"AtomGit CLI {result['version']} 已安装到 {result['python']}。\n"
        f"包位置: {result.get('package', 'unknown')}\n"
        f"命令路径: {result.get('command', 'unknown')}\n"
        f"脚本目录: {result['scripts']}"
    )
    if result.get("completion_warning"):
        click.echo(f"warning: {result['completion_warning']}", err=True)


@cli.group()
def completion():
    """管理 Zsh 命令补全"""
    pass


@completion.command(name="show")
@click.argument("shell", type=click.Choice(["zsh"], case_sensitive=False))
def show_completion(shell):
    """输出指定 shell 的补全脚本"""
    try:
        click.echo(completion_script(cli, shell), nl=False)
    except CompletionConfigError as error:
        raise click.ClickException(str(error)) from error


@completion.command(name="install")
@click.option(
    "--shell",
    type=click.Choice(["zsh"], case_sensitive=False),
    default="zsh",
    show_default=True,
)
def install_shell_completion(shell):
    """安装并启用指定 shell 的补全"""
    try:
        script_path, zshrc_path = install_completion(cli, shell)
    except CompletionConfigError as error:
        raise click.ClickException(str(error)) from error
    click.echo(f"Zsh 补全已安装: {script_path}")
    click.echo(f"启动配置已更新: {zshrc_path}")


@completion.command(name="uninstall")
@click.option(
    "--shell",
    type=click.Choice(["zsh"], case_sensitive=False),
    default="zsh",
    show_default=True,
)
def uninstall_shell_completion(shell):
    """移除 AtomGit 管理的 shell 补全"""
    try:
        uninstall_completion(shell)
    except CompletionConfigError as error:
        raise click.ClickException(str(error)) from error
    click.echo("Zsh 补全已移除")


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
    if token is not None and token_stdin:
        raise click.UsageError("--token 与 --token-stdin 不能同时使用")

    if token_stdin:
        token = sys.stdin.readline().rstrip('\r\n')
        if not token:
            raise click.UsageError("--token-stdin 未读取到访问令牌")

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
        print_error("登录失败，请根据上方提示处理")
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
    """显示当前登录用户"""
    if not config.is_logged_in():
        print_warning("请先登录：atomgit login")
        sys.exit(1)
    # 调用API获取用户信息
    user_info = api.get_login_user()
    if user_info:
        print_success(f"当前登录用户: {user_info['login']}")
    else:
        print_error("无法确认当前登录用户，请根据上方提示处理")
        sys.exit(1)


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
    try:
        removed = clear_atomgit_cache()
    except Exception as error:
        print_error(f"清理 AtomGit 缓存失败: {error}")
        sys.exit(1)
    print_success(f"AtomGit 缓存已清理（移除 {removed} 项）")


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
    if private == public_repo:
        raise click.UsageError("必须且只能指定 --private 或 --public")
    if not config.is_logged_in():
        print_error("请先登录：atomgit login")
        sys.exit(1)
    if not validate_repo_name(repo_name):
        print_error("仓库名称格式不正确，应为: username/repo-name")
        sys.exit(1)
    
    print_info(f"正在创建{repo_type}仓库: {repo_name}")
    if api.create_repo(repo_name, repo_type, private, exist_ok=exist_ok):
        if exist_ok:
            print_success(f"仓库 {repo_name} 已存在或已创建")
        else:
            print_success(f"仓库 {repo_name} 创建成功")
    else:
        print_error(f"仓库 {repo_name} 创建失败")
        sys.exit(1)


@repo.command(name='list')
def list_repositories():
    """列出当前用户可访问的仓库"""
    if not config.is_logged_in():
        print_error("请先登录：atomgit login")
        sys.exit(1)

    repositories = api.list_repos()
    if repositories is None:
        print_error("获取仓库列表失败")
        sys.exit(1)
    if not repositories:
        print_info("没有可显示的仓库")
        return

    for repository in repositories:
        repo_id = repository.get('full_name') or repository.get(
            'path_with_namespace'
        )
        if not repo_id:
            owner = repository.get('owner')
            owner_name = None
            if isinstance(owner, dict):
                owner_name = owner.get('login') or owner.get('path')
            name = repository.get('name') or repository.get('path')
            if owner_name and name:
                repo_id = f"{owner_name}/{name}"
            else:
                repo_id = name or "(unknown)"

        private = repository.get('private')
        if isinstance(private, bool):
            visibility = "private" if private else "public"
        else:
            visibility = repository.get('visibility') or "unknown"
        print_info(f"{visibility}\t{repo_id}")


@repo.command(name='visibility')
@click.argument('repo_id')
@click.argument('visibility', type=click.Choice(['public', 'private']))
def set_repository_visibility(repo_id, visibility):
    """修改并验证仓库可见性"""
    if not config.is_logged_in():
        print_error("请先登录：atomgit login")
        sys.exit(1)
    if not validate_repo_name(repo_id):
        print_error("仓库ID格式不正确，应为: username/repo-name")
        sys.exit(1)

    private = visibility == 'private'
    if api.set_repo_visibility(repo_id, private=private):
        print_success(f"仓库 {repo_id} 已设置为 {visibility}")
    else:
        print_error(f"仓库 {repo_id} 可见性修改失败")
        sys.exit(1)


@repo.command(name='delete')
@click.argument('repo_id')
@click.option(
    '--confirm', required=True, metavar='REPO_ID',
    help='必须原样重复仓库 ID，确认永久删除',
)
def delete_repository(repo_id, confirm):
    """永久删除仓库并验证远端已不存在"""
    if not config.is_logged_in():
        print_error("请先登录：atomgit login")
        sys.exit(1)
    if not validate_repo_name(repo_id):
        print_error("仓库ID格式不正确，应为: username/repo-name")
        sys.exit(1)
    if confirm != repo_id:
        raise click.UsageError("--confirm 必须与仓库 ID 完全一致")

    print_warning(f"正在永久删除仓库: {repo_id}")
    if api.delete_repo(repo_id, confirmation=confirm):
        print_success(f"仓库 {repo_id} 已删除并验证不存在")
    else:
        print_error(f"仓库 {repo_id} 删除失败或远端状态未知")
        sys.exit(1)


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
    if not config.is_logged_in():
        print_error("请先登录：atomgit login")
        sys.exit(1)
    if not validate_repo_name(repo_id):
        print_error("仓库ID格式不正确，应为: username/repo-name")
        sys.exit(1)
    if not branch_name or not is_supported_upload_revision(branch_name):
        raise click.UsageError("分支名称不合法")
    if not source or not is_supported_upload_revision(source):
        raise click.UsageError("来源 revision 不合法")
    if api.create_branch(repo_id, branch_name, source=source):
        print_success(f"分支 {branch_name} 创建成功")
    else:
        print_error(f"分支 {branch_name} 创建失败")
        sys.exit(1)


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
    if timeout_sec is not None and timeout_sec <= 0:
        print_error("上传超时时间必须大于 0 秒")
        sys.exit(2)
    if not is_supported_upload_revision(revision):
        print_error("上传 revision 名称不合法")
        sys.exit(2)
    if num_workers is not None and num_workers <= 0:
        print_error("并发 worker 数必须大于 0")
        sys.exit(2)
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
    user_ignore_patterns = parse_ignore_patterns(ignore)
    if user_ignore_patterns and any(
        "\\*" in pattern for pattern in user_ignore_patterns
    ):
        print_error(
            "--ignore 的 * 在引号内无需转义，请移除反斜杠后重试"
        )
        sys.exit(2)

    if path.is_file():
        resumable = False if resumable is None else resumable
        if is_macos_metadata_file(path):
            print_error(
                "显式选择的文件是 macOS 元数据，已拒绝上传"
            )
            sys.exit(2)
        if auto_configure_lfs:
            print_error("--auto-configure-lfs 仅支持 resumable 目录上传")
            sys.exit(2)
        if resumable:
            print_error("--resumable 仅支持目录上传")
            sys.exit(2)
        if user_ignore_patterns:
            print_error("--ignore 仅支持目录上传")
            sys.exit(2)
    elif path.is_dir():
        ignore_patterns = effective_cli_upload_ignore_patterns(
            user_ignore_patterns
        )
        if resumable is None:
            # A commit message requires HF upload_folder. Otherwise directories
            # automatically use the resilient large-folder uploader.
            resumable = not bool(message)
        if resumable and message:
            print_error("--resumable 不支持 --message")
            sys.exit(2)
        if auto_configure_lfs and not resumable:
            print_error("--auto-configure-lfs 仅支持 resumable 目录上传")
            sys.exit(2)
    else:
        print_error(f"不支持的路径类型: {path}")
        sys.exit(1)

    try:
        validate_upload_path_no_symlinks(path)
    except ValueError as error:
        print_error(str(error))
        sys.exit(1)

    if not config.is_logged_in():
        print_error("请先登录：atomgit login")
        sys.exit(1)

    if path.is_file():
        print_info(f"正在上传文件: {path}")
        file_size = format_file_size(path.stat().st_size)
        print_info(f"文件大小: {file_size}")
        if pipr:
            print_info(f"仓库内路径: {pipr}/")
        if repo_type:
            print_info(f"仓库类型: {repo_type}")
        if revision:
            print_info(f"目标分支: {revision}")
        if api.upload_folder(path, repo_id, message=message, upload_timeout=timeout_sec,
                             progress_bar=show_progress, path_in_repo=path_in_repo,
                             repo_type=repo_type, revision=revision,
                             ignore_patterns=user_ignore_patterns,
                             num_workers=num_workers):
            print_success(f"文件上传成功: {path.name}")
        else:
            print_error(f"文件上传失败: {path.name}")
            sys.exit(1)

    elif path.is_dir():
        file_count, upload_size = get_upload_file_stats(path, ignore_patterns)
        dir_size = format_file_size(upload_size)

        print_info(f"正在上传目录: {path}")
        print_info(f"待上传文件数量（应用忽略规则后）: {file_count}")
        print_info(f"待上传目录大小（应用忽略规则后）: {dir_size}")
        if resumable:
            print_info(
                "上传总时限: 不限时"
                if timeout_sec is None else f"上传总时限: {timeout_sec:g}秒"
            )
        else:
            print_info("上传总时限: 不限制（普通模式）")
        request_timeout = (
            timeout_sec
            if timeout_sec is not None
            else _RESUMABLE_DEFAULT_REQUEST_TIMEOUT
        )
        print_info(f"单次网络请求超时: {request_timeout:g}秒")
        if pipr:
            print_info(f"仓库内路径: {pipr}/")
        if repo_type:
            print_info(f"仓库类型: {repo_type}")
        if revision:
            print_info(f"目标分支: {revision}")
        print_info("macOS 元数据默认忽略: AppleDouble, .DS_Store")
        if user_ignore_patterns:
            print_info(
                f"额外用户忽略模式: {', '.join(user_ignore_patterns)}"
            )
        if num_workers:
            print_info(f"并发 worker: {num_workers}")
        print_info(f"外层批次上限: {batch_size} 个文件")
        if resumable:
            print_info("上传模式: 断点续传/分块 (resumable)")
            if auto_configure_lfs:
                print_info(
                    "Git LFS 自动配置: 已启用；将检查服务端判定的 LFS 扩展名并按需修改远端配置"
                )
            if not repo_type:
                print_info("提示：未指定 --repo-type，断点续传模式下默认按 model 处理")
        if not show_progress:
            print_info("进度条已禁用")

        if api.upload_directory(path, repo_id, message=message, upload_timeout=timeout_sec,
                                progress_bar=show_progress, path_in_repo=path_in_repo,
                                repo_type=repo_type, revision=revision,
                                ignore_patterns=ignore_patterns,
                                resumable=resumable, num_workers=num_workers,
                                batch_size=batch_size,
                                auto_configure_lfs=auto_configure_lfs):
            print_success(f"目录上传成功: {path}")
        else:
            print_error(f"目录上传失败: {path}")
            sys.exit(1)

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
            elif verify_checksum:
                print_info("目录已存在；将校验已有文件（不匹配时可使用 --force）")
            else:
                print_info("目录已存在；已有文件默认跳过（不校验内容，--force 可覆盖）")
    
    # 确保目录存在
    if not ensure_directory(local_path):
        print_error(f"无法创建目录: {local_path}")
        sys.exit(1)
    
    print_info(f"正在下载仓库: {repo_id}")
    print_info(f"下载到: {local_path}")
    if verify_checksum:
        print_info("checksum 校验已启用")
    if resume_download:
        print_info("断点续传已启用（完成后自动校验 checksum）")
    if prune:
        print_info("安全清理已启用（仅删除下载 manifest 记录的文件）")
    
    # 如果未登录，提示用户这是公开仓库下载模式
    if not config.is_logged_in():
        print_info("当前未登录，尝试下载公开仓库...")
    
    download_options = {
        "force_download": force,
        "repo_type": repo_type,
    }
    if verify_checksum:
        download_options["verify_checksum"] = True
    if resume_download:
        download_options["resume_download"] = True
    if prune:
        download_options["prune"] = True
    if api.download_repo(repo_id, local_path, **download_options):
        print_success(f"仓库下载成功: {local_path}")
    else:
        print_error(f"仓库下载失败: {repo_id}")
        if not config.is_logged_in():
            print_info("提示：如果这是私有仓库，请先使用 'atomgit login' 登录")
        sys.exit(1)


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
    if not validate_repo_name(repo_id):
        print_error("仓库ID格式不正确，应为: username/repo-name")
        sys.exit(1)

    if directory:
        if not is_valid_path(directory):
            print_error(f"无效的目录路径: {directory}")
            sys.exit(1)
        local_path = Path(directory)
    else:
        local_path = Path.cwd()

    if local_path.exists() and local_path.is_file():
        print_error(f"目标路径是文件，不是目录: {local_path}")
        sys.exit(1)
    if not ensure_directory(local_path):
        print_error(f"无法创建目录: {local_path}")
        sys.exit(1)

    print_info(f"正在下载文件: {repo_id}/{filename}")
    print_info(f"下载到: {local_path}")
    if verify_checksum:
        print_info("checksum 校验已启用")
    if resume_download:
        print_info("断点续传已启用（完成后自动校验 checksum）")
    if not config.is_logged_in():
        print_info("当前未登录，尝试从公开仓库下载...")

    download_options = {
        "force_download": force,
        "repo_type": repo_type,
    }
    if verify_checksum:
        download_options["verify_checksum"] = True
    if resume_download:
        download_options["resume_download"] = True
    if api.download_file(repo_id, filename, local_path, **download_options):
        print_success(f"文件下载成功: {filename}")
    else:
        print_error(f"文件下载失败: {repo_id}/{filename}")
        if not config.is_logged_in():
            print_info("提示：如果这是私有仓库，请先使用 'atomgit login' 登录")
        sys.exit(1)


@cli.command()
def config_show():
    """显示配置信息"""
    if config.is_logged_in():
        print_info(f"登录状态: 已登录")
        print_info(f"配置文件: {config.config_file}")
        
        # 简单检查Git集成状态
        if check_git_available():
            try:
                statuses = get_atomgit_git_helper_status()
                configured = [host for host, enabled in statuses.items() if enabled]
                missing = [host for host, enabled in statuses.items() if not enabled]
                if not missing:
                    print_info(
                        f"Git集成: 已启用（{len(configured)}/{len(statuses)} 域名）"
                    )
                elif configured:
                    print_info(
                        "Git集成: 部分启用（已配置: "
                        + ", ".join(configured)
                        + "；缺少: "
                        + ", ".join(missing)
                        + "）"
                    )
                else:
                    print_info("Git集成: 未启用")
            except Exception:
                print_info("Git集成: 检查失败")
    else:
        print_warning("当前未登录")
        print_info(f"配置文件: {config.config_file}")



if __name__ == '__main__':
    cli()
