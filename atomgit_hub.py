#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AtomGit Hub SDK - 类似huggingface_hub的SDK接口

这个模块提供了类似huggingface_hub的编程接口，
让用户可以通过Python代码直接使用AtomGit平台的功能。
"""

import os
import warnings
from typing import Optional, Union, List, Dict, Any
from pathlib import Path

try:
    from .runtime import configure_hf_environment
except ImportError:
    try:
        from runtime import configure_hf_environment
    except ImportError:
        from atomgit.runtime import configure_hf_environment

configure_hf_environment()

from huggingface_hub import snapshot_download as hf_snapshot_download
from huggingface_hub import hf_hub_download, upload_folder as hf_upload_folder, create_repo


try:
    from datasets import load_dataset as ds_load_dataset  # type: ignore
    from datasets.config import HF_DATASETS_CACHE  # type: ignore
    DATASET_SUPPORT = True
except ImportError:
    DATASET_SUPPORT = False
    ds_load_dataset = None
    HF_DATASETS_CACHE = None

try:
    from .config import config
    from .exceptions import (
        AtomGitAuthenticationError,
        AtomGitError,
        AtomGitNetworkError,
        AtomGitRepositoryExistsError,
        AtomGitRepositoryNotFoundError,
        AtomGitRevisionNotFoundError,
        AtomGitTimeoutError,
        AtomGitUnsupportedError,
    )
    from .utils import (
        is_auth_error,
        is_retryable_download_error,
        normalize_repo_id,
        run_download_with_retry,
        validate_upload_path_no_symlinks,
    )
except ImportError:
    try:
        from config import config
        from exceptions import (
            AtomGitAuthenticationError,
            AtomGitError,
            AtomGitNetworkError,
            AtomGitRepositoryExistsError,
            AtomGitRepositoryNotFoundError,
            AtomGitRevisionNotFoundError,
            AtomGitTimeoutError,
            AtomGitUnsupportedError,
        )
        from utils import (
            is_auth_error,
            is_retryable_download_error,
            normalize_repo_id,
            run_download_with_retry,
            validate_upload_path_no_symlinks,
        )
    except ImportError:
        from atomgit.config import config
        from atomgit.exceptions import (
            AtomGitAuthenticationError,
            AtomGitError,
            AtomGitNetworkError,
            AtomGitRepositoryExistsError,
            AtomGitRepositoryNotFoundError,
            AtomGitRevisionNotFoundError,
            AtomGitTimeoutError,
            AtomGitUnsupportedError,
        )
        from atomgit.utils import (
            is_auth_error,
            is_retryable_download_error,
            normalize_repo_id,
            run_download_with_retry,
            validate_upload_path_no_symlinks,
        )


def _sdk_error(error: Exception, operation: str, repo_id: str = None) -> AtomGitError:
    """Classify a dependency failure without echoing remote or signed URLs."""
    name = type(error).__name__
    message = str(error).lower()
    authentication_failure = is_auth_error(error)
    retryable_failure = is_retryable_download_error(error)
    if any(
        marker in message
        for marker in ("http://", "https://", "token", "secret", "signature", "certificate")
    ):
        error.args = (f"{name} details redacted",)
    target = f"：{repo_id}" if repo_id else ""
    if authentication_failure:
        return AtomGitAuthenticationError(
            f"{operation}认证失败或权限不足{target}；请检查 token 和仓库权限"
        )
    if name == "RevisionNotFoundError" or (
        "revision" in message and ("not found" in message or "404" in message)
    ):
        return AtomGitRevisionNotFoundError(
            f"{operation}的 revision 不存在{target}"
        )
    if "409" in message or "already exists" in message or name == "RepositoryExistsError":
        return AtomGitRepositoryExistsError(f"仓库已存在{target}")
    if name in ("RepositoryNotFoundError", "EntryNotFoundError") or (
        "404" in message or "not found" in message
    ):
        return AtomGitRepositoryNotFoundError(
            f"{operation}的仓库或文件不存在{target}"
        )
    if name == "TimeoutError" or "timeout" in message or "timed out" in message:
        return AtomGitTimeoutError(f"{operation}超时{target}；请检查网络或增大超时")
    if retryable_failure:
        return AtomGitNetworkError(f"{operation}网络连接失败{target}；请稍后重试")
    if "unsupported" in message or "not supported" in message:
        return AtomGitUnsupportedError(f"AtomGit 不支持请求的{operation}行为{target}")
    return AtomGitError(f"{operation}失败{target}（{name}）")


def _normalize_repo_id(repo_id: str) -> str:
    """标准化仓库 ID，兼容保留原有模块内辅助函数。"""
    return normalize_repo_id(repo_id)


def _atomgit_repo_type(repo_type: Optional[str]) -> Optional[str]:
    """Map dataset create/transfer calls to AtomGit's shared model route."""
    return "model" if repo_type == "dataset" else repo_type


