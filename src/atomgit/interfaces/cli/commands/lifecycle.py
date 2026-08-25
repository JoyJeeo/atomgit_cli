"""Update, uninstall, and completion command implementations."""


def stable_version_option(context, ctx, param, value):
    if value is not None and not context.is_stable_version(value):
        raise context.click.BadParameter("must be an exact stable X.Y.Z version")
    return value


def update(context, target_version, force_reinstall):
    try:
        result = context.run_update(
            version=target_version,
            force_reinstall=force_reinstall,
            python=context.sys.executable,
        )
    except context.ReleaseError as error:
        raise context.click.ClickException(str(error)) from error

    status = result.get("status")
    if status == "source":
        context.click.echo(
            "检测到 Git/可编辑源码安装；atomgit update 不会修改源码。请执行 "
            "git checkout yuto、git pull --ff-only，在隔离 conda 环境中安装锁定依赖，"
            "然后重新执行 python -m pip install -e .。",
            err=True,
        )
        raise context.click.exceptions.Exit(1)
    if status == "skipped":
        context.click.echo(f"AtomGit CLI 已是 {result['version']}，跳过更新。")
        return
    context.click.echo(
        f"AtomGit CLI {result['version']} 已安装到 {result['python']}。\n"
        f"包位置: {result.get('package', 'unknown')}\n"
        f"命令路径: {result.get('command', 'unknown')}\n"
        f"脚本目录: {result['scripts']}"
    )
    if result.get("completion_warning"):
        context.click.echo(f"warning: {result['completion_warning']}", err=True)


def uninstall(context, yes):
    try:
        plan = context.build_uninstall_plan()
    except context.UninstallError as error:
        raise context.click.ClickException(str(error)) from error

    context.click.echo(f"Python 解释器: {plan['python']}")
    context.click.echo(f"环境根目录: {plan['prefix']}")
    context.click.echo(f"AtomGit 版本: {plan['version']}")
    if plan["managed_paths"]:
        context.click.echo("将删除的环境补全文件:")
        for path in plan["managed_paths"]:
            context.click.echo(f"  {path}")
    else:
        context.click.echo("环境补全文件: 无（当前解释器不属于活动 conda 环境）")

    if not yes and not context.click.confirm("确认卸载 AtomGit CLI？"):
        raise context.click.Abort()
    try:
        context.run_uninstall(plan)
    except context.UninstallError as error:
        raise context.click.ClickException(str(error)) from error
    context.click.echo("AtomGit CLI 已从当前 Python 卸载。")
    if plan["managed_paths"]:
        context.click.echo(
            "当前 shell 可能仍加载旧补全；请执行 conda deactivate/activate 或 exec zsh。"
        )


def show_completion(context, shell):
    try:
        context.click.echo(context.completion_script(context.cli, shell), nl=False)
    except context.CompletionConfigError as error:
        raise context.click.ClickException(str(error)) from error


def install_shell_completion(context, shell):
    try:
        migrate_legacy = False
        if context.legacy_completion_present():
            context.click.echo("检测到旧版全局补全和 .zshrc 受控配置。")
            migrate_legacy = context.click.confirm(
                "是否备份 .zshrc、移除旧版全局补全并迁移到当前 conda 环境？"
            )
            if not migrate_legacy:
                raise context.click.Abort()
        script_path, activate_path, deactivate_path = context.install_completion(
            context.cli,
            shell,
            migrate_legacy=migrate_legacy,
        )
    except context.CompletionConfigError as error:
        raise context.click.ClickException(str(error)) from error
    context.click.echo(f"Zsh 补全已安装: {script_path}")
    context.click.echo(f"Conda 激活 hook 已安装: {activate_path}")
    context.click.echo(f"Conda 停用 hook 已安装: {deactivate_path}")
    context.click.echo("请重新激活当前 conda 环境，或执行 exec zsh 后再使用补全。")


def uninstall_shell_completion(context, shell):
    try:
        paths = context.uninstall_completion(shell)
    except context.CompletionConfigError as error:
        raise context.click.ClickException(str(error)) from error
    context.click.echo("当前 conda 环境的 Zsh 补全已移除")
    if paths:
        context.click.echo(
            "当前 shell 可能仍加载旧补全；请重新激活环境或执行 exec zsh。"
        )
