# atomgit upload 指令功能深度分析

> 本文档基于 `yuto` 分支当前代码（v1.0.5），深入分析 `atomgit upload` 指令的功能、参数、执行流程与实现细节。
> 运行环境约定：所有指令需在 conda 环境 `atomgit_cli` 下执行（`conda run -n atomgit_cli <command>`）。

---

## 一、指令定义

`atomgit upload` 定义在 `cli.py`，基于 Click 框架。完整签名：

```python
@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--repo-id', required=True, help='目标仓库ID (username/repo-name)')
@click.option('--message', '-m', default='', help='上传说明')
@click.option('--timeout', '-t', 'timeout_sec', default=300, type=float,
              help='上传超时时间（秒），默认300秒（5分钟）。大数据集建议增大此值')
def upload(path, repo_id, message, timeout_sec):
    """上传文件或目录到仓库"""
```

### 用法示例（来自 README）

```bash
# 上传模型目录
atomgit upload ./your-model-dir --repo-id your-username/your-model-name

# 上传数据集目录
atomgit upload ./your-dataset-dir --repo-id your-username/your-dataset-name

# 上传单个文件
atomgit upload ./model.bin --repo-id your-username/your-model-name

# 带提交说明与自定义超时
atomgit upload ./big-dir --repo-id user/repo -m "上传大模型权重" -t 1200
```

---

## 二、参数详解

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `path` | `click.Path(exists=True)` | 是 | — | 本地文件或目录路径，**Click 会校验路径必须存在** |
| `--repo-id` | TEXT | 是 | — | 目标仓库 ID，格式 `username/repo-name`（也支持多层命名空间） |
| `-m` / `--message` | TEXT | 否 | `''` | 上传提交说明；为空时由底层使用默认信息 |
| `-t` / `--timeout` | FLOAT | 否 | `300` | 上传超时秒数，默认 5 分钟；大模型/大数据集建议调大 |

`atomgit upload --help` 实际输出：

```
Usage: atomgit upload [OPTIONS] PATH
  上传文件或目录到仓库
Options:
  --repo-id TEXT       目标仓库ID (username/repo-name)  [required]
  -m, --message TEXT   上传说明
  -t, --timeout FLOAT  上传超时时间（秒），默认300秒（5分钟）。大数据集建议增大此值
```

---

## 三、前置校验（CLI 层）

`upload` 命令在真正上传前依次做 4 项校验，任一失败即 `sys.exit(1)` 退出：

1. **登录校验**：`config.is_logged_in()` —— 必须先 `atomgit login`，否则提示「请先登录：atomgit login」。
2. **仓库 ID 格式校验**：`validate_repo_name(repo_id)`（在 `utils.py`）—— 规则：
   - URL 解码后至少包含一个 `/`
   - 支持多层命名空间（如 `hf_mirrors/Qwen/Qwen3-Reranker-0.6B`）
   - 字符仅允许字母、数字、下划线、短横线、点、斜杠，以及 `%`（用于 URL 编码）
3. **路径存在校验**：`path.exists()`（Click 的 `exists=True` 已在参数阶段保证，此处为二次防御）。
4. **路径类型分发**：`path.is_file()` / `path.is_dir()` —— 文件与目录走不同分支；既非文件也非目录则报「不支持的路径类型」。

---

## 四、上传执行流程

### 情况 A：上传文件（`path.is_file()`）

```
cli.upload
 ├─ 打印文件名与大小（format_file_size）
 └─ api.upload_folder(path, repo_id, message=message, upload_timeout=timeout_sec)
      ├─ 校验 file_path.exists() 与登录凭证
      ├─ 在当前工作目录创建临时目录 ./.tmp_upload
      ├─ shutil.copy2(file_path, .tmp_upload/<文件名>)   # 仅复制单个文件
      ├─ monkey-patch: hf_constants.DEFAULT_REQUEST_TIMEOUT = upload_timeout
      ├─ huggingface_hub.upload_folder(
      │      repo_id=repo_id,
      │      folder_path='.tmp_upload',
      │      token=<保存的 token>,
      │      commit_message= message 或 "Upload folder using atomgit client")
      └─ finally: shutil.rmtree(.tmp_upload)              # 无论成败都清理临时目录
```

