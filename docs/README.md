# 文档导航

## 面向用户和维护者

- [vision.md](vision.md)：项目定位、边界和成功标准。
- [architecture.md](architecture.md)：当前代码结构、调用链和已知架构风险。
- [cli_feature_baseline.md](cli_feature_baseline.md)：当前公开 CLI 功能清单及不可回退的测试契约。
- [upload_command_analysis.md](upload_command_analysis.md)：当前 upload 参数、分支和
  已知缺陷。
- [development.md](development.md)：conda 环境、分支、Issue 开发流程，以及
  Codex 对话切换和 worktree 交接规则。
- [testing.md](testing.md)：离线、契约、打包和远程测试规范。
- [development_floor.md](development_floor.md)：所有现有和未来能力必须共同遵守的
  能力登记、行为不变量、证据和阻断门禁。
- [release.md](release.md)：当前打包方式和 `yuto` 独立分发目标。
- [faq.md](faq.md)：常见开发和使用问题。
- [yuto_branch.md](yuto_branch.md)：`main` 与 `yuto` 的权威分支关系。

## 文档事实规则

- README 面向首次使用者，保持简洁。
- `docs/` 解释当前行为和维护流程。
- `.ai/` 是 AI 执行规范，不代替源码和测试。
- 源码和锁定依赖签名是当前实现事实；远程能力必须有远程测试证据。
- `ROADMAP.md` 中的内容是计划，不是已经实现或已经授权的任务。
- AI Issue 生命周期、实现/Review/修复 Prompt 和人工验收规则见
  [`.ai/WORKFLOW.md`](../.ai/WORKFLOW.md)。

## 发布状态

- `yuto` 版本源来自 `src/atomgit/infrastructure/version.py`，稳定 Release 使用无 `v` 的 `X.Y.Z` tag。
- GitHub Release 提供 wheel、源码包和 `SHA256SUMS`；AtomGit CLI 不发布到 PyPI。
- 项目由 JoyJeeo 以 Apache License 2.0 授权。
