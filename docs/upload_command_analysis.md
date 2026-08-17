# `atomgit upload` 当前实现分析

> 本文基于 `yuto` 分支版本 1.1.0 的当前源码。它同时记录已实现参数和已知缺陷，
> 避免把 CLI 帮助中的能力直接等同于远程验证通过。

## 1. 命令接口

```text
atomgit upload [OPTIONS] PATH
```

| 参数 | 默认值 | 作用 |
|---|---|---|
| `PATH` | 必填 | 本地文件或目录，Click 要求存在 |
| `--repo-id` | 必填 | 目标仓库 ID |
| `-m, --message` | 空 | 提交消息 |
| `-t, --timeout` | 请求 300 秒、总时长不限 | 单次网络请求超时；resumable 目录同时作为上传总时限 |
| `--no-progress-bar` | 关闭 | 禁用 HF 上传进度条 |
| `-p, --path-in-repo` | 根目录 | 仓库内目标前缀 |
| `-r, --repo-type` | HF 默认 model | `model` 或 `dataset` |
| `--revision` | 默认分支 | CLI 接受已存在的安全分支名；需先显式创建 |
| `-i, --ignore` | 无 | 逗号分隔的额外 ignore patterns |
| `--resumable/--no-resumable` | 按路径自动 | 目录默认使用 `upload_large_folder`；可显式选择普通上传 |
| `--num-workers` | `5` | 所有目录上传模式的 worker 数 |
| `--batch-size` | `20` | 目录外层批次上限，可选 `1..20` |
| `--auto-configure-lfs` | 关闭 | 显式允许 resumable 为服务端判定的 LFS 扩展名检查并按需补齐仓库级 `.gitattributes` |

AtomGit 当前的 HF 兼容服务对 model 和 dataset 共用创建与上传传输路由。CLI
仍使用 `dataset` 表达仓库业务类型，但底层调用映射到 model 路由。2026-08-04
的受控大文件探测确认共享路由可进入 LFS 上传并保留恢复元数据，因此不再沿用
旧 dataset 端点的 404 拒绝保护；用户输入不会被改写。

## 2. CLI 前置处理

`cli.upload` 依次执行：

1. 校验 timeout、worker 数和安全 revision 名；
2. 使用 `validate_repo_name` 校验 repo ID；
3. 将 PATH 转为 `Path` 并区分文件或目录；
4. 使用 `normalize_path_in_repo` 与 `parse_ignore_patterns` 规整参数；
   目录上传再将用户模式稳定去重地追加到 CLI 默认 macOS 元数据
   规则之后；
5. 单文件默认普通上传；目录默认 resumable，未显式选模式的 `--message` 自动
   选择普通上传；`--auto-configure-lfs` 只接受 resumable 目录；
6. 检查 `config.is_logged_in()`；
7. 打印大小、文件数量和选择的参数；
8. 将参数传给 `api.upload_folder` 或 `api.upload_directory`。

第 7 步的统计使用与上传相同的 `filter_repo_objects`，先应用 CLI 默认
`._*`、`**/._*`、`.DS_Store`、`**/.DS_Store` 及用户追加模式，并排除
resumable 自身的 HF 元数据，因此 CLI 展示值与实际接收的
过滤后文件集合一致。`--ignore` 由逗号分隔器解析，再交给锁定 HF 的
`filter_repo_objects`；shell 中整体使用双引号即可，写成 `\*\*` 会把反斜杠作为
模式内容传入，CLI 会在远端调用前以退出码 2 拒绝这种错误写法。

CLI 在认证和远端调用前拒绝歧义组合：单文件不接受显式 `--resumable` 或
`--ignore`；显式 `--resumable` 不接受 `--message`；单文件和普通目录不接受
`--auto-configure-lfs`。`--num-workers` 与
`--path-in-repo` 是目录和文件上传的基础参数，普通目录与 resumable 均支持。
合法 `--batch-size` 仅影响目录外层分组；单文件命令接受该选项但没有外层批次可调整。
显式选择 basename 为 `.DS_Store` 或以 `._` 开头的单文件也以退出码 2
拒绝，避免 AppleDouble sidecar 因后缀命中 Git LFS 规则而误入库。
这些用法错误统一以退出码 2 结束，不会进入 API 层。

