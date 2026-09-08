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
- 🧩 **上传能力增强（1.1.0 稳定版）**：
  - 进度条开关（`--no-progress-bar`）
  - 仓库内目标路径（`-p/--path-in-repo`）
  - 仓库类型选择（`-r/--repo-type model|dataset`）
  - 显式分支创建与非 `main` 上传（CLI）
  - 忽略文件模式（`-i/--ignore`）
  - 目录默认断点续传/分块上传（`--resumable/--no-resumable`、`--num-workers`）
  - 单文件上传无本地拷贝（直接走 `upload_file`）
  - 语义化错误分类（认证失败 / 权限不足 / 仓库不存在 / 超时等，附可执行建议）

### SDK功能
- 🐍 **Python原生接口**：类似huggingface_hub的API设计
- 🔄 **与CLI共享配置**：使用相同的认证和配置文件
- 📦 **一键安装**：安装atomgit包即可同时使用CLI和SDK
- 🚀 **完整API**：snapshot_download、upload_folder、create_repository等
- 📝 **完善的文档**：详细的使用示例和错误处理

## 系统要求

- **Python 3.9+** (推荐Python 3.11+)
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

### 从 GitHub Release 安装

普通用户不需要 conda。安装器默认选择最高的、非 draft/非 prerelease、标签严格为
`X.Y.Z` 的已完成 GitHub Release，只下载匹配的 wheel 和 `SHA256SUMS`，在 pip
之前校验 Release、wheel 元数据和摘要：

```bash
curl -fsSL https://raw.githubusercontent.com/JoyJeeo/atomgit_cli/yuto/install.sh -o install.sh
sh install.sh
sh install.sh --version 1.1.1
sh install.sh --python /absolute/path/to/python --force-reinstall
```

`--python`、`--version`、`--force-reinstall` 和 `--no-completion` 可以组合。安装
成功只会在目标解释器通过版本、CLI、模块和导入验证后报告；输出还会显示解释器、包
位置、命令目录和 PATH 可见性。目标解释器属于当前活动 conda 环境且使用 Zsh 时，
官方安装器默认启用该环境自己的 AtomGit 补全；非 conda/venv 安装会准确说明已跳过，
设置失败是可见的非致命警告。

历史 `v...` Release 保留为不可变记录，但新安装器不会选择它们。没有已完成的
纯数字 Release 时安装会失败，不会回退到分支源码、归档或 PyPI。

已安装的 wheel 用户可以更新当前正在运行的 Python：

```bash
atomgit update
atomgit update --version 1.1.1
atomgit update --force-reinstall
```

`atomgit update` 只使用执行该命令的 `sys.executable`。源码或 editable 安装会被
拒绝，并提示使用 Git 更新 `yuto`，不会修改源码 checkout。

Windows 用户请下载指定 GitHub Release 的 `atomgit-X.Y.Z-py3-none-any.whl` 和
`SHA256SUMS`，使用支持的 Python 校验摘要后执行
`py -m pip install atomgit-X.Y.Z-py3-none-any.whl`；`install.sh` 仅支持 POSIX/macOS/Linux。

### 源码开发与更新

```bash
git clone https://github.com/JoyJeeo/atomgit_cli.git
cd atomgit_cli
git checkout yuto
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate atomgit_cli
python -m pip install -r requirements.txt
python -m pip install -e .
```

源码更新使用 Git，不使用 `atomgit update`：

```bash
git pull --ff-only
python -m pip install -r requirements.txt
python -m pip install -e .
```

AtomGit CLI 不发布到 PyPI；pip 仍可从用户配置的索引解析第三方依赖。

### 官方卸载

普通用户使用官方入口完整卸载当前解释器中的包和当前 conda 环境的受控补全：

```bash
curl -fsSL https://raw.githubusercontent.com/JoyJeeo/atomgit_cli/yuto/uninstall.sh | sh
```

也可直接运行 `atomgit uninstall`；该命令先显示解释器、环境根目录、版本和受控
目标，再要求确认。`--yes` 仅供官方非交互脚本使用。卸载不会删除
`~/.atomgit/config.json`、凭证、缓存或仓库。直接执行 `python -m pip uninstall
atomgit` 不是官方完整卸载路径；若环境补全仍存在，下次 conda 激活会只打印清理
指引，直到执行上述官方命令为止。

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

