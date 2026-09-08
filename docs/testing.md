# 测试指南

## 当前状态

仓库保留可直接执行的 `tests/test_*.py` 测试脚本，内部使用自定义 `check()`
聚合断言，并通过进程退出码表示结果。`pytest_offline_scripts.py` 会把每个脚本
收集为独立 pytest case，并在隔离子进程、临时 HOME 和临时 Git 配置中运行。

现有测试覆盖 CLI、SDK、配置、Git helper、下载传输、上传参数透传和
打包安装，包括：

- 进度条开关；
- 仓库内路径；
- model/dataset 类型；
- revision；
- ignore patterns；
- 目录默认 resumable、显式普通模式、worker 和 path-in-repo 稳定投影；
- resumable 既有仓库只读校验、隐式建仓屏蔽、超大 regular 文件保护和结构化
  子进程错误；
- 单文件直接上传；
- 上传错误分类。

token 校验、持久化、损坏配置恢复、logout、配置权限、Git credential helper
隔离、URL 重定向、路径穿越、HTTP 响应完整性、临时文件清理和 wheel 安装均有
隔离离线测试。当前完整矩阵包含 93 个 pytest case（自执行脚本内部可包含多个
聚合断言）。建仓、ignore、下载权限矩阵等远程路径已有一次受控
验收证据。维护者已授权两个固定测试仓库可直接重跑连线测试；其他仓库或
操作仍需单独授权。

能力 ID、行为不变量、证据映射和完整阻断规则见
[开发底线](development_floor.md)。`tests/development_floor_contract.py` 登记
27 个能力和 116 条不变量，`tests/test_development_floor.py` 验证每个离线测试、
文档和工作流标记都保持关联。

## 环境

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate atomgit_cli
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

测试不得读取真实的 `~/.atomgit/config.json`。离线测试应替换配置访问并使用
明显为假的 token。

## 运行现有测试

DoD 强制使用的完整离线基线命令：

```bash
python tests/run_cli_baseline.py
```

该入口使用当前 conda Python 运行完整隔离 pytest 矩阵。需要直接诊断 pytest
收集器时仍可运行 `python -m pytest`，两者覆盖相同的离线脚本集合。

需要诊断单个旧脚本时，仍可直接运行并以退出码为准：

```bash
for test_file in tests/test_*.py; do
    python "$test_file" || exit $?
done
```

如果开发安装尚未完成，应先执行 `python -m pip install -e .`，而不是临时使用
系统 Python。

基础静态检查：

```bash
python -m compileall -q .
git diff --check
```

`pyproject.toml` 统一声明 setuptools 构建后端、当前 `src/` 包映射、Python 3.9
目标和 pytest 收集策略。`requirements-dev.txt` 固定 Black、isort、Ruff 版本；
`python tests/test_packaging_metadata.py` 对现有格式、导入和静态检查债务建立精确
归一化指纹，并要求本 Issue 新增的契约文件立即通过干净策略。清理历史债务时必须
在同一变更中收紧指纹，不允许以全仓格式化混入其他 Issue。
嵌套 infrastructure、lifecycle 和 services 包还由 ownership、src-layout 和 wheel
smoke 三层证据验证，包括历史 facade/API 身份、patch 接缝以及安装后 provenance。

## 测试分层

### 单元测试

验证路径规范化、repo ID 校验、ignore 解析、错误分类和隔离配置文件读写。

### CLI 集成测试

使用 Click `CliRunner`，验证退出码、输出和传给 API 层的精确参数。文件和目录
必须分别覆盖。`tests/test_cli_surface.py` 还会枚举根命令公开的全部子命令，验证
login/logout/whoami/config-show 的认证、Git helper、失败与脱敏分支；所有依赖
均使用 fake，不访问真实 HOME、Git 配置或网络。
`tests/cli_baseline_contract.py` 精确锁定根命令、命令组、叶子命令以及每个参数的
顺序、类型、必填性、默认值、flag 语义、Choice 值和长短选项，并登记每个叶子
命令的成功分派及全部离线测试脚本。`tests/test_cli_baseline_guard.py` 会主动证明
未登记的新命令、新参数、新测试、失效登记、遗漏分派及不可执行的空测试脚本均会
让基线失败。`tests/test_cli_feature_baseline.py` 负责执行精确接口和最小成功分派。

