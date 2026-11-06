"""File-isolated upload rounds over the locked HF metadata and transfer helpers."""

import json
import math
import os
import sys
import tempfile
import threading
import time
from collections import deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path, PurePosixPath

import huggingface_hub._upload_large_folder as hf
from huggingface_hub._local_folder import (
    LocalUploadFileMetadata,
    get_local_upload_paths,
    read_upload_metadata,
)

from .errors import (
    _RESUMABLE_WORKER_ERROR_MESSAGES,
    _UPLOAD_STAGES,
    ResumableRecoveryStateError,
    ResumableWorkerError,
    _classify_upload_error,
    _format_upload_diagnostic,
    _resumable_error_chain,
    _resumable_failure_envelope,
    _validated_upload_diagnostic,
)
from .projection import _read_resumable_upload_metadata

_TRANSIENT = {
    "connection",
    "timeout",
    "service_unavailable",
    "rate_limit",
    "local_source_unavailable",
}
_GLOBAL = {
    "authentication",
    "permission",
    "repository",
    "revision",
    "lfs_quota",
    "lfs_bandwidth",
    "remote_commit_conflict",
    "remote_recovery_state",
    "worker_process",
}


def retry_category(error):
    envelope = _resumable_failure_envelope(error, stage="unknown")
    category = envelope["category"]
    diagnostic = getattr(error, "diagnostic", None) or envelope.get("diagnostic", {})
    # An expired object-store URL does not establish invalid repository access.
    if diagnostic.get("operation") == "object_upload" and category in {
        "authentication",
        "permission",
        "repository",
    }:
        return "connection"
    if category in {"remote_commit_unconfirmed", "lfs_pointer"}:
        reason = envelope.get("confirmation_failure") or getattr(
            error, "confirmation_failure", None
        )
        return {
            "authentication_failed": "authentication",
            "permission_denied": "permission",
            "rate_limited": "rate_limit",
            "service_unavailable": "service_unavailable",
            "request_timeout": "timeout",
            "connection_failed": "connection",
            "content_mismatch": "remote_recovery_state",
            "response_malformed": "remote_recovery_state",
            "response_too_large": "remote_recovery_state",
        }.get(reason, category)
    return category


