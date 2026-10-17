"""Ordinary upload dependency and process-global progress policy."""

import os
import threading
from contextlib import contextmanager

from huggingface_hub import HfApi, close_session
from huggingface_hub import constants as hf_constants
from huggingface_hub.utils import (
    are_progress_bars_disabled,
    disable_progress_bars,
    enable_progress_bars,
)

from ...infrastructure.runtime import ATOMGIT_HF_ENDPOINT

upload_folder = HfApi(endpoint=ATOMGIT_HF_ENDPOINT).upload_folder
hf_upload_file = HfApi(endpoint=ATOMGIT_HF_ENDPOINT).upload_file

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
    client = HfApi(endpoint=ATOMGIT_HF_ENDPOINT, token=token)
    original_create_commit = client.create_commit

    def create_commit_with_workers(*args, **call_kwargs):
        call_kwargs["num_threads"] = num_workers
        return original_create_commit(*args, **call_kwargs)

    client.create_commit = create_commit_with_workers
    return client.upload_folder(**kwargs)


_UPLOAD_STATE_LOCK = threading.RLock()


def _reset_upload_state_lock():
    global _UPLOAD_STATE_LOCK
    _UPLOAD_STATE_LOCK = threading.RLock()


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_reset_upload_state_lock)


@contextmanager
def _serialized_upload():
    # ponytail: serialize ordinary calls while HF owns global timeout/progress;
    # use per-request clients if the locked library gains isolated settings.
    with _UPLOAD_STATE_LOCK:
        yield


@contextmanager
def _scoped_upload_settings(timeout, progress=None):
    """Apply timeout to a fresh HTTP session and restore settings on every exit."""
    with _serialized_upload():
        original_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT
        original_progress = _capture_progress_bar_state()
        try:
            hf_constants.DEFAULT_REQUEST_TIMEOUT = timeout
            close_session()
            if progress is not None:
                _set_progress_bar(progress)
            yield
        finally:
            hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
            close_session()
            _restore_progress_bar_state(original_progress)
