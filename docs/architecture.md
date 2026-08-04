# AtomGit CLI 当前架构

> 本文描述 `yuto` 分支版本 1.0.5+yuto.1 的当前源码事实。已知缺陷会明确标注，不能把
> 设计目标当作已验证能力。

## 1. 项目形态

AtomGit CLI 同时提供命令行和 Python SDK：

```text
安装入口
  |
  +-- atomgit 命令 ----------> cli.py ----------> api.py
  |                               |                  |
  |                               v                  v
  |                          config.py/utils.py  huggingface_hub
  |
  +-- python -m atomgit -----> __main__.py -----> cli.py
  |
  +-- import atomgit_hub ----> atomgit_hub.py ---> huggingface_hub/datasets
```

CLI 和 SDK 共享本地凭证，但不是同一业务实现：

- CLI：`cli.py -> api.py`；
- SDK：直接调用 `atomgit_hub.py` 中的函数。

因此两侧上传、下载、repo ID 转换和异常行为可能发生漂移。

## 2. 目录与模块

```text
atomgit_cli/
├── AGENTS.md             # 仓库级 AI 指令
├── .ai/                  # AI 开发、测试、评审和任务规范
├── docs/                 # 面向维护者和用户的设计文档
├── __init__.py           # 包元数据和公开导出
├── __main__.py           # python -m atomgit 入口
├── cli.py                # Click 命令树和用户交互
├── api.py                # CLI 使用的 AtomGit/HF 包装层
├── atomgit_hub.py        # 对外 Python SDK
├── config.py             # ~/.atomgit/config.json 配置
├── runtime.py            # 共享 HF endpoint/XET/cache 运行时策略
├── exceptions.py         # 稳定 SDK 异常层次
├── utils.py              # 校验、格式化和 Git helper
├── tests/                # pytest 隔离矩阵与兼容的自执行回归脚本
├── setup.py              # Python 包与 console script
├── requirements.txt      # 运行依赖
└── deploy.sh             # 本地构建、安装和 PyPI 发布脚本
```

仓库当前采用根目录包映射，不是 `src/` 布局。除非单独设计并验证打包迁移，不应
为了目录美观创建空的 `src/` 模块树。

## 3. 入口和命令树

`setup.py` 注册：

```text
atomgit = atomgit.cli:cli
```

实际命令：

| 命令 | 作用 | 登录要求 |
|---|---|---|
| `atomgit login` | 验证并保存 token，配置 Git helper | 不适用 |
| `atomgit logout` | 清除 token 和 Git helper | 否 |
| `atomgit whoami` | 查询当前用户 | 是 |
| `atomgit repo create` | 创建 model/dataset 仓库 | 是 |
| `atomgit upload` | 上传单文件或目录 | 是 |
| `atomgit download` | 下载整个仓库 | 公开仓库可匿名 |
| `atomgit config-show` | 显示登录和 Git 集成状态 | 否 |

注意：命令名是 `config-show`，不是旧文档中的 `config`。

## 4. 导入时全局配置

`cli.py`、`api.py` 和 `atomgit_hub.py` 都会在导入 HF 前调用共享的
`runtime.configure_hf_environment()`，统一设置：

```text
HF_ENDPOINT=https://hub.atomgit.com
HF_HUB_DISABLE_XET=1
HF_HOME=~/.cache/atomgit
```

这些仍是导入时副作用，但定义和缓存创建策略只有一处且可重复调用。HF 进度条和
`DEFAULT_REQUEST_TIMEOUT` 也是进程级全局状态；CLI 与 SDK 上传会在成功和失败
路径恢复调用前的状态。

## 5. 配置和登录

`Config` 在导入时创建 `~/.atomgit/` 并读取 `config.json`。token 以 JSON 保存，
CLI 和 SDK 通过同一个全局配置实例读取。

登录流程：

```text
atomgit login
  -> api.login(token)
  -> GET https://atomgit.com/api/v5/user
  -> config.set_credentials(token)
  -> setup_git_credentials(token)
  -> 写入 ~/.atomgit/git-credential-atomgit
  -> 备份两个 AtomGit host 原有的全局 Git helper 配置
  -> 用空 helper + AtomGit helper 建立域名专属隔离链
```

风险：

