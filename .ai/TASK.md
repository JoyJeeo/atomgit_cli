# Current Issue Contract

Status: active (D12 upload session heartbeat timestamp)

## Successor Development Issue

- Updated: `2026-09-12`
- ID: `LOCAL-UPLOAD-RELIABILITY-20260907`
- Title: `上传可靠性与可观测性修复`
- Type: `bug`, `cli`, `sdk`, `compatibility`, `testing`, `documentation`
- Priority: `P1`（正常长时间上传可能被错误总时限终止）
- Source: `DISC-UPLOAD-RELIABILITY-20260904`，当前收录已确认的 `D01 / UPLOAD-01`、
  `D03 / UPLOAD-03`、`D04 / UPLOAD-04`、`D05 / LFS-01`、`D06 / LFS-02`、
  `D07 / LFS-03`、`D08 / LFS-04`、`D09 / MON-01`、`D10 / MON-02`、
  `D11 / MON-03` 和 `D12 / MON-04`；D02 已由 D01 解决并移除。
- Current phase: D01、D03、D04、D05、D06 和 D07 均已完成验收、提交、本地 no-ff
  合并和限定交付；D08 也已完成实现、验收、最终复验、任务提交、本地 no-ff 合并和
  `github/yuto` 限定推送。D09、D10 已完成阶段 1–5 的红灯、实现、专项、文档、
  开发底线、最终完整离线门禁和独立审查；维护者已接受结果，任务提交 `f1b4c78`
  已通过 no-ff 合并提交 `85167bd` 合入并限定推送至 `github/yuto`。D11 完整方案已
  接受并写入本 Issue。D11 已完成红灯、实现、专项、文档、开发底线、最终完整离线
  门禁和独立审查；维护者接受结果后，任务提交 `6a9d6f7` 已通过 no-ff 合并提交
  `0e0f7bd` 合入并限定推送至 `github/yuto`，任务分支未推送。D12 的快照发布时刷新
  会话 `updated_at` 方案已获维护者接受并写入本 Issue。维护者随后明确要求“开始开发”，
  D12 已在本地任务分支激活；heartbeat 时间与默认选择红灯已按预期复现，最小实现、
  回归、文档、开发底线、完整离线门禁和独立审查已完成；维护者已接受复验结果并授权
  限定 Git 交付，当前进入提交、no-ff 合入 `yuto` 和仅推送 `github/yuto` 阶段。
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
  维护者随后于 `2026-09-07` 明确表示“接受 按你的建议开始执行”，接受 D04 方案，
  授权写入并激活 D04、创建本地任务分支、修改相关源码、既有测试、用户文档和开发
  底线台账，并执行离线验证；未授权提交、合并、推送或真实 AtomGit 操作。
  维护者随后明确要求“自己去验收一下 没问题就提交推送”，授权 AI 完成 D04 最终
  验收；全部门禁无误后提交 D04、本地 no-ff 合入 `yuto`，并仅推送 `github/yuto`。
  任务分支不推送；真实 AtomGit 操作、PR、标签、发布和 D05–D18 实施仍未授权。
  维护者随后于 `2026-09-08` 明确要求“将开发方案落入本地开发issue中，不直接开始
  开发”，接受 D05 的三次只读确认方案并授权更新本地开发 Issue 与讨论交接。本次
  不授权激活 D05、创建分支、修改源码/测试/用户文档、运行实现验证、提交、合并、
  推送或任何真实 AtomGit 操作。
  维护者随后在新对话明确要求“现在开始开发”，据此授权激活 D05、创建本地任务分支、
  修改 D05 范围内的源码、既有测试、用户文档和开发底线台账，并执行离线验证；不授权
  提交、合并、推送、PR、发布或任何真实 AtomGit 操作，也不授权实施 D06–D18。
  维护者随后明确要求“自己验证一下 没有问题就提交并推送”；最终完整复验无误后，
  据此接受 D05 并授权提交任务分支、本地 no-ff 合入 `yuto`、仅推送 `github/yuto`
  及记录交付结果。任务分支不推送，其他远程操作和 D06–D18 实施仍未授权。
  维护者于 `2026-09-09` 确认 D06 采用“远端提交已创建但本地未确认”的
  独立失败状态，并明确要求将最终方案写入本地开发 Issue、暂不开发。
  本次只授权更新 `.ai/TASK.md` 和 `.ai/ISSUE_DISCUSSION.md`；不授权激活 D06、
  创建分支、修改源码/测试/用户文档、运行实施验证、提交、合并、推送或执行任何
  真实 AtomGit 操作，也不授权实施 D07–D18。
  维护者随后在新对话明确要求“现在开始开发”，据此授权激活 D06、创建本地任务
  分支、修改 D06 范围内的源码、既有测试、用户文档和开发底线台账，并执行离线
  验证；不授权提交、合并、推送、PR、发布、真实 AtomGit 操作或实施 D07–D18。
  维护者随后明确要求“自己测试一下，没有问题的话，就提交推送”；最终复验全部
  通过后，据此接受 D06 并授权提交本地任务分支、no-ff 合入 `yuto`、仅推送
  `github/yuto` 及记录交付结果。任务分支不推送，其他远程操作及 D07–D18 实施
  仍未授权。
  维护者于 `2026-09-10` 确认 D07 保持 D05 的三次只读确认与 `2/4` 秒退避不变，
  只对三次耗尽后的最后一次 pointer 确认失败原因进行安全判断、分类和报错汇报，
  并明确要求将开发方案登记到本地开发 Issue。本次只授权更新 `.ai/TASK.md` 和
  `.ai/ISSUE_DISCUSSION.md`；不授权激活 D07、创建分支、修改源码/测试/用户文档、
  运行实现验证、提交、合并、推送、真实 AtomGit 操作或实施 D08–D18。
  维护者随后在新对话明确要求“现在开始开发”，据此单独授权激活 D07、创建本地
  任务分支、修改 D07 范围内的源码、既有测试、用户文档和开发底线台账，并执行
  离线验证；不授权提交、合并、推送、PR、发布、真实 AtomGit 操作或实施 D08–D18。
  维护者随后明确要求“你自己验收一下，没有问题就提交并推送”；最终复验全部通过后，
  据此接受 D07 并授权提交本地任务分支、no-ff 合入 `yuto`、仅推送 `github/yuto`
  及记录交付结果。任务分支不推送，其他远程操作及 D08–D18 实施仍未授权。
  维护者于 `2026-09-12` 接受 D08 的“私有待对账提交凭据、重跑前只读核对、
  `parent_commit` 并发保护、冲突失败关闭”方案，并明确要求将开发方案写入本地开发
  Issue。本次只授权更新 `.ai/TASK.md` 和 `.ai/ISSUE_DISCUSSION.md`；不授权激活
  D08、创建分支、修改源码/测试/用户文档、运行实施验证、提交、合并、推送、真实
  AtomGit 操作或实施 D09–D18。
  维护者随后在新对话明确要求“开始开发”，据此单独授权激活 D08、创建本地
  任务分支、修改 D08 范围内的源码、既有测试、用户文档和开发底线台账，并执行离线
  验证；不授权提交、合并、推送、PR、发布、真实 AtomGit 操作或实施 D09–D18。
  维护者随后明确要求“自己再验证一下功能是否正常 没有问题就提交并推送”；据此接受
  D08 并授权最终复验通过后提交任务分支、本地 no-ff 合入 `yuto`、仅推送
  `github/yuto` 及记录交付结果。任务分支不推送，真实 AtomGit、PR、标签、发布和
  D09–D18 实施仍未授权。
  维护者随后于 `2026-09-12` 接受 D09 的“协调器结构化状态、UploadSession 最新状态
  覆盖、有界关键事件、5 秒显示采样与 30 秒正式窗口分离”方案，并明确要求将完整方案
  写入本地开发 Issue。本次只授权更新 `.ai/TASK.md` 和 `.ai/ISSUE_DISCUSSION.md`；
  不授权激活 D09、创建分支、修改源码/测试/用户文档、运行实施验证、提交、合并、
  推送、真实 AtomGit 操作或实施 D10–D18。
  维护者随后明确接受 D10 的“父进程单一状态所有者、独立 256 条有界观测队列、
  v1 脱敏 JSON envelope、与可靠结果队列彻底分离、中间显示样本允许降级丢失”方案，
  并要求将完整开发方案写入本地开发 Issue。本次只授权更新 `.ai/TASK.md` 和
  `.ai/ISSUE_DISCUSSION.md`；不授权激活 D09/D10、创建分支、修改源码/测试/用户文档、
  运行实施验证、提交、合并、推送、真实 AtomGit 操作或实施 D11–D18。
  维护者随后通过批注明确要求“开始联合开发 D09/D10”，授权激活本地 Issue、创建
  基于 `yuto@75094a7` 的本地任务分支、修改 D09/D10 范围内源码、既有测试、最小
  文档和开发底线，并运行离线验证；不授权提交、合并、推送、真实 AtomGit 操作或
  实施 D11–D18。
  维护者随后明确要求“自己验收一下 没问题就提交推送”；据此授权最终交付复验通过后
  接受 D09/D10，提交本地任务分支、no-ff 合入 `yuto`、仅推送 `github/yuto` 并记录
  交付结果。任务分支不推送，真实 AtomGit、PR、标签、发布和 D11–D18 仍未授权。
  维护者随后接受 D11 的父进程批次生命周期直连方案，并明确要求“将完整方案落入
  本地开发issue”。本次只授权更新 `.ai/TASK.md` 和 `.ai/ISSUE_DISCUSSION.md`，
  将 D11 登记为未激活的后继开发范围；不授权激活 D11、创建分支、修改源码/测试/
  用户文档、运行实现验证、提交、合并、推送、真实 AtomGit 操作或实施 D12–D18。
  维护者随后于 `2026-09-12` 明确要求“开始开发”，据此单独授权激活 D11、创建本地
  任务分支、修改 D11 范围内的源码、既有测试、用户文档和开发底线台账，并执行离线
  验证；不授权提交、合并、推送、PR、发布、真实 AtomGit 操作或实施 D12–D18。
  维护者随后明确要求“自己验收一下 没有问题就提交并推送”；据此接受 D11，并授权
  最终复验通过后提交本地任务分支、no-ff 合入 `yuto`、仅推送 `github/yuto` 及记录
  交付结果。任务分支不推送，真实 AtomGit、PR、标签、发布和 D12–D18 仍未授权。
  维护者随后于 `2026-09-12` 接受 D12 的最小修复：在每次实际持久化快照时，只刷新
  即将写入副本的会话 `updated_at`，Flow/事件时间和上传状态不变；并明确要求“将开发
  方案落入本地开发issue中”。本次只授权更新 `.ai/TASK.md` 和
  `.ai/ISSUE_DISCUSSION.md`，将 D12 登记为未激活的后继开发范围；不授权创建分支、
  修改源码/测试/用户文档、运行实现验证、提交、合并、推送、真实 AtomGit 操作或实施
  D13–D18。
  维护者随后明确要求“开始开发”，据此单独授权激活 D12、创建本地任务分支、修改
  D12 范围内的源码、既有测试、用户文档和开发底线台账，并执行离线验证；不授权提交、
  合并、推送、PR、发布、真实 AtomGit 操作或实施 D13–D18。
  维护者随后明确要求“自己验收一下 没有问题就推送”；据此在最终复验通过后接受 D12，
  授权提交本地任务分支、no-ff 合入 `yuto`、仅推送 `github/yuto` 并记录交付结果。
  任务分支不推送，真实 AtomGit、PR、标签、发布和 D13–D18 实施仍未授权。
- Delivery mode: 维护者明确要求“自己验证一下，没有问题就提交推送”。复验通过后，
  授权 D01 提交、本地合入 yuto、仅推送 github/yuto 和必要交付记录；不推任务分支。
  原有五份开发规范变更保持未提交。远程上传、PR、标签、发布仍未授权。
- D03 delivery mode: 复验通过后提交任务分支、本地 no-ff 合入 `yuto`、仅推送
  `github/yuto` 并核验远端一致；任务分支保持本地，不执行其他远程操作。
- D04 delivery mode: 本地验收通过后提交任务分支、本地 no-ff 合入 `yuto`、仅推送
  `github/yuto` 并核验远端一致；任务分支保持本地，不执行其他远程操作。
- D05 delivery mode: 最终复验通过后提交本地任务分支、no-ff 合入 `yuto`，并且只推送
  `github/yuto`；不推送任务分支，不执行真实 AtomGit 操作、PR、标签或发布。
- D06 delivery mode: 最终复验通过后提交本地任务分支、no-ff 合入 `yuto`，并且只
  推送 `github/yuto`；不推送任务分支，不执行真实 AtomGit 操作、PR、标签或发布。
- D07 delivery mode: 最终复验通过后提交本地任务分支、no-ff 合入 `yuto`，并且只
  推送 `github/yuto`；不推送任务分支，不执行真实 AtomGit 操作、PR、标签或发布。
- D08 delivery mode: 最终复验通过后提交本地任务分支、no-ff 合入 `yuto`，并且只推送
  `github/yuto`；不推送任务分支，不执行真实 AtomGit、PR、标签、发布或 D09–D18。
- D09/D10 delivery mode: 最终交付复验通过后提交本地任务分支、no-ff 合入 `yuto`，
  并且只推送 `github/yuto`；不推送任务分支，不执行真实 AtomGit、PR、标签、发布或
  D11–D18。
- D11 delivery mode: 最终复验通过后提交本地任务分支、no-ff 合入 `yuto`，并且只
  推送 `github/yuto`；不推送任务分支，不执行真实 AtomGit、PR、标签、发布或
  D12–D18。
- D12 delivery mode: 最终复验通过后提交本地任务分支、no-ff 合入 `yuto`，并且只推送
  `github/yuto`；不推送任务分支，不执行真实 AtomGit、PR、标签、发布或 D13–D18。
- Next exact action: 将 D12 任务文件提交到本地任务分支，no-ff 合入 `yuto`，写入交付
  记录后仅推送并核验 `github/yuto`；D13 讨论继续暂停。

### Repository Reconciliation

当前任务分支 `codex/d12-upload-session-heartbeat` 基于 `yuto@611a468` 创建；创建时
`github/yuto` 也是 `611a468`。D09/D10 任务提交 `f1b4c78` 已通过 no-ff 合并提交
`85167bd` 合入，
并仅推送 `github/yuto` 后核验远端一致。任务分支保留在本地且未推送。当前 worktree
保留五份既有 `.ai` 规范修改，未纳入 D09/D10 或 D11 提交；本次仅叠加获授权的 D12
`.ai/TASK.md` 与 `.ai/ISSUE_DISCUSSION.md` 方案记录。Git 还包含 R9、D01、D03、
D04、D05、D06 和 D07 的历史或已交付提交；旧记录不恢复为活跃任务。历史矛盾的
完整整理仍属于 D18，本次没有将 D18 标记为已解决。

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
- D03 实现提交 `c87c62e54f36a85f497780dc454bf5539cff6643` 已通过 no-ff 合并提交
  `6b5a9687cf461bf99a4e6d30445b5e17a4894c25` 合入 `yuto`；仅推送 `github/yuto`，
  远端与本地合并提交一致，远端不存在 D03 任务分支。

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
- [x] 提交、本地合并、推送及远端一致性核验完成。

当前 D03 已完成限定交付；D04 已获维护者确认并激活本地实施。

### D04 Objective And Evidence

resumable 上传失败时，在保留现有累计确认汇总的同时，准确显示当前失败批次已经
持久化的哈希、LFS 预上传和本地待确认文件/字节状态，使用户能判断断点元数据的实际
价值而不误判远端提交结果。

当前 `adapters/upload/service.py` 的失败路径只调用
`_resumable_committed_file_count`，随后输出新增提交、续传跳过和确认完成文件数。
锁定的 `huggingface-hub==1.1.7` 已在投影元数据中持久化 `size`、`sha256`、
`upload_mode`、`is_uploaded` 和 `is_committed`；HF 自带运行报告也使用这些字段，
但子进程失败后的 AtomGit 汇总没有读取并展示它们。因此大量 LFS 数据完成预上传后，
最终仍可能只显示“确认完成 0”。

### D04 Accepted Behavior

- 只在 resumable 当前批次失败时，读取该批次已有断点元数据并输出一条凭证安全的
  “断点状态”。此前成功批次继续由现有累计确认汇总表示。
- 已哈希以 `sha256` 非空为准；LFS 已预上传以 `upload_mode == "lfs"` 且
  `is_uploaded` 为准；本地待确认以 `is_committed` 为假为准。三类均显示文件数和
  以项目现有格式化函数表示的字节数。
- “LFS 已预上传”不能表述为已提交或永久可复用；“本地待确认”不能推断远端一定
  没有提交。现有失败类型、返回值、建议和重新执行指引保持不变。
- 元数据读取属于观察行为。单个状态无法读取时记录为未知，不按零处理；统计失败
  不能覆盖原始上传异常、导致成功或改变断点内容。
- 输出不包含源路径、远端路径、OID、token、URL、header、响应正文或异常明细。

### D04 Implementation Scope

1. 在 resumable 投影所有者中增加一个只读批次统计函数，按锁定 HF 1.1.7 元数据
   格式读取快照并复用既有文件大小格式化能力；保留现有已提交计数接口和兼容补丁面。
2. 在共享上传服务的 resumable 失败分支中读取并打印当前批次断点状态，顺序位于
   失败累计行与现有重新执行指引之间。
3. 扩展现有批次测试覆盖预上传后失败、部分提交、普通/LFS 混合、元数据读取异常，
   并证明成功路径、普通上传和原有累计汇总不变。
4. 更新最小权威用户文档与既有 `UPLOAD-RESUMABLE` 能力台账，不新增测试脚本。

### D04 Affected Capability IDs

`CLI-SURFACE`、`UPLOAD-FOLDER`、`UPLOAD-RESUMABLE`、`UPLOAD-LFS`、
`ERROR-REDACTION`、`DEPENDENCY-CONTRACT`、`ARCHITECTURE` 和 `FLOOR-REGISTRY`。

### D04 Protected Existing Invariants

- CLI、原生 SDK、历史 API 的参数、返回值、异常包装和上传路径保持兼容。
- 成功批次、失败累计、续传跳过、确认完成和重新执行指引语义不变。
- 断点元数据由 HF 上传流程拥有；观察代码不写入、修复或删除它，也不访问远端。
- 元数据观察失败不改变原始失败分类、退出状态、资源清理或全局状态恢复。
- 路径、OID、token、签名 URL、header、响应正文和异常明细不会进入新增输出。
- D01 的无限上传总时长、D03 的 pointer 请求超时、HF 60 秒写入等待、有限重试、
  取消清理、锁定依赖和 Python >=3.9 合同不变。