要点：
- **单文件上传实际仍走 `upload_folder`**：先把文件复制进 `.tmp_upload` 目录，再以「目录」形式提交给 HF `upload_folder`。
- 临时目录位于**当前工作目录**下的 `.tmp_upload`（非系统临时目录），运行结束自动删除。⚠️ 该目录未在 `.gitignore` 中，若在该项目仓库内执行上传，可能产生未跟踪文件。
- 通过 monkey-patch **全局**修改 `hf_constants.DEFAULT_REQUEST_TIMEOUT`（进程级），影响该进程内所有后续 HF 请求超时。

### 情况 B：上传目录（`path.is_dir()`）

```
cli.upload
 ├─ 统计文件数量 count_files_in_directory
 ├─ 统计目录大小 get_directory_size → format_file_size
 ├─ 打印目录信息与超时设置
 └─ api.upload_directory(path, repo_id, message=message, upload_timeout=timeout_sec)
      ├─ 校验目录存在且 is_dir、登录凭证
      ├─ monkey-patch: hf_constants.DEFAULT_REQUEST_TIMEOUT = upload_timeout
      └─ huggingface_hub.upload_folder(
             repo_id=repo_id,
             folder_path=<原目录路径>,         # 直接用原目录，不复制
             token=<保存的 token>,
             commit_message= message 或 "Upload folder using atomgit client")
```

要点：
- **目录上传直接使用原目录**，不再复制到临时目录（与文件上传不同）。
- 其余（token 来源、超时 monkey-patch、commit_message 默认值）与文件上传一致。

---

## 五、依赖的底层能力

`upload` 指令的全部上传能力来自 `huggingface_hub.upload_folder`，`api.py` 在模块加载时已通过环境变量把 HF 端点重定向到 AtomGit：

```python
os.environ["HF_ENDPOINT"] = "https://hub.atomgit.com"
os.environ["HF_HUB_DISABLE_XET"] = "1"   # 禁用 Xet 协议，避免 xet-write-token 请求
os.environ["HF_HOME"] = "~/.cache/atomgit"
```

因此 `atomgit upload` 的实质是：**用 HF Hub 的上传协议，把数据推到 `hub.atomgit.com`**。

### Token 来源
- CLI 层不直接传 token，由 `api.upload_folder`/`upload_directory` 内部从 `config.get_credentials()` 读取 `~/.atomgit/config.json` 中的 `token`。
- 这也是为什么 `upload` 前必须先 `atomgit login`。

### Commit Message
- 用户传 `-m` 时使用用户消息；未传则统一使用 `"Upload folder using atomgit client"`。

### 超时控制
- 默认 300 秒；`-t` 可调。
- 实现：临时覆写 `huggingface_hub.constants.DEFAULT_REQUEST_TIMEOUT`。
- ⚠️ 注意：这是**进程级全局**修改，非线程安全；在并发或同进程多次调用场景需谨慎。

---

## 六、`upload` 当前**不具备**的能力

基于代码现状，列出几项用户可能期望但当前实现未覆盖的功能，便于评估：

1. **不支持指定仓库内路径**：CLI 的 `upload` 没有 `--path-in-repo` / `remote_path` 参数，只能上传到仓库根目录。
   - 注：SDK 层 `atomgit_hub.upload_folder` 的 `api.upload_folder` 虽保留了 `remote_path` 形参，但 CLI 未暴露，且单文件分支会把它复制到 `.tmp_upload` 根，未真正使用 remote_path 语义。
