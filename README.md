# AtomGit CLI & SDK

基于Transformers和Hugging Face Hub的AtomGit平台模型文件上传下载CLI工具和Python SDK

## 简介

AtomGit 是一个完整的工具包，提供命令行工具（CLI）和Python SDK两种方式与AtomGit平台交互，支持模型和数据集的上传、下载等操作。类似于huggingface_hub，用户只需安装一个`atomgit`包即可同时使用CLI命令和Python编程接口。工具基于Transformers和Hugging Face Hub SDK开发，并配置为连接AtomGit API端点。

## 功能特性

### CLI功能
- 🔐 用户认证和登录管理
- 🔗 **Git集成**：自动配置Git凭证，支持标准Git命令
- 📁 支持模型和数据集仓库创建
- ⬆️ 文件和目录上传，支持丰富的参数控制（见下文「上传文件」）
- ⬇️ 仓库内容下载（公开仓库无需登录）
- 🎨 彩色终端输出
- 📊 上传进度条（可禁用）
- 🔧 配置文件管理
- 🧩 **上传能力增强（v1.0.5+yuto.1）**：
  - 进度条开关（`--no-progress-bar`）
  - 仓库内目标路径（`-p/--path-in-repo`）
  - 仓库类型选择（`-r/--repo-type model|dataset`）
  - 默认分支兼容参数（`--revision main`；其他值会拒绝）
  - 忽略文件模式（`-i/--ignore`）
  - 断点续传/分块上传（`--resumable`、`--num-workers`）
  - 单文件上传无本地拷贝（直接走 `upload_file`）
  - 语义化错误分类（认证失败 / 仓库不存在 / 超时等，附可执行建议）

### SDK功能
- 🐍 **Python原生接口**：类似huggingface_hub的API设计
- 🔄 **与CLI共享配置**：使用相同的认证和配置文件
- 📦 **一键安装**：安装atomgit包即可同时使用CLI和SDK
- 🚀 **完整API**：snapshot_download、upload_folder、create_repository等
- 📝 **完善的文档**：详细的使用示例和错误处理

## 系统要求

- **Python 3.8+** (推荐Python 3.11+)
- 支持的操作系统：Windows, macOS, Linux

## 安装

### 从源码安装

```bash
git clone https://github.com/JoyJeeo/atomgit_cli.git
cd atomgit_cli
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate atomgit_cli
python -m pip install -e .
```

### 从 GitHub Release 安装 yuto 版本

激活目标 conda 环境后，可使用固定版本和 SHA-256 校验安装器：

```bash
curl -fsSL https://raw.githubusercontent.com/JoyJeeo/atomgit_cli/yuto/install.sh | sh
```

从 `v1.0.5-yuto.1` Release 下载 wheel、源码包、`LICENSE` 和 `SHA256SUMS`，
完整校验后安装：

```bash
shasum -a 256 -c SHA256SUMS
python -m pip install atomgit-1.0.5+yuto.1-py3-none-any.whl
```

发布页：<https://github.com/JoyJeeo/atomgit_cli/releases/tag/v1.0.5-yuto.1>

### 使用 PyPI 安装上游版本

```bash
python -m pip install atomgit
```

该命令安装 PyPI 上的上游发行版，不代表本仓库 `yuto` 分支。`yuto` 独立分发
方案见 [docs/release.md](docs/release.md)。

### 虚拟环境推荐

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### 快速开始

#### CLI使用
```bash
# 登录
atomgit login

# 下载模型
atomgit download wuyw/Qwen3-Reranker-0.6B-test -d ./models

# 上传文件
atomgit upload ./my-model --repo-id username/my-repo
```

#### SDK使用
```python
# 导入SDK
from atomgit_hub import snapshot_download

# 下载模型到本地目录
snapshot_download("wuyw/Qwen3-Reranker-0.6B-test", local_dir="./Qwen3-Reranker-0.6B-test")
```

### 1. 登录

首先需要登录到AtomGit平台：

```bash
atomgit login
```

系统会提示输入访问令牌（从AtomGit平台获取）。

