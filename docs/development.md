# 开发指南

## 开发基线

本仓库采用特殊的双主线关系：

```text
AtomGit 上游 atomgit/main
            |
            v
        本地 main
            |
            v
        本地 yuto ----> github/yuto
```

- `main` 是 AtomGit 上游同步分支，不用于日常功能开发。
- `yuto` 是 GitHub 侧实际开发主线。
- 上游变化先进入 `main`，再选择性同步到 `yuto`。
- 功能开发和缺陷修复以 `yuto` 为基线。

详细约定见 [yuto_branch.md](yuto_branch.md)。

## 环境要求

本项目所有命令都必须在 `atomgit_cli` conda 环境中执行。每个新的 shell
会话先运行：

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate atomgit_cli
```

确认环境：

```bash
test "$CONDA_DEFAULT_ENV" = "atomgit_cli"
python --version
python -m pip --version
```

不要使用系统 Python 代替目标环境。

## 开发安装

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

验证入口：

```bash
atomgit --version
atomgit --help
python -m atomgit --help
python -c "import atomgit, atomgit_hub"
```

## Issue 开发流程

一个任务对应一个可以独立验收的 Issue 或问题：

1. 从 `yuto` 确认工作树状态。
2. 明确目标、证据、范围、非目标和验收标准。
3. 对较大任务创建独立任务分支。
4. 沿真实调用链阅读源码和测试。
5. 先增加能复现问题的测试，再实施修复。
6. 运行聚焦测试和完整离线检查。
7. 按 `.ai/DOD.md` 自检。
8. 对高风险变更按 `.ai/REVIEW.md` 独立评审。
9. 经授权后再提交、推送或创建 PR。

完整的角色、Issue 合同和可复用 Prompt 见 `.ai/WORKFLOW.md`。任何时候只能在
`.ai/TASK.md` 中激活一个 Issue。

任务可以修改完成同一行为所必需的多个模块。例如一个 CLI 上传缺陷可能同时
需要修改 `cli.py`、`api.py` 和对应测试；禁止的是无关重构，而不是跨越真实
调用边界。

### Issue 分类

本仓库按真实维护边界分类，而不是按“一个文件等于一个模块”拆分：

- `bug`、`compatibility`、`testing`；
- `cli`、`sdk`；
- `security`、`distribution`、`documentation`；
- `upstream-sync`、`release`。

Issue 必须包含用户影响、复现证据、当前/预期行为、调用链、范围、兼容要求、
验收标准、测试和逐项权限。路线图编号只是候选编号，未经授权不会自动创建远程
GitHub Issue。

### 实现、Review 与验收

```text
激活 Issue -> 实现与回归测试 -> DoD -> 独立 AI Review
           -> 修复与复测 -> 人工验收 -> 授权后的交付动作
```

Reviewer 阶段只报告问题，不直接修改。存在 P0/P1、超出 Issue 范围或缺少强制
证据时必须 `REQUEST CHANGES`。AI 的 `APPROVED` 不等于允许提交、推送或合并。

### 两种交付模式

- 本地验收：Review 和测试完成后由人验收，再按授权创建本地 commit。
- PR 模式：先按授权创建 commit、push 和 PR，再进行 Review、修复提交、CI、
  人工验收和授权 merge。

`TASK.md` 会分别记录 commit、push、PR、merge、Issue 状态和 release 权限，
不能用其中一个权限推导另一个权限。

## 修改范围

- 对外行为变化需要同步用户文档和示例。
- 内部重构不要求机械修改所有文档。
- 不创建只含注释、没有立即用途的占位源码。
- 不在功能任务中顺带迁移 `src/` 布局或升级依赖。
- 不留下无任务归属的 TODO、注释掉的旧实现或死代码。

## 安全边界

默认只允许运行离线测试。以下操作需要用户对具体动作明确授权：

- 创建、上传、推送、删除或修改真实 AtomGit 仓库；
- 修改真实的全局 Git credential helper；
- 读取真实 token；
- 推送分支、合并、打标签、创建 Release 或上传 PyPI。

Git helper 测试应使用隔离的 `HOME` 和 Git 配置。远程测试必须使用专用账号、
显式环境变量和唯一的一次性仓库名。

## 最低完成检查

```bash
python -m compileall -q .
git diff --check
```

还必须运行受影响的离线测试。完整规则见 [testing.md](testing.md) 和
`.ai/DOD.md`。
