"""Upload and download command implementations."""

import uuid

from ....infrastructure.upload_observe import UploadSession


def upload(
    context,
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
):
    if timeout_sec is not None and timeout_sec <= 0:
        context.print_error("上传超时时间必须大于 0 秒")
        context.sys.exit(2)
    if not context.is_supported_upload_revision(revision):
        context.print_error("上传 revision 名称不合法")
        context.sys.exit(2)
    if num_workers is not None and num_workers <= 0:
        context.print_error("并发 worker 数必须大于 0")
        context.sys.exit(2)
    if not context.validate_repo_name(repo_id):
        context.print_error("仓库ID格式不正确，应为: username/repo-name")
        context.sys.exit(1)

    path = context.Path(path)
    if not path.exists():
        context.print_error(f"路径不存在: {path}")
        context.sys.exit(1)

    show_progress = not no_progress_bar

    try:
        pipr = context.normalize_path_in_repo(path_in_repo)
    except ValueError as error:
        context.print_error(str(error))
        context.sys.exit(1)

    user_ignore_patterns = context.parse_ignore_patterns(ignore)
    if user_ignore_patterns and any(
        "\\*" in pattern for pattern in user_ignore_patterns
    ):
        context.print_error("--ignore 的 * 在引号内无需转义，请移除反斜杠后重试")
        context.sys.exit(2)

    if path.is_file():
        resumable = False if resumable is None else resumable
        if context.is_macos_metadata_file(path):
            context.print_error("显式选择的文件是 macOS 元数据，已拒绝上传")
            context.sys.exit(2)
        if auto_configure_lfs:
            context.print_error("--auto-configure-lfs 仅支持 resumable 目录上传")
            context.sys.exit(2)
        if resumable:
            context.print_error("--resumable 仅支持目录上传")
            context.sys.exit(2)
        if user_ignore_patterns:
            context.print_error("--ignore 仅支持目录上传")
            context.sys.exit(2)
    elif path.is_dir():
        ignore_patterns = context.effective_cli_upload_ignore_patterns(
            user_ignore_patterns
        )
        if resumable is None:
            resumable = not bool(message)
        if resumable and message:
            context.print_error("--resumable 不支持 --message")
            context.sys.exit(2)
        if auto_configure_lfs and not resumable:
            context.print_error("--auto-configure-lfs 仅支持 resumable 目录上传")
            context.sys.exit(2)
    else:
        context.print_error(f"不支持的路径类型: {path}")
        context.sys.exit(1)

    try:
        context.validate_upload_path_no_symlinks(path)
    except ValueError as error:
        context.print_error(str(error))
        context.sys.exit(1)

    if not context.config.is_logged_in():
        context.print_error("请先登录：atomgit login")
        context.sys.exit(1)

    if path.is_file():
        context.print_info(f"正在上传文件: {path}")
        file_size = context.format_file_size(path.stat().st_size)
        context.print_info(f"文件大小: {file_size}")
        if pipr:
            context.print_info(f"仓库内路径: {pipr}/")
        if repo_type:
            context.print_info(f"仓库类型: {repo_type}")
        if revision:
            context.print_info(f"目标分支: {revision}")
        result = context.run_usecase(
            "upload_file",
            path,
            repo_id,
            repo_type=repo_type,
            revision=revision,
            path_in_repo=path_in_repo or "./",
            ignore_patterns=user_ignore_patterns,
            timeout=timeout_sec or 300.0,
            progress=show_progress,
            message=message,
            num_workers=num_workers,
            _cli_repo_type_explicit=repo_type is not None,
        )
        if result.ok:
            context.print_success(f"文件上传成功: {path.name}")
        else:
            context.print_error(f"文件上传失败: {path.name}")
            context.sys.exit(1)

    elif path.is_dir():
        file_count, upload_size = context.get_upload_file_stats(path, ignore_patterns)
        dir_size = context.format_file_size(upload_size)

        context.print_info(f"正在上传目录: {path}")
        context.print_info(f"待上传文件数量（应用忽略规则后）: {file_count}")
        context.print_info(f"待上传目录大小（应用忽略规则后）: {dir_size}")
        context.print_info("上传总时限: 不限")
        request_timeout = (
            timeout_sec
            if timeout_sec is not None
            else context._RESUMABLE_DEFAULT_REQUEST_TIMEOUT
        )
        context.print_info(f"默认网络请求等待超时: {request_timeout:g}秒")
        if pipr:
            context.print_info(f"仓库内路径: {pipr}/")
        if repo_type:
            context.print_info(f"仓库类型: {repo_type}")
        if revision:
            context.print_info(f"目标分支: {revision}")
        context.print_info("macOS 元数据默认忽略: AppleDouble, .DS_Store")
        if user_ignore_patterns:
            context.print_info(f"额外用户忽略模式: {', '.join(user_ignore_patterns)}")
        if num_workers:
            context.print_info(f"并发 worker: {num_workers}")
        context.print_info(f"外层批次上限: {batch_size} 个文件")
        if resumable:
            context.print_info("上传模式: 断点续传/分块 (resumable)")
            if auto_configure_lfs:
                context.print_info(
                    "Git LFS 自动配置: 已启用；将检查服务端判定的 LFS 扩展名并按需修改远端配置"
                )
            if not repo_type:
                context.print_info(
                    "提示：未指定 --repo-type，断点续传模式下默认按 model 处理"
                )
        if not show_progress:
            context.print_info("进度条已禁用")

        observe_session = None
        if resumable:
            observe_session = UploadSession(
                uuid.uuid4().hex[:12],
                repo_name=repo_id,
                repo_type=repo_type or "model",
                revision=revision or "main",
            )
            observe_session.update(
                files_total=file_count,
                bytes_total=upload_size,
                batch=f"0/{max(1, (file_count + batch_size - 1) // batch_size)}",
            )
        try:
            if observe_session is not None:
                import importlib

                lfs_service = importlib.import_module("atomgit.adapters.lfs.service")
                lfs_service.set_upload_observer(
                    lambda event: observe_session.event(
                        event.get("kind", "LFS event"), event.get("kind", "lfs")
                    )
                )
            result = context.run_usecase(
                "upload_folder",
                path,
                repo_id,
                repo_type=repo_type,
                revision=revision,
                path_in_repo=path_in_repo or "./",
                ignore_patterns=ignore_patterns,
                resumable=resumable,
                num_workers=num_workers,
                batch_size=batch_size,
                timeout=request_timeout,
                progress=show_progress,
                message=message,
                auto_configure_lfs=auto_configure_lfs,
                _cli_repo_type_explicit=repo_type is not None,
            )
            if observe_session is not None:
                observe_session.finish("finished" if result.ok else "failed")
            if result.ok:
                context.print_success(f"目录上传成功: {path}")
            else:
                context.print_error(f"目录上传失败: {path}")
                context.sys.exit(1)
        except BaseException:
            if observe_session is not None:
                observe_session.finish("failed")
            raise
        finally:
            if observe_session is not None:
                lfs_service.set_upload_observer(None)
            if observe_session is not None:
                observe_session.close()


