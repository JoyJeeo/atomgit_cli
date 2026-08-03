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

## PyPI 发布

`deploy.sh twine` 面向原有 PyPI 发布流程，需要发布 token，并会执行外部写
操作。只有得到明确发布授权后才能运行。

当前 `yuto` 与上游包版本都可能显示为 `1.0.5`，用户无法只凭版本判断安装
来源。因此在独立分发建立前，不应把 PyPI 的 `atomgit` 默认视为 `yuto`
版本。

## yuto 独立分发目标

推荐建立与上游 PyPI 区分的安装渠道：

1. 使用可识别的版本，例如 `1.0.5+yuto.1` 或后续正式版本策略。
2. 创建 GitHub Release，并上传 wheel 和源码归档。
3. 为每个产物发布 SHA256。
4. 提供仓库自有 `install.sh`，默认下载固定 Release，而不是不断变化的分支。
5. 安装脚本支持显式版本，并验证校验和。

预期用户入口可以是：

```bash
curl -fsSL <raw-install-script-url> | bash
```

但在安装脚本、Release 和校验和真正创建前，这只是目标设计，不是当前可用
安装方式。

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
