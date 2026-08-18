import errno
import hashlib
import json
import math
import multiprocessing
import ntpath  # noqa: F401
import os
import random
import shutil
import socket
import ssl  # noqa: F401
import stat
import sys
import tempfile
import threading
import time
import types
import urllib.error
import urllib.request
from contextlib import ExitStack, contextmanager  # noqa: F401
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path, PurePosixPath, PureWindowsPath  # noqa: F401
from statistics import median
from typing import List, Optional, Set  # noqa: F401
from urllib.parse import quote, urljoin, urlsplit  # noqa: F401

import httpx

try:
    from .runtime import configure_hf_environment
except ImportError:
    from runtime import configure_hf_environment

configure_hf_environment()

# isort: off -- runtime policy must precede all Hugging Face imports.
try:
    from .cli_contracts import (
        _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
        DEFAULT_UPLOAD_BATCH_SIZE,
    )
except ImportError:
    from cli_contracts import (
        _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
        DEFAULT_UPLOAD_BATCH_SIZE,
    )

import huggingface_hub._upload_large_folder as hf_large_folder  # noqa: E402
import huggingface_hub.lfs as hf_lfs  # noqa: E402
from huggingface_hub import HfApi  # noqa: E402
from huggingface_hub import close_session as close_hf_session  # noqa: E402,F401
from huggingface_hub import constants as hf_constants  # noqa: E402
from huggingface_hub import (  # noqa: E402,F401
    create_repo,
    get_hf_file_metadata,
    hf_hub_download,
    snapshot_download,
    upload_folder,
)
from huggingface_hub._local_folder import (  # noqa: E402
    get_local_upload_paths,
    read_upload_metadata,
)
from huggingface_hub.file_download import http_get as hf_http_get  # noqa: E402,F401

try:
    from .config import config
    from .download import integrity as _download_integrity
    from .download import manifest as _download_manifest
    from .download import prune as _download_prune
    from .download import resume as _download_resume
    from .download import service as _download_service
    from .download import transport as _download_transport
    from .download.service import DownloadServiceMixin
    from .lfs_pointer import (
        CanonicalLfsPointerError,
        canonical_lfs_payloads,
        run_canonical_lfs_upload,
        verify_canonical_lfs_pointers,
    )
    from .services import _delete_legacy_patch, _forward_legacy_patch
    from .services import authentication as _authentication_service
    from .services import repositories as _repository_service
    from .services.authentication import (  # noqa: F401
        _ATOMGIT_IDENTITY_MAX_JSON_BYTES,
        AuthenticationServiceMixin,
    )
    from .services.repositories import (  # noqa: F401
        _ATOMGIT_V5_API_BASE,
        _ATOMGIT_V5_MAX_JSON_BYTES,
        RepositoryServiceMixin,
        _atomgit_repo_exists,
        _atomgit_repo_type,
        _atomgit_v5_branch_commit_id,
        _atomgit_v5_commit_sha,
        _atomgit_v5_get_json,
        _atomgit_v5_repo_path,
        _atomgit_v5_request_json,
        _classify_create_repo_error,
        _is_definitive_v5_write_error,
        _repo_private_state,
        _sanitized_v5_api_error,
    )
    from .utils import (  # noqa: F401
        auth_error_kind,
        is_auth_error,
        is_supported_upload_revision,
        normalize_path_in_repo,
        normalize_repo_id,
        parse_ignore_patterns,
        run_download_with_retry,
        sanitized_download_error,
        validate_upload_path_no_symlinks,
    )
except ImportError:
    from config import config
    from download import integrity as _download_integrity
    from download import manifest as _download_manifest
    from download import prune as _download_prune
    from download import resume as _download_resume
    from download import service as _download_service
    from download import transport as _download_transport
    from download.service import DownloadServiceMixin
    from lfs_pointer import (
        CanonicalLfsPointerError,
        canonical_lfs_payloads,
        run_canonical_lfs_upload,
        verify_canonical_lfs_pointers,
    )
    from services import _delete_legacy_patch, _forward_legacy_patch
    from services import authentication as _authentication_service
    from services import repositories as _repository_service
    from services.authentication import (  # noqa: F401
        _ATOMGIT_IDENTITY_MAX_JSON_BYTES,
        AuthenticationServiceMixin,
    )
    from services.repositories import (  # noqa: F401
        _ATOMGIT_V5_API_BASE,
        _ATOMGIT_V5_MAX_JSON_BYTES,
        RepositoryServiceMixin,
        _atomgit_repo_exists,
        _atomgit_repo_type,
        _atomgit_v5_branch_commit_id,
        _atomgit_v5_commit_sha,
        _atomgit_v5_get_json,
        _atomgit_v5_repo_path,
        _atomgit_v5_request_json,
        _classify_create_repo_error,
        _is_definitive_v5_write_error,
        _repo_private_state,
        _sanitized_v5_api_error,
    )
    from utils import (  # noqa: F401
        auth_error_kind,
        is_auth_error,
        is_supported_upload_revision,
        normalize_path_in_repo,
        normalize_repo_id,
        parse_ignore_patterns,
        run_download_with_retry,
        sanitized_download_error,
        validate_upload_path_no_symlinks,
    )

_DOWNLOAD_OWNER_EXPORTS = {
    "_atomgit_hf_endpoint": _download_transport,
    "_atomgit_resolve_url": _download_transport,
    "DownloadChecksumMismatchError": _download_integrity,
    "DownloadChecksumMetadataError": _download_integrity,
    "_atomgit_file_checksum": _download_integrity,
    "_checksum_from_hf_metadata": _download_integrity,
    "_checksum_from_metadata_values": _download_integrity,
    "_atomgit_file_download_metadata": _download_integrity,
    "_verify_download_checksum": _download_integrity,
    "_resume_cache_root": _download_resume,
    "_DOWNLOAD_MANIFEST_VERSION": _download_manifest,
    "_DOWNLOAD_MANIFEST_MAX_BYTES": _download_manifest,
    "_set_private_file_mode": _download_manifest,
    "_download_manifest_root": _download_manifest,
    "_download_manifest_path": _download_manifest,
    "_load_download_manifest": _download_manifest,
    "_write_download_manifest": _download_manifest,
    "_windows_file_lock_module": _download_manifest,
    "_try_lock_download_manifest_descriptor_windows": _download_manifest,
    "_unlock_download_manifest_descriptor_windows": _download_manifest,
    "_try_lock_download_manifest_descriptor": _download_manifest,
    "_unlock_download_manifest_descriptor": _download_manifest,
    "_download_manifest_lock": _download_manifest,
    "_resume_cache_identity": _download_resume,
    "_process_is_running": _download_resume,
    "_resume_download_lock": _download_resume,
    "_copy_resumed_file_to_destination": _download_resume,
    "_parse_content_range": _download_resume,
    "_atomgit_resume_raw": _download_resume,
    "_download_atomgit_file_resumable": _download_resume,
    "_atomgit_list_repo_files": _download_service,
    "_repository_filename_parts": _download_prune,
    "_safe_download_destination": _download_service,
    "_WindowsFileAPI": _download_prune,
    "_normalized_windows_handle_path": _download_prune,
    "_prune_managed_download_file_windows": _download_prune,
    "_uses_windows_prune": _download_prune,
    "_prune_managed_download_file": _download_prune,
    "_prune_managed_download_files": _download_prune,
    "_atomgit_resolve_url_raw": _download_transport,
    "_download_url_origin": _download_transport,
    "_prepare_download_redirect": _download_transport,
    "_AtomGitRedirectHandler": _download_transport,
    "_atomgit_open_url": _download_transport,
    "_atomgit_raw_http_request": _download_transport,
    "_atomgit_raw_http_get": _download_transport,
    "_atomgit_raw_http_head": _download_transport,
    "_raw_metadata_size": _download_integrity,
    "_atomgit_file_download_metadata_raw": _download_integrity,
    "_copy_exact_http_body": _download_transport,
    "_read_chunk_line": _download_transport,
    "_copy_chunked_http_body": _download_transport,
    "_copy_framed_http_body": _download_transport,
    "_atomgit_download_raw": _download_transport,
    "_download_atomgit_file": _download_transport,
}
for _download_name, _download_owner in _DOWNLOAD_OWNER_EXPORTS.items():
    globals()[_download_name] = getattr(_download_owner, _download_name)

# These exact aliases are consumed by unextracted upload/LFS code below and
# keep its historical static resolution explicit.
_atomgit_file_checksum = _download_integrity._atomgit_file_checksum
_atomgit_hf_endpoint = _download_transport._atomgit_hf_endpoint
_atomgit_open_url = _download_transport._atomgit_open_url
_atomgit_resolve_url = _download_transport._atomgit_resolve_url

# Shared repository policy remains the historical canonical old-path object.
_is_not_found_error = _repository_service._is_not_found_error
# isort: on

try:
    # 单文件上传专用：直接以 path_or_fileobj 上传，避免本地拷贝
    from huggingface_hub import upload_file as hf_upload_file
except ImportError:  # 老版本兜底
    hf_upload_file = None

try:
    # huggingface_hub >= 0.14 提供的进度条程序化开关
    from huggingface_hub.utils import (
        are_progress_bars_disabled,
        disable_progress_bars,
        enable_progress_bars,
        filter_repo_objects,
    )
    try:
        from huggingface_hub.utils.tqdm import progress_bar_states
    except ImportError:
        progress_bar_states = None
except ImportError:  # 老版本无此 API 时，提供 no-op 回退，保证可用
    progress_bar_states = None

    def are_progress_bars_disabled(*args, **kwargs):
        return False

    def enable_progress_bars(*args, **kwargs):
        pass

    def disable_progress_bars(*args, **kwargs):
        pass

    def filter_repo_objects(items, *, ignore_patterns=None, key=None, **kwargs):
        return items


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













































_RESUMABLE_COMMIT_MAX_ATTEMPTS = 5
_RESUMABLE_COMMIT_BACKOFF_BASE = 30.0
_RESUMABLE_COMMIT_BACKOFF_CAP = 300.0
_RESUMABLE_COMMIT_BATCH_SIZES = (20, 10, 5, 2, 1)
_RESUMABLE_LFS_PREUPLOAD_MAX_ATTEMPTS = 3
_RESUMABLE_LFS_PREUPLOAD_BACKOFF_BASE = 2.0
_RESUMABLE_LFS_PREUPLOAD_WAIT_CAP = 60.0
_RESUMABLE_LFS_ERROR_BODY_MAX_BYTES = 16 * 1024
_SLOW_FLOW_SAMPLE_SECONDS = 5.0
_SLOW_FLOW_WINDOW_SECONDS = 30.0
_SLOW_FLOW_REQUIRED_WINDOWS = 3
_SLOW_FLOW_MAX_REPLACEMENTS = 3
_SLOW_FLOW_REPLACEMENT_COOLDOWNS = (0.0, 60.0, 180.0)
_SLOW_FLOW_STREAM_CHUNK_BYTES = 512 * 1024
# HF Hub 1.1.7 documents a 1 GB regular-file commit payload limit. Files above
# it must be selected as LFS by the repository policy before commit encoding.
_RESUMABLE_REGULAR_FILE_MAX_BYTES = 1_000_000_000
_RESUMABLE_LFS_PATTERN_MAX_COUNT = 32
_RESUMABLE_LFS_PATTERN_MAX_EXTENSION = 32
_LFS_GITATTRIBUTES_MAX_BYTES = 1024 * 1024
_LFS_GITATTRIBUTES_MAX_ATTEMPTS = 3
_LFS_GITATTRIBUTES_PATH = ".gitattributes"


def _slow_flow_stable_baseline(speeds) -> Optional[float]:
    """Return a median when three speeds stay within the accepted 20% band."""
    values = tuple(float(speed) for speed in speeds)
    if len(values) != _SLOW_FLOW_REQUIRED_WINDOWS or any(
        not math.isfinite(speed) or speed <= 0 for speed in values
    ):
        return None
    if all(
        abs(current - previous) <= previous * 0.2
        for previous, current in zip(values, values[1:])
    ):
        return float(median(values))
    return None


def _slow_flow_peer_baseline(windows) -> Optional[float]:
    """Return a stable three-window peer median with at least two peers in-band."""
    peer_windows = tuple(tuple(float(speed) for speed in row) for row in windows)
    if len(peer_windows) != _SLOW_FLOW_REQUIRED_WINDOWS:
        return None
    medians = []
    for speeds in peer_windows:
        if len(speeds) < 2 or any(
            not math.isfinite(speed) or speed <= 0 for speed in speeds
        ):
            return None
        window_median = float(median(speeds))
        lower = window_median * 0.7
        upper = window_median * 1.3
        if sum(lower <= speed <= upper for speed in speeds) < 2:
            return None
        medians.append(window_median)
    return _slow_flow_stable_baseline(medians)


@dataclass(frozen=True)
class _SlowFlowDecision:
    object_key: object
    replacement_number: int
    delay: float
    probe: bool


@dataclass
class _SlowFlowState:
    total_bytes: int
    speeds: list = field(default_factory=list)
    stable_baseline: Optional[float] = None
    current_speed: Optional[float] = None
    slow_windows: int = 0
    degraded_windows: int = 0
    replacements: int = 0
    last_replacement_at: Optional[float] = None
    awaiting_improvement: bool = False
    replaced_speed: Optional[float] = None
    fresh_speeds: list = field(default_factory=list)
    disabled: bool = False
    active: bool = True
    probe: bool = False