新增功能时必须增加或扩展专项自执行测试；新增公开 CLI 接口时必须同步更新精确
schema 与叶子分派登记；新增 `test_*.py` 时必须加入能力分组。回归失败必须修复
开发代码并重跑完整门禁，不得为了通过而删除或放宽已有断言。只有当前 Issue 明确
记录维护者批准的兼容性破坏时，才允许同步修改旧基线契约。
每个新行为还必须同步登记稳定能力 ID 或不变量 ID，并把专项测试映射到该能力。
完整 baseline 适用于所有开发 Issue；失败或未运行会阻断完成、交付、合并、推送、
发布和继续扩展其他功能。
`tests/test_login_error_semantics.py` 进一步验证登录身份接口的 401、403、429、
5xx、网络、超时和畸形响应分类，且 token 与原始异常文本不会进入输出。
`tests/test_login_response_bound.py` 验证身份响应最多读取 1 MiB 加 1 字节，并在
解码和 JSON 解析前拒绝超限正文。

### 依赖契约测试

直接约束当前安装的 `huggingface-hub==1.1.7` 真实签名。禁止用无约束
`**kwargs` fake 掩盖真实 API 不接受的参数。

运行 `python tests/test_hf_api_contract.py` 可验证当前锁定版本、普通上传、
下载、建仓、`HfApi` 认证和 large-folder 调用签名。该测试只绑定函数签名，
不会发起网络请求；代表性生产调用点的关键字集合从 AST 提取后再绑定真实签名，
避免手写合法参数与实际代码漂移。

### 打包冒烟测试

在隔离环境构建 wheel 和 sdist，并使用 wheel 与默认 PEP 660 editable 安装验证：

- `atomgit --version`
- `atomgit --help`
- `python -m atomgit --help`
- `python -m atomgit.cli --help`
- `import atomgit`
- `import atomgit_hub`

`python tests/test_wheel_smoke.py` 会从临时源码副本离线构建 wheel/sdist，核对
每个预期运行模块，并分别安装到不继承仓库路径的临时 venv；安装后会逐一运行全部
顶层命令及 `repo create` 的帮助入口。该脚本也包含在标准 pytest 矩阵中，不会在
工作树生成构建产物。当前 `src/` 包映射由 `pyproject.toml` 与 `setup.py` 一致
声明，editable 隔离验证直接使用默认 setuptools PEP 517/660；同一组合同精确
核对 source、顶层 SDK 兼容代理、editable、wheel 和 sdist 的来源与模块集合。

### AtomGit 远程测试

远程测试默认关闭，只有用户明确授权后才运行。2026-08-06 起，用户已持续
授权使用已提供的测试登录，且仅可对以下两个专用仓库直接运行连线测试：

- `weixin_52273949/test_model`；
- `weixin_52273949/test_datasets`。
- `weixin_52273949/atomgit-cli-dataset-20260804-003221`（正向 dataset 写入目标）。

该授权不包括其他仓库、删除、发布或输出 token。`test_datasets` 仅保留为只读诊断
样本；正向 dataset 写入使用新增的固定仓库。连线测试必须使用：

- 专用测试 token；
- 唯一且可识别的一次性仓库名，或上述明确授权的固定仓库；
- 非生产仓库；
- 命令退出码；
- 下载回读和 SHA256 或 `cmp` 内容证据。

不能因为 CLI 打印“上传成功”就判定端到端通过。

截至 R8（2026-08-25）的既有授权验收使用隔离 HOME 和环境变量 token，验证了：

