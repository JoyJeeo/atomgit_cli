#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AtomGit Hub SDK - 类似huggingface_hub的SDK接口

这个模块提供了类似huggingface_hub的编程接口，
让用户可以通过Python代码直接使用AtomGit平台的功能。
"""

import os
from typing import Optional, Union, List, Dict, Any
from pathlib import Path

# 设置Hugging Face Hub的API端点为AtomGit
os.environ["HF_ENDPOINT"] = "https://hub.atomgit.com"
# 设置缓存目录
cache_dir = os.path.expanduser("~/.cache/atomgit")
os.makedirs(cache_dir, exist_ok=True)
os.environ["HF_HOME"] = cache_dir

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
except ImportError:
    try:
        from config import config
    except ImportError:
        from atomgit.config import config


def _normalize_repo_id(repo_id: str) -> str:
    """标准化仓库ID，处理三层格式转换"""
    parts = repo_id.split('/')
    
    # 如果是三层格式（如 wuyw/Qwen3-Reranker/0.6B-test）
    # 转换为特殊格式（如 wuyw-Qwen3-Reranker/0.6B-test）
    if len(parts) >= 3:
        # 只编码第一个斜杠，保留后面的斜杠
        first_part = parts[0]
        second_part = parts[1]
        remaining_parts = parts[2:]
        
        # 构建新格式：第一部分-第二部分/其余部分
        normalized = first_part + '-' + second_part
        if remaining_parts:
            normalized += '/' + '/'.join(remaining_parts)
        
        return normalized
    
    # 二层或单层格式直接返回
    return repo_id


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
    
    # 其他参数
    kwargs.update({
        'local_dir_use_symlinks': local_dir_use_symlinks,
        'library_name': library_name or "atomgit_hub",
        'library_version': library_version,
        'user_agent': user_agent,
        'proxies': proxies,
        'etag_timeout': etag_timeout,
        'resume_download': resume_download,
        'force_download': force_download,
        'local_files_only': local_files_only,
        'allow_patterns': allow_patterns,
        'ignore_patterns': ignore_patterns,
        'max_workers': max_workers,
        'tqdm_class': tqdm_class,
    })
    
    try:
        # 使用token下载
        result = hf_snapshot_download(**{k: v for k, v in kwargs.items() if v is not None})
        return result
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg:
            raise Exception(f"认证失败：{error_msg}。请检查token是否正确，或使用 'atomgit login' 重新登录。")
        elif "404" in error_msg:
            raise Exception(f"仓库不存在：{repo_id}。请检查仓库名称是否正确。")
        else:
            raise Exception(f"下载失败：{error_msg}")


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
        repo_type (str, 可选): 仓库类型
    
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
        result = hf_hub_download(**{k: v for k, v in kwargs.items() if v is not None})
        return result
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg:
            raise Exception(f"认证失败：{error_msg}")
        elif "404" in error_msg:
            raise Exception(f"文件不存在：{repo_id}/{filename}")
        else:
            raise Exception(f"下载失败：{error_msg}")


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
) -> str:
    """
    上传文件夹到AtomGit Hub
    
    参数:
        folder_path (str 或 Path): 本地文件夹路径
        repo_id (str): 仓库ID
        token (str, 可选): 认证token
        repo_type (str, 可选): 仓库类型
        revision (str, 可选): 分支名
        commit_message (str, 可选): 提交消息
        commit_description (str, 可选): 提交描述
        path_in_repo (str, 可选): 在仓库中的路径，默认为根目录
        ignore_patterns (List[str], 可选): 要忽略的文件模式
    
    返回:
        str: 提交的URL或ID
    
    示例:
        >>> upload_folder("./my-model/", "username/repo-name")
        >>> upload_folder("./data/", "username/repo", path_in_repo="datasets/")
    """
    # 标准化仓库ID
    normalized_repo_id = _normalize_repo_id(repo_id)
    
    # 转换为Path对象
    folder_path = Path(folder_path)
    
    if not folder_path.exists():
        raise FileNotFoundError(f"文件夹不存在: {folder_path}")
    
    if not folder_path.is_dir():
        raise NotADirectoryError(f"路径不是目录: {folder_path}")
    
    # 如果没有提供token，尝试使用保存的token
    if token is None:
        token = _get_token()
        if token is None:
            raise Exception("上传需要认证token，请先使用 'atomgit login' 登录，或提供token参数。")
    
    # 直接使用原始目录，或者创建临时目录来重新组织结构
    import tempfile
    import shutil
    
    if path_in_repo == "./" or path_in_repo == "." or path_in_repo == "":
        # 如果要上传到根目录，直接使用源文件夹
        upload_path = str(folder_path)
    else:
        # 如果要上传到特定路径，需要重新组织目录结构
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 创建目标路径
            target_path = temp_path / path_in_repo.strip('./')
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制整个目录树
            shutil.copytree(folder_path, target_path, dirs_exist_ok=True)
            
            upload_path = str(temp_path)
    
    try:
        # 使用huggingface_hub的upload_folder上传
        commit_msg = commit_message or f"Upload folder {folder_path.name}"
        result = hf_upload_folder(
            repo_id=normalized_repo_id,
            folder_path=upload_path,
            token=token,
            commit_message=commit_msg
        )
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg:
            raise Exception(f"认证失败：{error_msg}")
        elif "404" in error_msg:
            raise Exception(f"仓库不存在：{repo_id}")
        else:
            raise Exception(f"上传失败：{error_msg}")


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
        private (bool, 可选): 是否为私有仓库，默认False
        repo_type (str, 可选): 仓库类型，默认"model"
        exist_ok (bool, 可选): 如果仓库已存在是否报错，默认False
        其他参数: 主要用于Space类型仓库
    
    返回:
        str: 仓库的URL
    """
    # 标准化仓库ID
    normalized_repo_id = _normalize_repo_id(repo_id)
    
    # 如果没有提供token，尝试使用保存的token
    if token is None:
        token = _get_token()
        if token is None:
            raise Exception("创建仓库需要认证token，请先使用 'atomgit login' 登录，或提供token参数。")
    
    try:
        result = create_repo(
            repo_id=normalized_repo_id,
            token=token,
            private=private,
            repo_type=repo_type,
            exist_ok=exist_ok,
        )
        return result
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg:
            raise Exception(f"认证失败：{error_msg}")
        elif "409" in error_msg or "exists" in error_msg.lower():
            if exist_ok:
                return f"https://atomgit.com/{repo_id}"
            else:
                raise Exception(f"仓库已存在：{repo_id}")
        else:
            raise Exception(f"创建仓库失败：{error_msg}")


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
    
    # 构建参数字典
    load_kwargs = {
        'path': normalized_path,
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
    if token is not None:
        load_kwargs['token'] = token
    if revision is not None:
        load_kwargs['revision'] = revision
    
    # 合并额外的关键字参数
    load_kwargs.update(kwargs)
    
    try:
        dataset = ds_load_dataset(**{k: v for k, v in load_kwargs.items() if v is not None})
        return dataset
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg:
            raise Exception(f"认证失败：{error_msg}。请检查token是否正确，或使用 'atomgit login' 重新登录。")
        elif "404" in error_msg:
            raise Exception(f"数据集不存在：{path}。请检查数据集路径是否正确。")
        elif "ImportError" in error_msg or "No module named" in error_msg:
            raise ImportError("数据集功能需要安装datasets库。请运行: pip install datasets")
        else:
            raise Exception(f"加载数据集失败：{error_msg}")


# 为了兼容性，导出常用函数
__all__ = [
    'snapshot_download',
    'hub_download_url', 
    'download_file',
    'upload_folder',
    'create_repository',
    'load_dataset',
]