## 3. 单文件上传

默认路径：

```text
cli.upload
  -> api.upload_folder(file_path, ...)
  -> normalize_path_in_repo
  -> hf_upload_file(
       path_or_fileobj=原文件,
       path_in_repo=<前缀>/<文件名>,
       repo_id=原始 repo_id,
       token=保存的 token,
       commit_message=...,
       repo_type=可选,
       revision=可选)
```

默认不会复制原文件，避免大文件的额外本地磁盘开销。

以下情况退回 `upload_folder`：

- 当前 HF 版本没有 `upload_file`；
- API 调用方直接传入非空 ignore patterns（CLI 已拒绝单文件 `--ignore`）。

回退路径为每次调用创建唯一系统临时目录，复制文件后上传，并在成功或失败时
自动清理。临时内容只在 HF 调用期间存活，不会在当前工作目录创建共享目录。

## 4. 普通目录上传

显式 `--no-resumable`，或在没有显式选择模式时提供 `--message`，进入普通
目录上传：

```text
cli.upload
  -> api.upload_directory(dir_path, resumable=False, ...)
  -> upload_folder(
       folder_path=原目录,
       path_in_repo=<规范前缀>/ 或 ./,
       repo_id=原始 repo_id,
       token=保存的 token,
       commit_message=...,
       repo_type=可选,
       revision=可选,
       ignore_patterns=可选)
```

目录不会复制到临时目录。`path_in_repo`、repo type、revision 和完整有效
ignore patterns 都会按条件传给 HF `upload_folder`。同一有效集合同时驱动预上传
统计、用户配置的 `1..20` 文件批次选择和底层 HF 调用。

锁定的 `huggingface-hub==1.1.7` 先过滤目录对象；过滤后超过 30 个文件时记录
大目录提示，超过 200 个文件时提升为 warning。随后它为全部待上传对象构造
`CommitOperationAdd` 并读取文件计算哈希，完成前可能没有逐文件上传进度。普通
LFS 上传由 `create_commit(num_threads=...)` 控制，CLI 的 `--num-workers` 会传入
普通目录路径，默认值为 5。

LFS batch 响应没有 upload action 时，表示相同内容 OID 已存在于服务端，客户端
跳过数据传输并在提交中引用该对象。换一个 `path_in_repo` 后近乎立即成功属于
服务端内容去重，不是普通模式获得了本地断点续传。部分传输的单个新文件没有
large-folder 元数据保证；重新执行时只能可靠依赖已经完整存在或提交的对象去重。

普通模式先过滤并确定性排序文件，再按 `--batch-size` 顺序分批，默认
上限仍为 20。每个外层批次各调用一次 `upload_folder`，因此较小值会增加
调用和可能的提交数。此路径不修改源目录，失败后只需重试当前命令即可。批次选择和
状态都由程序内部管理，用户无需手工拆分目录。上传开始前会显示过滤后的文件
总数、计划批次数和配置的每批上限；每批按顺序显示开始、成功或失败、累计
确认进度，上一批确认成功后才会显示下一批开始。结束时汇总计划、新增提交、
续传跳过和确认完成的文件数。

单文件、普通目录和 resumable 三条路径共享同一个上下文隔离的 LFS commit
契约。HF 仍先按原流程上传实际 LFS 对象；提交生成阶段把每个 `lfsFile(path,
algo, oid, size)` 转换为 Base64 `file` 记录，其内容严格为：

```text
version https://git-lfs.github.com/spec/v1\n
oid sha256:<64-lowercase-hex>\n
size <non-negative-decimal>\n
```

