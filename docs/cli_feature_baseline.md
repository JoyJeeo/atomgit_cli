# CLI 基础功能与回归基线

本文记录 `1.0.6` 当前公开 CLI 的基础能力。代码仓采用单调演进原则：后续
开发可以增加能力，但新增能力必须同步增加专项测试、基线登记和文档；不得在没有
明确兼容决策的情况下删除、改名或破坏本文列出的命令、参数和行为。

精确接口契约位于 `tests/cli_baseline_contract.py`，接口和分派执行位于
`tests/test_cli_feature_baseline.py`，基线自身的防绕过测试位于
`tests/test_cli_baseline_guard.py`。DoD 入口 `python tests/run_cli_baseline.py`
会执行完整隔离 pytest 矩阵，不访问网络、真实 HOME、真实 Git 配置或凭证。

## 认证与本地配置

| 命令 | 当前能力 | 基础保证 |
|---|---|---|
| `atomgit login` | 交互输入、`--token/-t`、`--token-stdin` 登录 | 远端验证后保存凭证；输出不回显 token；Git 可用时配置 AtomGit 专属 credential helper |
| `atomgit logout` | 清除登录和托管的 Git helper 状态 | 可重复执行；Git helper 恢复失败时返回非零并保留恢复提示 |
| `atomgit whoami` | 查询当前登录用户 | 未登录或远端查询失败时返回非零；成功时显示已验证用户名 |
| `atomgit config-show` | 显示登录及 Git 集成状态 | 不显示 token；区分完整、部分、未启用和检查失败 |

## 仓库与分支管理

| 命令 | 当前能力 | 基础保证 |
|---|---|---|
| `atomgit repo create REPO --type model\|dataset --private\|--public` | 创建 model/dataset 仓库 | 可见性必须显式选择并在创建后验证；`--exist-ok` 提供显式幂等行为 |
| `atomgit repo list` | 列出当前凭证可访问的仓库 | 输出仓库 ID 和可见性；认证/API 失败返回非零 |
| `atomgit repo visibility REPO public\|private` | 修改仓库可见性 | 写入后读取验证远端最终状态 |
| `atomgit repo delete REPO --confirm REPO` | 永久删除仓库 | 必须原样重复仓库 ID；删除后验证远端已不存在 |
| `atomgit repo branch create REPO BRANCH --from REVISION` | 创建非 main 分支 | 解析来源提交、创建分支并验证分支名称和来源提交 |

仓库 ID 支持 `owner/repo` 及项目定义的多层 ID 映射。仓库管理命令需要登录，任务
分支、标签和提交的具体 AtomGit 远端语义仍以专项契约和受控远程证据为准。

## 上传

```text
atomgit upload PATH --repo-id REPO [OPTIONS]
```

现有基础能力：

- 上传单个文件或整个目录；
- `--message/-m` 提交消息；
- `--timeout/-t` 上传超时；
- `--no-progress-bar` 关闭进度条；
- `--path-in-repo/-p` 指定仓库内目录；
- `--repo-type/-r model|dataset` 指定业务类型；
- `--revision` 上传到已存在的 revision；
- `--ignore/-i` 为目录上传传递忽略模式；
- 目录默认使用 large-folder 断点续传，`--resumable/--no-resumable` 可显式选择，
  `--num-workers` 控制 worker 数；
- 参数冲突、无效路径、符号链接和缺少登录凭证会在上传前失败；
- 上传超时和进度条的进程级状态在成功与失败后恢复。

单文件默认直接读取原文件，不创建完整副本；必要的兼容回退使用唯一临时目录。
resumable 与 `--path-in-repo` 组合使用稳定的私有缓存投影并保留 HF 元数据。
large-folder 不支持单一提交说明，因此未显式选择模式的 `--message` 使用普通上传；
显式 `--resumable --message` 会在远端调用前拒绝。

## 下载

### 整仓下载

```text
atomgit download REPO [OPTIONS]
```

- `--directory/-d` 指定目标目录；
- 默认跳过已存在文件；
- `--force` 重新下载并安全替换文件；
- `--verify-checksum` 校验已有文件和新下载内容；
- `--resume` 保留未完成数据并从中断位置续传，完成后强制校验；
- `--prune` 仅清理由下载 manifest 记录、且远端已经删除的文件；
- `--repo-type/-r model|dataset` 显式指定类型，不指定时探测类型；
- 公开仓库可匿名下载，私有仓库使用已保存凭证；
- 下载文件名经过路径穿越、绝对路径、控制字符和符号链接边界检查；
- 标准及 raw Unicode 路径下载使用唯一临时文件，失败时保留原目标。

### 单文件下载

```text
atomgit download-file REPO FILENAME [OPTIONS]
```

支持 `--directory/-d`、`--force`、`--verify-checksum`、`--resume` 和
`--repo-type/-r`，并保持与整仓下载一致的公开/私有凭证选择、路径安全、原子替换
和错误退出语义。

## 回归测试边界

基础契约保护：

- 根命令、命令组和叶子命令集合必须与登记完全一致；
- 参数顺序、类型、必填性、默认值、flag、Choice 和长短选项必须精确一致；
- 每条命令的 `--help` 可用；
- 每个叶子命令必须登记且至少完成一次隔离成功分派；
- 关键参数到 API 层的映射保持不变；
- 每个 `test_*.py` 必须且只能登记一次，并具有真正执行 `main()` 的入口；
- 完整离线矩阵中的认证、仓库、上传、下载、SDK、依赖、安全、打包和跨平台
  专项测试全部通过；
- 登录输出不泄露测试 token，测试不触碰真实用户状态。

新增命令或参数但未更新 schema、新增测试但未登记、删除测试、遗漏叶子分派，都会
直接使门禁失败。新增功能使用现有命令时，也必须增加或扩展专项测试；统一入口会
自动执行这些测试。若既有能力回退，必须修复运行时代码并重新通过门禁，不能修改
测试去适配错误行为。只有维护者在当前 Issue 中明确批准公开兼容性破坏时，才允许
同步更新旧契约。

基础契约不冻结输出颜色和内部实现结构。下载完整性、凭证安全、Git helper、上传
生命周期、依赖签名、Windows 兼容和 wheel smoke 等保证由已登记专项测试提供。