**🎉 Git集成功能**：登录成功后，工具会自动配置Git凭证助手，这样你就可以直接使用标准的Git命令来操作AtomGit仓库，无需再次输入token。凭证助手会自动从AtomGit API获取你的真实用户名用于Git认证：

```bash
# 登录后，这些Git命令将自动使用保存的token
# 支持两种域名格式
git clone https://atomgit.com/username/repo-name.git
git clone https://hub.atomgit.com/username/repo-name.git
git push origin main
git pull origin main
```




### 2. 上传文件

`atomgit upload` 支持文件与目录上传，并提供丰富的参数控制。

#### 基础用法

```bash
# 上传模型目录（默认上传到仓库根目录，默认分支 main）
atomgit upload ./your-model-dir --repo-id your-username/your-model-name

# 上传数据集目录
atomgit upload ./your-dataset-dir --repo-id your-username/your-dataset-name -r dataset

# 上传单个文件（v1.0.5 起直接上传，无本地拷贝开销）
atomgit upload ./model.bin --repo-id your-username/your-model-name
```

#### 完整选项

```bash
atomgit upload <path> --repo-id <id> [options]
```

| 选项 | 说明 |
|------|------|
| `--repo-id <id>` | 目标仓库ID（必填，如 `username/repo-name`） |
| `-m, --message <text>` | 上传提交说明 |
| `-t, --timeout <sec>` | 上传超时秒数，默认 300（大文件建议调大） |
| `--no-progress-bar` | 禁用进度条（日志/CI 场景） |
| `-p, --path-in-repo <prefix>` | 仓库内目标目录前缀（如 `sub/`），默认根目录 |
| `-r, --repo-type <model\|dataset>` | 仓库类型，默认按 model 处理 |
| `--revision <name>` | 当前仅接受默认分支 `main`；其他值退出 2，不会上传 |
| `-i, --ignore <patterns>` | 忽略的文件模式（逗号分隔，如 `*.tmp,logs/`），仅对目录上传有意义 |
| `--resumable` | 目录大文件断点续传接口，重复同一命令可复用本地上传状态 |
| `--num-workers <n>` | 断点续传模式的并发 worker 数（仅 `--resumable` 生效） |

#### 进阶示例

```bash
# 上传到仓库内 sub/ 目录、dataset 类型，忽略 .tmp 文件
atomgit upload ./data --repo-id user/my-dataset \
  -p sub/ -r dataset -i "*.tmp"

# 大目录断点续传（中断后再次执行同一命令即可续传）
atomgit upload ./large-model --repo-id user/large-model \
  --resumable --num-workers 4 -t 1800

# 单文件无本地拷贝，直接上传到仓库内指定路径
atomgit upload ./weights.bin --repo-id user/model -p checkpoints/
```

> ⚠️ 注意：`--resumable` 模式下 HF 既定限制——`--path-in-repo` 与 `-m` 不生效（会产生多次提交）；`--repo-type` 必填，未指定时默认 `model`。

> 当前实现通过 `HfApi(token=...)` 认证，并已完成 404 MB 文件的真实中断、恢复
> 和 SHA-256 校验。AtomGit 不会创建请求的非默认分支，因此当前 CLI 在任何远程
> 调用前拒绝非 `main` revision。详见
> [上传实现分析](docs/upload_command_analysis.md)。

#### 错误处理

上传失败时，CLI 会给出语义化错误类型与可执行建议，例如：

```
上传文件失败[仓库不存在]: 404 ...
💡 建议: 仓库 user/repo 不存在或为私有且无访问权限。请检查 repo_id/repo_type，或先 atomgit login。
```

涵盖：认证失败 / 仓库不存在 / 受限仓库 / 仓库已禁用 / 分支不存在 / 请求参数错误 / 请求超时 / 网络连接失败 等情形。

### 3. 下载文件

#### 下载到当前目录

```bash
atomgit download your-username/your-model-name
```

#### 下载到指定目录

```bash
atomgit download your-username/your-model-name -d ./models/
```

### 4. 其他命令

#### 退出登录

```bash
atomgit logout
```

#### 显示配置信息

