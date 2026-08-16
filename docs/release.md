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

PyPI 的 `atomgit` 仍代表上游发行渠道，不应视为本仓库 `yuto` 版本。

## yuto 独立分发

`yuto` 使用与上游 PyPI 区分的 GitHub Release 渠道：

1. 包版本使用 `1.0.6`，Git tag 使用 `v1.0.6`。
2. 创建 GitHub Release，并上传 wheel 和源码归档。
3. 为每个产物发布 SHA256。
4. 提供仓库自有 `install.sh`，默认下载固定 Release，而不是不断变化的分支。
5. 安装脚本支持显式版本、验证校验和，并为 Zsh 默认启用命令补全。

仓库提供版本化、校验和安装脚本。激活目标 conda 环境后可运行：

```bash
curl -fsSL https://raw.githubusercontent.com/JoyJeeo/atomgit_cli/v1.0.6/install.sh | sh
```

默认安装 `v1.0.6`；显式版本可用
`sh install.sh --version 1.0.6`。脚本只从对应固定 GitHub Release
下载 wheel 和 `SHA256SUMS`，校验成功后使用当前 conda 环境的
`python -m pip` 安装。未激活 conda 或缺少校验工具时会停止，不会回退到系统
Python。

检测到 `$SHELL` 为 Zsh 时，官方安装器会在 wheel 成功安装后执行
`atomgit completion install --shell zsh`；`--no-completion` 可显式关闭。补全
设置失败会输出可重试警告，但不会否定已经成功的包安装。Bash/Fish 和非 Zsh
启动文件不会被修改。标准 pip 没有受支持的安装后钩子，因此直接
`python -m pip install` 的用户需要手动运行上述补全安装命令。

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