class _SlowFlowCoordinator:
    """Coordinate conservative, object-scoped slow-flow replacement decisions."""

    def __init__(
        self,
        *,
        monotonic=time.monotonic,
        reconnect_jitter=None,
        deadline=None,
        event_callback=None,
    ):
        self._monotonic = monotonic
        self._reconnect_jitter = reconnect_jitter or (
            lambda: random.uniform(2.0, 8.0)
        )
        self._deadline = deadline
        self._event_callback = event_callback
        self._states = {}
        self._probe_key = None
        self._lock = threading.Lock()

    def _emit(self, kind: str, **details) -> None:
        if self._event_callback is None:
            return
        try:
            self._event_callback({"kind": kind, **details})
        except Exception:
            pass

    def register(self, object_key, *, total_bytes: int) -> None:
        if not isinstance(total_bytes, int) or isinstance(total_bytes, bool) or total_bytes < 0:
            raise ValueError("LFS object size is invalid")
        with self._lock:
            state = self._states.get(object_key)
            if state is None:
                self._states[object_key] = _SlowFlowState(total_bytes=total_bytes)
            else:
                state.active = True
                if state.total_bytes != total_bytes:
                    raise RuntimeError("LFS object size changed during upload")

    def complete(self, object_key, *, reset_windows: bool = False) -> None:
        with self._lock:
            state = self._states.get(object_key)
            if state is not None:
                state.active = False
                if reset_windows:
                    state.speeds.clear()
                    state.stable_baseline = None
                    state.current_speed = None
                    state.slow_windows = 0
                    state.degraded_windows = 0
                    state.awaiting_improvement = False
                    state.replaced_speed = None
                    state.fresh_speeds.clear()
                    state.probe = False
                if self._probe_key == object_key:
                    self._probe_key = None

    def replacement_count(self, object_key) -> int:
        with self._lock:
            state = self._states.get(object_key)
            return state.replacements if state is not None else 0

    def is_disabled(self, object_key) -> bool:
        with self._lock:
            state = self._states.get(object_key)
            return state.disabled if state is not None else False

    def replacement_finished(self, object_key) -> None:
        with self._lock:
            state = self._states.get(object_key)
            if state is None:
                return
            state.awaiting_improvement = True
            state.fresh_speeds.clear()
            state.slow_windows = 0
            state.degraded_windows = 0

    def _peer_baseline(self, object_key) -> Optional[float]:
        peers = [
            state for key, state in self._states.items()
            if key != object_key and state.active and len(state.speeds) >= 3
        ]
        if len(peers) < 2:
            return None
        windows = tuple(
            tuple(state.speeds[-offset] for state in peers)
            for offset in (3, 2, 1)
        )
        return _slow_flow_peer_baseline(windows)

    def _collective_slowdown(self) -> bool:
        active = [state for state in self._states.values() if state.active]
        return (
            len(active) >= 2
            and all(
                state.stable_baseline is not None
                and state.current_speed is not None
                and state.current_speed <= state.stable_baseline * 0.3
                and state.degraded_windows >= _SLOW_FLOW_REQUIRED_WINDOWS
                for state in active
            )
        )

    def _collective_candidate(self) -> bool:
        active = [state for state in self._states.values() if state.active]
        return (
            len(active) >= 2
            and all(
                state.stable_baseline is not None
                and state.current_speed is not None
                and state.current_speed <= state.stable_baseline * 0.3
                and state.degraded_windows >= _SLOW_FLOW_REQUIRED_WINDOWS - 1
                for state in active
            )
        )

    def _replacement_delay(self, state: _SlowFlowState, now: float) -> float:
        if state.replacements == 0:
            return min(8.0, max(2.0, float(self._reconnect_jitter())))
        cooldown = _SLOW_FLOW_REPLACEMENT_COOLDOWNS[state.replacements]
        available_at = (state.last_replacement_at or now) + cooldown
        return max(0.0, available_at - now)

    def _decide(
        self,
        object_key,
        state: _SlowFlowState,
        *,
        speed: float,
        remaining_bytes: int,
        retransmit_bytes: int,
        expected_speed: float,
        probe: bool,
    ) -> Optional[_SlowFlowDecision]:
        if state.disabled or state.replacements >= _SLOW_FLOW_MAX_REPLACEMENTS:
            state.disabled = True
            return None
        now = self._monotonic()
        delay = self._replacement_delay(state, now)
        continue_time = remaining_bytes / speed
        replace_time = delay + (retransmit_bytes / expected_speed)
        if continue_time < 2.0 * replace_time:
            return None
        if self._deadline is not None and now + replace_time >= self._deadline:
            return None
        if probe and self._probe_key is not None:
            return None
        state.replacements += 1
        state.last_replacement_at = now + delay
        state.replaced_speed = speed
        state.slow_windows = 0
        state.degraded_windows = 0
        state.probe = probe
        if probe:
            self._probe_key = object_key
        decision = _SlowFlowDecision(
            object_key=object_key,
            replacement_number=state.replacements,
            delay=delay,
            probe=probe,
        )
        self._emit(
            "lfs_slow_flow_replace",
            replacement=state.replacements,
            delay=delay,
            probe=probe,
        )
        return decision

    def observe_window(
        self,
        object_key,
        speed: float,
        remaining_bytes: int,
        retransmit_bytes: Optional[int] = None,
    ) -> Optional[_SlowFlowDecision]:
        if (
            not math.isfinite(speed)
            or speed <= 0
            or not isinstance(remaining_bytes, int)
            or isinstance(remaining_bytes, bool)
            or remaining_bytes < 0
        ):
            return None
        with self._lock:
            state = self._states.get(object_key)
            if state is None:
                raise RuntimeError("LFS object is not registered")
            if state.disabled or not state.active:
                return None

            prior_baseline = state.stable_baseline
            state.current_speed = speed
            state.speeds.append(speed)
            if len(state.speeds) > 12:
                del state.speeds[:-12]

            if state.awaiting_improvement:
                state.fresh_speeds.append(speed)
                if len(state.fresh_speeds) < _SLOW_FLOW_REQUIRED_WINDOWS:
                    return None
                improved = float(median(state.fresh_speeds[-3:]))
                replaced_speed = state.replaced_speed or 0.0
                peer_baseline = self._peer_baseline(object_key)
                state.awaiting_improvement = False
                state.fresh_speeds.clear()
                if (
                    improved < replaced_speed * 2.0
                    or (
                        peer_baseline is not None
                        and improved < peer_baseline * 0.7
                    )
                ):
                    state.disabled = True
                    if self._probe_key == object_key:
                        self._probe_key = None
                    self._emit("lfs_slow_flow_disabled", reason="no_improvement")
                    return None
                state.stable_baseline = improved
                state.speeds = [improved] * 3
                if self._probe_key == object_key:
                    self._probe_key = None
                state.probe = False
                return None

            if prior_baseline is None and len(state.speeds) >= 3:
                state.stable_baseline = _slow_flow_stable_baseline(state.speeds[-3:])
                prior_baseline = state.stable_baseline

            if prior_baseline is None:
                return None
            if speed <= prior_baseline * 0.3:
                state.degraded_windows += 1
            else:
                state.degraded_windows = 0

            peer_baseline = self._peer_baseline(object_key)
            if peer_baseline is not None:
                slow = speed <= peer_baseline * 0.3 and speed <= prior_baseline * 0.5
                expected_speed = peer_baseline
            else:
                slow = speed <= prior_baseline * 0.3
                expected_speed = prior_baseline
            state.slow_windows = state.slow_windows + 1 if slow else 0

            retransmit = state.total_bytes if retransmit_bytes is None else retransmit_bytes
            if self._collective_slowdown():
                return self._decide(
                    object_key,
                    state,
                    speed=speed,
                    remaining_bytes=remaining_bytes,
                    retransmit_bytes=retransmit,
                    expected_speed=prior_baseline,
                    probe=True,
                )
            if self._collective_candidate():
                return None
            if self._probe_key is not None:
                return None
            if state.slow_windows < _SLOW_FLOW_REQUIRED_WINDOWS:
                if not slow:
                    recent_baseline = _slow_flow_stable_baseline(
                        state.speeds[-3:]
                    )
                    if recent_baseline is not None:
                        state.stable_baseline = recent_baseline
                return None
            return self._decide(
                object_key,
                state,
                speed=speed,
                remaining_bytes=remaining_bytes,
                retransmit_bytes=retransmit,
                expected_speed=expected_speed,
                probe=False,
            )


class _SlowFlowReconnect(RuntimeError):
    """Internal control signal that closes only the current LFS PUT."""

    def __init__(self, decision: _SlowFlowDecision):
        self.decision = decision
        super().__init__("replace slow LFS flow")


class _SlowFlowPayload:
    """Measure network-paced payload consumption without exposing object identity."""

    def __init__(
        self,
        fileobj,
        *,
        coordinator: _SlowFlowCoordinator,
        object_key,
        total_bytes: int,
        confirmed_bytes: int = 0,
        retransmit_bytes: Optional[int] = None,
        monotonic=time.monotonic,
    ):
        self._fileobj = fileobj
        self._coordinator = coordinator
        self._object_key = object_key
        self._total_bytes = total_bytes
        self._confirmed_bytes = confirmed_bytes
        self._retransmit_bytes = retransmit_bytes
        self._monotonic = monotonic
        self._last_read_end = monotonic()
        self._sample_elapsed = 0.0
        self._sample_bytes = 0
        self._window_elapsed = 0.0
        self._window_bytes = 0
        self._delivered_bytes = 0

    def __getattr__(self, name):
        return getattr(self._fileobj, name)

    def __iter__(self):
        while True:
            data = self.read(_SLOW_FLOW_STREAM_CHUNK_BYTES)
            if not data:
                return
            yield data

    def read(self, size=-1):
        read_start = self._monotonic()
        paced_elapsed = max(0.0, read_start - self._last_read_end)
        self._sample_elapsed += paced_elapsed
        if self._sample_elapsed >= _SLOW_FLOW_SAMPLE_SECONDS:
            self._window_elapsed += self._sample_elapsed
            self._window_bytes += self._sample_bytes
            self._sample_elapsed = 0.0
            self._sample_bytes = 0
            if self._window_elapsed >= _SLOW_FLOW_WINDOW_SECONDS:
                speed = self._window_bytes / self._window_elapsed
                remaining = max(
                    0,
                    self._total_bytes
                    - self._confirmed_bytes
                    - self._delivered_bytes,
                )
                decision = self._coordinator.observe_window(
                    self._object_key,
                    speed,
                    remaining,
                    self._retransmit_bytes,
                )
                self._window_elapsed = 0.0
                self._window_bytes = 0
                if decision is not None:
                    raise _SlowFlowReconnect(decision)
        data = self._fileobj.read(size)
        self._last_read_end = self._monotonic()
        if data:
            length = len(data)
            self._sample_bytes += length
            self._delivered_bytes += length
        return data


def _lfs_source_identity(operation):
    source = getattr(operation, "path_or_fileobj", None)
    if isinstance(source, (str, Path)):
        info = Path(source).stat()
        return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
    upload_info = getattr(operation, "upload_info", None)
    return (
        getattr(upload_info, "size", None),
        getattr(upload_info, "sha256", None),
        id(source),
    )


def _lfs_object_key(operation) -> bytes:
    digest = getattr(getattr(operation, "upload_info", None), "sha256", None)
    if not isinstance(digest, bytes) or len(digest) != 32:
        raise RuntimeError("LFS object identity is invalid")
    return digest


class _ResumableLfsTransferController:
    """Replace only internally classified slow basic or multipart PUTs."""

    def __init__(
        self,
        *,
        coordinator: _SlowFlowCoordinator,
        http_backoff=hf_lfs.http_backoff,
        raise_for_status=hf_lfs.hf_raise_for_status,
        get_session=hf_lfs.get_session,
        sleep=time.sleep,
    ):
        self._coordinator = coordinator
        self._http_backoff = http_backoff
        self._raise_for_status = raise_for_status
        self._get_session = get_session
        self._sleep = sleep

    def _wait_for_replacement(self, operation, identity, reconnect) -> None:
        if _lfs_source_identity(operation) != identity:
            raise RuntimeError("LFS source changed during upload")
        self._sleep(reconnect.decision.delay)
        self._coordinator.replacement_finished(reconnect.decision.object_key)

    def upload_single_part(self, operation, upload_url: str) -> None:
        object_key = _lfs_object_key(operation)
        total_bytes = operation.upload_info.size
        identity = _lfs_source_identity(operation)
        self._coordinator.register(object_key, total_bytes=total_bytes)
        succeeded = False
        try:
            while True:
                try:
                    with operation.as_file(with_tqdm=True) as fileobj:
                        payload = _SlowFlowPayload(
                            fileobj,
                            coordinator=self._coordinator,
                            object_key=object_key,
                            total_bytes=total_bytes,
                            retransmit_bytes=total_bytes,
                        )
                        response = self._http_backoff(
                            "PUT", upload_url, data=payload, max_retries=0
                        )
                        self._raise_for_status(response)
                    if _lfs_source_identity(operation) != identity:
                        raise RuntimeError("LFS source changed during upload")
                    succeeded = True
                    return
                except _SlowFlowReconnect as reconnect:
                    self._wait_for_replacement(operation, identity, reconnect)
        finally:
            self._coordinator.complete(
                object_key, reset_windows=not succeeded
            )

    def upload_multi_part(
        self, operation, header: dict, chunk_size: int, upload_url: str
    ) -> None:
        sorted_urls = hf_lfs._get_sorted_parts_urls(
            header=header,
            upload_info=operation.upload_info,
            chunk_size=chunk_size,
        )
        object_key = _lfs_object_key(operation)
        total_bytes = operation.upload_info.size
        identity = _lfs_source_identity(operation)
        response_headers = []
        self._coordinator.register(object_key, total_bytes=total_bytes)
        succeeded = False
        try:
            for part_index, part_url in enumerate(sorted_urls):
                confirmed_bytes = min(part_index * chunk_size, total_bytes)
                retransmit_bytes = total_bytes - confirmed_bytes
                while True:
                    try:
                        with operation.as_file(with_tqdm=True) as fileobj:
                            with hf_lfs.SliceFileObj(
                                fileobj,
                                seek_from=confirmed_bytes,
                                read_limit=chunk_size,
                            ) as part:
                                payload = _SlowFlowPayload(
                                    part,
                                    coordinator=self._coordinator,
                                    object_key=object_key,
                                    total_bytes=total_bytes,
                                    confirmed_bytes=confirmed_bytes,
                                    retransmit_bytes=retransmit_bytes,
                                )
                                response = self._http_backoff(
                                    "PUT", part_url, data=payload,
                                    max_retries=0,
                                )
                                self._raise_for_status(response)
                        if _lfs_source_identity(operation) != identity:
                            raise RuntimeError("LFS source changed during upload")
                        etag = response.headers.get("etag")
                        if not isinstance(etag, str) or not etag:
                            raise ValueError("Invalid ETag returned for LFS part")
                        response_headers.append({"etag": etag})
                        break
                    except _SlowFlowReconnect as reconnect:
                        self._wait_for_replacement(
                            operation, identity, reconnect
                        )
            completion = self._get_session().post(
                upload_url,
                json=hf_lfs._get_completion_payload(
                    response_headers, operation.upload_info.sha256.hex()
                ),
                headers=hf_lfs.LFS_HEADERS,
            )
            self._raise_for_status(completion)
            succeeded = True
        finally:
            self._coordinator.complete(
                object_key, reset_windows=not succeeded
            )


@contextmanager
def _scoped_resumable_lfs_recovery(coordinator: _SlowFlowCoordinator):
    """Install locked HF 1.1.7 LFS hooks only for one isolated child."""
    original_single = hf_lfs._upload_single_part
    original_multi = hf_lfs._upload_multi_part
    controller = _ResumableLfsTransferController(coordinator=coordinator)
    hf_lfs._upload_single_part = controller.upload_single_part
    hf_lfs._upload_multi_part = controller.upload_multi_part
    try:
        yield controller
    finally:
        hf_lfs._upload_single_part = original_single
        hf_lfs._upload_multi_part = original_multi


def _validated_lfs_patterns(patterns) -> tuple:
    """Return a bounded canonical list of safe extension-only LFS patterns."""
    if patterns is None:
        return ()
    if not isinstance(patterns, (list, tuple, set, frozenset)):
        return ()
    if len(patterns) > _RESUMABLE_LFS_PATTERN_MAX_COUNT:
        return ()
    validated = set()
    for pattern in patterns:
        if not isinstance(pattern, str) or not pattern.startswith("*."):
            continue
        extension = pattern[2:]
        if (
            not extension
            or len(extension) > _RESUMABLE_LFS_PATTERN_MAX_EXTENSION
            or not extension.isascii()
            or not extension[0].isalnum()
            or any(
                not (character.isalnum() or character in "._+-")
                for character in extension
            )
        ):
            continue
        validated.add(f"*.{extension}")
    return tuple(sorted(validated, key=lambda pattern: (pattern.lower(), pattern)))