def _get_token() -> Optional[str]:
    """获取保存的认证token"""
    try:
        credentials = config.get_credentials()
        if credentials and 'token' in credentials:
            return credentials['token']
    except Exception:
        pass
    return None


def snapshot_download(
    repo_id: str,
    revision: Optional[str] = None,
    cache_dir: Optional[Union[str, Path]] = None,
    local_dir: Optional[Union[str, Path]] = None,
    local_dir_use_symlinks: Union[bool, str] = "auto",
    library_name: Optional[str] = None,
    library_version: Optional[str] = None,
    user_agent: Optional[Union[str, Dict[str, str]]] = None,
    proxies: Optional[Dict[str, str]] = None,
    etag_timeout: float = 10,
    resume_download: bool = False,
    force_download: bool = False,
    token: Optional[Union[str, bool]] = None,
    local_files_only: bool = False,
    allow_patterns: Optional[Union[List[str], str]] = None,
    ignore_patterns: Optional[Union[List[str], str]] = None,
    max_workers: int = 8,
    tqdm_class: Optional[Any] = None,
) -> str:
    """
    从AtomGit Hub下载整个仓库的快照到本地目录
    
    参数:
        repo_id (str): 仓库ID，格式为 "username/repo-name" 或 "username/namespace/repo-name"
        revision (str, 可选): 指定版本/分支/标签，默认为 "main"
        cache_dir (str 或 Path, 可选): 缓存目录路径
        local_dir (str 或 Path, 可选): 下载到的本地目录路径
        local_dir_use_symlinks (bool 或 str, 可选): 是否使用符号链接，默认为 "auto"
        library_name (str, 可选): 调用库的名称
        library_version (str, 可选): 调用库的版本
        user_agent (str 或 dict, 可选): 用户代理
        proxies (dict, 可选): 代理配置
        etag_timeout (float, 可选): ETag超时时间，默认10秒
        resume_download (bool, 可选): 是否断点续传，默认False
        force_download (bool, 可选): 是否强制重新下载，默认False
        token (str 或 bool, 可选): 认证token，如果为None则尝试使用保存的token
        local_files_only (bool, 可选): 仅使用本地文件，默认False
        allow_patterns (list 或 str, 可选): 允许下载的文件模式
        ignore_patterns (list 或 str, 可选): 忽略的文件模式
        max_workers (int, 可选): 最大并发数，默认8
        tqdm_class (可选): 进度条类
    
    返回:
        str: 下载完成的本地目录路径
    
    示例:
        >>> from atomgit_hub import snapshot_download
        >>> local_path = snapshot_download("wuyw/Qwen3-Reranker-0.6B-test", local_dir="./models")
    """
    # 标准化仓库ID（处理三层格式）
    normalized_repo_id = _normalize_repo_id(repo_id)
    
    # 如果没有提供token，尝试使用保存的token
    if token is None:
        token = _get_token()
    
    # 构建参数字典
    kwargs = {
        'repo_id': normalized_repo_id,
    }
    
    # 添加可选参数
    if revision is not None:
        kwargs['revision'] = revision
    if cache_dir is not None:
        kwargs['cache_dir'] = str(cache_dir)
    if local_dir is not None:
        kwargs['local_dir'] = str(local_dir)
    if token is not None:
        kwargs['token'] = token

    legacy_options = []
    if local_dir_use_symlinks != "auto":
        legacy_options.append("local_dir_use_symlinks")
    if proxies is not None:
        legacy_options.append("proxies")
    if resume_download:
        legacy_options.append("resume_download")
    if legacy_options:
        warnings.warn(
            "huggingface-hub 1.1.7 no longer accepts and AtomGit ignores: "
            + ", ".join(legacy_options),
            FutureWarning,
            stacklevel=2,
        )
    
    # 其他参数
    kwargs.update({
        'library_name': library_name or "atomgit_hub",
        'library_version': library_version,
        'user_agent': user_agent,
        'etag_timeout': etag_timeout,
        'force_download': force_download,
        'local_files_only': local_files_only,
        'allow_patterns': allow_patterns,
        'ignore_patterns': ignore_patterns,
        'max_workers': max_workers,
        'tqdm_class': tqdm_class,
    })
    
    try:
        # 使用token下载
        result = run_download_with_retry(
            lambda: hf_snapshot_download(
                **{k: v for k, v in kwargs.items() if v is not None}
            )
        )
        return result
    except Exception as e:
        raise _sdk_error(e, "下载仓库", repo_id) from e


