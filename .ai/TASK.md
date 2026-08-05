# Current Issue Contract

# Issue DOWNLOAD-REPO-INFO-404

Status: `in_progress`

## Identity

- Local Issue: `DOWNLOAD-REPO-INFO-404`
- Title: `atomgit download 因 repo_info 404 误报"仓库为空"，需绕过 repo_info 直接下载`
- Type: `bug`, `cli`, `compatibility`
- Priority: `P1`
- Base: `yuto`
- Delivery mode: user-authorized local fix（未授权 commit/push，除非另行明确）。

## User Impact And Evidence

`python -m atomgit download weixin_52273949/test_model` 与
`.../test_datasets` 输出 `ℹ 仓库为空，没有可下载的文件；本地目录已创建`
并以 0 退出，而同一批文件在 hub 上确实存在（上传成功；
`GET https://hub.atomgit.com/{repo}/resolve/main/{file}` 带 token 返回 200）。

Root cause: `huggingface_hub==1.1.7` 的 `snapshot_download`/`hf_hub_download`
第一步调用 `repo_info`（`GET /api/models/{repo}`），AtomGit hub 未实现该路由
（404）。SDK 将仓库视为无文件，随后在 `tqdm.thread_map` 中对空迭代器触发
`ValueError: min() iterable argument is empty`，CLI 将其误判为空仓库。
探测证据：repo_info 404，tree/list_repo_files 200，resolve 200。

## Scope

In scope: `api.py download_repo`/`download_file` 绕过 repo_info，改用
`HfApi.list_repo_files` + resolve URL 直连下载（带 token、有限重试、
model/dataset 路由回退）；离线回归更新 `tests/test_download_contract.py`、
`tests/test_download_recovery.py`、`tests/test_repo_id_contract.py`。

Out of scope: `atomgit_hub.py` SDK 路径（仍走 HF SDK，受同一 repo_info 404
影响）、线上写操作、凭证、push/release。

## Acceptance Criteria

- `atomgit download <repo>` 能列出并下载真实文件；空仓库仍输出 `仓库为空`
  并成功退出。
- CLI 下载路径不再调用 `snapshot_download`/`repo_info`。
- 离线检查通过：test_download_contract 36/36、test_download_recovery 12/12、
  test_repo_id_contract 23/23；全量 pytest 基线不变（28 passed / 8 failed，
  均为既有 Windows 环境性问题）；`python -m compileall -q .`；
  `git diff --check`。

## Permissions

- Authorized: 本地源码/测试编辑。
- Not authorized: 线上仓库写操作、commit/push/merge/release、凭证变更。

## Delivery Record

- Fix: `download_repo`/`download_file` 通过 `_atomgit_list_repo_files`
  （HfApi.list_repo_files）列文件，再经 `_download_atomgit_file`
  （resolve URL + Authorization 头 + 有限重试 + model/dataset 路由回退）
  逐文件下载；空仓库判定基于真实文件清单；新增可选 `repo_type` 参数。
- Offline evidence: test_download_contract.py 36/36，test_download_recovery.py
  12/12，test_repo_id_contract.py 23/23；全量 pytest 28 passed / 8 failed
  （基线环境问题，无新增失败）；`python -m compileall -q .` OK；
  `git diff --check` OK。
- Live check: 待用户执行 `python -m atomgit download
  weixin_52273949/test_model -d <dir>` 验证。
- Copies: `C:\Users\29946\atomgit_cli` 与 `E:\桌面文件\atomgit_cli` 的 api.py
  已同步，测试文件已同步。

- Follow-up fix (user-reported live failure): Chinese filenames crashed download
  with UnicodeEncodeError because the resolve URL was built with the raw
  filename. `_atomgit_resolve_url` now percent-encodes via
  `urllib.parse.quote(filename, safe="/")`; regression added in
  test_download_contract.py (URL percent-encoded + ASCII-safe), suite now
  38/38. api.py + tests synced to `E:\桌面文件\atomgit_cli`.
- Remaining risk: SDK（atomgit_hub.py）下载仍受同一 repo_info 404 影响；
  在线下载尚未端到端验证。
## Follow-up: 子目录中文文件名下载回退（DOWNLOAD-REPO-INFO-404 扩展）

- User-reported: `sub/中文样本.csv` 下载报「仓库、文件或 revision 不存在」（404）。
- Root cause (platform): AtomGit resolve 路由对「子目录 + 非 ASCII 文件名」的百分号编码路径无法命中（404），但原始 UTF-8 字节路径可命中（200）；根目录中文文件名两种方式均 200。探测证据：标准 SDK 新上传的 sub2/嵌套中文测试.csv 同样编码 404 / 原始字节 200，与上传方式、文件新旧无关 → 平台缺陷。
- CLI fix (api.py): `_download_atomgit_file` 在编码 URL 全部 404 时，对非 ASCII 文件名追加原始 UTF-8 字节 URL 回退（`_atomgit_resolve_url_raw` + `_atomgit_download_raw`，基于 socket+ssl 直连，含重定向与 404 语义）。ASCII 文件名不触发回退；HF Hub 兼容性不变（标准编码 URL 优先）。
- Offline evidence: test_download_contract.py 43/43（新增 5 条回归）、test_download_recovery.py 12/12、test_repo_id_contract.py 23/23；全量 pytest 28 passed / 8 failed（基线不变）；compileall OK；git diff --check OK。
- Copies synced: C:\Users\29946\atomgit_cli 与 E:\桌面文件\atomgit_cli（api.py、tests/test_download_contract.py）。
- Online E2E (8/5, after user re-login): first live run failed with HTTPError 400 → root cause: the raw-socket sends in `_atomgit_raw_http_get` used literal `\\r\\n` (5 double-backslash escape errors, so no real CRLF; server replied 400 Bad Request). Fixed all 5 to real CRLF. After fix: `test_datasets` 14/14 files and `test_model` 62/62 files fully downloaded, including all nested Chinese filenames (`sub/中文样本.csv`, `sub2/嵌套中文测试.csv`, ...).
- 在线验证已完成（详见测试报告 3.5.1）；剩余：commit/push 待用户授权。
