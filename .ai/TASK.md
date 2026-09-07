# Current Issue Contract

Status: active (D03 LFS pointer request-timeout alignment)

## Successor Development Issue

- Updated: `2026-09-07`
- ID: `LOCAL-UPLOAD-RELIABILITY-20260907`
- Title: `上传可靠性与可观测性修复`
- Type: `bug`, `cli`, `sdk`, `compatibility`, `testing`, `documentation`
- Priority: `P1`（正常长时间上传可能被错误总时限终止）
- Source: `DISC-UPLOAD-RELIABILITY-20260904`，当前收录已确认的 `D01 / UPLOAD-01`
  和 `D03 / UPLOAD-03`；D02 已由 D01 解决并移除。
- Current phase: D01 已完成验收、提交、本地合并及推送；D03 实现、全量验证、最终
  独立审查和维护者人工验收已完成，当前按授权执行提交、合并及推送。
- User authorization: 维护者于 `2026-09-07` 明确要求“将你的修复方案加到开发issue中”；
  本次允许更新本地开发 Issue 和对应讨论交接，取代此前对 D01 写入的禁止。
  维护者随后明确要求“按照开发issue开始开发”，授权 D01 源码、测试、文档与必要
  本地分支修改及离线验证；不创建远程 Issue，不实施 D02–D18。
  维护者又于 `2026-09-07` 确认 D03 采用“LFS pointer 确认统一使用请求超时、HF
  60 秒写入等待保持不变”，并明确要求将方案写入开发 Issue。本次只授权记录 D03
  及同步讨论交接。维护者随后在新对话明确要求“现在开始开发task最新任务”，授权
  D03 的本地任务分支、源码、测试、文档修改及离线验证；不授权提交、合并、推送或
  远程操作。维护者随后明确要求“自己再完整测试一下，确认基线测试没有问题后，
  提交推送”，据此在复验通过后接受 D03，并授权提交、本地合入 `yuto` 及仅推送
  `github/yuto`；不推送任务分支。
- Delivery mode: 维护者明确要求“自己验证一下，没有问题就提交推送”。复验通过后，
  授权 D01 提交、本地合入 yuto、仅推送 github/yuto 和必要交付记录；不推任务分支。
  原有五份开发规范变更保持未提交。远程上传、PR、标签、发布仍未授权。
- D03 delivery mode: 复验通过后提交任务分支、本地 no-ff 合入 `yuto`、仅推送
  `github/yuto` 并核验远端一致；任务分支保持本地，不执行其他远程操作。
- Next exact action: 提交 D03、本地合入 `yuto`、仅推送 `github/yuto` 并核验。

### Repository Reconciliation

当前分支 `codex/d03-lfs-pointer-timeout`，基于与 `github/yuto` 一致的
`yuto@11ffbe524a0afabb364fc007ff9a0601b9901f3f`，只有当前 worktree。Git 已包含
R9 实现提交 `5c108f6`、合并
`4298043` 和交付记录 `2c5d351`，以及 D01 任务提交 `a4d7216`、合并 `720d641`
和交付记录 `11ffbe5`；
旧记录也注明实现完成、人工接受及无下一步。因此 R9 不作为新的活跃开发任务。
下方历史正文保留，不据其旧的 active/未实现描述恢复执行。历史矛盾的完整整理仍属于
D18；本次仅建立清晰的当前入口，没有将 D18 标记为已解决，也未核验新的远程状态。

### D01 Objective And Evidence

上传总时间不设限；请求超时只约束网络等待，不能终止仍在正常进行的长时间上传。

当前 CLI 省略 `--timeout` 时显示总时限不限，却在
`src/atomgit/interfaces/cli/commands/transfers.py` 将默认请求值 300 传给共享调用，
经 `interfaces/cli/runner.py` 成为 `upload_timeout`。
`adapters/upload/service.py` 用它创建 `time.monotonic() + upload_timeout`，
`adapters/upload/resumable.py` 按剩余时间等待并终止子进程。原生 SDK 的 resumable
路径也经 `adapters/huggingface.py` 到达同一上传服务。

证据来自当前源码、相关测试和已安装依赖的只读核对；并非本轮真实上传复现。
现有 `docs/faq.md`、`docs/upload_command_analysis.md` 和 CLI 帮助与默认执行不一致。

### D01 Accepted Behavior And Compatibility Migration

| 使用方式 | 上传总时限 | 默认网络请求等待超时 |
|---|---|---|
| 省略 `--timeout` | 不设限 | 300 秒 |
| `--timeout N` | 不设限 | N 秒 |

- CLI、原生 SDK 与历史上传接口的对应参数只控制请求等待；尽量保留参数名称、
  签名、调用方式、返回值和错误包装，不能让 SDK 暗中保留同一错误总倒计时。
- 明确的行为迁移：旧的显式 `--timeout N` / 对应 resumable API 参数会限制上传
  总时间；新行为取消该限制。依赖旧行为的脚本受影响，必须在受影响文档中明确说明。
- 当前 `huggingface-hub==1.1.7` 默认客户端使用
  `httpx.Timeout(DEFAULT_REQUEST_TIMEOUT, write=60.0)`；已安装 HTTPX 为 `0.28.1`。
  连接、读取、连接池等待采用配置值，写入等待仍为 60 秒；部分控制面请求使用
  `min(request_timeout, 15)`。这些既有细分保护保留，不宣称全部请求统一等待五分钟。
- 请求超时按网络等待阶段判断，不要求整个请求在 N 秒内完成，也不是全局上传进度
  看门狗。参考：<https://www.python-httpx.org/advanced/timeouts/>。
- D01 改变了 D02 的讨论前提；在 D01 接受时，细分参数与控制面展示仍留待 D02/D03
  逐项讨论。后续 D02、D03 决定见各自章节。

### D01 Implementation Scope

1. 在共享上传服务保留请求超时计算，取消从请求值生成上传总截止时间。
2. 子进程不再因累计运行达到请求超时值而被杀死；保留进程隔离、明确结果协议、
   异常退出处理和取消清理。子进程退出但没有有效成功结果必须失败。
3. 重试、LFS 预上传和慢速连接恢复不再受该错误总截止时间限制；保留既有错误分类、
   重试次数、退避上限、慢速判定、替换收益、冷却和次数上限。
4. 仅清理本次取消总计时后失去用途的参数、分支和说明；保留无关的等待、超时和
   恢复逻辑，不新增计时器、后台看门狗、依赖或抽象。不采用最初提出的全链路 `None`
   改造：取消总时限后，请求超时继续使用正常数值并保留合法性校验。
5. 核对 CLI、原生 SDK、历史 API、普通目录与单文件的实际调用；保留全局请求超时和
   进度状态在成功、失败后的恢复，以及临时资源、断点数据和源文件保护。
6. CLI 显示“上传总时限：不限”和“默认网络请求等待超时：N 秒”；删除帮助中的
   “resumable 同时作为总时限”，同步 FAQ、上传分析及受影响 SDK 文档和已有变更说明。
   解释请求路径可能存在更具体限制，不提前实现 D03。

### Affected Capability IDs

本次文档记录涉及 `FLOOR-REGISTRY`；后续 D01 实施涉及既有
`CLI-SURFACE`、`CLI-DISPATCH`、`UPLOAD-FILE`、`UPLOAD-FOLDER`、`UPLOAD-RESUMABLE`、
`UPLOAD-LFS`、`UPLOAD-LFS-RECOVERY`、`SDK-UPLOAD`、`RUNTIME`、`DEPENDENCY-CONTRACT`、
`ARCHITECTURE`、`ERROR-REDACTION`、`PORTABILITY` 和 `FLOOR-REGISTRY`。
实施时将下述不变量及回归证据登记到现有能力与 CLI 台账，不增加未经要求的新能力。

### Protected Existing Invariants

- 请求超时保护、不可重试错误的失败、可重试错误的既有次数和退避限制继续有效。
- LFS 重连的慢速、收益、冷却和替换上限继续有效；只移除上传总截止时间约束。
- Ctrl+C 能停止本次上传并清理子进程；失败不误报成功，已有断点保持可恢复。
- 凭证脱敏、进程隔离、源文件和缓存安全、临时资源存活周期、全局状态恢复不退化。
- 除本节明确的总时限迁移及提示外，原有 CLI/SDK 参数、结果、导入、补丁接口和
  model/dataset、revision 行为保持兼容。
- `huggingface-hub==1.1.7`、`datasets==4.4.1`、Python >=3.9 兼容合同与七目录架构不变。

### New Or Changed Invariants

- 默认和显式请求超时均不产生上传总截止时间；单批与多批累计时间不触发总计时终止。
- `--timeout N` 与对应 SDK/API 参数控制请求等待，按既有网络阶段覆盖规则生效。
- CLI 显示、帮助、API 说明、执行层和跨入口回归对超时语义保持一致。
- 旧的“显式总时限终止进程”测试按明确的兼容迁移替换，同时补足请求超时、故障退出、
  有限重试和取消清理证据；不能仅删除测试来通过基线。

### Focused Tests And Evidence

| 场景 | 必须证明的结果 |
|---|---|
| 从默认 CLI 入口模拟累计上传超过 300 秒 | 不创建总截止时间，不杀死健康上传进程 |
| 显式较小请求超时、持续传输、多批累计耗时 | 不按上传总时间终止，后续批次继续 |
| 注入读取/写入超时 | 进入实际错误处理，不以仅抛出模拟异常代替链路验证 |
| 连续可重试错误和不可重试错误 | 按既有次数耗尽退出或直接失败，不无限重试 |
| Ctrl+C、子进程异常退出、无有效结果 | 正确结束、清理子进程、不误报成功 |
| CLI、原生 SDK、历史 API 的默认和显式参数 | 请求语义与实际调用一致，普通/单文件不退化 |
| 成功、失败及前置失败 | 请求超时、进度状态和临时资源正确恢复 |
| 当前锁定 HF 客户端与控制面覆盖 | 默认请求值、write=60 和 min(N,15) 未被误改 |

优先扩展 `tests/test_upload_validation.py`、`tests/test_upload_resumable.py`、
`tests/test_resumable_recovery.py`、`tests/test_sdk_upload_timeout.py`、
`tests/test_lfs_preupload_policy.py` 及实际相关的慢速恢复、CLI/SDK、架构与依赖契约测试。
用可控时钟与模拟进程覆盖长时间场景；取消清理还需真实本地子进程的离线证据。
不真实等待五分钟，不访问 AtomGit。新增测试若确有必要，必须登记到完整测试清单和能力台账。

### Implementation Phases And Acceptance

1. 激活后先冻结现有调用、依赖与兼容契约，添加能暴露错误总计时的回归。
   验证：旧实现失败且原因确为总计时，明确记录迁移的旧测试。
2. 修复共享服务、进程执行及恢复链路，贯通 CLI/SDK。
   验证：上述长时间、请求超时、有限重试、故障退出及取消清理专项通过。
3. 同步帮助、文档和能力/测试/结构契约；执行完整离线门禁及独立审查。
   验证：实现、文档与新旧行为迁移一致，无未解决阻塞发现，再进入人工验收。

所有实施命令必须在 `atomgit_cli` conda 环境执行：

```bash
python tests/run_cli_baseline.py
python -m compileall -q .
python -m pip check
git diff --check
```

另按 `.ai/DOD.md`、`.ai/TESTING.md`、`.ai/REVIEW.md` 执行适用依赖签名、结构、
打包、脱敏、临时资源及平台检查。任何未通过或未执行的完整基线阻止实施 Issue 完成与交付。

### Complete Baseline Evidence And Residual Risks

所有验证均在 `atomgit_cli` conda 环境离线执行：

- 实施前基线：`python tests/run_cli_baseline.py`，93 passed in 98.60s。
- 红灯：新回归在旧实现上 2 failed，分别复现健康上传被请求时限终止、CLI 将请求值
  传为进程等待上限。旧实现和新回归的差异已确认。
- 首轮专项：上传/恢复/LFS 六项通过；跨入口及结构专项通过。
- 首次完整修复后基线：92 passed、1 failed，定位为 `test_upload_batching.py` 仍锁定
  旧的跨批次总时限。已按本 Issue 明确兼容迁移改为验证请求值保留、两批均无限时等待。
- 审查修正：请求超时回归同时断言错误分类，避免其他异常冒充超时通过；补充子进程
  报告成功后异常退出的失败回归。三项修正专项 3 passed in 15.18s。
- 最终完整基线：`python tests/run_cli_baseline.py`，**93 passed in 104.82s**；包含
  源码/打包、CLI、SDK、架构、依赖、开发底线及全部既有离线脚本。
- `python -m compileall -q .`、`python -m pip check`、`git diff --check` 均通过；
  变更 Python 文件通过 Python 3.9 语法解析，真实 HF `upload_large_folder` 签名已核对。
- `fork`、`spawn`、`forkserver` 的真实本地子进程验证覆盖成功、失败、崩溃、无结果、
  非法结果、成功后崩溃及 KeyboardInterrupt 清理；CLI/SDK 默认及显式超时覆盖模拟
  累计 602 秒以上的多批上传，HF 客户端网络阶段超时与全局恢复已验证。
- 已注册 `RESUMEUP-004`，不变量 117 -> 118；脚本数仍为 93，未删减测试清单。
  旧总时限测试迁移保留失败与取消保护。格式台账按实际缩减更新：Black 413 -> 410，
  isort 90 -> 89，Ruff 44 不变；没有放宽既有债务上限。
- 既有五份规范文档变更通过哈希比对完整保留，新增差异凭证模式与生成物检查通过。
- 未授权或未运行：真实 AtomGit 上传/下载与服务端写入、PR、标签、发布。
  Git 提交、本地合并和仅推送 github/yuto 已按本次条件授权完成。
  未在 Windows/Linux 主机或真实 Python 3.9 解释器执行；本机的启动方式测试和语法
  检查不能代替这些平台实测。请求超时仍不能发现所有内部死锁。
- 显式参数不再限制整个上传是已接受的兼容变化；帮助、README、FAQ、架构及上传分析
  已说明。D01 交付时 D02–D18 未实施、未接受，不因该次验证自动解决；后续 D02、
  D03 决定见各自章节。

### Delivery Verification

- 本次交付复验：`python tests/run_cli_baseline.py`，**93 passed in 105.41s**。
- compileall、pip check、差异检查、Python 3.9 语法、凭证模式和生成物检查通过。
- 复核无新的阻塞发现；暂存区文档合同检查通过。
- 原有五份规范修改按哈希验证保留且未暂存；只交付 D01 实现及关联文档。

### Independent Review

- Procedure: 按 `.ai/REVIEW.md` 在同一会话切换独立审查角色，依据任务合同、实际差异、
  调用链、测试结果和锁定依赖核对；没有使用外部审查代理。
- Findings: 审查中发现请求失败回归未区分断言失败与请求超时；已补充错误分类断言，
  并增加成功后进程崩溃回归。最终无未解决的 P0/P1/P2/P3 发现。
- Evidence: 生产总截止时间链路已删除，公开参数签名未变；CLI/SDK 一致性、有限重试、
  子进程结果协议和取消清理已覆盖；全部离线门禁通过。
- Residual risks: 远程服务、其他主机平台和真实 Python 3.9 执行未验证，如上记录。
- Verdict: `APPROVED`（实施审查通过，不代表人工验收或交付授权）。

### D01 Acceptance Checklist

- [x] 默认和显式请求超时均不限制上传总时长。
- [x] 网络等待保护、有限重试、故障退出与取消清理已验证。
- [x] CLI/SDK、帮助、文档和能力台账一致。
- [x] 回归、完整离线基线、编译、依赖及差异检查通过。
- [x] 独立审查无未解决发现，剩余验证边界已说明。
- [x] 维护者授权自行复验后提交推送；交付复验通过，满足验收条件。
- [x] 按交付权限提交、本地合入 yuto、仅推送 github/yuto，并核验远端一致。

### D03 Objective And Evidence

取消 AtomGit 自己添加的 LFS pointer 确认 15 秒上限，使确认请求直接采用调用方的
有效请求超时；不修改 HF 1.1.7 内部的 60 秒写入等待，也不恢复上传总时限。

当前单文件、普通目录、resumable、原生 SDK 和历史上传入口在调用
`run_canonical_lfs_upload` 或 `verify_canonical_lfs_pointers` 时使用
`min(request_timeout, 15)`、`min(timeout, 15)` 或 `min(upload_timeout, 15)`。
因此即使用户设置 `--timeout 300` 或 `--timeout 28800`，上传提交后的原始 LFS
pointer 读取仍只使用 15 秒等待；CLI 只展示默认请求超时，用户无法从运行提示判断
这个差异。

本机只读核对确认锁定依赖为 `huggingface-hub==1.1.7`、`httpx==0.28.1`。HF 默认
同步和异步客户端均使用
`httpx.Timeout(constants.DEFAULT_REQUEST_TIMEOUT, write=60.0)`；`upload_file`、
`upload_folder` 和 `upload_large_folder` 均不提供单次调用的 timeout 参数。60 秒
只约束向服务器写入数据时的等待，不是整个上传总时长，D03 不接管该全局客户端。

### D03 Accepted Behavior And Compatibility Migration

| 使用方式 | LFS pointer 确认等待 | 上传总时长 | HF 写入等待 |
|---|---:|---|---:|
| 省略 `--timeout` | 300 秒 | 不限 | 60 秒 |
| `--timeout N` | N 秒 | 不限 | 60 秒 |

- CLI、原生 `AtomGitClient`、历史 `AtomGitAPI` 和 `atomgit_hub` 的有效请求超时必须
  原样到达 LFS pointer 确认，不再暗中取 15 秒上限。
- 这些 timeout 约束对应网络等待操作，不要求单个请求或整个上传在 N 秒内完成。
- 对 N 大于 15 的调用，这是明确行为变化：确认故障可能等待更久，但不会再因隐藏
  上限提前失败；N 小于或等于 15 时行为不变。
- 不新增公开参数，不改变现有参数名称、签名、调用方式、返回值和错误包装。
- 本决定后续替代 D01 中“保留 `min(N,15)`”的细分保护；D01 取消总时限的核心行为
  和历史交付记录不变。

### D03 Implementation Scope

1. 删除所有公开上传链路中的 `min(..., 15)`，在
   `adapters/upload/service.py`、`adapters/upload/resumable.py`、
   `adapters/huggingface.py` 和 `adapters/sdk_uploads.py` 将有效请求超时原样传给 LFS
   pointer 确认。
2. `run_canonical_lfs_upload` 和 `verify_canonical_lfs_pointers` 继续使用现有
   `timeout` 参数；不新增参数。其默认值改用项目现有的 300 秒请求超时合同，避免
   漏传时回落到隐藏的 15 秒值，不为此增加新的配置层或抽象。
3. 单文件和目录 CLI 均显示“上传总时限：不限”和“默认网络请求等待超时：N 秒”；
   删除帮助中“部分请求阶段有独立等待上限”的旧提示，因为 LFS 确认已统一使用 N。
4. 同步 README、FAQ、架构、上传分析及 SDK 参数说明：删除 `min(N,15)`，明确 LFS
   pointer 确认使用 N，同时准确保留 HF 写入等待 60 秒及非全局总时限的说明。
5. 只改变确认等待值；保留 pointer 逐字节验证、失败关闭、凭证脱敏、错误分类、
   断点元数据、批次、取消清理、全局状态恢复和当前有限重试行为。