def hub_download_url(
    repo_id: str,
    filename: str,
    revision: Optional[str] = None,
    repo_type: Optional[str] = None,
) -> str:
    """
    获取AtomGit Hub上文件的下载URL
    
    参数:
        repo_id (str): 仓库ID
        filename (str): 文件名
        revision (str, 可选): 版本/分支/标签
        repo_type (str, 可选): 仓库类型，仅支持 model 或 dataset
    
    返回:
        str: 文件的下载URL
    """
    normalized_repo_id = _normalize_repo_id(repo_id)
    base_url = "https://hub.atomgit.com"
    
    if revision is None:
        revision = "main"
    
    if repo_type is None:
        repo_type = "model"
    
    # 构建URL
    url = f"{base_url}/{normalized_repo_id}/resolve/{revision}/{filename}"
    return url


def download_file(
    repo_id: str,
    filename: str,
    local_dir: Optional[Union[str, Path]] = None,
    revision: Optional[str] = None,
    token: Optional[str] = None,
    force_download: bool = False,
) -> str:
    """
    从AtomGit Hub下载单个文件
    
    参数:
        repo_id (str): 仓库ID
        filename (str): 文件名
        local_dir (str 或 Path, 可选): 本地目录
        revision (str, 可选): 版本/分支/标签
        token (str, 可选): 认证token
        force_download (bool, 可选): 是否强制重新下载
    
    返回:
        str: 下载的文件路径
    """
    # 标准化仓库ID
    normalized_repo_id = _normalize_repo_id(repo_id)
    
    # 如果没有提供token，尝试使用保存的token
    if token is None:
        token = _get_token()
    
    # 构建参数
    kwargs = {
        'repo_id': normalized_repo_id,
        'filename': filename,
    }
    
    if local_dir is not None:
        kwargs['local_dir'] = str(local_dir)
    if revision is not None:
        kwargs['revision'] = revision
    if token is not None:
        kwargs['token'] = token
    if force_download:
        kwargs['force_download'] = force_download
    
    try:
        result = run_download_with_retry(
            lambda: hf_hub_download(
                **{k: v for k, v in kwargs.items() if v is not None}
            )
        )
        return result
    except Exception as e:
        raise _sdk_error(e, "下载文件", repo_id) from e


