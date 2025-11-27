# AtomGit CLI & SDK

基于Transformers和Hugging Face Hub的AtomGit平台模型文件上传下载CLI工具和Python SDK

## 简介

AtomGit 是一个完整的工具包，提供命令行工具（CLI）和Python SDK两种方式与AtomGit平台交互，支持模型和数据集的上传、下载等操作。类似于huggingface_hub，用户只需安装一个`atomgit`包即可同时使用CLI命令和Python编程接口。工具基于Transformers和Hugging Face Hub SDK开发，并配置为连接AtomGit API端点。

## 功能特性

### CLI功能
- 🔐 用户认证和登录管理
- 🔗 **Git集成**：自动配置Git凭证，支持标准Git命令
- 📁 支持模型和数据集仓库创建
- ⬆️ 文件和目录批量上传
- ⬇️ 仓库内容下载
- 🎨 彩色终端输出
- 📊 上传下载进度显示
- 🔧 配置文件管理

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
git clone https://atomgit.com/gitcode-ai/atomgit_cli.git
cd atomgit_cli
pip install -e .
```

### 使用pip安装（如果已发布）

```bash
pip install atomgit
```

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

#### 上传模型

```bash
atomgit upload ./your-model-dir --repo-id your-username/your-model-name
```

#### 上传数据集

```bash
atomgit upload ./your-dataset-dir --repo-id your-username/your-dataset-name
```

#### 上传单个文件

```bash
atomgit upload ./model.bin --repo-id your-username/your-model-name
```

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
from atomgit_hub import snapshot_download

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

#### 上传单个文件

```python
from atomgit_hub import upload_folder

# 基本上传
upload_folder(
    folder_path="./local-file.txt",
    path_in_repo="remote-file.txt",
    repo_id="username/repo-name",
    commit_message="上传新文件"
)

# 上传到子目录
upload_folder(
    folder_path="./model.bin",
    path_in_repo="models/pytorch_model.bin",
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

# 创建公开仓库
repo_url = create_repository(
    repo_id="username/new-repo",
    private=False,
    repo_type="model"  # 或 "dataset"
)
print(f"仓库创建成功: {repo_url}")

# 创建私有仓库
create_repository(
    repo_id="username/private-repo",
    private=True,
    exist_ok=True  # 如果已存在不报错
)
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
except Exception as e:
    if "401" in str(e) or "403" in str(e):
        print("认证失败，请先使用 'atomgit login' 登录")
    elif "404" in str(e):
        print("仓库不存在，请检查仓库名称")
    else:
        print(f"下载失败: {e}")
```

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
        exist_ok=True
    )
    
    # 3. 修改模型文件（示例）
    import os
    readme_path = os.path.join(model_path, "README.md")
    with open(readme_path, "a") as f:
        f.write("\n\n## 修改说明\n\n这是基于原模型的修改版本。")
    
    # 4. 上传修改后的文件
    print("上传修改后的文件...")
    upload_folder(
        folder_path=readme_path,
        path_in_repo="README.md",
        repo_id="my-user/modified-model",
        commit_message="更新README文档"
    )
    
    print("完成！")

# 运行示例
if __name__ == "__main__":
    download_and_modify_model()
```

## 配置文件

配置文件保存在 `~/.atomgit/config.json`，包含用户认证信息和其他设置。

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
- 不影响其他Git仓库的认证配置
- `atomgit logout` 时自动清除凭证配置

### 注意事项

- 支持的URL格式：`https://atomgit.com/...` 或 `https://hub.atomgit.com/...`
- 如果Git命令仍需要输入密码，请重新登录：`atomgit logout` 然后 `atomgit login`

## 错误处理

- 如果遇到网络错误，工具会自动重试
- 上传大文件时会显示进度条
- 所有操作都有详细的错误信息提示

## 支持的文件类型

- 支持所有文件类型的上传和下载
- 自动处理目录结构
- 支持大文件传输

## 开发

### 项目结构

```
atomgit/
├── __init__.py          # 包初始化，导出SDK接口
├── __main__.py          # 主入口
├── cli.py               # CLI命令定义
├── api.py               # Hugging Face Hub API客户端
├── config.py            # 配置管理
├── utils.py             # 工具函数
├── atomgit_hub.py       # Python SDK接口
├── requirements.txt     # 依赖包
├── setup.py             # 包安装配置
└── README.md           # 说明文档
```

### 本地开发

```bash
# 克隆项目
git clone https://atomgit.com/gitcode-ai/atomgit_cli.git
cd atomgit_cli

# 安装依赖
pip install -r requirements.txt

# 开发模式安装
pip install -e .

# 测试CLI功能
atomgit --help

# 测试SDK功能
python -c "from atomgit_hub import snapshot_download; print('SDK导入成功')"

# 运行测试
python -m pytest tests/
```

## Python版本兼容性

本项目支持Python 3.8+版本，包括：

- ✅ Python 3.8
- ✅ Python 3.9  
- ✅ Python 3.10
- ✅ Python 3.11
- ✅ Python 3.12
- ✅ Python 3.13

### 兼容性测试

运行兼容性测试：

```bash
python test_compatibility.py
```

详细兼容性信息请参考 [PYTHON_COMPATIBILITY.md](PYTHON_COMPATIBILITY.md)

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

### 贡献指南

在贡献代码时，请确保：

1. 代码兼容Python 3.8+
2. 运行兼容性测试
3. 更新相关文档

## 联系我们

- 邮箱：support@atomgit.com
- 项目地址：https://atomgit.com/gitcode-ai/atomgit_cli
- 问题报告：https://atomgit.com/gitcode-ai/atomgit_cli/issues 