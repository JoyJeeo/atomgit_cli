# AtomGit CLI 当前架构

> 本文描述 `yuto` 分支版本 1.0.6 的当前源码事实。已知缺陷会明确标注，不能把
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
  |
  +-- Zsh Tab ---------------> 轻量 cli schema -> completion.py
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
├── cli_contracts.py      # CLI schema 与上传运行时共享的轻量常量
├── completion.py         # Zsh completion adapter 与受控安装/卸载
├── api.py                # CLI 使用的 AtomGit/HF 包装层
├── atomgit_hub.py        # 对外 Python SDK
├── config.py             # ~/.atomgit/config.json 配置
├── runtime.py            # 共享 HF endpoint/XET/cache 运行时策略
├── exceptions.py         # 稳定 SDK 异常层次
├── utils.py              # 校验、格式化和 Git helper
├── tests/                # pytest 隔离矩阵与兼容的自执行回归脚本
├── setup.py              # Python 包与 console script
├── requirements.txt      # 运行依赖
├── release.py            # Release 解析、校验、安装和 update 核心
└── deploy.sh             # 本地构建、安装和 checksum 脚本
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
| `atomgit repo list` | 列出当前用户可访问的仓库 | 是 |
| `atomgit repo visibility` | 修改并验证仓库公开/私有状态 | 是 |
| `atomgit repo delete` | 显式确认、永久删除并验证仓库不存在 | 是 |
| `atomgit repo branch create` | 显式创建并验证仓库分支 | 是 |
| `atomgit upload` | 上传单文件或目录 | 是 |
| `atomgit download` | 下载整个仓库 | 公开仓库可匿名 |
| `atomgit download-file` | 下载仓库中的单个文件 | 公开仓库可匿名 |
| `atomgit update` | 从已完成 GitHub Release 更新当前 Python | wheel 安装；源码安装拒绝 |
| `atomgit completion show zsh` | 输出 Zsh 补全 adapter | 否 |
| `atomgit completion install --shell zsh` | 安装并启用 Zsh 补全 | 否 |
| `atomgit completion uninstall --shell zsh` | 移除受控 Zsh 补全 | 否 |
| `atomgit config-show` | 显示登录和 Git 集成状态 | 否 |

注意：命令名是 `config-show`，不是旧文档中的 `config`。

Click 每次补全都会启动新的 `atomgit` 进程。`_ATOMGIT_COMPLETE` 存在时，包入口
只配置共享 HF 环境并加载轻量 CLI schema；`cli.py` 的 API 对象和工具函数按命令
执行惰性解析，因此补全不会导入 HF Hub、datasets、Torch、PyArrow 或 Pandas。
生成的 Zsh adapter 每次查询当前 Click 树，所以新增命令无需同步补全清单。

补全安装在 `~/.atomgit/completions/atomgit.zsh` 写入 `0600` adapter，并只在
`.zshrc` 中管理带边界标记的配置块；已有配置首次修改前备份。目录使用 `0700`，
符号链接、畸形标记、相对 `ZDOTDIR` 或读取后的并发修改会失败关闭；`.zshrc`
写入失败会回滚本次脚本和新建备份。官方安装器仅在 Zsh 下默认调用该能力，
`--no-completion` 可关闭；标准 pip 不运行非标准安装后钩子。

登录和 `whoami` 的远端失败采用固定、脱敏的类别提示：401、403、限流、服务端
故障、网络/超时和无效响应分别保留可执行的诊断；CLI 不会把所有失败都归因为
token 无效，也不会输出响应正文或底层异常详情。身份 JSON 最多接受 1 MiB，读取
上限加 1 字节后会在 UTF-8 解码和 JSON 解析前拒绝超限响应。