- 上传服务复用 infrastructure 的既有大小格式化所有者；新增内部依赖边必须进入
  精确结构合同，七目录所有权和依赖方向保持有效。

### D04 New Or Changed Invariants

- resumable 批次失败后，CLI 显示当前批次已哈希、LFS 已预上传和本地待确认的文件数
  与字节数，且不把预上传误报为已提交。
- 部分或全部元数据无法观察时明确显示未知数量；不可观察项不伪装成零进度。
- 新增状态只描述当前失败批次；命令级累计确认继续由既有汇总表示。

### D04 Focused Tests And Evidence

- 在 `tests/test_upload_batching.py` 中构造真实本地 HF 元数据，先证明旧实现遗漏断点
  状态，再覆盖已哈希、LFS 已预上传、本地待确认和字节统计。
- 覆盖部分已提交、混合 regular/LFS、元数据读取失败、首次失败无进度、成功输出和
  ordinary 路径不变；观察错误不能覆盖原始失败。
- 更新 `tests/development_floor_contract.py` 的既有能力与新增不变量，测试脚本总数不变。
- 更新 `tests/structure_contract.py` 登记上传服务复用文件大小格式化函数的真实依赖边。
- 完成后运行相关批次、错误脱敏、领域所有权、开发底线和依赖合同专项，以及
  `python tests/run_cli_baseline.py`、`python -m compileall -q .`、
  `python -m pip check`、Python 3.9 语法检查和 `git diff --check`。
- 全部验证仅离线执行；真实 AtomGit、Windows/Linux 和真实 Python 3.9 解释器不在
  本次授权范围，作为剩余风险报告。

### D04 Implementation Phases And Acceptance

1. 补充能证明旧失败汇总遗漏已持久化进度的红灯回归。
   验证：旧实现因缺少断点状态而失败，原有断点和累计断言继续通过。
2. 实现只读统计与失败输出，不改上传状态机或跨进程协议。
   验证：进度、未知状态、原始错误保持和敏感信息边界专项通过。
3. 同步最小文档和开发底线，运行完整离线门禁并执行独立审查。
   验证：无未解决发现后提交维护者人工验收；未获授权前不提交或交付。

### D04 Verification Evidence

- 红灯回归：`python tests/test_upload_batching.py` 退出 1；既有 12 个场景通过，新增
  “failure summary preserves checkpoint progress” 失败。模拟元数据已保存 20/20 哈希、
  1/2 LFS 预上传和 1 个已提交文件，旧实现仍只显示累计确认与总汇总，未输出断点状态。
- 红灯阶段确认原因与 D04 一致，当时尚未修改产品实现或运行完整基线。
- 实现后专项：批次、开发底线、打包元数据、上传所有权、错误脱敏、上传进度、
  resumable、结构、导入顺序、HF 依赖、错误处理、统计、恢复、SDK 超时和架构 parity
  共 14 个隔离脚本通过。
- 首轮完整离线基线：`python tests/run_cli_baseline.py`，**93 passed in 112.92s**；
  首轮审查修复后重新运行，**93 passed in 109.91s**。
- 维护者授权后的最终验收：`python tests/run_cli_baseline.py`，
  **93 passed in 100.75s**；`python -m compileall -q .`、`python -m pip check`、
  `git diff --check`、6 个变更 Python 文件的 Python 3.9 AST、锁定依赖版本与真实
  `get_local_upload_paths` 签名复核全部通过。
- `python -m compileall -q .`、`python -m pip check`、`git diff --check` 通过；6 个变更
  Python 文件通过 Python 3.9 AST 语法解析。
- 锁定依赖为 `huggingface-hub==1.1.7`、`httpx==0.28.1`；真实上传元数据为 8 行格式，
  `LocalUploadFileMetadata` 含对应状态字段，路径解析使用锁定的
  `get_local_upload_paths(local_dir, filename)`。
- 新增 `RESUMEUP-005`，开发底线保持 28 项能力、92 个隔离脚本，不变量 119 -> 120；
  精确格式债务因测试内既有生成器表达式被同一修改替换而收紧为 Black 409，isort 88、
  Ruff 44 不变。新增结构依赖边已登记，结构专项 18/18 通过。
- 差异均为文本且没有未跟踪生成物；原有五份规范文档修改保持原样，本任务仅在已有
  修改的 `.ai/DEVELOPMENT_FLOOR.md` 精确更新一处不变量计数。
- 未运行真实 AtomGit、Windows/Linux 或真实 Python 3.9 解释器；这些仍是 D04 的
  已知剩余风险，不影响已授权的 Git 交付。

### D04 Activation Status

- [x] 维护者接受 D04 行为和边界。
- [x] D04 已写入后继开发 Issue 并明确激活。
- [x] 本地任务分支已从当前 `yuto` 创建。
- [x] 红灯回归已证明旧行为。
- [x] 实现、文档和开发底线已完成。
- [x] 专项与完整离线门禁通过。
- [x] 首轮审查发现已修复，全新独立审查通过。
- [x] 维护者授权 AI 最终验收；最终门禁无误，D04 实现已接受。
- [x] 提交、本地合并、限定推送与远端一致性核验完成。

### D04 Independent Review

- 首轮审查：`REQUEST CHANGES`。发现 2 个 P2：讨论 Issue 的持久快照仍停留在 D04
  刚激活、尚未运行回归的旧阶段；“状态未知”仅用替换函数抛错验证，没有覆盖 HF 1.1.7
  对损坏元数据会记录本地路径并删除文件的真实读取行为，因此新统计的纯观察合同缺少
  直接证据。
- 修复要求：使用不修改元数据、不记录路径的只读快照解析覆盖失败汇总；增加真实损坏
  元数据回归并证明文件保持、输出脱敏和未知计数；同步两份交接后重跑专项与完整门禁，
  再进行全新审查。
- 修复结果：两项发现均已处理。失败统计改用不修改元数据、不记录路径的 8 行快照解析；
  新增真实损坏元数据回归，证明损坏文件保持不变、原始失败继续报告、未知数量明确且
  本地路径和解析明细不进入输出。同步交接后，专项 14/14、完整离线基线 93/93、
  compileall、pip check、Python 3.9 语法、锁定依赖签名和差异检查全部通过。
- 全新审查：无 P0–P3 发现。已核对 D04 验收行为、完整差异、相关源码与测试、用户文档、
  HF 1.1.7 真实实现和签名、Python 3.9 语法、开发底线映射、脱敏与权限边界；首轮两项
  P2 均已关闭。
- 缺失证据与剩余风险：无必需证据缺失；未运行真实 AtomGit、Windows/Linux 或真实
  Python 3.9 解释器，且未验证未来 HF 版本，均已明确保留为授权外风险。
- 结论：`APPROVED`。该结论不授权提交、合并、推送、关闭 Issue 或发布。

### D04 Delivery Verification

- D04 实现提交：`e0459f26b841e816cf1c2a021435029dd7780a10`
  （`fix(upload): report resumable failure progress`）。
- 本地 no-ff 合并提交：`bca794b99ca39a7afc40b20bdd9aa23e4d9ddc23`
  （`merge: report resumable failure progress`）；其提交树与已验收实现提交一致。
- 仅推送 `github/yuto`；推送后远端 `yuto` 与本地合并提交一致，远端不存在
  `codex/d04-upload-failure-progress` 分支。未修改 `main` 或 `atomgit` 远端。
- 最终交付前完整离线基线 93 passed in 100.75s；compileall、pip check、Python 3.9
  语法、锁定依赖签名、差异与敏感信息检查通过。
- 原有五份规范文档修改未进入 D04 实现或合并提交，继续保留在本地工作区。

### D05 Objective And Evidence

避免远端提交已经完成、但新 commit 的 LFS pointer 因暂时不可读或网络波动而被一次
确认请求立即判为上传失败。当前单文件、普通目录、resumable、原生 SDK 和历史 SDK
最终均进入共享的 `verify_canonical_lfs_pointers`；该函数对每个 pointer 只调用一次
V5 contents API。读取、解析或逐字节比较失败会立即进入安全失败路径，现有提交重试
不会重读该 pointer。

本结论来自当前源码、测试、Git 历史和既有故障记录的只读核对；D05 尚未执行新的
真实 AtomGit 远程复现。

### D05 Accepted Behavior

- 每个尚未确认的 pointer 最多读取 3 次；第一次失败后等待 2 秒，第二次失败后等待
  4 秒。任意一次读取到与预期完全一致的规范 pointer 即确认成功。
- 每次只使用同一个 repo ID、文件路径、已返回 commit SHA 和调用方有效请求超时 N；
  不新增隐藏总时限。
- 重试只允许读取 V5 contents API，不得重复 LFS 对象上传、preupload 或
  create-commit。已确认的 pointer 不重读，只重试当前失败项。
- 输入 token、repo ID、revision 或 timeout 无效时在重试前立即失败；Ctrl+C 立即
  向上传播，不等待剩余次数。
- 三次失败后保留现有 `CanonicalLfsPointerError`、CLI/SDK/resumable 安全包装和失败
  关闭语义。该结果只表示客户端无法安全确认上传成功，不能断言 pointer 内容必然错误。
- 正常首次确认成功时没有额外等待；本次不增加中间重试日志或公共配置项。

### D05 Implementation Scope

1. 在 `src/atomgit/adapters/lfs/pointer.py` 的共享验证边界用标准库休眠和私有固定退避
   常量实现单 pointer 循环；输入校验位于循环前，只让远程读取、响应解析和内容不匹配
   进入有界重读。
2. 扩展现有 `tests/test_canonical_lfs_pointer.py`，先增加能证明旧实现第一次失败即退出
   的红灯回归，再覆盖恢复、耗尽、顺序、timeout、输入校验、脱敏和 Ctrl+C。
3. 扩展 `tests/test_resumable_commit_policy.py`，证明确认恢复或耗尽时 create-commit 均
   只调用一次，并且 resumable 本地 committed 标记只在确认成功后写入。
4. 在 `tests/development_floor_contract.py` 登记新增 `LFS-005`，并同步 README、上传分析、
   架构和开发底线的最小权威说明；不新增测试脚本、依赖或公共接口。

### D05 Affected Capability IDs

`UPLOAD-FILE`、`UPLOAD-FOLDER`、`UPLOAD-RESUMABLE`、`UPLOAD-LFS`、`SDK-UPLOAD`、
`ERROR-REDACTION`、`RUNTIME`、`ARCHITECTURE`、`PORTABILITY` 和 `FLOOR-REGISTRY`。

### D05 Protected Existing Invariants

- 规范 pointer 继续按返回 commit SHA 读取原始 Git blob 并逐字节验证；无法确认不能
  误报上传成功，也不能下载大型 LFS 对象代替验证。
- CLI、原生 SDK、历史 SDK 的参数、签名、返回值和异常层次保持兼容；所有入口继续
  共享同一验证边界和调用方有效请求超时 N。
- token、Authorization、签名 URL、响应正文、仓库细节和底层异常原文不得进入输出、
  worker envelope、SDK 错误或测试夹具。
- resumable 只有确认成功后才能标记本地 committed；失败保留断点，取消继续清理子进程。
- D01 的上传总时长不限、D03 的 pointer 请求超时、D04 的失败断点状态、HF 60 秒写入
  等待、有限提交/preupload 重试和全局状态恢复均不改变。
- `huggingface-hub==1.1.7`、`datasets==4.4.1`、Python >=3.9、七目录所有权和离线默认
  测试合同保持不变。

### D05 New Or Changed Invariants

- `LFS-005`：同一 commit 的 pointer 确认只允许最多 3 次有界只读尝试，等待严格为
  2 秒和 4 秒；任何上传、preupload 或 create-commit 写操作不得因此重复。
- 多 pointer 验证按既有顺序执行；已经成功的项目不重读，仅当前失败项目消耗重试次数。
- 三次耗尽后保持未确认状态和现有安全错误；确认失败与 pointer 内容确定错误不能混同。

### D05 Focused Tests And Evidence

- 红灯：模拟第一次读取失败、随后成功；旧实现必须因只读取一次而失败，且原因与 D05
  一致。实现前不以删除或放宽现有断言替代红灯。
- 恢复：覆盖首次失败后成功、前两次失败后成功、内容暂时不匹配后恢复；断言请求次数、
  `2.0/4.0` 等待、相同 commit SHA 和 timeout N。
- 耗尽：持续读取失败、畸形响应或内容不匹配时恰好尝试 3 次，只抛最终安全错误；断言
  token、URL、响应正文和敏感仓库细节未泄露。
- 顺序与写入：多 pointer 时不重读已确认项；普通包装的 upload 和 resumable 的
  create-commit 均只执行一次，失败不写 committed，恢复后才写。
- 边界：无效 token/repo ID/revision/timeout 立即失败；读取或退避期间 Ctrl+C 直接中止。
- 专项至少运行 `test_canonical_lfs_pointer.py`、`test_resumable_commit_policy.py`、
  `test_upload_resumable.py`、`test_upload_file_no_copy.py` 和 `test_sdk_upload_timeout.py`。
- 最终在 `atomgit_cli` conda 环境运行 `python tests/run_cli_baseline.py`、
  `python -m compileall -q .`、`python -m pip check`、Python 3.9 语法与
  `git diff --check`，并执行凭证、生成物、依赖合同和最终差异检查。

### D05 Implementation Phases And Acceptance

1. 激活后从当前 `yuto` 创建本地 `codex/d05-pointer-verification-retry`，冻结调用链、
   锁定依赖和现有错误合同，增加红灯回归。
   验证：旧实现按预期失败，且没有修改生产代码或远端状态。
2. 在共享验证边界实现只读重试并补齐直接及 resumable 回归。
   验证：恢复、耗尽、无重复写入、状态顺序、脱敏、timeout 和取消专项通过。
3. 同步开发底线与最小文档，运行完整离线门禁并进入独立审查。
   验证：无未解决发现、完整基线通过后提交维护者人工验收；未获授权前不提交或交付。

### D05 Non-Goals And Residual Risks

- 不按 HTTP 状态、传输、权限、响应格式或内容不匹配细分错误，也不改变公开错误子类；
  精确分类留给 D07。
- 不区分“远端已提交”和“本地已确认”，不解决状态不明后的重复提交；留给 D06/D08。
- 当前统一错误合同会让确定性远端失败最多额外等待 6 秒；若每次请求均耗尽 N，单个失败
  pointer 的最坏结束时间接近 `3N + 6 秒`。
- 不新增重试事件、CLI/SDK 参数、依赖、线程、后台看门狗或上传总时限。
- 真实 AtomGit 最终一致性、Windows/Linux 和真实 Python 3.9 解释器未验证；远程写入
  测试需要维护者另行授权，不能用离线 mock 冒充。

### D05 Complete Baseline Evidence

- 实施前：`python tests/run_cli_baseline.py`，93 passed in 106.35s。
- 红灯：`python tests/test_canonical_lfs_pointer.py`，25/26；新增首次读取失败后恢复
  用例在旧实现上只读取 1 次并失败，其余既有项通过。
- 实现专项：canonical pointer 34/34、resumable commit 55/55、resumable 上传 61/61、
  单文件入口 21/21、SDK timeout 9/9、开发底线 15/15、打包元数据 13/13。
- 完整基线：首次 93 passed in 107.41s；同步当前 28 个能力、121 条不变量和 93 个测试
  脚本的文档计数后，最终 93 passed in 106.98s。
- `python -m compileall -q .`、`python -m pip check`、Python 3.9 语法解析、Ruff、生产
  文件 Black、格式债务指纹和 `git diff --check` 通过；无新增依赖、测试脚本、公共参数、
  未跟踪生成物或真实凭证。

### D05 Independent Review

- Procedure: 在实现与最终完整门禁后切换独立 reviewer 角色，依据 D05 合同、完整任务
  差异、调用链、锁定依赖签名和测试证据审查；审查阶段未编辑文件。
- Findings: 无 P0、P1、P2 或 P3 发现。
- Evidence: 重试只包围共享 V5 contents 读取、解析和逐字节比较；固定三次上限与
  `2.0/4.0` 退避、同一 commit/path/timeout、多 pointer 顺序、输入预检、Ctrl+C、
  脱敏以及普通/resumable 不重复写入均有离线回归。公开签名和 HF 1.1.7 调用未变。
- Residual risks: 未执行真实 AtomGit 最终一致性、Windows/Linux 或真实 Python 3.9
  解释器运行；离线 mock 不作为远程证据。
- Verdict: `APPROVED`。该结论不授权提交、合并、推送、关闭 Issue 或发布。

### D05 Activation Status

- [x] 维护者接受 D05 行为、权衡和边界。
- [x] 维护者授权将 D05 完整方案写入本地开发 Issue。
- [x] 维护者单独授权激活 D05。
- [x] 本地任务分支已创建。
- [x] 红灯回归、实现、文档和开发底线已完成。
- [x] 专项、完整离线门禁和独立审查通过。
- [x] 维护者完成人工验收并授权适用的 Git/远程交付。

### D06 Objective And Evidence

当上传边界已经返回有效 commit SHA、但后续 LFS pointer 确认失败时，
明确区分“远端提交已创建”和“客户端本地未确认”，不再将两个状态压缩成
无上下文的普通上传失败。整体结果仍必须失败关闭，不得误报上传成功。

当前 `src/atomgit/adapters/lfs/pointer.py` 在上传返回 result 及有效 `oid` 后才调用
`verify_canonical_lfs_pointers`；确认耗尽时直接抛出 `CanonicalLfsPointerError`，
已返回的远端 commit 事实没有进入稳定失败合同。resumable 的
`_ResumableCommitController` 也在 `create_commit` 返回后执行 pointer 确认，只在
全部确认通过后调用 `_mark_resumable_operations_committed`；因此确认失败时
远端 commit 可以已存在，而本地 `is_committed` 仍为 false。当前 CLI、worker 和
SDK 错误只显示 pointer 验证失败，用户不能区分远端已写入和远端状态未知。

### D06 Accepted State And Interface Contract

| 观测边界 | 远端状态 | 本地确认 | 对外结果 |
|---|---|---|---|
| 未取得有效 commit 响应 | `unknown` | `unconfirmed` | 保持原错误，不得宣称已提交 |
| 取得有效 commit SHA，pointer 确认失败 | `created` | `unconfirmed` | 独立细分失败，返回非成功 |
| 取得有效 commit SHA，pointer 确认成功 | `created` | `confirmed` | 保持现有上传成功 |

- 新增 `CanonicalLfsCommitUnconfirmedError`，继承现有
  `CanonicalLfsPointerError`，仅包装“已取得有效 commit SHA 后的 pointer 确认
  失败”。其稳定安全字段为 `remote_commit_status="created"`、
  `local_confirmation_status="unconfirmed"` 和 `commit_revision`。