```bash
atomgit config-show
```

#### 查看当前登录用户

```bash
atomgit whoami
```

#### 创建仓库

```bash
# 创建私有 model 仓库
atomgit repo create your-username/your-repo --type model --private

# 创建私有 dataset 仓库
atomgit repo create your-username/your-dataset --type dataset --private
```

## SDK使用方法

AtomGit除了提供CLI工具外，还提供了类似huggingface_hub的Python SDK接口，让您可以在Python代码中直接使用AtomGit的功能。

### SDK功能特性

- 🐍 **Python原生接口**：类似huggingface_hub的API设计
- 🔄 **与CLI共享配置**：使用相同的认证和配置文件
- 📦 **一键安装**：安装atomgit包即可同时使用CLI和SDK
- 🚀 **功能齐全**：支持上传、下载、仓库管理等完整功能

### 1. SDK导入

```python
# 推荐方式：直接从atomgit_hub导入
from atomgit_hub import snapshot_download

# 或者从atomgit包导入
from atomgit import snapshot_download

# 导入多个功能
from atomgit_hub import (
    snapshot_download,    # 下载整个仓库
    download_file,       # 下载单个文件
    upload_folder,       # 上传文件
    create_repository    # 创建仓库
)
```

### 2. SDK下载功能

#### 下载整个仓库（推荐用法）

```python
from atomgit_hub import (
    snapshot_download,
    AtomGitAuthenticationError,
    AtomGitRepositoryNotFoundError,
    AtomGitNetworkError,
)

# 基本用法：下载到指定目录
snapshot_download(
    "wuyw/Qwen3-Reranker-0.6B-test", 
    local_dir="./Qwen3-Reranker-0.6B-test"
)

# 高级用法：更多参数控制
snapshot_download(
    repo_id="username/model-name",
    local_dir="./models/my-model",
    revision="main",              # 指定分支/标签
    force_download=False,         # 是否强制重新下载
    allow_patterns=["*.py", "*.md"],  # 只下载特定文件
    ignore_patterns=["*.bin"],    # 忽略特定文件
)
```

#### 下载单个文件

```python
from atomgit_hub import download_file

# 下载单个文件
file_path = download_file(
    repo_id="username/repo-name",
    filename="README.md",
    local_dir="./downloads"
)
print(f"文件下载到: {file_path}")
```

#### 获取文件下载URL

```python
from atomgit_hub import hub_download_url

# 获取文件直接下载链接
url = hub_download_url(
    repo_id="username/repo-name",
    filename="model.bin",
    revision="main"
)
print(f"下载链接: {url}")
```

### 3. SDK上传功能

#### 上传目录

```python
from atomgit_hub import upload_folder

# 基本目录上传
upload_folder(
    folder_path="./model-directory",
    path_in_repo="./",
    repo_id="username/repo-name",
    commit_message="上传新文件"
)

# 将整个本地目录上传到仓库子目录
upload_folder(
    folder_path="./checkpoints",
    path_in_repo="models/checkpoints",
    repo_id="username/my-model",
    commit_message="更新模型文件"
)
```

#### 批量上传（使用CLI）

对于目录批量上传，建议使用CLI命令：

```python
import subprocess

# 通过SDK调用CLI命令进行批量上传
result = subprocess.run([
    "atomgit", "upload", "./model-directory", 
    "--repo-id", "username/repo-name",
    "--message", "上传完整模型"
], capture_output=True, text=True)

if result.returncode == 0:
    print("上传成功")
else:
    print(f"上传失败: {result.stderr}")
```

### 4. 仓库管理

#### 创建新仓库

```python
from atomgit_hub import create_repository

# 创建私有仓库
repo_url = create_repository(
    repo_id="username/private-repo",
    private=True,
    repo_type="model",  # 或 "dataset"
    exist_ok=True  # 如果已存在不报错
)
print(f"仓库创建成功: {repo_url}")
```

### 5. 认证管理

SDK与CLI共享相同的认证配置：