def upload_folder(
    folder_path: Union[str, Path],
    repo_id: str,
    token: Optional[str] = None,
    repo_type: Optional[str] = None,
    revision: Optional[str] = None,
    commit_message: Optional[str] = None,
    commit_description: Optional[str] = None,
    path_in_repo: str = "./",
    ignore_patterns: Optional[List[str]] = None,
    upload_timeout: float = 300.0,
) -> str:
    """
    上传文件夹到AtomGit Hub
    
    参数:
        folder_path (str 或 Path): 本地文件夹路径
        repo_id (str): 仓库ID
        token (str, 可选): 认证token
        repo_type (str, 可选): 仓库类型
        revision (str, 可选): 分支名。AtomGit 当前仅支持默认分支 main；
                              其他值会在上传前被拒绝
        commit_message (str, 可选): 提交消息
        commit_description (str, 可选): 提交描述
        path_in_repo (str, 可选): 在仓库中的路径，默认为根目录
        ignore_patterns (List[str], 可选): 要忽略的文件模式
        upload_timeout (float, 可选): 上传超时时间（秒），默认300秒（5分钟）。
                                      对于大文件，服务器处理响应可能需要较长时间。
    
    返回:
        str: 提交的URL或ID
    
    示例:
        >>> upload_folder("./my-model/", "username/repo-name")
        >>> upload_folder("./data/", "username/repo", path_in_repo="datasets/")
        >>> upload_folder("./big-files/", "username/repo", upload_timeout=1200.0)  # 20分钟超时
    """
    # 标准化仓库ID
    normalized_repo_id = _normalize_repo_id(repo_id)
    
    # 转换为Path对象
    folder_path = Path(folder_path)

    validate_upload_path_no_symlinks(folder_path)
    
    if not folder_path.exists():
        raise FileNotFoundError(f"文件夹不存在: {folder_path}")
    
    if not folder_path.is_dir():
        raise NotADirectoryError(f"路径不是目录: {folder_path}")

    if repo_type not in (None, "model", "dataset"):
        raise ValueError("repo_type 仅支持 model 或 dataset")

    # SDK has no explicit branch-creation API, so preserve its verified
    # main-only upload contract even though the CLI can create branches first.
    if revision not in (None, "", "main"):
        raise AtomGitUnsupportedError(
            "AtomGit 当前仅支持默认 revision main，非默认分支不会被创建"
        )
    
    # 如果没有提供token，尝试使用保存的token
    if token is None:
        token = _get_token()
        if token is None:
            raise AtomGitAuthenticationError(
                "上传需要认证 token；请先使用 'atomgit login' 登录或提供 token"
            )
    
    # 直接使用原始目录，或者创建临时目录来重新组织结构
    import tempfile
    import shutil

    temporary_directory = None
    hf_constants = None
    original_timeout = None
    try:
        if path_in_repo == "./" or path_in_repo == "." or path_in_repo == "":
            # 如果要上传到根目录，直接使用源文件夹
            upload_path = str(folder_path)
        else:
            # 如果要上传到特定路径，需要重新组织目录结构
            temporary_directory = tempfile.TemporaryDirectory()
            temp_path = Path(temporary_directory.name)

            # 创建目标路径
            target_path = temp_path / path_in_repo.strip('./')
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 复制整个目录树
            shutil.copytree(folder_path, target_path, dirs_exist_ok=True)

            upload_path = str(temp_path)
        # 使用 Monkey Patch 方式临时修改 huggingface_hub 的默认超时配置
        from huggingface_hub import constants as hf_constants

        # 保存原始超时配置
        original_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT

        # 临时修改超时配置
        hf_constants.DEFAULT_REQUEST_TIMEOUT = upload_timeout

        try:
            # 使用huggingface_hub的upload_folder上传
            commit_msg = commit_message or f"Upload folder {folder_path.name}"
            upload_kwargs = dict(
                repo_id=normalized_repo_id,
                folder_path=upload_path,
                token=token,
                commit_message=commit_msg,
            )
            if repo_type is not None:
                # AtomGit 的 dataset 仓库保留业务类型，但当前上传传输
                # 使用与 model 相同的兼容路由。
                upload_kwargs["repo_type"] = _atomgit_repo_type(repo_type)
            if revision:
                upload_kwargs["revision"] = revision
            if commit_description is not None:
                upload_kwargs["commit_description"] = commit_description
            if ignore_patterns:
                upload_kwargs["ignore_patterns"] = ignore_patterns
            result = hf_upload_folder(**upload_kwargs)

            return result

        except Exception as e:
            raise _sdk_error(e, "上传目录", repo_id) from e
    finally:
        if hf_constants is not None and original_timeout is not None:
            hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
        if temporary_directory is not None:
            temporary_directory.cleanup()


