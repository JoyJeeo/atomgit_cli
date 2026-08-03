# 测试指南

## 当前状态

仓库当前的 `tests/test_upload_*.py` 是可直接执行的 Python 测试脚本，内部使用
自定义 `check()` 聚合断言，并通过进程退出码表示结果。它们不是标准 pytest
测试，因此不能用 pytest 收集数量或覆盖率代表这些脚本已经运行。

现有测试主要覆盖上传参数透传：

- 进度条开关；
- 仓库内路径；
- model/dataset 类型；
- revision；
- ignore patterns；
- resumable 参数；
- 单文件直接上传；
- 上传错误分类。

配置权限和 Git credential helper 隔离已有独立的临时 HOME 测试。完整登录网络
交互、建仓、部分下载路径、Python SDK 和 wheel 安装仍缺少同等级自动化覆盖。

## 环境

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate atomgit_cli
python -m pip install -e .
```

测试不得读取真实的 `~/.atomgit/config.json`。离线测试应替换配置访问并使用
明显为假的 token。

## 运行现有测试

逐个执行所有现有脚本，并以退出码为准：

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
必须分别覆盖。

### 依赖契约测试

直接约束当前安装的 `huggingface-hub==1.1.7` 真实签名。禁止用无约束
`**kwargs` fake 掩盖真实 API 不接受的参数。

### 打包冒烟测试

在隔离环境构建并安装 wheel，然后验证：

- `atomgit --version`
- `atomgit --help`
- `python -m atomgit --help`
- `import atomgit`
- `import atomgit_hub`

### AtomGit 远程测试

远程测试默认关闭，只有用户明确授权后才运行。必须使用：

- 专用测试 token；
- 唯一且可识别的一次性仓库名；
- 非生产仓库；
- 命令退出码；
- 下载回读和 SHA256 或 `cmp` 内容证据。

不能因为 CLI 打印“上传成功”就判定端到端通过。

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

- 当前 resumable fake 的方法签名比真实 HF API 宽松，曾掩盖 `token` 参数错误。
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