- 公开 model 内容匿名下载成功并与上传源 SHA-256 一致；
- 私有 dataset 匿名下载失败、认证下载成功且 SHA-256 一致；
- `path_in_repo` 中保留文件存在，`*.tmp` 与 `logs/*` 哨兵远端不存在；
- dataset 建仓和传输必须复用 AtomGit 的 model 兼容路由；
- 私有 model 与 dataset 均以 399,300,506 字节文件完成 CLI 超时中断、恢复、
  下载与 SHA-256 一致性验证；
- HF `private=False` 创建会假成功为私有仓库；CLI 公开建仓因此先按私有创建，
  再通过 V5 PATCH 和 GET 校验可见性。历史 `atomgit_hub` SDK 仍拒绝公开建仓，
  原生 `AtomGitClient` 使用与 CLI 相同的收敛与验证 usecase；
- 多层 ID 被正确转换，但测试账号缺少转换后命名空间权限，create/upload 均以
  401 非零退出且未留下仓库；
- 固定测试仓库与多层物理 ID 最终在 model/dataset 路由均为 404。

## 远程测试矩阵

以下为 R8 后综合验收方案。本轮由维护者明确授权启动，执行结果必须在
`.ai/TASK.md` 中记录；方案不扩大两个固定测试仓库之外的授权。

### 范围与安全前提

- 只允许 `weixin_52273949/test_model`、`weixin_52273949/test_datasets` 和
  `weixin_52273949/atomgit-cli-dataset-20260804-003221`。URL、SSH 地址和规范化
  repo ID 必须解析到这三个仓库之一，否则在请求前终止。正向 dataset 写入只使用
  新增仓库，旧 `test_datasets` 不执行写入。
- 使用隔离 HOME、Git 配置、缓存、下载目录和临时目录；token 只能来自环境变量，
  不得读取真实配置或出现在命令、日志和报告中。
- 远端测试文件统一放在唯一的 `e2e/<run-id>/{cli,sdk,legacy}/` 前缀下，不覆盖
  前缀以外的内容。
- 每轮每仓库最多读取一次完整文件树并缓存；上传后对已知目标文件做直接 resolve
  回读，不重复刷新 tree/list。CLI、原生 SDK 和历史接口串行执行，遇到 429 或连续
  超时即停止当前仓库。
- 每项独立执行并记录 CLI 退出码或 SDK 结构化结果、远端 commit/revision、远端
  回读和 SHA-256；成功文案不能单独作为证据。

### 执行顺序

1. 记录分支、HEAD、工作树、完整 diff、Python 和锁定依赖版本。
2. 执行七目录、模块所有权、依赖边、循环依赖、parity registry 和 development
   floor 门禁。
3. 执行 92 case 完整离线基线、`compileall`、`pip check` 和当前工作树的
   `git diff --check`，核对 27 项能力和 116 条不变量。
4. 在隔离环境核对 source、editable、wheel 和 sdist 内容及所有 console、模块、
   公共和历史兼容导入入口。
5. 使用同一组严格 fake 比较 CLI 与原生 `AtomGitClient` 的 usecase、adapter、参数、
   token/revision 策略、结果、错误和全局状态恢复。
6. 对两个授权仓库做只读预检，记录类型、可见性、当前 revision/commit、文件清单、
   CLI/SDK 身份和仓库列表。
7. 对 model 和 dataset 仓库分别执行下表中的受控远程传输矩阵；R8 后新增的
   历史导入、compatibility facade、wheel/sdist/editable 来源检查也必须保留。
8. 远程测试结束后重跑完整离线基线、diff、凭据和构件检查。

### 受控远程传输矩阵

