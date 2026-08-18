"""Ordinary CLI upload dependencies and process-global progress policy."""

from huggingface_hub import HfApi, upload_folder
from huggingface_hub.utils import (
    are_progress_bars_disabled,
    disable_progress_bars,
    enable_progress_bars,
)

try:
    from huggingface_hub.utils.tqdm import progress_bar_states
except ImportError:
    progress_bar_states = None


def _set_progress_bar(enabled: bool) -> None:
    """控制 Hugging Face Hub 上传过程中的进度条显示。

    注意：此为进程级全局状态（HF Hub 的设计）。
    - enabled=True  时显式开启进度条（防御性兜底，覆盖任何先前禁用）；
    - enabled=False 时关闭进度条（适用于日志/CI 等非交互场景）。

    若环境变量 HF_HUB_DISABLE_PROGRESS_BARS=1 在 import 前已设置，则其优先级最高，
    程序化开关将被忽略（HF Hub 既定行为）。
    """
    try:
        if enabled:
            enable_progress_bars()
        else:
            disable_progress_bars()
    except Exception:
        # 进度条控制不应影响上传主流程
        pass


def _capture_progress_bar_state():
    if progress_bar_states is not None:
        return dict(progress_bar_states)
    return are_progress_bars_disabled()


def _restore_progress_bar_state(state) -> None:
    if progress_bar_states is not None and isinstance(state, dict):
        progress_bar_states.clear()
        progress_bar_states.update(state)
        return
    _set_progress_bar(not state)


def _upload_folder_with_workers(upload_kwargs: dict, num_workers: int = 5):
    """Call HF upload_folder while honoring the requested commit thread count."""
    if num_workers == 5:
        return upload_folder(**upload_kwargs)
    kwargs = dict(upload_kwargs)
    token = kwargs.pop("token", None)
    client = HfApi(token=token)
    original_create_commit = client.create_commit

    def create_commit_with_workers(*args, **call_kwargs):
        call_kwargs["num_threads"] = num_workers
        return original_create_commit(*args, **call_kwargs)

    client.create_commit = create_commit_with_workers
    return client.upload_folder(**kwargs)
