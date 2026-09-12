"""Canonical AtomGit LFS protocol, transfer recovery, and attributes owner.

The historical API preserves its compatibility surface and injects its former
module-level dependencies into this adapter owner.
"""

import json
import math
import os
import random
import socket
import tempfile
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path, PurePosixPath
from statistics import median
from typing import Optional
from urllib.parse import quote

import httpx
import huggingface_hub.lfs as hf_lfs
from huggingface_hub import HfApi
from huggingface_hub._local_folder import get_local_upload_paths, read_upload_metadata

# Compatibility-injected dependencies formerly resolved from atomgit.api or the
# upload error/projection owners. They are assigned by atomgit.api at import.
_atomgit_hf_endpoint = None
_atomgit_open_url = None
_atomgit_resolve_url = None
_atomgit_v5_get_json = None
_atomgit_v5_repo_path = None
_atomgit_v5_commit_sha = None
_resumable_error_chain = None
_resumable_error_status = None
_resumable_worker_error_category = None
_RESUMABLE_WORKER_ERROR_MESSAGES = None

_RESUMABLE_LFS_PREUPLOAD_MAX_ATTEMPTS = 3
_RESUMABLE_LFS_PREUPLOAD_BACKOFF_BASE = 2.0
_RESUMABLE_LFS_PREUPLOAD_WAIT_CAP = 60.0
_RESUMABLE_LFS_ERROR_BODY_MAX_BYTES = 16 * 1024
_SLOW_FLOW_SAMPLE_SECONDS = 5.0
_SLOW_FLOW_WINDOW_SECONDS = 30.0
_SLOW_FLOW_REQUIRED_WINDOWS = 3
_SLOW_FLOW_MAX_REPLACEMENTS = 3
_upload_observer = None


def set_upload_observer(callback):
    """Install an optional non-blocking observer callback for LFS events."""
    global _upload_observer
    _upload_observer = callback


def _dispatch_upload_observation(
    source_id, *, envelope: Optional[dict] = None, terminal: Optional[str] = None
) -> None:
    """Deliver one parent-owned observation without affecting an upload."""
    if _upload_observer is None:
        return
    packet = {"source_id": source_id}
    if envelope is not None:
        packet["envelope"] = envelope
    elif terminal is not None:
        packet["terminal"] = terminal
    else:
        return
    try:
        _upload_observer(packet)
    except Exception:
        pass


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
    flow_key: int = 0
    file_abbrev: str = ""
    transfer_type: str = "basic"
    speeds: list = field(default_factory=list)
    trend: list = field(default_factory=list)
    stable_baseline: Optional[float] = None
    peer_baseline: Optional[float] = None
    current_speed: Optional[float] = None
    sample_speed: Optional[float] = None
    window_speed: Optional[float] = None
    remaining_bytes: int = 0
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
    phase: str = "establishing_baseline"
    last_decision: str = "none"