def _lfs_pattern_from_repo_path(path_in_repo) -> Optional[str]:
    """Infer one safe repository-wide extension pattern without local paths."""
    if not isinstance(path_in_repo, str) or not path_in_repo:
        return None
    suffix = PurePosixPath(path_in_repo).suffix
    patterns = _validated_lfs_patterns((f"*{suffix}",)) if suffix else ()
    return patterns[0] if patterns else None


def _unsafe_resumable_lfs_patterns(items) -> tuple:
    patterns = set()
    for paths, metadata in items:
        if (
            getattr(metadata, "upload_mode", None) == "regular"
            and getattr(metadata, "size", 0)
            > _RESUMABLE_REGULAR_FILE_MAX_BYTES
        ):
            pattern = _lfs_pattern_from_repo_path(
                getattr(paths, "path_in_repo", None)
            )
            if pattern is not None:
                patterns.add(pattern)
    return _validated_lfs_patterns(patterns)


def _resumable_lfs_patterns(items) -> tuple:
    """Infer safe extension rules for items already selected for LFS."""
    patterns = set()
    for paths, metadata in items:
        if (
            getattr(metadata, "upload_mode", None) == "lfs"
            and not getattr(metadata, "should_ignore", False)
        ):
            pattern = _lfs_pattern_from_repo_path(
                getattr(paths, "path_in_repo", None)
            )
            if pattern is not None:
                patterns.add(pattern)
    if len(patterns) > _RESUMABLE_LFS_PATTERN_MAX_COUNT:
        raise ResumableLfsAttributesError()
    return _validated_lfs_patterns(patterns)


class ResumableUploadModeError(RuntimeError):
    """A server-selected resumable upload mode is unsafe for the file size."""

    def __init__(self, message: str, lfs_patterns=()):
        self.lfs_patterns = _validated_lfs_patterns(lfs_patterns)
        super().__init__(message)


class ResumableLfsAttributesError(RuntimeError):
    """Server-selected LFS extensions need remote attributes verification."""

    def __init__(self, lfs_patterns=()):
        self.lfs_patterns = _validated_lfs_patterns(lfs_patterns)
        super().__init__("server-selected LFS extensions need attributes")


class ResumableTargetRevisionError(RuntimeError):
    """A requested resumable upload revision does not exist."""


_RESUMABLE_WORKER_ERROR_MESSAGES = {
    "authentication": "resumable worker authentication failed",
    "permission": "resumable worker permission check failed",
    "repository": "resumable worker repository check failed",
    "revision": "resumable worker revision check failed",
    "request": "resumable worker request validation failed",
    "payload_size": "resumable worker payload is too large",
    "lfs_quota": "resumable worker LFS storage is insufficient",
    "lfs_bandwidth": "resumable worker LFS bandwidth is insufficient",
    "lfs_batch_rejected": "resumable worker LFS batch was rejected",
    "rate_limit": "resumable worker was rate limited",
    "service_unavailable": "resumable worker service is unavailable",
    "timeout": "resumable worker timed out",
    "connection": "resumable worker connection failed",
    "upload_mode": "resumable worker upload mode is unsafe",
    "lfs_attributes": "resumable worker LFS attributes need verification",
    "lfs_pointer": "resumable worker LFS pointer verification failed",
    "client_resource": "resumable worker client resources are insufficient",
    "unknown": "resumable worker failed",
}


class ResumableWorkerError(RuntimeError):
    """A credential-safe failure reconstructed from the upload child."""

    def __init__(self, category: str, lfs_patterns=()):
        if category not in _RESUMABLE_WORKER_ERROR_MESSAGES:
            category = "unknown"
        self.category = category
        self.lfs_patterns = (
            _validated_lfs_patterns(lfs_patterns)
            if category in ("upload_mode", "lfs_attributes")
            else ()
        )
        super().__init__(_RESUMABLE_WORKER_ERROR_MESSAGES[category])


class ResumableCommitError(RuntimeError):
    """A resumable commit could not complete under the bounded retry policy."""


class ResumableLfsPreuploadError(RuntimeError):
    """A resumable LFS preupload failed under the bounded retry policy."""

    def __init__(self, category: str):
        if category not in _RESUMABLE_WORKER_ERROR_MESSAGES:
            category = "unknown"
        self.category = category
        super().__init__(_RESUMABLE_WORKER_ERROR_MESSAGES[category])


def _resumable_error_chain(error: BaseException):
    """Yield a bounded exception chain without serializing exception text."""
    current = error
    seen = set()
    for _ in range(8):
        if not isinstance(current, BaseException) or id(current) in seen:
            return
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def _resumable_error_status(error: BaseException) -> Optional[int]:
    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)
    if isinstance(status_code, int):
        return status_code
    code = getattr(error, "code", None)
    return code if isinstance(code, int) else None


def _resumable_worker_error_category(error: BaseException) -> str:
    """Reduce an arbitrary child failure to one bounded, non-sensitive code."""
    for cause in _resumable_error_chain(error):
        if isinstance(cause, ResumableWorkerError):
            return cause.category
        if isinstance(cause, ResumableUploadModeError):
            return "upload_mode"
        if isinstance(cause, ResumableLfsAttributesError):
            return "lfs_attributes"
        if isinstance(cause, ResumableLfsPreuploadError):
            return cause.category
        if isinstance(cause, CanonicalLfsPointerError):
            return "lfs_pointer"

        name = type(cause).__name__
        if name == "RevisionNotFoundError":
            return "revision"
        if name == "RepositoryNotFoundError":
            return "repository"
        if name in ("GatedRepoError", "DisabledRepoError"):
            return "permission"

        credential_error = auth_error_kind(cause)
        if credential_error in ("authentication", "permission"):
            return credential_error

        status_code = _resumable_error_status(cause)
        if status_code == 401:
            return "authentication"
        if status_code == 403:
            return "permission"
        if status_code == 404:
            return "repository"
        if status_code == 413:
            return "payload_size"
        if status_code == 429:
            return "rate_limit"
        if status_code in (500, 502, 503, 504):
            return "service_unavailable"
        if status_code == 400 or name == "BadRequestError":
            return "request"

        if isinstance(
            cause,
            (httpx.TimeoutException, TimeoutError, socket.timeout),
        ):
            return "timeout"
        if isinstance(
            cause,
            (httpx.NetworkError, ConnectionError),
        ):
            return "connection"
        if isinstance(cause, MemoryError):
            return "client_resource"
        if isinstance(cause, OSError) and cause.errno in (
            errno.EACCES,
            errno.EPERM,
            errno.EFBIG,
            errno.EMFILE,
            errno.ENFILE,
            errno.ENOMEM,
            errno.ENOSPC,
            errno.EROFS,
        ):
            return "client_resource"
    return "unknown"


def _resumable_failure_envelope(error: BaseException) -> dict:
    """Build the only error payload allowed across the process boundary."""
    category = _resumable_worker_error_category(error)
    envelope = {"category": category}
    if category in ("upload_mode", "lfs_attributes"):
        for cause in _resumable_error_chain(error):
            patterns = _validated_lfs_patterns(
                getattr(cause, "lfs_patterns", ())
            )
            if patterns:
                envelope["lfs_patterns"] = list(patterns)
                break
    return envelope


class _ResumableLfsAttributesPolicy:
    """Gate LFS work until its extension rules are confirmed remotely."""

    def __init__(self, configured_patterns=()):
        self._configured = set(_validated_lfs_patterns(configured_patterns))
        self._lock = threading.Lock()

    def validate_patterns(self, patterns) -> None:
        validated = _validated_lfs_patterns(patterns)
        with self._lock:
            missing = tuple(
                pattern for pattern in validated
                if pattern not in self._configured
            )
        if missing:
            raise ResumableLfsAttributesError(missing)

    def validate_items(self, items) -> None:
        self.validate_patterns(_resumable_lfs_patterns(items))

    def validate_operations(self, operations) -> None:
        patterns = set()
        for operation in operations:
            if getattr(operation, "_upload_mode", None) != "lfs":
                continue
            pattern = _lfs_pattern_from_repo_path(
                getattr(operation, "path_in_repo", None)
            )
            if pattern is not None:
                patterns.add(pattern)
        self.validate_patterns(patterns)


def _validate_resumable_commit_operations(operations) -> None:
    """Reject unsafe regular blobs before commit serialization reads them."""
    unsafe_operations = []
    for operation in operations:
        upload_info = getattr(operation, "upload_info", None)
        size = getattr(upload_info, "size", None)
        upload_mode = getattr(operation, "_upload_mode", None)
        if (
            upload_mode == "regular"
            and isinstance(size, int)
            and not isinstance(size, bool)
            and size > _RESUMABLE_REGULAR_FILE_MAX_BYTES
        ):
            unsafe_operations.append(operation)
    if unsafe_operations:
        patterns = _validated_lfs_patterns(
            tuple(
                filter(
                    None,
                    (
                        _lfs_pattern_from_repo_path(
                            getattr(operation, "path_in_repo", None)
                        )
                        for operation in unsafe_operations
                    ),
                )
            )
        )
        raise ResumableUploadModeError(
            "服务端将超大文件判定为 regular；请在仓库 .gitattributes "
            "中为该文件类型配置 Git LFS 后重试。",
            patterns,
        )


def _validate_resumable_upload_mode_items(items) -> None:
    """Apply the regular-file size policy immediately after preupload mode."""
    unsafe = [
        item
        for item in items
        if item[1].upload_mode == "regular"
        and item[1].size > _RESUMABLE_REGULAR_FILE_MAX_BYTES
    ]
    if unsafe:
        raise ResumableUploadModeError(
            "服务端将超大文件判定为 regular；请在仓库 .gitattributes "
            "中为该文件类型配置 Git LFS 后重试。",
            _unsafe_resumable_lfs_patterns(unsafe),
        )


def _refresh_unsafe_resumable_upload_modes(folder_path: Path) -> int:
    """Refresh only unsafe uncommitted policy fields in locked HF metadata."""
    folder_path = Path(folder_path)
    if not (folder_path / ".cache" / "huggingface" / "upload").is_dir():
        return 0
    refreshed = 0
    for file_path in folder_path.rglob("*"):
        if not file_path.is_file():
            continue
        relative_path = file_path.relative_to(folder_path).as_posix()
        if relative_path.startswith(".cache/huggingface/"):
            continue
        paths = get_local_upload_paths(folder_path, relative_path)
        if not paths.metadata_path.is_file():
            continue
        metadata = read_upload_metadata(folder_path, relative_path)
        if (
            not metadata.is_committed
            and metadata.upload_mode == "regular"
            and metadata.size > _RESUMABLE_REGULAR_FILE_MAX_BYTES
        ):
            metadata.upload_mode = None
            metadata.should_ignore = None
            metadata.remote_oid = None
            metadata.save(paths)
            refreshed += 1
    return refreshed


def _resumable_projection_lfs_patterns(folder_path: Path) -> tuple:
    """Read safe LFS extension patterns already cached in HF metadata."""
    folder_path = Path(folder_path)
    if not (folder_path / ".cache" / "huggingface" / "upload").is_dir():
        return ()
    patterns = set()
    for file_path in folder_path.rglob("*"):
        if not file_path.is_file():
            continue
        relative_path = file_path.relative_to(folder_path).as_posix()
        if relative_path.startswith(".cache/huggingface/"):
            continue
        paths = get_local_upload_paths(folder_path, relative_path)
        if not paths.metadata_path.is_file():
            continue
        metadata = read_upload_metadata(folder_path, relative_path)
        if (
            metadata.upload_mode == "lfs"
            and not metadata.should_ignore
        ):
            pattern = _lfs_pattern_from_repo_path(relative_path)
            if pattern is not None:
                patterns.add(pattern)
    if len(patterns) > _RESUMABLE_LFS_PATTERN_MAX_COUNT:
        raise ResumableLfsAttributesError()
    return _validated_lfs_patterns(patterns)


def _lfs_config_cache_root() -> Path:
    """Return a private cache root for isolated `.gitattributes` transactions."""
    hf_home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "atomgit"))
    root = hf_home / "lfs-config"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("LFS 配置缓冲目录不安全")
    os.chmod(root, 0o700)
    return root


def _lfs_gitattributes_line(pattern: str) -> bytes:
    validated = _validated_lfs_patterns((pattern,))
    if validated != (pattern,):
        raise ValueError("LFS 文件类型规则不安全，无法自动配置")
    return (
        f"{pattern} filter=lfs diff=lfs merge=lfs -text".encode("ascii")
    )


def _merge_lfs_gitattributes(content: bytes, patterns) -> tuple:
    """Append missing standard LFS lines without rewriting existing bytes."""
    if not isinstance(content, bytes):
        raise TypeError(".gitattributes content must be bytes")
    if len(content) > _LFS_GITATTRIBUTES_MAX_BYTES:
        raise ValueError("远端 .gitattributes 过大，无法安全自动修改")
    validated = _validated_lfs_patterns(patterns)
    if not validated:
        raise ValueError("无法从文件路径推导安全的 LFS 文件类型规则")

    missing = tuple(
        pattern for pattern in validated
        if not _gitattributes_contains_lfs_patterns(content, (pattern,))
    )
    if not missing:
        return content, ()

    newline = b"\r\n" if b"\r\n" in content else b"\n"
    appended = missing
    updated = content
    if updated and not updated.endswith((b"\n", b"\r")):
        updated += newline
    for pattern in appended:
        updated += _lfs_gitattributes_line(pattern) + newline
    if len(updated) > _LFS_GITATTRIBUTES_MAX_BYTES:
        raise ValueError("更新后的 .gitattributes 过大，已拒绝提交")
    return updated, appended


def _gitattributes_contains_lfs_patterns(content: bytes, patterns) -> bool:
    if not isinstance(content, bytes):
        return False
    validated = _validated_lfs_patterns(patterns)
    if not validated:
        return False
    effective = set()
    for raw_line in reversed(content.splitlines()):
        line = raw_line.rstrip(b"\r")
        if not line or line.startswith(b"#"):
            continue
        fields = line.split()
        if len(fields) != 5:
            break
        try:
            pattern = fields[0].decode("ascii")
        except UnicodeDecodeError:
            break
        if (
            _validated_lfs_patterns((pattern,)) != (pattern,)
            or line != _lfs_gitattributes_line(pattern)
        ):
            break
        effective.add(pattern)
    return all(pattern in effective for pattern in validated)


def _remote_revision_commit_sha(
    *, token: str, repo_id: str, revision: str,
    request_timeout: float,
) -> str:
    """Resolve a mutable upload revision to one immutable AtomGit commit."""
    path = _atomgit_v5_repo_path(repo_id)
    path += "/commits/" + quote(revision or "main", safe="")
    payload = _atomgit_v5_get_json(path, token, timeout=request_timeout)
    commit_sha = _atomgit_v5_commit_sha(payload)
    if commit_sha is None:
        raise ValueError("无法解析目标 revision 的当前提交")
    return commit_sha