def create_repository(
    repo_id: str,
    token: Optional[str] = None,
    private: bool = False,
    repo_type: str = "model",
    exist_ok: bool = False,
    space_sdk: Optional[str] = None,
    space_hardware: Optional[str] = None,
    space_storage: Optional[str] = None,
    space_sleep_time: Optional[int] = None,
    space_secrets: Optional[List[Dict]] = None,
    space_variables: Optional[List[Dict]] = None,
) -> str:
    """
    在AtomGit Hub上创建仓库
    
    参数:
        repo_id (str): 仓库ID
        token (str, 可选): 认证token
        private (bool, 可选): 是否为私有仓库。AtomGit 当前只允许已验证的
                              私有创建语义，必须显式设为 True
        repo_type (str, 可选): 仓库类型，仅支持 model 或 dataset；dataset
                              使用 AtomGit 的共享 model 兼容路由创建
        exist_ok (bool, 可选): 如果仓库已存在是否报错，默认False
        其他参数: 为签名兼容保留；AtomGit 不支持 Space 创建，传入时会拒绝
    
    返回:
        str: 仓库的URL
    """
    # 标准化仓库ID
    normalized_repo_id = _normalize_repo_id(repo_id)

    if not private:
        raise AtomGitUnsupportedError(
            "AtomGit 当前无法可靠验证公开仓库语义；请设置 private=True"
        )
    if repo_type not in ("model", "dataset"):
        raise ValueError("repo_type 仅支持 model 或 dataset")
    space_options = {
        "space_sdk": space_sdk,
        "space_hardware": space_hardware,
        "space_storage": space_storage,
        "space_sleep_time": space_sleep_time,
        "space_secrets": space_secrets,
        "space_variables": space_variables,
    }
    unsupported_space_options = [
        name for name, value in space_options.items() if value is not None
    ]
    if unsupported_space_options:
        raise AtomGitUnsupportedError(
            "AtomGit 不支持 Space 仓库参数: "
            + ", ".join(unsupported_space_options)
        )
    
    # 如果没有提供token，尝试使用保存的token
    if token is None:
        token = _get_token()
        if token is None:
            raise AtomGitAuthenticationError(
                "创建仓库需要认证 token；请先使用 'atomgit login' 登录或提供 token"
            )
    
    try:
        result = create_repo(
            repo_id=normalized_repo_id,
            token=token,
            private=private,
            repo_type=_atomgit_repo_type(repo_type),
            exist_ok=exist_ok,
        )
        return result
    except Exception as e:
        converted = _sdk_error(e, "创建仓库", repo_id)
        if isinstance(converted, AtomGitRepositoryExistsError) and exist_ok:
            return f"https://atomgit.com/{repo_id}"
        raise converted from e