- 新错误保留验证错误为 `__cause__`，但稳定错误文本和 CLI 不得输出 token、
  鉴权头、签名 URL、响应正文、源/远端路径或 commit SHA。SDK 的结构化结果可以
  返回 `commit_revision`，但不将它插入可能被常规打印的底层异常原文。
- CLI 在上述已知状态下显示“远端提交已创建但未确认”、“远端提交状态：
  已创建”和“本地确认状态：失败”，返回非零退出码且不打印上传成功。提示用户
  不要将结果当作“未提交”，应先确认远端状态再决定是否重试。
- 原生 `AtomGitClient` 保持 `OperationResult`。该失败必须为 `ok=False`，并在
  `metadata` 中提供 `remote_commit="created"`、`local_confirmation="unconfirmed"` 和
  `commit_revision`；`error` 保留稳定脱敏错误。
- 历史 `atomgit_hub` 不改函数签名和成功返回，通过新子类报告该失败；已有
  `except CanonicalLfsPointerError` 仍能捕获。历史 `AtomGitAPI` 保留布尔失败返回合同，
  在返回 false 前输出上述独立安全状态。
- resumable worker 使用独立安全类别 `remote_commit_unconfirmed` 和经过校验的
  `commit_revision` 穿过子进程 envelope；CLI 不打印 revision，原生 SDK 可将其写入
  失败 metadata；不重复上传、preupload 或 create-commit，不进入 commit 降批，并保持
  本地 `is_committed=False`。失败汇总另行说明“远端已提交但本地未确认”。
- D06 不新建持久化状态文件，不改 HF 元数据格式。跨重启安全对账和防重复提交
  由 D08 决定；读取不可达、响应畸形和内容不匹配的精确分类由 D07 决定。

### D06 Implementation Scope

1. 在 `src/atomgit/adapters/lfs/pointer.py` 增加细分错误，将上传返回与 pointer 确认
   分成明确边界；只对有效 commit SHA 后的确认失败标记 `created/unconfirmed`。
2. 在 `src/atomgit/adapters/upload/resumable.py` 区分 create-commit 异常和提交后确认
   异常，扩展 worker 安全结果类别，保留已有重试、降批、对账和本地标记顺序。
3. 在 `src/atomgit/adapters/upload/errors.py`、`service.py`、`adapters/sdk_errors.py`、
   `adapters/huggingface.py` 及必要的 SDK/兼容边界传递状态，不改公开调用签名。
4. 扩展现有测试，不为 D06 新建测试脚本；同步 README、FAQ、上传分析、架构和
   开发底线的最小权威说明。

### D06 Affected Capability IDs

`CLI-SURFACE`、`CLI-DISPATCH`、`UPLOAD-FILE`、`UPLOAD-FOLDER`、`UPLOAD-RESUMABLE`、
`UPLOAD-LFS`、`SDK-UPLOAD`、`ERROR-REDACTION`、`RUNTIME`、`ARCHITECTURE`、
`PORTABILITY` 和 `FLOOR-REGISTRY`。

### D06 Protected Existing Invariants

- pointer 仍按返回 commit SHA 读取原始 Git blob 并逐字节验证；三次尝试、
  `2.0/4.0` 退避、请求超时 N 和已确认 pointer 不重读的 D05 合同不变。
- 任何 pointer 未确认都不得误报上传成功；resumable 只有确认通过后才标记
  `is_committed=True`，失败保留断点，取消继续清理子进程。
- 上传、preupload、create-commit、提交重试/降批次数及顺序不因 D06 变化。
- CLI、原生 SDK 和历史接口的公开参数、成功返回、repo type/revision 和
  timeout 传递保持；新错误子类保持对现有基类捕获的兼容。
- token、签名 URL、响应正文、路径、底层异常原文不得进入 CLI、worker envelope、
  SDK 错误、测试输出或文档示例。
- `huggingface-hub==1.1.7`、`datasets==4.4.1`、Python >=3.9、七目录所有权、
  全局状态恢复和完整离线基线合同不变。

### D06 New Or Changed Invariants

- 有效 commit SHA 已返回且 pointer 确认失败时，所有公开上传入口稳定报告
  `remote_commit=created` 和 `local_confirmation=unconfirmed`，同时保持失败结果。
- 没有有效 commit 响应时不得宣称已创建远端提交；提交结果不明确仍为
  `unknown/unconfirmed`。
- 新细分错误不触发上传、preupload、create-commit、降批或无界重试，
  resumable 本地 committed 状态仍只代表客户端已完成 pointer 确认。
- CLI 必须显示已知远端/本地状态并非零退出；SDK 必须给出可编程读取的
  状态和 commit revision，同时所有人类可见错误保持脱敏。

### D06 Focused Tests And Evidence

- 红灯：普通上传回调返回有效 `oid`，pointer 三次确认耗尽；旧实现只能给出
  普通 `CanonicalLfsPointerError`，无法观察已创建的远端 commit 状态。
- 阶段边界：提交前异常、缺少/无效 `oid`、提交响应超时均不得标记
  `remote_commit=created`；验证成功的旧路径完全不变。
- resumable：create-commit 返回有效 SHA 后确认耗尽，断言 create-commit 仅一次、
  不降批、新 worker 类别和经过校验的 revision 到达父进程、CLI 不打印 revision、
  `is_committed=False` 且断点保留。
- CLI：单文件、普通目录和 resumable 目录均返回非零，输出已创建/未确认状态、
  不输出成功，不暴露任何禁止字段。
- SDK：原生 `OperationResult.ok=False` 且 metadata 字段完整；历史
  `atomgit_hub` 异常子类可被现有基类捕获；历史 `AtomGitAPI` 仍返回 false。
- 多 pointer：前面项验证成功、后面项失败时，整个 commit 仍报告已创建/未确认，
  不虚构逐文件持久成功状态。
- 优先扩展 `tests/test_canonical_lfs_pointer.py`、`tests/test_resumable_commit_policy.py`、
  `tests/test_upload_error_classify.py`、`tests/test_upload_error_handling.py`、
  `tests/test_upload_batching.py`、`tests/test_upload_resumable.py` 和已有 SDK 错误/参数测试；
  不新增测试脚本。
- 实施完成后在 `atomgit_cli` conda 环境运行 `python tests/run_cli_baseline.py`、
  `python -m compileall -q .`、`python -m pip check`、Python 3.9 语法、锁定依赖签名、
  格式债务、凭证模式、生成物和 `git diff --check`。

### D06 Implementation Phases And Acceptance

1. 单独授权激活后，从当时 `yuto` 创建本地 `codex/d06-commit-confirmation-state`，
   冻结公开签名、成功返回、worker envelope 和错误脱敏合同，先添加红灯回归。
   验证：旧实现仅因丢失远端 commit 状态而失败，不访问真实 AtomGit。
2. 在共享 pointer 和 resumable 提交边界实现细分状态，贯通 worker、CLI 和 SDK。
   验证：已创建/未确认、远端未知、确认成功、无重复写入、断点与脱敏专项通过。
3. 同步最小用户文档和开发底线，运行完整离线门禁并进入独立审查。
   验证：完整基线通过、无未解决发现后才提交维护者人工验收；未获授权前不提交、
   合并或推送。

### D06 Non-Goals And Residual Risks

- 不区分传输不可达、最终一致性、响应畸形和字节不匹配；精确错误分类留给 D07。
- 不持久化远端 commit 状态，不在重启后自动查询、跳过或重提交；防重复与恢复策略
  留给 D08。
- 服务端已写入但 commit 响应在返回前丢失时，D06 仍只能标记
  `unknown/unconfirmed`，不能凭推测升级为 `created`。
- 多 pointer 提交可能在前面项已读取、后面项失败时整体保持未确认；D06 不引入
  逐文件新持久模型。
- 真实 AtomGit 远程、Windows/Linux 和真实 Python 3.9 解释器默认未验证；离线 mock
  不得作为远程证据。

### D06 Compatibility And Rollback

- 这是错误语义的增量细化；CLI 参数、SDK 公开函数签名、成功返回和 HF 传输调用
  不变。依赖精确错误文本的脚本可能观察到新分类，需在 README/FAQ 明确说明。
- 新异常继承旧基类；历史 `AtomGitAPI` 布尔合同和 resumable `is_committed`
  含义不变。SDK metadata 的新字段为增量信息。
- D06 不引入数据迁移。如回归无法解决，可整体回退未来单一 D06 实现提交；
  回退只恢复旧错误展示，不修改任何远端上传数据。

### D06 Activation Status

- [x] 维护者接受 D06 状态、接口、兼容和范围边界。
- [x] 维护者授权将 D06 完整方案写入本地开发 Issue。
- [x] 维护者单独授权激活 D06。
- [x] 本地任务分支已创建。
- [x] 红灯回归、实现、文档和开发底线已完成。
- [x] 专项、完整离线门禁和独立审查通过。
- [x] 维护者完成人工验收并授权适用的 Git/远程交付。

### D07 Objective And Evidence

在提交已经创建后，对 LFS pointer 确认失败原因进行安全、可理解的细分汇报，避免
把“无法读取 pointer”和“已读取但内容不匹配”压缩成同一种错误。整体上传仍必须
失败关闭；本方案不改变 D05 已确认的三次只读确认、`2/4` 秒退避或只读重试边界。

当前 `src/atomgit/adapters/lfs/pointer.py` 的 `_read_raw_pointer` 将 HTTP、网络、
超时、响应过大、响应格式异常等普通读取错误统一转换为 `CanonicalLfsPointerError`；
逐字节比较失败也抛出相同基类。D06 随后只保留 `remote_commit=created`、
`local_confirmation=unconfirmed`，导致 CLI、resumable worker 和 SDK 无法说明
确认失败的实际原因。

### D07 Accepted Behavior And Error Contract

- 三次只读确认和等待保持不变；只有三次耗尽后，才向外报告最后一次失败的安全原因。
- 有效 commit SHA 已返回时，继续报告 `remote_commit=created`、
  `local_confirmation=unconfirmed`，并增加 `confirmation_failure` 原因码。
- 没有有效 commit SHA 时，不得宣称远端提交已创建，继续使用原有未知/未确认错误语义。
- 原因码固定为以下白名单；未识别情况统一降级为 `unknown_read_failure`：

| 原因码 | 判断边界 | 易懂报错核心 |
|---|---|---|
| `authentication_failed` | HTTP 401 | 确认请求的登录凭证无效，请重新登录并先核对远端状态。 |
| `permission_denied` | HTTP 403 | 当前账号无权读取 pointer，请检查仓库权限并先核对远端状态。 |
| `pointer_unavailable` | HTTP 404 或确认接口暂未找到 pointer | 未找到对应 pointer，这不能证明远端提交不存在，请先核对远端状态。 |
| `rate_limited` | HTTP 429 | pointer 确认请求受到限流，请稍后核对远端状态。 |
| `service_unavailable` | HTTP 5xx | pointer 确认服务暂时不可用，请稍后核对远端状态。 |
| `request_timeout` | 请求/响应读取超时 | 读取 pointer 超时，请检查网络并先核对远端状态。 |
| `connection_failed` | DNS、代理、TLS、连接中断等网络错误 | 无法连接确认接口，请检查网络并先核对远端状态。 |
| `request_rejected` | 其他 HTTP 错误或异常重定向 | 确认请求被服务拒绝，请核对仓库状态或联系平台支持。 |
| `response_too_large` | 响应超过 64 KiB | 确认接口返回数据异常过大，未能读取 pointer，请联系平台支持。 |
| `response_malformed` | 非 UTF-8、无效 JSON、字段/编码/Base64 异常 | 确认接口返回格式异常，未能解析 pointer，请联系平台支持。 |
| `content_mismatch` | 已读取 blob，但任意字节与预期不一致 | pointer 内容与本次上传预期不一致，请联系平台支持检查该提交。 |
| `unknown_read_failure` | 其他无法安全识别的读取异常 | 读取 pointer 时发生未知错误，请先核对远端状态。 |

- CLI 保留“远端提交已创建但未确认”的失败标题，附带上述原因的中文建议，返回
  非零退出码；不得输出 commit SHA、路径、OID、URL、响应正文或凭证。
- 原生 SDK `OperationResult.ok` 保持 `False`，在现有 metadata 中增量加入
  `confirmation_failure`；经校验的 `commit_revision` 仍可作为结构化字段返回。
- resumable worker envelope 的新增字段只传白名单原因码，并保留 D06 已校验的
  `commit_revision` 和状态类别；历史 `atomgit_hub` 继续通过
  `CanonicalLfsPointerError` 基类捕获，公开函数签名和成功返回不变。
- 原因只表示最后一次确认失败的安全类别，不保存或传递异常原文，不新增公共参数、
  重试日志、持久化状态或异常类。

### D07 Implementation Scope

1. 在 `src/atomgit/adapters/lfs/pointer.py` 的读取和比较边界建立原因码判断；保留
   现有异常基类、三次尝试、`2/4` 秒等待、请求 timeout 和脱敏合同。
2. 在 `src/atomgit/adapters/upload/errors.py`、`resumable.py` 和上传 service 中
   传递并校验白名单原因码，生成对应 CLI 提示；不改变上传/提交重试和状态标记顺序。
3. 在 `src/atomgit/adapters/sdk_errors.py` 及必要 SDK 边界增加结构化原因 metadata；
   不修改 `atomgit_hub` 和 `AtomGitAPI` 的公开签名、成功返回或布尔失败合同。
4. 扩展现有 pointer、resumable、CLI/API、SDK、架构 parity 和错误分类测试；同步
   README、FAQ、上传分析、架构和开发底线的最小说明，不新增测试脚本或依赖。

### D07 Affected Capability IDs

`UPLOAD-FILE`、`UPLOAD-FOLDER`、`UPLOAD-RESUMABLE`、`UPLOAD-LFS`、`SDK-UPLOAD`、
`ERROR-REDACTION`、`ARCHITECTURE`、`PORTABILITY` 和 `FLOOR-REGISTRY`。

### D07 Protected Existing Invariants

- D05 的三次只读确认、`2.0/4.0` 退避、同一 commit/path/timeout、已确认 pointer
  不重读和不重复写入保持不变。
- D06 的 `created/unconfirmed` 状态、`is_committed=False`、失败返回和无合法 SHA
  时的未知状态保持不变。
- CLI、原生 SDK、历史 SDK 的公开参数、成功返回、错误基类兼容和 model/dataset、
  revision 行为保持不变。
- 任何人类可见输出、SDK 错误和测试输出均不得泄露 token、URL、响应正文、路径、
  OID、commit SHA 或底层异常原文；内部 worker envelope 除 D06 已校验的
  `commit_revision`、状态类别和本次白名单原因码外不得传递其他远端细节。
- `huggingface-hub==1.1.7`、`datasets==4.4.1`、Python >=3.9、全局状态恢复、
  临时资源和完整离线基线合同不变。

### D07 New Or Changed Invariants

- `LFS-007`：三次确认耗尽后，pointer 读取/响应/内容比较失败必须映射到固定白名单
  原因码；无法安全识别时只能使用 `unknown_read_failure`。
- `LFS-008`：CLI、resumable worker 和原生 SDK 使用同一原因码；CLI 展示易懂建议，
  SDK metadata 提供机器可读原因，且均保留 D06 的远端/本地状态。
- `REDACT-003`：原因分类不得通过异常原文、URL、响应正文、路径、OID 或 token 向
  公开输出或跨进程载荷传播；SHA 仅保留 D06 已校验的内部 envelope 和 SDK metadata
  字段，不进入 CLI、SDK 错误文本或测试输出。

### D07 Focused Tests And Evidence

- 扩展 `tests/test_canonical_lfs_pointer.py`，覆盖 401/403/404/429/5xx、超时、连接
  失败、异常重定向、响应过大、响应畸形、内容不匹配和未知异常的原因码。
- 覆盖每种失败仍恰好三次读取并等待 `2.0/4.0` 秒；前两次失败后恢复时不对外报告
  失败原因；混合失败只报告最后一次耗尽原因。
- 扩展 `tests/test_resumable_commit_policy.py`、`tests/test_upload_error_classify.py`、
  `tests/test_upload_error_handling.py`、`tests/test_sdk_upload_timeout.py` 和
  `tests/test_architecture_parity.py`，验证 worker envelope、CLI 提示、SDK metadata、
  历史基类捕获和状态保持。
- 验证 upload、preupload、create-commit 不重复，resumable 不降批且不标记 committed；
  无合法 SHA 时不产生 `created/unconfirmed`。
- 验证所有原因类别的输出不含 token、URL、响应正文、路径、OID 或 SHA；非法原因码
  降级为 `unknown_read_failure`。
- 最终在 `atomgit_cli` 环境运行 `python tests/run_cli_baseline.py`、
  `python -m compileall -q .`、`python -m pip check`、Python 3.9 语法、锁定依赖签名、
  凭证/生成物检查和 `git diff --check`；不执行真实 AtomGit 写操作。

### D07 Implementation Phases And Acceptance

1. 单独激活后，从当时 `yuto` 创建本地 D07 任务分支，先添加覆盖原因丢失的红灯回归。
   验证：旧实现无法区分读取失败与内容不匹配，且不访问真实 AtomGit。
2. 在共享 pointer 边界实现原因判断，贯通 post-commit、worker、CLI 和 SDK。
   验证：白名单分类、状态保留、三次确认、不重复写入和脱敏专项通过。
3. 同步用户文档与开发底线，运行完整离线门禁并进行独立审查。
   验证：完整基线通过、无未解决审查发现后才进入维护者人工验收；未获授权前不提交、
   合并或推送。

### D07 Complete Baseline Evidence

- 红灯回归：`tests/test_canonical_lfs_pointer.py` 为 37/51；新增 14 项均因旧实现没有
  `confirmation_failure` 而失败，原有 37 项保持通过。
- 实现后专项：canonical pointer 52/52、resumable commit 56/56、错误分类 58/58、
  CLI/API 错误处理 29/29、SDK timeout 11/11、架构 parity 23/23、开发底线 15/15、
  打包 13/13、结构 18/18；普通与 resumable 上传入口专项保持通过。
- 完整离线基线先后为 93 passed in 99.48s、98.45s、97.98s 和 112.18s；最终审查
  修正后为 **93 passed in 97.73s**。
- `python -m compileall -q .`、`python -m pip check`、12 个变更 Python 文件的
  Python 3.9 AST、公开异常构造签名、凭证模式、二进制差异、未跟踪生成物和
  `git diff --check` 均通过；锁定依赖仍为 `huggingface-hub==1.1.7`、
  `datasets==4.4.1` 和 `httpx==0.28.1`。