自动化场景可通过标准输入传入一行 token：

```bash
atomgit login --token-stdin < /path/to/protected-token-file
```

为兼容现有脚本，`atomgit login --token VALUE` 仍受支持，但参数值可能被 shell
历史或进程查看工具记录；优先使用交互输入或 `--token-stdin`。两种参数不可同时使用。

**🎉 Git集成功能**：登录成功后，工具会自动配置Git凭证助手，这样你就可以直接使用标准的Git命令来操作AtomGit仓库，无需再次输入token。登录时验证的用户名会随 token 保存在权限受限的本地配置中，Git 凭证查询不再发起网络请求：

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
| `-t, --timeout <sec>` | 默认网络请求等待超时秒数，省略时为 300 秒；上传总时长不限 |
| `--no-progress-bar` | 禁用进度条（日志/CI 场景） |
| `-p, --path-in-repo <prefix>` | 仓库内目标目录前缀（如 `sub/`），默认根目录 |
| `-r, --repo-type <model\|dataset>` | 仓库类型，默认按 model 处理 |
| `--revision <name>` | 上传到已存在分支；非 `main` 分支需先显式创建 |
| `-i, --ignore <patterns>` | 额外忽略的文件模式（逗号分隔，如 `*.tmp,logs/`），仅对目录上传有意义 |
| `--resumable / --no-resumable` | 目录默认使用断点续传；显式 `--no-resumable` 改用普通上传 |
| `--num-workers <n>` | 上传并发 worker 数，默认 5；普通目录和 resumable 目录均可使用 |
| `--batch-size <1-20>` | 每个目录上传外层批次的最大文件数，默认 20；单文件上传不受影响 |
| `--auto-configure-lfs` | 显式允许 resumable 为服务端判定的 LFS 扩展名检查并按需补齐仓库级 `.gitattributes` |

目录未显式选择模式时默认使用断点续传；单文件仍使用普通文件上传。目录指定
`--message` 且未显式选择模式时会自动使用普通上传，以保留单一提交说明。
冲突参数会在上传前以退出码 2 拒绝：显式 `--resumable` 仅适用于目录且不能与
`--message` 同用；`--ignore` 仅适用于目录上传；`--auto-configure-lfs` 仅适用于
resumable 目录。线程数和仓库内路径是所有适用上传模式的基础参数。

`--batch-size` 在忽略过滤和确定性排序之后对目录文件分组，普通上传和
resumable 上传使用同一上限。较小值可减少每批工作量和失败范围，但会增加
外层上传调用及可能的提交数。它不是 `--num-workers`，也不改变远程失败后的
内部 commit 降批策略。

```bash
atomgit upload ./data --repo-id user/my-dataset --batch-size 2
atomgit upload ./data --repo-id user/my-dataset --batch-size 10
```

CLI 目录上传默认忽略上传根目录和任意嵌套目录中的 AppleDouble
`._*` 与 `.DS_Store`；普通点文件、`.gitattributes` 和 `.gitignore` 不会被宽泛
排除。显式把这些 macOS 元数据作为单文件上传会在认证前失败，避免将
与 Git LFS 后缀规则重合的 sidecar 误提交为普通 blob。该默认仅属于 CLI；
Python SDK 的 `ignore_patterns` 仍完全由调用方控制。

`--ignore` 使用逗号分隔的 Unix shell 风格通配符，作为上述默认规则的追加项。
通配符整体使用双引号时，
不要再给 `*` 添加反斜杠；CLI 会在远端调用前拒绝 `\*`。例如，递归忽略隐藏
内容、JSON 文件和以 `output` 开头的内容：

```bash
atomgit upload ./data --repo-id user/my-dataset \
  --ignore ".*,**/.*,*.json,**/*.json,output*,**/output*" \
  --repo-type dataset
```

CLI 的文件数量和大小统计会先应用与上传相同的默认及用户追加
忽略规则，并排除 HF 断点
续传元数据，因此展示值与实际上传集合一致。底层的 `Upload N LFS files` 仍只
统计过滤后需要传输的 LFS 文件，不包含随提交发送的普通小文件。