### D03 Affected Capability IDs

`CLI-SURFACE`、`CLI-DISPATCH`、`UPLOAD-FILE`、`UPLOAD-FOLDER`、
`UPLOAD-RESUMABLE`、`UPLOAD-LFS`、`SDK-UPLOAD`、`RUNTIME`、
`DEPENDENCY-CONTRACT`、`ARCHITECTURE`、`ERROR-REDACTION` 和 `FLOOR-REGISTRY`。
实施时更新现有能力与不变量台账，不新增未要求的能力或测试脚本。

### D03 Protected Existing Invariants

- 默认和显式请求超时均不限制上传总时长，健康长上传不会按累计时间被终止。
- HF 1.1.7 的 `write=60.0`、连接/读取/连接池超时结构及进程全局状态恢复不变。
- LFS pointer 必须按返回提交逐字节验证；超时、读取失败、畸形响应或内容不匹配均
  不能误报上传成功。
- CLI/SDK 错误包装和凭证脱敏不退化，不泄露 token、签名 URL、响应正文或本地路径。
- Ctrl+C、resumable 子进程清理、临时目录、源文件、断点缓存、批次和 model/dataset、
  revision 行为保持兼容。
- 当前重试次数、退避、慢速恢复和远端状态核对保持不变；D03 不提前实施 D05–D08。

### D03 New Or Changed Invariants

- 所有公开上传入口的 LFS pointer 确认使用有效请求超时 N，不得再施加固定 15 秒上限。
- 省略参数时确认使用 300 秒；显式 10、300、28800 等合法值必须原样传递。
- 单文件与目录的 CLI 显示、帮助、SDK 说明、执行层和回归证据对该语义一致。
- N 大于 15 时允许确认故障等待更久，这是已接受的兼容变化，不得通过重新添加隐藏
  上限规避。

### D03 Focused Tests And Evidence

| 场景 | 必须证明的结果 |
|---|---|
| CLI/SDK 省略超时 | LFS pointer 确认收到 300，不是 15 |
| 显式 `--timeout 10` | 确认收到 10，既有小值行为不退化 |
| 显式 `--timeout 300` | 确认收到 300，不再截断为 15 |
| 显式 `--timeout 28800` | 大值原样传递，不引入独立控制面上限 |
| 单文件、普通目录、resumable | 三种上传模式均到达统一确认合同 |
| 原生 SDK、`AtomGitAPI`、`atomgit_hub` | 跨入口参数和结果语义一致 |
| 确认超时、读取失败、畸形响应、内容不匹配 | 仍安全失败且分类、脱敏不退化 |
| 成功、失败、前置失败、中断 | 请求超时、进度和临时/全局状态正确恢复 |
| D01 长时间与多批次回归 | N 不重新成为上传总截止时间 |
| 锁定 HF 客户端合同 | `write=60.0` 未被修改或错误宣称受 N 控制 |

优先扩展现有 `tests/test_canonical_lfs_pointer.py`、
`tests/test_upload_resumable.py`、`tests/test_upload_batching.py`、
`tests/test_upload_file_no_copy.py`、`tests/test_sdk_upload_timeout.py` 及必要的 CLI、SDK、
依赖和开发底线合同，不创建新测试脚本。所有测试离线执行，不真实等待 300 或 28800 秒，
不访问 AtomGit。

### D03 Implementation Phases And Acceptance

1. 激活后冻结六类公开入口、底层默认值和 HF 1.1.7 依赖合同，先添加大于 15 秒值
   被截断的回归。验证：旧实现因实际收到 15 而失败，失败原因确为隐藏上限。
2. 最小修改共享确认调用及底层默认值，不引入新参数、客户端工厂、重试或抽象。
   验证：默认、10、300、28800 及所有上传入口专项通过，错误与恢复专项不退化。
3. 同步 CLI/SDK 输出和文档、能力与不变量台账；执行完整离线基线、compileall、
   pip check、diff check 及独立审查。验证：无未解决阻塞发现后再进入人工验收。

实施必须在 `atomgit_cli` conda 环境运行；完整基线失败或未运行时不得完成、提交、
合并或推送 D03。

### D03 Verification Evidence

- 实施前完整离线基线：`python tests/run_cli_baseline.py`，93 passed in 111.82s。
- 锁定依赖只读核对：`huggingface-hub==1.1.7`、`httpx==0.28.1`；`upload_file`、
  `upload_folder`、`HfApi.upload_large_folder` 的真实签名不接收 timeout 参数；HF 客户端
  当前结构为 connect/read/pool 采用默认请求值、write=60.0。
- 红灯回归：`test_canonical_lfs_pointer.py` 为 23/25，通过项外的两项均实际收到 15
  而非默认 300；`test_upload_file_no_copy.py` 为 17/19，默认 300 与显式 28800 均被
  截断为 15。组合命令退出 1，失败原因与 D03 隐藏上限一致。
- 实现后专项：canonical pointer 25/25、单文件 CLI/原生 SDK 21/21、resumable 与普通
  目录 61/61、历史/原生 SDK 超时 9/9、CLI 验证/help 16/16、commit/retry 51/51、SDK
  参数 14/14、全局状态 7/7、parity 21/21、开发底线 15/15、结构 18/18、HF 依赖签名
  16/16、打包元数据 13/13；相关 batching 与 source-layout 脚本同时通过。
- 已删除四个适配器的六处 `min(..., 15)`，底层两个默认值统一复用 300 秒合同；新增
  `LFS-004`，不变量 118 -> 119，测试脚本数不变。格式债务未增长：Black 410、Ruff
  44 不变；新增导入使 isort 89 -> 88，精确摘要已收紧。
- 首次实现后完整基线：92 passed、1 failed in 104.41s；唯一失败是新增原生 SDK 测试
  只向 client 构造器提供假 token，隔离 HOME 下方法请求没有凭证而正确失败。测试已改为
  在两次原生 SDK 方法调用显式传入假 token；相关脚本重新通过，未修改产品鉴权行为。
- 最终完整离线基线：`python tests/run_cli_baseline.py`，93 passed in 105.02s。
- `python -m compileall -q .`、`python -m pip check`、`git diff --check` 通过；14 个变更
  Python 文件通过 Python 3.9 AST 语法解析，差异无凭证字面量、二进制、未跟踪生成物。
- 首轮审查 P2 已修复：断点元数据空操作只在新增 pointer 场景内生效并在 `finally`
  恢复。修复后专项 61/61、格式门禁 13/13，完整离线基线 93 passed in 109.24s；编译、
  依赖、Python 3.9 语法、差异、凭证字面量、二进制和未跟踪生成物检查再次通过。
- 第二轮审查 P2 已修复：开发与讨论交接的分支、D03 激活、权限和验证状态已同步。
  修复后完整离线基线 93 passed in 110.07s；compileall、pip check、diff check 再次通过，
  没有未跟踪文件。
- 当前未运行：真实 AtomGit、Windows/Linux 与真实 Python 3.9 解释器。

### D03 Delivery Verification

- 维护者交付授权后的完整离线复验：`python tests/run_cli_baseline.py`，
  **93 passed in 104.29s**。
- `python -m compileall -q .`、`python -m pip check`、`git diff --check` 通过；14 个
  变更 Python 文件通过 Python 3.9 AST 语法解析，锁定 HF/httpx 版本、方法签名和
  `write=60.0` 合同复核通过。
- 差异中的 6 个凭证形式字面量均为测试文件内带 `fake` 标记的占位值；无二进制差异、
  未跟踪生成物或真实凭证。原有五份规范文档修改保持在本次交付范围外。

### D03 Non-Goals And Residual Risks

- 不修改或替换 HF 全局 HTTP 客户端，不让 `--timeout` 控制 `write=60.0`。
- 不新增 LFS 确认重试；服务端最终一致性策略留给 D05。
- 不区分“远端已提交”和“本地已确认”，不改变重跑去重或错误子类型；留给 D06–D08。
- 较大 N 会延长提交后确认失败的等待，但这是统一参数的已接受结果。
- 本轮没有真实 AtomGit、Windows/Linux 或真实 Python 3.9 执行证据；未来实施时必须
  将未运行项作为剩余风险报告，远程写入仍需单独授权。

### D03 Independent Review

- 首轮审查：`REQUEST CHANGES`。发现 1 个 P2：新增 resumable pointer 超时回归在整个
  `test_upload_resumable.py` 运行期将断点元数据提交函数替换为空操作，补丁范围超出新增
  场景，可能削弱既有测试证据。生产实现、调用链、文档和依赖合同未发现其他问题。
- 修复要求：只在新增 pointer 场景内临时替换并在 `finally` 恢复；修复后重新运行相关
  专项、完整基线和全新独立审查。
- 修复状态：已按要求收窄并恢复补丁；修复后全部门禁通过，等待全新审查结论。
- 第二轮审查：`REQUEST CHANGES`。发现 1 个 P2：开发 Issue 的旧仓库核对段和讨论
  Issue 的头部、权限及持久快照仍声明 `yuto / D03 未激活`，与真实任务分支和当前
  授权冲突。实现、测试、文档行为与依赖合同未发现其他问题。
- 第二轮修复状态：两份交接已与真实分支和权限同步；修复后全部门禁通过，等待最终
  独立审查结论。
- 最终审查：无 P0/P1/P2/P3 发现；两项历史发现均已修复，生产超时传递、错误失败关闭、
  全局状态恢复、测试隔离、文档、锁定依赖、结构和开发底线证据一致。剩余风险仅为
  未执行真实 AtomGit、Windows/Linux 和真实 Python 3.9 验证。Verdict: `APPROVED`。

### D03 Activation And Delivery Status

- [x] 维护者确认行为方向和 HF 60 秒写入边界。
- [x] 完整方案已获准写入本地开发 Issue。
- [x] D03 实施已明确激活。
- [x] 红灯回归、实现、文档和能力台账完成。
- [x] 专项与完整离线门禁通过。
- [x] 独立审查和人工验收完成。
- [x] 提交、合并和仅推送 `github/yuto` 已获得明确授权。
- [ ] 提交、本地合并、推送及远端一致性核验完成。

当前 D03 已通过维护者要求的完整复验并获得交付授权；只允许本地合入 `yuto` 并推送
`github/yuto`，不能推送任务分支或执行其他远程操作。

### Current Handoff Snapshot

- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`，当前分支
  `codex/d03-lfs-pointer-timeout`，基于 `yuto` 的
  `11ffbe524a0afabb364fc007ff9a0601b9901f3f`；尚无 D03 提交。
- D01 任务提交：`a4d7216`（fix(upload): remove total upload deadline）。
- 本地 no-ff 合并并已推送的提交：`720d641a776fae7ff94c786f45fe813530387f25`。
- D01 交付记录提交 `11ffbe5` 已推送；当前远端 yuto 为该提交，远端没有
  `codex/d01-upload-request-timeout` 分支。
- 源码与测试等交付树同已验证的任务分支一致；没有修改 main 或 atomgit 远端。
- 原有 `.ai/DEVELOPMENT_RULES.md`、`.ai/DOD.md`、`.ai/MASTER_PROMPT.md`、
  `.ai/README.md`、`.ai/WORKFLOW.md` 五份未提交修改仍原样保留；本轮另有
  `.ai/ISSUE_DISCUSSION.md` 和 `.ai/TASK.md` 的 D02/D03 讨论与登记修改。续接使用
  当前 worktree。
- 最近完成：维护者交付授权后的完整复验 93 passed in 104.29s；compileall、pip check、
  Python 3.9 语法、依赖签名、差异、凭证与生成物检查通过。
- 下一步：提交 D03、本地 no-ff 合入 `yuto`、仅推送 `github/yuto` 并核验；D04 不实施。

# Historical R9 Contract (retained evidence, not current execution authority)

Historical status text (stale): `active (R9 upload observability monitor; issue activation only)`

## Historical R9 Development Issue

- Updated: `2026-08-26`
- ID: `LOCAL-R9-UPLOAD-OBSERVABILITY-MONITOR`
- Title: `Implement the read-only upload observability monitor window`
- Type: `cli`, `architecture`, `compatibility`, `security`, `testing`, `packaging`,
  `portability`, `documentation`
- Priority: `P1` (new public CLI surface with upload-process isolation and cache safety)
- User authorization: explicit request on `2026-08-26` to record the approved
  development plan as a project Issue; this turn does not authorize source edits or
  implementation execution.
- Delivery mode: local implementation and acceptance first; commit, push, merge,
  release, publication, and remote repository mutation require separate explicit
  authorization.
- Canonical design: `docs/features/upload-monitor.md`; it is the feature-level
  source of truth and must be kept consistent with this Issue and the executable
  capability/CLI ledgers.
- Current phase: implementation complete; human acceptance recorded on `2026-08-26`.
- Next exact action: none for this Issue; follow-up work requires a new authorized Issue.

### Objective

Add a top-level, read-only monitoring surface for resumable multi-file uploads:

```text
atomgit monitor upload status
atomgit monitor upload status --list
atomgit monitor upload status SESSION_ID
```

`status` continuously monitors the first session from the deterministic session list;
`--list` prints session summaries once; `status SESSION_ID` continuously monitors the
specified session. No `--watch` option and no separate one-shot detailed status command
are in scope.

The monitor must show complete current-session details by default. LFS files show
Flow-level speed and slow-flow state; ordinary files show session/batch progress only
and must not be assigned fabricated precise speeds. The Flow table uses the column
`文件缩写`; its value is the final ten Unicode characters of the basename by default
(or the full basename when shorter). The Flow table does not contain a repository
column; the repository name appears in the session header.

### Approved behavior decisions

- Active sessions sort before finished sessions; within each group, newest update first.
- If there is no active session, default `status` selects the newest finished session,
  displays its final state, keeps the final frame and last event for about two seconds,
  and exits. No sessions produces a clear message and a normal exit.
- A specified session follows the same two-second final-state behavior.
- `Ctrl+C` closes only the monitor and never signals or stops the upload process.
- The first implementation uses Click, ANSI control sequences, and standard-library
  fallback output only; it does not add curses, rich, textual, or another TUI dependency.
- The terminal displays the repository's final name component in the session header;
  the snapshot may store only that display label, not the owner, full repo ID, URL, or
  remote path. Flow rows omit the repository column.
- Monitoring persists structured snapshots and a bounded key-event history only; it
  does not persist a complete raw debug log.
- Monitor data lives under the AtomGit cache root at
  `upload-observe/v1/<session-id>.json` and is included in `atomgit cache clear` while
  preserving all existing cache-cleanup behavior and safety boundaries.

### Scope and data model

- Session fields include session ID, display repository name, repo type, revision,
  status, timestamps, batch progress, file/byte totals, active/peak Flow counts,
  replacement totals, improvement totals, auto-replacement-disabled totals, and
  bounded recent events.
- Flow fields include anonymous Flow ID, file ID, `文件缩写`, size, type, five-second
  sample speed, thirty-second formal speed, reliable baseline ratio, slow-window count,
  replacement count, estimated remaining bytes, trend, phase, update time, and the
  latest strategy explanation.
- A Flow never exposes a source path, remote path, full OID, request header, token,
  signed URL, or response body.
- Five-second speed is display-only; thirty-second speed is the formal strategy window.
  Existing self-baseline, peer-baseline, three-window slow-flow, benefit, cooldown,
  improvement, and three-replacement rules remain authoritative and are not duplicated
  or changed by the monitor.
- Every Flow retains a fixed twelve-window trend ring. Events are limited to important
  transitions such as low-speed observation, replacement approval/start, cooldown,
  improvement success/failure, disablement, completion, and failure; ordinary samples
  do not become events and the queue is bounded at approximately 200 entries.

### Runtime and storage design

- Existing upload/LFS recovery code publishes narrow observer updates; it does not
  depend on the CLI renderer and does not synchronously write to disk.
- A non-blocking in-memory publisher maintains one latest state per Flow and a bounded
  event queue. A background publisher writes a versioned JSON snapshot at most once per
  second (with an idle heartbeat approximately every two seconds).
- Snapshots are written to a same-directory temporary file and atomically replaced;
  monitor processes are read-only and never hold upload-worker objects.
- The cache root, monitor directory, version directory, snapshots, and temporary files
  use restrictive permissions (`0700` directories, `0600` files).
- Observer lock contention, serialization failure, monitor crash, snapshot deletion,
  or an unwritable monitor directory may lose replaceable intermediate display data but
  must never block, fail, or alter the upload decision.
- `cache clear` retains its current AtomGit-owned-root cleanup and additionally removes
  the monitor snapshot subtree and temporary monitor files, without touching source
  files, upload projections outside the existing managed root, remote content, or any
  path outside the AtomGit cache root.

### Affected Capability IDs

Existing capabilities affected by the public surface and integration:
`FLOOR-REGISTRY`, `CLI-SURFACE`, `CLI-DISPATCH`, `UPLOAD-FILE`, `UPLOAD-FOLDER`,
`UPLOAD-RESUMABLE`, `UPLOAD-LFS`, `UPLOAD-LFS-RECOVERY`, `CACHE`, `RUNTIME`,
`PACKAGING`, `PORTABILITY`, `ARCHITECTURE`, and `ERROR-REDACTION`.

New capability to register in the same implementation change:
`UPLOAD-OBSERVABILITY` — read-only upload session selection, Flow monitoring, structured
snapshot publication, and terminal rendering.

### Protected Existing Invariants

- All existing registered capabilities, invariants, and the complete offline baseline
  remain intact; no existing upload, LFS, cache, CLI, packaging, or security behavior
  may be weakened.
- The existing `atomgit upload` syntax, arguments, output contracts, exit behavior,
  LFS recovery thresholds, retry limits, cooldowns, and replacement decisions remain
  unchanged.
- Locked `huggingface-hub==1.1.7`, `datasets==4.4.1`, Python `>=3.9` metadata, the
  seven-directory source layout, historical imports, credential redaction, and cache
  root safety remain unchanged.
- `atomgit cache clear` continues to remove only AtomGit-owned cache content and
  preserves the root and all outside paths.
- Existing cache, upload projection, resumable metadata, and download state cleanup
  semantics remain compatible; monitoring adds only its own managed subtree.

### New Or Changed Invariants

- The three monitor commands have the exact schema above; `--watch` is rejected.
- Default session selection is deterministic: active first, then newest update; when
  no active session exists, the newest retained finished session is selected.
- `--list` emits session summaries only; detailed commands continuously render one
  selected session and hold its final frame for approximately two seconds.
- Flow rows use `文件缩写`, derive it from the basename's final ten Unicode characters,
  and omit the repository column; the session header displays the repository label.
- LFS Flow speed and slow-state values come from the existing recovery observations;
  ordinary files receive no fabricated precise speed.
- Monitor output and persisted snapshots are read-only with respect to upload behavior;
  `Ctrl+C`, monitor crash, snapshot loss, lock contention, and observer write failure do
  not change upload results.
- State snapshots are versioned, atomically replaced, bounded, permission-restricted,
  and free of tokens, URLs, request headers, source/remote paths, full OIDs, and response
  bodies.
- The event queue and trend history are bounded; repeated samples and stable states do
  not cause unbounded memory, disk, or terminal output growth.
- `atomgit cache clear` removes monitor snapshots and temporary files in addition to its
  existing managed cache contents, while preserving all outside data and remote state.
- Windows, macOS, Linux, ANSI terminals, non-ANSI terminals, narrow terminals, and
  redirected output have safe output behavior.

### Focused tests and evidence

The implementation must add executable offline coverage for:

- exact monitor CLI schema, help, dispatch, `--watch` rejection, and legacy upload
  compatibility;
- session ordering, default selection, no-session behavior, finished-session display,
  specified-session monitoring, final-frame delay, and `Ctrl+C` isolation;
- LFS Flow fields, ordinary-file session/batch accounting, basename abbreviation,
  repository placement in the header, and omission from Flow rows;
- five-second and thirty-second speeds, baselines, slow-window counters, replacement
  explanations, remaining-byte semantics, and twelve-window trends;
- bounded state/event memory, event filtering, stale heartbeat, malformed snapshots,
  atomic replacement, concurrent reads/writes, and monitor process failure;
- cache permissions, expiry, safe cleanup, and `cache clear` removal of the monitor
  subtree without deleting outside content;
- token/path/URL/OID/request-header redaction and warning/output stream separation;
- Windows/ANSI fallback behavior and installed source/editable/wheel/sdist command smoke.

The exact new test scripts must be added to `tests/cli_baseline_contract.py` and mapped
to the new capability in `tests/development_floor_contract.py`. Required final evidence:

```text
python tests/run_cli_baseline.py
python -m compileall -q .
python -m pip check
git diff --check
```

Controlled remote testing is not needed to prove the local state protocol, but the
approved remote matrix may later validate real LFS interruption/recovery and monitor
readback after separate test execution authorization.

### Approved remote test scope

Only these repository IDs may be used:

- `weixin_52273949/test_model`: model positive upload, large-file, interruption, and
  resume tests;
- `weixin_52273949/test_datasets`: read-only diagnostic access only; not a positive
  write fixture;
- `weixin_52273949/atomgit-cli-dataset-20260804-003221`: dataset positive upload,
  large-file, interruption, and resume tests.

Permitted operations after the maintainer's explicit start instruction include real
uploads, large files, interruption/recovery, readback, and leaving local monitor
snapshots. Repository creation/deletion, visibility changes, remote branch changes,
`.gitattributes` mutation, remote cleanup, publication, release, token output, and any
repository outside this list are excluded.

### Out of scope

- download monitoring;
- upload pause, cancel, manual reconnect, or concurrency control;
- complete raw HTTP debug-log persistence;
- Web UI or a resident background service;
- new TUI dependencies;
- remote repository lifecycle changes;
- changes to the existing upload recovery algorithm;
- source-path or full-repository identity exposure.

### Acceptance criteria

The Issue is complete only when the command contract, detailed session/Flow rendering,
speed semantics, cache integration, safe snapshot lifecycle, bounded event logging,
cross-platform fallback, upload isolation, focused regressions, capability/CLI ledger,
complete baseline, packaging smoke, security checks, and any explicitly authorized
remote evidence all agree. Remaining remote or Python-version limitations must be
reported rather than hidden.

## Deferred Design Record

- `docs/features/upload-monitor.md` records the maintainer-approved design
  conclusions from the upload observability discussion; the old
  `docs/upload_observability_design.md` path is a compatibility redirect.
- The design is documentation only: no `monitor` command, upload status command,
  telemetry snapshot, or runtime behavior has been implemented.
- A future conversation must reconcile the design with the then-current CLI and
  activate a separate maintainer-authorized Issue before implementation.

## Prior R8 Test Issue (inactive for handoff)

- Status: inactive for handoff after explicit activation of
  `LOCAL-R9-UPLOAD-OBSERVABILITY-MONITOR`; all R8 evidence, remote limitations, and
  review history below remain preserved as historical record.

- Updated: `2026-08-25`
- ID: `LOCAL-R8-POST-ACCEPTANCE-TEST`
- Title: `Update and execute the R8 post-delivery comprehensive acceptance plan`
- Type: `testing`, `compatibility`, `packaging`, `security`, `portability`
- Priority: `P1` (acceptance evidence gap; no implementation change authorized)
- User authorization: explicit request on `2026-08-25` to update and execute the plan
- Delivery mode: local evidence and documentation only; no commit, push, Issue transition,
  release, publication, or unrelated remote write authorized by this task
- Remote scope: only `weixin_52273949/test_model` and
  `weixin_52273949/test_datasets`, plus the explicitly supplied positive dataset target
  `weixin_52273949/atomgit-cli-dataset-20260804-003221`, using
  `ATOMGIT_TEST_TOKEN` without printing it. The old `test_datasets` target is read-only.
- Explicit remote exclusions: repository create/delete, visibility changes, remote branch
  create/delete, `.gitattributes` mutation, `--auto-configure-lfs`, cleanup, publication,
  release, and any repository outside the two-item allowlist
- Affected Capability IDs: `FLOOR-REGISTRY`, `PACKAGING`, `PORTABILITY`, `AUTH-CONFIG`,
  `REPO-MANAGEMENT`, `REVISION`, `UPLOAD-FILE`, `UPLOAD-FOLDER`, `UPLOAD-RESUMABLE`,
  `UPLOAD-LFS`, `UPLOAD-LFS-RECOVERY`, `DOWNLOAD-SNAPSHOT`, `DOWNLOAD-FILE`,
  `DOWNLOAD-INTEGRITY`, `DOWNLOAD-SECURITY`, `SDK-DOWNLOAD`, `SDK-UPLOAD`, `SDK-REPO`,
  `REPO-ID`, `ARCHITECTURE`
- Protected Existing Invariants: all 27 registered capabilities, 116 invariants, 92-case
  offline baseline, locked `huggingface-hub==1.1.7` and `datasets==4.4.1`, exact R8
  five-root source layout, historical imports, credential redaction, and artifact provenance
- New Or Changed Invariants: none; this task adds evidence only and must not weaken or relabel
  an existing invariant
- Required evidence: R8 source/structure/ownership/parity checks, complete offline baseline,
  compileall, pip check, diff check, source/editable/wheel/sdist smoke, strict offline parity,
  read-only remote preflight, and the in-scope controlled remote matrix
- Acceptance criteria: update `docs/testing.md` from the stale pre-R8 wording; record every
  test as passed, failed, or not run by scope; rerun the offline baseline after remote tests;
  leave no token, cache, artifact, or fixture in the worktree; explicitly report Python 3.9
  status and all residual remote limitations
- Current phase: execution complete; evidence recorded; awaiting human review of the
  rate-limited remote remainder
- Verification evidence: pre-remote and post-remote `python tests/run_cli_baseline.py`
  both passed `92/92` (108.11s and 95.35s); structure `18/18`, source layout `11/11`,
  packaging metadata `13/13`, architecture parity `21/21`, artifact smoke `49/49`,
  `python -m compileall -q .`, `python -m pip check`, and `git diff --check` passed.
- Remote evidence: read-only preflight succeeded for both authorized private repositories;
  SDK single-file upload/readback to model passed with 40-byte SHA-256
  `fbef9c3d…e0ac060b`; authenticated resolve read 77 bytes with SHA-256
  `789192e8…e56946`; anonymous private resolve returned HTTP 403 as expected.
- Remote limitation: subsequent file-tree access returned HTTP 429 Too Many Requests.
  Remaining directory, CLI/SDK cross-surface, resumable, checksum/prune, LFS, legacy
  `atomgit_hub`, and dataset transfer rows are recorded as not run by scope after the
  rate limit; no high-frequency retry was attempted.
- Portability limitation: no separate Python 3.9 interpreter is installed; Python 3.10.20
  was used, while package metadata and tool targets continue to assert Python `>=3.9`.
- Worktree changes: `.ai/TASK.md` and `docs/testing.md` only; no generated artifact,
  token, cache, or remote fixture entered the tracked worktree.
- Independent review: `APPROVED` for the documentation and evidence diff; no source,
  credential, scope, or test-integrity finding. Human acceptance remains pending for the
  explicit 429-limited remote remainder.
- Retry evidence (`2026-08-25`): model preflight exhausted low-frequency backoff with
  timeout/HTTP 429; dataset preflight recovered on attempt 2 but SDK single-file and folder
  uploads returned `BadRequestError`/`AtomGitError`, CLI upload exited 1, and remote file count
  remained 0. No dataset download or checksum row was claimed because no file was created.
- Retry post-gate: `python tests/run_cli_baseline.py` passed `92/92` in 105.50s;
  `compileall`, `pip check`, and `git diff --check` passed again. The remote failures are
  recorded as service-side rate-limit/fixed-repository constraints, not client regressions.
- Test strategy adjustment authorized by the latest user request: future remote retries use
  one cached manifest per repository, direct resolve readback for known targets, one batched
  directory operation, and finite exponential backoff; repeated tree/list refreshes stop on
  429 or consecutive timeouts.
- Low-request retry evidence: after a 30-second cooldown, one SDK directory upload to
  `weixin_52273949/test_model` and one direct readback passed (22 bytes, SHA-256
  `2bb82b98…f7ad1c5`); the equivalent dataset upload still returned `BadRequestError` with
  no new remote files. Final post-retry baseline passed `92/92` in 94.93s.
- Dataset-route diagnosis: `repo_type="dataset"` through the shared model-compatible route
  succeeded against the writable authorized model repository; direct readback passed for
  25 bytes with SHA-256 `393dacd4…c5bc2e1`. This preserves evidence that the client mapping
  is correct; the fixed dataset repository's `BadRequestError` remains a service-side state
  limitation.
- Maintainer decision: positive dataset transfer acceptance now uses
  `weixin_52273949/atomgit-cli-dataset-20260804-003221`; the old `test_datasets`
  repository is excluded from positive write assertions. Remote execution uses one cached
  tree per repository and direct known-target readback.
- Implementation fix: SDK `path_in_repo` directory uploads now prefix source-relative
  ignore patterns before passing them to HF, so `logs/` excludes projected nested files.
  Regression `14/14`, repo type `17/17`, and HF contract `16/16` passed.
- Final remote evidence: new dataset target passed CLI single upload/readback, SDK folder
  upload with `*.tmp` and `logs/` exclusions, historical folder upload, CLI checksum/resume,
  SDK snapshot and cross-surface downloads, manifest prune safety, legacy downloads, and
  `load_dataset` (1 row). Final baseline passed `92/92` in 103.51s; compileall, pip check,
  and diff check passed.

## Handoff Snapshot

- Updated: `2026-08-26`
- Phase: `R9 issue activated; implementation not started`
- Base branch: `yuto`
- Base commit: `af3a30e docs(features): add upload monitor specification`
- Task branch: `codex/r9-upload-observability-monitor` (local-only, created from yuto)
- Prior delivery: `R7 task commit 2e781d9 and yuto merge commit 8a93aa6 were pushed; local yuto, github/yuto, and ls-remote all verified at 8a93aa6d8344f18b1be0edd6a44b6fb46054d3d3`
- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`
- Worktree state: `uncommitted R9 implementation, tests, registry, and documentation changes; no generated artifact, token, cache, or remote fixture`
- Last completed action: `completed snapshot publisher/session facade, LFS observer hook, CLI/structure/packaging registrations, and full baseline`
- Next exact action: `none; Issue delivered on yuto`
- Blockers: `none; live remote behavior remains outside this Issue`
- Latest verification: `python tests/run_cli_baseline.py: 93 passed in 109.38s; compileall, pip check, and git diff --check passed`
- Review status: `finding resolved; follow-up review check passed` — child-process LFS
  observer events now bridge into the UploadSession snapshot path. Human acceptance
  and delivery authorization remain pending.
- Current evidence: `pre-change baseline 92/92 in 99.84s; pre-deletion rootless artifact smoke 49/49 and baseline 92/92 in 92.13s; post-deletion structure 18/18, source layout 11/11, packaging metadata 13/13, public imports 11/11, utilities 17/17, lifecycle 26/26, completion 19/19, uninstaller 14/14, config permissions 15/15, runtime 9/9, canonical LFS 24/24, LFS ownership 14/14, CLI facade 9/9, architecture parity 21/21, artifact smoke 49/49, independent review APPROVED, and acceptance baseline 92/92 in 99.27s; compileall, pip check, diff check, exact deletion scope, credential-pattern, and generated-artifact checks pass`
- Residual risk: `live remote behavior is outside this Issue and is not claimed; the active environment did not separately execute a Python 3.9 interpreter, while source/tool policy and the locked dependency contracts retain Python 3.9 support`