```python
# 方法1：使用CLI登录（推荐）
# 在终端运行：atomgit login

# 方法2：在代码中直接提供token
from atomgit_hub import snapshot_download

snapshot_download(
    "username/repo-name",
    local_dir="./model",
    token="your-access-token"  # 直接传入token
)
```

### 6. 错误处理

```python
from atomgit_hub import snapshot_download

try:
    path = snapshot_download(
        "username/repo-name",
        local_dir="./model"
    )
    print(f"下载成功: {path}")
except AtomGitAuthenticationError:
    print("认证失败，请先使用 'atomgit login' 登录")
except AtomGitRepositoryNotFoundError:
    print("仓库不存在，请检查仓库名称")
except AtomGitNetworkError as error:
    print(f"网络失败，可重试: {error}")
```

SDK 还导出 `AtomGitRepositoryExistsError`、`AtomGitRevisionNotFoundError`、
`AtomGitTimeoutError`、`AtomGitUnsupportedError` 和基类 `AtomGitError`。转换后的
异常保留脱敏的原始 cause，便于日志和程序化处理。

### 7. 完整示例

```python
from atomgit_hub import (
    snapshot_download, 
    upload_folder, 
    create_repository
)

def download_and_modify_model():
    """下载模型，修改后重新上传的完整示例"""
    
    # 1. 下载模型
    print("正在下载模型...")
    model_path = snapshot_download(
        "source-user/original-model",
        local_dir="./downloaded-model"
    )
    
    # 2. 创建新仓库
    print("创建新仓库...")
    create_repository(
        repo_id="my-user/modified-model",
        repo_type="model",
        private=True,
        exist_ok=True
    )
    
    # 3. 修改模型文件（示例）
    import os
    readme_path = os.path.join(model_path, "README.md")
    with open(readme_path, "a") as f:
        f.write("\n\n## 修改说明\n\n这是基于原模型的修改版本。")
    
    # 4. 上传修改后的目录
    print("上传修改后的文件...")
    upload_folder(
        folder_path=model_path,
        path_in_repo="./",
        repo_id="my-user/modified-model",
        commit_message="更新README文档"
    )
    
    print("完成！")

# 运行示例
if __name__ == "__main__":
    download_and_modify_model()
```

## 配置文件

配置文件保存在 `~/.atomgit/config.json`，包含用户认证信息和其他设置。Git
集成还会使用 `~/.atomgit/git-helper-state.json` 保存登录前两个 AtomGit 域名的
helper 配置；该状态文件不会写入本次登录 token，并使用 `0600` 权限。既有
helper 值会按原样保存，因此不应在 Git helper 命令中内嵌秘密。

## API端点配置

工具已预配置为连接AtomGit平台API端点：
- **API端点**：`https://hub.atomgit.com`
- **环境变量**：`HF_ENDPOINT=https://hub.atomgit.com`

此配置在程序启动时自动设置，用户无需手动配置。

## Git集成功能详解

### 自动配置

当你使用 `atomgit login` 登录成功后，工具会自动配置Git凭证，让你可以直接使用标准Git命令操作AtomGit仓库。

### 支持的Git操作

登录后，你可以直接使用以下Git命令，无需手动输入token：

```bash
# 克隆仓库（支持两种域名格式）
git clone https://atomgit.com/username/repo-name.git
git clone https://hub.atomgit.com/username/repo-name.git

# 推送代码
git push origin main

# 拉取更新
git pull origin main

# 添加远程仓库
git remote add origin https://atomgit.com/username/repo-name.git
```

### 安全性

- 凭证配置仅对 `atomgit.com` 和 `hub.atomgit.com` 域名生效
- token 安全存储在本地配置文件中
- 登录期间会重置这两个域名继承的 helper 链，避免 token 被系统通用 helper
  额外保存
- 不影响其他 Git 仓库的认证配置
- 登录前已有的 AtomGit 域名 helper 会按原顺序备份，并在 `atomgit logout`
  时恢复
- 如果恢复 Git 配置失败，logout 会以非零状态退出；修复 Git 配置后再次运行
  `atomgit logout` 会重试残留状态，即使 token 已在首次执行时清除

### 注意事项

