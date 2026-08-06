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
| `atomgit download-file` | 下载仓库中的单个文件 | 公开仓库可匿名 |
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

导入时只设置这些进程环境变量，不创建缓存目录；真正使用 HF 缓存时由依赖按需
创建。HF 进度条和 `DEFAULT_REQUEST_TIMEOUT` 也是进程级全局状态；CLI 与 SDK
上传会在成功和失败路径恢复调用前的状态。

## 5. 配置和登录

`Config` 在首次读取时才加载 `config.json`；导入和不存在配置时的只读访问不会
创建 `~/.atomgit/`。写入使用同目录 0600 临时文件并原子替换，目录权限为 0700。
token 和登录 API 已验证的非敏感 username 以 JSON 保存；公开
`get_credentials()` 仍只返回 token，CLI 和 SDK 通过同一个全局配置实例读取。

登录流程：

```text
atomgit login
  -> api.login(token)
  -> GET https://atomgit.com/api/v5/user
  -> config.set_credentials(token, username)
  -> setup_git_credentials(token)
  -> 写入 ~/.atomgit/git-credential-atomgit
  -> 备份两个 AtomGit host 原有的全局 Git helper 配置
  -> 用空 helper + AtomGit helper 建立域名专属隔离链
```

风险：

- 配置目录和 token 文件分别强制为 `0700` 和 `0600`（Windows 权限语义由系统决定）；
- Git helper 修改用户全局 Git 配置；原值保存在权限受限且不写入本次登录
  token 的 `git-helper-state.json`，logout 时事务性恢复；
- 生成的 helper 只读本地已验证 username/token，不执行网络身份查询；旧配置需
  重新 login 才能补齐 username；
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
- 非 `main` revision 已根据远程证据明确拒绝，避免静默写入默认分支。

resumable 通过 `HfApi(token=...)` 认证。私有 model 和 dataset 均已使用真实
399,300,506 字节文件验证中断、恢复和最终 SHA-256；dataset 在保留用户侧业务
类型的同时使用 AtomGit 可用的共享 model 传输路由。

## 7. 下载

整仓下载：

```text
atomgit download REPO
  -> validate_repo_name
  -> api.download_repo
  -> _normalize_repo_id
  -> _atomgit_list_repo_files（自动探测或使用 --repo-type）
  -> 预先校验全部本地目标路径
  -> 逐文件 resolve 下载
```

CLI 不强制登录；有本地 AtomGit token 时会用于列表和文件请求，没有时通过
`token=False` 显式禁用 HF SDK 的环境凭据并尝试匿名下载，避免把其他平台的
Token 发送到 AtomGit。
默认策略是跳过已经存在的目标文件且不校验其内容；`--force` 才重新下载并原子
替换。标准 URL 与非 ASCII raw UTF-8 回退都在目标目录创建唯一临时文件，完整
成功后替换目标，普通异常和重试失败会清理临时文件并保留原目标。

整仓和 CLI API 单文件下载在响应体不完整、读取超时或连接中断时从头自动
重试一次；SDK 的 snapshot/file 下载和 `load_dataset` 则由 HF 缓存保留可恢复
状态。认证、权限、仓库、文件或 revision 不存在等确定性错误不会重试。
重试仍失败时，CLI 和 SDK 只返回脱敏后的错误类别，不包含远端 URL、签名
URL 或其查询参数。

`atomgit download-file` 调用 `api.download_file`；它与整仓下载一样先列文件、
校验安全目标路径，再直连 resolve。SDK `download_file` 使用 HF
`hf_hub_download`，因此缓存路径和异常类型与 CLI API 不同。

## 8. Python SDK

`atomgit_hub.py` 导出：

- `snapshot_download`
- `hub_download_url`
- `download_file`
- `upload_folder`
- `create_repository`
- `load_dataset`

当前契约：

- 非根 `path_in_repo` 的临时目录覆盖完整 HF 调用，并在所有路径清理；
- `repo_type`、`revision`、`commit_description`、`ignore_patterns` 均有严格
  参数契约；dataset 传输使用 AtomGit 兼容的 model 路由；
- upload timeout 在成功和失败后恢复；
- 旧 snapshot 兼容形参仍保留，但不再传给 HF 1.1.7；非默认使用会明确警告；
- SDK 使用公开的 `AtomGitError` 层次区分认证、仓库、revision、网络、超时和
  不支持语义，并保留脱敏后的原始 cause。

## 9. Repo ID 转换

所有 CLI API 与 SDK 边界共享 `utils.normalize_repo_id`。三层及以上 ID 会把
前两个片段合并：

```text
org/namespace/repo -> org-namespace/repo
```

ID 必须至少包含 `owner/repository` 两段；每段只接受 ASCII 字母、数字、`_`、
`-`、`.`，但拒绝空段、`.`/`..` 点段、反斜杠、控制字符和所有 `%` 编码。
百分号编码不会先解码，以免验证与实际请求对同一输入产生不同解释。

create、文件/目录 upload、snapshot/file download、URL 构造和 dataset loading
均使用同一映射。公开示例的匿名只读探测已验证转换后 URL。2026-08-04 的受控
写入验收确认客户端会把多层 ID 转成预期物理 ID，并在测试账号不具备对应
`owner-namespace` 权限时对 create/upload 返回非零且不留下仓库；成功写入仍要求
账号属于转换后的物理命名空间。

CLI 直连 resolve 下载在目标目录使用唯一临时文件，完整成功后才原子替换目标；
标准和 raw UTF-8 传输失败都会清理本次临时文件并保留原目标。固定名
`<destination>.part` 可能是仓库中的真实文件，因此不会被当作残片删除。

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