- 新增 `LFS-007`、`LFS-008`、`REDACT-003`；当前为 28 个能力、125 条不变量、
  93 个测试脚本。Black/isort/Ruff 既有债务数量保持 409/87/44，摘要已按实际更新。
- 未执行真实 AtomGit、Windows/Linux 或真实 Python 3.9 解释器；没有执行远程写入、
  提交、合并、推送、PR、标签或发布。
- 维护者授权后的交付复验：`python tests/run_cli_baseline.py` 为 **93 passed in
  109.89s**；compileall、pip check、Python 3.9 AST、公开异常构造签名、锁定依赖、
  凭证模式、二进制差异、未跟踪生成物和 `git diff --check` 再次通过。自定义凭证
  扫描命中的三处均为现有测试中的显式占位 token，不是真实凭证。

### D07 Independent Review

- Procedure: 按 `.ai/REVIEW.md` 分阶段只读检查 D07 合同、完整差异、锁定依赖、
  pointer/worker/CLI/SDK 调用链、专项和完整门禁，不在审查角色中编辑。
- Resolved findings: 首轮发现 D06 内部 revision 合同与 D07 脱敏文字冲突、测试成功
  输出模拟 revision；后续发现不可哈希原因和畸形 HTTP 状态可破坏安全降级。均返回
  实现阶段以最小守卫和回归修复，并在每次修复后重跑专项和完整基线。
- Findings: 最终无未解决的 P0/P1/P2/P3 发现。
- Residual risks: 真实 AtomGit 状态码分布、Windows/Linux 和真实 Python 3.9 解释器
  未验证；HTTP 404 仍只能表示确认接口未找到，D08 跨重启防重复不在本次范围。
- Verdict: `APPROVED`（技术审查通过，不代表维护者人工验收或 Git/远程授权）。

### D07 Non-Goals And Residual Risks

- 不改变三次只读确认及退避，不按单次失败立即停止，也不新增重试参数或日志。
- 不实现 D08 的跨重启对账、防重复提交、自动跳过或远端状态恢复。
- HTTP 404 可能由暂时不可见、路径不存在或服务端权限策略造成；分类只能表达“确认
  接口未找到”，不能声称真实根因已经确定。
- 只传递最后一次原因，避免新增跨进程历史结构；这是有意的最小合同。
- 真实 AtomGit 状态码分布、Windows/Linux 和真实 Python 3.9 解释器仍为未验证边界。

### D07 Compatibility And Rollback

- 这是错误信息和结构化 metadata 的增量细化；不改变公开函数签名、成功返回、退出码
  方向或传输流程。依赖旧错误文本的脚本可能观察到新增原因内容。
- 原有 `CanonicalLfsPointerError` 捕获继续有效；新增原因字段缺失时按未知原因处理。
- 不涉及数据或缓存迁移。若实现回归，可整体回退 D07 单一实现提交，D05/D06 状态和
  重试合同不受影响。

### D07 Activation Status

- [x] 维护者接受 D07 方案并授权登记到本地开发 Issue。
- [x] 维护者单独授权激活 D07。
- [x] 本地任务分支已创建。
- [x] 红灯回归、实现、文档和开发底线已完成。
- [x] 专项、完整离线门禁和独立审查通过。
- [x] 维护者完成人工验收并授权适用的 Git/远程交付。

### D07 Delivery Verification

- 实现提交：`23e51d7f6a9cf979e78090418df78cdb14660b84`。
- no-ff 合并提交：`d109e6b1b7e6a92628dbe2477788069243603b87`；合并树与已验收
  任务树一致。
- 交付仅允许推送 `github/yuto`；任务分支保持本地，不执行真实 AtomGit、PR、标签、
  发布或 D08–D18 实施。
- 五份既有 `.ai` 规范修改在提交和合并前后哈希一致，未纳入 D07 交付。

### D08 Objective And Evidence

防止 resumable 上传在远端提交结果不明确或 LFS pointer 确认失败后，重新执行同一
上传身份时再次提交相同路径、产生重复历史或覆盖并发修改。重跑必须先只读核对远端
不可变快照；只有状态能够被完整证明时才恢复或继续，未知和冲突状态一律失败关闭。

当前 `src/atomgit/adapters/upload/resumable.py` 只在 pointer 验证成功后写入 HF
`is_committed=True`。D06/D07 的合法 commit revision、`created/unconfirmed` 状态和
失败原因只通过异常与 worker envelope 传递，没有跨进程持久化。锁定的 HF 1.1.7
`LocalUploadFileMetadata` 只有 `is_committed` 布尔值，无法区分“尚未提交”和“提交
结果不明”；重跑会把所有未 committed 文件再次放入 commit 队列。现有对账只处理
同一进程内的模糊网络错误，并对非 `main` revision 直接放弃匹配。

已核对锁定依赖：`HfApi.create_commit` 支持 `parent_commit`，可在不新增依赖或公开
参数的前提下建立服务端并发保护。本方案只基于源码、测试和已安装依赖签名设计，未
执行真实 AtomGit 读写。

### D08 Accepted Behavior And State Contract

- 仅处理 CLI 默认目录 resumable、`AtomGitAPI.upload_directory(resumable=True)` 和
  `AtomGitClient.upload_folder(resumable=True)`；单文件、普通目录及
  `--no-resumable` 不在 D08 范围。
- 同一上传身份继续沿用稳定投影隔离：endpoint、源目录、仓库、传输类型、revision、
  远端前缀、外层 batch size 和 batch index 均一致时才能复用状态。
- 在现有投影的 `.cache/huggingface/atomgit/pending-commit-v1.json` 保存一个私有、
  原子更新的待对账提交凭据，不修改 HF 八行 metadata 格式。凭据只有 schema version、
  `attempting` 或 `created_unconfirmed` 状态、提交前 base revision、可选的已返回 commit
  revision，以及当前提交操作的远端相对路径、大小、SHA-256、上传模式和 regular
  Git blob SHA-1；不得保存 token、URL、响应正文、异常原文或本地绝对路径。
- 凭据目录必须为 `0700`，凭据和锁文件必须为 `0600`；JSON 使用同目录临时文件和
  `os.replace` 原子替换，大小上限 64 KiB，操作数上限 20。未知版本、字段缺失、非法
  路径/摘要/大小或超限内容必须失败关闭，不能自动删除后继续提交。
- 每次远端提交前解析目标 revision 的当前不可变 SHA，先原子写入 `attempting`
  凭据，再把该 SHA 作为 `parent_commit` 调用锁定 HF API；凭据写入失败时不得调用
  `create_commit`。已验证为空的初始分支允许 base revision 为 null，但普通 404 不得
  被猜测为空分支。
- 远端返回合法 commit SHA 后，将凭据更新为 `created_unconfirmed`，再执行 D05 的
  同一 commit 三次只读 pointer 确认。只有 pointer 和 metadata 均确认成功后才设置
  `is_committed=True` 并删除凭据；任一步骤异常都保留可恢复状态。
- 重跑发现凭据时，必须在任何 upload、preupload 或 create-commit 前读取目标 revision
  的不可变快照 H1，比较每个文件的远端强摘要和大小；regular 比较 Git blob SHA-1，
  LFS 比较对象 SHA-256/大小并复用严格三行 pointer 验证。应用结果前再次解析 H2，
  只有 H1 == H2 才允许更新本地 metadata。
- 完全匹配项标记 committed，并计为“确认复用”；部分匹配只确认匹配项，冲突项保留
  在凭据中。任何读取失败、pointer 不可确认、本地内容变化、凭据损坏或 H1/H2 变化
  都不得触发新写入。
- 若当前 revision 仍等于凭据的 base revision，可证明上次尝试没有推进该分支，允许
  只对仍缺失的操作安全重试；若 revision 已前进且仍有不匹配项，则报告内容冲突并
  停止，不自动覆盖、合并或重放。
- 同一投影的“凭据读取、对账、上传子进程完成”由跨进程锁串行化；不同上传身份仍可
  并行。`parent_commit` 发生 409/412 时进入只读冲突处理，不在新 HEAD 上自动重放。
- CLI 只显示确认复用、冲突和仍需提交的数量，不显示路径、SHA、OID 或远端细节。
  全部恢复时成功汇总必须显示新增提交 0、续传跳过 N；冲突或未知状态必须返回非零并
  明确说明本次没有创建新提交。
- 原生 SDK resumable 在全部恢复时返回成功，在冲突或未知时返回失败；历史
  `AtomGitAPI.upload_directory` 保持布尔合同。公开签名、参数、默认值和普通上传
  行为不变，不提前扩展 D09/D10 monitor/Flow 数据合同。

### D08 Implementation Scope

1. 在 `src/atomgit/adapters/upload/resumable.py` 增加最小凭据读写、严格校验、投影级
   锁、不可变 revision 解析、跨重跑远端对账和 `parent_commit` 状态转换；复用现有
   `_atomgit_file_checksum`、canonical pointer 验证和 metadata 标记，不新建生产模块。
2. 在 `src/atomgit/adapters/upload/service.py` 于启动 HF worker 前执行凭据恢复，并
   准确区分确认复用、新增提交、冲突和完成数量；全已确认批次仍进入既有仓库/权限
   检查，但不能调用远端提交。
3. 在 `src/atomgit/adapters/upload/errors.py` 增加内部
   `remote_commit_conflict`、`remote_recovery_state` 安全类别，worker 只传固定类别、
   原因码和有界数量；不新增公开异常基类。同步 `compatibility/api.py` 的 owner、consumer
   和 patch 接缝，保持历史 monkeypatch/导入身份。
4. 保留现有 429、413 降批、模糊网络错误对账和 auto-configure-lfs 流程：413 在确认
   未写入后清理原组凭据再建立子组凭据；409/412 保留凭据并失败关闭；网络、5xx、
   Ctrl+C 或进程崩溃保留凭据。已 committed 条目和遗留凭据必须可幂等收敛。
5. 扩展既有 resumable commit、batching、CLI/SDK、HF 签名、cache 和 portability 测试；
   同步 README、FAQ、上传分析、架构和开发底线说明。不新增依赖、公共参数或测试脚本。

### D08 Affected Capability IDs

`UPLOAD-RESUMABLE`、`UPLOAD-LFS`、`REVISION`、`SDK-UPLOAD`、`CACHE`、
`DEPENDENCY-CONTRACT`、`ERROR-REDACTION`、`PORTABILITY`、`ARCHITECTURE` 和
`FLOOR-REGISTRY`。

### D08 Protected Existing Invariants

- D05 的同一 commit/path/timeout 三次只读确认、`2.0/4.0` 退避和已确认 pointer
  不重读保持不变；D06 的 `created/unconfirmed` 和 D07 的最终白名单原因码保持。
- 未确认状态不能标记 committed，失败不能误报成功；已确认文件、预上传对象和完成
  批次不得重复写入，源文件与稳定投影 metadata 不得损坏。
- 上传总时长继续不限，请求 timeout、429 重试、413 降批、模糊错误对账、LFS 慢流
  恢复、auto-configure-lfs、Ctrl+C 子进程清理及全局 HF 状态恢复不得退化。
- CLI、原生 SDK 和历史 API 的公开签名、默认值、model/dataset、revision、repo ID、
  path-in-repo、ignore 和成功返回合同不变；非 resumable 入口不受影响。
- 所有人类可见输出、SDK 错误、worker envelope 和测试日志不得泄露 token、URL、响应
  正文、本地绝对路径、远端路径、OID、commit SHA 或底层异常原文。
- `huggingface-hub==1.1.7`、`datasets==4.4.1`、Python >=3.9、source/editable/wheel/
  sdist、Windows/POSIX 和 93 脚本完整离线基线合同不变。

### D08 New Or Changed Invariants

- `RESUMEUP-006`：resumable 提交意图必须在远端写入前私密、原子持久化；跨进程重跑
  必须先对账，不能盲目重复提交或覆盖已前进 revision。
- `LFS-009`：只有同一不可变 revision 上的强摘要、大小和规范 LFS pointer 全部匹配，
  待确认文件才能转为 committed；不匹配、读取未知或并发变化不得触发新写入。
- 可执行登记从当前 Git 权威状态的 28 个能力、125 条不变量、93 个测试脚本更新为
  28 个能力、127 条不变量、93 个测试脚本；不得使用 TASK 历史段落中的旧计数。

### D08 Focused Tests And Evidence

| 场景 | 必须证明的结果 |
|---|---|
| 首次 commit 返回 SHA、pointer 确认耗尽，独立第二次运行 | 累计 create-commit 恰好一次；第二次只读确认、标记 committed 并清理凭据 |
| commit 响应超时或进程在返回前退出，远端实际已完成 | `attempting` 凭据保留；重跑确认远端后不重复提交 |
| 当前 revision 等于 base、目标操作仍缺失 | 以同一 `parent_commit` 只提交缺失操作 |
| 当前 revision 已前进且部分内容不同 | 匹配项可确认，冲突项保留；本次 create-commit 为零且返回非零 |
| pointer 读取超时、404、畸形或内容不匹配 | 保持 D05/D07 次数与原因；凭据保留且无新写入 |
| H1/H2 不同或 409/412 | 识别并发变化，禁止在新 HEAD 自动重放 |
| 本地内容变化、凭据损坏/超限/未知版本 | 失败关闭，不删除保护状态、不输出敏感字段、不远端写入 |
| regular、LFS、混合批次与部分 metadata 保存后崩溃 | 状态幂等收敛，统计准确，完成项不重做 |
| `main`、非 `main`、model、dataset、CLI、原生 SDK、历史 resumable API | 路由和结果合同一致，普通上传完全不变 |
| 两个相同投影并发运行 | 投影锁与 `parent_commit` 保证最多一个提交者，另一方重新读取状态 |
| cache clear、Ctrl+C 和子进程异常退出 | 只清理 AtomGit 缓存或保留恢复凭据，凭证、源文件和其他缓存不受影响 |

优先扩展 `tests/test_resumable_commit_policy.py`、`tests/test_upload_batching.py`、
`tests/test_upload_resumable.py`、`tests/test_hf_api_contract.py`、`tests/test_cache_clear.py`
和 `tests/test_windows_compatibility.py`。红灯必须在旧实现上证明第二次提交或冲突覆盖
风险；不能仅断言内部函数或使用宽松 `**kwargs` fake。真实 HF 1.1.7
`create_commit(parent_commit=...)` 签名必须参与合同验证。

### D08 Implementation Phases And Acceptance

1. 激活后先冻结 HF metadata、create-commit、投影身份和现有恢复调用链，添加跨两次
   独立运行的红灯回归。验证：旧实现产生第二次提交，失败原因与 D08 一致。
2. 实现私有凭据、严格 schema、原子权限和投影锁。验证：损坏、并发、异常退出、
   半完成 metadata 和 cache 清理专项通过，尚不改变远端提交策略。
3. 实现不可变快照对账、二次 HEAD 检查和匹配/未知/冲突状态。验证：所有未知和冲突
   场景远端写调用为零，完全匹配能够幂等恢复。
4. 接入 `parent_commit`、控制器状态转换、413/409/412/网络错误和 CLI/SDK 统计提示。
   验证：安全缺失只提交一次，确认复用不计新增提交，各入口一致。
5. 同步用户文档、架构、开发底线和完整测试映射；执行完整离线门禁并独立审查。
   验证：93/93 基线、compileall、pip check、Python 3.9 语法、锁定依赖、打包、结构、
   脱敏、生成物和 diff check 全部通过，无未解决阻塞发现后再进入人工验收。

### D08 Independent Review

- 首轮只读审查发现锁路径未拒绝符号链接/非普通文件（P2），以及 409/412 文档误称
  create-commit 调用为零（P3）；已返回实现模式分别补充失败关闭回归和修正文案。
- 修复后提交策略 70/70、恢复与进程 52/52、打包 13/13 和 93 脚本完整基线重新通过；
  compileall、pip check、Python 3.9 AST、锁定依赖签名、格式债务、凭证、二进制、
  未跟踪生成物和 diff check 通过。
- 第二轮只读审查无新的 P0/P1/P2/P3 发现，所有发现均已关闭，结论 `APPROVED`。
  该结论不代表人工验收，也不授权提交、合并、推送或任何真实 AtomGit 操作。

### D08 Non-Goals And Residual Risks

- 不为单文件、普通目录、`--no-resumable` 或旧版本已经产生但没有 D08 凭据的状态提供
  追溯防重；更改 `HF_HOME`、源目录、repo/revision/prefix/batch identity 或清理缓存后
  自动防重保证失效。
- 不新增强制覆盖/合并参数。冲突默认停止；维护者人工确认需要以本地覆盖时，可显式
  选择既有非 resumable 路径，但该操作不属于自动恢复。
- 服务端没有幂等键时，客户端不能消除“远端写入成功且本地持久介质同时永久损坏”的
  全部极端窗口；空分支没有 parent SHA 时并发保护较弱。
- 每个提交增加一次只读 revision 查询，这是防止重复与覆盖的接受成本；仍使用现有
  请求 timeout，不增加总时限或无限重试。
- 真实 AtomGit 的 `parent_commit`、409/412、空分支和不可变 revision 行为，Windows/
  Linux 进程锁及真实 Python 3.9 仍是实施交付时必须报告的未验证边界；任何真实写入
  验证需要单独授权。

### D08 Compatibility And Rollback

- 兼容变化仅发生在冲突 resumable 重跑：旧行为可能继续提交，新行为返回非零并禁止
  覆盖；公共参数、返回类型和非 resumable 行为不变。
- 新凭据只保护新版本创建的状态，不迁移旧 HF metadata。未知 schema 失败关闭，避免
  降级误判。
- 若实现回归，可整体回退 D08 单一实现提交；新凭据位于既有 AtomGit/HF cache 下，不
  修改源文件或凭证。旧版本会忽略凭据并失去防重保护，有未解决凭据时不得直接降级
  重跑；`atomgit cache clear` 只能在人工核对远端后作为最后手段。

### D08 Activation Status

- [x] 维护者接受 D08 最终方案并授权登记到本地开发 Issue。
- [x] 维护者单独授权激活 D08。
- [x] 本地任务分支已创建。
- [x] 红灯回归、实现、文档和开发底线已完成。
- [x] 专项、完整离线门禁和独立审查通过。
- [x] 维护者完成人工验收并授权适用的 Git/远程交付。

### D09 Objective And Evidence

让 resumable LFS 上传的每个 Flow 把真实速度、基线、低速窗口、替换次数、剩余字节、
阶段和有限趋势写入上传会话快照，使 `atomgit monitor upload status` 不再只有 Flow
表头。观测信息必须直接来自既有慢流协调器，不能从终端文字反推，也不能复制或改变
恢复策略。

