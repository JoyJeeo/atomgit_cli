# 常见问题

## 开发时应该使用哪个分支？

使用 `yuto`。`main` 只用于镜像 AtomGit 上游，详见
[yuto_branch.md](yuto_branch.md)。

## 为什么所有命令都要求激活 conda 环境？

项目依赖锁定的 `huggingface-hub==1.1.7` 和 `datasets==4.4.1`。不同环境中的
函数签名可能不同，错误环境会导致测试结果和用户行为不一致。

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate atomgit_cli
```

## CLI 是怎样安装出来的？

`setup.py` 注册 `atomgit=atomgit.cli:cli`。执行 `python -m pip install -e .`
后，当前 conda 环境会生成 `atomgit` 命令。

## CLI 和 SDK 是同一套实现吗？

不是。CLI 主要走 `cli.py -> api.py`，Python SDK 走 `atomgit_hub.py`。它们
共享配置，但上传、下载和错误处理存在平行实现，因此修改公共能力时必须检查
两侧是否产生行为漂移。

## token 保存在哪里？

默认保存在 `~/.atomgit/config.json`。不要把该文件内容复制到日志、Issue、
测试夹具或提交中。

## 登录为什么会修改 Git 配置？

登录成功后，CLI 会为 `atomgit.com` 和 `hub.atomgit.com` 注册全局 Git
credential helper，使 Git HTTPS 操作能够复用保存的 token。因为它会修改用户
全局状态，自动化测试默认不应在真实 HOME 下执行。

## 未登录可以下载吗？

CLI 允许尝试下载公开仓库。私有仓库需要有效 token。是否真正匿名可访问仍取决
于仓库权限和 AtomGit 服务端响应。

## resumable 当前是否可用？

可以。当前实现通过 `HfApi(token=...)` 完成认证，不再把不兼容的 `token` 参数
传给 `upload_large_folder()`。真实 404 MB 文件测试已验证中断后复用本地状态、
继续上传，并通过下载回读 SHA-256 校验。

## `--revision dev` 是否已经验证？

尚未完整验证。已有测试中 CLI 返回上传成功，但 Git 无法发现远端 `dev` 分支。
需要区分客户端参数问题和 AtomGit 服务端 revision 语义后才能给出支持结论。

## dataset 上传和建仓是否已经验证？

已经验证。dataset 建仓保留 dataset 业务类型，上传通过 AtomGit 当前可用的共享
model 传输路由完成；小型 CSV 和约 399 MB 文件均通过下载回读 SHA-256 校验。

## 为什么离线测试通过仍可能有远程问题？

mock 只能证明本地参数构造符合测试预期。如果 fake 接受任意 `**kwargs`，它甚至
可能接受真实 HF 方法拒绝的参数。依赖契约测试和受控远程回读缺一不可。

## 可以直接运行 `deploy.sh twine` 吗？

不可以作为日常测试运行。它会向 PyPI 写入发布产物，必须有明确发布授权。详细
流程见 [release.md](release.md)。