## Completed Issue

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-R8-ROOT-FACADE-PHYSICAL-CLOSURE`
- Title: `Move non-entry root Python facades into the seven responsibility directories without breaking historical imports`
- Primary type: `refactoring`
- Secondary types: `architecture`, `compatibility`, `cli`, `sdk`, `distribution`, `testing`, `packaging`, `documentation`, `portability`
- Priority: `P1`
- Status: `completed and accepted; implementation bd859b7 merged as 5c342ce and pushed to github/yuto`
- Delivery: `read-only inventory -> explicit implementation authorization -> focused migration slices -> exact-root deletion gate -> complete offline verification -> independent review -> human acceptance -> separately authorized commit/merge/push`

### Objective

Reduce the physical Python files directly under `src/atomgit` from R7's frozen
fifteen-file allowlist to exactly these five package entry and historical entry
shims:

```text
__init__.py
__main__.py
api.py
atomgit_hub.py
cli.py
```

The seven first-level responsibility directories remain exact and unchanged:

```text
adapters/
compatibility/
core/
domain/
infrastructure/
interfaces/
usecases/
```

Real implementation must remain with its canonical responsibility owner.
Historical root module behavior moves physically under `compatibility` or is
provided by a finite explicit alias/loader. Removing a root file must not
remove its `atomgit.<name>` import path, symbols, signature, return, exception,
identity, patch seam, lazy-import behavior, or applicable module execution.

### Current Evidence And Problem Statement

- R7 delivered an exact seven-directory physical tree, but retained fifteen
  approved root Python files because their historical compatibility behavior
  was separately frozen.
- `cli_contracts.py`, `exceptions.py`, `lfs_pointer.py`, `runtime.py`, and
  `version.py` are small forwarding or authority modules with low-to-medium
  migration risk.
- `config.py` has a package-attribute/module-name collision with the exported
  shared `config` singleton.
- `release.py` preserves historical symbol patching and executable-module
  behavior.
- `completion.py`, `uninstaller.py`, and `utils.py` forward monkeypatch
  assignment and deletion to multiple canonical infrastructure owners; a
  simple module alias is not automatically equivalent.
- Before R8, `setup.py` read `src/atomgit/version.py` directly; it now reads the
  canonical `src/atomgit/infrastructure/version.py` authority without runtime import.
- Existing structure, package artifact, public import, installed smoke,
  completion, lifecycle, utility, SDK, and CLI contracts freeze the current
  paths and must be tightened in the same change as each physical removal.

### User Impact

No user-visible capability or supported import is intended to change. CLI,
native `atomgit.interfaces.sdk.AtomGitClient`, and historical `atomgit_hub`
behavior must remain compatible. This Issue changes physical ownership and
module loading only; any historical path that cannot be preserved must be
reported before deletion and requires a separate maintainer compatibility
decision.

### Affected Capability IDs

`FLOOR-REGISTRY`, `ARCHITECTURE`, `CLI-SURFACE`, `CLI-DISPATCH`, `AUTH-CONFIG`,
`GIT-CREDENTIAL`, `UPLOAD-LFS`, `SDK-DOWNLOAD`, `SDK-UPLOAD`, `SDK-REPO`,
`RUNTIME`, `CACHE`, `DEPENDENCY-CONTRACT`, `PACKAGING`, `PORTABILITY`, and
`ERROR-REDACTION`.

### Protected Existing Invariants

- The development floor remains at 27 capabilities and 116 invariants unless
  the maintainer explicitly authorizes an invariant replacement. `ARCH-004`
  is tightened from the current root allowlist to the exact five-file result;
  no registered behavior evidence is deleted or weakened.
- `atomgit`, `atomgit.api`, `atomgit.cli`, `atomgit_hub`, console execution,
  `python -m atomgit`, `python -m atomgit.cli`, and
  `python -m atomgit.cli.__main__` retain current behavior.
- Historical imports including `atomgit.cli_contracts`, `atomgit.exceptions`,
  `atomgit.lfs_pointer`, `atomgit.runtime`, `atomgit.config`,
  `atomgit.version`, `atomgit.release`, `atomgit.completion`,
  `atomgit.uninstaller`, and `atomgit.utils` remain importable.
- Public and tested private symbols preserve signatures, callable/class/singleton
  identities where currently contracted, returns, error categories, module
  assignment/deletion behavior, and `unittest.mock.patch` propagation.
- Completion-only imports stay lightweight and do not eagerly load Hugging
  Face, datasets, SDK, remote transport, or CLI business execution paths.
- The shared config singleton, private configuration permissions, atomic
  persistence, credential-helper isolation, token redaction, global-state
  restoration, managed-path safety, and source/editable-install protections
  remain unchanged.
- Locked `huggingface-hub==1.1.7`, `datasets==4.4.1`, Python 3.9 support,
  package contents, console entry point, wheel, sdist, and editable-install
  behavior remain exact.

### New Or Changed Invariants

- `src/atomgit` has exactly the seven canonical first-level directories and
  exactly the five approved root Python files; any sixth root file fails the
  source-layout, structure, packaging, and installed-artifact gates.
- The ten removed root files have one explicit compatibility route each; no
  unbounded fallback importer or generic root-module shim registry is allowed.
- Canonical production code imports canonical owners directly. It must not use
  a historical alias as an internal dependency merely to preserve compatibility.
- Physical compatibility facades belong under `compatibility`; core errors and
  contracts remain under `core`; LFS pointer protocol remains under `adapters`;
  runtime, configuration, lifecycle, utilities, release, and version facilities
  remain under `infrastructure`.
- `compatibility` may translate historical paths, names, signatures, identities,
  and patches but may not contain new validation, orchestration, filesystem,
  credential, release transport, or remote business implementation.
- Every facade debt ceiling, module owner, dependency edge, package manifest,
  and artifact expectation tightens in the same slice that removes a root file.

### Implemented Destination Map

| Former root file | Canonical implementation owner | Historical compatibility location/treatment | Risk |
|---|---|---|---|
| `cli_contracts.py` | `core/contracts.py` | `compatibility/cli_contracts.py` or exact runtime alias | low |
| `exceptions.py` | `core/errors.py` | `compatibility/exceptions.py` or exact runtime alias | low |
| `lfs_pointer.py` | `adapters/lfs/pointer.py` | `compatibility/lfs_pointer.py` or exact runtime alias | low |
| `runtime.py` | `infrastructure/runtime.py` | `compatibility/runtime.py` or exact runtime alias | low |
| `version.py` | `infrastructure/version.py` | exact `atomgit.version` alias; update build-time reader | medium |
| `release.py` | `infrastructure/release.py` | `compatibility/release.py` plus execution loader if required | medium-high |
| `completion.py` | `infrastructure/completion.py` and existing lifecycle owners | `compatibility/completion.py` composite facade | high |
| `uninstaller.py` | `infrastructure/uninstall.py`, `environment.py`, `managed_paths.py` | `compatibility/uninstaller.py` composite facade | high |
| `config.py` | `infrastructure/config.py` | `compatibility/config.py` or dedicated module/singleton-safe alias | high |
| `utils.py` | `infrastructure/validation.py`, `filesystem.py`, `output.py`, `cache.py`, `git_credentials.py` | `compatibility/utils.py` composite facade | high |

The implemented routes preserve the recorded identity and patch requirements
without moving canonical behavior into the compatibility layer or creating an
eighth first-level directory.

### R8 Package Evidence Ledger

- `WP-00: completed | HEAD=8a93aa6 | pre-change baseline 92/92 in 99.84s; ten root modules, callers, metadata, import modes, execution paths, artifacts, and locked signatures inventoried`
- `WP-01: completed | exact five-file target plus bounded ten-file migration allowance; sixth-root and missing-entry fixtures fail closed; structure 18/18`
- `WP-02: completed | cli_contracts, exceptions, lfs_pointer, and runtime use canonical owners through finite historical routes; identities covered by public/ownership tests`
- `WP-03: completed | infrastructure/version.py is the build/runtime authority; setup.py reads it without runtime import; source and artifact version identity passes`
- `WP-04: completed | compatibility/release.py retains forwarded identities, assignment/deletion seams, and warning-free python -m atomgit.release --help`
- `WP-05: completed | compatibility completion/uninstaller facades retain multi-owner assignment/deletion propagation; lifecycle 26/26, completion 19/19, uninstaller 14/14`
- `WP-06: completed | atomgit.config retains Config/shared-singleton identity, normal-import package attribute behavior, permissions, and atomic persistence; config 15/15`
- `WP-07: completed | compatibility/utils.py retains validation/filesystem/output/cache/Git seams and sys.modules preload compatibility; utilities 17/17 plus repaired affected baseline scripts`
- `WP-08: completed (non-destructive) | all ten historical paths pass with root files omitted from isolated source, wheel, sdist, and PEP 660 editable copies; artifact smoke 49/49; pre-deletion full baseline 92/92 in 92.13s`
- `WP-09: completed | maintainer authorized the ten exact paths on 2026-08-25; only those tracked regular files were deleted; exact five-root source, owner, edge, facade-debt, wheel, sdist, tool-debt, and documentation contracts reconciled; structure 18/18, source layout 11/11, packaging metadata 13/13`
- `WP-10: completed and accepted | final post-deletion focused gates pass; wheel/sdist/editable artifact smoke 49/49; acceptance baseline 92/92 in 99.27s; compileall, pip check, diff/scope/security/artifact scans pass; independent review APPROVED with no findings; delivered as bd859b7 merged by 5c342ce`

The exact deletion gate was satisfied by the maintainer's explicit authorization
on `2026-08-25`. The maintainer accepted the final test result and authorized
commit/push on the same date; the task commit was merged locally and only
`github/yuto` was pushed. Live tests and unrelated remote writes were not
authorized or performed.

### Independent Review

- Inputs: active Issue and acceptance criteria, complete diff from `8a93aa6`,
  all affected and new source/tests, architecture and release documentation,
  locked dependency contracts, focused results, artifact smoke, and the final
  complete offline baseline.
- Findings: none.
- Missing evidence: no live remote operations were run because they are outside
  the authorized scope; no separate Python 3.9 interpreter run was performed.
- Verdict: `APPROVED`.
- The verdict does not authorize commit, merge, push, Issue closure, release, or
  any remote write.

### Work Packages And Authorization Gates

Only one package may be active at a time. Each slice adds/fixes focused tests
before deleting its old physical root file.

1. **WP-00: read-only inventory and freeze.** Inventory all source, test,
   documentation, build, module-execution, lazy-import, symbol identity, and
   patch callers for the ten root modules. Record required `__name__`,
   `__package__`, `__file__`, `sys.modules`, package-attribute, and `python -m`
   behavior. Reconcile the destination map before any source edit.
2. **WP-01: fail-closed contracts first.** Extend structure, source-layout,
   facade debt, import, alias/loader, packaging, wheel, sdist, and editable
   tests to describe the intended five-root outcome while retaining tests for
   the current state during staged migration. Register any new test script in
   the baseline inventory and capability ledger.
3. **WP-02: low-risk owner routes.** Redirect internal imports to
   `core.contracts`, `core.errors`, `adapters.lfs.pointer`, and
   `infrastructure.runtime`; implement explicit historical routes for
   `cli_contracts`, `exceptions`, `lfs_pointer`, and `runtime`; prove identities
   and patch behavior before physical removal.
4. **WP-03: version and build authority.** Create
   `infrastructure/version.py`, update package imports and `setup.py` build-time
   reading without importing runtime dependencies, preserve `atomgit.version`,
   and verify source/wheel/sdist version identity.
5. **WP-04: release compatibility.** Move the historical forwarding surface to
   `compatibility/release.py`, retain all established symbols and patch seams,
   and add a narrow meta-path loader only if required to preserve executable
   `atomgit.release` behavior without a physical root file.
6. **WP-05: completion and uninstall compatibility.** Move composite facades
   to `compatibility`, preserve every cross-owner assignment/deletion seam,
   managed-path and environment safety, and prove the completion schema path
   remains lightweight before deleting the root files.
7. **WP-06: config module/singleton compatibility.** Resolve the
   `atomgit.config` module versus package-level `atomgit.config` singleton
   collision explicitly. Preserve `Config`, the shared singleton, lazy config
   reads, private modes, atomic writes, and import-order behavior in clean
   processes and installed artifacts.
8. **WP-07: utility composite compatibility.** Move only forwarding and patch
   maps to `compatibility/utils.py`; keep validation, filesystem, output,
   cache, and Git credential behavior in their existing infrastructure owners.
   Verify every public and registered private seam, including `os.walk`,
   `subprocess.run`, output helpers, and Git-helper transaction helpers.
9. **WP-08: alias/loader cutover and exact deletion gate.** Prove all ten old
   imports in source, editable, wheel, and sdist environments with the physical
   root files absent in a temporary copy. Stop for explicit authorization to
   delete exactly `cli_contracts.py`, `completion.py`, `config.py`,
   `exceptions.py`, `lfs_pointer.py`, `release.py`, `runtime.py`,
   `uninstaller.py`, `utils.py`, and `version.py`; do not use a broad glob or
   recursive deletion.
10. **WP-09: physical closure and artifact reconciliation.** After exact
    deletion authorization, remove only the approved files, tighten the root
    allowlist to the five entry files, update owner/edge/debt and artifact
    declarations, and reconcile the smallest authoritative architecture,
    testing, development-floor, and packaging documentation.
11. **WP-10: final verification and review.** Run focused suites, complete
    offline baseline, build/install smoke, compile/dependency/diff/security
    checks, independent review, fix all findings, rerun gates, and request human
    acceptance. Commit, merge, and push remain separately authorized actions.

### Focused Tests And Evidence

- Add an exact root-file contract that fails on a sixth root `.py`, a missing
  required entry file, or any recreated historical first-level directory.
- Test all ten historical imports in fresh subprocesses, in multiple import
  orders, with and without completion mode, and from source, PEP 660 editable,
  wheel, and sdist installations isolated from the worktree.
- Compare public/tested-private symbol presence, `inspect.signature`, callable
  identity, class identity, singleton identity, exception inheritance,
  `__all__`, package exports, `sys.modules`, assignment, deletion, and
  `patch.object` restoration against the pre-migration contract.
- Verify `atomgit --help`, `atomgit --version`, `python -m atomgit --help`,
  `python -m atomgit.cli --help`, and
  `python -m atomgit.cli.__main__ --help` without warnings. Test historical
  release module execution only if WP-00 proves it is an existing contract.
- Preserve and extend `test_infrastructure_utils_ownership.py`,
  `test_environment_lifecycle_ownership.py`, `test_runtime_policy.py`,
  `test_config_permissions.py`, `test_import_order_contract.py`,
  `test_public_import_contract.py`, `test_api_facade_conversion.py`,
  `test_cli_facade_conversion.py`, `test_sdk_domain_ownership.py`,
  `test_src_layout_migration.py`, `test_structure_guard.py`,
  `test_packaging_metadata.py`, and `test_wheel_smoke.py`.
- Prove no compatibility facade adds business definitions, concrete network
  calls, credential persistence, broad dynamic imports, heavy schema-only
  dependencies, cycles, unregistered edges, or duplicate implementation.
- Verify the build backend reads one version authority without importing the
  AtomGit runtime or user configuration.
- Keep the monotonic ledger at 27 capabilities and 116 invariants unless an
  explicitly reviewed replacement is required. Every new `test_*.py` joins the
  exact baseline inventory and at least one affected capability.

### Required Final Commands

All Python and project commands run in the `atomgit_cli` conda environment:

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate atomgit_cli
python tests/run_cli_baseline.py
python -m compileall -q .
python -m pip check
git diff --check
```

Also run the focused import/identity/patch suites, structure/layout suites,
source/editable/wheel/sdist smoke, installed-entry probes, locked dependency
signature checks, issue-owned Black/isort/Ruff clean policy, and credential,
generated-artifact, bytecode, and repository-leak scans.

### Out Of Scope

- New CLI, native SDK, or historical `atomgit_hub` capabilities or parameters.
- Dependency upgrades, version release, publication, broad formatting cleanup,
  remote Issue/PR operations, or unrelated roadmap work.
- Remote AtomGit repository creation, deletion, visibility/branch changes,
  upload, download, LFS, credential mutation, or fixture cleanup. The separate
  comprehensive test plan for `test_model` and `test_datasets` is not started
  by this Issue plan.
- Removing `__init__.py`, `__main__.py`, `api.py`, `cli.py`,
  `atomgit_hub.py`, or top-level `src/atomgit_hub.py`.
- Silently breaking a historical import or patch seam because it is private;
  any unpreservable path requires an explicit compatibility decision.

### Acceptance Criteria

1. `src/atomgit` contains exactly seven first-level directories and exactly
   the five approved root Python files.
2. The ten former root module paths remain importable through finite explicit
   compatibility routes in source, editable, wheel, and sdist environments.
3. Canonical implementations remain in the destination layers listed above;
   compatibility owns only path/signature/identity/patch translation.
4. CLI, native `AtomGitClient`, historical `atomgit_hub`, package exports,
   config singleton, errors, lifecycle, utilities, release, LFS pointer,
   runtime, and version behavior pass focused equivalence tests.
5. Completion imports remain lightweight; module execution paths are warning
   free; no new cycle, forbidden edge, facade business definition, duplicate
   owner, unowned module, or stale artifact path exists.
6. The exact structure, package metadata, source/editable/wheel/sdist, security,
   portability, locked dependency, compile, dependency, and diff gates pass.
7. The complete offline baseline passes with all 27 capabilities and 116
   invariants accounted for, or an explicitly authorized replacement record.
8. Independent review has no open P0/P1/P2 finding, human acceptance is
   recorded, and all unrun tests and residual risks are explicit before any
   delivery action.

### Authorization And Handoff

- The maintainer authorized recording this complete local development Issue
  plan on `2026-08-25` after R7 was completed and pushed.
- The maintainer authorized R8 implementation and creation of the local task
  branch on `2026-08-25`.
- The maintainer separately authorized deletion of exactly the ten listed root
  files on `2026-08-25`; no broad glob or recursive deletion was used.
- The maintainer accepted the final verification and authorized commit/push on
  `2026-08-25`; task commit `bd859b7` was merged as `5c342ce` and only
  `github/yuto` was pushed. Live tests, publication, remote Issue/PR operations,
  and unrelated remote writes were not authorized or performed.

## Historical R7 Delivery Evidence

### WP-00/WP-01 Evidence

- Authorization: `the maintainer explicitly authorized implementation in the current conversation`
- Frozen canonical directories: `adapters`, `compatibility`, `core`, `domain`, `infrastructure`, `interfaces`, `usecases`
- Frozen root Python compatibility allowlist: `__init__.py`, `__main__.py`, `api.py`, `atomgit_hub.py`, `cli.py`, `cli_contracts.py`, `completion.py`, `config.py`, `exceptions.py`, `lfs_pointer.py`, `release.py`, `runtime.py`, `uninstaller.py`, `utils.py`, `version.py`
- Current physical result: `src/atomgit contains exactly adapters, compatibility, core, domain, infrastructure, interfaces, and usecases; the nine historical first-level directories are absent`
- Contract changes: `tests/structure_contract.py`, `tests/test_src_layout_migration.py`, and `tests/test_structure_guard.py` now fail closed on an eighth directory or an unlisted root Python file; ARCH-004 is registered in the development-floor ledger
- Verification: `python tests/test_development_floor.py passed 15/15; post-deletion layout passed 9/9, structure passed 15/15, wheel/sdist/editable smoke passed 38/38, and python tests/run_cli_baseline.py passed 92/92 in 85.39s after the final review fix`

### WP-02 CLI Slice Evidence

- Canonical owner: `src/atomgit/interfaces/cli/commands/{authentication,lifecycle,repositories,transfers}.py`
- Compatibility surface: `compatibility.legacy_packages` dynamically registers historical command imports against canonical modules and preserves module identities and patch seams without a physical commands directory
- Lazy boundary: `src/atomgit/interfaces/cli/__init__.py` exposes only a deferred `run`; native adapters now live in `interfaces/cli/runner.py`, keeping completion schema paths free of Hugging Face imports
- Packaging: `pyproject.toml`, `setup.py`, source-layout, structure ownership, wheel, and sdist contracts include the new nested interface package
- Physical result: `the historical CLI command directory is absent; focused schema, callback, import, identity, and patch-seam checks pass through runtime aliases`

### WP-02 SDK And Facade Cutover Evidence

- Canonical SDK owners: `adapters.sdk_common`, `sdk_datasets`, `sdk_downloads`, `sdk_errors`, `sdk_repositories`, and `sdk_uploads`; every `sdk/*` module is a compatibility alias
- Canonical API/CLI assembly: `compatibility.api` and `compatibility.cli`; frozen root `api.py` and `cli.py` shims preserve imports and module execution after the old package directories were removed
- Compatibility proof: SDK ownership 20/20, API facade 8/8, CLI facade 9/9, CLI command ownership 13/13, public imports 8/8, and import-order 5/5

### WP-03 Authentication And Repository Evidence

- Canonical owners: `compatibility.authentication`, `compatibility.repositories`, and `adapters.atomgit_v5`; historical services imports are runtime aliases and no physical services directory or ownership domain remains
- Locked dependency evidence: installed `huggingface_hub==1.1.7` `create_repo` and `HfApi.__init__` signatures match every changed call site
- Verification: authentication/repository ownership 25/25 and API facade 8/8

### WP-04 Transfer Evidence

- Canonical owners: `adapters.download`, `compatibility.download`, `adapters.upload`, `adapters.lfs`, and `adapters.sdk_uploads`; historical download/upload/LFS imports resolve through runtime aliases with no old physical directories
- Upload defaults now have one `core.contracts` authority and are forwarded by adapter/root compatibility contracts
- Verification: download ownership 20/20, upload ownership 17/17, LFS ownership 14/14, packaging metadata 13/13, and wheel/editable smoke 37/37

### WP-05 Lifecycle Evidence

- Canonical owners: `infrastructure.completion`, `environment`, `managed_paths`, `uninstall`, and `release`; historical lifecycle imports plus root completion/uninstaller and release paths preserve identities and patch seams through compatibility forwarding without a physical lifecycle directory
- Verification: lifecycle ownership 26/26, shell completion 19/19, uninstaller 14/14, release/update focused suites, import-order 5/5, packaging 13/13, and wheel/editable smoke 37/37

### WP-06 Physical Closure Evidence

- `compatibility.legacy_packages` registers historical commands/download/LFS/lifecycle/SDK/services/upload packages and child modules directly against canonical owners during normal imports without loading them on completion-only paths
- A temporary source copy containing only the seven canonical directories and frozen root Python shims passed all representative historical imports and `python -m atomgit.cli --help`
- The maintainer explicitly authorized deletion of the nine exact old directories on `2026-08-25`; only those resolved repository paths were removed, including their ignored bytecode caches
- The real tree now contains exactly the seven canonical first-level directories; source ownership, dependency edges, package discovery, wheel/sdist declarations, and facade debt ceilings no longer register deleted physical modules
- Post-deletion layout is 9/9, structure is 15/15, packaging metadata is 13/13, and the nine focused compatibility/ownership suites pass 152/152

### WP-07 Final Gate And Review Evidence

- Complete offline baseline: `python tests/run_cli_baseline.py` passed 92/92 in
  85.39s after the final review fix.
- Artifact and entry proof: wheel/sdist/editable smoke passed 38/38, including
  exact contents, console and module help, all historical imports, and
  warning-free installed `python -m atomgit.cli.__main__ --help`.
- DoD proof: `python -m compileall -q .`, `python -m pip check`, packaging clean
  policy 13/13, and `git diff 23c6d7d --check` pass; locked versions and real
  callable signatures remain `huggingface-hub==1.1.7` and `datasets==4.4.1`.
- Security/artifact proof: no credential-shaped additions, tracked build
  artifacts, bytecode, or unrelated paths were found in the complete R7 diff.
- Formatting audit: repository-wide Black/isort/Ruff retain the exact registered
  historical debt (79 files, 82 files, and 15 files/44 findings respectively);
  Issue-owned files pass Black, isort, and Ruff through the clean policy gate.
- Independent review: initial P2 for a successful but warning-producing private
  CLI module execution was fixed with an exact meta-path loader and new source
  plus installed regressions. Final verdict `APPROVED`; no open P0/P1/P2/P3
  findings.

## Historical Completed Issue: R7 Seven-Directory Physical Closure

- Remote Issue: `none; no remote Issue was created`
- ID: `LOCAL-R7-SEVEN-DIRECTORY-PHYSICAL-CLOSURE`
- Title: `Migrate the source tree to exactly seven responsibility directories without losing existing capabilities`
- Primary type: `refactoring`
- Secondary types: `architecture`, `compatibility`, `cli`, `sdk`, `testing`, `packaging`, `documentation`, `portability`
- Priority: `P1`
- Status: `completed, accepted, merged, and pushed on 2026-08-25`
- Delivery: `task commit 2e781d9 -> local no-ff merge 8a93aa6 -> github/yuto push -> local/tracking/ls-remote equality verified at 8a93aa6d8344f18b1be0edd6a44b6fb46054d3d3`

### Objective

Make the physical source layout under `src/atomgit` converge to exactly these
seven first-level responsibility directories and no others:

```text
src/atomgit/
├── core/
├── domain/
├── usecases/
├── interfaces/
├── adapters/
├── compatibility/
└── infrastructure/
```

These are the permanent architecture standard for all future CLI and SDK
development. New business or technical implementation must be added under one
of these seven directories according to its layer; historical paths may remain
only as explicitly listed root-level `.py` entry shims or as runtime aliases
registered by `compatibility`, never as additional first-level directories.

The migration is behavior-preserving. Existing user-visible capabilities must
not be removed; their implementation is moved to the appropriate canonical
layer, while public CLI/SDK/API entry behavior remains available through the
new interfaces and compatibility conversion.

### Current Evidence And Problem Statement

- The current tree has exactly seven first-level directories under `src/atomgit`;
  the nine noncanonical directories are physically absent.
- Canonical implementation ownership has moved into the seven target
  directories, and legacy services, SDK, lifecycle, transfer, command, API,
  and CLI paths no longer own business implementation.
- `tests/test_src_layout_migration.py` and `tests/test_structure_guard.py` enforce
  the exact seven-directory allowlist and pass after physical deletion.
- The prior R1-R6 packages proved runtime ownership and compatibility slices,
  but did not satisfy this newly clarified physical layout requirement.

### User Impact