OID 或 size 元数据不合法会在提交前失败。提交成功后按返回 commit SHA 调用官方
V5 contents API，读取未解析的原始 Git blob 并与预期字节完全比较，不下载 LFS
对象。非规范、响应畸形或无法确认都会使上传失败。该包装使用上下文变量隔离，
同一进程中不属于 AtomGit 上传的 HF commit 仍保持锁定依赖的原始 `lfsFile`
行为。历史提交中的旧 pointer 不在上传流程中自动修复。

## 5. Resumable 目录上传

目录在没有显式选择且没有 `--message` 时默认进入该分支。`--resumable` 可继续
用于显式选择：

resumable 分支调用：

```text
HfApi(
    endpoint="https://hub.atomgit.com",
    token=保存的_token,
).upload_large_folder(
    repo_id=...,
    folder_path=...,
    repo_type=model,  # 用户选择 dataset 时也映射到共享兼容路由
    revision=...,
    ignore_patterns=...,
    num_workers=...,
)
```

当前锁定的 `huggingface-hub==1.1.7` 要求把 endpoint 和 `token` 传给
`HfApi(endpoint="https://hub.atomgit.com", token=...)` 构造函数；显式 endpoint
避免子进程回落到 `huggingface.co`。`upload_large_folder()` 方法本身不接收
`token`。实现和严格签名测试均遵守该契约。私有 model 和 dataset 已分别用
399,300,506 字节文件完成真实
CLI 中断、恢复、下载与 SHA-256 验证。

HF 1.1.7 在恢复元数据前固定调用 `create_repo(exist_ok=True)`。AtomGit CLI 不把
上传当作建仓入口：父进程先通过 AtomGit V5 仓库详情接口，并在指定非 `main`
revision 时通过分支详情接口，对规范化后的目标做一次只读校验。这样私有仓库不依赖
HF tree 路由的可见性；随后子进程用已校验仓库引用满足 HF 启动流程，不发送隐式建仓
请求。不存在、不可访问或分支不存在的目标会在投影、哈希和上传 worker 启动前失败；
全部文件已经提交的续传也仍执行这次远端校验。

HF large-folder 模式的其他限制：

- CLI 和 SDK 在凭证或上传调用前拒绝上传根路径及目录树中的全部符号链接；
  `ignore_patterns` 不会绕过该安全检查；
- CLI 在 `$HF_HOME/upload-projections/` 使用 credential-free 哈希身份为每个
  resumable 上传和每个配置批次建立持久投影，避免同一源目录上传到不同仓库时复用错误的 HF
  元数据。HF 方法不接收 `path_in_repo`，带前缀时投影把源文件放在对应目录下再把
  投影根传给 HF。相同源目录、规范化仓库、传输类型、revision 和前缀会复用同一
  投影与 HF 元数据；同步会反映源文件增删改并排除源目录自身的
  `.cache/huggingface`，CLI 默认 macOS 规则及用户 `--ignore` 排除的文件
  也不会物化到投影；复用投影时会移除新规则已排除的旧 sidecar，但保留
  投影根的 HF 断点元数据；
  批次上限同时进入投影身份，相同值复用状态，切换值不会绑定到旧分组元数据；
- 投影优先使用硬链接，跨文件系统或平台不支持时仅使用符号链接，绝不复制源
  文件字节；两种链接均不可用时安全失败。投影根权限在支持 POSIX 权限的平台设为 `0700`；
- 不支持用户指定的单一 commit message，CLI 在远端调用前拒绝
  显式 `--resumable --message`；未显式选择模式时 `--message` 自动走普通上传，
  服务过程可产生多次提交；
- repo type 必填，CLI 未指定时补为 `model`；
- 续传元数据由 HF 写入按上传身份隔离的稳定投影根，不污染源目录。

HF 1.1.7 的 regular commit 载荷上限为 1 GB。服务端 `preupload` 若仍将超过该值
的单文件判定为 `regular`，子进程会在 commit 构造再次读取文件或进行 Base64 编码
前终止，不进入重试、远端核对或降批，并提示在仓库 `.gitattributes` 中配置 Git
LFS。重新执行时仅清空这种危险且未提交元数据的 `upload_mode`、`should_ignore`
和 `remote_oid`，使服务端重新判定策略；SHA-256 和已提交记录保持不变。