| 场景 | CLI | 原生 SDK | 最低远端证据 |
|---|---:|---:|---|
| 单文件上传 | 是 | 是 | 路径、大小、远端回读 SHA-256 |
| 普通目录上传 | 是 | 是 | 嵌套清单和逐文件 SHA-256 |
| `path_in_repo` | 是 | 是 | 目标前缀准确且根目录无误放 |
| ignore 规则 | 是 | 是 | 保留文件存在且哨兵文件不存在 |
| resumable 上传 | 是 | 是 | 中断、恢复和最终 SHA-256 |
| 单文件下载 | 是 | 是 | 与远端内容逐字节一致 |
| 仓库下载 | 是 | 是 | 文件清单和内容一致 |
| checksum | 是 | 是 | 正确内容通过且破坏内容失败 |
| resumable 下载 | 是 | 是 | 从中断偏移恢复并最终一致 |
| manifest prune | 是 | 是 | 只删除本地 manifest 管理文件 |
| LFS pointer | 是 | 是 | raw blob、OID、size 和结尾 LF |
| CLI 上传、SDK 下载 | 交叉 | 交叉 | 内容及元数据一致 |
| SDK 上传、CLI 下载 | 交叉 | 交叉 | 内容及元数据一致 |

历史 `atomgit_hub` 还要验证适用的下载、目录上传、直接 URL 和 `load_dataset`
接口。已有公开仓库验证匿名下载，已有私有仓库验证认证下载；不为测试改变可见性。

### 本轮明确不执行

- 创建或删除仓库，以及删除后不存在验证；
- 修改仓库可见性；
- 创建或删除远程分支；
- `--auto-configure-lfs` 或仓库级 `.gitattributes` 修改；
- 发布、真实环境卸载、远程测试文件清理；
- 访问两个授权仓库之外的任何仓库。

这些项目在报告中记为“按范围未执行”，不能登记为失败，也不能登记为已通过远程
验证。最终报告分为通过、失败、按范围未执行三组；每项远程通过必须带接口、仓库、
操作结果、revision/commit 和回读校验和。Python 3.9 若环境没有独立解释器，
记录为按环境未执行，不以 Python 3.10 结果替代。

## R8 后执行记录（2026-08-25）

本轮在 `yuto` / `fdaf572`、Python 3.10.20、`huggingface_hub==1.1.7`、
`datasets==4.4.1` 环境执行。离线基线前后均为 `92 passed`；结构 18/18、源布局
11/11、打包元数据 13/13、架构 parity 21/21、wheel/sdist/editable artifact
smoke 49/49，`compileall`、`pip check` 和 `git diff --check` 均通过。

受控远程结果：

- 通过：只读预检确认两个固定仓库均为私有、默认分支为 `main`；model 仓库文件清单
  读取成功；原生 SDK 向 `weixin_52273949/test_model` 的唯一
  `e2e/r8-accept-20260825/` 前缀上传单文件并完成远端回读，40 字节 SHA-256 为
  `fbef9c3d…e0ac060b`；认证 resolve 下载成功（77 字节，SHA-256
  `789192e8…e56946`）。匿名访问同一私有文件按预期返回 HTTP 403。
- 失败：后续文件树查询收到服务端 HTTP 429（Too Many Requests）；没有将限流误判为
  客户端功能失败，也未继续高频重试。
- 按范围未执行：因 429 未完成剩余目录上传、CLI/SDK 交叉传输、resumable 上传/下载、
  checksum/prune、LFS pointer、历史 `atomgit_hub` 远程路径和 dataset 内容传输；
  本轮未改变仓库可见性、分支、`.gitattributes`，也未创建、删除或清理仓库内容。

Python 3.9 未执行：当前环境没有独立 Python 3.9 解释器；wheel 元数据和工具目标仍已
验证 `>=3.9`。

### R8 远程重试记录（2026-08-25）

- `test_model`：低频退避三次后仍出现超时和 HTTP 429，未继续请求。
- `test_datasets`：低频预检第二次成功并确认远端仍为空；随后 SDK 单文件、SDK 目录
  （ignore）和 CLI 单文件上传分别以 `BadRequestError`、结构化 `AtomGitError` 和
  退出码 1 失败，远端文件数保持 0。由于没有成功写入文件，认证下载、checksum、
  resumable、prune 和交叉接口项目没有可验证对象，均按范围未执行。
