# 开发底线

## 正式定义

> AtomGit CLI 的所有已实现能力，都必须拥有稳定的能力登记、明确的行为不变量、可执行的离线回归测试、必要的依赖和安全契约，以及在适用时的受控远程证据。任何开发活动都必须证明受影响的旧能力未退化，并将新增能力纳入同一套基线。未通过开发底线的变更，不得进入 Issue 完成、合并、发布或继续扩展开发阶段。

开发底线不是冻结内部实现，而是冻结已经向用户或维护者承诺的行为和安全结果。
模块可以重构，测试可以改进，但已登记能力不能在没有明确兼容决策的情况下被删除、
改名、弱化或停止验证。

## 当前基线

当前完整离线基线包含：

- 26 个稳定能力 ID；
- 110 条可观察行为不变量；
- 90 个隔离 pytest case，每个 case 对应一个可直接执行的
  `tests/test_*.py` 回归脚本；
- 精确 CLI schema、叶子命令分派、依赖、安全、打包和跨平台合同。

统一入口：

```bash
python tests/run_cli_baseline.py
```

`tests/development_floor_contract.py` 是能力和不变量的可执行登记册；
`tests/test_development_floor.py` 校验登记完整性、证据映射和工作流文档；
`tests/cli_baseline_contract.py` 继续精确锁定 CLI 接口、分派和测试脚本清单。

结构重构还受 `tests/structure_contract.py` 与
`tests/test_structure_guard.py` 阻断：当前每个生产模块必须有唯一能力所有者，新增
依赖边和禁止方向会失败，现存 facade 体量与两条反向依赖减少时必须在同一变更中
收紧声明，防止之后回长；空占位包禁止进入源码。公共导入、函数签名以及 source、PEP 660 editable、wheel、
sdist 的模块内容也属于同一永久合同。已交付的 infrastructure owner 与历史
utils/config/runtime facade 还锁定实现来源、对象身份和 patch 接缝；其他批准的目标
目录不是当前实现，不能据此提前创建空包或宣称迁移已经完成。
SDK owner 与两个历史 `atomgit_hub` facade 还锁定公开/私有函数身份、签名、
依赖补丁传播以及 source、editable、wheel、sdist 的精确模块集合。
CLI command owner 还锁定历史 Click schema、18 个叶 callback 签名、运行时旧路径
patch 传播和 `cli.py` facade 体量不回长。

## 能力登记册

| 能力 ID | 能力边界 | 主要保护结果 |
|---|---|---|
| `FLOOR-REGISTRY` | 开发底线自身 | 能力、测试、文档和证据不能失联 |
| `CLI-SURFACE` | CLI 公共接口 | 命令、参数、默认值、类型和 help 稳定 |
| `CLI-DISPATCH` | CLI 叶子命令 | 每个叶子命令都有真实隔离分派 |
| `AUTH-CONFIG` | 登录与配置 | 有界验证、私密原子写入、准确失败语义 |
| `GIT-CREDENTIAL` | Git helper | 域名隔离、原配置保留和事务恢复 |
| `REPO-MANAGEMENT` | 仓库管理 | 建仓、列表、可见性和删除均验证最终状态 |
| `REVISION` | 分支与 revision | 分支显式创建并验证，未验证 revision 不上传 |
| `UPLOAD-FILE` | 单文件上传 | 不复制源文件、路径准确、临时资源安全 |
| `UPLOAD-FOLDER` | 普通目录上传 | ignore、前缀、批次、worker 和错误语义稳定 |
| `UPLOAD-RESUMABLE` | resumable 上传 | 投影隔离、恢复、超时、对账和进度正确 |
| `UPLOAD-LFS` | LFS 策略 | preupload、规范 pointer 和 attributes 安全 |
| `UPLOAD-LFS-RECOVERY` | LFS 慢流恢复 | 只替换异常对象并有界停止 |
| `DOWNLOAD-SNAPSHOT` | 整仓下载 | 清单、既有文件、重试、manifest 和 prune 安全 |
| `DOWNLOAD-FILE` | 单文件下载 | 精确目标、resume、checksum 和 Unicode 行为 |
| `DOWNLOAD-INTEGRITY` | 下载完整性 | framing、大小、摘要和原子替换一致 |
| `DOWNLOAD-SECURITY` | 下载安全 | 路径、重定向、凭证、锁和 prune 边界 |
| `SDK-DOWNLOAD` | SDK 下载 | snapshot、file、URL 和 dataset 合同 |
| `SDK-UPLOAD` | SDK 上传 | 参数、临时生命周期和全局状态恢复 |
| `SDK-REPO` | SDK 建仓 | 类型、支持边界和稳定异常层次 |
| `REPO-ID` | 仓库 ID | 所有入口使用一致校验和多层映射 |
| `RUNTIME` | 运行时策略 | endpoint、cache、timeout 和 progress 状态 |
| `CACHE` | 缓存清理 | 只清理 AtomGit 管理内容 |
| `DEPENDENCY-CONTRACT` | 锁定依赖 | 真实 HF/datasets 签名拒绝宽松 fake |
| `PACKAGING` | 分发安装 | wheel、入口、导入、installer 和 deploy |
| `PORTABILITY` | 平台兼容 | Python 3.9+、Windows 和 POSIX 安全结果一致 |
| `ERROR-REDACTION` | 错误脱敏 | 保留错误类别但不暴露凭证或签名 URL |

每个登记项还包含风险级别、入口、完整不变量、离线测试、文档、证据类别和受控
远程证据状态。详细机器可读内容以可执行登记册为准。

## 行为不变量

行为不变量必须描述可观察结果，例如：

- CLI exit code 和下游参数；
- 上传到达的仓库、revision 和路径；
- 下载内容、大小和摘要；
- 失败后原文件、临时资源和断点元数据状态；
- timeout、progress、环境变量和 Git 配置恢复；
- token、签名 URL 和远端响应不进入输出。

每条不变量都有唯一 ID，并映射到至少一个可执行离线测试。仅描述内部函数结构、
仅检查调用次数或使用任意 `**kwargs` fake，不能作为充分证据。

## 新功能接入

任何新 Issue 在实现前必须记录：

- `Affected Capability IDs`；
- `Protected Existing Invariants`；
- `New Or Changed Invariants`；
- 专项测试和需要的依赖、安全、打包、跨平台或远程证据；
- 完整 baseline 结果；
- 未运行检查和剩余风险。

新功能必须先增加失败测试，再更新能力登记和文档。新增 `test_*.py` 必须进入精确
测试清单并映射到至少一个能力。专项测试用于快速定位，不能替代完整 baseline。

## 阻断规则

完整 baseline 适用于功能、缺陷、测试、文档、重构、兼容、分发和发布等所有开发
Issue。失败或未运行时，Issue 保持活动状态，禁止完成、人工验收、交付 commit、
merge、push、tag、release、publication 和继续扩展其他功能。

不得通过删除测试、跳过测试、放宽 fake、降低期望值或修改登记数量来适配非预期
回归。应修复真实问题并重新运行完整 baseline。

有意兼容性变化必须由维护者在活动 Issue 中明确授权，记录旧/新行为、迁移路径、
受影响 ID、替代证据和剩余风险，并在最终完整 baseline 通过后才能交付。

## 远程证据边界

离线测试证明客户端行为和安全失败，但不能替代 AtomGit 服务端事实。需要远程
证据的能力会登记为 `controlled`、`partial` 或 `required-before-claim`。远程测试
必须继续遵守专用凭证、授权仓库、回读 checksum 和禁止泄露 token 的规则。