上传总时间不设限。`--timeout N` 设置默认网络请求等待超时，LFS pointer 确认也使用
N 秒，不要求整个请求在 N 秒内完成；HF 1.1.7 的写入等待仍为 60 秒。
原生 SDK 的 `timeout` 和历史上传 API 的 `upload_timeout` 采用相同语义。N 大于 15
时，提交后的 pointer 确认故障可能比旧版本等待更久，但不会再被隐藏上限提前终止。
兼容变化：显式超时不再终止整次 resumable 上传，依赖旧总时限行为的脚本需相应调整。

resumable 的 Git LFS 预上传不会无限重试。认证、权限、仓库不存在、LFS 存储或
带宽额度不足，以及被拒绝的 Batch 请求会立即停止；限流、服务暂不可用、超时和
连接失败最多尝试三次，使用有上限的退避并遵循有效的 `Retry-After`。失败时 SHA-256、LFS 模式和已确认批次均保留，未确认
对象不会标记为已上传或已提交；外部条件恢复后可重新执行同一命令继续。

resumable 还会在上传数据实际被网络请求持续消费时监测单个 LFS 连接。只有对象先
形成可靠的自身或同伴速度基线，随后连续三个 30 秒窗口显著降速，并且预计更换连接
至少节省一半剩余时间时，才会只关闭并重建该对象的请求。basic PUT 会从对象起点
重传；multipart 仅保留同一上传 action 中已经由服务端返回有效 ETag 的 part。每个
对象最多更换三次，并使用退避；新连接不仅需要比原慢流快至少 2 倍，有稳定同伴
时还必须达到同伴基线的 70%。所有对象同时变慢时最多运行一个
保守探针，避免重连风暴。首次窗口就慢、没有可信基线或预计无收益的连接不会仅因
速度低而自动更换。HTTP 结果不明确时会先重新查询 LFS Batch，已存在的完整 OID
不会重复上传。

所有 CLI 上传模式都会保留原有 LFS 对象传输，但把提交中的 LFS 引用固定序列化为
标准三行 Git LFS pointer，最后一行以且仅以一个 LF 结束。提交返回后，CLI 使用
AtomGit V5 contents API 按精确 commit SHA 读取原始 Git blob 并逐字节验证，不会
下载大型 LFS 对象；pointer 不规范或无法验证时命令返回失败，不打印上传成功。
每个尚未确认的 pointer 最多读取三次，失败后依次等待 2 秒、4 秒；重试只重复
同一 commit 的只读确认，不会重复上传对象或创建 commit。三次均无法确认时仍安全
失败，这表示客户端未能确认成功，不等于已经证明远端 pointer 内容错误。
该逻辑对所有仓库统一生效，不按仓库名称适配。它防止新 CLI 上传继续产生脏克隆，
但不会自动改写已有提交或修复历史中已经不规范的 pointer。

为避免 Hugging Face 上传实现读取选定路径之外的内容，上传文件、上传目录根路径
以及目录树中的文件、目录或失效符号链接都会在读取登录凭证和发送远端请求前被
拒绝。`--ignore` 不能绕过这项安全检查；需要上传目标内容时，请先将其复制为上传
目录内的普通文件。

#### 进阶示例

```bash
# 上传到仓库内 sub/ 目录、dataset 类型，忽略 .tmp 文件
atomgit upload ./data --repo-id user/my-dataset \
  -p sub/ -r dataset -i "*.tmp"

# 目录默认断点续传（中断后再次执行同一命令即可续传）
atomgit upload ./large-model --repo-id user/large-model \
  --num-workers 4 -t 1800

# dataset 使用相同的断点续传接口，底层自动走 AtomGit 兼容路由
atomgit upload ./large-dataset --repo-id user/large-dataset \
  --repo-type dataset --num-workers 4 -t 1800

# 显式允许检测到不安全 regular 模式时配置仓库级 Git LFS 并恢复当前批次
atomgit upload ./large-dataset --repo-id user/large-dataset \
  --repo-type dataset --auto-configure-lfs

# 默认断点续传也可上传到仓库子目录
atomgit upload ./large-model --repo-id user/large-model \
  --path-in-repo checkpoints/ -t 1800

# 单文件无本地拷贝，直接上传到仓库内指定路径
atomgit upload ./weights.bin --repo-id user/model -p checkpoints/

# 清空 AtomGit 产生的本地缓存
atomgit cache clear
```