- 重试后 `python tests/run_cli_baseline.py` 仍为 `92 passed`（105.50s），
  `compileall`、`pip check` 和 `git diff --check` 通过。

上述远程失败保留为服务端限流/固定 dataset 仓库写入约束证据，不作为客户端实现回归
结论；本轮没有创建、删除、清理或改变任何远端仓库状态。

低请求策略重试后，model 仓库单次 SDK 目录上传并对已知目标直接回读通过，22 字节
SHA-256 为 `2bb82b98…f7ad1c5`；dataset 目录上传仍返回 `BadRequestError`，远端没有
新增文件。该次重试后的离线基线为 `92 passed`（94.93s）。

进一步诊断确认客户端的 dataset 兼容路由有效：使用 `repo_type="dataset"` 向可写的
授权 model 仓库执行一次 SDK 目录上传，直接回读 25 字节内容成功，SHA-256 为
`393dacd4…c5bc2e1`。因此固定 `test_datasets` 的 `BadRequestError` 属于该仓库/服务端
状态限制，而非 dataset 到 model 传输映射缺陷。

### 低请求重试策略

为避免测试本身放大服务端限流，后续重试采用以下本地策略：每个仓库最多一次清单
读取并在本轮缓存；上传后只对已知目标文件做直接 resolve 回读；目录场景合并为一次
上传；失败后使用有限指数退避，收到 429 或连续超时即停止该仓库，不重复刷新 tree
清单。该策略只改变测试请求编排，不绕过服务端限额，也不扩大仓库和操作授权范围。

## 已知测试风险

- 依赖签名契约固定在 `huggingface-hub==1.1.7` 和 `datasets==4.4.1`；任一
  版本变更都必须先更新真实签名测试，不能仅放宽 fake。
- 远程 revision 行为不能仅根据 HF 文档推断，必须验证 AtomGit 服务端。
- 测试使用已有仓库无法证明建仓功能成功。
- 非法占位 repo ID 只能证明输入校验有效，不能证明 dataset 功能失败。

AI 专用测试要求见 `.ai/TESTING.md`。

## Issue 测试证据

每个活动 Issue 都要在 `.ai/TASK.md` 记录：

- 完整测试命令；
- `atomgit_cli` 环境；
- 离线或远程测试类型；
- 退出状态和关键结果；
- 未运行检查及原因；
- 剩余风险。

“全部通过”不能替代分层证据。远程能力还必须记录仓库状态、revision、隐私属性
或回读校验和，不能只引用 CLI 成功文案。
本轮正向 dataset 验收目标固定为
`weixin_52273949/atomgit-cli-dataset-20260804-003221`；旧
`weixin_52273949/test_datasets` 仅用于记录服务端拒绝写入，不再计入正向成功率。

## R8 最终执行记录（2026-08-25）

- 发现并修复 SDK 目录上传在 `path_in_repo` 下的目录忽略缺陷：`logs/` 原先按源目录
  相对路径传给 HF，临时投影后无法匹配 `e2e/.../logs/x.log`；现在忽略模式会随投影
  前缀规范化。专项回归 `14/14`，repo type `17/17`，依赖契约 `16/16`。
- 新 dataset 仓库正向远程验证通过：CLI 单文件上传回读 21 字节，SDK 目录上传回读
  并正确排除 `skip.tmp` 与 `logs/x.log`，历史 `atomgit_hub` 目录上传回读成功。
- 下载矩阵通过：CLI 上传到 SDK 下载、CLI checksum、CLI resume、SDK snapshot
  allow-pattern、manifest prune 保留非托管文件、历史 `download_file`、历史
  `snapshot_download` 和 `load_dataset`（1 条记录）均通过。
- 最终离线基线 `92 passed`（103.51s），`compileall`、`pip check`、`git diff --check`
  通过。dataset 正向目标为新仓库；旧 `test_datasets` 不再计入正向验收。