仓库列表使用 AtomGit V5 `GET /api/v5/user/repos`，凭据只通过
`PRIVATE-TOKEN` 请求头发送；响应经过大小限制和 JSON 集合校验后才交给 CLI。
可见性修改使用 `PATCH /api/v5/repos/:owner/:repo`，随后 GET 同一资源验证远端
状态。建仓通过已验证的 HF model 兼容路由先请求私有仓库，再对明确请求的公开
或私有状态执行上述收敛和验证，包括 `--exist-ok` 命中已有仓库的路径。任何转换
或验证失败都会返回失败且不自动删除，并提示远端状态可能未知，必须重新检查和
设置可见性。

可见性 PATCH 与分支创建 POST 若返回超时、连接错误或 5xx，会继续执行原有的
目标 GET，并只在读取状态匹配时恢复成功；4xx 属于确定拒绝，不执行恢复读取。
GET 不可用或读取状态不匹配时返回失败，并以脱敏信息说明写请求状态未知。
分支创建在 POST 前通过 V5 commit 读取把来源分支、标签或提交解析为不可变
commit ID，POST 后的分支读取必须同时匹配目标名称和该 commit ID；来源解析
失败时不发送写请求，同名但来源提交不同的分支不能恢复为成功。

仓库删除使用官方 V5 `DELETE /api/v5/repos/:owner/:repo`，不经过需要 repo type
的 HF 删除接口。CLI 要求 `--confirm` 与输入仓库 ID 完全一致，API 在 DELETE 前
GET 目标、在 DELETE 后再次 GET；只有后置请求返回 404 才成功。若 DELETE 响应
不确定，仍通过后置 GET 恢复结果；仓库仍存在或无法验证时返回失败，且错误输出
不包含 token。该能力不进入公开 Python SDK。

`HuggingFaceAPI.get_repo_info` 是保留的方法兼容面，不对应 CLI 命令。当前版本不
实现仓库详情读取；调用时固定返回 `None` 和脱敏的不支持提示，不读取凭据、不发
网络请求，也不会再返回容易被误认为已验证仓库信息的占位字典。需要现有仓库集合
时使用 `repo list`，仓库详情查询仍属于未实现能力。

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
创建 `~/.atomgit/`。写入使用同目录 0600 临时文件并原子替换，目录权限为 0700；
支持 `fchmod` 时按文件描述符设置模式，旧版 Windows Python 则在写入前对临时
路径应用系统权限语义。token 和登录 API 已验证的非敏感 username 以 JSON 保存；公开
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
- 托管 helper 命令显式调用当前 Python 解释器，并对 Windows/空格路径做
  shell 安全引用；
- 生成的 helper 只读本地已验证 username/token，不执行网络身份查询；旧配置需
  重新 login 才能补齐 username；
- 多处异常被吞掉，诊断信息有限。

## 6. 上传

完整参数和分支见 [upload_command_analysis.md](upload_command_analysis.md)。

简化调用流：

```text
atomgit upload PATH
  -> repo ID/path/path-in-repo 和选项冲突校验
  -> 拒绝上传根路径或目录树中的任何符号链接
  -> 登录校验
  -> 文件
       -> 默认 hf upload_file（直接读取原文件）
       -> 传 ignore 或旧 HF 无 upload_file 时：临时目录 + upload_folder
  -> 目录
       -> 默认 resumable：稳定私有投影 + HfApi.upload_large_folder
       -> path-in-repo：源内容投影到远端前缀
       -> --auto-configure-lfs：服务端 LFS 判定后、对象上传或引用提交前检查并按需单文件提交属性；同时修复不安全 regular 模式
       -> --no-resumable 或自动兼容 message：upload_folder
  -> 所有 LFS commit：规范 pointer payload + 返回 commit 的原始 V5 blob 精确验证
```

符号链接检查先于凭证读取、HF 上传调用和 resumable worker 创建。普通、失效、
指向目录外或原本会被 `--ignore` 排除的符号链接都统一失败关闭，避免锁定版 HF
上传逻辑把链接目标内容作为普通文件提交。检查不跟随目录符号链接。

已知问题：

