# AtomGit CLI 代码仓运行逻辑梳理

> 本文档基于 `yuto` 分支当前代码（版本 1.0.5）梳理，描述项目整体结构、模块职责、运行流程与关键设计点。
> 运行环境约定：所有指令需在 conda 环境 `atomgit_cli` 下执行（`conda run -n atomgit_cli <command>`）。

---

## 一、项目定位

AtomGit CLI 是一个**双形态工具包**：既是一个命令行工具（CLI），也是一个 Python SDK。

- 底层完全基于 **Hugging Face Hub SDK**（`huggingface_hub`）实现，通过把 HF 的 API 端点重定向到 AtomGit，复用 HF Hub 的下载/上传/建仓能力。
- 用户安装一个 `atomgit` 包即可同时获得 CLI 命令与 Python 编程接口。
- 主要支持**模型（model）**与**数据集（dataset）**两类仓库的上传、下载、创建等操作。

对外端点：
- Hub API（SDK 走的端点）：`https://hub.atomgit.com`
- 用户/账号 API（登录鉴权）：`https://atomgit.com/api/v5/user`

---

## 二、目录结构

```
atomgit_cli/
├── __init__.py        # 包入口，导出 config/api/cli 及 SDK 函数
├── __main__.py        # python -m atomgit 入口
├── config.py          # 配置与凭证管理（~/.atomgit/config.json）
├── api.py             # API 客户端（CLI 调用层），封装 HF Hub
├── atomgit_hub.py     # Python SDK（类 huggingface_hub 接口）
├── cli.py             # Click 命令行定义（login/upload/download…）
├── utils.py           # 工具函数 + Git 凭证助手生成
├── setup.py           # 打包配置，注册 console_script `atomgit`
├── requirements.txt   # 依赖锁定
├── deploy.sh          # 构建/安装/发布到 PyPI 的脚本
├── MANIFEST.in
└── README.md
```

入口点（`setup.py` 的 `entry_points`）：
```
atomgit = atomgit.cli:cli
```
即安装后可直接使用 `atomgit <command>`，等价于 `python -m atomgit`。

---

## 三、模块职责与关键逻辑

### 1. `config.py` —— 配置与凭证管理

- 配置目录：`~/.atomgit/`
- 配置文件：`~/.atomgit/config.json`
- 核心是全局单例 `config = Config()`。
- 维护 `token`（访问令牌），并提供：
  - `set_credentials(token)` / `get_credentials()` / `clear_credentials()`
  - `is_logged_in()` 判断登录状态
  - `set_value/get_value` 通用键值存取
- CLI 与 SDK 共享同一份配置文件，因此「命令行登录后，SDK 也能直接读到 token」。

### 2. `api.py` —— CLI 使用的 API 客户端

- 全局单例 `api = HuggingFaceAPI()`，被 `cli.py` 调用。
- 模块加载时即设置 HF 环境变量，把 HF 端点指向 AtomGit：
  - `HF_ENDPOINT = https://hub.atomgit.com`
  - `HF_HUB_DISABLE_XET = 1`（禁用 Xet 协议，避免 `xet-write-token` 请求）
  - `HF_HOME = ~/.cache/atomgit`（缓存目录）
- 关键方法：
  - `login(token)`：调用 AtomGit `api/v5/user` 验证 token，成功后写入 `config`。
  - `_get_login_user_by_token(token)`：用 `urllib` 直接请求 AtomGit 账号 API，返回 `{login, name, email}`。
  - `create_repo(repo_name, repo_type, private)`：调用 HF `create_repo`。
  - `upload_folder(...)` / `upload_directory(...)`：调用 HF `upload_folder`，通过 monkey-patch `hf_constants.DEFAULT_REQUEST_TIMEOUT` 临时调大超时。
  - `download_repo(repo_id, local_path, force_download)`：调用 HF `snapshot_download`，公开仓库可不带 token。
  - `download_file(repo_id, filename, ...)`：调用 HF `hf_hub_download`；公开下载失败且为 403 时，回退用 token 重试。
- **`_normalize_repo_id(repo_id)`**：核心转换函数。
  - 当 repo_id 为三层格式 `A/B/C…`（如 `hf_mirrors/Qwen/Qwen2.5-Coder-0.5B-Instruct`）时，把第一个 `/` 替换为 `-`，得到 `A-B/C…`。
  - 二层或单层格式原样返回。
  - 这是为了适配 AtomGit 的命名空间到 HF `repo_id` 的映射规则。

### 3. `cli.py` —— 命令行接口（基于 Click）

模块加载时同样设置 HF 环境变量（与 `api.py` 一致，确保即使直接 import cli 也生效）。

