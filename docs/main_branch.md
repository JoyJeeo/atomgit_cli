# main 分支与 GitHub 远程

## 当前约定

- 唯一代码仓库：[JoyJeeo/atomgit_cli](https://github.com/JoyJeeo/atomgit_cli)。本地远程名 `github`，维护者 checkout 使用 `git@github.com:JoyJeeo/atomgit_cli.git`；README 的新 clone 使用同仓库 HTTPS 地址。
- `main` 是 GitHub 默认分支、开发与发布主线，本地跟踪 `github/main`。
- 较大改动从 `main` 创建本地任务分支；验收并获授权后合回 `main`，只推送 `main`，任务分支不推送。
- push CI 仅监听 `main`，PR 和发布仍执行完整离线矩阵。发布必须来自 `main` 的明确 SHA，并通过完整 CI 和 `release-approval` 人工审批。
- GitHub Actions 的 checkout 远程名为 `origin`，发布校验使用 `origin/main`；它与本地的 `github` 指向同一仓库。
- 不再维护 AtomGit Git 远程、镜像分支或自动上游同步。CLI/SDK 访问 AtomGit 模型与数据集的服务端点保持不变。

## 2026-10-24 迁移与兼容

原开发分支 `yuto` 延续为 `main`。迁移前的旧 `main` 完全包含在开发分支历史中，
因此采用快进更新，无强制推送或提交历史重写。标签、发布产物和其他功能分支保留。
历史验收记录中的 `yuto` 是当时真实名称，不改写为新的历史事实。

旧 `/yuto/` raw 地址在删除旧分支后可能失效。当前地址：

- 安装：https://raw.githubusercontent.com/JoyJeeo/atomgit_cli/main/install.sh
- 清理：https://raw.githubusercontent.com/JoyJeeo/atomgit_cli/main/uninstall.sh

已有环境里生成的补全清理提示不会自动更新；遇到旧地址时使用上面的新清理地址。
升级源码后可在目标 conda 环境重新安装补全，写入新提示。

## 其他开发者迁移旧 checkout

先检查并提交或妥善保存本地改动，备份仓库；不要直接删除带有独有提交的旧分支。
在使用相同远程名 `github` 的 checkout 中：

```bash
git fetch github
git status --short --branch
git branch -vv
git log --oneline github/main..yuto
```

最后一条若有输出，先保留并评审本地独有提交，不要 reset 或强推覆盖。
确认原本地 `main` 没有需要保留的独有工作后，将它改名为本地备份，再迁移：

```bash
git branch -m main backup-main-before-migration
git switch yuto
git branch -m main
git branch --set-upstream-to=github/main main
git pull --ff-only
git remote set-head github -a
git fetch github --prune
```

仅当旧 `main` 存在且备份分支名未占用时执行第一条；没有旧 `yuto` 的新 checkout
直接跟踪 `github/main`。若仍配置了名为 `atomgit` 的旧代码远程，先保存其 URL
及需保留的远程分支引用，再执行 `git remote remove atomgit`。这不会删除远端仓库。

回滚迁移应依据迁移前备份恢复旧 `yuto` 引用、默认分支和发布环境分支限制；
不要把已包含后续开发的 `main` 强制退回旧提交。
