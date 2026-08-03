# `atomgit upload` 当前实现分析

> 本文基于 `yuto` 分支版本 1.0.5 的当前源码。它同时记录已实现参数和已知缺陷，
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
| `--revision` | 默认分支 | 目标 revision |
| `-i, --ignore` | 无 | 逗号分隔的 ignore patterns |
| `--resumable` | 关闭 | 目录使用 `upload_large_folder` |
| `--num-workers` | HF 默认 | resumable worker 数 |

AtomGit 当前的 HF 兼容服务对 model 和 dataset 共用上传传输路由。CLI 仍
使用 `dataset` 表达仓库业务类型，但底层上传调用映射到 model 路由，以
避免 dataset LFS batch 端点返回 404。建仓类型和用户输入不会被改写。

## 2. CLI 前置处理

`cli.upload` 依次执行：

1. 检查 `config.is_logged_in()`；
2. 使用 `validate_repo_name` 校验 repo ID；
3. 将 PATH 转为 `Path` 并区分文件或目录；
4. 使用 `normalize_path_in_repo` 统一斜杠并拒绝 `..`；
5. 使用 `parse_ignore_patterns` 拆分、去空和去重；
6. 打印大小、文件数量和选择的参数；
7. 将参数传给 `api.upload_folder` 或 `api.upload_directory`。

`--resumable` 用于文件时会警告并忽略。`--ignore` 用于单文件时会警告，但仍
传给 API 层并触发回退上传路径。

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
- 用户传入非空 ignore patterns。

回退路径在当前工作目录创建共享 `.tmp_upload`，复制文件后上传，并在 `finally`
中删除。该设计存在并发冲突和异常进程残留风险，新实现不应继续扩展这种模式。

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

resumable 分支计划调用：

```text
HfApi().upload_large_folder(
    repo_id=...,
    folder_path=...,
    repo_type=model-or-dataset,
    token=...,
    revision=...,
    ignore_patterns=...,
    num_workers=...,
)
```

当前锁定的 `huggingface-hub==1.1.7` 中，`token` 应传给 `HfApi(token=...)`
构造函数，`upload_large_folder()` 方法本身不接受 `token`。因此当前
`--resumable` 会在调用阶段失败：

```text
HfApi.upload_large_folder() got an unexpected keyword argument 'token'
```

这是已经确认的兼容性缺陷。现有 fake 接受宽松参数，因此旧测试没有发现真实
签名问题。

HF large-folder 模式的其他限制：

- 不支持 `path_in_repo`，CLI 只打印警告；
- 不使用单一 commit message，会产生多次提交；
- repo type 必填，CLI 未指定时补为 `model`；
- 续传元数据由 HF 写入上传目录下的缓存位置。

修复参数问题后仍需通过真实的“中断 -> 再次执行 -> 文件校验”测试，才能声明
断点续传完成。

## 6. 进度条和 timeout

上传前调用 `_set_progress_bar(progress_bar)`，退出上传分支时恢复为开启状态。
由于 HF 的进度条开关是进程级全局状态，并发调用仍需谨慎。

timeout 通过覆盖 `hf_constants.DEFAULT_REQUEST_TIMEOUT` 实现。当前代码没有保存并
恢复原值，所以一次上传会永久改变同一 Python 进程后续 HF 请求的 timeout。
注释中的“临时修改”与实际行为不一致，这是已知缺陷。

## 7. Repo ID

`HuggingFaceAPI` 定义了多层 repo ID 转换，但上传方法没有调用它。上传当前将
CLI 校验通过的原始 `repo_id` 直接交给 HF。下载则会调用转换。

因此多层 ID 在上传中的实际支持状态不确定，不能仅根据
`validate_repo_name` 允许多层格式就宣称可用。

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

这些测试没有证明：

- resumable 与真实 HF 签名兼容；
- revision 会在 AtomGit 创建或写入目标远端分支；
- 合法 dataset 仓库端到端上传成功；
- 多层 repo ID 上传成功；
- timeout 在同一进程中正确恢复；
- ignore 在真实远端确实排除了文件。

远程测试应拆分每项能力并执行上传、下载回读和内容校验，详见
[testing.md](testing.md)。