def _download_remote_gitattributes(
    *, token: str, repo_id: str, repo_type: str, revision: str,
    destination: Path, request_timeout: float,
) -> bool:
    """Download only root `.gitattributes`, returning False only for file 404."""
    request = urllib.request.Request(
        _atomgit_resolve_url(
            repo_id, repo_type, _LFS_GITATTRIBUTES_PATH, revision
        ),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "*/*",
            "Accept-Encoding": "identity",
            "User-Agent": "atomgit-cli",
        },
        method="GET",
    )
    try:
        with _atomgit_open_url(request, timeout=request_timeout) as response:
            content_length = response.headers.get("Content-Length")
            if content_length is not None:
                try:
                    declared_size = int(content_length, 10)
                except ValueError as error:
                    raise ValueError(
                        "远端 .gitattributes 长度无效"
                    ) from error
                if declared_size < 0:
                    raise ValueError("远端 .gitattributes 长度无效")
                if declared_size > _LFS_GITATTRIBUTES_MAX_BYTES:
                    raise ValueError(
                        "远端 .gitattributes 过大，无法安全自动修改"
                    )
            content = response.read(_LFS_GITATTRIBUTES_MAX_BYTES + 1)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            files = HfApi(
                endpoint=_atomgit_hf_endpoint(), token=token
            ).list_repo_files(
                repo_id,
                revision=revision,
                repo_type=repo_type,
            )
            if _LFS_GITATTRIBUTES_PATH not in files:
                return False
        raise
    if len(content) > _LFS_GITATTRIBUTES_MAX_BYTES:
        raise ValueError("远端 .gitattributes 过大，无法安全自动修改")
    destination.write_bytes(content)
    os.chmod(destination, 0o600)
    return True


def _configure_remote_lfs_attributes(
    *, token: str, repo_id: str, repo_type: str, revision: str,
    patterns, request_timeout: float,
) -> dict:
    """Merge and commit only `.gitattributes` with optimistic concurrency."""
    validated = _validated_lfs_patterns(patterns)
    if not validated:
        raise ValueError("无法从文件路径推导安全的 LFS 文件类型规则")
    target_revision = revision or "main"
    cache_root = _lfs_config_cache_root()

    for attempt in range(_LFS_GITATTRIBUTES_MAX_ATTEMPTS):
        parent_commit = _remote_revision_commit_sha(
            token=token,
            repo_id=repo_id,
            revision=target_revision,
            request_timeout=request_timeout,
        )
        with tempfile.TemporaryDirectory(
            prefix="transaction-", dir=cache_root
        ) as temporary_name:
            transaction = Path(temporary_name)
            os.chmod(transaction, 0o700)
            attributes_path = transaction / _LFS_GITATTRIBUTES_PATH
            existed = _download_remote_gitattributes(
                token=token,
                repo_id=repo_id,
                repo_type=repo_type,
                revision=parent_commit,
                destination=attributes_path,
                request_timeout=request_timeout,
            )
            content = attributes_path.read_bytes() if existed else b""
            updated, appended = _merge_lfs_gitattributes(content, validated)
            if not appended:
                return {
                    "changed": False,
                    "created": False,
                    "verified_after_error": False,
                    "patterns": validated,
                }
            attributes_path.write_bytes(updated)
            os.chmod(attributes_path, 0o600)

            write_error = None
            try:
                HfApi(
                    endpoint=_atomgit_hf_endpoint(), token=token
                ).upload_file(
                    path_or_fileobj=str(attributes_path),
                    path_in_repo=_LFS_GITATTRIBUTES_PATH,
                    repo_id=repo_id,
                    repo_type=repo_type,
                    revision=target_revision,
                    commit_message="chore: configure Git LFS",
                    parent_commit=parent_commit,
                )
            except Exception as error:
                write_error = error

            verify_commit = _remote_revision_commit_sha(
                token=token,
                repo_id=repo_id,
                revision=target_revision,
                request_timeout=request_timeout,
            )
            attributes_path.unlink(missing_ok=True)
            verified_exists = _download_remote_gitattributes(
                token=token,
                repo_id=repo_id,
                repo_type=repo_type,
                revision=verify_commit,
                destination=attributes_path,
                request_timeout=request_timeout,
            )
            verified_content = (
                attributes_path.read_bytes() if verified_exists else b""
            )
            if _gitattributes_contains_lfs_patterns(
                verified_content, appended
            ):
                return {
                    "changed": True,
                    "created": not existed,
                    "verified_after_error": write_error is not None,
                    "patterns": appended,
                }
            if write_error is None:
                raise RuntimeError(".gitattributes 提交后远端验证失败")
            if (
                _resumable_error_status(write_error) not in (409, 412)
                or attempt + 1 >= _LFS_GITATTRIBUTES_MAX_ATTEMPTS
            ):
                raise write_error

    raise RuntimeError(".gitattributes 并发更新重试次数已耗尽")


def _commit_error_status(error: BaseException) -> Optional[int]:
    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)
    return status_code if isinstance(status_code, int) else None


def _commit_retry_after(error: BaseException) -> Optional[float]:
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    value = headers.get("Retry-After") if headers is not None else None
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        try:
            retry_at = parsedate_to_datetime(value)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(
                0.0,
                (retry_at - datetime.now(timezone.utc)).total_seconds(),
            )
        except (TypeError, ValueError, OverflowError):
            return None


def _bounded_lfs_retry_after(error: BaseException) -> Optional[float]:
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    value = headers.get("Retry-After") if headers is not None else None
    if not value:
        return None
    try:
        numeric_delay = float(value)
    except (TypeError, ValueError):
        numeric_delay = None
    if numeric_delay is not None:
        if not math.isfinite(numeric_delay) or numeric_delay < 0:
            return None
        return min(numeric_delay, _RESUMABLE_LFS_PREUPLOAD_WAIT_CAP)
    try:
        retry_at = parsedate_to_datetime(value)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        delay = (retry_at - datetime.now(timezone.utc)).total_seconds()
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(delay) or delay < 0:
        return None
    return min(delay, _RESUMABLE_LFS_PREUPLOAD_WAIT_CAP)


def _bounded_lfs_error_payload(error: BaseException) -> Optional[dict]:
    """Read only a small JSON object for narrow AtomGit quota detection."""
    response = getattr(error, "response", None)
    try:
        content = getattr(response, "content", None)
    except Exception:
        return None
    if not isinstance(content, bytes) or len(content) > _RESUMABLE_LFS_ERROR_BODY_MAX_BYTES:
        return None
    try:
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _is_atomgit_lfs_quota_error(error: BaseException) -> bool:
    if _resumable_error_status(error) != 413:
        return False
    payload = _bounded_lfs_error_payload(error)
    if payload is None:
        return False
    code = payload.get("error_code_name")
    if code in ("INSUFFICIENT_LFS_SPACE", "LFS_QUOTA_EXCEEDED"):
        return True
    message = payload.get("error_message")
    marker = "Insufficient LFS space"
    if not isinstance(message, str) or not message.startswith(marker):
        return False
    return len(message) == len(marker) or message[len(marker)] in " :,.(-"


def _lfs_preupload_error_category(error: BaseException) -> tuple:
    """Return the safe category and whether one LFS failure is retryable."""
    for cause in _resumable_error_chain(error):
        if isinstance(cause, ResumableLfsPreuploadError):
            return cause.category, False
        status_code = _resumable_error_status(cause)
        if status_code == 401:
            return "authentication", False
        if status_code == 403:
            return "permission", False
        if status_code == 404:
            return "repository", False
        if status_code == 507 or _is_atomgit_lfs_quota_error(cause):
            return "lfs_quota", False
        if status_code == 509:
            return "lfs_bandwidth", False
        if status_code == 429:
            return "rate_limit", True
        if status_code in (413, 422) or (
            isinstance(status_code, int) and 400 <= status_code < 500
        ):
            return "lfs_batch_rejected", False
        if status_code in (500, 502, 503, 504):
            return "service_unavailable", True
        if isinstance(
            cause,
            (httpx.TimeoutException, TimeoutError, socket.timeout),
        ):
            return "timeout", True
        if isinstance(cause, (httpx.NetworkError, ConnectionError)):
            return "connection", True
        if isinstance(cause, ValueError):
            return "lfs_batch_rejected", False
    category = _resumable_worker_error_category(error)
    return category, False


class _ResumableLfsPreuploadController:
    """Bound retries before HF's worker can requeue an LFS preupload job."""

    def __init__(
        self,
        preupload_lfs,
        *,
        sleep=time.sleep,
        jitter=None,
        monotonic=time.monotonic,
        deadline=None,
        max_attempts: int = _RESUMABLE_LFS_PREUPLOAD_MAX_ATTEMPTS,
        fatal_callback=None,
        event_callback=None,
        lfs_attributes_policy=None,
    ):
        self._preupload_lfs = preupload_lfs
        self._sleep = sleep
        self._jitter = jitter or (
            lambda delay: random.uniform(0.0, min(0.5, delay * 0.1))
        )
        self._monotonic = monotonic
        self._deadline = deadline
        self._max_attempts = max_attempts
        self._fatal_callback = fatal_callback
        self._event_callback = event_callback
        self._lfs_attributes_policy = lfs_attributes_policy

    def _emit(self, event) -> None:
        if self._event_callback is None:
            return
        try:
            self._event_callback(event)
        except Exception:
            pass

    def _fail(self, category: str, *, attempts: int = 1):
        error = ResumableLfsPreuploadError(category)
        if attempts >= self._max_attempts and self._event_callback is not None:
            self._emit({
                "kind": "lfs_preupload_exhausted",
                "category": category,
                "attempts": attempts,
            })
        if self._fatal_callback is not None:
            self._fatal_callback(error)
        raise error

    def _retry_delay(self, error: BaseException, attempt: int) -> float:
        retry_after = _bounded_lfs_retry_after(error)
        if retry_after is not None:
            return retry_after
        base = min(
            _RESUMABLE_LFS_PREUPLOAD_BACKOFF_BASE * (2 ** (attempt - 1)),
            _RESUMABLE_LFS_PREUPLOAD_WAIT_CAP,
        )
        return min(base + self._jitter(base), _RESUMABLE_LFS_PREUPLOAD_WAIT_CAP)

    def preupload_lfs(self, *args, **kwargs):
        if self._lfs_attributes_policy is not None:
            items = kwargs.get("items")
            if items is None and args:
                items = args[0]
            try:
                self._lfs_attributes_policy.validate_items(items or [])
            except ResumableLfsAttributesError as error:
                if self._fatal_callback is not None:
                    self._fatal_callback(error)
                raise
        for attempt in range(1, self._max_attempts + 1):
            try:
                return self._preupload_lfs(*args, **kwargs)
            except Exception as error:
                category, retryable = _lfs_preupload_error_category(error)
                if not retryable or attempt >= self._max_attempts:
                    self._fail(category, attempts=attempt)
                delay = self._retry_delay(error, attempt)
                if (
                    self._deadline is not None
                    and self._monotonic() + delay >= self._deadline
                ):
                    self._fail("timeout")
                self._emit({
                    "kind": "lfs_preupload_retry",
                    "category": category,
                    "attempt": attempt + 1,
                    "max_attempts": self._max_attempts,
                    "delay": delay,
                })
                self._sleep(delay)


def _is_ambiguous_commit_error(error: BaseException) -> bool:
    status_code = _commit_error_status(error)
    if status_code in (502, 503, 504):
        return True
    return isinstance(
        error,
        (
            httpx.TimeoutException,
            httpx.NetworkError,
            TimeoutError,
            ConnectionError,
            socket.timeout,
        ),
    )


def _is_retryable_commit_error(error: BaseException) -> bool:
    status_code = _commit_error_status(error)
    if status_code in (429, 502, 503, 504):
        return True
    return isinstance(
        error,
        (
            httpx.TimeoutException,
            httpx.NetworkError,
            TimeoutError,
            ConnectionError,
            socket.timeout,
        ),
    )


def _is_reducible_commit_error(error: BaseException) -> bool:
    status_code = _commit_error_status(error)
    if status_code in (413, 502, 503, 504):
        return True
    return isinstance(
        error,
        (httpx.ReadTimeout, httpx.WriteTimeout, TimeoutError, socket.timeout),
    )


def _operation_git_sha1(operation) -> Optional[str]:
    upload_info = getattr(operation, "upload_info", None)
    size = getattr(upload_info, "size", None)
    source = getattr(operation, "path_or_fileobj", None)
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        return None
    digest = hashlib.sha1()
    digest.update(b"blob " + str(size).encode("ascii") + b"\0")
    try:
        if isinstance(source, bytes):
            digest.update(source)
        elif isinstance(source, (str, Path)):
            with Path(source).open("rb") as stream:
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
        elif hasattr(source, "read"):
            position = source.tell()
            try:
                source.seek(0)
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
            finally:
                source.seek(position)
        else:
            return None
    except (OSError, ValueError, AttributeError):
        return None
    return digest.hexdigest()


def _reconcile_resumable_commit_operations(
    *, repo_id: str, repo_type: str, revision: str, operations, token: str
) -> Set[str]:
    """Return paths whose remote object identity matches the commit operation."""
    if revision not in (None, "main"):
        return set()
    matched = set()
    for operation in operations:
        path_in_repo = getattr(operation, "path_in_repo", None)
        upload_info = getattr(operation, "upload_info", None)
        if not isinstance(path_in_repo, str) or upload_info is None:
            continue
        try:
            algorithm, remote_digest, remote_size = _atomgit_file_checksum(
                repo_id, repo_type, path_in_repo, token
            )
        except Exception:
            continue
        local_size = getattr(upload_info, "size", None)
        if remote_size != local_size:
            continue
        if algorithm == "sha256":
            local_sha256 = getattr(upload_info, "sha256", None)
            if isinstance(local_sha256, bytes) and local_sha256.hex() == remote_digest:
                matched.add(path_in_repo)
        elif algorithm == "git-sha1":
            if _operation_git_sha1(operation) == remote_digest:
                matched.add(path_in_repo)
    return matched


def _next_resumable_commit_batch_size(item_count: int) -> int:
    for batch_size in _RESUMABLE_COMMIT_BATCH_SIZES:
        if batch_size < item_count:
            return batch_size
    return 1


def _mark_resumable_operations_committed(
    folder_path: Path, operations
) -> None:
    """Persist successful sub-commits before the outer HF batch completes."""
    folder_path = Path(folder_path)
    for operation in operations:
        path_in_repo = getattr(operation, "path_in_repo", None)
        upload_info = getattr(operation, "upload_info", None)
        local_sha256 = getattr(upload_info, "sha256", None)
        if not isinstance(path_in_repo, str) or not isinstance(local_sha256, bytes):
            raise ResumableCommitError(
                "resumable commit metadata is unavailable"
            )
        paths = get_local_upload_paths(folder_path, path_in_repo)
        metadata = read_upload_metadata(folder_path, path_in_repo)
        if metadata.sha256 != local_sha256.hex():
            raise ResumableCommitError(
                "resumable commit metadata changed during upload"
            )
        metadata.is_committed = True
        metadata.save(paths)