No intended loss of existing capability. Preserve the CLI schema, defaults,
Chinese output, prompts, progress, exits, public SDK/API functions, signatures,
returns, error categories, package entry paths, token safety, temporary-resource
lifetime, global-state restoration, and supported upload/download/repository/
lifecycle behavior. Physical module identity may change where required by the
strict seven-directory target; any public or tested private path that cannot be
preserved must be reported before deletion rather than silently broken.

### Affected Capability IDs

`FLOOR-REGISTRY`, `ARCHITECTURE`, `CLI-SURFACE`, `CLI-DISPATCH`, `AUTH-CONFIG`,
`GIT-CREDENTIAL`, `REPO-MANAGEMENT`, `REVISION`, `UPLOAD-FILE`, `UPLOAD-FOLDER`,
`UPLOAD-RESUMABLE`, `UPLOAD-LFS`, `UPLOAD-LFS-RECOVERY`, `DOWNLOAD-SNAPSHOT`,
`DOWNLOAD-FILE`, `DOWNLOAD-INTEGRITY`, `DOWNLOAD-SECURITY`, `SDK-DOWNLOAD`,
`SDK-UPLOAD`, `SDK-REPO`, `REPO-ID`, `RUNTIME`, `CACHE`, `PACKAGING`,
`PORTABILITY`, `DEPENDENCY-CONTRACT`, `ERROR-REDACTION`.

### Protected Existing Invariants

- CLI command names, options, defaults, output, prompts, progress behavior,
  callback identities, exit codes, and both Python/console entry paths remain
  compatible.
- Public imports and symbols from `atomgit`, `atomgit.api`, `atomgit.cli`,
  `atomgit_hub`, completion, uninstall, and legacy HF-style SDK functions keep
  their signatures, primary returns, exception mapping, and patch behavior.
- Shared usecase routing, repository/revision/type/token policies, upload/LFS
  pointer verification, download checksum/resume/prune/path safety, release and
  lifecycle state restoration, and locked HF Hub/datasets call signatures remain
  unchanged.
- No token, signed URL, secret-bearing cause, generated artifact, or real
  credential content enters source, tests, documentation, logs, or handoff.

### New Or Changed Invariants

- `src/atomgit` contains exactly seven first-level directories listed above;
  any eighth directory fails the structure gate.
- Every production `.py` file belongs to one of the seven directories or to an
  explicit, finite root-file compatibility allowlist; unlisted files fail
  source-layout, packaging, and artifact checks.
- `core`, `domain`, `usecases`, `interfaces`, `adapters`, and `infrastructure`
  contain canonical implementation only; `compatibility` contains historical
  path/signature/identity/patch conversion only and no business orchestration.
- All future CLI and SDK capability work enters through `interfaces`, shared
  `usecases`, `domain`, `core`, `adapters`, and `infrastructure`; no new
  implementation may be added to a historical root shim.
- Existing public capabilities remain reachable after physical directory
  removal; compatibility tests compare observable behavior and canonical owner
  identity rather than requiring legacy directory identity.
- Structure, source-layout, package artifact, import, and ownership tests fail
  closed on legacy directory reintroduction, duplicate implementations, stale
  artifact declarations, unowned files, forbidden edges, or facade business
  logic.

### Layer Responsibilities

- `core/`: stable contracts, ports, errors, policies, parity and shared
  low-level invariants; no Click, HF, V5, or concrete transport calls.
- `domain/`: pure authentication, repository, transfer, revision, and success
  rules; no UI, filesystem side effects, or concrete network calls.
- `usecases/`: ordered business workflows, reconciliation, rollback, and final
  state verification; no printing or process exits.
- `interfaces/`: CLI presentation/Click dispatch and native SDK request/result
  mapping; no duplicated remote business rules.
- `adapters/`: HF 1.1.7, AtomGit V5, upload/download/LFS transport, filesystem,
  checksum, manifest, cache, and other external technical boundaries.
- `compatibility/`: historical imports, signatures, defaults, returns,
  exception conversion, identities, and patch seams; no new implementation.
- `infrastructure/`: configuration, credentials persistence, runtime state,
  filesystem facilities, Git helpers, completion, installation, update,
  uninstall, and distribution/lifecycle technical facilities.

### Migration Map

The following is the required default destination map. WP-00 may refine a
specific file's destination only with a recorded owner rationale; it may not
create another first-level directory.

| Current path | Canonical destination | Required treatment |
|---|---|---|
| `commands/` | `interfaces/cli/` | Move Click command implementations and presentation; keep no business owner here. |
| `sdk/` | `interfaces/sdk/` plus `compatibility/` | Native SDK mapping belongs in `interfaces/sdk`; legacy HF-style conversion belongs in `compatibility`. |
| `download/` | `adapters/download/` plus `compatibility/` | Move technical download behavior to adapters; preserve public legacy conversion without the old directory. |
| `upload/` | `adapters/upload/` plus `compatibility/` | Move ordinary/resumable/projection/error behavior to adapters; preserve old calls through compatibility. |
| `lfs/`, `lfs_pointer.py` | `adapters/lfs/` plus `compatibility/` | Move protocol, pointer, attributes, and recovery ownership to adapters. |
| `services/` | `domain/`, `usecases/`, `adapters/`, `compatibility/` | Split rules, orchestration, V5 transport, and historical wrappers by layer; no services owner remains. |
| `lifecycle/` | `infrastructure/` | Move completion, environment, managed paths, uninstall, and installation provenance. |
| `api/` | `compatibility/` plus an approved root shim | Keep `HuggingFaceAPI` and singleton compatibility assembly only; implementation resolves to canonical owners. |
| `cli/` | `interfaces/cli/` plus an approved root shim | Keep Click schema/module execution compatibility while implementation lives in the interface layer. |
| `atomgit_hub.py` | `compatibility/` plus the top-level package shim | Keep the existing top-level SDK entry, forwarding only to canonical owners. |
| `release.py` | `infrastructure/release.py` plus an approved root shim | Preserve historical release imports and patch seams while infrastructure owns behavior. |
| root `config.py`, `runtime.py`, `utils.py`, `completion.py`, `uninstaller.py`, `version.py`, `exceptions.py`, `cli_contracts.py` | `infrastructure/`, `core/`, or `interfaces/cli/` by responsibility | Move implementation first; retain only explicitly approved root shims required by public imports. |

### Compatibility And Root-File Rules

- Public compatibility is defined by observable imports, symbols, signatures,
  returns, errors, entry paths, and documented patch seams, not by retaining an
  old directory.
- The root `.py` allowlist must be frozen during WP-00 after auditing public
  imports, console/module entry paths, packaging, and lazy-import behavior. No
  generic or unbounded shim set is permitted.
- The draft allowlist must explicitly account for `atomgit`, `python -m atomgit`,
  `python -m atomgit.cli`, the console script, `atomgit.api`, `atomgit_hub`,
  completion/uninstall/config/utils imports, and any release or pointer path
  proven public by tests or documentation.
- Private paths such as `atomgit.download.service`, `atomgit.upload.service`,
  `atomgit.lfs.service`, `atomgit.services.repositories`, `atomgit.sdk.uploads`,
  and `atomgit.cli.__main__` must be inventoried. Preserve them only when a
  strict seven-directory layout permits a real alias; otherwise report the
  exact path, callers, and break risk before deletion.
- No compatibility shim may import heavy HF dependencies on schema-only paths,
  contain a second implementation, or grow without an owner and test.

### Work Packages And Authorization Gates

Only one package may be active at a time.

1. **WP-00: read-only inventory and migration freeze**. Record every current
   file, import, public/private path, owner, caller, test, artifact, and root
   shim candidate. Produce the final seven-directory map and root-file allowlist.
   This package does not edit source and is the next action after implementation
   is explicitly activated.
2. **WP-01: executable physical-layout contract**. Add/update the exact
   first-level directory allowlist, root-file allowlist, owner map, dependency
   edges, duplicate-definition checks, and wheel/sdist expectations. Register
   every new test in the development floor and baseline inventory.
3. **WP-02: interface and compatibility migration**. Move command and SDK
   presentation/mapping code into `interfaces`; build compatibility conversion
   and patch-seam registration without changing observable behavior.
4. **WP-03: authentication and repository migration**. Split old services into
   domain rules, usecase orchestration, V5 adapters, infrastructure config/Git,
   and compatibility wrappers. Re-run focused ownership and behavior suites.
5. **WP-04: download, upload, and LFS migration**. Move all technical transfer
   code to adapters, preserve request keywords, temporary lifetimes, global
   state, checksums, resume/prune, pointer verification, and legacy conversions.
6. **WP-05: lifecycle and distribution migration**. Move completion, uninstall,
   runtime, release, and installation facilities to infrastructure and verify
   console/module entry behavior.
7. **WP-06: compatibility cutover and old-directory deletion**. First prove all
   capabilities and artifacts pass with the old directories unused. Then stop
   and request the separate destructive deletion confirmation. Delete only the
   exact old-directory targets approved by the migration map; do not use broad
   recursive deletion.
8. **WP-07: final gate and handoff**. Run the complete offline baseline and all
   structural, import, packaging, installed-entry, security, portability,
   compile, dependency, and diff checks; obtain independent review and human
   acceptance. Commit, merge, and push remain separate authorizations.

### Focused Tests And Evidence

- Add a fail-closed physical-tree test that compares actual first-level
  directories and root files with the frozen allowlists.
- Update `tests/structure_contract.py`, `tests/test_structure_guard.py`,
  `tests/test_src_layout_migration.py`, packaging contracts, and artifact tests
  so legacy directories cannot be accepted merely because they are registered.
- Add AST/import tests for one canonical owner per implementation, no duplicate
  business definitions, no direct external calls from interfaces/domain, no
  compatibility business orchestration, and no future legacy-directory growth.
- Preserve and extend CLI schema/dispatch, public import/signature/identity,
  patch/lazy-import, upload/LFS, download, lifecycle, dependency-signature,
  security, source/editable/wheel/sdist, and installed-entry regressions.
- Every new `test_*.py` must be registered exactly once in the development-floor
  ledger and `tests/run_cli_baseline.py` inventory.
- Required final offline commands, in the `atomgit_cli` environment:
  `python tests/run_cli_baseline.py`, `python -m compileall -q .`,
  `python -m pip check`, and `git diff --check`; run applicable Black, isort,
  Ruff, artifact/credential scans, and package smoke tests.
- Live repository operations, credential mutation, publication, and remote
  writes are not part of this Issue unless separately authorized.

### Out Of Scope

- New CLI/SDK product capabilities, dependency upgrades, broad formatting debt,
  publication, or unrelated roadmap work.
- Silent removal of public behavior or private paths without the WP-00 audit and
  maintainer decision.
- Remote repository creation/deletion, live upload/download, credential helper
  mutation, remote Issue/PR changes, commit, merge, or push without separate
  authorization.

### Acceptance Criteria

The Issue cannot close until all of the following are true:

1. The actual `src/atomgit` tree contains exactly the seven target directories,
   and every root `.py` file is on the approved finite allowlist.
2. All old first-level directories are removed only after the separate deletion
   gate, and no production import or package artifact depends on them.
3. Every existing capability has one canonical owner in the seven-layer model;
   compatibility contains forwarding/conversion only.
4. Public CLI, SDK/API, entry, signature, return, exception, patch, security,
   temporary-resource, global-state, packaging, and locked-dependency contracts
   pass focused regressions and the complete baseline.
5. Structure and artifact tests fail closed on an eighth directory, an unlisted
   root file, a duplicate implementation, a stale path, or a new legacy owner.
6. `.ai/ARCHITECTURE.md`, `docs/architecture.md`, the development-floor ledger,
   and this handoff describe the verified current tree rather than the former
   transitional layout.
7. Compile, dependency, diff, packaging, installed-entry, security,
   portability, independent review, and human acceptance gates pass; remaining
   unrun remote evidence is recorded explicitly.

### Authorization And Handoff

- The maintainer authorized the seven-directory target, capability-preserving
  migration, physical identity changes where necessary, replacement of stale
  structure/packaging/documentation contracts, and eventual old-directory
  removal as the scope of this Issue.
- Implementation start was explicitly authorized; WP-00 through WP-05 and the
  non-destructive WP-06 compatibility cutover are complete.
- The maintainer separately authorized deletion of exactly the nine approved
  directories on `2026-08-25`; WP-06 physical deletion is complete.
- The maintainer explicitly authorized one pre-deletion checkpoint commit and
  push of the current task branch on `2026-08-25`.
- On `2026-08-25`, after reviewing the final plan and repository state, the
  maintainer explicitly marked R7 complete, granted human acceptance, and
  authorized the cohesive final task commit, local merge into `yuto`, and push
  of only `yuto`. The task branch must not be pushed again.
- Remote Issue/PR changes, publication, credential mutation, and live remote
  tests remain unauthorized. The planned comprehensive remote matrix was not
  run and is retained as residual evidence rather than reported as passing.
- R7 is closed and must not resume as an active Issue. Future work uses the R8
  contract at the top of this file, while preserving the delivered seven-directory
  result and reconciling any newer `yuto` state before implementation.

