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

可以。当前实现通过
`HfApi(endpoint="https://hub.atomgit.com", token=...)` 固定 AtomGit 端点并
完成认证，不再把不兼容的 `token` 参数传给 `upload_large_folder()`。2026-08-04
分别对私有 model 和 dataset 使用
399,300,506 字节文件执行了 CLI 超时中断、同目录续传、下载回读；两者最终
SHA-256 均一致。dataset 的用户类型保持不变，底层自动使用共享 model 兼容路由。
CLI 目录上传现在默认选择 resumable；`--path-in-repo` 通过稳定的本地投影表达
远端前缀并保留 HF 元数据。需要单一提交说明或普通目录上传时使用 `--message`
（未显式选模式时自动普通上传）或 `--no-resumable`。

resumable 只上传到已存在的仓库。CLI 在所有批次前执行一次只读仓库/revision
校验，并屏蔽 HF 1.1.7 large-folder 启动阶段的隐式建仓请求；创建仓库仍需显式
使用 `atomgit repo create`。如果仓库策略把超过 1 GB 的文件判定为普通 Git 文件，
CLI 会在提交读取和 Base64 编码前停止，提示在 `.gitattributes` 中配置 Git LFS。
默认行为不会修改仓库；错误提示会说明可以在明确授权配置提交时加
`--auto-configure-lfs`。启用后 CLI 显示推导出的 `*.扩展名` 规则及其全仓库影响，
在私有缓冲目录单独读取或创建根目录 `.gitattributes`，保留已有字节并追加标准
LFS 行，携带目标 revision 当前 commit 做并发保护，只提交该文件并验证远端内容，
然后重试当前批次。无法安全推导扩展名、同一规则仍不生效或远端状态无法确认时会
停止。修正策略后重试仅刷新危险且尚未提交的模式缓存，保留文件哈希和已提交状态。
自动配置路径已有离线回归覆盖，但尚未完成真实 AtomGit 写入验收。

## 为什么普通大目录上传会警告并长时间没有进度？

`--no-resumable` 使用锁定 `huggingface-hub==1.1.7` 的 `upload_folder`。该版本在
应用 ignore patterns 后超过 30 个文件时提示大目录上传，超过 200 个文件时使用
warning 级别。提示不是失败，也不是根据总字节数触发；随后客户端会先读取并计算
全部待上传文件的哈希，因此真正的网络上传进度可能很久以后才出现。

普通模式直接读取源目录，不建立 `~/.cache/atomgit/upload-projections/` 完整
投影；LFS 文件默认最多使用 5 个线程并行上传。它会通过内容哈希询问服务端，已
存在的完整 LFS 内容只需在新提交中引用，因此相同文件换一个仓库内目录后可能
近乎立即完成。这是服务端内容去重，不是本地断点续传；传输到一半的单个新文件
仍可能需要从头重传。

一次处理数百或数千个文件可能在全部哈希和 LFS 传输之后，才因最终提交过大或
网络问题失败。当前 CLI 会在程序内部按 20 个实际上传文件顺序分批，失败后重新
执行同一命令即可继续使用稳定的批次投影；不会修改源目录，也不要同时运行多个
大目录上传进程争抢磁盘、网络和同一仓库分支。

CLI 会先应用 `--ignore` 再打印文件数量和大小，因此该数字与实际上传集合一致。
双引号已经阻止 shell 展开通配符，不要写成 `\*\*`；CLI 会在远端调用前拒绝
这种写法。递归忽略隐藏内容、JSON 和 `output` 前缀内容应写为：

```bash
--ignore ".*,**/.*,*.json,**/*.json,output*,**/output*"
```

省略 `--timeout` 只表示没有上传总时限；单次网络请求默认最多等待 300 秒。
resumable commit 收到 429 时按 `Retry-After` 或指数退避，不通过拆小批次增加请求
数量；响应超时后先核对远端对象，未提交的内容才按 `20/10/5/2/1` 降批。连续
失败会返回非零并保留断点元数据，重新执行同一命令可继续。

## 长时间上传时可以锁屏或熄灭显示器吗？

显示器熄灭或锁屏不会终止终端进程，只要操作系统仍保持唤醒，上传就会继续。
整机睡眠、合盖睡眠、关机、关闭承载上传的终端或断开源磁盘会暂停或终止网络与
文件读取。macOS 可在另一个保持开启的终端中使用
`caffeinate -i -w <上传进程 PID>`，仅在对应上传进程存活期间阻止空闲系统睡眠；
它不保证阻止合盖、手动睡眠、关机或电量耗尽。

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