class _ResumableCommitController:
    """Apply AtomGit-specific retry and reconciliation to HF commit calls."""

    def __init__(
        self,
        create_commit,
        *,
        token: str,
        sleep=time.sleep,
        jitter=None,
        reconcile=_reconcile_resumable_commit_operations,
        max_attempts: int = _RESUMABLE_COMMIT_MAX_ATTEMPTS,
        mark_committed=None,
        canonical_payloads=canonical_lfs_payloads,
        verify_committed=None,
        fatal_callback=None,
        event_callback=None,
        lfs_attributes_policy=None,
    ):
        self._create_commit = create_commit
        self._token = token
        self._sleep = sleep
        self._jitter = jitter or (
            lambda delay: random.uniform(0.0, min(1.0, delay * 0.1))
        )
        self._reconcile = reconcile
        self._max_attempts = max_attempts
        self._mark_committed = mark_committed or (lambda operations: None)
        self._canonical_payloads = canonical_payloads
        self._verify_committed = verify_committed or (
            lambda expectations, repo_id, revision: None
        )
        self._fatal_callback = fatal_callback
        self._event_callback = event_callback
        self._lfs_attributes_policy = lfs_attributes_policy

    def _emit(self, kind: str, **details) -> None:
        if self._event_callback is None:
            return
        try:
            self._event_callback({"kind": kind, **details})
        except Exception:
            # Observability must never change upload or retry semantics.
            pass

    def _raise_fatal(self, error: BaseException, item_count: int):
        status_code = _commit_error_status(error)
        if status_code is not None:
            detail = f"HTTP {status_code}"
        else:
            detail = type(error).__name__
        wrapped = ResumableCommitError(
            f"resumable commit failed for {item_count} file(s): {detail}"
        )
        if self._fatal_callback is not None:
            self._fatal_callback(error)
        raise wrapped from error

    def _retry_delay(self, error: BaseException, attempt: int) -> float:
        retry_after = _commit_retry_after(error)
        if retry_after is not None:
            return retry_after
        delay = min(
            _RESUMABLE_COMMIT_BACKOFF_BASE * (2 ** (attempt - 1)),
            _RESUMABLE_COMMIT_BACKOFF_CAP,
        )
        return delay + self._jitter(delay)

    def _commit_group(self, args, kwargs, operations):
        operations = list(operations)
        attempts = 0
        last_error = None
        while operations and attempts < self._max_attempts:
            attempts += 1
            call_kwargs = dict(kwargs)
            call_kwargs["operations"] = operations
            expectations = []
            try:
                with self._canonical_payloads() as expectations:
                    result = self._create_commit(*args, **call_kwargs)
                if expectations:
                    commit_revision = getattr(result, "oid", None)
                    if not isinstance(commit_revision, str) or not commit_revision:
                        raise RuntimeError(
                            "resumable commit revision is unavailable"
                        )
                    self._verify_committed(
                        expectations,
                        call_kwargs.get("repo_id"),
                        commit_revision,
                    )
                self._mark_committed(operations)
                return result
            except Exception as error:
                last_error = error
                if _is_ambiguous_commit_error(error):
                    self._emit(
                        "reconcile_start",
                        item_count=len(operations),
                        attempt=attempts,
                    )
                    matched = self._reconcile(
                        repo_id=call_kwargs.get("repo_id"),
                        repo_type=call_kwargs.get("repo_type") or "model",
                        revision=call_kwargs.get("revision") or "main",
                        operations=operations,
                        token=self._token,
                    )
                    matched_operations = [
                        operation for operation in operations
                        if getattr(operation, "path_in_repo", None) in matched
                    ]
                    if matched_operations:
                        matched_expectations = [
                            expectation for expectation in expectations
                            if expectation.path_in_repo in matched
                        ]
                        try:
                            if matched_expectations:
                                self._verify_committed(
                                    matched_expectations,
                                    call_kwargs.get("repo_id"),
                                    call_kwargs.get("revision") or "main",
                                )
                            self._mark_committed(matched_operations)
                        except Exception as metadata_error:
                            self._raise_fatal(
                                metadata_error, len(matched_operations)
                            )
                    operations = [
                        operation for operation in operations
                        if getattr(operation, "path_in_repo", None) not in matched
                    ]
                    self._emit(
                        "reconcile_result",
                        confirmed=len(matched_operations),
                        remaining=len(operations),
                        attempt=attempts,
                    )
                    if not operations:
                        return None
                if _commit_error_status(error) == 413:
                    break
                if not _is_retryable_commit_error(error):
                    self._raise_fatal(error, len(operations))
                if attempts < self._max_attempts:
                    delay = self._retry_delay(error, attempts)
                    status_code = _commit_error_status(error)
                    if status_code == 429:
                        self._emit(
                            "rate_limit_wait",
                            delay=delay,
                            attempt=attempts,
                            item_count=len(operations),
                        )
                    self._emit(
                        "retry",
                        attempt=attempts + 1,
                        max_attempts=self._max_attempts,
                        item_count=len(operations),
                        status_code=status_code,
                        error_type=type(error).__name__,
                    )
                    self._sleep(delay)

        if not operations:
            return None
        if (
            len(operations) == 1
            or not _is_reducible_commit_error(last_error)
        ):
            self._raise_fatal(last_error, len(operations))

        batch_size = _next_resumable_commit_batch_size(len(operations))
        self._emit(
            "reduce",
            from_size=len(operations),
            to_size=batch_size,
        )
        result = None
        for index in range(0, len(operations), batch_size):
            result = self._commit_group(
                args,
                kwargs,
                operations[index:index + batch_size],
            )
        return result

    def create_commit(self, *args, **kwargs):
        operations = list(kwargs.get("operations", ()))
        if not operations:
            return self._create_commit(*args, **kwargs)
        try:
            if self._lfs_attributes_policy is not None:
                self._lfs_attributes_policy.validate_operations(operations)
            _validate_resumable_commit_operations(operations)
        except (ResumableUploadModeError, ResumableLfsAttributesError) as error:
            if self._fatal_callback is not None:
                self._fatal_callback(error)
            raise
        return self._commit_group(args, kwargs, operations)


def _print_resumable_commit_event(event, batch_context) -> None:
    """Print one credential-safe child event with its outer batch identity."""
    if not batch_context:
        return
    current, total = batch_context
    prefix = f"[批次 {current}/{total}]"
    kind = event.get("kind")
    if kind == "rate_limit_wait":
        print(
            f"{prefix} 请求限流，等待 {event['delay']:g} 秒后重试",
            flush=True,
        )
    elif kind == "retry":
        reason = (
            f"HTTP {event['status_code']}"
            if event.get("status_code") is not None
            else event.get("error_type", "网络错误")
        )
        print(
            f"{prefix} 重试 {event['attempt']}/{event['max_attempts']}"
            f"（{reason}，{event['item_count']} 个文件）",
            flush=True,
        )
    elif kind == "reconcile_start":
        print(
            f"{prefix} 提交结果不明确，正在核对远端状态"
            f"（{event['item_count']} 个文件）",
            flush=True,
        )
    elif kind == "reconcile_result":
        print(
            f"{prefix} 远端核对完成: 确认 {event['confirmed']}，"
            f"仍待提交 {event['remaining']}",
            flush=True,
        )
    elif kind == "reduce":
        print(
            f"{prefix} 降低提交批量: {event['from_size']} -> "
            f"{event['to_size']}",
            flush=True,
        )


def _print_resumable_lfs_preupload_event(event, batch_context) -> None:
    """Print one bounded retry decision without dependency error details."""
    if not batch_context:
        return
    current, total = batch_context
    if event.get("kind") == "lfs_preupload_retry":
        print(
            f"[批次 {current}/{total}] LFS 预上传重试 "
            f"{event['attempt']}/{event['max_attempts']}，"
            f"等待 {event['delay']:g} 秒（{event['category']}）",
            flush=True,
        )
    elif event.get("kind") == "lfs_preupload_exhausted":
        print(
            f"[批次 {current}/{total}] LFS 预上传已达到最多 "
            f"{event['attempts']} 次尝试，正在安全停止",
            flush=True,
        )


def _print_resumable_slow_flow_event(event, batch_context) -> None:
    """Print an object-anonymous LFS flow recovery decision."""
    if not batch_context:
        return
    current, total = batch_context
    kind = event.get("kind")
    if kind == "lfs_slow_flow_replace":
        mode = "整体降速探针" if event.get("probe") else "单对象低速"
        print(
            f"[批次 {current}/{total}] 检测到{mode}，仅替换当前 LFS "
            f"连接（第 {event['replacement']}/"
            f"{_SLOW_FLOW_MAX_REPLACEMENTS} 次，等待 "
            f"{event['delay']:g} 秒）",
            flush=True,
        )
    elif kind == "lfs_slow_flow_disabled":
        print(
            f"[批次 {current}/{total}] 新 LFS 连接未达到 2 倍改善，"
            "停止该对象的自动连接替换",
            flush=True,
        )


def _run_resumable_upload(
    token, kwargs, result_queue,
    request_timeout: float = _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
    batch_context=None,
    upload_deadline=None,
    auto_configure_lfs=False,
    configured_lfs_patterns=(),
):
    """Run HF's resumable uploader in an isolated child process.

    The child is deliberately short-lived so a timed-out transfer can be
    terminated without leaving worker threads running in the CLI process.
    """
    original_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT
    original_get_upload_mode = hf_large_folder._get_upload_mode
    original_preupload_lfs = hf_large_folder._preupload_lfs
    lfs_attributes_policy = (
        _ResumableLfsAttributesPolicy(configured_lfs_patterns)
        if auto_configure_lfs
        else None
    )
    slow_flow_coordinator = _SlowFlowCoordinator(
        deadline=upload_deadline,
        event_callback=lambda event: _print_resumable_slow_flow_event(
            event, batch_context
        ),
    )
    result_sent = False

    def send_failure(error):
        nonlocal result_sent
        if not result_sent:
            result_queue.put((False, _resumable_failure_envelope(error)))
            result_sent = True

    def fatal_exit(error):
        if multiprocessing.current_process().name == "MainProcess":
            return
        send_failure(error)
        if hasattr(result_queue, "close"):
            result_queue.close()
        if hasattr(result_queue, "join_thread"):
            result_queue.join_thread()
        os._exit(1)

    def get_upload_mode_with_policy(*args, **kwargs):
        result = original_get_upload_mode(*args, **kwargs)
        items = kwargs.get("items")
        if items is None and args:
            items = args[0]
        try:
            _validate_resumable_upload_mode_items(items or [])
            if lfs_attributes_policy is not None:
                lfs_attributes_policy.validate_items(items or [])
        except (ResumableUploadModeError, ResumableLfsAttributesError) as error:
            fatal_exit(error)
            raise
        return result

    try:
        hf_constants.DEFAULT_REQUEST_TIMEOUT = request_timeout
        close_hf_session()
        client = HfApi(endpoint=_atomgit_hf_endpoint(), token=token)
        _refresh_unsafe_resumable_upload_modes(Path(kwargs["folder_path"]))
        if lfs_attributes_policy is not None:
            cached_patterns = _resumable_projection_lfs_patterns(
                Path(kwargs["folder_path"])
            )
            if cached_patterns:
                try:
                    lfs_attributes_policy.validate_patterns(cached_patterns)
                except ResumableLfsAttributesError as error:
                    fatal_exit(error)
                    raise

        def existing_repo(repo_id, *, private=None, repo_type=None,
                          exist_ok=False):
            """Satisfy HF 1.1.7 setup after the parent validated the target."""
            return type("_ExistingRepo", (), {"repo_id": repo_id})()

        # HF 1.1.7 otherwise sends create_repo(exist_ok=True) before metadata
        # recovery. AtomGit upload targets are required to pre-exist.
        client.create_repo = existing_repo
        hf_large_folder._get_upload_mode = get_upload_mode_with_policy
        preupload_controller = _ResumableLfsPreuploadController(
            original_preupload_lfs,
            deadline=upload_deadline,
            fatal_callback=fatal_exit,
            event_callback=lambda event: _print_resumable_lfs_preupload_event(
                event, batch_context
            ),
            lfs_attributes_policy=lfs_attributes_policy,
        )
        hf_large_folder._preupload_lfs = preupload_controller.preupload_lfs
        create_commit = getattr(client, "create_commit", None)
        if callable(create_commit):
            controller = _ResumableCommitController(
                create_commit,
                token=token,
                mark_committed=lambda operations: (
                    _mark_resumable_operations_committed(
                        Path(kwargs["folder_path"]), operations
                    )
                ),
                verify_committed=lambda expectations, repo_id, revision: (
                    verify_canonical_lfs_pointers(
                        token=token,
                        repo_id=repo_id,
                        revision=revision,
                        expectations=expectations,
                        timeout=min(request_timeout, 15),
                    )
                ),
                fatal_callback=fatal_exit,
                event_callback=lambda event: _print_resumable_commit_event(
                    event, batch_context
                ),
                lfs_attributes_policy=lfs_attributes_policy,
            )
            client.create_commit = controller.create_commit
        with _scoped_resumable_lfs_recovery(slow_flow_coordinator):
            client.upload_large_folder(**kwargs)
        result_queue.put((True, None))
        result_sent = True
    except BaseException as exc:
        send_failure(exc)
    finally:
        hf_large_folder._get_upload_mode = original_get_upload_mode
        hf_large_folder._preupload_lfs = original_preupload_lfs
        hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
        close_hf_session()


class ResumableProjectionError(ValueError):
    """A local resumable projection cannot be prepared safely."""


def _resumable_projection_cache_root() -> Path:
    """Return the private cache for stable path-in-repo upload projections."""
    hf_home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "atomgit"))
    root = hf_home / "upload-projections"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise ResumableProjectionError("断点续传投影缓存目录不安全")
    os.chmod(root, 0o700)
    return root


def _ensure_projection_directory(path: Path, projection_root: Path) -> None:
    """Create an internal projection directory without following symlinks."""
    relative = path.relative_to(projection_root)
    current = projection_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ResumableProjectionError("断点续传投影缓存包含符号链接")
        if current.exists() and not current.is_dir():
            current.unlink()
        current.mkdir(mode=0o700, exist_ok=True)


def _source_projection_files(source: Path):
    """Yield regular source files while excluding HF's local resume metadata."""
    for root_name, directory_names, filenames in os.walk(
        str(source), topdown=True, followlinks=False
    ):
        root = Path(root_name)
        relative_root = root.relative_to(source)
        if tuple(part.casefold() for part in relative_root.parts[:2]) == (
            ".cache", "huggingface"
        ):
            directory_names[:] = []
            continue

        retained_directories = []
        for name in directory_names:
            candidate = root / name
            if candidate.is_symlink():
                raise ValueError("上传路径包含符号链接，已拒绝上传")
            if name == ".git":
                continue
            relative = candidate.relative_to(source)
            if tuple(part.casefold() for part in relative.parts[:2]) != (
                ".cache", "huggingface"
            ):
                retained_directories.append(name)
        directory_names[:] = retained_directories

        for name in filenames:
            candidate = root / name
            if candidate.is_symlink():
                raise ValueError("上传路径包含符号链接，已拒绝上传")
            try:
                file_stat = candidate.stat()
            except OSError as error:
                raise ValueError("无法读取上传目录，已拒绝上传") from error
            if stat.S_ISREG(file_stat.st_mode):
                yield candidate.relative_to(source), candidate, file_stat


