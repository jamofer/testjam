"""Buffers ``step_result.log_appended`` payloads and flushes them in batches.

Robot Framework can emit hundreds of log lines per second. Persisting each
line is cheap (it appends to the existing column), but pushing one WebSocket
frame per line wastes bandwidth and chokes clients. This module accumulates
payloads per execution and flushes a single batched event after a configurable
debounce window (default ``100 ms``).

The flush interval is read from ``AppSettings.ws_log_flush_ms``. Admins can
tune it from the Settings page; :func:`configure` updates the in-process
cache without a restart.
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any

from testjam.realtime import manager

log = logging.getLogger("testjam.log_flusher")

DEFAULT_FLUSH_MS = 100


class LogFlusher:
    def __init__(self) -> None:
        self._buffers: dict[int, list[dict[str, Any]]] = defaultdict(list)
        self._pending: dict[int, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._flush_ms: int = DEFAULT_FLUSH_MS

    def configure(self, flush_ms: int | None) -> None:
        if flush_ms is None or flush_ms < 0:
            self._flush_ms = DEFAULT_FLUSH_MS
            return
        self._flush_ms = int(flush_ms)

    @property
    def flush_ms(self) -> int:
        return self._flush_ms

    async def append(self, execution_id: int, payload: dict[str, Any]) -> None:
        if self._flush_ms <= 0:
            await self._broadcast(execution_id, [payload])
            return
        async with self._lock:
            self._buffers[execution_id].append(payload)
            if execution_id in self._pending:
                return
            loop = asyncio.get_running_loop()
            self._pending[execution_id] = loop.create_task(
                self._flush_after_delay(execution_id),
            )

    async def _flush_after_delay(self, execution_id: int) -> None:
        try:
            await asyncio.sleep(self._flush_ms / 1000)
        except asyncio.CancelledError:
            return
        await self._drain(execution_id)

    async def _drain(self, execution_id: int) -> None:
        async with self._lock:
            entries = self._buffers.pop(execution_id, [])
            self._pending.pop(execution_id, None)
        if not entries:
            return
        await self._broadcast(execution_id, entries)

    async def _broadcast(self, execution_id: int, entries: list[dict[str, Any]]) -> None:
        await manager.broadcast(
            f"execution:{execution_id}",
            {"event": "step_result.log_appended", "data": {"entries": entries}},
        )


flusher = LogFlusher()


def schedule_append(execution_id: int, payload: dict[str, Any]) -> None:
    """Schedule a log-append from sync or async code.

    Routes the coroutine through :func:`testjam.realtime._schedule` so the
    behaviour matches the rest of the WebSocket dispatch path: tasks run on the
    captured main loop when called from a threadpool handler, on the current
    loop when called from an async one, and are dropped silently when neither
    is available.
    """
    from testjam.realtime import _schedule

    _schedule(flusher.append(execution_id, payload))


def configure_from_settings(settings_row: Any) -> None:
    flusher.configure(getattr(settings_row, "ws_log_flush_ms", None))
