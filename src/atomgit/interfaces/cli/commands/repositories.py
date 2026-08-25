"""Cache and repository command implementations."""


def clear_cache(context):
    try:
        removed = context.clear_atomgit_cache()
    except Exception as error:
        context.print_error(f"清理 AtomGit 缓存失败: {error}")
        context.sys.exit(1)
    context.print_success(f"AtomGit 缓存已清理（移除 {removed} 项）")


def create(context, repo_name, repo_type, private, public_repo, exist_ok):
    if private == public_repo:
        raise context.click.UsageError("必须且只能指定 --private 或 --public")
    if not context.config.is_logged_in():
        context.print_error("请先登录：atomgit login")
        context.sys.exit(1)
    if not context.validate_repo_name(repo_name):
        context.print_error("仓库名称格式不正确，应为: username/repo-name")
        context.sys.exit(1)

    context.print_info(f"正在创建{repo_type}仓库: {repo_name}")
    result = context.run_usecase(
        "create_repository",
        repo_name,
        repo_type=repo_type,
        private=private,
        exist_ok=exist_ok,
    )
    if result.ok:
        if exist_ok:
            context.print_success(f"仓库 {repo_name} 已存在或已创建")
        else:
            context.print_success(f"仓库 {repo_name} 创建成功")
    else:
        context.print_error(f"仓库 {repo_name} 创建失败")
        context.sys.exit(1)


def list_repositories(context):
    if not context.config.is_logged_in():
        context.print_error("请先登录：atomgit login")
        context.sys.exit(1)

    result = context.run_usecase("list_repositories")
    repositories = result.value if result.ok else None
    if repositories is None:
        context.print_error("获取仓库列表失败")
        context.sys.exit(1)
    if not repositories:
        context.print_info("没有可显示的仓库")
        return

    for repository in repositories:
        repo_id = repository.get("full_name") or repository.get("path_with_namespace")
        if not repo_id:
            owner = repository.get("owner")
            owner_name = None
            if isinstance(owner, dict):
                owner_name = owner.get("login") or owner.get("path")
            name = repository.get("name") or repository.get("path")
            if owner_name and name:
                repo_id = f"{owner_name}/{name}"
            else:
                repo_id = name or "(unknown)"

        private = repository.get("private")
        if isinstance(private, bool):
            visibility = "private" if private else "public"
        else:
            visibility = repository.get("visibility") or "unknown"
        context.print_info(f"{visibility}\t{repo_id}")


def set_repository_visibility(context, repo_id, visibility):
    if not context.config.is_logged_in():
        context.print_error("请先登录：atomgit login")
        context.sys.exit(1)
    if not context.validate_repo_name(repo_id):
        context.print_error("仓库ID格式不正确，应为: username/repo-name")
        context.sys.exit(1)

    private = visibility == "private"
    result = context.run_usecase("set_repository_visibility", repo_id, private=private)
    if result.ok:
        context.print_success(f"仓库 {repo_id} 已设置为 {visibility}")
    else:
        context.print_error(f"仓库 {repo_id} 可见性修改失败")
        context.sys.exit(1)


def delete_repository(context, repo_id, confirm):
    if not context.config.is_logged_in():
        context.print_error("请先登录：atomgit login")
        context.sys.exit(1)
    if not context.validate_repo_name(repo_id):
        context.print_error("仓库ID格式不正确，应为: username/repo-name")
        context.sys.exit(1)
    if confirm != repo_id:
        raise context.click.UsageError("--confirm 必须与仓库 ID 完全一致")

    context.print_warning(f"正在永久删除仓库: {repo_id}")
    result = context.run_usecase("delete_repository", repo_id, confirmation=confirm)
    if result.ok:
        context.print_success(f"仓库 {repo_id} 已删除并验证不存在")
    else:
        context.print_error(f"仓库 {repo_id} 删除失败或远端状态未知")
        context.sys.exit(1)


def create_branch(context, repo_id, branch_name, source):
    if not context.config.is_logged_in():
        context.print_error("请先登录：atomgit login")
        context.sys.exit(1)
    if not context.validate_repo_name(repo_id):
        context.print_error("仓库ID格式不正确，应为: username/repo-name")
        context.sys.exit(1)
    if not branch_name or not context.is_supported_upload_revision(branch_name):
        raise context.click.UsageError("分支名称不合法")
    if not source or not context.is_supported_upload_revision(source):
        raise context.click.UsageError("来源 revision 不合法")
    result = context.run_usecase("create_branch", repo_id, branch_name, source=source)
    if result.ok:
        context.print_success(f"分支 {branch_name} 创建成功")
    else:
        context.print_error(f"分支 {branch_name} 创建失败")
        context.sys.exit(1)