def _projection_file_is_current(
    source: Path, destination: Path, source_stat
) -> bool:
    if destination.is_symlink():
        try:
            return os.path.samefile(source, destination)
        except OSError:
            return False
    if not destination.is_file():
        return False
    try:
        if os.path.samefile(source, destination):
            return True
        destination_stat = destination.stat()
    except OSError:
        return False
    return (
        destination_stat.st_size == source_stat.st_size
        and destination_stat.st_mtime_ns == source_stat.st_mtime_ns
    )


def _is_projection_hf_metadata(path: Path, projection: Path) -> bool:
    relative = path.relative_to(projection)
    return tuple(part.casefold() for part in relative.parts[:2]) == (
        ".cache", "huggingface"
    )


def _sync_resumable_projection(
    source: Path,
    projection: Path,
    prefix: str = None,
    ignore_patterns=None,
    selected_paths: Optional[Set[Path]] = None,
) -> None:
    """Mirror source files below prefix while retaining HF metadata at root."""
    payload_root = (
        projection.joinpath(*prefix.split("/")) if prefix else projection
    )
    _ensure_projection_directory(payload_root, projection)
    desired_paths = set()

    source_files = filter_repo_objects(
        _source_projection_files(source),
        ignore_patterns=ignore_patterns,
        key=lambda item: item[0].as_posix(),
    )
    for relative, source_file, source_stat in source_files:
        if selected_paths is not None and relative not in selected_paths:
            continue
        desired_paths.add(relative)
        destination = payload_root / relative
        if _is_projection_hf_metadata(destination, projection):
            raise ResumableProjectionError(
                "上传内容与 HF 断点续传元数据路径冲突，请使用 --no-resumable"
            )
        _ensure_projection_directory(destination.parent, projection)
        if destination.is_dir():
            shutil.rmtree(destination)
        elif _projection_file_is_current(source_file, destination, source_stat):
            continue
        elif destination.exists():
            destination.unlink()

        try:
            os.link(source_file, destination)
        except OSError:
            try:
                os.symlink(source_file, destination)
            except OSError as error:
                raise ResumableProjectionError(
                    "无法为断点续传创建无副本投影；请确认缓存目录与源目录支持硬链接或符号链接"
                ) from error

    for root_name, directory_names, filenames in os.walk(
        str(payload_root), topdown=False, followlinks=False
    ):
        root = Path(root_name)
        for name in filenames:
            candidate = root / name
            relative = candidate.relative_to(payload_root)
            if _is_projection_hf_metadata(candidate, projection):
                continue
            if relative not in desired_paths:
                candidate.unlink()
        for name in directory_names:
            candidate = root / name
            if candidate.is_symlink():
                candidate.unlink()
                continue
            relative = candidate.relative_to(payload_root)
            if _is_projection_hf_metadata(candidate, projection):
                continue
            try:
                candidate.rmdir()
            except OSError:
                pass


def _prepare_resumable_upload_projection(
    source: Path,
    repo_id: str,
    repo_type: str,
    revision: str,
    path_in_repo: str = None,
    ignore_patterns=None,
    selected_paths: Optional[Set[Path]] = None,
    batch_key: str = "all",
) -> Path:
    """Build or refresh one stable large-folder projection for a remote prefix."""
    parts = path_in_repo.split("/") if path_in_repo else []
    folded_parts = [part.casefold() for part in parts]
    if ".git" in folded_parts or any(
        folded_parts[index:index + 2] == [".cache", "huggingface"]
        for index in range(len(folded_parts) - 1)
    ):
        raise ResumableProjectionError(
            "断点续传模式不能上传到 HF 保留路径，请使用 --no-resumable"
        )

    source = source.expanduser().resolve(strict=True)
    cache_root = _resumable_projection_cache_root()
    try:
        source.relative_to(cache_root)
    except ValueError:
        pass
    else:
        raise ResumableProjectionError("不能将断点续传投影缓存作为上传源")

    identity = "\0".join(
        (
            _atomgit_hf_endpoint(),
            str(source),
            repo_id,
            repo_type,
            revision or "main",
            path_in_repo or "",
            batch_key,
        )
    )
    projection = cache_root / hashlib.sha256(identity.encode("utf-8")).hexdigest()
    _ensure_projection_directory(projection, cache_root)
    os.chmod(projection, 0o700)
    _sync_resumable_projection(
        source,
        projection,
        path_in_repo,
        ignore_patterns=ignore_patterns,
        selected_paths=selected_paths,
    )
    return projection


def _collect_resumable_upload_files(source: Path, ignore_patterns=None):
    """Return deterministic source-relative files selected for upload."""
    source_files = filter_repo_objects(
        _source_projection_files(source),
        ignore_patterns=ignore_patterns,
        key=lambda item: item[0].as_posix(),
    )
    return sorted(list(source_files), key=lambda item: item[0].as_posix())


def _resumable_committed_file_count(
    projection: Path, selected_paths, path_in_repo: str = None
) -> int:
    """Count current projected files already committed by HF large-folder."""
    prefix = f"{path_in_repo}/" if path_in_repo else ""
    committed = 0
    for relative_path in selected_paths:
        try:
            metadata = read_upload_metadata(
                Path(projection), prefix + relative_path.as_posix()
            )
        except Exception:
            # This helper is observational. HF remains authoritative and will
            # validate or repair its own metadata in the upload process.
            continue
        if metadata.is_committed:
            committed += 1
    return committed


def _print_upload_batch_plan(
    file_count: int, batch_count: int, batch_size: int
) -> None:
    print(
        f"上传批次计划: 共 {file_count} 个文件，{batch_count} 个批次，"
        f"每批最多 {batch_size} 个文件",
        flush=True,
    )


def _print_upload_batch_summary(
    planned: int, submitted: int, skipped: int, completed: int
) -> None:
    print(
        f"上传批次汇总: 计划 {planned}，新增提交 {submitted}，"
        f"续传跳过 {skipped}，确认完成 {completed}",
        flush=True,
    )


def _execute_resumable_upload_process(
    *, token: str, upload_kwargs: dict, request_timeout: float,
    upload_deadline, upload_timeout, batch_context,
    auto_configure_lfs: bool = False, configured_lfs_patterns=(),
) -> None:
    """Run one outer resumable batch and require an explicit child result."""
    methods = multiprocessing.get_all_start_methods()
    context = multiprocessing.get_context(
        "fork" if "fork" in methods else "spawn"
    )
    result_queue = context.Queue()
    process = context.Process(
        target=_run_resumable_upload,
        args=(
            token,
            upload_kwargs,
            result_queue,
            request_timeout,
            batch_context,
            upload_deadline,
            auto_configure_lfs,
            configured_lfs_patterns,
        ),
    )
    process.daemon = True
    remaining_timeout = None
    if upload_deadline is not None:
        remaining_timeout = upload_deadline - time.monotonic()
    if remaining_timeout is not None and remaining_timeout <= 0:
        raise TimeoutError(
            f"resumable upload timed out after {upload_timeout}s"
        )
    process.start()
    process.join(remaining_timeout)
    if process.is_alive():
        process.terminate()
        process.join(2)
        raise TimeoutError(
            f"resumable upload timed out after {upload_timeout}s"
        )
    try:
        ok, error = result_queue.get(timeout=1)
    except Exception as exc:
        raise RuntimeError(
            "resumable upload worker exited without a result"
        ) from exc
    if not ok:
        category = error.get("category") if isinstance(error, dict) else None
        patterns = (
            error.get("lfs_patterns", ())
            if isinstance(error, dict)
            else ()
        )
        raise ResumableWorkerError(category or "unknown", patterns)


def _validate_resumable_upload_target(
    *, token: str, repo_id: str, revision: str = None,
    request_timeout: float = _RESUMABLE_DEFAULT_REQUEST_TIMEOUT,
) -> None:
    """Perform one read-only repository/revision check before local hashing."""
    repo_path = _atomgit_v5_repo_path(repo_id)
    repository = _atomgit_v5_get_json(
        repo_path, token, timeout=request_timeout
    )
    if not isinstance(repository, dict):
        raise ValueError("repository response is malformed")
    if revision in (None, "main"):
        return

    branch_path = repo_path + "/branches/" + quote(revision, safe="")
    try:
        branch = _atomgit_v5_get_json(
            branch_path, token, timeout=request_timeout
        )
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise ResumableTargetRevisionError(
                "target revision does not exist"
            ) from error
        raise
    if not isinstance(branch, dict) or branch.get("name") != revision:
        raise ResumableTargetRevisionError(
            "target revision could not be verified"
        )


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


def _prefix_resumable_ignore_patterns(path_in_repo: str, ignore_patterns):
    """Apply source-relative ignore patterns to a projected remote prefix."""
    if not path_in_repo or not ignore_patterns:
        return ignore_patterns
    return [
        f"{path_in_repo}/{pattern.lstrip('/')}" for pattern in ignore_patterns
    ]


def _classify_upload_error(e: Exception, repo_id: str = None) -> tuple:
    """把 HF Hub 上传异常归类为 (error_type, hint) 二元组，供上层给出语义化提示。

    覆盖以下典型情形（基于 huggingface_hub 错误类型与文本特征）：
      - 认证失败 (401/403, 无有效 token)
      - 仓库不存在 (RepositoryNotFoundError)
      - 仓库已禁用 (DisabledRepoError)
      - 分支不存在 (RevisionNotFoundError)
      - 请求参数错误 (BadRequestError / 400)
      - 超时 / 网络连接 (timeout / connection)
      - 其他未知错误

    返回 (error_type, hint)，其中 hint 是给用户的可执行建议。
    """
    if isinstance(e, ResumableWorkerError):
        structured_errors = {
            "authentication": (
                "认证失败",
                "登录凭证无效或已过期。请使用 'atomgit login' 重新登录后重试。",
            ),
            "permission": (
                "权限不足",
                "当前登录凭证无权上传到目标仓库。请检查仓库权限或目标命名空间。",
            ),
            "repository": (
                "仓库不存在",
                f"目标仓库 {repo_id or ''} 不存在或不可访问。请先使用 "
                "'atomgit repo create' 创建仓库，或检查 repo_id / repo_type。",
            ),
            "revision": (
                "分支/版本不存在",
                "目标分支不存在且无法自动创建。请检查 revision 是否正确。",
            ),
            "request": (
                "请求参数错误",
                "请求参数不合法。请检查 repo_id、repo_type、path_in_repo 等参数。",
            ),
            "payload_size": (
                "提交过大",
                "提交已降至单文件仍超过服务端限制；断点状态已保留，请联系平台支持。",
            ),
            "lfs_quota": (
                "LFS 存储空间不足",
                "请增加仓库或账号的 LFS 配额，或删除无用对象并完成服务端 LFS GC；"
                "断点状态已保留，释放空间后可重新执行同一命令。",
            ),
            "lfs_bandwidth": (
                "LFS 带宽额度不足",
                "请等待带宽额度重置或联系平台支持；断点状态已保留，"
                "条件恢复后可重新执行同一命令。",
            ),
            "lfs_batch_rejected": (
                "LFS 协商请求被拒绝",
                "Git LFS Batch 请求被服务端拒绝；断点状态已保留，"
                "请在平台支持解决后重新执行同一命令。",
            ),
            "rate_limit": (
                "请求限流",
                "服务端持续限流，上传已停止且断点状态已保留；请稍后重新执行同一命令。",
            ),
            "service_unavailable": (
                "服务暂不可用",
                "服务端暂时不可用，上传断点状态已保留；请稍后重新执行同一命令。",
            ),
            "timeout": (
                "请求超时",
                "请求超时。可使用 -t/--timeout 增大超时时间后重试。",
            ),
            "connection": (
                "网络连接失败",
                "无法连接到服务器。请检查网络或代理设置后重试。",
            ),
            "upload_mode": (
                "上传模式不安全",
                "服务端将超大文件判定为 regular；请在仓库 .gitattributes "
                "中为该文件类型配置 Git LFS 后重试；如允许 CLI 提交该配置，"
                "可加 --auto-configure-lfs 重新执行同一命令。断点状态已保留。",
            ),
            "lfs_pointer": (
                "LFS 指针验证失败",
                "AtomGit 服务生成的 Git LFS pointer 不符合规范或无法按原始 "
                "Git blob 确认；本次上传未确认成功，请保留断点并联系平台支持。",
            ),
            "client_resource": (
                "客户端资源不足",
                "本机内存、磁盘空间或文件句柄不足；释放资源后重新执行同一命令。",
            ),
            "unknown": (
                "未知错误",
                "上传子进程失败且未能安全识别原因；断点状态已保留，请稍后重试。",
            ),
        }
        return structured_errors[e.category]

    if isinstance(e, ResumableUploadModeError):
        return (
            "上传模式不安全",
            "服务端将超大文件判定为 regular；请在仓库 .gitattributes "
            "中为该文件类型配置 Git LFS 后重试；如允许 CLI 提交该配置，"
            "可加 --auto-configure-lfs 重新执行同一命令。断点状态已保留。",
        )

    if isinstance(e, CanonicalLfsPointerError):
        return (
            "LFS 指针验证失败",
            "AtomGit 服务生成的 Git LFS pointer 不符合规范或无法按原始 "
            "Git blob 确认；本次上传未确认成功，请联系平台支持。",
        )

    if isinstance(e, ResumableTargetRevisionError):
        return (
            "分支/版本不存在",
            "目标分支不存在且无法自动创建。请检查 revision 是否正确。",
        )

    msg = str(e)
    ename = type(e).__name__

    # 仓库已禁用（需放在 RepositoryNotFoundError 之前，避免被 403 误吞）
    if ename == "DisabledRepoError" or "disabled" in msg.lower() and "repo" in msg.lower():
        return "仓库已禁用", "该仓库已被作者禁用，无法上传。请联系仓库所有者。"

    # 分支/版本不存在
    if ename == "RevisionNotFoundError" or "revision" in msg.lower() and ("not found" in msg.lower() or "404" in msg):
        return "分支/版本不存在", f"目标分支不存在且无法自动创建。请检查 revision 是否正确。"

    # 受限仓库的可靠特征。HF 401 通用文案（"If you are trying to access a
    # private or gated repo..."）也含 "gated" 一词，不能仅凭该词判定。
    gated_markers = (
        "cannot access gated repo" in msg.lower()
        or "you are not on the authorized list" in msg.lower()
        or "you are not in the authorized list" in msg.lower()
        or "repo is gated" in msg.lower()
        or "is gated" in msg.lower()
    )

    # 仓库不存在（HF 既定：404/401 或 "Repository Not Found"、"创建提交前仓库
    # 必须已存在 / 检查 repo_id 与 repo_type" 等特征；preupload 预检对不存在
    # 或不可访问的仓库返回 404/401）
    if (
        ename in ("RepositoryNotFoundError", "GatedRepoError")
        or "repository not found" in msg.lower()
        or ("404" in msg and "not found" in msg.lower())
        or "creating a commit assumes that the repo already exists" in msg.lower()
        or "please make sure you specified the correct `repo_id` and `repo_type`" in msg.lower()
    ):
        if ename == "GatedRepoError" or gated_markers:
            return "受限仓库", "该仓库为受限仓库(gated)，您未在授权名单内。请在平台申请访问权限。"
        if "preupload" in msg.lower():
            return (
                "仓库不存在",
                f"目标仓库 {repo_id or ''} 不存在或为私有且无访问权限。"
                "请先使用 'atomgit repo create' 创建仓库，或检查 repo_id / repo_type。",
            )
        return "仓库不存在", f"仓库 {repo_id or ''} 不存在或为私有且无访问权限。请检查 repo_id/repo_type，或先 atomgit login。"

    # 受限仓库（文本特征兜底：仅限明确的 gated 语义）
    if gated_markers:
        return "受限仓库", "该仓库为受限仓库(gated)，您未在授权名单内。请在平台申请访问权限。"

    if isinstance(e, ResumableProjectionError):
        return "本地投影失败", msg

    if "429" in msg or "too many requests" in msg.lower():
        return (
            "请求限流",
            "服务端持续限流，上传已停止且断点状态已保留；请稍后重新执行同一命令。",
        )

    if "413" in msg:
        return (
            "提交过大",
            "提交已降至单文件仍超过服务端限制；断点状态已保留，请联系平台支持。",
        )

    if any(code in msg for code in ("502", "503", "504")):
        return (
            "服务暂不可用",
            "服务端暂时不可用，上传断点状态已保留；请稍后重新执行同一命令。",
        )

    # 请求参数错误
    if ename == "BadRequestError" or "400" in msg and "client error" in msg.lower():
        return "请求参数错误", "请求参数不合法。请检查 repo_id、repo_type、path_in_repo 等参数。"

    # 认证/权限失败（且不属于上述仓库类错误）
    credential_error = auth_error_kind(e)
    if credential_error == "authentication":
        return (
            "认证失败",
            "登录凭证无效或已过期。请使用 'atomgit login' 重新登录后重试。",
        )
    if credential_error == "permission":
        return (
            "权限不足",
            "当前登录凭证无权上传到目标仓库。请检查仓库权限或目标命名空间。",
        )

    # 超时
    if "timeout" in msg.lower() or "timed out" in msg.lower() or ename == "TimeoutError":
        return "请求超时", "请求超时。可使用 -t/--timeout 增大超时时间后重试。"

    # 网络连接
    if "connection" in msg.lower() or "connectionerror" in ename.lower() or "resolve" in msg.lower():
        return "网络连接失败", "无法连接到服务器。请检查网络或代理设置后重试。"

    # 其他
    return "未知错误", "服务返回了未识别的错误；请稍后重试，仍失败时联系平台支持。"