> ⚠️ 注意：CLI resumable 目录上传会在
> `~/.cache/atomgit/upload-projections/` 建立按源目录、仓库、revision 和远端前缀
> 隔离的稳定投影，避免不同仓库误用同一份 HF 元数据。HF large-folder 接口本身
> 没有 `path_in_repo`，投影也用于表达远端前缀。文件优先使用硬链接；跨文件系统
> 无法硬链接时仅创建符号链接，不复制源文件字节；若两种链接均不可用则安全失败。
> 目标仓库必须先由 `atomgit repo create` 或平台界面创建；上传会在所有批次前
> 通过 AtomGit V5 仓库/分支详情接口做一次只读校验，不会借用 HF
> large-folder 的隐式建仓请求。
> 程序内部按 20 个文件顺序分批上传，不改变源目录内容。commit 限流会遵循
> `Retry-After` 或指数退避；响应超时后先核对远端对象，确认未提交才按
> `20 → 10 → 5 → 2 → 1` 降批。连续失败会退出并保留断点元数据，而不是无限
> 重试。large-folder 仍不支持单一提交说明，需指定
> `--message`（自动普通上传）或显式 `--no-resumable`。HF 底层要求 `repo_type`，
> CLI 未指定时自动使用 `model`。
> `--auto-configure-lfs` 启用后，CLI 会在服务端把文件判定为 LFS 后、对象预上传或
> 引用提交前，从安全扩展名生成 `*.ext filter=lfs diff=lfs merge=lfs -text`，检查
> 目标 revision 根目录 `.gitattributes` 并仅追加缺失或被后续规则覆盖的规则。CLI
> 会显示规则作用于整个仓库，保留已有属性字节，使用当前提交做并发保护，并只提交
> `.gitattributes`。同一命令内已确认的扩展名不会跨批重复检查。对于服务端把超过
> 1 GB 的文件错误判定为普通 Git 文件的情况，该选项仍会先补齐规则、刷新上传模式
> 并重试当前批次。无安全扩展名、规则仍不生效、权限失败或并发状态无法确认时停止，
> 不生成宽泛规则或无限提交；已有哈希和已提交状态不会被清除。
> 该主动配置路径已在授权测试仓库完成真实验收：缺失规则会先追加再上传；同一命令
> 重跑时已提交文件被断点跳过，已有规则只检查不重复提交。

> 显式 `--no-resumable` 会直接读取源目录，不建立上述完整投影；普通 LFS 上传
> 默认最多并行传输 5 个文件，并会跳过服务端已有的相同内容。它不提供单个文件
> 的中途续传。锁定 HF 版本会对过滤后超过 30 个文件的普通目录上传给出大目录
> 提示，超过 200 个文件时使用 warning 级别；这不是立即失败，但一次性哈希和
> 提交大量文件可能在长时间运行后失败。超大目录应优先按可重试的小批次顺序
> 上传。详见 [常见问题](docs/faq.md) 和
> [上传实现分析](docs/upload_command_analysis.md)。

> 当前实现通过 `HfApi(endpoint="https://hub.atomgit.com", token=...)`
> 固定 AtomGit 端点并认证，已分别对 model 和 dataset 完成约
> 399 MB 文件的真实中断、恢复和 SHA-256 校验。AtomGit 不会创建请求的非默认
> 分支，因此 CLI 不依赖 HF 隐式建分支。先运行
> `atomgit repo branch create REPO_ID BRANCH --from main`，再使用
> `upload --revision BRANCH`。原生 `AtomGitClient` 可使用同一已验证分支；历史
> `atomgit_hub.upload_folder` 仍保持 `main`-only。详见
> [上传实现分析](docs/upload_command_analysis.md)。V5 分支写入若遇到超时、
> 网络中断或服务端错误，CLI 会读取目标分支恢复结果；4xx 拒绝不会按已有分支
> 误报成功。创建前会将 `--from` 解析为不可变提交，并在创建后校验目标分支
> 指向同一提交；无法验证时会明确提示远端状态未知。

