# `atomgit upload` 当前实现分析

> 本文基于 `yuto` 分支版本 1.0.6 的当前源码。它同时记录已实现参数和已知缺陷，
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
| `-i, --ignore` | 无 | 逗号分隔的 ignore patterns |
| `--resumable/--no-resumable` | 按路径自动 | 目录默认使用 `upload_large_folder`；可显式选择普通上传 |
| `--num-workers` | `5` | 所有目录上传模式的 worker 数 |

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
5. 单文件默认普通上传；目录默认 resumable，未显式选模式的 `--message` 自动
   选择普通上传，并拒绝其余歧义组合；
6. 检查 `config.is_logged_in()`；
7. 打印大小、文件数量和选择的参数；
8. 将参数传给 `api.upload_folder` 或 `api.upload_directory`。

第 7 步的统计使用与上传相同的 `filter_repo_objects`，先应用用户的
`ignore_patterns` 并排除 resumable 自身的 HF 元数据，因此 CLI 展示值与实际接收的
过滤后文件集合一致。`--ignore` 由逗号分隔器解析，再交给锁定 HF 的
`filter_repo_objects`；shell 中整体使用双引号即可，写成 `\*\*` 会把反斜杠作为
模式内容传入，CLI 会在远端调用前以退出码 2 拒绝这种错误写法。

CLI 在认证和远端调用前拒绝歧义组合：单文件不接受显式 `--resumable` 或
`--ignore`；显式 `--resumable` 不接受 `--message`。`--num-workers` 与
`--path-in-repo` 是目录和文件上传的基础参数，普通目录与 resumable 均支持。
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

目录不会复制到临时目录。`path_in_repo`、repo type、revision 和 ignore patterns
都会按条件传给 HF `upload_folder`。

锁定的 `huggingface-hub==1.1.7` 先过滤目录对象；过滤后超过 30 个文件时记录
大目录提示，超过 200 个文件时提升为 warning。随后它为全部待上传对象构造
`CommitOperationAdd` 并读取文件计算哈希，完成前可能没有逐文件上传进度。普通
LFS 上传由 `create_commit(num_threads=...)` 控制，CLI 的 `--num-workers` 会传入
普通目录路径，默认值为 5。

LFS batch 响应没有 upload action 时，表示相同内容 OID 已存在于服务端，客户端
跳过数据传输并在提交中引用该对象。换一个 `path_in_repo` 后近乎立即成功属于
服务端内容去重，不是普通模式获得了本地断点续传。部分传输的单个新文件没有
large-folder 元数据保证；重新执行时只能可靠依赖已经完整存在或提交的对象去重。

普通模式会在一次调用中哈希并提交过滤后集合；客户端内部按 20 个文件顺序分批
调用 `upload_folder`，不修改源目录，失败后只需重试当前命令即可。批次选择和
状态都由程序内部管理，用户无需手工拆分目录。上传开始前会显示过滤后的文件
总数、计划批次数和每批最多 20 个文件；每批按顺序显示开始、成功或失败、累计
确认进度，上一批确认成功后才会显示下一批开始。结束时汇总计划、新增提交、
续传跳过和确认完成的文件数。

## 5. Resumable 目录上传

目录在没有显式选择且没有 `--message` 时默认进入该分支。`--resumable` 可继续
用于显式选择：

resumable 分支调用：

```text
HfApi(token=保存的_token).upload_large_folder(
    repo_id=...,
    folder_path=...,
    repo_type=model,  # 用户选择 dataset 时也映射到共享兼容路由
    revision=...,
    ignore_patterns=...,
    num_workers=...,
)
```

当前锁定的 `huggingface-hub==1.1.7` 要求把 `token` 传给 `HfApi(token=...)`
构造函数，`upload_large_folder()` 方法本身不接收 `token`。实现和严格签名测试
均遵守该契约。私有 model 和 dataset 已分别用 399,300,506 字节文件完成真实
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
  resumable 上传和 20 文件批次建立持久投影，避免同一源目录上传到不同仓库时复用错误的 HF
  元数据。HF 方法不接收 `path_in_repo`，带前缀时投影把源文件放在对应目录下再把
  投影根传给 HF。相同源目录、规范化仓库、传输类型、revision 和前缀会复用同一
  投影与 HF 元数据；同步会反映源文件增删改并排除源目录自身的
  `.cache/huggingface`，用户 `--ignore` 排除的文件也不会物化到投影；
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
确认完成数、剩余数、复用保留断点的指引以及一致汇总。

真实 404 MB 文件测试已完成“中断 -> 再次执行 -> 下载回读”，文件大小和
SHA-256 均一致。

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
CLI 全局状态恢复以及大文件中断恢复。这些测试仍没有证明：

- CLI 先通过 `repo branch create` 的 V5 POST/GET 创建并验证分支，随后
  revision 才会写入目标远端分支；SDK 仍只支持 main；
- 多层 repo ID 的远程创建和上传成功；
- ignore 在真实远端确实排除了文件。

远程测试应拆分每项能力并执行上传、下载回读和内容校验，详见
[testing.md](testing.md)。