class HuggingFaceAPI(
    AuthenticationServiceMixin, RepositoryServiceMixin, DownloadServiceMixin
):
    """AtomGit API client with historical identity and owned service methods."""

    def __init__(self):
        pass

    def upload_folder(self, file_path: Path, repo_id: str,
                   remote_path: str = None, message: str = None,
                   upload_timeout: Optional[float] = None,
                   progress_bar: bool = True,
                   path_in_repo: str = None,
                   repo_type: str = None,
                   revision: str = None,
                   ignore_patterns=None,
                   num_workers: int = 5) -> bool:
        """上传单个文件 - 使用Hugging Face Hub SDK

        优先使用 HF ``upload_file`` 直接以文件路径上传，避免旧实现中
        "先复制再上传"的额外本地拷贝开销；仅在 HF 版本过旧（无
        ``upload_file``）时回退到 ``upload_folder`` + 唯一系统临时目录。

        Args:
            path_in_repo: 仓库内目标目录前缀。为空/``./`` 时上传到仓库根目录；
                否则文件会被放到该前缀下（如 ``sub/`` → ``sub/<文件名>``）。
            repo_type: 仓库类型，``model`` 或 ``dataset``。为空时由 HF
                默认按 ``model`` 处理（保持既有行为）。
            revision: 上传目标 revision。AtomGit 当前仅支持空值或 ``main``；
                CLI 会在调用本方法前拒绝其他值。
            ignore_patterns: 单文件上传路径下该参数仅会匹配 ``file_path.name``，
                几乎不生效——主要对目录上传有意义。新实现（``upload_file``）
                不支持该参数，传入时若非空会回退到 ``upload_folder`` 旧路径
                以保留语义。
        """
        if not is_supported_upload_revision(revision):
            print("上传 revision 名称不合法，已拒绝上传")
            return False
        try:
            try:
                validate_upload_path_no_symlinks(file_path)
            except ValueError as error:
                print(str(error))
                return False
            if not file_path.exists():
                print(f"文件不存在: {file_path}")
                return False

            credentials = config.get_credentials()
            if not credentials:
                print("未找到登录凭证")
                return False

            # 规范化 path_in_repo（remote_path 为旧别名，向后兼容）
            try:
                pipr = normalize_path_in_repo(path_in_repo if path_in_repo is not None else remote_path)
            except ValueError as e:
                print(f"上传路径不合法: {e}")
                return False

            original_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT
            original_progress_state = _capture_progress_bar_state()
            _set_progress_bar(progress_bar)

            commit_message = message or "Upload folder using atomgit client"
            normalized_repo_id = self._normalize_repo_id(repo_id)
            # 使用 Monkey Patch 方式临时修改 huggingface_hub 的默认超时配置
            request_timeout = (
                upload_timeout
                if upload_timeout is not None
                else _RESUMABLE_DEFAULT_REQUEST_TIMEOUT
            )
            hf_constants.DEFAULT_REQUEST_TIMEOUT = request_timeout
            close_hf_session()

            try:
                # 路径2（推荐）：直接 upload_file，无本地拷贝
                if hf_upload_file is not None and not ignore_patterns:
                    # upload_file 需要完整的 path_in_repo（含文件名）
                    remote_file_path = f"{pipr}/{file_path.name}" if pipr else file_path.name
                    file_kwargs = dict(
                        path_or_fileobj=str(file_path),
                        path_in_repo=remote_file_path,
                        repo_id=normalized_repo_id,
                        token=credentials['token'],
                        commit_message=commit_message,
                    )
                    upload_repo_type = _atomgit_repo_type(repo_type)
                    if upload_repo_type is not None:
                        file_kwargs['repo_type'] = upload_repo_type
                    if revision is not None:
                        file_kwargs['revision'] = revision
                    run_canonical_lfs_upload(
                        lambda: hf_upload_file(**file_kwargs),
                        token=credentials['token'],
                        repo_id=normalized_repo_id,
                        timeout=min(request_timeout, 15),
                    )
                    return True

                # 路径1（回退）：upload_folder + 临时目录拷贝（旧实现）
                # 触发条件：HF 版本过旧无 upload_file，或用户传了 ignore_patterns
                import tempfile
                with tempfile.TemporaryDirectory(prefix="atomgit-upload-") as temp_name:
                    temp_dir = Path(temp_name)
                    if pipr:
                        target_file = temp_dir / pipr / file_path.name
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        upload_path_in_repo = f"{pipr}/"
                    else:
                        target_file = temp_dir / file_path.name
                        upload_path_in_repo = "./"
                    import shutil
                    shutil.copy2(file_path, target_file)
                    upload_kwargs = dict(
                        repo_id=normalized_repo_id,
                        folder_path=str(temp_dir),
                        path_in_repo=upload_path_in_repo,
                        token=credentials['token'],
                        commit_message=commit_message,
                    )
                    upload_repo_type = _atomgit_repo_type(repo_type)
                    if upload_repo_type is not None:
                        upload_kwargs['repo_type'] = upload_repo_type
                    if revision is not None:
                        upload_kwargs['revision'] = revision
                    if ignore_patterns:
                        upload_kwargs['ignore_patterns'] = ignore_patterns
                    run_canonical_lfs_upload(
                        lambda: upload_folder(**upload_kwargs),
                        token=credentials['token'],
                        repo_id=normalized_repo_id,
                        timeout=min(request_timeout, 15),
                    )
                    return True
            finally:
                hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
                close_hf_session()
                _restore_progress_bar_state(original_progress_state)
        except Exception as e:
            err_type, hint = _classify_upload_error(e, repo_id=repo_id)
            print(f"上传文件失败[{err_type}]")
            print(f"💡 建议: {hint}")
            return False

    def upload_directory(self, dir_path: Path, repo_id: str,
                        message: str = None, progress_callback=None,
                        upload_timeout: Optional[float] = None,
                        progress_bar: bool = True,
                        path_in_repo: str = None,
                        repo_type: str = None,
                        revision: str = None,
                        ignore_patterns=None,
                        resumable: bool = False,
                        num_workers: int = 5,
                        auto_configure_lfs: bool = False,
                        batch_size: int = DEFAULT_UPLOAD_BATCH_SIZE) -> bool:
        """上传目录 - 使用Hugging Face Hub SDK

        Args:
            path_in_repo: 仓库内目标目录前缀。为空/``./`` 时上传到仓库根目录；
                否则目录内容会被放到该前缀下。
            repo_type: 仓库类型，``model`` 或 ``dataset``。为空时由 HF
                默认按 ``model`` 处理（保持既有行为）。
            revision: 上传目标 revision。AtomGit 当前仅支持空值或 ``main``；
                CLI 会在调用本方法前拒绝其他值。
            ignore_patterns: 忽略的文件模式列表（fnmatch/glob 风格，如
                ``*.tmp``、``logs/``、``**/.DS_Store``）。为 None 时不忽略。
            resumable: 是否启用可断点续传/分块上传模式。为 True 时改用 HF
                ``upload_large_folder``：进程级元数据写入目录下
                ``.cache/.huggingface/``，中断后再次执行可自动续传；适合
                大目录。CLI 使用按上传身份隔离的私有持久投影；
                ``path_in_repo`` 非空时将源目录内容放到对应远端前缀下，同时
                保留 HF 元数据。该模式不支持单一
                ``message`` / ``commit_message``（会产生多次提交），且 HF
                要求 ``repo_type`` 必填，为空时默认 ``model``。
            num_workers: 上传 worker 数，默认为 5；适用于断点续传和普通目录上传。
            batch_size: 外层目录批次的最大文件数，必须为 1..20 的整数。
            auto_configure_lfs: 仅用于 resumable。服务端将文件判定为 LFS 时，
                检查并补齐根目录 ``.gitattributes`` 的安全扩展名规则；同时保留
                超大 regular 文件的策略修复。规则作用于整个目标仓库。
        """
        if not is_supported_upload_revision(revision):
            print("上传 revision 名称不合法，已拒绝上传")
            return False
        if auto_configure_lfs and not resumable:
            print("--auto-configure-lfs 仅支持 resumable 目录上传")
            return False
        if (
            not isinstance(batch_size, int)
            or isinstance(batch_size, bool)
            or not 1 <= batch_size <= DEFAULT_UPLOAD_BATCH_SIZE
        ):
            print("上传批次大小必须是 1 到 20 之间的整数")
            return False
        try:
            try:
                validate_upload_path_no_symlinks(dir_path)
            except ValueError as error:
                print(str(error))
                return False
            if not dir_path.exists() or not dir_path.is_dir():
                print(f"目录不存在: {dir_path}")
                return False

            credentials = config.get_credentials()
            if not credentials:
                print("未找到登录凭证")
                return False

            # 规范化 path_in_repo
            try:
                pipr = normalize_path_in_repo(path_in_repo)
            except ValueError as e:
                print(f"上传路径不合法: {e}")
                return False

            original_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT
            original_progress_state = _capture_progress_bar_state()
            _set_progress_bar(progress_bar)

            try:
                commit_message = message or "Upload folder using atomgit client"
                request_timeout = (
                    upload_timeout
                    if upload_timeout is not None
                    else _RESUMABLE_DEFAULT_REQUEST_TIMEOUT
                )
                hf_constants.DEFAULT_REQUEST_TIMEOUT = request_timeout
                close_hf_session()

                selected_files = _collect_resumable_upload_files(
                    dir_path, ignore_patterns
                )
                batches = [
                    selected_files[index:index + batch_size]
                    for index in range(0, len(selected_files), batch_size)
                ] or [[]]
                batch_count = len(batches)
                total_files = len(selected_files)
                submitted_files = 0
                skipped_files = 0
                completed_files = 0
                _print_upload_batch_plan(
                    total_files, batch_count, batch_size
                )

                if resumable:
                    # 断点续传/分块上传：走 upload_large_folder
                    eff_repo_type = _atomgit_repo_type(repo_type) or "model"
                    normalized_repo_id = self._normalize_repo_id(repo_id)
                    upload_deadline = (
                        None
                        if upload_timeout is None
                        else time.monotonic() + upload_timeout
                    )
                    _validate_resumable_upload_target(
                        token=credentials['token'],
                        repo_id=normalized_repo_id,
                        revision=revision,
                        request_timeout=request_timeout,
                    )
                    attempted_lfs_patterns = set()
                    for batch_index, batch in enumerate(batches):
                        batch_number = batch_index + 1
                        batch_file_count = len(batch)
                        print(
                            f"[批次 {batch_number}/{batch_count}] 开始: "
                            f"{batch_file_count} 个文件",
                            flush=True,
                        )
                        selected_paths = {item[0] for item in batch}
                        upload_root = None
                        batch_skipped = 0
                        try:
                            upload_root = _prepare_resumable_upload_projection(
                                dir_path,
                                normalized_repo_id,
                                eff_repo_type,
                                revision,
                                pipr,
                                ignore_patterns=None,
                                selected_paths=selected_paths,
                                batch_key=f"batch-{batch_size}-{batch_index}",
                            )
                            batch_skipped = _resumable_committed_file_count(
                                upload_root, selected_paths, pipr
                            )
                            if batch_skipped:
                                print(
                                    f"[批次 {batch_number}/{batch_count}] "
                                    f"续传跳过: {batch_skipped} 个已确认完成文件",
                                    flush=True,
                                )

                            lf_kwargs = dict(
                                repo_id=normalized_repo_id,
                                folder_path=str(upload_root),
                                repo_type=eff_repo_type,
                                num_workers=num_workers or 5,
                            )
                            if revision is not None:
                                lf_kwargs['revision'] = revision
                            if ignore_patterns:
                                lf_kwargs['ignore_patterns'] = (
                                    _prefix_resumable_ignore_patterns(
                                        pipr, ignore_patterns
                                    )
                                )
                            while True:
                                try:
                                    # Fully committed projections still enter HF
                                    # so authorization remains checked.
                                    _execute_resumable_upload_process(
                                        token=credentials['token'],
                                        upload_kwargs=lf_kwargs,
                                        request_timeout=request_timeout,
                                        upload_deadline=upload_deadline,
                                        upload_timeout=upload_timeout,
                                        batch_context=(
                                            batch_number, batch_count
                                        ),
                                        auto_configure_lfs=auto_configure_lfs,
                                        configured_lfs_patterns=_validated_lfs_patterns(
                                            attempted_lfs_patterns
                                        ),
                                    )
                                    break
                                except ResumableWorkerError as error:
                                    if (
                                        error.category not in (
                                            "upload_mode", "lfs_attributes"
                                        )
                                        or not auto_configure_lfs
                                    ):
                                        raise
                                    patterns = _validated_lfs_patterns(
                                        error.lfs_patterns
                                    )
                                    new_patterns = tuple(
                                        pattern
                                        for pattern in patterns
                                        if pattern not in attempted_lfs_patterns
                                    )
                                    if (
                                        len(attempted_lfs_patterns)
                                        + len(new_patterns)
                                        > _RESUMABLE_LFS_PATTERN_MAX_COUNT
                                    ):
                                        print(
                                            f"[批次 {batch_number}/{batch_count}] "
                                            "本次上传检测到的 LFS 扩展名超过自动配置上限；"
                                            "请手动配置 .gitattributes",
                                            flush=True,
                                        )
                                        raise
                                    if not new_patterns:
                                        if not patterns:
                                            print(
                                                f"[批次 {batch_number}/{batch_count}] "
                                                "无法从文件名推导安全的扩展名规则；"
                                                "请手动配置 .gitattributes",
                                                flush=True,
                                            )
                                        else:
                                            print(
                                                f"[批次 {batch_number}/{batch_count}] "
                                                "已尝试的 Git LFS 规则仍未生效；"
                                                "已停止自动修改以避免循环提交",
                                                flush=True,
                                            )
                                        raise
                                    attempted_lfs_patterns.update(new_patterns)
                                    if error.category == "lfs_attributes":
                                        print(
                                            f"[批次 {batch_number}/{batch_count}] "
                                            "检测到服务端判定为 LFS 的文件类型；"
                                            "正在检查远端 .gitattributes",
                                            flush=True,
                                        )
                                    else:
                                        print(
                                            f"[批次 {batch_number}/{batch_count}] "
                                            "检测到超大 regular 文件，需要配置 Git LFS",
                                            flush=True,
                                        )
                                    print(
                                        "将使用 --auto-configure-lfs 提交规则: "
                                        + ", ".join(new_patterns)
                                        + "（规则作用于整个仓库）",
                                        flush=True,
                                    )
                                    configuration_timeout = request_timeout
                                    if upload_deadline is not None:
                                        remaining = (
                                            upload_deadline - time.monotonic()
                                        )
                                        if remaining <= 0:
                                            raise TimeoutError(
                                                "resumable upload timed out "
                                                "during Git LFS configuration"
                                            )
                                        configuration_timeout = min(
                                            request_timeout, remaining
                                        )
                                    outcome = _configure_remote_lfs_attributes(
                                        token=credentials['token'],
                                        repo_id=normalized_repo_id,
                                        repo_type=eff_repo_type,
                                        revision=revision,
                                        patterns=new_patterns,
                                        request_timeout=configuration_timeout,
                                    )
                                    if outcome["changed"]:
                                        action = (
                                            "已创建" if outcome["created"]
                                            else "已更新"
                                        )
                                        continuation = (
                                            "正在刷新上传模式并重试当前批次"
                                            if error.category == "upload_mode"
                                            else "正在重试当前批次"
                                        )
                                        print(
                                            f"[批次 {batch_number}/{batch_count}] "
                                            f"{action}远端 .gitattributes；"
                                            f"{continuation}",
                                            flush=True,
                                        )
                                    else:
                                        continuation = (
                                            "正在刷新上传模式并重试当前批次"
                                            if error.category == "upload_mode"
                                            else "正在重试当前批次"
                                        )
                                        print(
                                            f"[批次 {batch_number}/{batch_count}] "
                                            "远端 .gitattributes 已包含所需规则；"
                                            f"{continuation}",
                                            flush=True,
                                        )
                        except Exception:
                            confirmed_in_batch = batch_skipped
                            if upload_root is not None:
                                confirmed_in_batch = max(
                                    confirmed_in_batch,
                                    _resumable_committed_file_count(
                                        upload_root, selected_paths, pipr
                                    ),
                                )
                            skipped_files += batch_skipped
                            submitted_files += max(
                                0, confirmed_in_batch - batch_skipped
                            )
                            completed_files += confirmed_in_batch
                            remaining_files = total_files - completed_files
                            print(
                                f"[批次 {batch_number}/{batch_count}] 失败: "
                                f"累计确认完成 {completed_files}/{total_files}，"
                                f"剩余 {remaining_files}",
                                flush=True,
                            )
                            print(
                                "断点元数据已保留；修复问题后重新执行同一命令可继续上传",
                                flush=True,
                            )
                            _print_upload_batch_summary(
                                total_files,
                                submitted_files,
                                skipped_files,
                                completed_files,
                            )
                            raise

                        skipped_files += batch_skipped
                        newly_submitted = batch_file_count - batch_skipped
                        submitted_files += newly_submitted
                        completed_files += batch_file_count
                        print(
                            f"[批次 {batch_number}/{batch_count}] 成功: "
                            f"新增提交 {newly_submitted}，续传跳过 {batch_skipped}，"
                            f"累计完成 {completed_files}/{total_files}",
                            flush=True,
                        )
                else:
                    # 仓库内目标前缀：空 → "./"（根目录）
                    upload_path_in_repo = pipr + "/" if pipr else "./"
                    upload_kwargs = dict(
                        repo_id=self._normalize_repo_id(repo_id),
                        folder_path=str(dir_path),
                        path_in_repo=upload_path_in_repo,
                        token=credentials['token'],
                        commit_message=commit_message,
                    )
                    upload_repo_type = _atomgit_repo_type(repo_type)
                    if upload_repo_type is not None:
                        upload_kwargs['repo_type'] = upload_repo_type
                    if revision is not None:
                        upload_kwargs['revision'] = revision
                    for batch_index, batch in enumerate(batches):
                        batch_number = batch_index + 1
                        batch_file_count = len(batch)
                        print(
                            f"[批次 {batch_number}/{batch_count}] 开始: "
                            f"{batch_file_count} 个文件",
                            flush=True,
                        )
                        try:
                            if batch:
                                upload_kwargs['allow_patterns'] = [
                                    item[0].as_posix() for item in batch
                                ]
                            if ignore_patterns:
                                upload_kwargs['ignore_patterns'] = ignore_patterns
                            run_canonical_lfs_upload(
                                lambda: _upload_folder_with_workers(
                                    upload_kwargs, num_workers or 5
                                ),
                                token=credentials['token'],
                                repo_id=upload_kwargs['repo_id'],
                                timeout=min(request_timeout, 15),
                            )
                        except Exception:
                            remaining_files = total_files - completed_files
                            print(
                                f"[批次 {batch_number}/{batch_count}] 失败: "
                                f"累计确认完成 {completed_files}/{total_files}，"
                                f"剩余 {remaining_files}",
                                flush=True,
                            )
                            _print_upload_batch_summary(
                                total_files,
                                submitted_files,
                                skipped_files,
                                completed_files,
                            )
                            raise
                        submitted_files += batch_file_count
                        completed_files += batch_file_count
                        print(
                            f"[批次 {batch_number}/{batch_count}] 成功: "
                            f"新增提交 {batch_file_count}，续传跳过 0，"
                            f"累计完成 {completed_files}/{total_files}",
                            flush=True,
                        )

                _print_upload_batch_summary(
                    total_files,
                    submitted_files,
                    skipped_files,
                    completed_files,
                )

                return True
            finally:
                hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
                close_hf_session()
                _restore_progress_bar_state(original_progress_state)

        except Exception as e:
            err_type, hint = _classify_upload_error(e, repo_id=repo_id)
            print(f"上传目录失败[{err_type}]")
            print(f"💡 建议: {hint}")
            return False
    