命令树：

| 命令 | 说明 | 是否需要登录 |
|------|------|------------|
| `atomgit login [--token]` | 登录并保存 token；同时配置 Git 凭证助手 | — |
| `atomgit logout` | 清除凭证与 Git 凭证配置 | — |
| `atomgit whoami` | 查看当前登录用户 | 是 |
| `atomgit repo create <name> --type {model,dataset} [--private]` | 创建仓库 | 是 |
| `atomgit upload <path> --repo-id <id> [-m msg] [-t timeout]` | 上传文件/目录 | 是 |
| `atomgit download <repo_id> [-d dir] [--force]` | 下载仓库（公开仓库无需登录） | 否（私有需要） |
| `atomgit config` | 显示配置/登录状态 | — |

`upload` 流程：
- 文件 → 走 `api.upload_folder`（先复制到 `.tmp_upload` 临时目录再上传，上传后清理）。
- 目录 → 走 `api.upload_directory`（直接上传原目录）。
- 支持自定义 `--timeout`（默认 300 秒，大文件建议调大）。

`download` 流程：
- 默认下载到 `./<repo_name 末段>`，可用 `-d` 指定目录。
- 目录已存在且非强制时，启用断点续传模式；`--force` 则强制重下。
- 未登录时自动尝试公开仓库下载。

### 4. `atomgit_hub.py` —— Python SDK（对外编程接口）

提供类 `huggingface_hub` 的函数式 API，供 `from atomgit_hub import ...` 使用：

| 函数 | 作用 |
|------|------|
| `snapshot_download(repo_id, ...)` | 下载整个仓库快照 |
| `hub_download_url(repo_id, filename, ...)` | 拼接文件直链 URL |
| `download_file(repo_id, filename, ...)` | 下载单个文件 |
| `upload_folder(folder_path, repo_id, ...)` | 上传文件夹 |
| `create_repository(repo_id, ...)` | 创建仓库 |
| `load_dataset(path, ...)` | 加载数据集（可选，依赖 `datasets` 库） |

设计要点：
- 同样设置 HF 环境变量、同样的 `_normalize_repo_id` 三层格式转换。
- token 缺省时通过 `_get_token()` 从 `config` 读取 —— 与 CLI 共享凭证。
- `DATASET_SUPPORT`：若未安装 `datasets`，`load_dataset` 会抛 `ImportError` 提示安装。
- 对 401/403/404 等错误做了语义化封装（认证失败 / 仓库不存在 / 文件不存在）。
- `upload_folder` 通过 monkey-patch `hf_constants.DEFAULT_REQUEST_TIMEOUT` 控制 HF 请求超时；`path_in_repo` 非根目录时，会先 `copytree` 到临时目录重组结构再上传。

### 5. `utils.py` —— 工具函数与 Git 集成

- 彩色输出：`print_success/print_error/print_warning/print_info`（基于 colorama）。
- 校验：`validate_repo_name`（支持多层命名空间，如 `hf_mirrors/Qwen/Qwen3-Reranker-0.6B`，允许 URL 编码 `%`）、`validate_repo_type`。
- 文件统计：`get_file_size` / `format_file_size` / `get_directory_size` / `count_files_in_directory`。
- 交互：`confirm_action`。
- 路径：`is_valid_path` / `ensure_directory` / `get_relative_path`。
- **Git 凭证助手（关键特性）**：
  - `setup_git_credentials(token)`：在 `~/.atomgit/` 下生成可执行脚本 `git-credential-atomgit`，并通过 `git config --global credential.https://{host}.helper` 为 `atomgit.com` 与 `hub.atomgit.com` 两个域名注册。
  - 该脚本在 git 需要 `get` 凭证时，读取 `~/.atomgit/config.json` 中的 token，并调用 `atomgit.com/api/v5/user` 获取真实用户名，输出 `username/password` 给 git。
  - `clear_git_credentials()`：移除全局 git 配置并删除脚本文件。
  - `check_git_available()` / `get_git_user_info()`：检测 git 可用性与读取全局 user.name/email。

效果：`atomgit login` 之后，可直接用原生 `git clone/push` 访问 AtomGit 仓库，无需每次输密码。

---

## 四、核心运行流程

### 登录流程
```
atomgit login --token <TOKEN>
  └─ cli.login
       ├─ api.login(token)
       │    ├─ _get_login_user_by_token → GET atomgit.com/api/v5/user  (鉴权)
       │    └─ config.set_credentials(token) → 写入 ~/.atomgit/config.json
       └─ setup_git_credentials(token)
            ├─ 生成 ~/.atomgit/git-credential-atomgit
            └─ git config --global credential.https://{atomgit.com,hub.atomgit.com}.helper
```

