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
- resumable 参数；
- 单文件直接上传；
- 上传错误分类。

token 校验、持久化、损坏配置恢复、logout、配置权限、Git credential helper
隔离、URL 重定向、路径穿越、HTTP 响应完整性、临时文件清理和 wheel 安装均有
隔离离线测试。2026-08-06 的完整矩阵为 43 个 pytest case（自执行脚本内部可包含
多个聚合断言）。建仓、ignore、下载权限矩阵等远程路径已有一次受控
验收证据。维护者已授权两个固定测试仓库可直接重跑连线测试；其他仓库或
操作仍需单独授权。

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

标准完整离线命令：

```bash
python -m pytest
```

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

## 测试分层

### 单元测试

验证路径规范化、repo ID 校验、ignore 解析、错误分类和隔离配置文件读写。

### CLI 集成测试

使用 Click `CliRunner`，验证退出码、输出和传给 API 层的精确参数。文件和目录
必须分别覆盖。`tests/test_cli_surface.py` 还会枚举根命令公开的全部子命令，验证
login/logout/whoami/config-show 的认证、Git helper、失败与脱敏分支；所有依赖
均使用 fake，不访问真实 HOME、Git 配置或网络。

### 依赖契约测试

直接约束当前安装的 `huggingface-hub==1.1.7` 真实签名。禁止用无约束
`**kwargs` fake 掩盖真实 API 不接受的参数。

运行 `python tests/test_hf_api_contract.py` 可验证当前锁定版本、普通上传、
下载、建仓、`HfApi` 认证和 large-folder 调用签名。该测试只绑定函数签名，
不会发起网络请求。

### 打包冒烟测试

在隔离环境构建并安装 wheel，然后验证：

- `atomgit --version`
- `atomgit --help`
- `python -m atomgit --help`
- `import atomgit`
- `import atomgit_hub`

`python tests/test_wheel_smoke.py` 会从临时源码副本离线构建 wheel，并安装到
临时 venv；安装后会逐一运行全部顶层命令及 `repo create` 的帮助入口。该脚本也
包含在标准 pytest 矩阵中，不会在工作树生成构建产物。

### AtomGit 远程测试

远程测试默认关闭，只有用户明确授权后才运行。2026-08-06 起，用户已持续
授权使用已提供的测试登录，且仅可对以下两个专用仓库直接运行连线测试：

- `weixin_52273949/test_model`；
- `weixin_52273949/test_datasets`。

该授权不包括其他仓库、删除、发布或输出 token。连线测试必须使用：

- 专用测试 token；
- 唯一且可识别的一次性仓库名，或上述明确授权的固定仓库；
- 非生产仓库；
- 命令退出码；
- 下载回读和 SHA256 或 `cmp` 内容证据。

不能因为 CLI 打印“上传成功”就判定端到端通过。

2026-08-04 的授权验收使用隔离 HOME 和环境变量 token，验证了：

- 公开 model 内容匿名下载成功并与上传源 SHA-256 一致；
- 私有 dataset 匿名下载失败、认证下载成功且 SHA-256 一致；
- `path_in_repo` 中保留文件存在，`*.tmp` 与 `logs/*` 哨兵远端不存在；
- dataset 建仓和传输必须复用 AtomGit 的 model 兼容路由；
- 私有 model 与 dataset 均以 399,300,506 字节文件完成 CLI 超时中断、恢复、
  下载与 SHA-256 一致性验证；
- HF `private=False` 创建会假成功为私有仓库，因此客户端继续拒绝公开建仓；
- 多层 ID 被正确转换，但测试账号缺少转换后命名空间权限，create/upload 均以
  401 非零退出且未留下仓库；
- 固定测试仓库与多层物理 ID 最终在 model/dataset 路由均为 404。

## 远程测试矩阵

每项应独立执行，避免一个失败使多个能力都无法判断：

| 能力 | 最低证据 |
|---|---|
| model 建仓 | 新唯一仓库存在且类型正确 |
| dataset 私有建仓 | 仓库存在、类型和私有属性正确 |
| 单文件上传 | 下载回读校验和一致 |
| 目录上传 | 多个文件下载回读一致 |
| path-in-repo | 目标路径存在，仓库根目录没有误放文件 |
| ignore | 保留文件存在，被忽略文件不存在 |
| revision | 远端分支可查询，目标文件只在预期 revision |
| resumable | 首次中断，第二次恢复，最终校验和一致 |
| 公开下载 | 无 token 环境可以下载 |
| 私有下载 | 无 token 失败，有 token 成功 |

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
