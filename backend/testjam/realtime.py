"""WebSocket pub/sub connection manager.

Topic-based registry. Topics are arbitrary strings; the convention used by the
rest of the app is:

- ``user:{id}``       — per-user push (notifications, prefs changes)
- ``project:{id}``    — execution lifecycle within a project
- ``execution:{id}``  — result/step updates while a run is active

Single in-process registry — fine for single-replica dev. For HA swap the
broadcast helper with a Redis pub/sub fanout (P2.11.12).
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._by_topic: dict[str, set[WebSocket]] = defaultdict(set)
        self._ws_topics: dict[WebSocket, set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, topic: str, ws: WebSocket) -> None:
        async with self._lock:
            self._by_topic[topic].add(ws)
            self._ws_topics[ws].add(topic)

    async def unsubscribe(self, topic: str, ws: WebSocket) -> None:
        async with self._lock:
            self._discard_locked(topic, ws)

    async def unsubscribe_all(self, ws: WebSocket) -> None:
        async with self._lock:
            for topic in list(self._ws_topics.get(ws, ())):
                self._discard_locked(topic, ws)

    async def broadcast(self, topic: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            sockets = list(self._by_topic.get(topic, ()))
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    for topic in list(self._ws_topics.get(ws, ())):
                        self._discard_locked(topic, ws)

    def topics_for(self, ws: WebSocket) -> set[str]:
        return set(self._ws_topics.get(ws, ()))

    def subscribers(self, topic: str) -> int:
        return len(self._by_topic.get(topic, ()))

    def _discard_locked(self, topic: str, ws: WebSocket) -> None:
        bucket = self._by_topic.get(topic)
        if bucket is not None:
            bucket.discard(ws)
            if not bucket:
                self._by_topic.pop(topic, None)
        ws_bucket = self._ws_topics.get(ws)
        if ws_bucket is not None:
            ws_bucket.discard(topic)
            if not ws_bucket:
                self._ws_topics.pop(ws, None)

    # Backwards-compatible helpers for the legacy /notifications/ws endpoint.
    async def connect(self, user_id: int, ws: WebSocket) -> None:
        await ws.accept()
        await self.subscribe(f"user:{user_id}", ws)

    async def disconnect(self, user_id: int, ws: WebSocket) -> None:
        await self.unsubscribe_all(ws)

    async def send_to_user(self, user_id: int, payload: dict[str, Any]) -> None:
        await self.broadcast(f"user:{user_id}", payload)


manager = ConnectionManager()

_main_loop: asyncio.AbstractEventLoop | None = None


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Capture the API's main event loop so sync handlers can dispatch onto it."""
    global _main_loop
    _main_loop = loop


def _schedule(coro: Any) -> None:
    """Run an async manager call from sync or async code.

    From an async context (running loop), schedules a task on the current loop.
    From a sync context (FastAPI sync handler in the threadpool), forwards the
    coroutine to the captured main loop via ``run_coroutine_threadsafe``.
    If neither is available (sync unit tests with no loop at all), the
    coroutine is closed silently — persisted state is still readable via REST.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
        return
    except RuntimeError:
        pass
    if _main_loop is not None and _main_loop.is_running():
        asyncio.run_coroutine_threadsafe(coro, _main_loop)
        return
    coro.close()


def notify_user(user_id: int, payload: dict[str, Any]) -> None:
    _schedule(manager.broadcast(f"user:{user_id}", payload))


def notify_project(project_id: int, payload: dict[str, Any]) -> None:
    _schedule(manager.broadcast(f"project:{project_id}", payload))


def notify_execution(execution_id: int, payload: dict[str, Any]) -> None:
    _schedule(manager.broadcast(f"execution:{execution_id}", payload))