当前 `UploadSession` 以 `flows=[]` 创建，只有通用字段更新和文字事件追加，没有 Flow
upsert。CLI 的 LFS observer 只把事件 `kind` 作为消息保存，其他结构化详情被丢弃；
`_SlowFlowCoordinator` 的速度、基线、低速和替换状态只保留在 `_states` 中，注册、
5 秒采样、30 秒窗口、重连验证、完成和失败均未形成完整观测状态。monitor renderer
虽会遍历 `flows`，但生产端从未填充该数组。

本方案依据当前源码、既有测试、`docs/features/upload-monitor.md` 和可执行开发底线形成，
未运行真实 AtomGit 上传。历史 R9 文本不是当前实现权威；实际源码与测试显示观测集成
只完成了快照/界面外壳和少量事件接线。

### D09 Accepted Behavior And State Contract

- 每个 coordinator 内首次注册一个 LFS 对象时建立匿名 Flow 关联；同一对象的连接替换、
  multipart 后续 part 和改善验证沿用该关联。最终会话显示使用 `Flow-01`、`Flow-02`
  等匿名编号；完整 OID、SHA、源路径和远端路径不得离开上传内部。
- Flow 注册后立即产生状态，尚无速度时显示 `--` 和“建立基线”；不能等到低速替换后
  才出现。文件列只允许使用现有规则生成的 basename 最后十个 Unicode 字符缩写，不
  保存完整源路径或远端路径。
- `_SlowFlowPayload` 每约 5 秒计算 `sample_speed` 和估计剩余字节，仅用于显示；每约
  30 秒继续调用既有 `observe_window`，更新 `window_speed`、自身/同伴基线、低速窗口、
  替换次数和决策解释。5 秒数据不得进入或改变慢流策略。
- Flow 阶段使用稳定内部状态并由 renderer 转换为中文：建立基线、稳定、疑似低速、
  等待替换、重连后验证、已恢复、自动替换已停用、完成、失败。注册、正式窗口、替换
  批准、replacement finished、改善成功/失败及 PUT 终态均必须更新最新状态。
- 展示趋势与策略 `state.speeds` 分离，只保存实际产生的最近 12 个正式窗口；策略在
  重连后重置或校准自身窗口时不得伪造、清空或改写用户看到的历史趋势。
- 采用“完整最新 `flow_state` 覆盖 + 低频 `flow_event` 追加”。普通 5 秒采样、重复
  稳定状态和普通剩余字节变化不进入事件队列；低速阶段变化、替换、改善、停用、完成
  和失败可进入最多 200 条的关键事件队列。
- `UploadSession` 按匿名关联覆盖 Flow，而不是追加重复行；从最新状态幂等计算
  `active_flows`、`peak_flows`、`replacement_total`、`improvement_total` 和
  `disabled_total`。重复或迟到的相同状态不能膨胀累计值。
- 协调器锁内只复制待发布的普通数据，实际 observer 调用在锁外执行。callback 异常、
  字段错误、序列化失败、快照不可写或 monitor 崩溃均不得改变上传决策、重试、结果或
  CLI 退出码。
- Flow 状态和事件只接受白名单字段、固定状态/原因码及有界安全数值；不得包含 token、
  URL、请求头、响应正文、异常原文、源/远端路径、完整 OID 或可用于重放请求的内容。
- D09 只定义状态生产、归并、持久化字段和 Flow 行展示。子进程到父进程的可靠传递由
  已接受的 D10 合同实现，批次/文件进度由 D11 决定；D09/D10 必须联合交付，不得只
  交付 D09 或提前声称独立 monitor 在 `fork`、`spawn`、`forkserver` 下均已修复。

### D09 Implementation Scope

1. 在 `src/atomgit/adapters/lfs/service.py` 扩展既有 `_SlowFlowState` 和协调器 observer：
   增加匿名关联、5 秒显示采样、独立 12 窗口趋势、阶段/决策状态及成功/失败终态；复用
   既有速度和恢复事实，不新增恢复算法或生产模块。
2. 在 `src/atomgit/infrastructure/upload_observe.py` 为 `UploadSession` 增加单一结构化
   观测入口，严格验证白名单并用新列表/字典覆盖 Flow 状态，幂等维护会话计数；保留
   现有原子快照、权限、1 秒限频、2 秒 heartbeat 和旧快照兼容。
3. 仅补齐 Flow 必需展示：文件缩写、5 秒/30 秒速度、相对基线、低速/替换计数、趋势
   和阶段。D14 的时间格式、D15 的刷新方式以及其他 monitor UX 不在本次修改范围。
4. `src/atomgit/interfaces/cli/commands/transfers.py` 的最终结构化接线必须服从后续已接受
   的 D10 数据合同，不能继续用只传 `kind` 的 lambda，也不能先提交一个仅适用于
   `fork` 的临时实现。
5. 扩展既有 `tests/test_lfs_slow_flow_recovery.py` 和
   `tests/test_upload_observability.py`；更新开发底线及最小权威文档。不新增依赖、公开
   命令/参数、SDK 签名、生产模块或测试脚本。

### D09 Affected Capability IDs

`UPLOAD-OBSERVABILITY`、`UPLOAD-LFS-RECOVERY`、`UPLOAD-RESUMABLE`、
`ERROR-REDACTION`、`PORTABILITY` 和 `FLOOR-REGISTRY`。

### D09 Protected Existing Invariants

- 现有 30 秒正式窗口、自身/同伴稳定基线、连续三次低速、收益检查、整体降速探针、
  `2/8` 秒首次抖动、`60/180` 秒冷却、改善要求和每对象最多三次替换完全不变。
- basic PUT 从对象起点重传、multipart 保留已确认 part、源文件身份检查、LFS Batch
  回退、异常传播和上传成功/失败判断不得退化。
- CLI、原生 SDK 和历史 API 的命令、参数、签名、返回值、错误层次、model/dataset、
  revision、batch 和 timeout 行为保持兼容；普通及非 resumable 上传不产生虚假 Flow。
- observer、publisher、monitor 或快照故障不阻塞上传，不触发或禁止连接替换，不改变
  错误与退出码；全局 callback 在成功、失败和取消后仍须恢复。
- 现有快照目录 `0700`、文件 `0600`、同目录临时文件和 `os.replace` 原子更新保持；
  旧 v1 空 Flow 快照仍可读取，cache clear 边界不变。
- `huggingface-hub==1.1.7`、`datasets==4.4.1`、Python >=3.9、七目录架构、source/
  editable/wheel/sdist、93 个测试脚本及所有既有能力/不变量不得退化。

### D09 New Or Changed Invariants

- `UPO-002`：每个 resumable LFS 对象从注册到终态拥有稳定匿名、可覆盖且安全脱敏的
  Flow 状态；同一对象重连不产生重复行。
- `UPO-003`：约 5 秒速度只用于显示，约 30 秒正式窗口和独立 12 窗口趋势来自真实
  payload 消费；新增观测对既有慢流策略决策为零影响。
- `UPO-004`：结构化状态、会话计数和关键事件有界且幂等；任何 observer、归并或
  持久化失败都不影响上传结果或泄露敏感内容。
- 实施时预计将当前 28 个能力、127 条不变量、93 个测试脚本更新为 28 个能力、130 条
  不变量、93 个测试脚本；实际数字必须以实施时 Git 和可执行登记册为准，不得预先
  声称登记已经完成。

### D09 Focused Tests And Evidence

| 场景 | 必须证明的结果 |
|---|---|
| Flow 注册但尚无采样 | 立即出现一个匿名 Flow；速度为 `--`，阶段为建立基线 |
| 受控时钟推进约 5 秒 | `sample_speed` 和剩余字节更新；慢流策略状态和决定不变 |
| 连续 30 秒正式窗口 | window speed、基线、peer baseline、低速窗口和真实趋势一致 |
| 同一对象触发替换、重连和改善 | Flow ID 不变；替换计数、阶段、事件和改善汇总只增加一次 |
| 改善不足或次数耗尽 | 阶段为停用，原因准确，不再触发额外替换或重复计数 |
| basic/multipart 成功与失败 | 写入完成/失败终态，active count 收敛且现有传输语义不变 |
| 超过 12 个窗口、200 个事件或重复状态 | 趋势/事件限长；最新状态保留且累计值不膨胀 |
| callback 抛错、畸形/越界/敏感 payload、快照不可写 | 状态被安全丢弃，上传决定、结果、退出码及脱敏不变 |
| 旧空 Flow 快照、普通和非 resumable 上传 | 继续兼容读取；不制造精确速度或虚假 Flow |

优先扩展 `tests/test_lfs_slow_flow_recovery.py` 与
`tests/test_upload_observability.py`，不创建新测试脚本。红灯必须通过真实
`_SlowFlowCoordinator -> structured observer -> UploadSession -> snapshot/render`
边界证明旧实现保持 `flows=[]` 或缺少生命周期/速度状态；不能只断言一个新 helper。

实施完成后在 `atomgit_cli` conda 环境执行：

```bash
python tests/test_lfs_slow_flow_recovery.py
python tests/test_upload_observability.py
python tests/test_upload_resumable.py
python tests/test_development_floor.py
python tests/test_structure_guard.py
python tests/run_cli_baseline.py
python -m compileall -q .
python -m pip check
git diff --check
```

完整基线和静态门禁必须在最后一次修正后重跑并记录；真实 AtomGit 上传不是 D09 本地
状态合同的必需证据，不得以离线 mock 宣称远端已验证。

### D09 Implementation Phases And Acceptance

1. 在 D10 方案也获接受且维护者单独激活后，冻结现有 observer、慢流状态、上传入口和
   开发底线，添加 D09 红灯。验证：旧实现因 Flow 空缺或状态不完整失败，既有断言通过。
2. 实现协调器结构化状态、5 秒显示采样、独立趋势和完整生命周期。验证：慢流恢复专项
   全部通过，新增观测前后的 decision、delay、replacement count 完全相同。
3. 实现 UploadSession 白名单归并、幂等计数、限长快照和 Flow 展示。验证：旧/新快照、
   重复更新、终态、异常和脱敏专项通过。
4. 按已接受的 D10 合同接入上传子进程与父进程；在此之前 D09 阶段只能记为本地组件
   完成，不能进入交付验收。验证：实际父进程持有唯一会话状态并写出完整 Flow 快照。
5. 同步 `tests/development_floor_contract.py`、`docs/features/upload-monitor.md`、
   `docs/development_floor.md` 和必要架构说明；运行完整离线门禁并按 `.ai/REVIEW.md`
   独立审查。无未解决发现后才进入人工验收。

### D09 Non-Goals And Residual Risks

- 不处理 D10 跨进程协议、D11 批次/文件进度、D12 heartbeat、D13 自动退出、D14 时间
  显示、D15 刷屏、D16 仓库类型警告或 D17 完整真实跨进程测试范围。
- 不提供下载监控、暂停/取消上传、Web UI、常驻 daemon、原始 debug log 或新的 TUI
  依赖；不改变上传恢复策略或远端仓库。
- D10 接线前，在 `fork` 下继承 callback 仍可能写父进程副本，在 `spawn` 下可能完全
  收不到状态；这是已知阻塞依赖，不能用 D09 单元测试掩盖。
- 真实网络节奏、Windows/Linux 多进程调度和真实 Python 3.9 解释器仍是后续验收需明确
  报告的边界；任何真实 AtomGit 写入必须获得单独授权。

### D09 Compatibility And Rollback

- 不改变公开 CLI/SDK/API；快照继续使用 v1，新增行为主要是填充已有 Flow 字段。旧
  快照缺失 Flow 或新增字段时继续按 `--`/空表降级，未知字段被忽略。
- 不迁移 HF metadata、上传投影、源文件或远端数据。若实现回归，可整体回退 D09/D10
  对应实现提交；新快照仍是普通 JSON，旧版本会忽略额外字段。
- 必要时可使用既有 `atomgit cache clear` 清理观测快照，但不能触及源文件、续传元数据
  或远端内容。

### D09 Activation Status

- [x] 维护者接受 D09 完整方案并授权登记到本地开发 Issue。
- [x] D10 跨进程数据合同已讨论并接受。
- [x] 维护者单独授权激活 D09 实施。
- [x] 本地任务分支已创建。
- [x] 红灯、实现、文档和开发底线已完成。
- [x] 专项、完整离线门禁和独立审查通过。
- [x] 维护者完成人工验收并授权适用的 Git/远程交付。

### D10 Objective And Evidence

在 resumable 上传子进程与 CLI 父进程之间建立跨 `fork`、`spawn` 和
`forkserver` 同义的结构化观测数据合同，使 D09 的 Flow 状态只由父进程
归并并写入 JSON 快照，同时保证观测拥塞、字段错误或 monitor 故障不影响
上传结果、退出码、取消和断点元数据。

当前 CLI 在父进程创建 `UploadSession` 和后台 `SnapshotPublisher`，然后
`adapters/upload/resumable.py` 另建子进程执行 HF worker。
`set_upload_observer(lambda ...)` 只是进程内全局回调：`fork` 会让子进程继承
`UploadSession` 副本并直接写快照，父进程发布器又可用旧副本覆盖；
`spawn` / `forkserver` 不继承该回调，状态可完全丢失。父进程当前在
`process.join()` 中阻塞，只有一条上传结果队列，没有运行期间的状态通道。
monitor 只读 JSON 快照，无法直接访问上传子进程或修复该缺口。

证据来自当前源码、`tests/test_upload_observability.py`、
`tests/test_resumable_recovery.py`、`tests/test_upload_resumable.py`、
`tests/test_lfs_slow_flow_recovery.py` 和 `docs/features/upload-monitor.md` 的只读核对；
未运行真实 AtomGit 上传。

### D10 Accepted Transport And Ownership Contract

- 父进程是 `UploadSession`、会话 Flow 映射和 JSON 快照的唯一写入者。
  子进程不得持有会话对象、publisher 线程、快照路径或父进程 callback。
- 保留现有独立 `result_queue` 传递必须可靠到达的上传成功/失败结果；
  另建 `multiprocessing.Queue(maxsize=256)` 作为 `observation_queue`。
  两条队列不混用，状态洪水不得阻塞或改写结果 envelope。
- 观测队列只传 UTF-8 JSON bytes。子进程使用 `ensure_ascii=False`、
  `allow_nan=False` 和紧凑分隔符序列化；单条消息最大 16 KiB。序列化失败、
  消息超限、队列满或队列关闭时丢弃当前观测消息，不等待、不重试。
- 内部 envelope 固定为 v1，且只允许 `version`、`type`、`sequence`、
  `flow_key` 和 `payload`。`version` 必须为 `1`；`type` 只能为
  `flow_state` 或 `flow_event`；`sequence` 是子进程流中严格递增的正整数；
  `flow_key` 是 coordinator 内部匿名正整数，不得使用 OID、SHA 或路径。
- `flow_state.payload` 只允许 D09 的安全字段：最多十个 Unicode 字符的
  `file_abbrev`，`basic` / `multipart` 传输类型，有界大小与剩余字节，
  有限非负速度/基线，`0..3` 低速窗口和替换次数，固定阶段/决策码，
  以及最多 12 个有限正式窗口速度。
- `flow_event.payload` 只允许固定事件码及必要安全数值：进入低速观察、
  批准替换、开始新连接、改善通过/失败、自动替换停用与 Flow 完成/失败。
  普通 5 秒样本和重复稳定状态不进入事件历史。
- envelope 不携带 session ID、仓库名、源/远程路径、完整文件名、OID、
  SHA、token、URL、请求头、响应正文、异常原文或可重放请求的信息。
  墙上时间由父进程接收合法消息时生成，子进程不传时间戳。
- 每次 `_execute_resumable_upload_process` 调用由父进程建立私有
  `source_id`，不持久化到快照。父进程将 `(source_id, flow_key)` 映射为会话内
  唯一的 `Flow-01`、`Flow-02` 等编号；同一 coordinator 中的 basic 重连、
  multipart 后续 part 和改善验证沿用同一 `flow_key`。
- 父进程按 `(source_id, sequence)` 拒绝重复或迟到消息。非法 JSON、未知
  版本/类型、多余字段、越界数值或敏感 payload 整条丢弃，不创建 Flow、
  不增加计数，也不更新会话时间。
- 子进程启动后首先清除可能由 `fork` 继承的父进程 observer，再把
  D09 coordinator 的结构化输出写入显式传入的观测队列。coordinator 锁内只
  复制待发布数据，实际 callback 和序列化/入队在锁外执行。
- 父进程用约 100 ms 的 `process.join(timeout)` 与队列排空循环取代一次
  无期限 `join()`。子进程退出后，先排空已成功入队的消息，再读取和
  验证原有 result envelope。
- 父进程根据已确认的成功、失败、无结果崩溃或 Ctrl+C，用固定安全
  原因将当前 source 中仍活跃的已知 Flow 收敛为完成、失败或中断。不为
  从未注册的 Flow 伪造记录，不改变原有上传结果分类、异常或 CLI 退出码。
- 队列满或子进程被 `SIGKILL` / `os._exit` 截断时，允许丢失未成功入队的
  中间显示样本。`flow_state` 是完整覆盖值，后续样本可自愈；父进程对已知
  Flow 的终态收敛和独立可靠的上传结果不受影响。

### D10 Implementation Scope

1. 在 `src/atomgit/adapters/upload/resumable.py` 增加最小的 v1 JSON envelope
   编解码、有界非阻塞子进程发送器、独立观测队列和父进程排空循环。
   `_run_resumable_upload` 只在末尾增加可选观测队列参数，保持既有调用和补丁接缝。
2. 在 `src/atomgit/adapters/lfs/service.py` 与 D09 一起产生匿名、白名单、完整
   覆盖的 Flow 状态和低频关键事件；不在该模块写 JSON 快照或实现跨进程存储。
3. 在 `src/atomgit/infrastructure/upload_observe.py` 为 `UploadSession` 增加单一
   结构化入口，完成 envelope/payload 严格验证、source/序号去重、会话 Flow ID
   映射、完整状态覆盖和幂等累计。继续使用新列表/字典提交快照，不让
   publisher 线程观察到原地修改的共享结构。
4. 在 `src/atomgit/interfaces/cli/commands/transfers.py` 将只保存 `kind` 的 lambda
   改为完整结构化入口，并保持成功、失败、取消后的 observer 恢复和会话关闭。
5. 与 D09 共同更新 `tests/development_floor_contract.py`、
   `docs/features/upload-monitor.md`、`docs/development_floor.md` 和必要的架构说明。
   不新增生产模块、外部依赖、公开命令/参数或测试脚本。