def load_dataset(
    path: str,
    name: Optional[str] = None,
    data_dir: Optional[str] = None,
    data_files: Optional[Union[str, List[str], Dict]] = None,
    split: Optional[str] = None,
    cache_dir: Optional[Union[str, Path]] = None,
    token: Optional[str] = None,
    streaming: bool = False,
    revision: Optional[str] = None,
    **kwargs
) -> Any:
    """
    从AtomGit Hub加载数据集
    
    参数:
        path (str): 数据集路径，格式为 "username/dataset-name"
        name (str, 可选): 数据集名称
        data_dir (str, 可选): 数据目录路径
        data_files (str, List[str], Dict, 可选): 数据文件
        split (str, 可选): 数据集分割，如 "train", "test", "validation"
        cache_dir (str 或 Path, 可选): 缓存目录路径，默认使用HF_DATASETS_CACHE
        token (str, 可选): 认证token，如果为None则尝试使用保存的token
        streaming (bool, 可选): 是否以流式方式加载数据集，默认False
        revision (str, 可选): 指定版本/分支/标签，默认为 "main"
        **kwargs: 其他传递给load_dataset的参数
    
    返回:
        Dataset或DatasetDict: 加载的数据集对象
    
    示例:
        >>> from atomgit_hub import load_dataset
        >>> dataset = load_dataset("wuyw/my-dataset", split="train")
        >>> dataset = load_dataset("wuyw/my-dataset", streaming=True)
    
    异常:
        ImportError: 如果datasets库未安装
        Exception: 各种下载和认证错误
    """
    # 检查数据集支持
    if not DATASET_SUPPORT:
        raise ImportError("数据集功能需要安装datasets库。请运行: pip install datasets")
    
    # 标准化数据集路径（处理三层格式）
    normalized_path = _normalize_repo_id(path)
    
    # 如果没有提供token，尝试使用保存的token
    if token is None:
        token = _get_token()
    
    # 设置缓存目录
    if cache_dir is None:
        cache_dir = HF_DATASETS_CACHE
    
    snapshot_kwargs = {
        'repo_id': normalized_path,
        'repo_type': 'dataset',
        'token': token,
        'revision': revision,
    }
    if cache_dir is not None:
        snapshot_kwargs['cache_dir'] = str(cache_dir)

    def collect_patterns(value):
        if isinstance(value, str):
            return [value] if not os.path.isabs(value) and '://' not in value else []
        if isinstance(value, dict):
            patterns = []
            for item in value.values():
                patterns.extend(collect_patterns(item))
            return patterns
        if isinstance(value, (list, tuple)):
            patterns = []
            for item in value:
                patterns.extend(collect_patterns(item))
            return patterns
        return []

    allow_patterns = collect_patterns(data_files)
    if data_dir is not None:
        allow_patterns = [
            f"{data_dir.rstrip('/')}/{pattern.lstrip('/')}"
            for pattern in allow_patterns
        ]
    if allow_patterns:
        snapshot_kwargs['allow_patterns'] = allow_patterns

    try:
        local_dataset_path = run_download_with_retry(
            lambda: hf_snapshot_download(
                **{k: v for k, v in snapshot_kwargs.items() if v is not None}
            )
        )
    except Exception as e:
        raise _sdk_error(e, "下载数据集", path) from e

    # datasets 4.4.1 cannot discover AtomGit repositories directly, but it can
    # infer supported formats from a local Hub snapshot.
    load_kwargs = {
        'path': str(local_dataset_path),
        'cache_dir': str(cache_dir) if cache_dir else None,
        'streaming': streaming,
    }
    
    # 添加可选参数
    if name is not None:
        load_kwargs['name'] = name
    if data_dir is not None:
        load_kwargs['data_dir'] = data_dir
    if data_files is not None:
        load_kwargs['data_files'] = data_files
    if split is not None:
        load_kwargs['split'] = split
    # 合并额外的关键字参数
    load_kwargs.update(kwargs)
    
    try:
        dataset = ds_load_dataset(**{k: v for k, v in load_kwargs.items() if v is not None})
        return dataset
    except Exception as e:
        error_msg = str(e)
        if isinstance(e, ImportError) or "No module named" in error_msg:
            raise ImportError("数据集功能需要安装datasets库。请运行: pip install datasets")
        raise _sdk_error(e, "加载数据集", path) from e


# 为了兼容性，导出常用函数
__all__ = [
    'AtomGitError',
    'AtomGitAuthenticationError',
    'AtomGitRepositoryNotFoundError',
    'AtomGitRepositoryExistsError',
    'AtomGitRevisionNotFoundError',
    'AtomGitTimeoutError',
    'AtomGitNetworkError',
    'AtomGitUnsupportedError',
    'snapshot_download',
    'hub_download_url', 
    'download_file',
    'upload_folder',
    'create_repository',
    'load_dataset',
]
