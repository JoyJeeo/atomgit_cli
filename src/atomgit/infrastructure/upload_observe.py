"""Read-only upload observability snapshots and terminal rendering."""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

MAX_EVENTS = 200
MAX_TREND = 12
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SESSION_FIELDS = {
    "session_id",
    "repo_name",
    "repo_type",
    "revision",
    "status",
    "created_at",
    "started_at",
    "finished_at",
    "updated_at",
    "batch",
    "files_total",
    "files_done",
    "bytes_total",
    "bytes_done",
    "active_flows",
    "peak_flows",
    "replacement_total",
    "improvement_total",
    "disabled_total",
    "events",
    "flows",
    "version",
}
_FLOW_FIELDS = {
    "flow_id",
    "file_id",
    "file_abbrev",
    "basename",
    "size",
    "type",
    "sample_speed",
    "window_speed",
    "stable_baseline",
    "peer_baseline",
    "slow_windows",
    "replacement_count",
    "remaining_bytes",
    "phase",
    "updated_at",
    "last_decision",
    "trend",
}
_FLOW_STATE_FIELDS = {
    "file_abbrev",
    "type",
    "size",
    "remaining_bytes",
    "sample_speed",
    "window_speed",
    "stable_baseline",
    "peer_baseline",
    "slow_windows",
    "replacement_count",
    "phase",
    "last_decision",
    "trend",
}
_FLOW_PHASES = {
    "establishing_baseline",
    "stable",
    "suspected_slow",
    "waiting_replacement",
    "verifying_reconnect",
    "recovered",
    "replacement_disabled",
    "completed",
    "failed",
    "interrupted",
}
_FLOW_TERMINAL_PHASES = {"completed", "failed", "interrupted"}
_FLOW_DECISIONS = {
    "none",
    "collective_wait",
    "probe_in_progress",
    "not_beneficial",
    "replacement_approved",
    "reconnect_started",
    "improvement_passed",
    "improvement_failed",
    "replacement_disabled",
    "completed",
    "failed",
    "interrupted",
}
_FLOW_EVENT_FIELDS = {"event", "replacement", "slow_windows", "delay", "probe"}
_FLOW_EVENTS = {
    "slow_observed",
    "replacement_approved",
    "reconnect_started",
    "improvement_passed",
    "improvement_failed",
    "replacement_disabled",
    "completed",
    "failed",
}
_PHASE_LABELS = {
    "establishing_baseline": "建立基线",
    "stable": "稳定",
    "suspected_slow": "疑似低速",
    "waiting_replacement": "等待替换",
    "verifying_reconnect": "重连后验证",
    "recovered": "已恢复",
    "replacement_disabled": "自动替换已停用",
    "completed": "完成",
    "failed": "失败",
    "interrupted": "已中断",
}
_EVENT_LABELS = {
    "slow_observed": "进入低速观察",
    "replacement_approved": "已批准连接替换",
    "reconnect_started": "开始新连接",
    "improvement_passed": "替换后改善验证通过",
    "improvement_failed": "替换后改善验证失败",
    "replacement_disabled": "自动连接替换已停用",
    "completed": "上传完成",
    "failed": "上传失败",
}
_MAX_SAFE_INTEGER = (1 << 63) - 1
_MAX_SAFE_SPEED = float(1 << 60)


def observe_root() -> Path:
    root = Path(
        os.environ.get("HF_HOME", Path.home() / ".cache" / "atomgit")
    ).expanduser()
    directory = root / "upload-observe" / "v1"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    os.chmod(root / "upload-observe", 0o700)
    os.chmod(directory, 0o700)
    return directory


def publish_snapshot(session: Dict[str, Any]) -> Path:
    """Atomically publish a sanitized snapshot; failures never escape callers."""
    try:
        session = {k: v for k, v in dict(session).items() if k in _SESSION_FIELDS}
        session.setdefault("version", 1)
        session["events"] = list(session.get("events", []))[-MAX_EVENTS:]
        flows = []
        for flow in session.get("flows", []):
            item = {k: v for k, v in dict(flow).items() if k in _FLOW_FIELDS}
            if "basename" in item:
                item["basename"] = Path(str(item["basename"])).name
            if "file_abbrev" not in item and "basename" in item:
                item["file_abbrev"] = abbreviate_basename(item["basename"])
            item["trend"] = list(item.get("trend", []))[-MAX_TREND:]
            flows.append(item)
        session["flows"] = flows
        sid = str(session["session_id"])
        if not _SAFE_ID.fullmatch(sid):
            return Path("")
        path = observe_root() / f"{sid}.json"
        fd, tmp = tempfile.mkstemp(
            prefix=f".{sid}.", suffix=".tmp", dir=str(path.parent)
        )
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(session, handle, ensure_ascii=False, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, path)
            os.chmod(path, 0o600)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        return path
    except Exception:
        return Path("")