### D10 Affected Capability IDs

`UPLOAD-OBSERVABILITY`、`UPLOAD-LFS-RECOVERY`、`UPLOAD-RESUMABLE`、
`ERROR-REDACTION`、`PORTABILITY`、`ARCHITECTURE` 和 `FLOOR-REGISTRY`。

### D10 Protected Existing Invariants

- D09 的 5 秒显示采样、30 秒正式窗口、独立趋势、阶段、白名单和幂等归并
  合同保持；新传输通道不改变慢流判断、替换次数、等待、改善要求或结果。
- 子进程必须继续传回一个经严格验证的成功或失败 result envelope；空结果、
  非法结果、崩溃和成功后异常退出仍必须失败，不得因观测消息误报成功。
- Ctrl+C 仍停止本次上传并通过现有 terminate/kill/join 路径回收子进程；
  观测队列和 callback 不得吞掉 `KeyboardInterrupt`。
- D05–D08 的 pointer 确认、错误分类、已创建/未确认状态、私有待对账凭据、
  `parent_commit` 并发保护和无重复远程写入保持。
- CLI、原生 SDK 和历史 API 的公开命令、参数、签名、返回值、错误层次、
  model/dataset、revision、batch 和 timeout 行为保持；普通及非 resumable 上传
  不生成虚假 Flow。
- 快照目录 `0700`、文件 `0600`、同目录临时文件与 `os.replace` 原子替换、
  1 秒写入限频、2 秒 heartbeat、旧 v1 快照读取和 cache clear 边界不退化。
- `huggingface-hub==1.1.7`、`datasets==4.4.1`、Python >=3.9、七目录架构、
  source/editable/wheel/sdist、93 个测试脚本及全部既有能力/不变量不得退化。

### D10 New Or Changed Invariants

- `UPO-005`：resumable 观测使用显式、版本化、脱敏、有界且非阻塞的子进程
  到父进程通道；父进程是会话和快照的唯一写入者，观测故障不影响上传结果。
- `PORT-009`：`fork`、`spawn` 和可用时的 `forkserver` 均通过同一显式数据
  合同向父进程传递同义状态；不依赖继承 callback 或子进程直接写快照。
- D09/D10 联合实施时预计将 28 个能力、127 条不变量、93 个测试脚本更新为
  28 个能力、132 条不变量、93 个测试脚本。实际数字必须以实施时 Git 和
  可执行登记册为准，不得预先声称登记已完成。

### D10 Focused Tests And Evidence

| 场景 | 必须证明的结果 |
|---|---|
| `fork` 子进程发送状态 | 不调用继承的会话 callback，只由父进程归并和写快照 |
| `spawn` / `forkserver` 受控发送 | 不依赖内存继承，父进程收到同义、同序消息 |
| 同一 Flow 重连、multipart 后续 part | `flow_key` 和会话 Flow ID 不变，不增加重复行 |
| 不同批次或子进程 source 复用相同 `flow_key` | 分配不同会话 Flow ID，状态不相互覆盖 |
| 重复/迟到序号 | 旧状态被丢弃，趋势、累计值和终态不回退 |
| 非法 JSON、未知版本/类型、多余/越界/敏感字段 | 整条安全丢弃，不建 Flow、不写快照、不泄露信息 |
| 单条超过 16 KiB 或队列满 | 发送立即返回；中间样本可丢弃，上传继续 |
| 观测队列洪水 | 独立 result 仍能送达并准确分类成功/失败 |
| callback 抛错、publisher 或快照不可写 | 观测降级，上传决策、结果和退出码不变 |
| 成功、报告失败、无结果、崩溃、成功后崩溃、Ctrl+C | 已知活跃 Flow 安全收敛，既有结果分类和子进程回收不变 |
| 旧 v1 空 Flow 快照、普通/非 resumable 上传 | 继续兼容，不制造虚假 Flow |

优先扩展 `tests/test_upload_observability.py`、`tests/test_resumable_recovery.py`、
`tests/test_upload_resumable.py` 和 `tests/test_lfs_slow_flow_recovery.py`，必要时同步
`tests/test_upload_batching.py`、`tests/test_development_floor.py` 和
`tests/test_structure_guard.py`，但不新增测试脚本。D10 红灯必须直接证明旧
实现的 callback 继承/丢失或父进程覆盖问题，不能只断言一个新 helper。

实施完成后在 `atomgit_cli` conda 环境执行：

```bash
python tests/test_lfs_slow_flow_recovery.py
python tests/test_upload_observability.py
python tests/test_resumable_recovery.py
python tests/test_upload_resumable.py
python tests/test_upload_batching.py
python tests/test_development_floor.py
python tests/test_structure_guard.py
python tests/run_cli_baseline.py
python -m compileall -q .
python -m pip check
git diff --check
```

最后一次修正后必须重跑完整离线基线和静态门禁，并按 `.ai/REVIEW.md`
执行独立审查。真实 AtomGit 写入不是 D09/D10 本地状态合同的必需证据，
未获授权时不得执行或用离线 mock 代替声称。

### D10 Implementation Phases And Acceptance

1. 维护者单独激活后，从 `yuto@75094a7` 创建本地 D09/D10 任务分支，
   冻结当前源码、进程结果合同、D09 状态字段和发展底线，先添加红灯。
   验证：旧实现在至少一个真实父子进程边界上失败，既有断言继续通过。
2. 完成 D09 coordinator 结构化状态、5 秒显示样本、30 秒正式窗口、独立
   趋势和完整生命周期。验证：慢流恢复专项通过，新增观测前后的决策、
   delay 和 replacement count 完全一致。
3. 实现 D10 v1 JSON 消息、非阻塞子进程发送、独立有界队列与父进程
   排空循环。验证：可用启动方式同义，洪水不阻塞 result，失败/崩溃/
   取消的结果和清理不变。
4. 实现 `UploadSession` 严格验证、序号去重、会话 Flow 映射、幂等计数和终态
   收敛，再完成 CLI 结构化接线。验证：父进程持有唯一会话并写出完整
   Flow 快照，迟到/非法/敏感消息不改变状态。
5. 同步用户文档、架构、开发底线及 D09/D10 证据；执行专项、完整离线门禁和
   独立审查。无未解决发现后才进入人工验收；人工验收不自动授权提交或远程操作。

验收必须同时满足：父进程是唯一快照写入者；三种可用启动方式使用同一数据
合同；同一 Flow 重连不重复；不同 source 不冲突；迟到/非法/超限消息失败关闭；
观测洪水、callback、publisher、快照或 monitor 故障不影响上传；崩溃/取消后已知 Flow
收敛且子进程回收；脱敏合同、公开兼容、完整基线和独立审查全部通过。

### D10 Non-Goals And Residual Risks

- 不更新 D11 的批次/文件进度，不处理 D12–D17 的 heartbeat、monitor 退出、
  时间格式、刷屏、仓库类型警告和完整真实命令链路。D09/D10 实施后仍不得
  声称整个 monitor 问题已修复。
- 不提供下载监控、暂停/取消上传、Web UI、常驻 daemon、socket、共享内存、
  外部消息系统或新 TUI 依赖。
- 观测是有界 best-effort；队列满或进程被 `SIGKILL` / `os._exit` 截断时，
  最后一个未成功入队的显示样本可丢失。后续完整状态可自愈，父进程只能对已知
  Flow 收敛终态，不能补造从未成功注册的 Flow 历史。
- 当前生产启动方式选择保持不变；D10 保证数据合同不依赖内存继承，
  但 Windows/Linux 真实调度、真实 Python 3.9 和长时间网络节奏仍是交付时必须报告的
  未验证边界。D17 仍负责真实 CLI 上传子进程、JSON 快照和独立 monitor
  命令的端到端覆盖。
- 真实 AtomGit 写入、PR、标签、发布、提交、合并和推送未授权。

### D10 Compatibility And Rollback

- 不改公开 CLI/SDK/API；快照继续使用 v1，旧快照缺少 Flow 或新字段时按
  `--` / 空表降级，未知字段被忽略。
- `_run_resumable_upload` 的内部补丁接缝保留；观测队列参数仅能作为末尾可选值增加，
  原有位置参数调用不失效。result envelope 的字段、分类和验证保持。
- 无持久数据迁移；新版本运行后自然写出包含 Flow 的 v1 快照，不修改 HF metadata、
  上传投影、源文件或远程数据。
- 若实现回归，必须整体回退 D09/D10 实现提交，不得只保留子进程状态生产或
  只回退跨进程通道。新快照仍是普通 JSON，旧版本可忽略新字段。
- 必要时可用既有 `atomgit cache clear` 清理观测快照，但不得删除源文件、
  resumable 元数据、D08 待对账凭据或远程内容。

### D10 Activation Status

- [x] 维护者接受 D10 完整方案并授权登记到本地开发 Issue。
- [x] 维护者单独授权激活 D09/D10 联合实施。
- [x] 本地任务分支已创建。
- [x] 红灯、D09 状态生产、D10 跨进程通道、文档和开发底线已完成。
- [x] 专项、完整离线门禁和独立审查通过。
- [x] 维护者完成人工验收并授权适用的 Git/远程交付。

### D09/D10 Independent Review

- Procedure: 按 `.ai/REVIEW.md` 以独立审查角色核对任务合同、完整源码和测试差异、
  用户及 AI 文档、锁定依赖版本/签名、最终离线门禁、凭证模式、二进制和生成物状态。
- Findings: 首轮 P2 的观测队列创建/清理异常隔离已修复并增加回归；续接复核发现的
  P3 陈旧当前状态和 127 条旧登记计数已校正。最终复核无开放 P0/P1/P2/P3 发现。
- Missing evidence: 未执行真实 AtomGit、Windows/Linux、独立 Python 3.9 解释器或
  D17 真实 CLI/快照/monitor 端到端链路；这些均为已记录的范围外或后续验证边界。
- Verdict: `APPROVED`。该结论不授权提交、合并、推送、Issue 关闭、发布或远程写入。

### D11 Objective And Evidence

修复 resumable 目录上传会话的批次状态长期停留在 `0/N`：上传服务在父进程完成
实际文件选择并进入每个外层批次时，直接把当前批次和累计已确认文件数更新到父进程
拥有的 `UploadSession`，使 `atomgit monitor upload status --list` 和详细监控反映
真实外层批次，同时保证任何观测故障都不改变上传结果。

当前 `interfaces/cli/commands/transfers.py` 只在会话创建时按 CLI 文件统计写一次
`batch="0/N"`；`adapters/upload/service.py` 随后才应用真实文件选择并计算批次，且在
批次开始、成功和失败处已经维护 `batch_number`、`batch_count`、`total_files` 与
`completed_files`，但只打印日志。`UploadSession.update()` 已能刷新父进程状态并提交
最新快照；历史 `upload_directory()` 签名还保留未使用的 `progress_callback`。
因此根因位于父进程批次生命周期没有回写会话，不需要解析 stdout，也不需要修改
D10 的子进程 JSON 观测协议。

证据来自当前源码、`tests/test_upload_batching.py`、
`tests/test_upload_observability.py`、`tests/test_upload_progress.py`、
`tests/test_resumable_recovery.py`、开发底线和 `docs/features/upload-monitor.md` 的
只读核对；本次方案登记没有运行测试或真实 AtomGit 上传。D09/D10 最近一次已记录
完整离线基线为 93/93，但不能替代 D11 实施后的红灯、专项和完整复验。

### D11 Accepted State And Ownership Contract

- `batch` 继续使用现有 `i/N` 字符串，唯一含义是“当前外层批次/总批次”；不新增
  `completed_batches`、批次阶段或快照版本字段。`files_done` 只表示远端已确认完成
  文件，不计入仅哈希、仅 LFS 预上传或本地待确认的文件。
- CLI 创建 resumable 会话时先写 `0/N`、`files_done=0`；上传服务应用忽略规则完成
  实际文件选择后，再以真实 `files_total` 和 `batch_count` 提交一次 `0/N`，纠正
  CLI 预估与实际选择之间可能存在的差异。
- 第 `i` 个外层批次开始即提交 `i/N` 和此前累计确认数；成功后使用现有
  `completed_files` 提交累计确认数。最后一批成功后的状态必须为 `N/N` 且
  `files_done == files_total`。
- 批次失败时先复用现有断点元数据、续传跳过和远端确认结果计算
  `confirmed_in_batch`，再提交失败批次 `i/N` 及累计确认数。仓库、revision、权限等
  批次开始前失败保持 `0/N`，不能伪造已开始或已完成进度。
- 内部提交降批、LFS preupload 重试、远端对账、连接替换和同一外层批次内暂态不
  增加批次号。单批执行期间 `files_done` 可以保持上一次确认值；当前批次和 D09 Flow
  状态共同表示任务仍在活动。
- 父进程继续是 `UploadSession`、批次状态和快照的唯一写入者。批次更新使用既有
  `progress_callback` 在父进程内直达会话，不进入 D10 的 `flow_state` / `flow_event`
  envelope、256 条 observation queue 或独立 result queue。
- callback 每次只收到完整安全字典：`batch`、`files_total`、`files_done`。不得携带
  session ID、仓库名、源/远程路径、文件名、OID、SHA、token、URL、请求头、响应正文、
  异常原文或任何可重放请求信息。
- callback 为可选 best-effort 观测边界。普通 `Exception` 被隔离，不改变上传返回、
  异常分类、CLI 退出码、断点元数据或远端写入；`KeyboardInterrupt` / `SystemExit`
  继续遵循现有取消和退出语义。
- 既有 publisher 允许合并短时间内的中间状态，但内存中的最新状态和 `close()` 最终
  刷新必须正确。旧 v1 快照缺少文件字段时继续可读，不显示伪造的 `0/0`。

### D11 Implementation Scope

1. 在 `src/atomgit/interfaces/cli/commands/transfers.py` 的 resumable 会话初始状态补充
   `files_done=0`，并通过一个 CLI 私有参数把安全进度字典转换为
   `observe_session.update(**progress)`；现有成功/失败终态和 observer 恢复逻辑保持。
2. 在 `src/atomgit/interfaces/cli/runner.py` 的 `run()` 中先弹出私有批次 callback，
   注入 `_CliTransferPort`，再调用公开 native SDK 方法；只有目录 resumable 路径把
   callback 交给历史 `upload_directory(progress_callback=...)`。不修改
   `UploadRequest`、`TransferPort` 或 `AtomGitClient.upload_folder()` 公开合同。
3. 在 `src/atomgit/adapters/upload/service.py` 增加一个最小的安全通知 helper，只在
   resumable 实际计划、外层批次开始、成功和失败边界发送完整进度字典。失败通知
   必须位于现有 `completed_files` 核对完成之后；普通上传分支不新增监控行为。
4. 在 `src/atomgit/infrastructure/upload_observe.py` 的详细渲染中，仅当
   `files_total` 存在时显示“已确认文件 x/y”。`render_list()` 已读取 `batch`，无需
   新列或 schema 变化；`UploadSession.update()` 和字段白名单已满足本 Issue，不新增
   session 类型或存储层。
5. 更新 `tests/test_upload_batching.py`、`tests/test_upload_observability.py`、
   `tests/development_floor_contract.py`、`.ai/DEVELOPMENT_FLOOR.md`、
   `docs/features/upload-monitor.md`、`docs/development_floor.md` 和必要的
   `docs/architecture.md` 说明。不新增生产模块、测试脚本、依赖、CLI 参数或 SDK 参数。

### D11 Affected Capability IDs

`UPLOAD-OBSERVABILITY`、`UPLOAD-RESUMABLE`、`CLI-DISPATCH`、`ARCHITECTURE`、
`ERROR-REDACTION`、`RUNTIME`、`PORTABILITY`、`PACKAGING` 和 `FLOOR-REGISTRY`。

### D11 Protected Existing Invariants

- `UPO-001`–`UPO-005`：快照继续只读、有界、原子、脱敏；父进程仍是唯一会话写入者；
  D09 Flow 状态和 D10 跨进程观测/结果隔离不退化。
- `RESUMEUP-002`、`RESUMEUP-005`、`RESUMEUP-006`：失败不误报成功，断点详情、待对账
  提交、`parent_commit` 并发保护和现有累计确认口径保持。
- `RUNTIME-002`：HF timeout、progress 和其他进程全局状态在所有出口恢复；批次 callback
  不建立新的可泄漏全局状态。
- `REDACT-001`：快照、callback、CLI 输出和测试中不出现 token、URL、OID、路径、响应
  正文或异常原文。
- `ARCH-001`、`ARCH-003`：公开 CLI/native SDK 继续通过共享 usecase，私有 observer
  在 CLI adapter 边界消费，不扩展公开请求或结果。
- `PORT-001`：Python >=3.9、Windows/POSIX 和当前多进程启动方式继续得到同义上传结果；
  callback 不被序列化或传入子进程。
- `PKG-002`：既有格式债务数量不增长；修改旧债务文件后只同步精确摘要。
- 公开 Click schema、历史 `upload_directory` 签名、native/legacy SDK 返回与异常、
  普通目录上传、单文件上传、model/dataset、revision、timeout 和 batch 行为不变。
- 当前 28 个能力、132 条不变量、93 个离线脚本在实施前保持基线；不得删减或弱化
  既有登记来通过 D11。

### D11 New Or Changed Invariants

- `UPO-006`：resumable 外层批次在实际计划、开始、成功和失败时更新父进程拥有的
  当前批次与累计已确认文件数；callback、publisher 或快照失败不得改变上传结果。
- 实施完成后预计保持 28 个能力和 93 个测试脚本，不变量从 132 增至 133。实际计数
  必须以实施时 Git 和可执行登记册为准，方案登记不能预先声称新增不变量已实现。

### D11 Focused Tests And Evidence

| 场景 | 必须证明的结果 |
|---|---|
| 21 个文件、20 文件批次，两批成功 | callback 顺序为实际 `0/2`、`1/2`、第一批完成 20、`2/2`、最终完成 21 |
| 第二批失败 | 最终保留失败批次 `2/N` 和第一批累计确认数，不进入下一批 |
| 第一批部分确认后失败 | 使用现有断点/远端核对后的确认数，不把待确认文件计入完成 |
| 续传全部或部分跳过 | 跳过文件在现有成功口径下计入最终确认完成数，不重复提交 |
| 批次开始前验证失败 | 会话终态为 failed，批次仍为 `0/N`，文件完成数不增加 |
| callback、publisher 或快照写入抛错 | 上传结果、错误分类、退出码、断点元数据和远端调用次数不变 |
| CLI→runner→API→UploadSession→JSON | 私有 callback 完整贯通，最终 JSON、详细渲染和 `--list` 使用真实批次 |
| 旧 v1 快照缺少文件字段 | 正常加载，不崩溃、不显示伪造 `0/0` |
| 普通目录、单文件和 native SDK | 不创建批次会话，不增加公开参数或改变结果 |
| 敏感测试载荷 | callback 和快照只保留三个安全字段，不泄露路径、OID、URL 或 token |