### 上传流程
```
atomgit upload <path> --repo-id <id> -m <msg> -t <timeout>
  └─ 校验登录 + repo_id 格式
  ├─ 文件 → api.upload_folder (经 .tmp_upload 临时目录)
  └─ 目录 → api.upload_directory (直接上传)
       └─ monkey-patch hf_constants.DEFAULT_REQUEST_TIMEOUT
       └─ huggingface_hub.upload_folder(repo_id, folder_path, token, commit_message)
            (repo_id 经 _normalize_repo_id 三层格式转换)
```

### 下载流程
```
atomgit download <repo_id> [-d dir] [--force]
  └─ 校验 repo_id（无需登录）
  └─ api.download_repo
       ├─ _normalize_repo_id(repo_id)
       └─ huggingface_hub.snapshot_download(repo_id, local_dir, force_download, token?)
            token 缺省 → 公开仓库直接下；私有仓库需已登录
```

单文件下载（SDK / api.download_file）：
```
hf_hub_download(...) 无 token 尝试
  └─ 403/FORBIDDEN → 回退带 token 重试（需已登录）
```

---

## 五、关键设计点

1. **复用 HF Hub，而非自建协议**：所有上传/下载/建仓都委托 `huggingface_hub`，仅通过环境变量改端点（`HF_ENDPOINT`）、禁用 Xet（`HF_HUB_DISABLE_XET=1`）、改缓存（`HF_HOME`）。三个模块（api/cli/atomgit_hub）各自独立设置一遍环境变量，保证单独导入任意模块都生效。

2. **三层命名空间映射**：AtomGit 支持 `org/namespace/repo` 形态，而 HF `repo_id` 是 `owner/name`。`_normalize_repo_id` 把首个 `/` 转成 `-`，使三层 ID 能被 HF SDK 正确识别。

3. **CLI 与 SDK 共享凭证**：两者都读 `~/.atomgit/config.json`，SDK 缺省 token 时自动回退到 `config.get_credentials()`。一次 `atomgit login`，两边通用。

4. **公开仓库免登录下载**：`download` 命令不强制登录；`download_file` 在无 token 公开下载失败且判定为认证问题时，再用已存 token 重试。

5. **Git 原生集成**：登录时自动注册 git credential helper，使 `git clone https://atomgit.com/...` 也能复用 token，降低使用门槛。

6. **超时可调**：上传支持 `--timeout`，内部对 HF 全局 `DEFAULT_REQUEST_TIMEOUT` 做 monkey-patch（注意：这是进程级全局修改，并发场景需谨慎）。

7. **可选数据集支持**：`load_dataset` 仅在安装了 `datasets` 时可用，否则提示安装，避免硬依赖。

---

## 六、依赖与发布

### 运行时依赖（requirements.txt）
- `click>=8.1.7`（CLI 框架）
- `requests>=2.31.0`
- `tqdm>=4.66.1`（进度条）
- `colorama>=0.4.6`（彩色输出）
- `tabulate>=0.9.0`
- `huggingface-hub==1.1.7`（核心，锁定版本）
- `datasets==4.4.1`（数据集，锁定版本）

### 打包（setup.py）
- 包名 `atomgit`，版本 1.0.5
- `entry_points` 注册 `atomgit=atomgit.cli:cli`
- `package_dir={'atomgit': '.'}`：把当前目录作为 `atomgit` 包
- `py_modules=['atomgit_hub']`：`atomgit_hub.py` 作为顶层模块可独立 import

### 发布（deploy.sh）
- `./deploy.sh build` —— `python -m build` 产出 dist
- `./deploy.sh install` —— 卸载旧版后 `pip install dist/*.whl`
- `./deploy.sh twine` —— 用 `twine` 上传 PyPI（需环境变量 `atomgitsdktoken`，以 `__token__` 用户上传）

---

## 七、本地开发运行约定（yuto 分支）

- **运行环境**：conda 环境 `atomgit_cli`，所有命令建议以 `conda run -n atomgit_cli <command>` 执行，避免与其它项目环境相互干扰。
- **开发安装**：在 `atomgit_cli` 环境下执行 `pip install -e .`（可编辑安装），即可使用 `atomgit` 命令与 `import atomgit_hub`。
- **当前分支模型**（详见 `docs/yuto_branch.md`）：
  - `yuto`：GitHub 主分支（本项目主开发线）
  - `main`：从 AtomGit 上游拉取的外部同步分支
  - 同步链路：AtomGit 上游 → `main` → `yuto`