def load_sessions() -> List[Dict[str, Any]]:
    result = []
    try:
        for path in observe_root().glob("*.json"):
            try:
                with path.open(encoding="utf-8") as handle:
                    value = json.load(handle)
                if isinstance(value, dict) and value.get("session_id"):
                    result.append(value)
            except (OSError, ValueError, TypeError):
                continue
    except OSError:
        return []
    return sorted(
        result,
        key=lambda s: (
            s.get("status") in ("active", "uploading", "上传中"),
            s.get("updated_at", ""),
        ),
        reverse=True,
    )


def select_session(session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    sessions = load_sessions()
    if session_id is not None:
        return next(
            (s for s in sessions if str(s.get("session_id")) == session_id), None
        )
    active = [
        s for s in sessions if s.get("status") in ("active", "uploading", "上传中")
    ]
    pool = active or sessions
    return max(pool, key=lambda s: s.get("updated_at", ""), default=None)


def abbreviate_basename(name: str) -> str:
    return name if len(name) <= 10 else name[-10:]


def _valid_integer(value: Any, lower: int = 0, upper: int = _MAX_SAFE_INTEGER) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and lower <= value <= upper
    )


def _valid_speed(value: Any, *, optional: bool = True) -> bool:
    if value is None:
        return optional
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and 0 <= value <= _MAX_SAFE_SPEED
    )


def _valid_flow_state(payload: Any) -> bool:
    if not isinstance(payload, dict) or set(payload) != _FLOW_STATE_FIELDS:
        return False
    abbreviation = payload.get("file_abbrev")
    trend = payload.get("trend")
    size = payload.get("size")
    remaining = payload.get("remaining_bytes")
    return (
        isinstance(abbreviation, str)
        and len(abbreviation) <= 10
        and "/" not in abbreviation
        and "\\" not in abbreviation
        and payload.get("type") in ("basic", "multipart")
        and _valid_integer(size)
        and _valid_integer(remaining, upper=size)
        and all(
            _valid_speed(payload.get(name))
            for name in (
                "sample_speed",
                "window_speed",
                "stable_baseline",
                "peer_baseline",
            )
        )
        and _valid_integer(payload.get("slow_windows"), upper=3)
        and _valid_integer(payload.get("replacement_count"), upper=3)
        and payload.get("phase") in _FLOW_PHASES
        and payload.get("last_decision") in _FLOW_DECISIONS
        and isinstance(trend, list)
        and len(trend) <= MAX_TREND
        and all(_valid_speed(speed, optional=False) for speed in trend)
    )


def _valid_flow_event(payload: Any) -> bool:
    if (
        not isinstance(payload, dict)
        or not {"event"} <= set(payload) <= _FLOW_EVENT_FIELDS
        or payload.get("event") not in _FLOW_EVENTS
    ):
        return False
    if "replacement" in payload and not _valid_integer(payload["replacement"], upper=3):
        return False
    if "slow_windows" in payload and not _valid_integer(
        payload["slow_windows"], upper=3
    ):
        return False
    if "delay" in payload and not _valid_speed(payload["delay"], optional=False):
        return False
    return "probe" not in payload or isinstance(payload["probe"], bool)


def _format_speed(value: Any) -> str:
    if not _valid_speed(value) or value is None:
        return "--"
    speed = float(value)
    if speed >= 1024 * 1024:
        return f"{speed / (1024 * 1024):.1f}MiB/s"
    if speed >= 1024:
        return f"{speed / 1024:.1f}KiB/s"
    return f"{speed:.1f}B/s"


def _relative_baseline(flow: Dict[str, Any]) -> str:
    reference = flow.get("peer_baseline") or flow.get("stable_baseline")
    speed = flow.get("window_speed")
    if not _valid_speed(reference) or not reference or not _valid_speed(speed):
        return "--"
    return f"{float(speed) / float(reference):.0%}"


def _render_trend(flow: Dict[str, Any]) -> str:
    reference = flow.get("peer_baseline") or flow.get("stable_baseline")
    trend = flow.get("trend", [])
    if not reference or not _valid_speed(reference) or not isinstance(trend, list):
        return "·" * min(len(trend), MAX_TREND) or "--"
    levels = "▁▂▃▄▅▆▇█"
    thresholds = (0.15, 0.3, 0.5, 0.7, 0.9, 1.1, 1.3)
    result = []
    for speed in trend[-MAX_TREND:]:
        ratio = float(speed) / float(reference)
        result.append(levels[sum(ratio >= threshold for threshold in thresholds)])
    return "".join(result) or "--"