- 支持的URL格式：`https://atomgit.com/...` 或 `https://hub.atomgit.com/...`
- 如果Git命令仍需要输入密码，请重新登录：`atomgit logout` 然后 `atomgit login`

## 错误处理

- 如果遇到网络错误，工具会自动重试
- 上传大文件时会显示进度条
- **上传失败语义化提示**：CLI 会把异常归类为「认证失败 / 仓库不存在 / 受限仓库 / 仓库已禁用 / 分支不存在 / 请求参数错误 / 请求超时 / 网络连接失败 / 未知错误」并附可执行建议
- 所有操作都有详细的错误信息提示

## 支持的文件类型

- 支持所有文件类型的上传和下载
- 自动处理目录结构
- 支持大文件传输

## 开发

### 项目结构

```
atomgit/
├── AGENTS.md           # 仓库级 AI 开发指令
├── .ai/                # AI 开发、测试、评审与任务规范
├── docs/               # 架构、开发、测试和发布文档
├── __init__.py          # 包初始化，导出SDK接口
├── __main__.py          # 主入口
├── cli.py               # CLI命令定义
├── api.py               # Hugging Face Hub API客户端
├── config.py            # 配置管理
├── runtime.py           # 共享HF端点和缓存策略
├── exceptions.py        # SDK异常类型
├── utils.py             # 工具函数（路径/忽略模式解析等）
├── atomgit_hub.py       # Python SDK接口
├── requirements.txt     # 依赖包
├── setup.py             # 包安装配置
├── deploy.sh            # 构建/安装/发布脚本
├── tests/               # 集成测试（upload 各能力）
└── README.md            # 说明文档
```

### 本地开发

```bash
# 克隆项目
git clone https://github.com/JoyJeeo/atomgit_cli.git
cd atomgit_cli

# 激活项目约定环境
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate atomgit_cli

# 安装依赖
python -m pip install -r requirements.txt

# 开发模式安装
python -m pip install -e .

# 测试CLI功能
atomgit --help

# 测试SDK功能
python -c "from atomgit_hub import snapshot_download; print('SDK导入成功')"

# 运行集成测试（需在 atomgit_cli conda 环境下）
python tests/test_upload_progress.py        # 进度条
python tests/test_upload_path_in_repo.py    # 仓库内路径
python tests/test_upload_repo_type.py       # 仓库类型
python tests/test_revision_rejection.py      # 非 main revision 拒绝
python tests/test_upload_ignore.py          # 忽略模式
python tests/test_upload_resumable.py       # 断点续传
python tests/test_upload_file_no_copy.py    # 单文件无拷贝
python tests/test_upload_error_classify.py  # 错误分类
python tests/test_upload_error_handling.py  # 错误处理集成
python tests/test_git_credentials_isolation.py  # Git helper 隔离与恢复
```

现有自执行脚本由隔离 pytest 矩阵统一收集。安装开发依赖后运行
`python -m pytest`；完整说明见 [docs/testing.md](docs/testing.md)。

## Python版本兼容性

`setup.py` 声明支持 Python 3.8+，列出的目标版本包括：

- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13

当前 wheel 已在项目 Python 3.10 conda 环境中通过自动化隔离安装和入口冒烟。
仓库尚无覆盖 Python 3.8–3.13 的完整 CI/conda 版本矩阵，因此这些版本除当前
环境外仍属于打包兼容声明，而不是逐版本运行证据。

## 项目文档

文档入口见 [docs/README.md](docs/README.md)，包括当前架构、开发流程、测试规范、
`yuto` 分支关系和独立发布目标。

## 许可证

本项目由 JoyJeeo 以 [Apache License 2.0](LICENSE) 授权。

## 贡献

欢迎提交Issue和Pull Request！

### 贡献指南

在贡献代码时，请确保：

1. 代码兼容Python 3.8+
2. 运行兼容性测试
3. 更新相关文档

## 联系我们

- 邮箱：JoyJeeo@163.com
- 项目地址：https://github.com/JoyJeeo/atomgit_cli
- 问题报告：https://github.com/JoyJeeo/atomgit_cli/issues