#### 错误处理

上传失败时，CLI 会给出语义化错误类型与可执行建议，例如：

```
上传文件失败[仓库不存在]
💡 建议: 仓库 user/repo 不存在或为私有且无访问权限。请检查 repo_id/repo_type，或先 atomgit login。
```

涵盖：认证失败 / 权限不足 / 仓库不存在 / 受限仓库 / 仓库已禁用 / 分支不存在 / 请求参数错误 / 请求超时 / 网络连接失败 / LFS 指针验证失败等情形。底层异常原文不会输出，以免泄露 token、Authorization 头或签名 URL。

### 3. 下载

#### 下载整个仓库

#### 下载到当前目录

```bash
atomgit download your-username/your-model-name
```

#### 下载到指定目录

```bash
atomgit download your-username/your-model-name -d ./models/
```

当 model 与 dataset 路由需要明确区分时，可指定仓库类型：

```bash
atomgit download your-username/your-dataset -d ./data/ --repo-type dataset
```

未指定 `--repo-type` 时会安全探测两种路由；若两种路由返回不同内容，命令会
要求显式选择，避免混合下载错误仓库的数据。

目标目录中已存在的文件默认直接跳过，不会校验大小或内容，也不代表断点续传。
需要重新下载并覆盖已有文件时使用 `--force`：

```bash
atomgit download your-username/your-model-name -d ./models/ --force
```

需要验证本地文件与仓库内容一致时使用 `--verify-checksum`：

```bash
atomgit download your-username/your-model-name -d ./models/ --verify-checksum
```

该选项会校验已有文件而不重新传输；新下载或 `--force` 下载的内容会在替换目标
文件前完成校验。普通 Git 文件使用 Git blob SHA-1，LFS 文件使用内容 SHA-256。
checksum 不匹配或服务未提供受支持的强校验值时命令会失败，不会用错误内容替换
已有文件；已有文件不匹配时可结合 `--force --verify-checksum` 重新下载并校验。
仓库中的嵌套非 ASCII 文件名同样支持 checksum 校验和断点续传。

大文件下载中断后需要保留进度时使用 `--resume`：

```bash
atomgit download your-username/your-model-name -d ./models/ --resume
```

未完成数据保存在权限受限的 AtomGit 缓存中；再次执行相同命令会从已保存字节
继续。完成后自动校验仓库 checksum，再原子替换目标文件并清理缓存。该选项不会
改变默认策略：目标文件已经存在且未使用 `--force` 时仍直接跳过。

需要删除远端已经移除的本地文件时，显式使用 `--prune`：

```bash
atomgit download your-username/your-model-name -d ./models/ --prune
```

清理范围由 AtomGit 缓存中的私有下载 manifest 限定：只删除此前由整仓下载实际
写入并登记、且本次完整远端文件清单中已不存在的普通文件。命令不会扫描或删除
未登记文件、目录、符号链接；首次对已有目录使用 `--prune` 也不会把跳过的本地
文件自动纳入管理。全部下载成功后才执行清理并原子更新 manifest。默认不清理，
`--force` 仍只表示重新下载和覆盖，不会删除本地多余文件；首次使用时可执行一次
`--force --prune`，将成功重下的远端文件建立为受管理基线。普通下载遇到 manifest
不可用时会警告但仍完成下载，这些文件不会被后续清理；显式 `--prune` 则失败关闭。
同一仓库、类型和本地目录的整仓下载会独占 manifest 事务；并发命令会在传输或
清理前失败并提示等待当前任务完成，不会覆盖彼此的受管理文件记录。

#### 只下载一个文件

仓库内文件名可以包含子目录；本地会保留该相对目录结构：

```bash
atomgit download-file your-username/your-model-name weights/model.bin -d ./models/
```

dataset、强制覆盖和匿名下载与整仓命令使用相同策略：

```bash
atomgit download-file your-username/your-dataset data/sample.csv \
  -d ./data/ --repo-type dataset --force --verify-checksum
```

### 4. 其他命令

#### Zsh 命令补全