- 上传、下载和建仓共享多层 repo ID 转换；远程写入仍需受控验收；
- 单文件 fallback 使用唯一系统临时目录，并在成功或失败后自动清理；
- 非默认 revision 必须预先存在；CLI 通过 V5 分支详情验证后才转发给上传和可选
  LFS 配置事务，避免静默写入默认分支。

锁定 HF 客户端完成 LFS 对象上传后，AtomGit 上传上下文会把 `lfsFile` 元数据转换
为固定 ASCII/LF 的标准三行 pointer，并作为普通 Git blob 内容提交，绕过服务端
缺少末尾 LF 的 pointer 物化逻辑。单文件、普通目录和 SDK 使用返回的 commit SHA
回读 V5 contents 原始 blob；resumable 在每个子提交成功后验证，响应不明确时先做
既有 OID/size 对账，再验证目标 revision，最后才标记断点元数据为已提交。验证不
解析到大型 LFS 对象，且该 HF 序列化包装在非 AtomGit 上下文中保持关闭。

resumable 通过显式 AtomGit endpoint 的 `HfApi(endpoint=..., token=...)` 认证，
避免隔离子进程回落到 `huggingface.co`。私有 model 和 dataset 均已使用真实
399,300,506 字节文件验证中断、恢复和最终 SHA-256；dataset 在保留用户侧业务
类型的同时使用 AtomGit 可用的共享 model 传输路由。锁定版 HF 不支持在
large-folder 方法上传入 `path_in_repo`，因此 CLI 以源目录、规范化仓库、revision
和前缀、批次序号为身份建立稳定缓存投影；所有 resumable 上传使用该投影隔离 HF 元数据，
带前缀时源内容位于对应投影子目录，文件同步优先使用硬链接，跨文件系统仅使用
符号链接，不复制源文件字节；目录上传按 20 个文件顺序分批。隔离子进程在创建
HF client 前设置并验证单次请求超时，并包装 `create_commit`：429 遵循
`Retry-After` 或退避且不拆批，超时先通过 resolve 元数据核对远端对象，确认缺失
后才按 `20/10/5/2/1` 降批。连续失败终止隔离进程，保留未完成的 HF 元数据。
同一子进程在 HF `_preupload_lfs` 原子边界分类 Git LFS Batch 失败：终止性配额、
权限和请求错误立即退出，只有限流、500/502/503/504、超时和连接错误最多尝试三次，
退避等待受 60 秒上限和显式上传总 deadline 约束。作用域补丁在成功和失败后均恢复。
LFS PUT 同样由该隔离子进程安装作用域包装：按 5 秒采样网络请求对 payload 的消费，
以三个 30 秒窗口建立稳定自身/同伴基线并确认持续低速，且只有替换预计至少节省一半
剩余时间时才中断当前对象请求。basic PUT 从零重传；multipart 在同一 action 内只
复用已确认 ETag 的 part。对象级三次上限、2-8/60/180 秒退避、新连接 2 倍改善及
稳定同伴基线 70% 检查，以及全局单探针门避免无限循环或整体降速时的重连风暴。
普通 HTTP 异常不在签名 PUT
URL 内盲重试，而是回到有界 `_preupload_lfs` 边界重新取得 Batch 状态；完整 OID 已
存在时依赖按 no-op 对账。源文件身份在每次替换和成功传输后复核，包装及依赖符号在
子进程退出前恢复。
子进程发现超过 regular 上限的文件时只向父进程返回经过白名单校验的扩展名规则。
默认仍安全失败；显式 `--auto-configure-lfs` 才会在 `$HF_HOME/lfs-config/` 的私有
事务目录中单独读取或创建根 `.gitattributes`，按字节保留已有内容并追加标准 LFS
规则，通过目标 revision 的 `parent_commit` 防止覆盖并发更新，回读确认后重试同一
批次。该规则作用于整个仓库；无安全扩展名或已尝试规则仍无效时停止自动修改。
`atomgit cache clear` 可清理 `$HF_HOME` 下由工具产生的缓存。

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

