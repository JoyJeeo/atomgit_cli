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

## Codex 对话切换与任务恢复

Codex 对话记录不是项目事实来源。需要跨对话保留的目标、权限、决定、验证证据和
下一步统一写入 `.ai/TASK.md`，长期产品或架构事实写入对应 `.ai` 或 `docs` 文档。
不要另建并行的 `HANDOFF.md`、`PROJECT_STATE.md` 或聊天摘要文件。

### 准备切换对话

在调查完成、复现失败、实现完成、测试或 Review 结束、工作阻塞，以及计划切换
对话时，更新一次 `TASK.md` 的 `Handoff Snapshot`：

1. 记录 Issue 状态和当前阶段。
2. 记录 base/task branch、base commit、当前 HEAD 和工作树状态。
3. 工作树不干净时记录变更文件，并注明必须继续使用的 worktree。
4. 记录最后完成的动作、下一项可以直接执行的动作、阻塞和开放问题。
5. 记录准确的测试结果、失败和未运行项。
6. 只记录会约束后续工作的技术决定，不复制长命令输出或聊天内容。

交接内容禁止包含 token、真实配置内容、签名 URL 或可能携带凭据的原始异常。

### 在新对话中恢复

新对话应从仓库根目录或原任务 worktree 启动。根目录 `AGENTS.md` 会要求 Codex：

1. 读取 `.ai/README.md` 和 `.ai/TASK.md`；
2. 检查 Git 根目录、branch、HEAD、worktree、status、近期提交和相关 diff；
3. 将真实 Git 状态与交接快照比较；
4. 按任务类型读取需要的 `.ai` 文档和受影响源码、测试、用户文档；
5. 在编辑前报告恢复出的目标、阶段、下一步以及任何不一致。

可以用以下请求开始新对话：

```text
读取 AGENTS.md，按 .ai/README.md 和 .ai/TASK.md 恢复当前任务；先核对 Git、
相关源码和测试并汇报恢复结果，不要仅依据旧聊天或 TASK.md 推测代码状态。
```

### Worktree 边界

- 同一 worktree 中的新对话可以读取现有未提交修改。
- 独立 worktree 只能可靠继承已经提交的 Git 状态，不能看到另一个 worktree 的
  staged、unstaged 或尚未提交的 `TASK.md`。
- 有未提交工作时必须在原 worktree 继续。只有工作树干净，或已得到明确授权形成
  checkpoint commit 后，才能将任务转到独立 worktree。
- 不得仅为切换对话而绕过仓库的 commit、push 或 merge 授权规则。

`TASK.md` 为 `completed` 时不得推断仍需继续实现；选择下一个 Issue 前应按流程
将其重置为 `inactive`。历史合同和完成证据由 Git 历史保留。

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