2. **不支持选择仓库类型**：无 `--repo-type`（model/dataset）参数，上传时默认按 model 仓库处理（HF `upload_folder` 默认 `repo_type="model"`）。
3. **不支持指定分支/revision**：无 `--revision` 参数。
4. **不支持 ignore patterns**：无法在上传时排除某些文件（如 `*.tmp`）。
5. **不支持断点续传/分块上传的显式控制**：依赖 HF `upload_folder` 自身行为，CLI 层无额外开关。
6. **无进度条**：CLI 仅打印文件数/大小，未接入 `tqdm`（SDK 层 `snapshot_download` 预留了 `tqdm_class`，但上传未用）。
7. **单文件上传会多一次本地拷贝**：走 `.tmp_upload`，对超大文件有额外磁盘开销。
8. **错误处理较粗**：`api.upload_folder`/`upload_directory` 捕获异常后仅 `print` 并返回 `False`，不区分 401/403/404 等语义（与 SDK 层 `atomgit_hub.upload_folder` 的细化错误封装不同）。

---

## 七、与 SDK 层 `upload_folder` 的差异

| 维度 | CLI `atomgit upload` | SDK `atomgit_hub.upload_folder` |
|------|----------------------|---------------------------------|
| 入口 | `cli.upload` → `api.upload_folder` | `atomgit_hub.upload_folder` |
| path_in_repo | 固定根目录（CLI 未暴露） | 支持，非根时先 `copytree` 重组 |
| repo_type | 默认 model（不可选） | 可传 `repo_type` |
| revision | 不支持 | 可传 `revision` |
| ignore_patterns | 不支持 | 可传 |
| token | 自动从 config 取 | 自动取，或显式传 |
| 错误封装 | 笼统 `print` + 返回 False | 区分 401/403/404 语义化异常 |
| 超时控制 | `--timeout`（monkey-patch） | `upload_timeout`（monkey-patch） |

即：CLI 是 SDK 的一个**简化子集**，屏蔽了 path_in_repo / repo_type / revision / ignore_patterns 等高级参数。

---

## 八、完整调用链（一图概览）

```
atomgit upload <path> --repo-id <id> -m <msg> -t <timeout>
   │
   ▼  Click 解析参数
cli.upload(path, repo_id, message, timeout_sec)
   │
   ├─ config.is_logged_in()        # 前置：登录校验
   ├─ validate_repo_name(repo_id)  # 前置：仓库ID格式校验
   ├─ path.exists() / is_file / is_dir
   │
   ├─[文件]─ api.upload_folder(path, repo_id, message, timeout)
   │           ├─ 创建 ./.tmp_upload，copy2 单文件入内
   │           ├─ monkey-patch DEFAULT_REQUEST_TIMEOUT
   │           └─ huggingface_hub.upload_folder(...)
   │
   └─[目录]─ api.upload_directory(dir_path, repo_id, message, timeout)
               ├─ monkey-patch DEFAULT_REQUEST_TIMEOUT
               └─ huggingface_hub.upload_folder(folder_path=原目录, ...)
   │
   ▼  HF Hub 协议（端点已重定向为 hub.atomgit.com）
HTTP PUT/POST → https://hub.atomgit.com/<repo_id>/...
   │
   ▼  结果回传
cli: 成功 print_success / 失败 print_error + sys.exit(1)
```

---

## 九、使用建议

1. **上传前先 `atomgit login`**，并确保 `--repo-id` 命名空间正确（支持多层 `org/ns/repo`，内部会做 `-` 转换）。
2. **大文件/大数据集务必用 `-t` 调大超时**，如 `-t 1800`（30 分钟），避免服务端处理响应期间客户端超时。
3. **目录上传比单文件上传更省磁盘**：目录直接走原路径，单文件会被复制到 `.tmp_upload`。
4. **上传到非根目录、指定 dataset 类型、排除临时文件**等需求，当前 CLI 不支持，需改用 SDK：
   ```python
   from atomgit_hub import upload_folder
   upload_folder("./data/", "user/repo", repo_type="dataset",
                 path_in_repo="datasets/", ignore_patterns=["*.tmp"])
   ```
5. **注意 `.tmp_upload`**：若在 git 仓库工作目录内执行单文件上传，会生成 `.tmp_upload` 目录（虽上传后自动删除，但进程异常退出时可能残留），建议将其加入 `.gitignore`。
