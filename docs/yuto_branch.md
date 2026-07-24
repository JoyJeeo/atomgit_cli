# Yuto 主分支说明

> 本说明文件仅存在于 `yuto` 分支，用于标识该分支的用途与同步约定。

## 分支定位

本 GitHub 代码仓的**主分支**（main branch）是 `yuto`，而非 `main`。

各分支的角色如下：

- **`yuto`（本分支）**：GitHub 代码仓的主分支，承载本项目的实际开发与演进。
- **`main`**：从 [AtomGit](https://atomgit.com) 上拉取的**外部同步分支**，仅用于镜像/同步 AtomGit 上游的内容，不作为本项目的主开发线。

## 同步流程

当 AtomGit 上游开发出有趣的特性时，按以下流程同步：

1. 将 AtomGit 上游的新内容同步到 `main` 分支
2. 再将 `main` 分支的内容同步到 `yuto` 分支（本分支）

即：`AtomGit 上游` → `main`（外部同步分支）→ `yuto`（GitHub 主分支）。

## 分支约定

- 分支名：`yuto`
- 身份：GitHub 代码仓主分支
- `main` 分支定位为外部同步分支，不直接作为开发主线
- 仅在本分支保留的文件：`docs/yuto_branch.md`（即本文件）
- 本文件由 `yuto` 分支独有，用于明确区分 GitHub 主分支与外部同步分支