def retry_delay(error, rounds=0, base=10.0):
    """Respect Retry-After even when it exceeds the ordinary backoff cap."""
    for cause in _resumable_error_chain(error):
        response = getattr(cause, "response", None)
        value = getattr(response, "headers", {}).get("Retry-After")
        if not value:
            continue
        try:
            delay = float(value)
        except (ValueError, TypeError):
            try:
                target = parsedate_to_datetime(value)
                if target.tzinfo is None:
                    target = target.replace(tzinfo=timezone.utc)
                delay = (target - datetime.now(timezone.utc)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                continue
        if math.isfinite(delay) and delay >= 0:
            return delay
    return min(300.0, base * 2 ** min(rounds, 5))


def _warning(message, *, abnormal=False):
    if sys.stdout.isatty() and sys.stderr.isatty() and "NO_COLOR" not in os.environ:
        color = "31" if abnormal else "33"
        message = f"\033[{color}m{message}\033[0m"
    sys.stdout.write(message + "\n")
    sys.stdout.flush()


def _failure_details(error, stage="unknown"):
    """Describe a failure using classified reasons and allowlisted diagnostics."""
    category = retry_category(error)
    diagnostic = _resumable_failure_envelope(error, stage=stage).get("diagnostic", {})
    reason = _classify_upload_error(ResumableWorkerError(category))[0]
    if category == "unknown":
        reason = "未识别，现有诊断不足以确定"
        local_reasons = {
            "selected file is excluded by upload policy": "选中的文件不符合本次上传过滤规则",
            "server excluded a selected file": "服务端将选中的文件标记为忽略，尚未提交",
            "source changed during upload": "文件在上传过程中发生变化，需重新检查",
            "source changed before commit": "文件在提交前发生变化，需重新检查",
        }
        if (
            type(error) is ValueError
            and len(error.args) == 1
            and isinstance(error.args[0], str)
        ):
            reason = local_reasons.get(error.args[0], reason)
    detail = _format_upload_diagnostic(diagnostic)
    return (
        f"阶段：{_UPLOAD_STAGES.get(diagnostic.get('stage', stage), '未知')}\n"
        f"原因：{reason}（{category}）" + (f"；{detail}" if detail else "")
    )


class RetryReport:
    """Task-wide queue accounting, without timers or terminal output."""

    def __init__(self):
        self.batches = {}

    def counts(self):
        return {
            "queued": sum(
                item.get("queued", item["pending"] - item["abnormal"])
                for item in self.batches.values()
            ),
            "abnormal": sum(item["abnormal"] for item in self.batches.values()),
        }


def _queue_counts(queued, active, abnormal, other):
    return (
        f"当前候补：{queued + other.get('queued', 0)} 个｜"
        f"正在补传：{active} 个｜"
        f"异常待处理：{abnormal + other.get('abnormal', 0)} 个"
    )


class RetryState:
    """Small atomic sidecar; HF metadata remains the authority for completion."""

    def __init__(self, root):
        self.path = root / ".cache/huggingface/atomgit/retry-state-v1.json"
        self.files = {}
        self.lock = threading.RLock()
        try:
            for directory in (self.path.parent, *self.path.parent.parents):
                if directory == root:
                    break
                if directory.is_symlink():
                    raise ValueError("unsafe retry directory")
            if self.path.is_symlink():
                raise ValueError("unsafe retry state")
            if self.path.exists():
                if self.path.stat().st_size > 256 * 1024:
                    raise ValueError("oversized retry state")
                value = json.loads(self.path.read_text(encoding="utf-8"))
                if (
                    set(value) != {"version", "files"}
                    or type(value["version"]) is not int
                    or value["version"] != 1
                ):
                    raise ValueError("invalid retry version")
                self.files = value["files"]
                if not isinstance(self.files, dict) or len(self.files) > 20:
                    raise ValueError("invalid retry files")
                for key, record in self.files.items():
                    if not isinstance(key, str) or not isinstance(record, dict):
                        raise ValueError("invalid retry record")
                    parsed = PurePosixPath(key)
                    if (
                        not key
                        or parsed.is_absolute()
                        or ".." in parsed.parts
                        or "\\" in key
                        or parsed.as_posix() != key
                        or key.startswith(".cache/huggingface/")
                    ):
                        raise ValueError("unsafe retry path")
                    required = {
                        "attempts",
                        "failures",
                        "rounds",
                        "category",
                        "stage",
                        "status",
                        "next_attempt",
                        "updated_at",
                    }
                    if (
                        not required
                        <= set(record)
                        <= required | {"signature", "diagnostic"}
                    ):
                        raise ValueError("invalid retry fields")
                    if (
                        record["category"] not in _RESUMABLE_WORKER_ERROR_MESSAGES
                        or record["stage"] not in _UPLOAD_STAGES
                    ):
                        raise ValueError("invalid retry reason")
                    if record["status"] not in {
                        "ready",
                        "prepare",
                        "commit",
                        "committed",
                        "retry",
                        "abnormal",
                    }:
                        raise ValueError("invalid retry status")
                    if "diagnostic" in record:
                        record["diagnostic"] = _validated_upload_diagnostic(
                            record["diagnostic"]
                        )
                    signature = record.get("signature")
                    if signature is not None and (
                        not isinstance(signature, list)
                        or len(signature) != 2
                        or any(type(n) is not int or n < 0 for n in signature)
                    ):
                        raise ValueError("invalid source signature")
                    for field in ("attempts", "failures", "rounds"):
                        if type(record[field]) is not int or record[field] < 0:
                            raise ValueError("invalid retry count")
                    if record["attempts"] > 3:
                        raise ValueError("invalid round attempts")
                    for field in ("next_attempt", "updated_at"):
                        if type(record[field]) not in (float, int) or not math.isfinite(
                            record[field]
                        ):
                            raise ValueError("invalid retry time")
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise ResumableRecoveryStateError("retry state is unsafe") from error

    def record(self, name):
        return self.files.setdefault(
            name,
            {
                "attempts": 0,
                "failures": 0,
                "rounds": 0,
                "category": "unknown",
                "stage": "prepare",
                "status": "ready",
                "next_attempt": 0.0,
                "updated_at": time.time(),
            },
        )

    def record_failure(self, name, error, category):
        """Persist one failed attempt and its next eligible retry atomically."""
        with self.lock:
            record = self.record(name)
            record["attempts"] += 1
            record["failures"] += 1
            record["category"] = category
            diagnostic = _resumable_failure_envelope(error, stage=record["stage"]).get(
                "diagnostic", {}
            )
            record["diagnostic"] = diagnostic
            record["updated_at"] = time.time()
            exhausted = record["attempts"] >= 3
            if exhausted:
                record["rounds"] += 1
            delay = retry_delay(
                error,
                record["rounds"] if exhausted else 0,
                base=(
                    10.0
                    if exhausted or category not in _TRANSIENT
                    else 2.0 ** record["attempts"]
                ),
            )
            record["next_attempt"] = time.time() + delay
            record["status"] = "retry" if category in _TRANSIENT else "abnormal"
            self.save()
        return delay, exhausted

    def pending_summary(self, names, source_paths=None):
        """Reconstruct waiting retries for the current selection, not stale records."""
        pending = abnormal = failures = confirmed = 0
        root = self.path.parents[3]
        for name in dict.fromkeys(names):
            record = self.files.get(name)
            if not record or not record["failures"]:
                continue
            try:
                source = (
                    Path(source_paths[name])
                    if source_paths is not None
                    else root / name
                )
                current = source.stat()
                metadata = _read_resumable_upload_metadata(root, name, current.st_size)
                if metadata["is_committed"] and record.get("signature") == [
                    current.st_size,
                    current.st_mtime_ns,
                ]:
                    confirmed += 1
                    continue
            except (OSError, ValueError):
                pass  # Unavailable or invalid metadata cannot prove completion.
            failures += record["failures"]
            if record["category"] not in _TRANSIENT:
                abnormal += 1
                pending += 1
            elif record["rounds"] or record["attempts"] >= 3:
                pending += 1
        return {
            "pending": pending,
            "abnormal": abnormal,
            "failures": failures,
            "confirmed": confirmed,
        }

    def save(self):
        with self.lock:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                os.chmod(self.path.parent, 0o700)
                descriptor, temporary = tempfile.mkstemp(
                    prefix=".retry-", dir=self.path.parent
                )
                try:
                    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                        json.dump({"version": 1, "files": self.files}, stream)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary, self.path)
                finally:
                    Path(temporary).unlink(missing_ok=True)
            except OSError as error:
                raise ResumableRecoveryStateError(
                    "retry state cannot be saved"
                ) from error