def render_session(session: Dict[str, Any]) -> str:
    header = "会话 {session_id} | {status} | 仓库 {repo} | 批次 {batch}".format(
        session_id=session.get("session_id", "-"),
        status=session.get("status", "-"),
        repo=session.get("repo_name", "-"),
        batch=session.get("batch", "-"),
    )
    lines = [header]
    if "files_total" in session:
        lines.append(
            f"已确认文件 {session.get('files_done', 0)}/{session['files_total']}"
        )
    lines.extend(
        [
            f"活跃 Flow {session.get('active_flows', 0)} | 累计替换 {session.get('replacement_total', 0)}",
            "Flow  文件缩写  5秒速度  30秒速度  相对基线  低速  替换  最近6分钟  状态",
        ]
    )
    for flow in session.get("flows", []):
        name = flow.get("file_abbrev") or abbreviate_basename(
            str(flow.get("basename", ""))
        )
        lines.append(
            f"{flow.get('flow_id', '-')}  {name or '-'}  "
            f"{_format_speed(flow.get('sample_speed'))}  "
            f"{_format_speed(flow.get('window_speed'))}  "
            f"{_relative_baseline(flow)}  "
            f"{flow.get('slow_windows', 0)}/3  "
            f"{flow.get('replacement_count', 0)}/3  "
            f"{_render_trend(flow)}  "
            f"{_PHASE_LABELS.get(flow.get('phase'), flow.get('phase', '--'))}"
        )
    events = session.get("events", [])[-5:]
    if events:
        lines.append("最近事件")
        lines.extend(str(event.get("message", event)) for event in events)
    return "\n".join(lines)


def render_list(sessions: Iterable[Dict[str, Any]]) -> str:
    lines = ["SESSION  状态  批次  最近更新"]
    for session in sessions:
        lines.append(
            f"{session.get('session_id', '-')}  {session.get('status', '-')}  {session.get('batch', '-')}  {session.get('updated_at', '-')}"
        )
    return "\n".join(lines)


class SnapshotPublisher:
    """Bounded, best-effort background snapshot publisher."""

    def __init__(self, interval: float = 1.0, heartbeat: float = 2.0):
        self.interval = max(0.1, float(interval))
        self.heartbeat = max(self.interval, float(heartbeat))
        self._latest: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> "SnapshotPublisher":
        if self._thread is None or not self._thread.is_alive():
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._run, name="atomgit-upload-observe", daemon=True
            )
            self._thread.start()
        return self

    def submit(self, session: Dict[str, Any]) -> None:
        with self._lock:
            self._latest = dict(session)
        self._wake.set()

    def stop(self, timeout: float = 1.0) -> None:
        with self._lock:
            snapshot = dict(self._latest) if self._latest is not None else None
        if snapshot is not None:
            publish_snapshot(snapshot)
        self._stop.set()
        self._wake.set()
        if self._thread is not None:
            self._thread.join(timeout=max(0.0, timeout))

    def _run(self) -> None:
        last_write = 0.0
        while not self._stop.is_set():
            self._wake.wait(timeout=self.heartbeat)
            self._wake.clear()
            now = time.monotonic()
            with self._lock:
                snapshot = dict(self._latest) if self._latest is not None else None
            if snapshot is not None and now - last_write >= self.interval:
                publish_snapshot(snapshot)
                last_write = now