## Historical Completed Issue: R6 Lifecycle Facade Closure

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-R6-LIFECYCLE-FACADE-CLOSURE`
- Title: `Move release/update technical ownership behind infrastructure while preserving the historical facade`
- Primary type: `refactoring`
- Secondary types: `architecture`, `compatibility`, `cli`, `sdk`, `testing`, `packaging`, `documentation`
- Priority: `P1`
- Delivery: `local implementation -> focused/full offline verification -> independent review -> human acceptance; commit, merge, push, and remote writes remain unauthorized`

### Objective

Make `infrastructure.release` the canonical technical owner of release/update
validation, bounded downloads, installation, and post-install verification.
Keep historical `atomgit.release` as a compatibility facade with the exact
existing exports, identities, signatures, returns, errors, and monkeypatch
seams. The migration must preserve CLI update behavior and package artifacts.

### User Impact

No intended user-visible behavior change. Existing update/uninstall/completion
commands, release helper imports, signatures, error categories, temporary
resource lifetime, bounded network behavior, and package entry points remain
exact.

### Affected Capability IDs

`FLOOR-REGISTRY`, `ARCHITECTURE`, `CLI-DISPATCH`, `RUNTIME`, `PACKAGING`,
`PORTABILITY`, `ERROR-REDACTION`.

### Protected Existing Invariants

- CLI schema, defaults, Chinese output, exit codes, and callback identities
  remain unchanged.
- Historical `atomgit.release` imports, symbol identities, signatures, return
  values, errors, assignment/deletion patch propagation, and lazy imports
  remain unchanged.
- Release validation, bounded response/asset sizes, redirect origin policy,
  temporary wheel lifetime, subprocess ordering, and source/editable install
  detection remain unchanged.

### New Or Changed Invariants

- `infrastructure.release` is the sole technical owner of release/update
  behavior; historical `atomgit.release` contains only forwarding and seam
  registration.
- Structure and ownership tests fail closed if release business definitions or
  direct release transport calls return to the historical facade.

### In Scope

- release owner module, historical facade/export/patch-seam forwarding, owner
  and dependency contracts, packaging/artifact declarations, focused offline
  regressions, architecture documentation, complete baseline, DoD checks, and
  independent review.

### Out Of Scope

- new release features or public parameter changes;
- upload/LFS behavior, dependency upgrades, broad formatting, or publication;
- live upload, repository/branch creation or deletion, credential mutation,
  publication, remote Issue/PR actions, commit, merge, or push.

### Focused Tests And Evidence

- fail-closed release owner/facade and lifecycle tests;
- release workflow, installer, structure, packaging, and installed artifact
  suites;
- `python tests/run_cli_baseline.py`, `python -m compileall -q .`,
  `python -m pip check`, formatting/static debt audit, and `git diff --check`.

### Acceptance Criteria

1. `infrastructure.release` owns all release/update technical behavior.
2. `atomgit.release` preserves every registered identity, signature, return,
   error, lazy-import, assignment/deletion, and monkeypatch seam.
3. Lifecycle, packaging, artifact, and security contracts pass the focused and
   complete offline suites.
4. Structure gates fail closed on facade business logic, forbidden dependency
   edges, missing owners, or stale artifacts.
5. Architecture and durable task evidence match the source and Git state;
   independent review has no open blocking finding before acceptance.

### Authorization

The maintainer's explicit `继续按照本地开发 issue 进行开发` request activates
this local R6 package. Commit, merge, push, remote Issue/PR changes, live
remote operations, credential changes, release, and publication remain
unauthorized.

### Complete Baseline Evidence

`python tests/run_cli_baseline.py` passed 92/92 in 86.06s in the `atomgit_cli`
environment (offline). Compileall, pip check, diff check, packaging metadata,
source-layout, wheel/sdist, structure, import-order, completion, lifecycle and
release ownership, dependency signature, and public import checks passed. No
live release download/publication or credential mutation was run.

### Independent Review

`APPROVED` on 2026-08-25. Independent review of the R6 diff found no open
P0/P1/P2/P3 findings. Review covered release owner edges, historical module
identity and patch propagation, module execution compatibility, source/editable/
wheel/sdist artifacts, security/state behavior, and the complete offline
evidence.

### R6 Exit-Gate Evidence

- `infrastructure.release` owns release/update validation, bounded asset
  transport, installation, and post-install verification; `atomgit.release`
  is a forwarding facade with preserved identities and patch seams.
- Structure, lifecycle ownership, source-layout, packaging, release workflow,
  deploy, public import, and complete baseline checks passed.
- Residual risk: release downloads/publication and remote update behavior remain
intentionally unrun; no credentials or remote state were changed.

### Human Acceptance And Delivery

Human acceptance and explicit commit/push authorization were granted in the
current conversation. Authorized delivery is one cohesive local task commit,
local no-ff merge into `yuto`, push of `yuto`, and remote equality verification.
The task branch remains local-only; no live release operation, credential
mutation, remote Issue/PR change, or publication is authorized.

### R5 Exit-Gate Evidence

- Canonical owners: `adapters.upload`, `adapters.lfs`, and
  `adapters.sdk_uploads`; historical `upload/`, `lfs/`, `lfs_pointer.py`, and
  `sdk/uploads.py` are import aliases with preserved identity and patch seams.
- Contracts updated: structure, packaging/source artifact, HF 1.1.7 call-site
  binding, upload/LFS/SDK ownership tests, and architecture documentation.
- Installation evidence: wheel/sdist smoke passed 37/37 in isolated venvs;
  completion/import-order remains free of Hugging Face imports on schema-only
  paths.
- Residual risk: controlled remote upload, resumable recovery, and LFS remote
  state/checksum evidence remain intentionally unrun; R6 is out of scope.

### Review Disposition

Human acceptance was granted by the maintainer's explicit request to commit
and push the completed R5 work. Delivery evidence is task commit `51d7410`,
merge commit `097a5bb`, and remote `github/yuto` verified at
`097a5bb1f507adac346bfad60bcc5fb198b80e46`. The task branch was not pushed;
no remote Issue transition, credential mutation, publication, or live remote
operation was performed.

### Corrective Work Package Status

| Package | Status | Scope boundary |
|---|---|---|
| `R0` evidence recovery and acceptance re-audit | `completed` | read-only reconciliation; identified P1 gaps; no source edits |
| `R1` executable architecture and call-path contract | `completed` | importable and invocation-level route checks; deliberate legacy bypass fixture fails closed |
| `R2` CLI shared-usecase wiring | `completed` | authentication, repository, upload, and download CLI paths use shared usecases; baseline and review passed |
| `R3` authentication/repository owner migration | `completed` | adapter owner, compatibility seams, focused evidence, baseline, and independent review passed |
| `R4` download owner migration | `completed` | unify CLI/native SDK download path, integrity, resume, prune, and repo policy |
| `R5` upload/LFS owner migration | `completed` | canonical adapter ownership, compatibility seams, offline gate, review, acceptance, and delivery completed |
| `R6` lifecycle and compatibility closure | `pending` | make compatibility the sole historical facade and place technical owners correctly |
| `R7` final gate, independent review, and human acceptance | `completed` | verified original intent, updated docs/evidence, and delivered the Issue |

Only one row may become `in_progress`; a later row cannot change status until
the preceding row has an exit-gate result recorded below or in a later durable
handoff. R0 is complete because the re-audit and baseline evidence are recorded;
R1 is complete because its invocation finding was fixed and its bypass fixture
fails closed; R2 is complete because its compatibility gate and independent
review passed; R3 is complete because its owner migration, baseline, and
independent review passed; R4 is complete because its technical owner migration,
compatibility regressions, final baseline, and independent review passed. Human
acceptance was granted before delivery and Issue closure.
Human acceptance for R3 was granted on 2026-08-24 with the instruction to
continue development; R4 was accepted in the current delivery request. No new
feature Issue may start without explicit activation after this corrective Issue.

### R1 Exit-Gate Evidence

- `src/atomgit/core/parity.py` now exposes `RUNTIME_ROUTE_REGISTRY` and
  `validate_runtime_routes()`, resolving every parity-required usecase, declared
  usecase method, CLI owner, and native SDK callable.
- `tests/test_architecture_parity.py` proves the complete registry, missing-route
  rejection, non-importable-route rejection, and legacy-bypass rejection; the
  focused script passes 18/18.
- The gate is intentionally limited to executable route declarations. It does not
  claim adapter technical ownership has already migrated; CLI adapters still
  delegate to historical API owners and that migration is assigned to R3.

### R1 Independent Review And Resolution

- Initial verdict: `REQUEST CHANGES`; resolved by the R2 implementation below,
  with a fresh review still required before R2 acceptance.
- `P1` resolution: `validate_runtime_routes()` now inspects CLI callback source
  for the registered `context.run_usecase()` operation and SDK source for its
  corresponding usecase delegate; a deliberate legacy owner fixture fails closed.
- `P1` runtime resolution: production command owners call the shared bridge;
  adapters remain legacy-backed by design for R2 and are the R3 boundary.
- `P2` mitigation: route operation/delegate contracts are executable and tested;
  remaining technical-owner duplication is explicitly tracked for R3.

### R2 Exit-Gate Evidence

- CLI authentication, repository, upload, and download command owners now call
  `context.run_usecase(...)`; the bridge preserves historical context patch
  seams while routing through `AtomGitClient` and the shared usecases.
- Upload request validation preserves `message`, worker count, and whether
  `repo_type` was explicitly supplied; focused regressions pass 16/16,
  17/17, and 49/49 for file, repo-type, and resumable behavior.
- Structural and ownership gates pass: `test_structure_guard.py` 14/14,
  `test_lfs_domain_ownership.py` 13/13, and packaging metadata 13/13.
- `python tests/run_cli_baseline.py` passes 92/92 isolated cases after the
  final fix; `compileall`, `pip check`, `git diff --check`, Black, and isort
  checks also pass. No live remote write or credential mutation was run.

### R2 Independent Review

- Verdict: `APPROVED` for the R2 package.
- Findings: no open P0/P1/P2/P3 findings within the R2 scope. The historical
  API-backed adapter ownership is intentional and remains the explicit R3
  migration boundary, not an R2 acceptance gap.
- Residual review risk: technical-owner duplication and controlled remote
  behavior remain unverified until R3 and authorized remote testing.

### R3 Authentication/Repository Owner Migration Evidence

- `src/atomgit/adapters/atomgit_v5.py` now owns the direct bounded V5 JSON
  transport, identity lookup, repository list/create/visibility/delete/branch
  operations, response parsing, error classification, and Hugging Face create
  boundary. It has no import edge to `api` or `services`.
- `services.authentication` and `services.repositories` retain only historical
  method signatures, output/return conventions, API class provenance, and
  patchable helper aliases; their methods delegate technical work to the
  canonical adapter. Old API helper assignments now propagate to the adapter.
- Repository creation preserves the logical (un-normalized) ID for the legacy
  visibility callback while using the normalized ID for the remote create call.
  Ambiguous visibility, deletion, and branch writes retain the old verified or
  unknown-state diagnostics.
- Focused evidence: authentication/repository ownership 24/24; login response
  bound 5/5; login error semantics 11/11; repository list 24/24; visibility
  30/30; deletion 48/48; branch 28/28; repository ID 68/68; structure 14/14;
  packaging metadata 13/13.
- Baseline: `python tests/run_cli_baseline.py` 92 passed in 80.22s in the
  `atomgit_cli` environment (offline). Compileall, dependency, and diff checks
  passed; no live remote writes or credential mutations were run.
- Review status: `APPROVED`. Initial review found a P1 compatibility gap where
  legacy direct branch calls could reach transport before revision validation;
  `AtomGitV5Adapter.create_branch` now rejects unsafe branch/source values before
  any request, with a focused regression. Final review found no open P0/P1/P2/P3
  findings.

### Audit Evidence And Decision

- Former implementation commit: `e927a4b refactor(architecture): align CLI and native SDK capabilities`
- Historical delivery records: `bc7b9ed`, `398beb1`, and `8d9490d` remain evidence of what was previously declared, not proof that the objective is currently satisfied.
- Re-audit decision: `REQUEST CHANGES`; the closed Issue's offline tests are green, but its final seven-directory runtime ownership and shared CLI/SDK usecase requirements are not met by the actual call graph.
- Blocking findings: `P1` CLI bypasses shared usecases; `P1` adapters depend on legacy business owners; `P1` parity registry does not verify runtime routing; `P2` compatibility ownership remains distributed.
- Remote evidence: `no live remote tests were run; controlled remote authorization remains limited to the dedicated test repositories`

The predecessor CLI Facade Conversion Issue and the architecture/parity Issue
remain historical records. Their prior completion claims are superseded for
acceptance purposes by this corrective Issue. The authoritative source state at
audit entry was clean `yuto` at `8d9490d`, equal to `github/yuto`; the current
task branch contains only this TASK activation change.

## Historical Completed Issue: R1-R5 Architecture Recovery

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-ARCH-CLI-SDK-PARITY-RECOVERY`
- Title: `Reopen architecture/parity delivery and drive runtime ownership to the seven-directory contract`
- Primary type: `refactoring`
- Secondary types: `architecture`, `compatibility`, `cli`, `sdk`, `testing`, `packaging`, `documentation`
- Priority: `P1`
- Delivery: `local task branch -> focused tests -> complete offline baseline -> independent review -> human acceptance -> cohesive commit 2056237 -> local no-ff merge 17ebd5a -> github/yuto push and equality verification`

### Objective

Reconcile the delivered architecture/parity Issue with its original intent. The
seven directories must become the actual canonical runtime ownership model, not
a parallel SDK facade over legacy business owners. CLI and native SDK entries for
every general remote capability must call one registered shared usecase, while
all existing CLI, legacy SDK, import, identity, signature, return, exception,
patch-seam, packaging, security, and state-restoration contracts remain stable.

This Issue is corrective and may not add unrelated product capabilities. It is
executed one work package at a time. A package is not complete because its
metadata exists; its exit gate must prove the real source/runtime behavior.

### Reproducible Evidence

- `python tests/run_cli_baseline.py` passes 92 isolated cases, so the current
  offline behavior is not showing an immediate regression.
- `python -m compileall -q .`, `python -m pip check`, `git diff --check`, and
  `python tests/test_structure_guard.py` pass.
- Production CLI command owners call `context.run_usecase`; the R2 bridge
  assembles `AtomGitClient` with context-preserving adapters.
- `adapters.atomgit_v5` and the HF adapter remain legacy-backed technical
  adapters by explicit R2 scope; R3 migrates those owners.
- The parity registry now resolves runtime symbols and checks CLI/SDK source
  delegation to the registered shared usecases, with a bypass fixture that
  fails closed.
- The `compatibility` package is a registry alias, while historical facade and
  patch logic remains distributed across multiple old paths.

### In Scope

- executable architecture and real call-path contracts;
- CLI-to-usecase wiring with exact presentation/exit compatibility;
- vertical migration of authentication, repositories, download, upload/LFS,
  and lifecycle owners;
- compatibility facade consolidation and patch-seam preservation;
- packaging/artifact declarations, structure tests, parity registry, and
  architecture documentation required by the migration;
- focused regressions, complete offline verification, independent review, and
  final human acceptance against the original objective.

### Out Of Scope

- new user-facing product capabilities unrelated to architecture compliance;
- intentional changes to existing CLI/SDK behavior without explicit migration
  authorization;
- dependency upgrades, broad formatting debt removal, or release work;
- live remote writes, repository creation/deletion, credential mutation, push,
  publication, or Issue state changes on a remote tracker without explicit
  authorization.

### Affected Capability IDs

`FLOOR-REGISTRY`, `ARCHITECTURE`, `CLI-SURFACE`, `CLI-DISPATCH`,
`AUTH-CONFIG`, `GIT-CREDENTIAL`, `REPO-MANAGEMENT`, `REVISION`, `UPLOAD-FILE`,
`UPLOAD-FOLDER`, `UPLOAD-RESUMABLE`, `UPLOAD-LFS`, `UPLOAD-LFS-RECOVERY`,
`DOWNLOAD-SNAPSHOT`, `DOWNLOAD-FILE`, `DOWNLOAD-INTEGRITY`,
`DOWNLOAD-SECURITY`, `SDK-DOWNLOAD`, `SDK-UPLOAD`, `SDK-REPO`, `REPO-ID`,
`RUNTIME`, `CACHE`, `DEPENDENCY-CONTRACT`, `PACKAGING`, `PORTABILITY`,
`ERROR-REDACTION`.

### Protected Existing Invariants

Existing command names, options, defaults, output, prompts, progress, exit
codes, public imports, object/class/function identities, signatures, return
values, exception categories, monkeypatch seams, locked HF/datasets calls,
package entry paths, token redaction, temporary-resource lifetime, global-state
restoration, installation/uninstallation behavior, and public/anonymous token
semantics remain unchanged. Existing legacy HF-style SDK functions remain
available with their compatibility semantics.

### New Or Changed Invariants

- Each parity-required capability has one executable shared usecase and both a
  CLI and native SDK route to that same usecase.
- Canonical `interfaces/usecases/domain/core/adapters/infrastructure` code has
  no dependency on legacy facades or legacy business owners.
- `compatibility` is the only owner of historical path/signature/identity/patch
  adaptation and contains no new business orchestration.
- The parity registry and structure guard fail closed on missing runtime routes,
  one-sided capabilities, new legacy dependencies, facade growth, unowned
  modules, cycles, stale artifacts, and missing focused evidence.
- New development work cannot add product behavior while this Issue has an open
  P1 exit gate.

### Focused Tests And Evidence

- Add a failing test for each real CLI/SDK/usecase route before changing it.
- Add structural tests that inspect import edges and runtime route identity,
  not only registry strings.
- Preserve and extend ownership, compatibility, dependency-signature,
  packaging, security, portability, and parity suites for each vertical slice.
- Run the complete `python tests/run_cli_baseline.py` after every corrective
  package and after the final review fix.
- Before closure also run `python -m compileall -q .`, `python -m pip check`,
  and `git diff --check`.
- Controlled remote evidence remains optional unless a package explicitly
  needs it; no live support claim may be made without authorized remote proof.

### Acceptance Criteria

The Issue cannot close until all of the following are true:

1. The actual CLI and native SDK call paths share the registered usecases for
   authentication, repositories, upload, download, revision, repo type, token,
   checksum, resume, prune, LFS, and final-state verification.
2. The seven-directory architecture is the canonical implementation location;
   old `services/download/upload/lfs/sdk` modules are compatibility or technical
   adapters only and do not receive new business logic.
3. Existing public and safety contracts listed above pass focused regressions
   and the complete baseline.
4. Structure/parity tests fail closed when a future contributor bypasses the
   canonical route or adds a one-sided CLI/SDK capability.
5. Architecture and development-floor documentation describe verified current
   behavior, and `TASK.md` evidence agrees with the real Git/source state.
6. All corrective packages have recorded exit-gate evidence, independent review
   returns `APPROVED`, and the human maintainer accepts the result against the
   original development intent.

## Historical Completed Issue

- Remote Issue: `none; do not create one without explicit authorization`
- ID: `LOCAL-ARCH-CLI-SDK-PARITY`
- Title: `Reorganize business architecture and align CLI and SDK capabilities`
- Primary type: `refactoring`
- Secondary types: `architecture`, `compatibility`, `cli`, `sdk`, `testing`, `dependency`, `packaging`, `documentation`
- Priority: `P1`
- Delivery: `local implementation -> focused/full offline verification -> independent review -> human acceptance -> authorized delivery`

### Objective

Complete two separate phases. Phase 1 establishes the final seven-directory responsibility
architecture with no observable behavior change. Phase 2 gives the native SDK
every CLI general remote/business capability while preserving old HF-style SDK
functions. An executable parity registry and structural gates prevent future
one-sided CLI/SDK capability debt.

Parity-required capabilities are authentication, repositories, upload, download,
revision, repo type, token, checksum, resume, prune, LFS, and final-state
verification. Completion, update, uninstall, Shell hooks, interactive config
display, and presentation remain CLI-only. CLI default macOS metadata filtering
is also CLI policy, not an SDK parity requirement; SDK ignore behavior remains
caller-controlled.

### User Impact

- Phase 1: no change to commands, options, defaults, output, prompts, exits, SDK signatures, returns, exceptions, imports, identities, entry paths, remote calls, credentials, installation, or uninstallation.
- Phase 2: new native SDK capabilities and structured results; old HF-style functions remain available with their compatibility semantics.
- A new general remote capability is incomplete until both CLI and native SDK interfaces exist.

### Affected Capability IDs

`FLOOR-REGISTRY`, `ARCHITECTURE`, `CLI-SURFACE`, `CLI-DISPATCH`,
`AUTH-CONFIG`, `GIT-CREDENTIAL`, `REPO-MANAGEMENT`, `REVISION`,
`UPLOAD-FILE`, `UPLOAD-FOLDER`, `UPLOAD-RESUMABLE`, `UPLOAD-LFS`,
`UPLOAD-LFS-RECOVERY`, `DOWNLOAD-SNAPSHOT`, `DOWNLOAD-FILE`,
`DOWNLOAD-INTEGRITY`, `DOWNLOAD-SECURITY`, `SDK-DOWNLOAD`, `SDK-UPLOAD`,
`SDK-REPO`, `REPO-ID`, `RUNTIME`, `CACHE`, `DEPENDENCY-CONTRACT`,
`PACKAGING`, `PORTABILITY`, and `ERROR-REDACTION`.

### Protected Existing Invariants

Existing CLI commands, options, defaults, output, prompts, exit codes, public
imports, function/class identities, signatures, return values, exception
categories, patch seams, locked Hugging Face/datasets calls, package entry
paths, credential redaction, temporary-resource lifetime, and process-global
state restoration remain unchanged unless explicitly listed as a new native SDK
surface. No remote write or credential mutation is required for offline
acceptance.

### New Or Changed Invariants

General remote capabilities have one registered shared usecase and both CLI and
native SDK entries. Native SDK operations return structured results and stable
redacted `AtomGitError` subclasses. Shared token, repository ID/type, revision,
checksum, resume, prune, LFS, and final-state policies are used by both entry
surfaces. CLI presentation and macOS metadata filtering remain CLI-only.

### Focused Tests And Evidence

Architecture/parity, structure, SDK result/error/token, compatibility, locked
dependency, packaging, security, portability, compile, and import contracts
are included in the complete offline baseline. The required command is
`python tests/run_cli_baseline.py` in the `atomgit_cli` environment, followed by
`python -m compileall -q .`, `python -m pip check`, and `git diff --check`.
Black/isort/Ruff are audited against the existing repository debt; broad debt
removal is outside this Issue.

### Complete Baseline Evidence

Final revalidation on 2026-08-24: `python tests/run_cli_baseline.py` passed 92
isolated cases in 92.32s; compileall, pip check, and git diff --check passed.

### Residual Risks

No live AtomGit upload/download/checksum/LFS tests were run. Controlled remote
authorization remains limited to the dedicated test repositories. Black,
isort, and Ruff still report pre-existing repository-wide formatting debt.

## Final Architecture

```text
src/atomgit/
├── core/
├── domain/
├── usecases/
├── interfaces/
├── adapters/
├── compatibility/
└── infrastructure/
```

Historical paths remain as thin facades, not additional business layers:

```text
atomgit/cli/   -> historical CLI, Click, console/module entry surface
atomgit/api/   -> historical HuggingFaceAPI and api singleton surface
atomgit_hub.py -> historical top-level SDK surface
```

Responsibilities:

- `core/`: Request/Result contracts, stable errors, ports, and shared policies; no Click, HF, V5, or concrete network imports.
- `domain/`: authentication, repository, upload, download, and LFS rules and success invariants; no UI or concrete external calls.
- `usecases/`: ordered create/list/visibility/branch/delete/upload/download operations and final-state verification; no printing or `sys.exit`.
- `interfaces/`: user layer. `interfaces/cli` owns Click, prompts, output, progress, exits. `interfaces/sdk` owns native Python methods, parameter mapping, Results, and public errors. Neither owns remote business logic.
- `adapters/`: outbound HF 1.1.7, AtomGit V5, filesystem/cache/manifest, and transport boundaries.
- `compatibility/`: old paths, signatures, defaults, returns, exception mapping, identities, and patch seams; no new business logic.
- `infrastructure/`: config, token persistence, runtime, cache, Git helper, completion, update, uninstall, and technical lifecycle facilities.

Dependency direction:

```text
interfaces / compatibility -> usecases -> domain -> core -> outbound adapters
```

Forbid new SDK-to-CLI dependencies, domain-to-HF/V5 imports, interface business
implementations, Shell copies of core rules, compatibility growth, cycles,
unowned modules, and direct external calls that bypass usecases/adapters.

## Execution Runbook

The Issue is executed as numbered work packages. Only one package may be
`in_progress`; later packages remain pending until the current package exit
gate is recorded. Each package has a bounded scope, focused evidence, a
checkpoint, and a defined next action. A failed gate keeps the same package
active; it never authorizes skipping forward. Phase 2 is locked until the Phase
1 gate is accepted. If a conversation ends mid-package, resume the same
worktree and package rather than creating a parallel branch.

### Package Rules

- Before editing: record entry HEAD, worktree state, changed-path scope,
  capability IDs, invariants, and the package gate.
- After editing: run focused checks, `git diff --check`, and the required
  baseline slice; record exact results and changed paths in this Issue.
- Do not mix Phase 1 behavior-preserving migration with Phase 2 new SDK APIs.
- A behavior difference in Phase 1 is a blocking regression, not a migration
  choice. Stop and repair the package-owned change.