先扩展 `tests/test_upload_batching.py`，要求旧实现因完全不调用
`progress_callback` 而红灯；不得用只测试新 helper 的方式代替真实批次循环证据。
再扩展 `tests/test_upload_observability.py` 覆盖真实 CLI 私有接线、会话 JSON、详细
渲染、列表、旧快照和脱敏。复验 `tests/test_upload_progress.py`、
`tests/test_resumable_recovery.py`、`tests/test_upload_domain_ownership.py`、
`tests/test_architecture_parity.py`、`tests/test_cli_error_redaction.py` 和
`tests/test_development_floor.py`。不新增测试脚本，因此无需扩大 CLI baseline 的
脚本 inventory。

实施完成后在 `atomgit_cli` conda 环境运行：

```bash
python tests/test_upload_batching.py
python tests/test_upload_observability.py
python tests/test_upload_progress.py
python tests/test_resumable_recovery.py
python tests/test_upload_domain_ownership.py
python tests/test_architecture_parity.py
python tests/test_cli_error_redaction.py
python tests/test_development_floor.py
python tests/run_cli_baseline.py
python -m compileall -q .
python -m pip check
git diff --check
```

最后一次代码、测试或文档修正后必须重跑完整离线基线和静态门禁，并按
`.ai/REVIEW.md` 执行独立审查。真实 AtomGit 上传不是本地批次状态合同的必需证据，
未获授权时不得执行或以 mock 结果声称远程验证。

### D11 Implementation Phases And Acceptance

1. 维护者单独激活后，从最新 `yuto` 创建本地 `codex/d11-upload-batch-progress`
   任务分支；冻结 D09/D10、公开签名、批次统计和开发底线，在既有测试中添加红灯。
   验证：旧实现只因没有批次 callback 回写而失败，既有断言继续通过。
2. 接通 CLI 私有 callback、runner adapter 和父进程上传服务四个生命周期边界。
   验证：两批成功、第二批失败、部分确认、续传跳过、前置失败和 callback 异常专项
   全部通过，普通上传与 native SDK 不变。
3. 更新详细渲染、用户说明、架构和 `UPO-006` 开发底线登记。验证：旧快照降级、
   `--list`、详细文件计数、脱敏、结构和登记合同通过，预计计数为 28/133/93。
4. 运行完整离线门禁、差异/凭证/生成物检查和独立审查。验证：实现、测试和文档一致，
   原有五份未提交 `.ai` 规范修改未混入任务差异，无未解决 P0/P1/P2/P3 发现，再进入
   人工验收。

验收必须同时满足：第一批开始后不再显示 `0/N`；列表和详细视图显示实际当前外层
批次；成功最终为 `N/N` 和全部文件确认；失败保留实际失败批次及核对后的累计确认数；
前置失败不伪造进度；callback/持久化故障不影响上传；D09/D10、普通上传、SDK、公开
参数和快照 v1 不退化；完整基线、静态门禁、开发底线和独立审查全部通过。

### D11 Non-Goals And Residual Risks

- 不处理 D12 heartbeat/更新时间、D13 自动退出、D14 时间格式、D15 刷屏、D16 仓库
  类型警告、D17 真实 CLI 跨进程端到端覆盖或 D18 历史文档矛盾。
- 不提供单个外层批次内部的逐文件实时确认，不填充精确 `bytes_done`，不为普通目录
  或单文件上传新增 monitor，不提供下载监控、暂停/取消、daemon、socket 或新 TUI。
- 单批最多 20 个文件的执行期间，`files_done` 可能保持上一确认值；`batch=i/N` 与
  D09 Flow 速度/阶段用于表示仍在活动。若未来必须显示批次内提交进度，应另行讨论
  是否扩展 D10 子进程协议，不能在 D11 中预留未验收的消息类型。
- publisher 会合并快速中间状态，monitor 不是完整审计日志；只要求最新和最终状态
  正确。真实 Windows/Linux 调度、独立 Python 3.9 和真实 AtomGit 网络节奏未验证，
  交付时必须作为范围外证据报告。
- 本次登记不授权实施、分支、测试、提交、合并、推送、PR、标签、发布或任何真实
  AtomGit 写入。

### D11 Compatibility And Rollback

- 不改变公开 CLI/native SDK/legacy SDK 的命令、参数、函数签名、返回值或异常。
  历史 `upload_directory(progress_callback=None)` 签名保持；只有显式提供 callback
  的 resumable 调用在外层批次边界收到安全字典，callback 异常被隔离。
- 快照继续为 v1，使用现有 `batch`、`files_total`、`files_done` 白名单字段；旧快照
  继续可读，旧版本也会忽略已有但未展示的字段。没有 HF metadata、上传投影、源文件
  或远端数据迁移。
- 若实现回归，可整体回退单个 D11 实现提交恢复旧显示；无需清理或转换快照。不得只
  保留半条 callback 接线，避免服务产生状态但 CLI 丢弃，或 CLI 注入 callback 但服务
  从不通知。

### D11 Activation Status

- [x] 维护者接受 D11 完整方案并授权登记到本地开发 Issue。
- [x] 维护者单独授权激活 D11 实施。
- [x] 本地任务分支已创建。
- [x] 红灯、实现、文档和开发底线已完成。
- [x] 专项、完整离线门禁和独立审查通过。
- [x] 维护者完成人工验收并授权适用的 Git/远程交付。

### D12 Objective And Evidence

修复 resumable 上传监控会话的更新时间不能反映观测发布存活的问题：后台 publisher
每次实际写出快照时刷新会话 `updated_at`，使活动会话排序、默认选择和后续陈旧判断
使用最近一次成功发布的时间，同时不伪造上传进度或改变上传结果。

当前 `src/atomgit/infrastructure/upload_observe.py` 中 `SnapshotPublisher` 会在状态唤醒
和空闲约两秒 heartbeat 时重复调用 `publish_snapshot()`，但 `_latest` 只是
`UploadSession.update()` 当时的浅副本；只有业务 `update()` 会刷新 `updated_at`。
因此磁盘快照可以持续原子替换，JSON 中的会话时间却长期不变。`load_sessions()` 和
`select_session()` 又直接按该字段排序并选择默认会话，导致仍在发布的会话可能排在
已经停止更新的旧活动会话之后。

证据来自当前 `publish_snapshot()`、`SnapshotPublisher`、`UploadSession`、
`load_sessions()`、`select_session()`、`tests/test_upload_observability.py`、
`docs/features/upload-monitor.md` 和 `UPLOAD-OBSERVABILITY` 开发底线的只读核对。本次
仅登记方案，没有运行实现测试或真实 AtomGit 上传；D11 的 93/93 交付基线不能替代
D12 红灯和实施后的完整复验。

### D12 Accepted Timestamp Contract

- 会话 `updated_at` 表示上传进程最近一次成功发布可读快照的时间，用于同类会话排序、
  默认会话选择和观测通路陈旧判断。新鲜时间只证明 publisher 仍在发布，不证明文件
  字节、批次或远端提交正在推进，也不能单独证明上传成功或失败。
- `publish_snapshot()` 在既有白名单复制之后、序列化之前，用 `str(time.time())` 覆盖
  即将发布副本的会话 `updated_at`。该统一边界覆盖首次写入、业务状态唤醒、空闲
  heartbeat、直接发布和 `close()` 最终刷新，不在各调用者重复更新时间逻辑。
- 时间刷新不得反向修改调用者字典、`UploadSession.data`、Flow 或事件。Flow/事件各自
  的 `updated_at` 继续只表示对应业务状态变化；`batch`、`files_total`、`files_done`、
  速度、阶段、累计值、终态和上传结果均保持原值。
- `publish_snapshot()` 继续先复制和过滤允许字段，并沿用异常吞吐边界。只有成功写入并
  原子替换后的磁盘快照才暴露新时间；临时文件、序列化、权限或替换失败仍只导致本次
  观测丢失，不改变上传返回、异常、CLI 退出码、断点数据或远程状态。
- 保留快照 version 1、字符串 Unix 秒格式、最多每秒一次持久化、空闲约两秒 heartbeat、
  `0700` 目录、`0600` 文件、原子替换和现有清理行为；不新增 `heartbeat_at`、
  `progress_at` 或文件 mtime 回退模型。

### D12 Implementation Scope

1. 在 `src/atomgit/infrastructure/upload_observe.py` 的 `publish_snapshot()` 白名单副本上
   统一刷新 `updated_at`。不修改 `SnapshotPublisher` 调度、`UploadSession.update()`、
   `load_sessions()`、`select_session()` 或 monitor 命令接口；现有消费者自然读取新时间。
2. 扩展 `tests/test_upload_observability.py`：先建立旧实现下 heartbeat 重写但时间不变的
   红灯，再覆盖副本不回写、连续 heartbeat、状态唤醒、关闭最终刷新、活动会话排序/
   默认选择、旧 v1 快照和写入失败隔离。测试使用受控短间隔或有界轮询，不真实等待两秒。
3. 为 `UPLOAD-OBSERVABILITY` 在 `tests/development_floor_contract.py` 增加 `UPO-007`，并
   同步 `.ai/DEVELOPMENT_FLOOR.md`、`docs/development_floor.md`、
   `docs/features/upload-monitor.md` 以及必要的 `.ai/ARCHITECTURE.md`、
   `docs/architecture.md`。不新增测试脚本、生产模块、依赖、CLI/SDK 参数或 schema 版本。

### D12 Affected Capability IDs

`UPLOAD-OBSERVABILITY`、`UPLOAD-RESUMABLE`、`RUNTIME`、`PORTABILITY`、
`ARCHITECTURE`、`ERROR-REDACTION` 和 `FLOOR-REGISTRY`。

### D12 Protected Existing Invariants

- `UPO-001`–`UPO-006`：快照继续只读、有界、原子、脱敏；父进程仍是会话唯一状态
  所有者，D09 Flow、D10 跨进程观测/结果隔离和 D11 批次/文件进度不退化。
- `RESUMEUP-002`、`RESUMEUP-005`、`RESUMEUP-006`：失败不误报成功，断点、待对账提交、
  `parent_commit` 并发保护及结果分类不受 heartbeat 影响。
- `RUNTIME-002`：后台 publisher 的异常和生命周期继续被隔离；不增加全局状态、线程、
  进程、锁、队列或同步磁盘等待到上传热路径。
- `REDACT-001`：时间刷新不增加仓库、路径、文件名、OID、token、URL、请求头、响应正文、
  异常原文或其他敏感字段。
- `ARCH-001`、`ARCH-003`：修改留在现有 infrastructure 持久化边界，不把渲染、上传
  编排或跨进程协议引入 `publish_snapshot()`。
- `PORT-001`：继续使用 Python 3.9 标准库时间和文件操作；Windows/POSIX 的快照格式及
  上传结果保持一致。
- 公开 Click schema、CLI/native/legacy SDK 签名、返回与异常、普通上传、model/dataset、
  revision、timeout、批次、Flow、缓存清理和快照读取行为不变。
- 实施前基线为 28 个能力、133 条不变量和 93 个离线脚本；不得删除、跳过、弱化或改写
  既有证据来通过 D12。

### D12 New Or Changed Invariants

- `UPO-007`：每次成功持久化上传会话快照均以发布时的会话 `updated_at` 表示观测存活；
  heartbeat 只更新发布副本的会话时间，不修改调用者状态、业务进度、Flow/事件时间或
  上传结果，失败仍保持 best-effort 隔离。
- 实施完成后预计保持 28 个能力和 93 个测试脚本，不变量从 133 增至 134；实际数字必须
  以实施时 Git 和可执行登记册为准，方案登记不代表不变量已经实现。

### D12 Focused Tests And Evidence

| 场景 | 必须证明的结果 |
|---|---|
| 同一活动会话无业务提交，publisher 连续 heartbeat | 磁盘 `updated_at` 递增，其余会话、批次、文件、Flow 和事件内容不变 |
| 调用方传入固定旧时间后直接发布 | 写出副本使用发布时间，原始字典和 `UploadSession.data` 不被后台修改 |
| 业务状态唤醒和 `close()` 最终刷新 | 最新及最终快照时间不会被旧 `_latest` 恢复，真实 status 和业务字段保留 |
| 两个活动会话具有不同最近发布时间 | `load_sessions()` 排序和 `select_session()` 默认选择最新发布者 |
| 旧 v1、字段缺失、非法 session ID 和畸形快照 | 旧快照继续可读或按现有规则安全忽略，不要求迁移或新增字段 |
| 序列化、目录、权限、临时文件或原子替换失败 | 只丢失观测更新，不改变上传结果、错误分类、退出码、断点或远端调用 |
| publisher 存活但批次/Flow 长期不变 | 只刷新会话时间，不伪装业务推进或生成成功/失败结论 |