- 配置目录和 token 文件分别强制为 `0700` 和 `0600`（Windows 权限语义由系统决定）；
- Git helper 修改用户全局 Git 配置；原值保存在权限受限且不写入本次登录
  token 的 `git-helper-state.json`，logout 时事务性恢复；
- 登录 API 和生成的 helper 使用的 Authorization 形式不同；
- 多处异常被吞掉，诊断信息有限。

## 6. 上传

完整参数和分支见 [upload_command_analysis.md](upload_command_analysis.md)。

简化调用流：

```text
atomgit upload PATH
  -> 登录/repo ID/path/path-in-repo 校验
  -> 文件
       -> 默认 hf upload_file（直接读取原文件）
       -> 传 ignore 或旧 HF 无 upload_file 时：临时目录 + upload_folder
  -> 目录
       -> 普通模式：upload_folder
       -> resumable：HfApi.upload_large_folder
```

已知问题：

- 上传、下载和建仓共享多层 repo ID 转换；远程写入仍需受控验收；
- 单文件 fallback 使用唯一系统临时目录，并在成功或失败后自动清理；
- `revision` 参数已透传，但 AtomGit 远端 `dev` 分支行为尚未验证成功。

resumable 通过 `HfApi(token=...)` 认证，已使用真实 404 MB 文件验证中断、恢复和
最终 SHA-256。dataset 上传在保留业务类型的同时使用 AtomGit 可用的共享 model
传输路由。

## 7. 下载

整仓下载：

```text
atomgit download REPO
  -> validate_repo_name
  -> api.download_repo
  -> _normalize_repo_id
  -> snapshot_download(local_dir, force_download, token-or-none)
```

CLI 不强制登录；有本地 token 时会直接传入，没有时尝试匿名下载。

整仓、单文件和 `load_dataset` 使用的数据集快照下载共享同一恢复策略：遇到响应体
不完整、读取超时或连接中断时自动重试一次，以便复用 HF 本地缓存中的部分下载；
认证、权限、仓库、文件或 revision 不存在等确定性错误不会重试。重试仍失败时，
CLI 和 SDK 只返回脱敏后的错误类别，不包含远端 URL、签名 URL 或其查询参数。

`api.download_file` 不对 CLI 暴露，它先匿名调用 `hf_hub_download`，只有错误文本
包含特定 403 特征时才回退到保存的 token。SDK 的 `download_file` 则直接使用显式
或保存的 token，两者行为不完全一致。

## 8. Python SDK

`atomgit_hub.py` 导出：

- `snapshot_download`
- `hub_download_url`
- `download_file`
- `upload_folder`
- `create_repository`
- `load_dataset`

已知问题：

- 非根 `path_in_repo` 上传时，临时目录在 HF 调用前已经退出并删除；
- `repo_type`、`revision`、`commit_description`、`ignore_patterns` 形参没有传给
  HF `upload_folder`；
- 保存的 timeout 没有恢复；
- 旧 snapshot 兼容形参仍保留，但不再传给 HF 1.1.7；非默认使用会明确警告；
- SDK 使用公开的 `AtomGitError` 层次区分认证、仓库、revision、网络、超时和
  不支持语义，并保留脱敏后的原始 cause。

## 9. Repo ID 转换

所有 CLI API 与 SDK 边界共享 `utils.normalize_repo_id`。三层及以上 ID 会把
前两个片段合并：

```text
org/namespace/repo -> org-namespace/repo
```

create、文件/目录 upload、snapshot/file download、URL 构造和 dataset loading
均使用同一映射。公开示例的匿名只读探测已验证转换后 URL；创建和上传仍需显式
授权的远程写验收，离线一致性不能替代远程证据。

## 10. 测试和打包

- 自执行回归脚本由 pytest 隔离矩阵逐个在子进程和临时 HOME 中运行；
- 它们主要验证离线契约，不替代需要显式授权的远程行为验收；
- `requirements.txt` 锁定 `huggingface-hub==1.1.7` 和 `datasets==4.4.1`；
- 包名和版本为 `atomgit==1.0.5+yuto.1`；
- `py_modules=['atomgit_hub']` 同时保留顶层兼容导入；
- `deploy.sh twine` 是真实 PyPI 写操作，不能作为日常验证运行。

详细开发、测试和发布规则见：

- [development.md](development.md)
- [testing.md](testing.md)
- [release.md](release.md)
