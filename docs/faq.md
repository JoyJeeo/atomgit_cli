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
全局状态，自动化测试默认不应在真实 HOME 下执行。登录期间，这两个域名会用
空 helper 条目重置继承的通用 helper 链，避免 token 被系统 keychain 等其他
helper 再次保存。原有的域名专属 helper 值会原样保存到权限受限状态文件，但
不会写入本次登录 token，并在 logout 时按原顺序恢复；其他域名不受影响。
如果恢复失败，logout 会返回非零；解决 Git 配置问题后可再次执行 logout，CLI
会根据残留状态文件重试恢复，即使当前已经显示为未登录。

Git helper 使用登录时已验证并缓存的用户名，不会在每次 Git 操作时调用身份
API。从旧版本升级后应重新运行一次 `atomgit login`；如果本地配置缺少 username，
helper 会拒绝返回 token。

## 未登录可以下载吗？

CLI 允许尝试下载公开仓库。私有仓库需要有效 token。是否真正匿名可访问仍取决
于仓库权限和 AtomGit 服务端响应。2026-08-04 的受控矩阵确认同一版本客户端可
匿名下载公开测试仓库；对私有仓库匿名请求失败，提供 token 后下载和 SHA-256
回读成功。

## resumable 当前是否可用？

可以。当前实现通过 `HfApi(token=...)` 完成认证，不再把不兼容的 `token` 参数
传给 `upload_large_folder()`。2026-08-04 分别对私有 model 和 dataset 使用
399,300,506 字节文件执行了 CLI 超时中断、同目录续传、下载回读；两者最终
SHA-256 均一致。dataset 的用户类型保持不变，底层自动使用共享 model 兼容路由。

## `--revision dev` 是否已经验证？

远程证据表明 AtomGit 不会创建或暴露请求的 `dev` 分支。为避免把内容静默写入
`main` 后报告假成功，CLI 和 SDK 当前只接受空值或 `main`；其他 revision 会在
任何远程调用前明确拒绝。

## dataset 上传和建仓是否已经验证？

已经验证。AtomGit 的 HF dataset 创建路由会返回 401，因此 dataset 建仓与上传
都通过当前可用的共享 model 兼容路由完成，用户侧仍使用 dataset 业务类型；
小型文件和约 399 MB 文件均有下载回读 SHA-256 证据。

## 为什么离线测试通过仍可能有远程问题？

mock 只能证明本地参数构造符合测试预期。如果 fake 接受任意 `**kwargs`，它甚至
可能接受真实 HF 方法拒绝的参数。依赖契约测试和受控远程回读缺一不可。

## 可以直接运行 `deploy.sh twine` 吗？

不可以作为日常测试运行。它会向 PyPI 写入发布产物，必须有明确发布授权。详细
流程见 [release.md](release.md)。
