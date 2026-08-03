# 文档导航

## 面向用户和维护者

- [vision.md](vision.md)：项目定位、边界和成功标准。
- [architecture.md](architecture.md)：当前代码结构、调用链和已知架构风险。
- [upload_command_analysis.md](upload_command_analysis.md)：当前 upload 参数、分支和
  已知缺陷。
- [development.md](development.md)：conda 环境、分支和 Issue 开发流程。
- [testing.md](testing.md)：离线、契约、打包和远程测试规范。
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

## 已知文档缺口

- README 声明 MIT License，`setup.py` 也使用 MIT classifier，但仓库当前没有独立
  `LICENSE` 文件。正式对外分发前应由项目所有者确认版权主体并补齐许可证文本。
- README 的上游 PyPI 安装说明不代表 `yuto` 独立版本；独立安装渠道仍在规划中。
