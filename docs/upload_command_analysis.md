# `atomgit upload` 当前实现分析

> 本文基于 `yuto` 分支版本 1.0.5+yuto.1 的当前源码。它同时记录已实现参数和已知缺陷，
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
| `-t, --timeout` | `300` | HF 请求超时秒数 |
| `--no-progress-bar` | 关闭 | 禁用 HF 上传进度条 |
| `-p, --path-in-repo` | 根目录 | 仓库内目标前缀 |
| `-r, --repo-type` | HF 默认 model | `model` 或 `dataset` |
| `--revision` | 默认分支 | CLI 接受已存在的安全分支名；需先显式创建 |
| `-i, --ignore` | 无 | 逗号分隔的 ignore patterns |
| `--resumable` | 关闭 | 目录使用 `upload_large_folder` |
| `--num-workers` | HF 默认 | resumable worker 数 |

AtomGit 当前的 HF 兼容服务对 model 和 dataset 共用创建与上传传输路由。CLI
仍使用 `dataset` 表达仓库业务类型，但底层调用映射到 model 路由。2026-08-04
的受控大文件探测确认共享路由可进入 LFS 上传并保留恢复元数据，因此不再沿用
旧 dataset 端点的 404 拒绝保护；用户输入不会被改写。

## 2. CLI 前置处理

`cli.upload` 依次执行：

1. 校验 timeout、worker 数、安全 revision 名和 worker/resumable 关系；
2. 使用 `validate_repo_name` 校验 repo ID；
3. 将 PATH 转为 `Path` 并区分文件或目录；
4. 使用 `normalize_path_in_repo` 与 `parse_ignore_patterns` 规整参数；
5. 根据文件/目录类型拒绝歧义选项组合；
6. 检查 `config.is_logged_in()`；
7. 打印大小、文件数量和选择的参数；
8. 将参数传给 `api.upload_folder` 或 `api.upload_directory`。

CLI 在认证和远端调用前拒绝歧义组合：单文件不接受 `--resumable` 或
`--ignore`；`--num-workers` 必须与 `--resumable` 同用；resumable 目录不接受
`--path-in-repo` 或 `--message`。这些用法错误统一以退出码 2 结束，不会
进入 API 层。

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

## 5. Resumable 目录上传

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

HF large-folder 模式的其他限制：

- 不支持 `path_in_repo`，CLI 在远端调用前拒绝该组合；
- 不支持用户指定的单一 commit message，CLI 在远端调用前拒绝
  `--message`；服务过程可产生多次提交；
- repo type 必填，CLI 未指定时补为 `model`；
- 续传元数据由 HF 写入上传目录下的缓存位置。

真实 404 MB 文件测试已完成“中断 -> 再次执行 -> 下载回读”，文件大小和
SHA-256 均一致。

## 6. 进度条和 timeout

上传前保存完整进度条状态和 `hf_constants.DEFAULT_REQUEST_TIMEOUT`，退出上传
分支时在 `finally` 中恢复调用前状态。由于这些仍是进程级全局值，并发调用需
谨慎。

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
