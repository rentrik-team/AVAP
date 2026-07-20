"""Tracks in-flight scanner subprocesses so a running scan can be cancelled.

Scans execute in a background thread (see ScanService), so a separate HTTP
request handling a cancel action has no direct handle to the subprocess.
This module is a process-wide, in-memory registry bridging the two: the
executing thread registers its subprocess.Popen handle under the scan_id,
and the cancelling thread flips a flag the executor polls.

In-memory only: cancellation state does not survive a server restart, and
is not shared across multiple worker processes. That matches the current
single-process deployment; a multi-worker deployment would need a shared
store (e.g. Redis) instead.
"""

import subprocess  # nosec B404 -- handle tracking only, no invocation (see scanner_executor.py)
import threading
import uuid


class _RunningScan:
    def __init__(self, process: subprocess.Popen):
        self.process = process
        self.cancel_requested = threading.Event()


class ScanRuntimeRegistry:
    """Thread-safe registry of currently executing scanner subprocesses."""

    _lock = threading.Lock()
    _running: dict[uuid.UUID, _RunningScan] = {}

    @classmethod
    def register(cls, scan_id: uuid.UUID, process: subprocess.Popen) -> None:
        """Record the subprocess handle for a scan that just started executing."""
        with cls._lock:
            cls._running[scan_id] = _RunningScan(process)

    @classmethod
    def unregister(cls, scan_id: uuid.UUID) -> None:
        """Remove a scan's entry once its subprocess has finished."""
        with cls._lock:
            cls._running.pop(scan_id, None)

    @classmethod
    def request_cancel(cls, scan_id: uuid.UUID) -> bool:
        """Flag a running scan for cancellation.

        Returns:
            True if an active scan was found and flagged, False if no
            matching scan is currently executing (already finished, or
            never started in this process).
        """
        with cls._lock:
            running = cls._running.get(scan_id)
        if running is None:
            return False
        running.cancel_requested.set()
        return True

    @classmethod
    def is_cancel_requested(cls, scan_id: uuid.UUID) -> bool:
        """Whether cancellation has been requested for the given scan."""
        with cls._lock:
            running = cls._running.get(scan_id)
        return running is not None and running.cancel_requested.is_set()

    @classmethod
    def is_running(cls, scan_id: uuid.UUID) -> bool:
        """Whether a scan currently has an active, registered subprocess."""
        with cls._lock:
            return scan_id in cls._running