官方安装器在活动 conda + Zsh 环境中默认启用补全。可手动执行：

```bash
atomgit completion install --shell zsh
```

补全候选直接来自当前 Click 命令树，新增命令无需维护另一份列表或重新安装补全
脚本；支持命令、嵌套子命令、选项、枚举值和本地路径，不会补全远端仓库、分支或
文件名，也不会在按 Tab 时读取 token 或访问网络。管理命令包括：

```bash
atomgit completion show zsh
atomgit completion uninstall --shell zsh
```

安装只管理当前 `CONDA_PREFIX` 下的 adapter、`activate.d` hook 和 `deactivate.d`
hook；激活环境时加载该环境的实时 schema，停用时先解除 `_atomgit_completion`
和 `compdef` 绑定。非 conda 环境不会写全局补全或 `.zshrc`。若检测到 1.1.0 的
旧版全局补全，会先说明迁移内容并要求明确确认；迁移保留 `.zshrc.atomgit.bak`
和全部无关配置。受控路径中的符号链接、非普通文件或并发修改会失败关闭，安装
中途失败会回滚本次环境文件。

#### 列出当前用户可访问的仓库

```bash
atomgit repo list
```

该命令需要先登录，输出仓库 ID 和服务返回的可见性信息。

#### 退出登录

```bash
atomgit logout
```

#### 显示配置信息

```bash
atomgit config-show
```

Git 集成状态会分别检查 `atomgit.com` 与 `hub.atomgit.com`：两者都有托管 helper
才显示“已启用”，只配置一个会显示“部分启用”并列出缺失域名；输出不会展示
helper 命令或 token。

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

# 创建公开 model 仓库（创建后通过 V5 接口校验可见性）
atomgit repo create your-username/your-model --type model --public

# 幂等自动化：仓库已存在时也返回成功
atomgit repo create your-username/your-repo --type model --private --exist-ok
```

默认情况下仓库已存在会返回失败，避免误报“新建成功”；仅在明确需要幂等行为时
使用 `--exist-ok`，成功提示会显示“已存在或已创建”。

必须明确指定 `--private` 或 `--public`。所有创建请求都会先安全地要求 HF 创建
私有仓库，再通过 V5 接口把仓库收敛到明确请求的公开或私有状态并读取验证；如果
转换或验证失败，命令返回失败且不会自动删除，但远端状态可能未达到目标，必须
立即检查并设置目标可见性。已有仓库可单独修改：

```bash
atomgit repo visibility your-username/your-repo public
atomgit repo visibility your-username/your-repo private
```

`--exist-ok` 命中已有仓库时仍会确保并验证命令明确请求的公开或私有状态；只有
最终 GET 返回的可见性与请求一致，命令才会成功。

#### 永久删除仓库

删除不可恢复，必须登录并通过 `--confirm` 原样重复仓库 ID：

```bash
atomgit repo delete your-username/your-repo \
  --confirm your-username/your-repo
```

命令会先读取并确认目标仓库，再调用 AtomGit V5 删除接口，最后重新读取同一地址；
只有远端返回 404 才报告成功。确认值缺失或不完全一致时不会发送 API 请求。若删除
响应丢失但随后验证仓库已不存在，命令仍可确认成功；无法验证时返回非零并明确提示
远端状态未知。原生 `AtomGitClient.delete_repository()` 通过同一 usecase 提供相同的
确认和最终状态验证；历史 `atomgit_hub` 兼容接口不提供删除函数。

## SDK使用方法

AtomGit 同时提供两种 Python 接口：

- 原生 `atomgit.interfaces.sdk.AtomGitClient` 面向新开发，与 CLI 的通用远程能力
  共享 usecase，返回结构化 `OperationResult`；
- 历史 `atomgit_hub` 保留类似 `huggingface_hub` 的函数、签名、返回值和异常，
  用于兼容既有调用方，其能力面有意小于原生客户端。

### SDK功能特性

- **原生对称接口**：认证、仓库、上传和下载通过 `AtomGitClient` 与 CLI 共享业务层
- **历史兼容接口**：`atomgit_hub` 保留已有 HF 风格调用合同
- **共享配置**：CLI 和两种 SDK 接口使用相同的认证和配置文件
- **统一安装**：安装 `atomgit` 包即可使用 CLI 和两种 Python 接口

### 1. SDK导入

```python
# 新功能开发：使用与 CLI 共享 usecase 的原生客户端
from atomgit.interfaces.sdk import AtomGitClient

