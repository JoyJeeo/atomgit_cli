"""Child-owned LFS progress and coordinated console output."""

import logging
import math
import sys
import threading
import time
from datetime import datetime
from pathlib import PurePosixPath
from weakref import WeakSet

from tqdm import tqdm


class _ProgressStream:
    """Keep each thread's print fragments together before moving the bars."""

    def __init__(self, owner, stream):
        self.owner = owner
        self.stream = stream
        self.pending = {}

    def __getattr__(self, name):
        return getattr(self.stream, name)

    def write(self, text):
        with self.owner.lock:
            key = threading.get_ident()
            value = self.pending.pop(key, "") + text
            head, separator, tail = value.rpartition("\n")
            if separator:
                self.owner.write(head + separator, self.stream)
            if tail:
                self.pending[key] = tail
        return len(text)

    def flush(self):
        with self.owner.lock:
            pending = self.pending.pop(threading.get_ident(), "")
            if pending:
                self.owner.write(pending, self.stream)
            self.stream.flush()


class _UploadProgress:
    """Render existing five-second samples; never participate in upload policy."""

    def __init__(self, enabled=True, *, monotonic=time.monotonic):
        self.enabled = enabled
        self.monotonic = monotonic
        self.lock = threading.RLock()
        self.names = {}
        self.bars = {}
        self.last_log = {}
        self.fresh = set()
        self.streams = None

    def __enter__(self):
        # A child must own its bar positions and lock, not inherit a parent's
        # active tqdm instances or clear unrelated progress displays.
        class FileBar(tqdm):
            monitor_interval = 0
            _instances = WeakSet()
            _lock = threading.RLock()

        self.bar_type = FileBar
        self.original = (sys.stdout, sys.stderr)
        self.output = sys.stdout
        self.dynamic = self.enabled and all(
            getattr(stream, "isatty", lambda: False)() for stream in self.original
        )
        self.streams = tuple(_ProgressStream(self, stream) for stream in self.original)
        self.handlers = []
        loggers = [logging.root, *list(logging.Logger.manager.loggerDict.values())]
        handlers = set()
        for logger in loggers:
            if isinstance(logger, logging.Logger):
                handlers.update(logger.handlers)
        for handler in handlers:
            if isinstance(handler, logging.StreamHandler) and "stream" in vars(handler):
                for original, replacement in zip(self.original, self.streams):
                    if handler.stream is original:
                        self.handlers.append((handler, original))
                        handler.stream = replacement
                        break
        sys.stdout, sys.stderr = self.streams
        return self

    def write(self, text, stream=None):
        target = self.output if stream is None else stream
        with self.lock:
            # All bars use self.output, including when a log goes to stderr.
            with self.bar_type.external_write_mode(file=self.output):
                target.write(text)
                target.flush()

    def observe(self, message):
        if not self.enabled or self.streams is None:
            return
        with self.lock:
            key = message["flow_key"]
            if message["type"] == "file_name":
                name = PurePosixPath(message["name"]).name
                self.names[key] = "".join(c if c.isprintable() else "?" for c in name)
                self.last_log.pop(key, None)
                self.fresh.add(key)
                return
            if message["type"] != "flow_state":
                return
            state = message["payload"]
            name = self.names.get(key, f"文件 {key}")
            # The number also distinguishes identical basenames in nested folders.
            label = f"[{key}] {name}"
            total = state["size"]
            done = max(0, total - state["remaining_bytes"])
            phase = state["phase"]
            terminal = phase in ("completed", "failed")
            if phase == "completed":
                done = total
            speed = state["sample_speed"]
            if key in self.fresh:
                self.fresh.remove(key)
                done, speed = 0, None
            rate = (
                tqdm.format_sizeof(speed, suffix="B/s") if speed is not None else "--"
            )
            eta = (
                tqdm.format_interval(math.ceil((total - done) / speed))
                if speed and speed > 0
                else "--"
            )
            if self.dynamic:
                bar = self.bars.get(key)
                if bar is None and not terminal:
                    bar = self.bar_type(
                        total=total,
                        desc=label,
                        unit="B",
                        unit_scale=True,
                        leave=False,
                        file=self.output,
                        dynamic_ncols=True,
                    )
                    self.bars[key] = bar
                if bar is not None:
                    bar.n = done
                    bar.bar_format = (
                        "{desc} {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} "
                        + f"{rate} 剩余约{eta}"
                    )
                    if terminal:
                        bar.close()
                        self.bars.pop(key)
                    else:
                        bar.refresh()
            now = self.monotonic()
            if terminal:
                status = (
                    "传输完成，等待提交确认"
                    if phase == "completed"
                    else "传输中断，结果以重试或批次最终确认为准"
                )
                self.write(f"[{datetime.now():%H:%M:%S}] {label} {status}\n")
                self.last_log.pop(key, None)
            elif not self.dynamic and now - self.last_log.get(key, -math.inf) >= 10:
                percent = 100 * done / total if total else 0
                self.write(
                    f"[{datetime.now():%H:%M:%S}] {label} 上传中：{percent:.0f}%，"
                    f"{tqdm.format_sizeof(done, suffix='B')}/"
                    f"{tqdm.format_sizeof(total, suffix='B')}，{rate}，剩余约{eta}\n"
                )
                self.last_log[key] = now

    def close(self):
        with self.lock:
            if self.streams is None:
                return
            streams, self.streams = self.streams, None
            try:
                for bar in self.bars.values():
                    try:
                        bar.close()
                    except Exception:
                        pass
                self.bars.clear()
                for proxy in streams:
                    for text in proxy.pending.values():
                        try:
                            self.write(text, proxy.stream)
                        except Exception:
                            pass
                    proxy.pending.clear()
            finally:
                sys.stdout, sys.stderr = self.original
                for handler, original in self.handlers:
                    handler.stream = original

    def __exit__(self, *args):
        self.close()

    @staticmethod
    def clear_terminal():
        """Reclaim the child's live area after exit, including kill/Ctrl+C."""
        try:
            if all(
                getattr(stream, "isatty", lambda: False)()
                for stream in (sys.stdout, sys.stderr)
            ):
                sys.stdout.write("\r\033[J")
                sys.stdout.flush()
        except Exception:
            pass
