"""Authentication and configuration command implementations."""


def login(context, token, token_stdin):
    if token is not None and token_stdin:
        raise context.click.UsageError("--token 与 --token-stdin 不能同时使用")

    if token_stdin:
        token = context.sys.stdin.readline().rstrip("\r\n")
        if not token:
            raise context.click.UsageError("--token-stdin 未读取到访问令牌")

    if not token:
        token = context.getpass("请输入访问令牌: ")

    if not token:
        context.print_error("令牌不能为空")
        context.sys.exit(1)

    context.print_info("正在验证登录信息...")

    result = context.run_usecase("login", token)
    if result.ok:
        context.print_success("登录成功！")

        if context.check_git_available():
            if context.setup_git_credentials(token):
                context.print_info(
                    "✨ Git凭证已配置，现在可以直接使用git命令访问AtomGit仓库"
                )
            else:
                context.print_warning("Git凭证配置失败，请手动配置或使用完整URL")
        else:
            context.print_warning("未检测到Git，跳过Git凭证配置")
    else:
        context.print_error("登录失败，请根据上方提示处理")
        context.sys.exit(1)


def logout(context):
    was_logged_in = context.config.is_logged_in()
    config_dir = context.Path.home() / ".atomgit"
    has_git_state = any(
        (config_dir / filename).exists()
        for filename in ("git-helper-state.json", "git-credential-atomgit")
    )

    if was_logged_in:
        result = context.run_usecase("logout")
        if not result.ok:
            context.print_error("退出登录失败")
            context.sys.exit(1)

    if (was_logged_in or has_git_state) and context.check_git_available():
        if not context.clear_git_credentials():
            context.print_error(
                "登录 token 已清除，但 Git 凭证配置恢复失败；"
                "请修复 Git 配置后重新运行 'atomgit logout'"
            )
            context.sys.exit(1)

    if was_logged_in:
        context.print_success("已退出登录")
    else:
        context.print_info("当前未登录")


def whoami(context):
    if not context.config.is_logged_in():
        context.print_warning("请先登录：atomgit login")
        context.sys.exit(1)
    result = context.run_usecase("whoami")
    user_info = result.value if result.ok else None
    if user_info:
        context.print_success(f"当前登录用户: {user_info['login']}")
    else:
        context.print_error("无法确认当前登录用户，请根据上方提示处理")
        context.sys.exit(1)


def config_show(context):
    if context.config.is_logged_in():
        context.print_info("登录状态: 已登录")
        context.print_info(f"配置文件: {context.config.config_file}")

        if context.check_git_available():
            try:
                statuses = context.get_atomgit_git_helper_status()
                configured = [host for host, enabled in statuses.items() if enabled]
                missing = [host for host, enabled in statuses.items() if not enabled]
                if not missing:
                    context.print_info(
                        f"Git集成: 已启用（{len(configured)}/{len(statuses)} 域名）"
                    )
                elif configured:
                    context.print_info(
                        "Git集成: 部分启用（已配置: "
                        + ", ".join(configured)
                        + "；缺少: "
                        + ", ".join(missing)
                        + "）"
                    )
                else:
                    context.print_info("Git集成: 未启用")
            except Exception:
                context.print_info("Git集成: 检查失败")
    else:
        context.print_warning("当前未登录")
        context.print_info(f"配置文件: {context.config.config_file}")
