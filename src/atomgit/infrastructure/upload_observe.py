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


def render_session(session: Dict[str, Any]) -> str:
    header = "会话 {session_id} | {status} | 仓库 {repo} | 批次 {batch}".format(
        session_id=session.get("session_id", "-"),
        status=session.get("status", "-"),
        repo=session.get("repo_name", "-"),
        batch=session.get("batch", "-"),
    )
    lines = [header, "Flow  文件缩写  5秒速度  30秒速度  低速  替换  状态"]
    for flow in session.get("flows", []):
        name = flow.get("file_abbrev") or abbreviate_basename(
            str(flow.get("basename", ""))
        )
        lines.append(
            f"{flow.get('flow_id', '-')}  {name}  {flow.get('sample_speed', '--')}  {flow.get('window_speed', '--')}  {flow.get('slow_windows', '--')}  {flow.get('replacement_count', '--')}  {flow.get('phase', '--')}"
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
        # Child upload workers may inherit the observer after fork; persist the
        # bounded event immediately because the parent's publisher thread is
        # intentionally not shared across processes.
        publish_snapshot(self.data)

    def finish(self, status: str = "finished") -> None:
        self.update(status=status, finished_at=str(time.time()))

    def close(self) -> None:
        self.publisher.stop()
