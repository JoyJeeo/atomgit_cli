"""Dataset loading behavior for the public Python SDK."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from huggingface_hub import snapshot_download as hf_snapshot_download

from ..infrastructure.utils import run_download_with_retry
from .common import _get_token, _normalize_repo_id
from .errors import _sdk_error

try:
    from datasets import load_dataset as ds_load_dataset  # type: ignore
    from datasets.config import HF_DATASETS_CACHE  # type: ignore

    DATASET_SUPPORT = True
except ImportError:
    DATASET_SUPPORT = False
    ds_load_dataset = None
    HF_DATASETS_CACHE = None


def _collect_patterns(value):
    if isinstance(value, str):
        return [value] if not os.path.isabs(value) and "://" not in value else []
    if isinstance(value, dict):
        patterns = []
        for item in value.values():
            patterns.extend(_collect_patterns(item))
        return patterns
    if isinstance(value, (list, tuple)):
        patterns = []
        for item in value:
            patterns.extend(_collect_patterns(item))
        return patterns
    return []


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
    **kwargs,
) -> Any:
    """Load an AtomGit dataset from a stable local Hub snapshot."""
    if not DATASET_SUPPORT:
        raise ImportError("数据集功能需要安装datasets库。请运行: pip install datasets")

    normalized_path = _normalize_repo_id(path)
    if token is None:
        token = _get_token()
    if cache_dir is None:
        cache_dir = HF_DATASETS_CACHE

    snapshot_kwargs = {
        "repo_id": normalized_path,
        "repo_type": "dataset",
        "token": token,
        "revision": revision,
    }
    if cache_dir is not None:
        snapshot_kwargs["cache_dir"] = str(cache_dir)

    allow_patterns = _collect_patterns(data_files)
    if data_dir is not None:
        allow_patterns = [
            f"{data_dir.rstrip('/')}/{pattern.lstrip('/')}"
            for pattern in allow_patterns
        ]
    if allow_patterns:
        snapshot_kwargs["allow_patterns"] = allow_patterns

    try:
        local_dataset_path = run_download_with_retry(
            lambda: hf_snapshot_download(
                **{
                    key: value
                    for key, value in snapshot_kwargs.items()
                    if value is not None
                }
            )
        )
    except Exception as error:
        raise _sdk_error(error, "下载数据集", path) from error

    load_kwargs = {
        "path": str(local_dataset_path),
        "cache_dir": str(cache_dir) if cache_dir else None,
        "streaming": streaming,
    }
    if name is not None:
        load_kwargs["name"] = name
    if data_dir is not None:
        load_kwargs["data_dir"] = data_dir
    if data_files is not None:
        load_kwargs["data_files"] = data_files
    if split is not None:
        load_kwargs["split"] = split
    load_kwargs.update(kwargs)

    try:
        return ds_load_dataset(
            **{key: value for key, value in load_kwargs.items() if value is not None}
        )
    except Exception as error:
        if isinstance(error, ImportError) or "No module named" in str(error):
            raise ImportError(
                "数据集功能需要安装datasets库。请运行: pip install datasets"
            )
        raise _sdk_error(error, "加载数据集", path) from error