激活后至少运行：

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate atomgit_cli
python tests/test_upload_observability.py
python tests/test_resumable_recovery.py
python tests/test_upload_batching.py
python tests/test_development_floor.py
python tests/test_architecture_parity.py
python tests/test_cli_error_redaction.py
python tests/run_cli_baseline.py
python -m compileall -q .
python -m pip check
git diff --check
```

最后一次代码、测试或文档修正后必须重新运行完整离线基线和静态门禁，并按
`.ai/REVIEW.md` 执行独立审查。真实 AtomGit 上传不是本地 heartbeat 合同的必需证据，
未获授权时不得执行或以 mock 结果声称远程验证。

### D12 Implementation Phases And Acceptance

1. 维护者单独激活后，从最新 `yuto` 创建本地
   `codex/d12-upload-session-heartbeat` 任务分支；冻结快照 v1、发布频率、D09–D11
   合同和开发底线，在既有上传观测脚本中增加红灯。验证：旧实现仅因 heartbeat
   重写旧 `updated_at` 而失败，其他断言继续通过。
2. 在 `publish_snapshot()` 的白名单副本上增加一次发布时间刷新，不新增 helper、字段
   或调用方接线。验证：直接发布、状态唤醒、连续 heartbeat、最终刷新和失败隔离专项
   通过，调用方及业务字段不变。
3. 更新 `UPO-007`、用户说明和必要架构文档。验证：能力登记预计为 28/134/93，旧 v1、
   脱敏、结构、权限、缓存清理和 Python 3.9 合同通过。
4. 运行完整离线门禁、差异/凭证/生成物检查和独立审查。验证：实现、测试和文档一致，
   原有五份未提交 `.ai` 规范修改未混入任务差异，无未解决 P0/P1/P2/P3 发现，再进入
   人工验收。

验收必须同时满足：空闲活动会话每次成功 heartbeat 发布后会话时间更新；排序和默认
选择使用最近发布者；状态唤醒及关闭最终快照正确；调用方、Flow、事件、批次、文件和
上传结果未被 heartbeat 修改；写入失败仍隔离；快照 v1、公开接口、D09–D11、普通上传、
SDK、安全和可移植性不退化；完整基线、静态门禁、开发底线和独立审查全部通过。

### D12 Non-Goals And Residual Risks

- 不处理 D13 终态自动退出、D14 Unix 时间格式、D15 终端刷屏、D16 仓库类型警告、
  D17 真实跨进程端到端测试或 D18 历史文档矛盾。
- 不新增 `heartbeat_at`、`progress_at`、mtime 回退、停滞看门狗、daemon、socket、TUI、
  下载监控、普通上传或单文件 monitor，也不改变 publisher 的 1 秒限频与约 2 秒心跳。
- publisher 存活但上传 worker 停滞时，会话 `updated_at` 仍会保持新鲜；用户必须结合
  `batch`、`files_done` 和 Flow 状态判断业务是否推进。D12 不把该情况误报为成功或失败。
- 继续使用现有 wall-clock Unix 秒；系统时间回拨可能短暂影响排序。真实 Windows/Linux
  调度、独立 Python 3.9 解释器和真实网络节奏未在方案登记阶段验证，交付时必须报告。
- 本次登记不授权实施、分支、测试、提交、合并、推送、PR、标签、发布或任何真实
  AtomGit 操作。

### D12 Compatibility And Rollback

- 快照继续为 version 1，`updated_at` 保持现有字符串 Unix 秒格式；旧快照和旧读取方
  无需迁移。内部直接调用 `publish_snapshot()` 时，传入的历史 `updated_at` 将按已接受
  的新语义被发布时间覆盖，但调用方字典保持不变。
- 不改变 CLI/native SDK/legacy SDK 的命令、参数、签名、返回、异常、上传协议、HF
  metadata、缓存投影、源文件或远端内容；无需数据迁移或清理已有快照。
- 若实现回归，可整体回退单个 D12 实现提交；新版本写出的快照仍是旧代码可读的 v1
  JSON。不得保留文档/台账而只回退实现，或保留实现而删除 `UPO-007` 回归证据。

### D12 Activation Status

- [x] 维护者接受 D12 完整方案并授权登记到本地开发 Issue。
- [x] 维护者单独授权激活 D12 实施。
- [x] 本地任务分支已创建。
- [x] 红灯、实现、文档和开发底线已完成。
- [x] 专项、完整离线门禁和独立审查通过。
- [x] 维护者完成人工验收并授权适用的 Git/远程交付。

### D12 Implementation And Focused Evidence

- 红灯：在旧实现上运行 `python tests/test_upload_observability.py` 为 23/25；新增的
  heartbeat 时间和活动会话默认选择两项失败，既有 23 项通过，根因确认为发布副本
  沿用旧 `updated_at`。
- 实现：`publish_snapshot()` 在白名单复制后用 `str(time.time())` 只刷新待写副本的
  会话时间；未修改调用者、Flow/事件时间、批次/文件进度、上传结果、发布调度、公开
  接口、快照 version 或依赖。
- 回归与文档：扩展既有上传观测脚本，覆盖连续 heartbeat、状态唤醒、活动会话排序和
  默认选择、关闭最终刷新、调用方不回写及 Flow/事件不变；登记 `UPO-007` 并同步上传
  监控、架构、测试和开发底线文档。登记册为 28 个能力、134 条不变量、93 个脚本。
- 专项（离线，`atomgit_cli` 环境）：上传观测 25/25、resumable 恢复 81/81、上传批次
  17/17、开发底线 15/15、架构 parity 23/23、CLI 脱敏 20/20 通过。
- 原有五份未提交 `.ai` 规范修改的差异哈希保持为
  `3b97e958e3fd66ea382d1164e9fd0802469542f0ed996be8448bacba9f69b794`、
  `062c160b446f4a2f5f135e098ab424434c4512ec6bba7651e451971cd4ab746c`、
  `f656f5fc112147b2a5b652171d0f5598ae18239a4823ad3da6c029fee300f8c2`、
  `e0821287447ba0301d272ee9e504594c9becf1255c8897b0580a0886749fb03f`、
  `89790cfb07499e86735b2a3ffe3f73ec884544fb8019b13224b1e3189c6ca277`。
- 本实施检查点之后继续运行完整离线基线、最终静态/安全检查和独立审查；Issue 保持
  active，未授权提交、合并、推送或真实 AtomGit 操作。

### D12 Complete Gate Evidence

- 最后一次测试修改后，`python tests/test_upload_observability.py` 为 **25/25**，完整
  基线为 **93 passed in 114.57s**；审查记录写回后的终局
  `python tests/run_cli_baseline.py` 为 **93 passed in 119.77s**。均在 `atomgit_cli`
  conda 环境离线运行。
- `python -m compileall -q .`、`python -m pip check`、3 个变更 Python 文件的
  Python 3.9 AST、Black、Ruff、任务拥有的两个导入文件 isort、打包/格式债务 13/13、
  `git diff --check`、凭证模式、二进制差异和未跟踪生成物检查通过。运行环境为
  Python 3.10.20，锁定版本为 `huggingface-hub==1.1.7`、`datasets==4.4.1`；D12 未新增
  或修改第三方依赖调用。
- `tests/development_floor_contract.py` 的全文件 isort 在当前和 `HEAD` 均退出 1，且本次
  差异不含 import；这是登记册已锁定的既存格式债务，没有增长，不在 D12 范围内改写。
- 原有五份 `.ai` 规范修改哈希再次核对不变。未运行真实 AtomGit、Windows/Linux、
  独立 Python 3.9 解释器或 D17 真实跨进程端到端链路；这些不是本地 heartbeat 合同的
  必需证据，作为残余风险保留。完整门禁通过后进入独立审查，仍未授权提交、合并或推送。

### D12 Independent Review

- Findings: 无 P0/P1/P2/P3 发现。
- Review scope: 核对活动 Issue、任务差异、`publish_snapshot()` 全部调用方、
  `SnapshotPublisher.stop()` 与后台写入顺序、CLI 上传的 finish/close 顺序、回归强度、
  `UPO-007`、文档、锁定依赖版本、93/93 完整基线和静态/安全证据。
- Conclusion: 发布时间只写入白名单副本；并发最终刷新即使与后台发布重叠，也只会原子
  发布同一终态副本和更晚 heartbeat，不会回退调用方、Flow/事件、批次/文件进度或上传
  结果。未发现需要扩大 D12 的可复现问题。
- Missing evidence and residual risks: 未运行真实 AtomGit、Windows/Linux、独立 Python
  3.9 解释器或 D17 真实跨进程链路；系统 wall clock 回拨和 publisher 存活但 worker
  停滞仍是已接受限制。
- Verdict: `APPROVED`。该结论不代表人工验收，也不授权提交、合并或推送。

### D12 Delivery Verification

- 维护者授权交付后，`python tests/test_upload_observability.py` 为 **25/25**，
  `python tests/run_cli_baseline.py` 为 **93 passed in 118.02s**；验收与授权记录写回后的
  提交前完整基线为 **93 passed in 114.83s**。
- compileall、pip check、Python 3.9 AST、Black、任务拥有文件的 isort、Ruff、打包与
  格式债务 13/13、凭证模式、二进制差异、未跟踪生成物和 `git diff --check` 通过；
  原有五份未提交 `.ai` 规范修改哈希不变。
- 人工验收：`accepted`。授权范围仅为 D12 本地任务提交、no-ff 合入 `yuto`、仅推送
  `github/yuto` 和交付记录；任务分支、真实 AtomGit、PR、标签、发布及 D13–D18 不推送
  或不执行。

### Current Handoff Snapshot

- Worktree: `/Users/yutaozhang/yuto/codes/atomgit_cli`，当前任务分支
  `codex/d12-upload-session-heartbeat` 基于 `yuto@611a468` 创建；D11 任务提交
  `6a9d6f7` 已通过 no-ff 合并提交 `0e0f7bd` 合入并限定推送至 `github/yuto`，任务
  分支保留在本地且未推送。D09/D10 任务提交
  `f1b4c78` 已通过 no-ff 合并提交 `85167bd` 完成本地合入，
  并已仅推送和核验 `github/yuto`。D09/D10 任务分支保留在本地且未推送。
- D03 no-ff 合并提交：`6b5a9687cf461bf99a4e6d30445b5e17a4894c25`，已仅推送
  `github/yuto` 并核验当时远端一致。
- D01 任务提交：`a4d7216`（fix(upload): remove total upload deadline）。
- 本地 no-ff 合并并已推送的提交：`720d641a776fae7ff94c786f45fe813530387f25`。
- D01 交付记录提交 `11ffbe5` 已推送；当前远端 yuto 为该提交，远端没有
  `codex/d01-upload-request-timeout` 分支。
- D04 合并提交树同已验证的任务分支一致；只推送 `github/yuto`，没有修改 main 或
  atomgit 远端，远端没有 D04 任务分支。
- D05 本地任务分支 `codex/d05-pointer-verification-retry` 保留且未推送；远端不存在该
  任务分支，没有修改 `main`、其他远端分支或真实 AtomGit 仓库。
- 原有 `.ai/DEVELOPMENT_RULES.md`、`.ai/DOD.md`、`.ai/MASTER_PROMPT.md`、
  `.ai/README.md`、`.ai/WORKFLOW.md` 五份未提交修改仍原样保留；续接必须使用当前
  worktree，不能将其误归入后续 Issue；本次只叠加获授权的 D12 `.ai/TASK.md` 和
  `.ai/ISSUE_DISCUSSION.md` 方案记录。D06–D11 任务分支保留在本地且未推送，没有
  修改 `main`、其他远端分支或真实 AtomGit 仓库。
- D11 红灯：`python tests/test_upload_batching.py` 退出 1；既有 15 个场景通过，仅新增
  的 21 文件两批 callback 生命周期失败，确认旧实现从不调用 `progress_callback`。
- D11 实现：上传服务在 resumable 实际计划、外层批次开始、成功和失败后发送三个
  安全字段；CLI 私有 callback 经 runner 到历史 API 并更新父进程 `UploadSession`；
  详细视图仅在存在 `files_total` 时显示累计确认数，公开合同和 D10 队列不变。
- D11 专项：batching 17/17、上传观测 24/24、上传进度 28/28、多进程恢复 81/81、
  上传 ownership 17/17、架构 parity 23/23、CLI 脱敏 20/20、开发底线 15/15、
  resumable 入口 61/61、SDK 参数 14/14、结构 18/18、CLI surface 54/54 和打包 13/13
  通过。登记为 28 个能力、133 条不变量、93 个离线脚本。
- D11 完整门禁：`python tests/run_cli_baseline.py` 为 **93 passed in 116.51s**；
  compileall、pip check、8 个变更 Python 文件的 Python 3.9 AST、HF 1.1.7 真实签名、
  格式债务、凭证模式、二进制差异、未跟踪生成物和 `git diff --check` 均通过。
  原有五份 `.ai` 规范修改哈希保持不变；未运行真实 AtomGit、Windows/Linux 或独立
  Python 3.9 解释器。当前进入独立审查，未授权提交、合并或推送。
- D11 最终复验：独立审查前，`python tests/run_cli_baseline.py` 为
  **93 passed in 117.79s**；compileall、pip check、打包 13/13、公开 legacy/native
  SDK 签名、凭证模式和 `git diff --check` 再次通过。
- D11 独立审查：无 P0/P1/P2/P3 发现，结论 `APPROVED`。审查确认批次状态口径、
  失败后确认数、callback 隔离、D10 队列边界、公开兼容和文档一致；真实 AtomGit、
  Windows/Linux、独立 Python 3.9 解释器和 D17 真实端到端链路未运行。该结论不授权
  提交、合并或推送。
- D11 交付复验：维护者授权后，`python tests/run_cli_baseline.py` 首轮为
  **93 passed in 118.03s**，证据写回后终轮为 **93 passed in 117.61s**；compileall、
  pip check、打包 13/13、Python 3.9 AST、
  锁定依赖和公开签名、凭证模式、二进制差异、未跟踪生成物及 `git diff --check`
  均通过。原有五份 `.ai` 规范修改哈希保持不变。
- D11 交付：实现提交 `6a9d6f7`，no-ff 合并提交 `0e0f7bd`；已仅推送并核验
  `github/yuto`，远端不存在 D11 任务分支，未修改 `main` 或其他远端分支。
- D12 当前状态：维护者已接受发布边界刷新会话 `updated_at` 的完整方案并单独授权
  开始开发；本地任务分支已创建。旧实现专项 23/25 的两项新失败已由发布副本单行刷新
  修复；实现、文档、`UPO-007`、专项和最终 93/93 完整离线门禁均已完成，独立审查无
  P0/P1/P2/P3 发现并 `APPROVED`，当前等待人工验收；尚未提交、合并、推送或执行真实
  AtomGit 操作，D13 讨论暂停。
- D06 红灯：`test_canonical_lfs_pointer.py` 为 34/35、
  `test_resumable_commit_policy.py` 为 55/56；旧实现仅缺少有效 commit 返回后的
  `created/unconfirmed` 细分状态，原有断言全部通过。
- D06 实现与专项：新增兼容 pointer 错误子类，贯通普通/resumable、worker、CLI、
  原生 SDK 和历史 SDK；普通 pointer 37/37、resumable 提交 56/56、错误分类 45/45、
  CLI/API 错误处理 29/29、SDK timeout 10/10、架构 parity 23/23、结构 18/18、打包
  13/13，开发底线新增 `LFS-006`，当前为 28 个能力、122 条不变量、93 个测试脚本。
- D06 完整门禁：`python tests/run_cli_baseline.py` 为 93 passed in 107.44s；compileall、
  pip check、Python 3.9 AST、锁定依赖真实签名、生产文件格式策略、格式债务和
  `git diff --check` 均通过。Black 债务未增长，isort 债务减少一个差异块。
- D06 交付复验：维护者授权后重跑 `python tests/run_cli_baseline.py`，结果为
  93 passed in 103.05s；compileall、pip check、Python 3.9 AST、锁定依赖真实签名、
  凭证模式、二进制差异、未跟踪生成物和 `git diff --check` 再次通过。
- D06 独立审查：无 P0/P1/P2/P3 发现，结论 `APPROVED`；真实 AtomGit、Windows/Linux
  和真实 Python 3.9 仍未验证。该结论不授权提交、合并或推送。
- D06 交付：实现提交 `928b8b9`，no-ff 合并提交 `0e7bb12`；交付记录提交
  `505f384` 已仅推送 `github/yuto`，任务分支未推送。
- D07 交付：实现提交 `23e51d7`，no-ff 合并提交 `d109e6b`；任务分支保持本地且不
  推送，仅推送并核验 `github/yuto`。
- D08 实现与专项：新增私有原子 `pending-commit-v1.json`、投影锁、H1/H2 强摘要对账、
  `parent_commit` 并发保护、冲突/未知失败关闭和恢复统计；提交策略 70/70、恢复与进程
  52/52、上传错误 29/29、结构 18/18、打包 13/13 及批次专项通过。审查前修正了恢复
  异常绕过 fatal 回调的问题并增加回归；格式债务保持 Black 409、isort 87、Ruff 44。
- D08 最终完整基线：`python tests/run_cli_baseline.py` 为 **93 passed in 97.66s**；
  compileall、pip check、15 个变更 Python 文件的 Python 3.9 AST、锁定依赖真实签名、
  格式债务、凭证模式、二进制差异、未跟踪生成物和 `git diff --check` 均通过。
- D08 交付复验：维护者授权后重跑 `python tests/run_cli_baseline.py`，结果为
  **93 passed in 101.76s**；compileall、pip check、Python 3.9 AST、锁定依赖签名、
  格式债务、凭证模式、二进制差异、未跟踪生成物和 `git diff --check` 再次通过，
  五份既有 `.ai` 规范修改哈希保持不变。
- D08 独立审查：首轮 P2/P3 已修复并重新通过全部门禁；第二轮无新发现，结论
  `APPROVED`。未执行真实 AtomGit、提交、合并、推送、PR 或发布。
- D08 交付：任务提交 `16025c8`，no-ff 合并提交 `9ee013c`；仅推送并核验
  `github/yuto`，任务分支保留在本地且未推送。没有修改 `main`、其他远端分支或真实
  AtomGit 仓库。
- D09/D10 红灯：旧实现不接受 coordinator `observation_callback`，缺少
  `UploadSession.observe`，并且 `spawn`、`fork`、`forkserver` 均无法通过显式通道把
  Flow 状态交给父进程；原有恢复决策、结果分类和回收断言保持通过。
- D09/D10 实现：协调器产生匿名完整 Flow 状态、独立 5 秒显示样本、30 秒正式窗口、
  12 项趋势和有界事件；resumable 子进程使用独立 256 条、单条 16 KiB 的 v1 JSON
  观测队列，父进程严格校验、去重、归并和收敛已知 Flow，且是快照唯一写入者。
- D09/D10 专项：慢流恢复 33/33、上传观测 22/22、多进程恢复 81/81、resumable 入口
  61/61、上传批次 16/16、dataset resumable 11/11、上传错误 29/29、开发底线 15/15、
  结构 18/18、打包与格式 13/13 通过。`spawn`、`fork`、`forkserver` 均使用同一显式
  合同；沙箱限制下的 forkserver 和用户缓存权限专项已在沙箱外离线运行。
- D09/D10 完整门禁：首轮实现后为 92/93，唯一失败是既有 dataset inline Queue 替身
  未接受新有界队列接口；补齐后为 93 passed in 101.07s。首轮审查发现观测队列创建和
  清理异常未完全隔离（P2），修复并新增回归后多进程专项为 81/81，最终完整基线为
  93 passed in 106.16s。最后一处文档校正后再次在 `atomgit_cli` 环境运行完整门禁，
  结果为 **93 passed in 106.38s**；compileall、pip check、打包 13/13、锁定依赖
  版本/签名、格式债务、凭证模式、二进制差异和 `git diff --check` 均通过。
- D09/D10 交付复验：维护者授权后再次运行 `python tests/run_cli_baseline.py`，结果为
  **93 passed in 106.13s**；compileall、pip check、打包 13/13、凭证模式、二进制、
  未跟踪生成物和 `git diff --check` 再次通过，`github/yuto` 仍为基线 `75094a7`。
- D09/D10 独立审查：首轮 P2 和续接复核的 P3 文档一致性问题均已修复；最终无开放
  P0/P1/P2/P3 发现，结论 `APPROVED`。真实 AtomGit、Windows/Linux、独立 Python 3.9
  和 D17 真实端到端链路未运行；该结论不授权提交、合并或推送。
- D09/D10 交付：任务提交 `f1b4c78`，no-ff 合并提交 `85167bd`；仅推送并核验
  `github/yuto`，任务分支保留在本地且未推送。没有修改 `main`、其他远端分支或真实
  AtomGit 仓库。
- D04 变更：`src/atomgit/adapters/upload/{projection,service}.py`、
  `tests/{test_upload_batching,development_floor_contract,packaging_contract,structure_contract}.py`、
  `docs/{upload_command_analysis,development_floor}.md`、`.ai/{TASK,ISSUE_DISCUSSION}.md`，
  以及已有用户修改中的 `.ai/DEVELOPMENT_FLOOR.md` 一处计数；无未跟踪文件。
- D05 红灯：`python tests/test_canonical_lfs_pointer.py` 为 25/26，通过项不变；新增
  “首次读取失败、第二次成功”用例在旧实现上只调用 1 次并失败，原因与 D05 一致。
- D05 实现与专项：共享验证边界使用标准库固定 `2.0/4.0` 退避；pointer 直接回归
  34/34、resumable 提交策略 55/55、上传入口与开发底线专项全部通过。新增 `LFS-005`，
  当前登记为 28 个能力、121 条不变量、93 个测试脚本；格式债务数量未增长。
- D05 完整门禁：第一次完整基线 93 passed in 107.41s；校准当前基线计数后最终运行
  `python tests/run_cli_baseline.py` 为 93 passed in 106.98s。`compileall`、`pip check`、
  Python 3.9 语法、Ruff、生产文件 Black、格式债务、差异和生成物状态检查均通过。
- D05 交付复验：`python tests/run_cli_baseline.py` 为 93 passed in 108.68s；compileall、
  pip check、Python 3.9 语法、Ruff、生产文件 Black、格式债务、差异与未跟踪生成物
  检查通过。维护者据此接受 D05 并授权限定提交、合并和推送。
- D05 独立审查：无 P0/P1/P2/P3 发现，结论 `APPROVED`；真实 AtomGit、Windows/Linux
  与真实 Python 3.9 仍未验证。
- D05 修改路径：`src/atomgit/adapters/lfs/pointer.py`，`tests/{test_canonical_lfs_pointer,
  test_resumable_commit_policy,development_floor_contract,packaging_contract}.py`，`README.md`，
  `docs/{architecture,development_floor,testing,upload_command_analysis}.md`，以及
  `.ai/{ARCHITECTURE,DEVELOPMENT_FLOOR,ISSUE_DISCUSSION,TASK,TESTING}.md`。
- 原有 `.ai/DEVELOPMENT_RULES.md`、`.ai/DOD.md`、`.ai/MASTER_PROMPT.md`、
  `.ai/README.md`、`.ai/WORKFLOW.md` 的未提交修改继续原样保留；
  `.ai/ISSUE_DISCUSSION.md` 和 `.ai/TASK.md` 还叠加了获授权的 D09/D10 方案与实施记录；
  后续交付必须精确隔离，不能误纳入无关修改。
- D05 交付：实现提交 `b6d65eb`，no-ff 合并提交 `ef17f41`；仅推送
  `github/yuto` 后以 `git ls-remote` 核验远端为 `ef17f41`，任务分支未推送。
- D11 当前状态：实现提交 `6a9d6f7` 已通过 no-ff 合并提交 `0e0f7bd` 合入 `yuto`，
  并仅推送和核验 `github/yuto`；任务分支保留在本地且未推送。D12 已单独激活本地
  实施与离线验证；真实 AtomGit、D13–D18 实施及 D12 提交/合并/推送仍未授权。
- D04 验证：专项 14/14；三次完整离线基线均 93/93，最终验收为
  93 passed in 100.75s；compileall、pip check、Python 3.9 语法、锁定依赖和差异检查通过。
- D05 验证与交付证据以上述 D05 专项、完整门禁、审查和交付记录为准。

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
