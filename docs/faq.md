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

## 普通用户怎样安装 CLI？

使用 `install.sh` 从已完成 GitHub Release 下载并校验 wheel；不要求 conda，可用
`--python` 指定目标 Python。Windows 使用固定 Release wheel 和 `SHA256SUMS` 手工
安装；POSIX/macOS/Linux 才支持 `install.sh`。

## CLI 是怎样开发安装出来的？

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
`--auto-configure-lfs`。启用后 CLI 会为服务端判定为 LFS 的安全扩展名显示
`*.扩展名` 规则及其全仓库影响，并在 LFS 对象上传或引用提交前检查根目录
`.gitattributes`。缺少有效规则时，它在私有缓冲目录保留已有字节并追加标准 LFS
行，携带目标 revision 当前 commit 做并发保护，只提交该文件并验证远端内容，再
重试当前批次；同一命令内已确认的扩展名不会跨批重复检查。对于超过 1 GB 却被服务端
判定为 regular 的文件，该选项仍会补齐规则并刷新模式。规则无法安全推导、权限失败、
并发冲突无法确认或配置后仍被判定为 regular 时会停止，不会生成宽泛规则或无限配置
commit。已有哈希和已提交状态会保留。
该主动路径已在授权测试仓库完成“缺失规则追加并上传、不可变 commit 回读、相同命令
重跑不产生新提交”的真实验收。

## 为什么 CLI 上传的 LFS 文件会让新克隆立即显示 modified？

旧的 AtomGit HF commit 服务会把 `lfsFile` 元数据生成成缺少最终 LF 的 Git LFS
pointer。文件的 LFS OID、大小和实际对象没有变化，但 `git-lfs clean` 会把 pointer
规范化并补上 LF，于是 Git 把刚克隆的文件判定为已修改。

当前 CLI 和 SDK 上传会在客户端生成固定 ASCII/LF 的标准 pointer，同时保留原有
LFS 对象上传；提交完成后再按精确 commit SHA 读取 V5 原始 blob 做逐字节验证。
单文件、普通目录和 resumable 目录统一使用这项契约，不针对某个仓库名称。若服务
返回的 pointer 不规范或无法验证，上传返回失败而不是误报成功。此修复阻止未来
CLI 上传继续引入问题，但不会自动改写既有提交；已有非规范 pointer 需要单独授权
的规范化提交或服务端修复。

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

如果某个 LFS 对象已有稳定速度基线，之后连续约 90 秒明显落后于自身和健康同伴，
CLI 会先估算继续等待与重建请求的剩余时间。只有重建预计至少快一倍时才只替换该
对象的连接，其他 worker 不暂停。basic LFS 对象必须从零重传；multipart 只重试
当前未确认 part，并保留同一 action 中已确认的 ETag。每个对象最多自动替换三次；
新连接未达到 2 倍改善，或有稳定同伴时未达到同伴基线的 70%，便停止继续替换。
全部连接同时变慢时最多允许一个探针。因此首次就慢、
缺少可信基线或剩余数据很少的对象可能继续当前连接，这是为避免无收益重传和重连
风暴而保留的限制。网络或服务端响应不明确仍通过新的 LFS Batch 查询对账，而不是
直接在旧签名 URL 上重复 PUT。

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

## `atomgit update` 会修改源码 checkout 吗？

不会。editable/source 安装会被拒绝，并提示 `git checkout yuto`、
`git pull --ff-only`、锁定依赖和 `pip install -e .` 的路径。只有 wheel 安装支持
`atomgit update`。

## 可以用 deploy.sh 发布到 PyPI 吗？

不可以。AtomGit CLI 的唯一官方发布渠道是受保护的手动 GitHub Actions Release
workflow；`deploy.sh` 没有 twine、PyPI token 或远程写路径。详细流程见
[release.md](release.md)。