class _SlowFlowCoordinator:
    """Coordinate conservative, object-scoped slow-flow replacement decisions."""

    def __init__(
        self,
        *,
        monotonic=time.monotonic,
        reconnect_jitter=None,
        event_callback=None,
        observation_callback=None,
    ):
        self._monotonic = monotonic
        self._reconnect_jitter = reconnect_jitter or (lambda: random.uniform(2.0, 8.0))
        self._event_callback = event_callback
        self._observation_callback = observation_callback
        self._states = {}
        self._next_flow_key = 1
        self._probe_key = None
        self._lock = threading.Lock()

    def _emit(self, kind: str, **details) -> None:
        if _upload_observer is not None:
            try:
                _upload_observer({"kind": kind, **details})
            except Exception:
                pass
        if self._event_callback is None:
            return
        try:
            self._event_callback({"kind": kind, **details})
        except Exception:
            pass

    def _publish(self, message: dict) -> None:
        if self._observation_callback is None:
            return
        try:
            self._observation_callback(message)
        except Exception:
            pass

    @staticmethod
    def _state_message(state: _SlowFlowState) -> dict:
        return {
            "type": "flow_state",
            "flow_key": state.flow_key,
            "payload": {
                "file_abbrev": state.file_abbrev,
                "type": state.transfer_type,
                "size": state.total_bytes,
                "remaining_bytes": state.remaining_bytes,
                "sample_speed": state.sample_speed,
                "window_speed": state.window_speed,
                "stable_baseline": state.stable_baseline,
                "peer_baseline": state.peer_baseline,
                "slow_windows": state.slow_windows,
                "replacement_count": state.replacements,
                "phase": state.phase,
                "last_decision": state.last_decision,
                "trend": list(state.trend),
            },
        }

    @staticmethod
    def _event_message(state: _SlowFlowState, event: str, **details) -> dict:
        return {
            "type": "flow_event",
            "flow_key": state.flow_key,
            "payload": {"event": event, **details},
        }

    def register(
        self,
        object_key,
        *,
        total_bytes: int,
        file_abbrev: str = "",
        transfer_type: str = "basic",
    ) -> None:
        if (
            not isinstance(total_bytes, int)
            or isinstance(total_bytes, bool)
            or total_bytes < 0
        ):
            raise ValueError("LFS object size is invalid")
        if transfer_type not in ("basic", "multipart"):
            raise ValueError("LFS transfer type is invalid")
        abbreviation = PurePosixPath(str(file_abbrev)).name[-10:]
        with self._lock:
            state = self._states.get(object_key)
            if state is None:
                state = _SlowFlowState(
                    total_bytes=total_bytes,
                    flow_key=self._next_flow_key,
                    file_abbrev=abbreviation,
                    transfer_type=transfer_type,
                    remaining_bytes=total_bytes,
                )
                self._states[object_key] = state
                self._next_flow_key += 1
            else:
                state.active = True
                if state.total_bytes != total_bytes:
                    raise RuntimeError("LFS object size changed during upload")
                state.phase = (
                    "stable"
                    if state.stable_baseline is not None
                    else "establishing_baseline"
                )
                state.last_decision = "none"
            message = self._state_message(state)
        self._publish(message)

    def complete(self, object_key, *, reset_windows: bool = False) -> None:
        message = None
        event = None
        with self._lock:
            state = self._states.get(object_key)
            if state is not None:
                state.active = False
                state.phase = "failed" if reset_windows else "completed"
                state.last_decision = state.phase
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
                message = self._state_message(state)
                event = self._event_message(state, state.phase)
        if message is not None:
            self._publish(message)
            self._publish(event)

    def observe_sample(self, object_key, speed: float, remaining_bytes: int) -> None:
        if (
            not math.isfinite(speed)
            or speed < 0
            or not isinstance(remaining_bytes, int)
            or isinstance(remaining_bytes, bool)
            or remaining_bytes < 0
        ):
            return
        with self._lock:
            state = self._states.get(object_key)
            if state is None or not state.active:
                return
            state.sample_speed = float(speed)
            state.remaining_bytes = min(state.total_bytes, remaining_bytes)
            message = self._state_message(state)
        self._publish(message)

    def replacement_count(self, object_key) -> int:
        with self._lock:
            state = self._states.get(object_key)
            return state.replacements if state is not None else 0

    def is_disabled(self, object_key) -> bool:
        with self._lock:
            state = self._states.get(object_key)
            return state.disabled if state is not None else False

    def replacement_finished(self, object_key) -> None:
        message = None
        event = None
        with self._lock:
            state = self._states.get(object_key)
            if state is None:
                return
            state.awaiting_improvement = True
            state.fresh_speeds.clear()
            state.slow_windows = 0
            state.degraded_windows = 0
            state.phase = "verifying_reconnect"
            state.last_decision = "reconnect_started"
            message = self._state_message(state)
            event = self._event_message(
                state,
                "reconnect_started",
                replacement=state.replacements,
            )
        self._publish(message)
        self._publish(event)

    def _peer_baseline(self, object_key) -> Optional[float]:
        peers = [
            state
            for key, state in self._states.items()
            if key != object_key and state.active and len(state.speeds) >= 3
        ]
        if len(peers) < 2:
            return None
        windows = tuple(
            tuple(state.speeds[-offset] for state in peers) for offset in (3, 2, 1)
        )
        return _slow_flow_peer_baseline(windows)

    def _collective_slowdown(self) -> bool:
        active = [state for state in self._states.values() if state.active]
        return len(active) >= 2 and all(
            state.stable_baseline is not None
            and state.current_speed is not None
            and state.current_speed <= state.stable_baseline * 0.3
            and state.degraded_windows >= _SLOW_FLOW_REQUIRED_WINDOWS
            for state in active
        )

    def _collective_candidate(self) -> bool:
        active = [state for state in self._states.values() if state.active]
        return len(active) >= 2 and all(
            state.stable_baseline is not None
            and state.current_speed is not None
            and state.current_speed <= state.stable_baseline * 0.3
            and state.degraded_windows >= _SLOW_FLOW_REQUIRED_WINDOWS - 1
            for state in active
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
            state.phase = "replacement_disabled"
            state.last_decision = "replacement_disabled"
            return None
        now = self._monotonic()
        delay = self._replacement_delay(state, now)
        continue_time = remaining_bytes / speed
        replace_time = delay + (retransmit_bytes / expected_speed)
        if continue_time < 2.0 * replace_time:
            state.last_decision = "not_beneficial"
            return None
        if probe and self._probe_key is not None:
            state.last_decision = "probe_in_progress"
            return None
        state.replacements += 1
        state.last_replacement_at = now + delay
        state.replaced_speed = speed
        state.slow_windows = 0
        state.degraded_windows = 0
        state.probe = probe
        if probe:
            self._probe_key = object_key
        state.phase = "waiting_replacement"
        state.last_decision = "replacement_approved"
        decision = _SlowFlowDecision(
            object_key=object_key,
            replacement_number=state.replacements,
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
        decision = None
        event = None
        legacy_event = None
        with self._lock:
            state = self._states.get(object_key)
            if state is None:
                raise RuntimeError("LFS object is not registered")
            if state.disabled or not state.active:
                return None

            prior_baseline = state.stable_baseline
            state.current_speed = speed
            state.window_speed = float(speed)
            state.remaining_bytes = min(state.total_bytes, remaining_bytes)
            state.speeds.append(speed)
            if len(state.speeds) > 12:
                del state.speeds[:-12]
            state.trend.append(float(speed))
            if len(state.trend) > 12:
                del state.trend[:-12]

            if state.awaiting_improvement:
                state.phase = "verifying_reconnect"
                state.fresh_speeds.append(speed)
                if len(state.fresh_speeds) >= _SLOW_FLOW_REQUIRED_WINDOWS:
                    improved = float(median(state.fresh_speeds[-3:]))
                    replaced_speed = state.replaced_speed or 0.0
                    peer_baseline = self._peer_baseline(object_key)
                    state.peer_baseline = peer_baseline
                    state.awaiting_improvement = False
                    state.fresh_speeds.clear()
                    if improved < replaced_speed * 2.0 or (
                        peer_baseline is not None and improved < peer_baseline * 0.7
                    ):
                        state.disabled = True
                        state.phase = "replacement_disabled"
                        state.last_decision = "improvement_failed"
                        event = self._event_message(
                            state,
                            "improvement_failed",
                            replacement=state.replacements,
                        )
                        legacy_event = (
                            "lfs_slow_flow_disabled",
                            {"reason": "no_improvement"},
                        )
                    else:
                        state.stable_baseline = improved
                        state.speeds = [improved] * 3
                        state.phase = "recovered"
                        state.last_decision = "improvement_passed"
                        state.probe = False
                        event = self._event_message(
                            state,
                            "improvement_passed",
                            replacement=state.replacements,
                        )
                    if self._probe_key == object_key:
                        self._probe_key = None
            else:
                if prior_baseline is None and len(state.speeds) >= 3:
                    state.stable_baseline = _slow_flow_stable_baseline(
                        state.speeds[-3:]
                    )
                    prior_baseline = state.stable_baseline

                if prior_baseline is None:
                    state.phase = "establishing_baseline"
                    state.last_decision = "none"
                else:
                    if speed <= prior_baseline * 0.3:
                        state.degraded_windows += 1
                    else:
                        state.degraded_windows = 0

                    peer_baseline = self._peer_baseline(object_key)
                    state.peer_baseline = peer_baseline
                    if peer_baseline is not None:
                        slow = (
                            speed <= peer_baseline * 0.3
                            and speed <= prior_baseline * 0.5
                        )
                        expected_speed = peer_baseline
                    else:
                        slow = speed <= prior_baseline * 0.3
                        expected_speed = prior_baseline
                    state.slow_windows = state.slow_windows + 1 if slow else 0
                    state.phase = "suspected_slow" if slow else "stable"
                    state.last_decision = "none"

                    retransmit = (
                        state.total_bytes
                        if retransmit_bytes is None
                        else retransmit_bytes
                    )
                    if self._collective_slowdown():
                        decision = self._decide(
                            object_key,
                            state,
                            speed=speed,
                            remaining_bytes=remaining_bytes,
                            retransmit_bytes=retransmit,
                            expected_speed=prior_baseline,
                            probe=True,
                        )
                    elif self._collective_candidate():
                        state.last_decision = "collective_wait"
                    elif self._probe_key is not None:
                        state.last_decision = "probe_in_progress"
                    elif state.slow_windows < _SLOW_FLOW_REQUIRED_WINDOWS:
                        if not slow:
                            recent_baseline = _slow_flow_stable_baseline(
                                state.speeds[-3:]
                            )
                            if recent_baseline is not None:
                                state.stable_baseline = recent_baseline
                    else:
                        decision = self._decide(
                            object_key,
                            state,
                            speed=speed,
                            remaining_bytes=remaining_bytes,
                            retransmit_bytes=retransmit,
                            expected_speed=expected_speed,
                            probe=False,
                        )
                    if decision is not None:
                        event = self._event_message(
                            state,
                            "replacement_approved",
                            replacement=decision.replacement_number,
                            delay=decision.delay,
                            probe=decision.probe,
                        )
                        legacy_event = (
                            "lfs_slow_flow_replace",
                            {
                                "replacement": decision.replacement_number,
                                "delay": decision.delay,
                                "probe": decision.probe,
                            },
                        )
                    elif state.disabled:
                        event = self._event_message(
                            state,
                            "replacement_disabled",
                            replacement=state.replacements,
                        )
                    elif slow:
                        event = self._event_message(
                            state,
                            "slow_observed",
                            slow_windows=state.slow_windows,
                        )
            message = self._state_message(state)
        self._publish(message)
        if event is not None:
            self._publish(event)
        if legacy_event is not None:
            self._emit(legacy_event[0], **legacy_event[1])
        return decision


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
            sample_elapsed = self._sample_elapsed
            sample_bytes = self._sample_bytes
            self._window_elapsed += sample_elapsed
            self._window_bytes += self._sample_bytes
            self._sample_elapsed = 0.0
            self._sample_bytes = 0
            remaining = max(
                0,
                self._total_bytes - self._confirmed_bytes - self._delivered_bytes,
            )
            self._coordinator.observe_sample(
                self._object_key,
                sample_bytes / sample_elapsed,
                remaining,
            )
            if self._window_elapsed >= _SLOW_FLOW_WINDOW_SECONDS:
                speed = self._window_bytes / self._window_elapsed
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
        self._coordinator.register(
            object_key,
            total_bytes=total_bytes,
            file_abbrev=str(operation.path_in_repo),
            transfer_type="basic",
        )
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
            self._coordinator.complete(object_key, reset_windows=not succeeded)

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
        self._coordinator.register(
            object_key,
            total_bytes=total_bytes,
            file_abbrev=str(operation.path_in_repo),
            transfer_type="multipart",
        )
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
                                    "PUT",
                                    part_url,
                                    data=payload,
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
                        self._wait_for_replacement(operation, identity, reconnect)
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
            self._coordinator.complete(object_key, reset_windows=not succeeded)


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
            and getattr(metadata, "size", 0) > _RESUMABLE_REGULAR_FILE_MAX_BYTES
        ):
            pattern = _lfs_pattern_from_repo_path(getattr(paths, "path_in_repo", None))
            if pattern is not None:
                patterns.add(pattern)
    return _validated_lfs_patterns(patterns)


def _resumable_lfs_patterns(items) -> tuple:
    """Infer safe extension rules for items already selected for LFS."""
    patterns = set()
    for paths, metadata in items:
        if getattr(metadata, "upload_mode", None) == "lfs" and not getattr(
            metadata, "should_ignore", False
        ):
            pattern = _lfs_pattern_from_repo_path(getattr(paths, "path_in_repo", None))
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


class ResumableLfsPreuploadError(RuntimeError):
    """A resumable LFS preupload failed under the bounded retry policy."""

    def __init__(self, category: str):
        if category not in _RESUMABLE_WORKER_ERROR_MESSAGES:  # noqa: F821
            category = "unknown"
        self.category = category
        super().__init__(_RESUMABLE_WORKER_ERROR_MESSAGES[category])  # noqa: F821


class _ResumableLfsAttributesPolicy:
    """Gate LFS work until its extension rules are confirmed remotely."""

    def __init__(self, configured_patterns=()):
        self._configured = set(_validated_lfs_patterns(configured_patterns))
        self._lock = threading.Lock()

    def validate_patterns(self, patterns) -> None:
        validated = _validated_lfs_patterns(patterns)
        with self._lock:
            missing = tuple(
                pattern for pattern in validated if pattern not in self._configured
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
        if metadata.upload_mode == "lfs" and not metadata.should_ignore:
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
    return f"{pattern} filter=lfs diff=lfs merge=lfs -text".encode("ascii")


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
        pattern
        for pattern in validated
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
        if _validated_lfs_patterns((pattern,)) != (
            pattern,
        ) or line != _lfs_gitattributes_line(pattern):
            break
        effective.add(pattern)
    return all(pattern in effective for pattern in validated)


def _remote_revision_commit_sha(
    *,
    token: str,
    repo_id: str,
    revision: str,
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
    *,
    token: str,
    repo_id: str,
    repo_type: str,
    revision: str,
    destination: Path,
    request_timeout: float,
) -> bool:
    """Download only root `.gitattributes`, returning False only for file 404."""
    request = urllib.request.Request(
        _atomgit_resolve_url(repo_id, repo_type, _LFS_GITATTRIBUTES_PATH, revision),
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
                    raise ValueError("远端 .gitattributes 长度无效") from error
                if declared_size < 0:
                    raise ValueError("远端 .gitattributes 长度无效")
                if declared_size > _LFS_GITATTRIBUTES_MAX_BYTES:
                    raise ValueError("远端 .gitattributes 过大，无法安全自动修改")
            content = response.read(_LFS_GITATTRIBUTES_MAX_BYTES + 1)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            files = HfApi(endpoint=_atomgit_hf_endpoint(), token=token).list_repo_files(
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
    *,
    token: str,
    repo_id: str,
    repo_type: str,
    revision: str,
    patterns,
    request_timeout: float,
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
                HfApi(endpoint=_atomgit_hf_endpoint(), token=token).upload_file(
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
            verified_content = attributes_path.read_bytes() if verified_exists else b""
            if _gitattributes_contains_lfs_patterns(verified_content, appended):
                return {
                    "changed": True,
                    "created": not existed,
                    "verified_after_error": write_error is not None,
                    "patterns": appended,
                }
            if write_error is None:
                raise RuntimeError(".gitattributes 提交后远端验证失败")
            if (
                _resumable_error_status(write_error) not in (409, 412)  # noqa: F821
                or attempt + 1 >= _LFS_GITATTRIBUTES_MAX_ATTEMPTS
            ):
                raise write_error

    raise RuntimeError(".gitattributes 并发更新重试次数已耗尽")


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
    if (
        not isinstance(content, bytes)
        or len(content) > _RESUMABLE_LFS_ERROR_BODY_MAX_BYTES
    ):
        return None
    try:
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _is_atomgit_lfs_quota_error(error: BaseException) -> bool:
    if _resumable_error_status(error) != 413:  # noqa: F821
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
    for cause in _resumable_error_chain(error):  # noqa: F821
        if isinstance(cause, ResumableLfsPreuploadError):
            return cause.category, False
        status_code = _resumable_error_status(cause)  # noqa: F821
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
    category = _resumable_worker_error_category(error)  # noqa: F821
    return category, False


class _ResumableLfsPreuploadController:
    """Bound retries before HF's worker can requeue an LFS preupload job."""

    def __init__(
        self,
        preupload_lfs,
        *,
        sleep=time.sleep,
        jitter=None,
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
            self._emit(
                {
                    "kind": "lfs_preupload_exhausted",
                    "category": category,
                    "attempts": attempts,
                }
            )
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
                self._emit(
                    {
                        "kind": "lfs_preupload_retry",
                        "category": category,
                        "attempt": attempt + 1,
                        "max_attempts": self._max_attempts,
                        "delay": delay,
                    }
                )
                self._sleep(delay)


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