`--verify-checksum` 对标准路径通过锁定 HF Hub 的 `get_hf_file_metadata` 读取
resolve 元数据；嵌套非 ASCII 路径仅在编码请求返回 404 时，改用 raw UTF-8
HEAD 读取同一组强元数据，并沿用跨域凭据剥离和 HTTPS 降级拒绝规则。40 位
十六进制 ETag 按 Git blob SHA-1 校验，64 位按内容 SHA-256 校验，并同时要求
文件大小一致；冲突或缺失的大小会失败关闭。已有文件只读取校验；新下载内容在
唯一临时文件中校验通过后才原子替换。checksum 不匹配会重试一次，仍失败或
元数据不受支持时保留已有目标并返回非零。该选项不改变默认的已有文件跳过策略。

`--resume` 使用锁定 HF Hub 的 `http_get(resume_size=...)` 续传标准 URL；raw
UTF-8 路径使用同等严格的 Range/Content-Range 校验。未完成数据位于权限为
`0700` 的 AtomGit resume 缓存中，partial 文件为 `0600`，缓存键不含 token、
签名 URL 或明文仓库名。完成数据通过 checksum 后复制到目标目录的唯一临时
文件，再次校验并原子替换；成功后清理 partial，失败时保留原目标。

整仓下载成功后会在目标目录外的 AtomGit 私有缓存维护版本化 manifest。manifest
路径由 endpoint、规范化仓库 ID、仓库类型和解析后的本地目录共同哈希，目录权限
为 `0700`、文件权限为 `0600`，内容不含 token 或下载 URL，并通过唯一临时文件
原子替换。只有本次实际写入的文件才会新增为受管理文件；默认跳过的既有文件不会
被自动接管。普通下载的 manifest 记录是尽力而为：缓存不可用时警告但不改变既有
下载成功语义，未记录的文件不会被后续清理；显式 `--prune` 对 manifest 错误失败
关闭。首次对既有目录执行 `--force --prune` 可用成功重下的文件建立管理基线。

每个 manifest 身份旁维护一个不含仓库名或凭据的私有 advisory lock 文件。
POSIX 使用非阻塞 `flock`，Windows 使用非阻塞单字节 `msvcrt.locking`；锁从
manifest 读取前持续到下载、可选 prune 和原子写入结束。OS 会在进程退出时释放
所有权，锁文件可持久存在。同一 checkout 的竞争命令在任何传输或清理前失败，
不同仓库类型或目标目录的锁互不影响。

`--prune` 只计算“上次 manifest 中受管理文件 - 本次完整远端文件清单”，且必须
在全部下载成功后才执行。POSIX 通过目录文件描述符逐层打开并拒绝跟随符号链接；
Windows 通过 Win32 句柄打开根目录和目标，拒绝目录与重解析点，比较句柄解析后的
最终路径，并只按已验证目标句柄标记删除。两条路径都只删除普通文件，不扫描目标
树、不删除目录或未登记内容。缺失文件视为已清理；manifest 无效、受管理路径
类型变化、超出根目录、下载或删除失败时命令失败且不推进 manifest。空仓库仍会
进入该流程，因此可安全移除全部历史受管理文件。

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
  不支持语义，并保留脱敏后的原始 cause。401 与 403 均保持兼容的
  `AtomGitAuthenticationError` 类型，但消息分别表达重新认证和权限不足；分类
  优先读取结构化 HTTP 状态，任意文本中的孤立数字不会触发认证分类。

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
- 包名为 `atomgit`，版本由 `version.py` 单一来源提供；
- `py_modules=['atomgit_hub']` 同时保留顶层兼容导入；
- `deploy.sh` 只执行本地 build/install/checksum；GitHub Release workflow 才是唯一
  发布入口，仓库不包含 PyPI/twine 写路径。

详细开发、测试和发布规则见：

- [development.md](development.md)
- [testing.md](testing.md)
- [release.md](release.md)