client = AtomGitClient()
result = client.list_repositories()

# 兼容既有 HF 风格代码：从 atomgit_hub 导入
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

以下函数式示例均属于历史 `atomgit_hub` 兼容接口。原生客户端还提供
`login/logout/whoami`、仓库列表/可见性/分支/删除、单文件上传以及带
checksum/resume/prune 的下载方法。

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

配置文件保存在 `~/.atomgit/config.json`，包含 token、登录时验证的用户名和其他设置。Git
集成还会使用 `~/.atomgit/git-helper-state.json` 保存登录前两个 AtomGit 域名的
helper 配置；该状态文件不会写入本次登录 token，并使用 `0600` 权限。既有
helper 值会按原样保存，因此不应在 Git helper 命令中内嵌秘密。托管 helper
通过当前 Python 解释器启动，并安全引用包含空格的 Windows 或 POSIX 路径。

## API端点配置

工具已预配置为连接AtomGit平台API端点：
- **API端点**：`https://hub.atomgit.com`
- **环境变量**：`HF_ENDPOINT=https://hub.atomgit.com`

此配置在程序启动时自动设置，用户无需手动配置。

## Git集成功能详解

### 自动配置

当你使用 `atomgit login` 登录成功后，工具会自动配置Git凭证，让你可以直接使用标准Git命令操作AtomGit仓库。
从旧版本升级后请重新运行一次 `atomgit login`，以缓存已验证用户名并生成离线
Git helper；缺少缓存用户名时 helper 不会返回 token。

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
- Git helper 只读取登录时缓存的用户名和 token，不调用远程身份 API
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
- **上传失败语义化提示**：CLI 会把异常归类为「认证失败 / 权限不足 / 仓库不存在 / 受限仓库 / 仓库已禁用 / 分支不存在 / 请求参数错误 / 请求超时 / 网络连接失败 / LFS 指针验证失败 / 未知错误」并附可执行建议；401 建议重新登录，403 建议检查仓库或命名空间权限；服务端原始指针无法按返回提交确认时不会误报上传成功
- 错误输出提供安全的分类和操作建议，不回显可能含凭据的底层异常原文

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
├── src/
│   ├── atomgit/         # CLI、SDK domain 与兼容 facade
│   └── atomgit_hub.py   # 历史顶层SDK兼容代理
├── requirements.txt     # 依赖包
├── setup.py             # 包安装配置
├── deploy.sh            # 构建/安装/发布脚本
├── install.sh / uninstall.sh # 官方普通用户安装与卸载入口
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
python tests/test_revision_rejection.py      # 安全 revision 转发与非法 ref 拒绝
python tests/test_upload_ignore.py          # 忽略模式
python tests/test_upload_resumable.py       # 断点续传
python tests/test_upload_file_no_copy.py    # 单文件无拷贝
python tests/test_upload_error_classify.py  # 错误分类
python tests/test_upload_error_handling.py  # 错误处理集成
python tests/test_git_credentials_isolation.py  # Git helper 隔离与恢复
```

现有自执行脚本由隔离 pytest 矩阵统一收集。安装开发依赖后运行强制防回退门禁
`python tests/run_cli_baseline.py`；完整说明见 [docs/testing.md](docs/testing.md)。

## Python版本兼容性

`setup.py` 声明支持 Python 3.9+，列出的目标版本包括：

- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13

当前 wheel 已在项目 Python 3.10 conda 环境中通过自动化隔离安装和入口冒烟。
仓库尚无覆盖 Python 3.9–3.13 的完整 CI/conda 版本矩阵，因此这些版本除当前
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

1. 代码兼容Python 3.9+
2. 运行兼容性测试
3. 更新相关文档

## 联系我们

- 邮箱：JoyJeeo@163.com
- 项目地址：https://github.com/JoyJeeo/atomgit_cli
- 问题报告：https://github.com/JoyJeeo/atomgit_cli/issues