def download(
    context,
    repo_id,
    directory,
    force,
    verify_checksum,
    resume_download,
    prune,
    repo_type,
):
    if not context.validate_repo_name(repo_id):
        context.print_error("仓库ID格式不正确，应为: username/repo-name")
        context.sys.exit(1)

    if directory:
        local_path = context.Path(directory)
        if not context.is_valid_path(directory):
            context.print_error(f"无效的目录路径: {directory}")
            context.sys.exit(1)
    else:
        local_path = context.Path.cwd() / repo_id.split("/")[-1]

    if local_path.exists():
        if local_path.is_file():
            context.print_error(f"目标路径是文件，不是目录: {local_path}")
            context.sys.exit(1)
        elif local_path.is_dir() and any(local_path.iterdir()):
            if force:
                context.print_info("强制覆盖模式，将重新下载所有文件")
            elif verify_checksum:
                context.print_info(
                    "目录已存在；将校验已有文件（不匹配时可使用 --force）"
                )
            else:
                context.print_info(
                    "目录已存在；已有文件默认跳过（不校验内容，--force 可覆盖）"
                )

    if not context.ensure_directory(local_path):
        context.print_error(f"无法创建目录: {local_path}")
        context.sys.exit(1)

    context.print_info(f"正在下载仓库: {repo_id}")
    context.print_info(f"下载到: {local_path}")
    if verify_checksum:
        context.print_info("checksum 校验已启用")
    if resume_download:
        context.print_info("断点续传已启用（完成后自动校验 checksum）")
    if prune:
        context.print_info("安全清理已启用（仅删除下载 manifest 记录的文件）")

    if not context.config.is_logged_in():
        context.print_info("当前未登录，尝试下载公开仓库...")

    result = context.run_usecase(
        "download_snapshot",
        repo_id,
        repo_type=repo_type,
        local_dir=local_path,
        force=force,
        checksum=verify_checksum,
        resume=resume_download,
        prune=prune,
    )
    if result.ok:
        context.print_success(f"仓库下载成功: {local_path}")
    else:
        context.print_error(f"仓库下载失败: {repo_id}")
        if not context.config.is_logged_in():
            context.print_info("提示：如果这是私有仓库，请先使用 'atomgit login' 登录")
        context.sys.exit(1)


def download_file(
    context,
    repo_id,
    filename,
    directory,
    force,
    verify_checksum,
    resume_download,
    repo_type,
):
    if not context.validate_repo_name(repo_id):
        context.print_error("仓库ID格式不正确，应为: username/repo-name")
        context.sys.exit(1)

    if directory:
        if not context.is_valid_path(directory):
            context.print_error(f"无效的目录路径: {directory}")
            context.sys.exit(1)
        local_path = context.Path(directory)
    else:
        local_path = context.Path.cwd()

    if local_path.exists() and local_path.is_file():
        context.print_error(f"目标路径是文件，不是目录: {local_path}")
        context.sys.exit(1)
    if not context.ensure_directory(local_path):
        context.print_error(f"无法创建目录: {local_path}")
        context.sys.exit(1)

    context.print_info(f"正在下载文件: {repo_id}/{filename}")
    context.print_info(f"下载到: {local_path}")
    if verify_checksum:
        context.print_info("checksum 校验已启用")
    if resume_download:
        context.print_info("断点续传已启用（完成后自动校验 checksum）")
    if not context.config.is_logged_in():
        context.print_info("当前未登录，尝试从公开仓库下载...")

    result = context.run_usecase(
        "download_file",
        repo_id,
        filename,
        repo_type=repo_type,
        local_dir=local_path,
        force=force,
        checksum=verify_checksum,
        resume=resume_download,
    )
    if result.ok:
        context.print_success(f"文件下载成功: {filename}")
    else:
        context.print_error(f"文件下载失败: {repo_id}/{filename}")
        if not context.config.is_logged_in():
            context.print_info("提示：如果这是私有仓库，请先使用 'atomgit login' 登录")
        context.sys.exit(1)