- The historical implementation backup branch is read-only reference material;
  it is not evidence for the reopened implementation and must not be
  cherry-picked as a substitute for current tests.

### Phase 1 Work Packages

#### WP-00: Recovery, Scope, and Baseline Freeze

Entry: no source edits for this Issue. Read `AGENTS.md`, `.ai/README.md`, this
Issue, and required references (`MASTER_PROMPT.md`, `DEVELOPMENT_RULES.md`,
`DOD.md`, `ARCHITECTURE.md`, `STYLE_GUIDE.md`, `TESTING.md`,
`DEVELOPMENT_FLOOR.md`, `WORKFLOW.md`, `REVIEW.md`). Reconcile Git root,
branch, HEAD, worktrees, status, recent log, current source/tests/docs, owner
registries, and locked HF/datasets signatures.

Actions: run the pre-change `python tests/run_cli_baseline.py`; inventory CLI
commands/schema/dispatch, SDK exports/signatures, API/CLI identities and
patch seams, external calls, package/entry paths, global-state contracts, and
current owners. Do not classify the former implementation as current evidence.

Outputs: baseline result, reconciled entry snapshot, capability inventory,
file-level migration map, and confirmed worktree. Exit gate: no unresolved
state mismatch and baseline result recorded. Checkpoint before WP-01.

#### WP-01: Executable Architecture Contracts

Entry: WP-00 passed. Define real owner maps for `core`, `domain`, `usecases`,
`interfaces`, `adapters`, `compatibility`, and `infrastructure`; allowed and
forbidden edges; facade debt limits; compatibility seam registry; source and
installed package expectations; and the Phase 2 parity-registry schema.

Add focused fail-closed tests for unowned modules, cycles, forbidden edges,
facade business definitions, missing seams, stale paths, and missing parity
metadata. Do not add empty packages or new business behavior. Exit gate:
contracts pass against the unchanged tree or fail only on explicitly registered
target-state assertions, and the complete baseline still passes.

#### WP-02: Core Contracts and External Boundaries

Entry: WP-01 passed. Add only immediately used Request/Result/error/port
contracts. Define HF 1.1.7, AtomGit V5, filesystem/cache, and config/runtime
boundaries without moving business callers. Add strict installed-signature tests
and verify `core` has no Click/HF/V5/concrete transport import. Exit gate:
compile/import/order/contract tests and complete baseline pass.

#### WP-03: Infrastructure and Outbound Adapter Ownership

Entry: WP-02 passed. Move or wrap config, runtime, cache/manifest, filesystem,
Git-helper, HF, and V5 implementations behind their target owners while
preserving lazy imports, credential safety, global-state restoration, and
installed provenance. Do not migrate authentication/repository/upload/download
orchestration in this package. Exit gate: runtime, dependency, security,
ownership, packaging, and complete baseline tests pass.

#### WP-04: Authentication Vertical Slice

Entry: WP-03 passed. Move authentication rules into domain/usecase boundaries
and connect existing CLI/API facades through interfaces, without adding new SDK
public methods. Preserve login, logout, whoami, Git-helper, config, redaction,
and all error categories. Cover 401/403/429/5xx/network/timeout/malformed
responses and config permissions. Exit gate: focused auth/security/seam tests,
installed imports, and complete baseline pass.

#### WP-05: Repository Vertical Slice

Entry: WP-04 passed. Migrate create/list/visibility/branch/delete into one
repository usecase family. Preserve CLI output, API bool results, validation,
confirmation, visibility convergence, source-commit resolution, target-commit
verification, and delete absence verification. Do not add native SDK methods.
Exit gate: repository/revision/redaction/ownership/import/packaging tests and
complete baseline pass.

#### WP-06: Download Vertical Slice

Entry: WP-05 passed. Migrate CLI/API download orchestration, transport,
integrity, resume, manifest, prune, repo-type resolution, redirect/token
isolation, and path safety behind usecase/adapters. Preserve existing HF-style
SDK behavior and signatures. Exit gate: all download/security/global-state/
dependency/ownership/packaging tests and complete baseline pass.

#### WP-07: Upload and LFS Vertical Slice

Entry: WP-06 passed. Migrate CLI/API file, folder, ordinary, resumable,
projection, worker, batch, timeout/progress, revision, ignore, LFS policy,
canonical pointer, and raw-blob verification ownership. Keep macOS metadata
filtering as injected CLI policy; do not change SDK defaults in Phase 1. Exit
gate: upload/LFS/global-state/dependency/security/ownership/packaging tests and
complete baseline pass.

#### WP-08: Lifecycle, Distribution, and Facade Closure

Entry: WP-07 passed. Place lifecycle/distribution technical implementations
behind infrastructure/interfaces. Shrink `atomgit.cli`, `atomgit.api`, and
`atomgit_hub` to compatibility conversion and seam registration only. Preserve
Click callback/module identities, lazy imports, console and both Python module
entry paths, old signatures/returns/exceptions, and patch behavior. Exit gate:
facade AST/debt, seam, CLI schema/dispatch, public import, source/editable/
wheel/sdist, installed-entry, completion, and complete baseline tests pass.

#### WP-09: Phase 1 Architecture Gate

Entry: WP-08 passed. Compare WP-00 inventory to the post-migration inventory.
Run full baseline, compileall, pip check, Black, isort, Ruff, credential and
artifact scans, package smoke, diff check, and independent review. Record exact
evidence and residual risk. Output: an accepted Phase 1 checkpoint and explicit
permission to begin Phase 2. If rejected, remain in Phase 1 and fix only
architecture regressions.

### Phase 2 Work Packages

#### WP-10: Parity Registry and Native SDK Contract

Entry: WP-09 accepted and Phase 1 source/tests are frozen except parity-owned
changes. Register every CLI general capability as `parity-required` or a
documented CLI-only exception. Define `AtomGitClient`, Request/Result types,
token priority, repo ID/type, visibility, revision, error, and final-state
contracts. Freeze old HF-style signatures. Exit gate: no CLI business capability
is unclassified, native SDK contracts have tests, and baseline still passes.

#### WP-11: Native SDK Authentication and Repository Parity

Entry: WP-10 passed. Add native SDK login/logout/whoami/create/list/visibility/
branch/delete methods with structured Results and stable `AtomGitError` mapping.
Preserve confirmation and final-state checks. Add canonical-request comparison
tests and keep old API/SDK functions thin. Exit gate: auth/repository parity,
compatibility, CLI contracts, security, locked signatures, and baseline pass.

#### WP-12: Native SDK Upload Parity

Entry: WP-11 passed. Expose file, ordinary folder, resumable, prefix, ignore,
workers, batches, timeout/progress restoration, revision, and LFS verification
through native SDK methods and shared usecases. Keep CLI metadata filtering a
CLI policy and old `upload_folder` compatibility. Exit gate: upload/LFS/result/
error/token/temp-lifetime/global-state/pointer/cross-entry tests and baseline.

#### WP-13: Native SDK Download Parity

Entry: WP-12 passed. Expose repository/file download, model/dataset resolution,
anonymous access, token, revision, force, checksum, persistent resume, and
manifest-scoped prune. Preserve `snapshot_download` and legacy `download_file`
semantics. Exit gate: download/security/checksum/resume/prune/cross-entry/
packaging tests and baseline pass.

#### WP-14: Parity Closure and Future-Debt Gate

Entry: WP-13 passed. Verify every parity-required item has one usecase, CLI
entry, native SDK entry, and cross-entry evidence; verify CLI-only exceptions;
add structure tests that fail on one-sided business paths, bypassed usecases,
missing registry entries, or facade growth. Update architecture/API/testing and
user documentation. Exit gate: Phase 2 acceptance, full baseline, package
smoke, independent review, and human acceptance pass.

### Checkpoint Format

At every package boundary record: current package/status, entry HEAD and
worktree state, changed paths, capabilities/invariants, focused commands and
exact results, complete baseline result, review status, last completed action,
next exact action, blockers, and residual risks. Never mark a later package
started before its predecessor exit gate is recorded.

### Package Evidence Ledger

The implementation turn must append one compact record per completed package;
do not replace earlier records with a summary:

```text
WP-XX: completed | HEAD=<commit> | changed=<paths>
Focused evidence: <commands and pass counts>
Baseline: <exact command/result>
Review: <not started/request changes/approved>
Residual risk: <none or explicit limitation>
Next: WP-YY <first action>
```

For a failed package, record the failure and keep the package `in_progress`:

```text
WP-XX: blocked by <contract/test>
Repair scope: <task-owned paths only>
Next: reproduce, fix, rerun the same gate
```

WP-00: completed | HEAD=bcd679d | changed=.ai/TASK.md
Focused evidence: `huggingface-hub==1.1.7`, `datasets==4.4.1`; 61 production
modules, 122 registered internal edges, 23 CLI schema nodes, 5 compatibility
facades, and the locked public HF-style signatures were inventoried.
Baseline: `python tests/run_cli_baseline.py` in `atomgit_cli`: 91 passed in
93.60s (offline).
Review: not started
Residual risk: local `yuto` remains divergent from `github/yuto`; remote history
contains the historical implementation and will not be force-pushed.
Next: WP-01 add executable target architecture contracts.

WP-01: completed | HEAD=bcd679d | changed=tests/structure_contract.py, tests/test_structure_guard.py, tests/test_architecture_parity.py, src/atomgit/{core,domain,usecases,interfaces,adapters,compatibility}
Focused evidence: architecture parity 14/14; structure guard 14/14; src-layout 6/6.
Baseline: `python tests/run_cli_baseline.py` 92 passed (offline).
Review: approved in final independent review.
Residual risk: remote behavior remains unverified by design.
Next: WP-02 through WP-08 completed in the same behavior-preserving migration.

WP-02: completed | HEAD=bcd679d | changed=src/atomgit/core, src/atomgit/adapters
Focused evidence: core dependency guard passed; locked HF/datasets signatures verified; compileall passed.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: locked dependency upgrades remain a future task.
Next: WP-03.

WP-03: completed | HEAD=bcd679d | changed=src/atomgit/adapters, src/atomgit/infrastructure, packaging contracts
Focused evidence: pip check, packaging metadata 13/13, source/editable/wheel/sdist contracts in baseline.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: no live installation or publication performed.
Next: WP-04.

WP-04: completed | HEAD=bcd679d | changed=authentication usecase/interface wiring
Focused evidence: authentication and credential-safety scripts in complete baseline; no token-like content scan hits.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: controlled remote auth evidence not required for this offline gate.
Next: WP-05.

WP-05: completed | HEAD=bcd679d | changed=repository usecase/interface wiring
Focused evidence: repository, revision, normalized-ID, and final-state scripts in complete baseline; parity branch verification 14/14.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: no remote repository mutation performed.
Next: WP-06.

WP-06: completed | HEAD=bcd679d | changed=download revision/filter context and transfer boundaries
Focused evidence: download contract 45/45, path security 15/15, recovery 12/12, repo-type resolution 7/7, checksum 23/23.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: remote checksum/resume evidence remains intentionally unrun.
Next: WP-07.

WP-07: completed | HEAD=bcd679d | changed=upload/LFS shared transfer boundaries
Focused evidence: upload/LFS, progress, batching, pointer, timeout, and global-state scripts in complete baseline.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: no live upload or LFS mutation performed.
Next: WP-08.

WP-08: completed | HEAD=bcd679d | changed=historical API/CLI/SDK facades and packaging ownership
Focused evidence: facade conversion, seam, import identity, CLI schema, entrypoint, and packaging contracts passed.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: task branch is local-only and remote yuto remains divergent.
Next: WP-09.

WP-09: completed | HEAD=bcd679d | changed=architecture/parity gate evidence
Focused evidence: compileall, pip check, git diff --check, Ruff, Black/isort, focused contracts, and complete baseline passed.
Baseline: 92 passed in `atomgit_cli` (offline).
Review: APPROVED; no open P0/P1/P2/P3 findings.
Residual risk: human acceptance and delivery history reconciliation remain.
Next: WP-10.

WP-10: completed | HEAD=bcd679d | changed=core/parity.py, interfaces/sdk, architecture parity registry
Focused evidence: registry fail-closed checks and native request/result contracts 14/14.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: no controlled remote evidence claimed.
Next: WP-11.

WP-11: completed | HEAD=bcd679d | changed=AtomGitClient authentication/repository methods
Focused evidence: explicit token precedence, repository final-state/branch checks, and compatibility baseline passed.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: no remote write authorization exercised.
Next: WP-12.

WP-12: completed | HEAD=bcd679d | changed=AtomGitClient upload methods and shared transfer port
Focused evidence: structured upload result, resumable/batch/LFS policy forwarding, upload/LFS baseline passed.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: live upload and LFS verification not run.
Next: WP-13.

WP-13: completed | HEAD=bcd679d | changed=AtomGitClient download methods and revision-safe transport
Focused evidence: revision/filter forwarding, explicit anonymous context, revision-scoped resume identity, and download suites passed.
Baseline: 92 passed (offline).
Review: approved.
Residual risk: remote checksum/resume/prune evidence not claimed.
Next: WP-14.

WP-14: completed | HEAD=bcd679d | changed=parity registry, docs, tests, packaging, and TASK evidence
Focused evidence: all registry/structure/packaging checks plus final 92-case baseline passed; no credential/artifact scan hits.
Baseline: `python tests/run_cli_baseline.py` 92 passed in 89.66s (offline).
Review: APPROVED.
Residual risk: no live remote write or checksum/LFS test was run; no force-push was performed.
Next: final closure revalidation and documentation reconciliation.

Final closure revalidation: completed | HEAD=398beb1 before documentation reconciliation | changed=.ai/ARCHITECTURE.md, .ai/TESTING.md, .ai/TASK.md
Focused evidence: final complete offline baseline 92 passed in 93.49s; compileall, pip check, and git diff --check passed.
Review: APPROVED; final diff review found no P0/P1/P2/P3 findings.
Residual risk: Black/isort/Ruff retain pre-existing repository-wide debt; no live remote tests were run.
Next: record accepted closure and await the next authorized Issue.

Corrective R2: completed | HEAD=8d9490d (working tree) | changed=.ai/TASK.md, docs/architecture.md, src/atomgit/{adapters/huggingface.py,cli,commands,core,domain/transfers.py,interfaces,usecases/transfers.py}, tests/{development_floor_contract.py,structure_contract.py,test_architecture_parity.py}
Focused evidence: architecture 18/18; upload file 16/16; repo type 17/17;
resumable upload 49/49; structure 14/14; LFS ownership 13/13; packaging
metadata 13/13; compileall, pip check, diff check, Black, and isort passed.
Baseline: `python tests/run_cli_baseline.py` 92 passed in 84.03s (offline).
Review: APPROVED for R2; no open P0/P1/P2/P3 findings.
Residual risk: adapters remain historical-API-backed by design for R2; R3
technical-owner migration and live remote behavior are not complete.
Next: R3 only after human acceptance and explicit authorization.

Corrective R4: completed | HEAD=2056237 (task commit; merged as 17ebd5a) | changed=.ai/TASK.md, .ai/ARCHITECTURE.md, docs/architecture.md, pyproject.toml, setup.py, src/atomgit/{adapters/download,adapters/__init__.py,adapters/atomgit_v5.py,adapters/huggingface.py,api/__init__.py,cli,commands,core,domain,download,interfaces,services,upload,usecases}, tests/{development_floor_contract.py,structure_contract.py,packaging_contract.py,test_download_domain_ownership.py,test_architecture_parity.py,test_api_facade_conversion.py,test_auth_repository_services_ownership.py,test_packaging_metadata.py,test_src_layout_migration.py}
Focused evidence: download ownership 18/18 then 21/21 after final compatibility regressions; download contract 45/45; checksum 23/23; resume 17/17; prune 49/49; path security 15/15; raw integrity 12/12; redirect security 9/9; manifest concurrency 9/9; Windows compatibility 12/12; structure 14/14; packaging metadata 13/13; wheel/sdist smoke 37/37.
Baseline: `python tests/run_cli_baseline.py` passed 92/92 in 81.33s in `atomgit_cli` (offline) after the final review repairs; compileall, pip check, git diff --check, Black, isort, and Ruff passed.
Review: APPROVED after resolving P1 compatibility findings for local missing-source exceptions, remote missing-file classification, CLI diagnostic presentation, and context-managed anonymous download credentials.
Residual risk: upload/LFS technical-owner migration remains R5; no controlled remote download/checksum/resume/prune evidence was run; no remote writes or credential mutations were performed.
Next: delivery completed; activate a new Issue explicitly before further development.

Corrective R5: completed | HEAD=51d7410 (task commit; merged as 097a5bb) | changed=.ai/TASK.md, .ai/ARCHITECTURE.md, docs/architecture.md, pyproject.toml, setup.py, src/atomgit/{adapters,lfs,lfs_pointer.py,sdk,upload,api,atomgit_hub.py}, tests/{structure_contract.py,packaging_contract.py,test_upload_domain_ownership.py,test_lfs_domain_ownership.py,test_sdk_domain_ownership.py,test_hf_api_contract.py,test_src_layout_migration.py,test_download_domain_ownership.py,test_auth_repository_services_ownership.py}
Focused evidence: upload ownership 17/17; LFS ownership 14/14; SDK ownership 19/19; repository ownership 24/24; download ownership 18/18; structure 14/14; HF contract 16/16; packaging 13/13; src-layout 6/6; import-order 5/5; completion 19/19; wheel/sdist smoke 37/37.
Baseline: `python tests/run_cli_baseline.py` passed 92/92 in 81.03s in `atomgit_cli` (offline); compileall, pip check, and git diff --check passed.
Review: APPROVED; no open P0/P1/P2/P3 findings. Human acceptance granted; task commit 51d7410, merge 097a5bb, and github/yuto equality verified.
Residual risk: controlled remote upload, resumable recovery, and LFS remote state/checksum evidence remain intentionally unrun; R6 is out of scope.
Next: activate a new Issue explicitly before further development.

## Detailed Package Specifications

The summaries above define ordering. This section defines the minimum work
that must be completed inside each package; it is the implementation checklist,
not a suggestion to broaden scope.

### WP-00 Detail: establish the starting truth

Investigate before editing:

- the real Git state and branch ancestry, including whether `yuto` is clean and
  whether the local task branch is based on the recorded base commit;
- the actual command tree and every public option from `cli/__init__.py` and
  `tests/cli_baseline_contract.py`;
- every public SDK import, signature, identity, and patch target from
  `atomgit_hub`, `atomgit.atomgit_hub`, `atomgit`, and the SDK ownership tests;
- current owners and dependency edges from `tests/structure_contract.py`,
  `tests/test_structure_guard.py`, and the source tree;
- real `huggingface-hub==1.1.7` and `datasets==4.4.1` signatures at every
  production call site;
- packaging discovery in `setup.py` and `pyproject.toml`, including source,
  editable, wheel, sdist, console, and both Python module entry paths;
- global timeout/progress/runtime/config/Git-helper state and all credential
  redaction boundaries.

The required output is a checked-in-Issue inventory, not a new source package:

```text
capability -> current owner -> current CLI path -> current SDK path
            -> protected tests -> target work package
```

The baseline must run before any new contract is interpreted. A failure is
triaged as pre-existing, environment-related, or caused by this planning state;
the implementation cannot silently inherit an unexplained failure.

### WP-01 Detail: make architecture rules executable

Produce four maps before moving implementation:

