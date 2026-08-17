# 构建、安装与发布

## 当前打包方式

`setup.py` 将仓库根目录映射为 `atomgit` 包，并发布兼容的顶层
`atomgit_hub` 模块。console script 为：

```text
atomgit = atomgit.cli:cli
```

因此安装后同时获得：

- `atomgit` 命令；
- `python -m atomgit`；
- `import atomgit`；
- `import atomgit_hub`。

## 开发安装

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate atomgit_cli
python -m pip install -e .
```

## 本地构建

仓库现有 `deploy.sh build` 会清理 `dist/` 并调用 `python -m build`：

```bash
./deploy.sh build
```

构建后应在隔离环境安装 wheel 并执行入口冒烟测试。仅构建成功不代表 wheel
中的包结构和命令入口正确。

## GitHub Release 分发

GitHub Release 是 AtomGit CLI 唯一官方发布渠道，项目不发布到 PyPI。`deploy.sh`
只负责本地构建、安装和生成 `SHA256SUMS`，不包含 twine、PyPI token 或远程写路径。
第三方依赖仍可从用户配置的 pip 索引解析。

发布身份和版本规则：

1. `yuto` 是唯一发布分支；版本源在 `version.py`，使用稳定 `X.Y.Z`。
2. 从明确的 `yuto` SHA 创建本地 `release/X.Y.Z` 准备分支，合并回 `yuto` 后才发布。
3. 维护者手动启动 `.github/workflows/release.yml`，输入版本和精确 SHA；workflow
   使用受保护的 `release-approval` 环境。
4. Actions 使用仓库局部的 `github-actions[bot]` 身份创建不可移动的
   annotated `X.Y.Z` tag，构建 wheel/sdist/checksum，先创建 draft Release 并验证
   资产，再转为公开 Release。
5. 重跑只接受同名且字节相同的 tag/asset；不覆盖不同内容。未完成 draft 不会被
   安装器的稳定 resolver 选择。
6. GitHub Release 正文来自精确发布 SHA 中的 `RELEASE_NOTES.md`，必须列出本版
   范围和已知限制，不得使用空说明发布。

普通用户安装器选择最高的已完成纯数字 Release，显式 `--version X.Y.Z` 选择指定
版本。历史 `v...` tag 和 Release 不删除，但永远不参与新的默认选择。

源码开发者应使用 `git checkout yuto`、隔离 conda 环境、锁定依赖和
`python -m pip install -e .`。源码更新使用 `git pull --ff-only` 后重新安装依赖和
editable 包；`atomgit update` 会检测并拒绝修改这种安装。

## 发布门禁

- 版本值一致；
- 全部离线测试通过；
- wheel 隔离安装和 CLI/SDK 冒烟测试通过；
- Release notes 明确已知限制；
- 产物不包含 token、缓存、临时目录或本地配置；
- 发布动作获得明确授权；
- 发布后从用户视角重新安装并验证。

此外，稳定版必须满足 `.ai/ROADMAP.md` 的 Stability Release Gate：已知核心
缺陷完成验收、model/dataset 和 resumable 具有远程证据、无开放 P0/P1 Review
问题、版本来源可识别。满足构建条件不自动授权发布。

AI 发布规范同时受 `.ai/DOD.md` 和 `.ai/DEVELOPMENT_RULES.md` 约束。