未提供 `--auto-configure-lfs` 时保持上述失败关闭行为，并提示只有在允许 CLI 创建
配置 commit 时才能使用该选项。显式启用后，服务端每次判定 upload mode 后，CLI
会从 `lfs` 项推导最多 32 个经过 ASCII 扩展名白名单校验的 `*.ext`。对断点元数据
中已缓存为 `lfs` 的项目，同一门禁还会在 LFS 预上传及引用提交边界检查。缺少本次
命令已确认记录的规则时，子进程在对象上传或提交前仅回传这些安全规则，不传本地
完整路径、URL、响应正文或凭据；父进程显示规则会影响整个仓库，然后执行以下事务：

1. 通过 V5 commit 详情把目标 revision 解析为不可变 SHA；
2. 在 `$HF_HOME/lfs-config/` 下的 `0700` 唯一缓冲目录，只读取该 SHA 的根目录
   `.gitattributes`；404 表示文件缺失，其他认证、权限或仓库错误不得当作缺失；
3. 保留原字节和换行，仅追加缺少的
   `*.ext filter=lfs diff=lfs merge=lfs -text`，文件和目录分别使用 `0600/0700`；
4. 用显式 AtomGit endpoint、同一有效 repo type/revision 和 `parent_commit` 调用
   `HfApi.upload_file`，因此 commit 只含 `.gitattributes`；
5. 对最新不可变 SHA 回读规则。写响应不明确但回读存在规则时视为成功；409/412
   并发冲突最多重新拉取合并三次；其他无法确认状态安全失败；
6. 把已确认规则带入重试子进程并重试当前外层批次。一个规则在同次命令只检查一次；
   对超大 regular 修复仍刷新危险的未提交模式。无扩展名或规则仍不生效时不会生成
   `*` 或循环提交。

该路径的 SDK 1.1.7 参数、合并、并发、超时回读和批次恢复已有严格离线测试。
2026-08-12 在授权测试仓库完成主动配置真实验收：服务端把唯一测试扩展名判为 LFS
后，CLI 在对象预上传前追加并回读根 `.gitattributes`，再上传 12 MiB 对象；相同命令
重跑时已提交文件被断点跳过、规则只检查不重复提交，远端 HEAD 保持不变。

CLI 在隔离子进程内为 `create_commit` 增加 AtomGit 专用控制：429 遵循
`Retry-After` 或指数退避且不拆批；网络超时后先用远端 checksum/OID 核对请求
是否已经成功，只重试缺失对象；持续的超时或 5xx 才按 `20 → 10 → 5 → 2 → 1`
降批。这些限流等待、重试、远端状态核对和降批事件都带当前外层批次编号。
外层批次开始时会读取 HF 1.1.7 的持久元数据：内容未变化且已经提交的文件显示
为“续传跳过”，不会计入本次新增提交；全部已完成的批次仍进入 HF 流程，以保留
远端仓库存在性和权限校验，但不会被报告为新的提交。
达到连续失败上限后子进程仅传回受限的结构化错误类别，不跨进程传递原始响应、
URL、凭证或本地完整路径。CLI 据此区分认证、权限、仓库/revision 不存在、载荷、
限流、服务不可用、超时、连接、上传模式和客户端资源错误，并显示失败批次、累计

同一子进程还在 HF 1.1.7 `_preupload_lfs` 原子边界安装作用域控制器，避免依赖
worker 捕获异常后立即、无限地把同一对象放回队列。AtomGit 结构化 413 配额响应
及协议 507 归为 LFS 存储不足，509 归为带宽额度不足；不匹配配额语义的 413、422、
其他 4xx 和畸形 Batch 响应安全终止为 LFS 协商拒绝。只有 429、500/502/503/504、
超时和连接失败允许重试，固定最多三次，基础退避为 2 秒、4 秒，等待上限 60 秒；
有效 `Retry-After` 受同一上限和显式上传总 deadline 约束。终止或耗尽后仅传回受限
类别，不回传响应正文、URL、header、OID、trace ID 或本地路径；SHA-256、LFS 模式、
未确认上传/提交状态及先前已提交批次保持可恢复。此失败不会触发
`--auto-configure-lfs`，因为它不是 regular/LFS 策略误判。
确认完成数、剩余数、复用保留断点的指引以及一致汇总。