def run_upload_round(
    api,
    repo_id,
    folder_path,
    *,
    repo_type,
    revision=None,
    private=None,
    allow_patterns=None,
    ignore_patterns=None,
    num_workers=None,
    print_report=True,
    print_report_every=60,
    selected_paths=None,
    retry_counts=None,
    batch_context=None,
):
    """Drain one round, returning deferred files without falsifying HF metadata."""
    root = Path(folder_path)
    names = list(
        hf.filter_repo_objects(
            (
                p.relative_to(root).as_posix()
                for p in root.rglob("*")
                if p.is_file() or p.is_symlink()
            ),
            allow_patterns=allow_patterns,
            ignore_patterns=list(ignore_patterns or []) + hf.DEFAULT_IGNORE_PATTERNS,
        )
    )
    state = RetryState(root)
    allowed = set(names)
    # The parent's frozen selection distinguishes missing files from a later
    # invocation's changed filters or batch membership.
    if selected_paths is not None:
        names = list(dict.fromkeys(selected_paths))
        state.files = {
            name: record for name, record in state.files.items() if name in names
        }
    else:
        names = list(dict.fromkeys([*names, *state.files]))
    if len(names) > 20:
        raise ResumableRecoveryStateError("upload round exceeds projection limit")
    ready = deque()
    commits = deque()
    active = {}
    items = {}
    signatures = {}
    deferred = set()
    queued = set()
    abnormal_waiting = set()
    other = retry_counts or {}
    committed = set()
    previously_committed = set()
    cooldown = 0.0
    consecutive_failures = 0
    last_report = time.monotonic()
    for name in names:
        record = state.record(name)
        summary = state.pending_summary([name])
        if summary["confirmed"]:
            previously_committed.add(name)
        if summary["abnormal"]:
            abnormal_waiting.add(name)
        elif summary["pending"]:
            queued.add(name)
        if record["next_attempt"] > time.time():
            deferred.add(name)
        else:
            if record["attempts"] >= 3:
                record["attempts"] = 0
            ready.append(name)

    def label(name):
        prefix = (
            f"[批次 {batch_context[0]}/{batch_context[1]}] " if batch_context else ""
        )
        filename = "".join(
            c if c.isprintable() else "?" for c in PurePosixPath(name).name
        )
        return f"{prefix}文件 {names.index(name) + 1}（{filename[:240]}）"

    def counts(starting=None):
        working = {
            n
            for n, _ in active.values()
            if state.record(n)["failures"] and n not in previously_committed
        }
        if starting is not None:
            working.add(starting)
        return _queue_counts(len(queued), len(working), len(abnormal_waiting), other)

    kwargs = dict(
        api=api, repo_id=repo_id, repo_type=repo_type, revision=revision or "main"
    )

    def transfer(name):
        record = state.record(name)
        with state.lock:
            record["stage"] = "prepare"
        paths = get_local_upload_paths(root, name)
        current = paths.file_path.stat()
        if name not in allowed:
            raise ValueError("selected file is excluded by upload policy")
        signature = (current.st_size, current.st_mtime_ns)
        metadata = read_upload_metadata(root, name)
        previous = record.get("signature")
        if previous is not None and list(signature) != previous:
            metadata = LocalUploadFileMetadata(size=current.st_size)
        signatures[name] = signature
        with state.lock:
            record["signature"] = list(signature)
            state.save()
        item = (paths, metadata)
        items[name] = item
        if metadata.is_committed:
            if record["failures"]:
                print(f"[恢复方式] {label(name)}：已确认提交，跳过上传", flush=True)
            return "committed"
        if record["failures"] or metadata.sha256:
            reuse = "复用已有哈希" if metadata.sha256 else "重新计算哈希"
            if metadata.upload_mode == "lfs" and metadata.is_uploaded:
                recovery = "本地记录对象已上传，尝试复用并核对提交；失效时重新上传"
            elif metadata.upload_mode == "lfs":
                recovery = "重新查询对象；如需上传，整文件 PUT 从头传输"
            elif metadata.upload_mode == "regular":
                recovery = "等待普通文件提交"
            else:
                recovery = "重新查询上传方式，不能据此恢复文件内字节进度"
            print(f"[恢复方式] {label(name)}：{reuse}；{recovery}", flush=True)
        hf._compute_sha256(item)
        with state.lock:
            record["stage"] = "upload_mode"
        if metadata.upload_mode is None or metadata.should_ignore is not False:
            hf._get_upload_mode([item], **kwargs)
        if metadata.should_ignore:
            # A server exclusion is not evidence of a successful commit.
            raise ValueError("server excluded a selected file")
        with state.lock:
            record["stage"] = "preupload"
        if metadata.upload_mode == "lfs" and not metadata.is_uploaded:
            hf._preupload_lfs([item], **kwargs)
        after = paths.file_path.stat()
        if (after.st_size, after.st_mtime_ns) != signature:
            raise ValueError("source changed during upload")
        return "commit"

    def commit(name):
        paths, metadata = items[name]
        current = paths.file_path.stat()
        if (current.st_size, current.st_mtime_ns) != signatures[name]:
            raise ValueError("source changed before commit")
        with state.lock:
            state.record(name)["stage"] = "commit"
        hf._commit([(paths, metadata)], **kwargs)
        return "committed"

    workers = num_workers or 5
    pool = ThreadPoolExecutor(max_workers=workers)
    try:
        while ready or commits or active:
            now = time.time()
            commit_active = any(stage == "commit" for _, stage in active.values())
            while len(active) < workers and now >= cooldown:
                if commits and not commit_active:
                    name, stage, operation = commits.popleft(), "commit", commit
                    commit_active = True
                elif ready and any(
                    state.record(n)["next_attempt"] <= now for n in ready
                ):
                    while state.record(ready[0])["next_attempt"] > now:
                        ready.rotate(-1)
                    name, stage, operation = ready.popleft(), "prepare", transfer
                else:
                    break
                record = state.record(name)
                queued.discard(name)
                abnormal_waiting.discard(name)
                if (
                    stage == "prepare"
                    and record["failures"]
                    and name not in previously_committed
                ):
                    event = (
                        "开始补传"
                        if record["rounds"] or record["category"] not in _TRANSIENT
                        else "开始本轮重试"
                    )
                    print(
                        f"[{event}] {label(name)}\n[队列状态] {counts(starting=name)}\n",
                        end="",
                        flush=True,
                    )
                with state.lock:
                    record["status"] = stage
                active[pool.submit(operation, name)] = (name, stage)
            done, _ = (
                wait(active, timeout=0.1, return_when=FIRST_COMPLETED)
                if active
                else ((), ())
            )
            if not active:
                time.sleep(0.1)
            for future in done:
                name, stage = active.pop(future)
                record = state.record(name)
                try:
                    outcome = future.result()
                except Exception as error:
                    category = retry_category(error)
                    if category in _GLOBAL or category in {
                        "upload_mode",
                        "lfs_attributes",
                    }:
                        raise
                    consecutive_failures += 1
                    delay, exhausted = state.record_failure(name, error, category)
                    if category not in _TRANSIENT:
                        deferred.add(name)
                        abnormal_waiting.add(name)
                        event = "异常待处理"
                    elif exhausted:
                        deferred.add(name)
                        queued.add(name)
                        event = "加入候补"
                    else:
                        ready.append(name)
                        event = "本轮重试"
                    if category == "rate_limit" or (
                        category in _TRANSIENT and consecutive_failures >= workers
                    ):
                        cooldown = max(cooldown, time.time() + delay)
                    if event == "本轮重试":
                        action = f"等待至少 {delay:g} 秒后进行本轮重试"
                    elif event == "加入候补":
                        action = f"已让出上传位置，至少 {delay:g} 秒后轮转补传"
                    else:
                        action = f"保留断点并让出上传位置，至少 {delay:g} 秒后重新检查"
                    _warning(
                        f"[上传失败] {label(name)}\n"
                        f"本轮失败：{record['attempts']}/3｜累计失败：{record['failures']} 次\n"
                        f"{_failure_details(error, record['stage'])}\n"
                        f"处理：[{event}] {action}\n"
                        f"[队列状态] {counts()}",
                        abnormal=category not in _TRANSIENT,
                    )
                else:
                    consecutive_failures = 0
                    queued.discard(name)
                    abnormal_waiting.discard(name)
                    with state.lock:
                        record["status"] = outcome
                        record["next_attempt"] = 0.0
                        if outcome == "commit":
                            commits.append(name)
                        else:
                            committed.add(name)
                        state.save()
            if print_report and time.monotonic() - last_report >= print_report_every:
                last_report = time.monotonic()
                print(
                    f"[上传状态] 已哈希 {sum(bool(m.sha256) for _, m in items.values())}/{len(names)}，"
                    f"已预上传 {sum(m.is_uploaded for _, m in items.values())}，"
                    f"已提交 {len(committed)}，补传/异常待处理 {len(deferred)}，"
                    f"工作中 {len(active)}",
                    flush=True,
                )
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    pending = len(names) - len(committed)
    return {
        "pending": pending,
        "delay": max(
            0.0,
            min((state.record(n)["next_attempt"] for n in deferred), default=0)
            - time.time(),
        ),
        "abnormal": len(abnormal_waiting),
        "failures": sum(r["failures"] for r in state.files.values()),
        "cooldown": max(0.0, cooldown - time.time()),
    }