_repository_service._atomgit_open_url = _atomgit_open_url
_repository_service._is_not_found_error = _is_not_found_error
_authentication_service._sanitized_v5_api_error = _sanitized_v5_api_error
_download_service._is_not_found_error = _is_not_found_error
_download_integrity._is_not_found_error = _is_not_found_error
_download_transport._is_not_found_error = _is_not_found_error
_download_integrity._atomgit_open_url = _atomgit_open_url
_download_transport._atomgit_open_url = _atomgit_open_url

_DOWNLOAD_PATCH_TARGETS = {
    "errno": (_download_manifest,),
    "hashlib": (_download_integrity, _download_manifest, _download_resume),
    "json": (_download_manifest,),
    "ntpath": (_download_prune,),
    "os": (_download_manifest, _download_prune, _download_resume, _download_transport),
    "shutil": (_download_resume, _download_transport),
    "socket": (_download_transport,),
    "ssl": (_download_transport,),
    "stat": (_download_manifest, _download_prune),
    "tempfile": (_download_manifest, _download_resume, _download_transport),
    "time": (_download_resume,),
    "urllib": (
        _download_integrity,
        _download_manifest,
        _download_resume,
        _download_transport,
    ),
    "ExitStack": (_download_service,),
    "contextmanager": (_download_manifest, _download_resume),
    "Path": (
        _download_integrity,
        _download_manifest,
        _download_prune,
        _download_resume,
        _download_service,
        _download_transport,
    ),
    "PurePosixPath": (_download_prune,),
    "PureWindowsPath": (_download_prune,),
    "quote": (_download_transport,),
    "urljoin": (_download_integrity, _download_transport),
    "urlsplit": (_download_integrity, _download_resume, _download_transport),
    "config": (_download_service,),
    "HfApi": (_download_service,),
    "get_hf_file_metadata": (_download_integrity,),
    "hf_http_get": (_download_resume,),
    "is_auth_error": (_download_service,),
    "run_download_with_retry": (_download_transport,),
    "sanitized_download_error": (_download_service,),
    "DownloadChecksumMetadataError": (_download_integrity,),
    "DownloadChecksumMismatchError": (_download_integrity, _download_resume),
    "_DOWNLOAD_MANIFEST_VERSION": (_download_manifest,),
    "_DOWNLOAD_MANIFEST_MAX_BYTES": (_download_manifest,),
    "_atomgit_hf_endpoint": (
        _download_integrity,
        _download_manifest,
        _download_resume,
        _download_transport,
    ),
    "_atomgit_resolve_url": (_download_integrity, _download_resume, _download_transport),
    "_atomgit_resolve_url_raw": (
        _download_integrity,
        _download_resume,
        _download_transport,
    ),
    "_atomgit_file_checksum": (_download_integrity, _download_service),
    "_checksum_from_hf_metadata": (_download_integrity,),
    "_checksum_from_metadata_values": (_download_integrity,),
    "_atomgit_file_download_metadata": (_download_integrity, _download_resume),
    "_verify_download_checksum": (
        _download_integrity,
        _download_resume,
        _download_service,
        _download_transport,
    ),
    "_raw_metadata_size": (_download_integrity,),
    "_atomgit_file_download_metadata_raw": (_download_integrity,),
    "_set_private_file_mode": (_download_manifest,),
    "_download_manifest_root": (_download_manifest,),
    "_download_manifest_path": (_download_manifest, _download_service),
    "_load_download_manifest": (_download_manifest, _download_service),
    "_write_download_manifest": (_download_manifest, _download_service),
    "_windows_file_lock_module": (_download_manifest,),
    "_try_lock_download_manifest_descriptor_windows": (_download_manifest,),
    "_unlock_download_manifest_descriptor_windows": (_download_manifest,),
    "_try_lock_download_manifest_descriptor": (_download_manifest,),
    "_unlock_download_manifest_descriptor": (_download_manifest,),
    "_download_manifest_lock": (_download_manifest, _download_service),
    "_resume_cache_root": (_download_resume,),
    "_resume_cache_identity": (_download_resume,),
    "_process_is_running": (_download_resume,),
    "_resume_download_lock": (_download_resume,),
    "_copy_resumed_file_to_destination": (_download_resume,),
    "_parse_content_range": (_download_resume,),
    "_atomgit_resume_raw": (_download_resume,),
    "_download_atomgit_file_resumable": (_download_resume, _download_service),
    "_is_not_found_error": (
        _download_integrity,
        _download_service,
        _download_transport,
    ),
    "_atomgit_list_repo_files": (_download_service,),
    "_repository_filename_parts": (
        _download_manifest,
        _download_prune,
        _download_service,
    ),
    "_safe_download_destination": (_download_service,),
    "_WindowsFileAPI": (_download_prune,),
    "_normalized_windows_handle_path": (_download_prune,),
    "_prune_managed_download_file_windows": (_download_prune,),
    "_uses_windows_prune": (_download_prune,),
    "_prune_managed_download_file": (_download_prune,),
    "_prune_managed_download_files": (_download_prune, _download_service),
    "_download_url_origin": (_download_integrity, _download_transport),
    "_prepare_download_redirect": (
        _download_integrity,
        _download_resume,
        _download_transport,
    ),
    "_AtomGitRedirectHandler": (_download_transport,),
    "_atomgit_open_url": (_download_integrity, _download_transport),
    "_atomgit_raw_http_request": (_download_transport,),
    "_atomgit_raw_http_get": (
        _download_integrity,
        _download_resume,
        _download_transport,
    ),
    "_atomgit_raw_http_head": (_download_integrity,),
    "_copy_exact_http_body": (_download_transport,),
    "_read_chunk_line": (_download_transport,),
    "_copy_chunked_http_body": (_download_transport,),
    "_copy_framed_http_body": (_download_resume, _download_transport),
    "_atomgit_download_raw": (_download_transport,),
    "_download_atomgit_file": (_download_service, _download_transport),
}

# Preserve historical module-object patching while service methods resolve
# their dependencies in the new owner modules. The API module itself remains a
# partial implementation until the later transfer and facade program steps.
_PATCH_TARGETS = {
    "urllib": (_authentication_service, _repository_service),
    "json": (_authentication_service, _repository_service),
    "socket": (_repository_service,),
    "config": (_authentication_service, _repository_service),
    "create_repo": (_repository_service,),
    "HfApi": (_repository_service,),
    "quote": (_repository_service,),
    "auth_error_kind": (_repository_service,),
    "is_supported_upload_revision": (_repository_service,),
    "normalize_repo_id": (_repository_service,),
    "_atomgit_open_url": (_repository_service,),
    "_is_not_found_error": (_repository_service,),
    "_ATOMGIT_IDENTITY_MAX_JSON_BYTES": (_authentication_service,),
    "_ATOMGIT_V5_API_BASE": (_repository_service,),
    "_ATOMGIT_V5_MAX_JSON_BYTES": (_repository_service,),
    **{
        name: (_repository_service,)
        for name in (
            "_atomgit_repo_type",
            "_atomgit_repo_exists",
            "_atomgit_v5_branch_commit_id",
            "_atomgit_v5_commit_sha",
            "_atomgit_v5_get_json",
            "_atomgit_v5_repo_path",
            "_atomgit_v5_request_json",
            "_classify_create_repo_error",
            "_is_definitive_v5_write_error",
            "_repo_private_state",
        )
    },
    "_sanitized_v5_api_error": (
        _authentication_service,
        _repository_service,
    ),
}

for _patch_name, _download_targets in _DOWNLOAD_PATCH_TARGETS.items():
    _existing_targets = _PATCH_TARGETS.get(_patch_name, ())
    _PATCH_TARGETS[_patch_name] = tuple(
        dict.fromkeys((*_existing_targets, *_download_targets))
    )

    # Initialize every former resolution point from the historical module
    # before its forwarding module type becomes active.
    _patch_value = globals()[_patch_name]
    for _patch_target in _download_targets:
        setattr(_patch_target, _patch_name, _patch_value)

_FacadeModule = type(
    "_FacadeModule",
    (types.ModuleType,),
    {"__setattr__": _forward_legacy_patch, "__delattr__": _delete_legacy_patch},
)
sys.modules[__name__].__class__ = _FacadeModule

# 全局API实例
api = HuggingFaceAPI()