真实 404 MB 文件测试已完成“中断 -> 再次执行 -> 下载回读”，文件大小和
SHA-256 均一致。

默认 macOS 排除是 CLI 边界策略。`api.upload_directory` 仍只应用调用方显式
传入的模式，公开 Python SDK `atomgit_hub.upload_folder(ignore_patterns=...)`
也保持调用方完全控制，不隐式追加 CLI 默认。

## 6. 进度条和 timeout

上传前保存完整进度条状态和 `hf_constants.DEFAULT_REQUEST_TIMEOUT`，关闭旧 HF
session 后以目标请求超时创建新 client，退出上传分支时在 `finally` 中恢复调用前
状态并再次关闭 session。由于这些仍是进程级全局值，并发调用需谨慎。

省略 `--timeout` 时，上传总时长不限，但单次 HF 网络请求默认超时 300 秒，以便
网络失效后进入可控重试而不是永久阻塞。显式 `--timeout N` 时，两种模式都把
请求超时设置为 N 秒；resumable 模式还以 N 秒等待整个隔离上传进程，超过后终止
该进程。因此显式 resumable timeout 是本次命令的硬总时限，不会因某个分块完成
而重新计时。

批次生命周期日志不依赖 HF 进度条；使用 `--no-progress-bar` 时计划、开始、
成功/跳过/失败、累计进度、重试事件和最终汇总仍会输出，适合 CI 日志留存。

## 7. Repo ID

上传、下载、建仓、SDK URL 和 dataset loading 共享同一个多层 ID 映射：
`org/namespace/repo -> org-namespace/repo`。匿名公开读取已验证该映射；上传和
创建的远程写结果仍需授权后验收；当前持续授权仅限已提供的两个固定
测试仓库。

## 8. 错误处理

上传异常由 `_classify_upload_error` 分类为：

- 认证失败；
- 仓库不存在；
- 受限仓库；
- 仓库已禁用；
- revision 不存在；
- 请求参数错误；
- 请求超时；
- 网络连接失败；
- 上传模式不安全；
- 客户端资源不足；
- 未知错误。

API 方法打印类型和建议后返回 `False`，CLI 再以非零状态退出。分类同时依赖异常
类名和字符串特征，服务端文本变化可能影响判断。

## 9. 当前测试结论

离线测试已经验证参数解析和 fake 调用，包括：

- path-in-repo 规范化与 `..` 拒绝；
- repo type、revision、ignore 和进度条参数；
- 单文件默认走 `upload_file`；
- 单文件 ignore 回退及临时目录清理；
- resumable 参数构造；
- 错误分类。

离线契约与远程测试还验证了 resumable 的真实 HF 签名、dataset 上传路由、
CLI 全局状态恢复以及大文件中断恢复。2026-08-11 的受控小型 `.bin` 上传还证明：
实际 LFS OID/size 保持不变，提交树中的新 pointer 与客户端预期字节完全相等，
以单个 LF 结尾，并通过 `git lfs pointer --check --strict`。测试仓库的既有旧
pointer 没有在该验收中修复。这些测试仍没有证明：

- CLI 先通过 `repo branch create` 的 V5 POST/GET 创建并验证分支，随后
  revision 才会写入目标远端分支；SDK 仍只支持 main；
- 多层 repo ID 的远程创建和上传成功；
- ignore 在真实远端确实排除了文件。

远程测试应拆分每项能力并执行上传、下载回读和内容校验，详见
[testing.md](testing.md)。