class UploadSession:
    """Small upload-owned facade that never exposes worker objects."""

    def __init__(
        self,
        session_id: str,
        *,
        repo_name: str = "",
        repo_type: str = "model",
        revision: str = "main",
        publisher: Optional[SnapshotPublisher] = None,
    ):
        self.data: Dict[str, Any] = {
            "session_id": session_id,
            "repo_name": str(repo_name).rsplit("/", 1)[-1],
            "repo_type": repo_type,
            "revision": revision,
            "status": "active",
            "created_at": str(time.time()),
            "updated_at": str(time.time()),
            "events": [],
            "flows": [],
        }
        self._source_sequences: Dict[Any, int] = {}
        self._flow_ids: Dict[Any, str] = {}
        self._improved_flows = set()
        self._disabled_flows = set()
        self._next_flow_id = 1
        self.publisher = publisher or SnapshotPublisher().start()
        self.publisher.submit(self.data)

    def update(self, **fields: Any) -> None:
        self.data.update(fields)
        self.data["updated_at"] = str(time.time())
        self.publisher.submit(self.data)

    def event(self, message: str, kind: str = "info") -> None:
        events = list(self.data.get("events", []))
        events.append(
            {"kind": kind, "message": str(message), "updated_at": str(time.time())}
        )
        self.data["events"] = events[-MAX_EVENTS:]
        self.update()

    def _refresh_flow_totals(self) -> None:
        flows = self.data.get("flows", [])
        active = sum(flow.get("phase") not in _FLOW_TERMINAL_PHASES for flow in flows)
        self.data["active_flows"] = active
        self.data["peak_flows"] = max(self.data.get("peak_flows", 0), active)
        self.data["replacement_total"] = sum(
            flow.get("replacement_count", 0) for flow in flows
        )
        self.data["improvement_total"] = len(self._improved_flows)
        self.data["disabled_total"] = len(self._disabled_flows)

    def _flow_id(self, source_id, flow_key: int, *, create: bool) -> Optional[str]:
        identity = (source_id, flow_key)
        flow_id = self._flow_ids.get(identity)
        if flow_id is None and create:
            flow_id = f"Flow-{self._next_flow_id:02d}"
            self._next_flow_id += 1
            self._flow_ids[identity] = flow_id
        return flow_id

    def _observe_envelope(self, source_id, envelope: Any) -> bool:
        if (
            not isinstance(envelope, dict)
            or set(envelope) != {"version", "type", "sequence", "flow_key", "payload"}
            or envelope.get("version") != 1
            or envelope.get("type") not in ("flow_state", "flow_event")
            or not _valid_integer(envelope.get("sequence"), lower=1)
            or not _valid_integer(envelope.get("flow_key"), lower=1)
        ):
            return False
        message_type = envelope["type"]
        payload = envelope.get("payload")
        if message_type == "flow_state":
            if not _valid_flow_state(payload):
                return False
        elif not _valid_flow_event(payload):
            return False
        sequence = envelope["sequence"]
        if sequence <= self._source_sequences.get(source_id, 0):
            return False
        flow_id = self._flow_id(
            source_id,
            envelope["flow_key"],
            create=message_type == "flow_state",
        )
        if flow_id is None:
            return False

        now = str(time.time())
        if message_type == "flow_state":
            flow = {"flow_id": flow_id, **payload, "updated_at": now}
            flows = [
                dict(item)
                for item in self.data.get("flows", [])
                if item.get("flow_id") != flow_id
            ]
            flows.append(flow)
            flows.sort(key=lambda item: item.get("flow_id", ""))
            self.data["flows"] = flows
            if payload["last_decision"] == "improvement_passed":
                self._improved_flows.add(flow_id)
            if payload["phase"] == "replacement_disabled":
                self._disabled_flows.add(flow_id)
        else:
            event = dict(payload)
            event.update(
                {
                    "kind": payload["event"],
                    "flow_id": flow_id,
                    "message": f"{flow_id} {_EVENT_LABELS[payload['event']]}",
                    "updated_at": now,
                }
            )
            events = list(self.data.get("events", []))
            events.append(event)
            self.data["events"] = events[-MAX_EVENTS:]
            if payload["event"] == "improvement_passed":
                self._improved_flows.add(flow_id)
            if payload["event"] in (
                "improvement_failed",
                "replacement_disabled",
            ):
                self._disabled_flows.add(flow_id)
        self._source_sequences[source_id] = sequence
        self._refresh_flow_totals()
        self.update()
        return True

    def _converge_source(self, source_id, terminal: Any) -> bool:
        if terminal not in _FLOW_TERMINAL_PHASES:
            return False
        flow_ids = {
            flow_id
            for (known_source, _), flow_id in self._flow_ids.items()
            if known_source is source_id or known_source == source_id
        }
        changed = False
        flows = []
        now = str(time.time())
        for current in self.data.get("flows", []):
            flow = dict(current)
            if (
                flow.get("flow_id") in flow_ids
                and flow.get("phase") not in _FLOW_TERMINAL_PHASES
            ):
                flow["phase"] = terminal
                flow["last_decision"] = terminal
                flow["updated_at"] = now
                changed = True
            flows.append(flow)
        if not changed:
            return False
        self.data["flows"] = flows
        self._refresh_flow_totals()
        self.update()
        return True

    def observe(self, packet: Any) -> bool:
        """Validate and merge one parent-side structured observation."""
        try:
            if not isinstance(packet, dict) or "source_id" not in packet:
                return False
            source_id = packet["source_id"]
            hash(source_id)
            if set(packet) == {"source_id", "envelope"}:
                return self._observe_envelope(source_id, packet["envelope"])
            if set(packet) == {"source_id", "terminal"}:
                return self._converge_source(source_id, packet["terminal"])
            return False
        except Exception:
            return False

    def finish(self, status: str = "finished") -> None:
        self.update(status=status, finished_at=str(time.time()))

    def close(self) -> None:
        self.publisher.stop()