1. **Owner map**: every production module has exactly one target owner among
   the seven responsibility directories; historical facades are marked as
   compatibility surfaces, not business owners.
2. **Edge map**: every current import edge is classified as allowed, temporary
   migration edge, or forbidden; temporary edges have a removal package.
3. **Seam map**: every historical patchable symbol records its canonical owner,
   consumers, assignment/deletion propagation, and restoration behavior.
4. **Parity map**: every current CLI capability is classified
   `parity-required`, `cli-only`, or `sdk-only`, with no new SDK method claimed.

Add fail-closed tests for these maps. The tests must prove that a deliberately
introduced unowned module, forbidden edge, facade function, missing seam, or
unregistered parity capability fails. Do not use a generic compatibility layer
or empty package to make the map pass.

### WP-02 Detail: define contracts without moving behavior

Define only contracts needed by the first migration slice:

- request objects for authentication, repository, upload, and download inputs;
- result objects or internal result protocols for operations whose old callers
  currently receive `bool` or `str`;
- error categories and cause/redaction rules;
- ports for HF calls, V5 calls, filesystem/cache, configuration, and time/retry
  behavior where a usecase needs substitution;
- shared policy interfaces for repo ID, repo type, revision, token, and file
  selection.

Every contract must state who owns validation, who owns side effects, and who
converts the result for CLI, native SDK, and compatibility callers. Do not
create a speculative `core` abstraction merely because a future capability may
need it. Contract tests must bind the real locked dependency signatures where
the port represents an HF call.

### WP-03 Detail: isolate technical boundaries

Move or wrap technical implementation one boundary at a time:

1. configuration and token persistence, preserving lazy reads, permissions,
   atomic writes, and no token leakage;
2. runtime environment and HF global-state setup/restoration;
3. filesystem, temporary resources, cache, manifest, checksum, and locks;
4. Git credential helper and lifecycle filesystem transactions;
5. HF Hub construction and calls using the real installed signatures;
6. AtomGit V5 request, response-size, redirect, authentication-header, and
   error handling.

After each boundary, prove the old caller still reaches the same behavior. No
authentication/repository/upload/download flow is redesigned here. The exit
condition is one technical owner per boundary and no interface/domain direct
external import, not merely the existence of new directories.

### WP-04 Detail: authentication slice

Trace and migrate the complete authentication flow:

```text
login input -> token validation -> identity request -> config persistence
            -> optional Git-helper setup -> CLI/legacy result
logout      -> config clear -> helper restoration -> result
whoami      -> saved-login check -> identity request -> result
```

Domain owns token/identity rules and error categories. The usecase owns ordering
and rollback semantics. Outbound adapters own the identity endpoint, config,
and Git calls. Interfaces preserve Chinese output, prompts, exits, and old API
boolean behavior. Tests must cover no-credential paths, all existing HTTP
categories, bounded malformed responses, redaction, config permissions, and
Git-helper preservation. Do not add native SDK methods until Phase 2 WP-11.

### WP-05 Detail: repository slice

Migrate each operation as a separately testable usecase, not one large
repository service:

- create: validate type/ID/visibility, create through the compatible route,
  converge visibility, and verify final state;
- list: authenticate, fetch bounded collection, validate response shape, and
  expose the existing CLI/API form;
- visibility: issue the update, recover only from allowed uncertain failures,
  and GET-verify the requested state;
- branch: resolve the source to an immutable commit, create, and verify target
  name plus commit;
- delete: require exact confirmation, GET before and after DELETE, and only
  report success after verified absence.

The shared result may be richer internally, but Phase 1 adapters must preserve
existing CLI output and API `bool`/error semantics. Add no native SDK public
surface in this package; that belongs to WP-11 after Phase 1.

### WP-06 Detail: download slice

Separate the download usecase into repository enumeration, destination safety,
transport, integrity, resume, manifest, and prune responsibilities. Preserve:

- public anonymous access and private token selection;
- model/dataset detection and explicit type forwarding;
- existing-file skip/force behavior;
- checksum handling for existing and new files;
- persistent resume identity and cleanup;
- manifest-scoped prune safety;
- redirect credential isolation and path traversal rejection;
- old SDK HF parameter warnings/forwarding and return values.

The usecase decides when a repository download is complete; filesystem and HTTP
adapters only perform bounded operations. Tests must verify each failure before
moving the next concern, so a checksum or prune regression cannot hide behind a
successful transport mock.

### WP-07 Detail: upload and LFS slice

Migrate upload by path/mode, keeping the following sequence explicit:

```text
validate path/symlinks -> normalize request -> select files by policy
  -> choose ordinary/resumable mode -> prepare projection if needed
  -> transfer -> commit -> verify pointer/raw blob -> return result
```

The slice must preserve direct single-file behavior, folder lifetime, path
prefix projection, ignore parsing, resumable batching/workers, timeout and
progress restoration, revision forwarding/rejection, retry/fatal categories,
LFS attribute transaction, canonical pointer bytes, and ambiguous-commit
reconciliation. CLI macOS metadata filtering is passed as a CLI policy; SDK
defaults are not changed in Phase 1. A fake that accepts invalid HF keywords is
not sufficient: each call binds to the real 1.1.7 signature.

### WP-08 Detail: lifecycle and facade closure

Keep lifecycle and distribution concerns separate from repository transfer
usecases. Verify completion install/uninstall transactions, update provenance,
package-absent fallback, exact managed paths, and user-state preservation.

Then shrink historical surfaces in dependency order:

1. move Click schema/context assembly behind `interfaces/cli` while keeping
   `atomgit.cli` as the observed module object;
2. move `HuggingFaceAPI` method resolution behind `compatibility/api` while
   preserving class and singleton identity;
3. move top-level and package SDK exports behind `compatibility/sdk` while
   preserving function identity/signatures and patch propagation;
4. verify `python -m atomgit`, `python -m atomgit.cli`, console script,
   completion-only imports, source provenance, and all artifact surfaces.

No facade may retain a second implementation “temporarily” without a named
owner and removal checkpoint. If a seam cannot be preserved, stop this package
and redesign the forwarding mechanism before changing behavior.

### WP-09 Detail: architecture release gate

Compare the WP-00 inventory field by field: command schema, SDK signatures,
object identities, call keywords, output/exit behavior, global-state snapshots,
package file set, and import side effects. Run the full offline matrix only
after focused failures are resolved. Independent review must inspect the whole
Phase 1 diff and test evidence as a structural refactor, not only new files.

The gate produces a decision: `Phase 1 accepted` or `Phase 1 rejected`. Only
`accepted` unlocks WP-10. A passing subset or a favorable code review cannot
unlock Phase 2 when the complete baseline is missing.

### WP-10 Detail: define the native SDK parity product

Create the parity registry from the actual CLI capability inventory, not from a
wish list. For every item define:

- native SDK method name and signature;
- whether it uses stored, explicit, or anonymous credentials;
- request normalization and repo type/revision rules;
- structured Result fields and guaranteed versus optional fields;
- `AtomGitError` mapping and preserved cause policy;
- CLI presentation differences;
- compatibility function(s) that must remain unchanged;
- focused, cross-entry, dependency, package, and (if authorized) remote tests.

The native API must not be designed by adding arbitrary CLI flags to old
HF-style functions. Old signatures are frozen; new AtomGit semantics belong to
`AtomGitClient` or explicitly named native functions.

### WP-11 Detail: authentication and repository parity

Implement native SDK adapters only after the shared usecases already pass.
Return structured identity/repository/visibility/branch/deletion results. Keep
delete confirmation and final absence verification in the SDK API, not in a
hidden interactive prompt. Compare CLI and SDK canonical requests using the
same fake transport, then separately test CLI output/exit and SDK return/error.

Remote validation, when used, is restricted to the authorized
`weixin_52273949/test_datasets` repository and must record pre-state, result,
checksum or final state, and cleanup. No repository deletion is authorized.

### WP-12 Detail: upload parity

Expose native SDK upload methods in capability increments: file, ordinary
folder, resumable folder, path prefix, ignore, workers/batches, timeout/progress,
revision, and LFS verification. For each increment, compare the SDK request
with the CLI request at the shared boundary before adding the next option.

Preserve old `upload_folder` result/signature semantics through compatibility.
Do not silently add CLI macOS metadata exclusions to SDK defaults. Use offline
strict fakes first, then the authorized remote repository only for separately
identified upload/recovery/LFS evidence.

### WP-13 Detail: download parity

Expose native repository/file download in increments: repo type, token/anonymous
selection, revision, force, checksum, resume, and prune. Define which fields in
`DownloadResult` are guaranteed and ensure partial failures never claim complete
success. Keep `snapshot_download` HF warnings/parameters and legacy
`download_file` return behavior through compatibility.

Cross-entry tests must compare canonical normalized requests, destination
policy, transport headers, checksum decisions, manifest mutations, and final
result status. Remote tests must use checksums or explicit remote state, not CLI
success text.

### WP-14 Detail: close the future-debt loop

Prove every parity registry row has one shared usecase, one CLI interface, one
native SDK interface, compatibility coverage where applicable, and tests at all
required layers. Add a deliberately incomplete one-sided fixture to prove the
parity gate fails closed, then remove only the fixture and keep the guard.

Update the authoritative architecture, testing, API, and user documentation
with current behavior and intentional CLI-only exceptions. Run the final full
baseline and independent review. The package is complete only after human
acceptance; a passing implementation without acceptance remains active.

## Phase 1: Behavior-Preserving Architecture

### Steps

1. Freeze CLI schema/dispatch/output/exits, SDK signatures/returns/errors,
   public imports/identities, patch seams, locked dependency signatures,
   global-state restoration, package surfaces, and the complete baseline.
2. Add executable owner, edge, facade-debt, packaging, import, behavior, and
   compatibility-seam contracts before moving implementation.
3. Establish core contracts, domain owners, usecase boundaries, interfaces,
   outbound adapters, compatibility registry, and infrastructure ownership.
4. Migrate complete vertical slices: infrastructure/ports, authentication,
   repositories, downloads, uploads, LFS, then lifecycle/distribution.
5. Keep historical paths stable; shrink their facades only after new owners and
   usecases are stable and tested. Remove duplicate implementations last.

### Non-goals

No CLI or SDK behavior change, new SDK capability, dependency upgrade, live
AtomGit write, credential mutation, publication, broad formatting, or unrelated
roadmap work.

### Invariants

- `ARCH-001`: every production module has one owner and registered edges; no new unowned module, cycle, forbidden edge, or facade business definition.
- `ARCH-002`: existing CLI/SDK/API behavior and locked-library calls remain exact.
- `ARCH-003`: historical module/object/callback/function/signature/entry/patch identities remain stable.
- `ARCH-004`: interfaces translate, usecases orchestrate, domains define rules, outbound adapters call external systems.
- `ARCH-005`: compatibility contains translation and seams only.
- `ARCH-006`: source/editable/wheel/sdist preserve historical entries and exclude stale duplicate implementations.

### Evidence

Run focused owner/edge/facade/import/patch/lazy tests for every slice and the
full `python tests/run_cli_baseline.py` after each slice and at the end. Also
run compileall, pip check, Black, isort, Ruff, credential/artifact scans, and
git diff check. No live evidence is required; live writes remain unauthorized.

## Phase 2: CLI/SDK Capability Alignment

### Steps

1. Freeze Phase 1 evidence.
2. Create a fail-closed registry classifying each capability as `parity-required`, `cli-only`, or `sdk-only`.
3. Define shared Request, Result, error, token, repo ID, repo type, visibility, revision, checksum, resume, prune, LFS, and final-state contracts.
4. Implement one shared usecase and outbound adapter per general capability.
5. Add native `interfaces/sdk` `AtomGitClient` methods and structured Results.
6. Keep `snapshot_download`, `upload_folder`, `download_file`, `create_repository`, `hub_download_url`, and `load_dataset` through compatibility with existing signatures and primary semantics.
7. Keep CLI output/prompts/progress/exits in the CLI interface and SDK Results/AtomGitError mapping in the SDK interface.
8. Add cross-entry tests comparing canonical requests and remote result invariants.

### SDK parity inventory

- Authentication: login validation, logout state, whoami.
- Repositories: create model/dataset, list, visibility, branch creation, safe delete with post-delete absence verification.
- Upload: file, ordinary folder, resumable, path prefix, ignore, workers, batches, timeout/progress restoration, revision, canonical LFS pointer/commit verification.
- Download: repository, file, model/dataset resolution, anonymous public access, token, revision, force, checksum, persistent resume, manifest-scoped prune.
- Shared policies: repo ID, repo type, visibility, revision, token priority, redaction, errors, final-state verification.

### Invariants

- `PARITY-001`: each parity-required capability has one shared usecase and both CLI/native SDK interfaces before completion.
- `PARITY-002`: CLI and SDK use one repo ID, repo type, revision, visibility, and token contract.
- `PARITY-003`: CLI and SDK agree on remote success/failure and final verification; only presentation, wrapping, and exit behavior differ.
- `PARITY-004`: SDK remote failures use stable redacted `AtomGitError` subclasses; local parameter failures remain standard exceptions.
- `PARITY-005`: old HF-style functions preserve signatures, defaults, paths, primary behavior, and compatibility returns.
- `PARITY-006`: no one-sided general capability can merge without registry and cross-entry evidence.
- `PARITY-007`: CLI macOS filtering remains explicit CLI policy and is not silently imposed on SDK callers.

## Shared Rules

Token priority:

```text
explicit non-empty token > explicit token=False > saved config token > anonymous read > auth error for writes
```

Explicit credentials never silently fall back. Validate repo ID before credentials
or network; normalize once; preserve logical model/dataset semantics; default
revision is `main`; non-main upload requires an explicitly created and verified
branch. Missing revisions map to `AtomGitRevisionNotFoundError`.

Shared usecases return structured results or classified internal errors. CLI
converts them to established output/exits. Native SDK returns structured Results
and stable `AtomGitError` subclasses. Compatibility converts them to historical
contracts. Tokens, signed URLs, response bodies, and secret-bearing causes never
enter results, logs, fixtures, or messages.

## Parity Delivery Gate

Every future feature records:

```text
capability ID, classification, shared usecase, CLI entry, SDK entry,
parameter mapping, shared remote result, CLI presentation, SDK result/error,
focused tests, documentation
```

Every parity-required capability must have core/domain/usecase, outbound adapter,
CLI interface, SDK interface, compatibility coverage, shared result tests, CLI
output/exit tests, SDK result/error tests, registry/documentation updates, and a
passing complete baseline. A one-sided implementation may remain on a branch
while work continues, but cannot be complete, merged, released, or used as the
basis for further feature expansion. Structure tests must fail closed when a
new business path bypasses the shared owner or lacks parity registration.

## Acceptance Criteria

### Phase 1

1. The seven responsibility directories and dependency direction are implemented without moving user behavior into domain or adding another business layer.
2. Existing CLI, SDK, API, packaging, entry, dependency, global-state, credential-safety, and remote-call behavior remains exact.
3. All migrated capabilities have one owner; historical facades contain no new business implementation and preserve identities/seams.
4. Architecture, ownership, edge, facade, import, packaging, and behavior contracts fail closed.
5. Focused tests, complete baseline, compileall, pip check, lint, security, artifact, and installed smoke pass.

### Phase 2

1. Native SDK interfaces cover every CLI general remote/business capability in the parity inventory.
2. CLI and SDK share usecases, domain rules, outbound adapters, remote result invariants, and stable errors.
3. Existing HF-style SDK functions remain compatible through thin facades.
4. CLI-only capabilities and macOS policy are explicit exceptions, not accidental SDK gaps.
5. Every parity capability has both-entry tests, cross-entry evidence, documentation, and complete baseline evidence.
6. Future one-sided business additions fail parity and structure gates.
7. Independent review has no open P0/P1/P2/P3 finding before human acceptance.

## Required Verification

All commands run in `atomgit_cli`:

```bash
python tests/run_cli_baseline.py
python -m compileall -q .
python -m pip check
git diff --check
```

Also run applicable focused architecture/ownership/import/compatibility,
CLI schema/dispatch/output, SDK signature/result/error/token, locked HF/datasets,
packaging, source/editable/wheel/sdist, security, portability, Black, isort,
Ruff, credential/artifact, and installed-entry tests. Independent review uses
`.ai/REVIEW.md`. Controlled remote tests require separate explicit authorization.

## Authorization And Delivery

- The maintainer explicitly authorized R5 implementation and verification by requesting continued development, then authorized committing and pushing the completed work in the current request. Source, tests, contracts, packaging, and documentation were in scope.
- Delivery mode is local task branch -> focused/full offline verification -> independent review -> human acceptance -> cohesive commit -> local no-ff merge into yuto -> push only yuto -> remote equality verification.
- Controlled remote test authorization: the maintainer explicitly authorizes
  authenticated upload and download, test-branch creation, repository
  visibility changes, deletion of test files or test branches, Git push, and
  necessary test-data cleanup only in
  `weixin_52273949/test_datasets` (`git@atomgit.com:weixin_52273949/test_datasets.git`).
  Record pre-test state, keep fixtures clearly test-owned, verify final remote
  state/checksums, and restore visibility or other mutable state after the
  applicable scenario. Never display credentials.
- Repository deletion, use of any other remote repository, remote repository
  creation, remote Issue/PR operations, task-branch push to the development
  repository, credential mutation, publication, tags/releases, and upstream
  changes remain unauthorized.
- Human acceptance was granted by the maintainer's explicit request to commit and push the completed R5 work. Standing project rules allowed one cohesive conventional commit, local no-ff merge into yuto, push only yuto, fetch, and remote equality verification; the task branch was not pushed.
- Delivery evidence: task commit `51d7410`, merge commit `097a5bb`, and remote `github/yuto` verified at `097a5bb1f507adac346bfad60bcc5fb198b80e46` with `git fetch`, `git rev-parse`, and `git ls-remote`.

## Independent Review

- Verdict: `APPROVED`
- Findings: `R4 review initially REQUEST CHANGES for local FileNotFoundError compatibility, remote missing-file classification, lost CLI diagnostics, and context-managed credential handling; all were repaired with focused regressions before the final APPROVED review`
- Review evidence: `final diff reviewed against the active Issue, locked huggingface-hub==1.1.7 and datasets==4.4.1 signatures, structure/parity contracts, download ownership and security suites, packaging/source/wheel/sdist contracts, compileall, pip check, Ruff, Black/isort, diff check, and the complete 92-case offline baseline`
- Residual review risk: `controlled remote upload/download/checksum/LFS evidence was not run; no credential mutation or live repository test was performed`

## Definition Of Done

- [x] Phase 1 and Phase 2 remain separate and each has observable acceptance evidence.
- [x] Capability IDs, protected invariants, and new invariants agree with executable registries.
- [x] No behavior change is hidden in Phase 1.
- [x] Every general remote CLI capability has a native SDK counterpart or an explicit CLI-only classification.
- [x] Old imports, signatures, identities, patch seams, entry paths, and package artifacts remain compatible.
- [x] Focused, complete baseline, dependency, packaging, security, portability, compile, and diff checks pass.
- [x] Black/isort/Ruff were audited; their pre-existing repository-wide debt is recorded as residual risk and is outside this closure scope.
- [x] Independent review is APPROVED with no open blocking finding.
- [x] Human acceptance of R5 was granted by the maintainer; commit, merge, push, and remote equality verification are complete.
- [x] Remaining risks, unrun tests, and controlled-remote limitations are explicit.
