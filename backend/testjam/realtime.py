"""WebSocket connection manager for per-user push notifications.

Single in-process registry — fine for single-replica dev. For HA you'd swap
the broadcast helper with a Redis pub/sub fanout.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._by_user: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._by_user[user_id].add(ws)

    async def disconnect(self, user_id: int, ws: WebSocket) -> None:
        async with self._lock:
            self._by_user.get(user_id, set()).discard(ws)
            if not self._by_user.get(user_id):
                self._by_user.pop(user_id, None)

    async def send_to_user(self, user_id: int, payload: dict[str, Any]) -> None:
        async with self._lock:
            sockets = list(self._by_user.get(user_id, ()))
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                await self.disconnect(user_id, ws)


manager = ConnectionManager()


def notify_user(user_id: int, payload: dict[str, Any]) -> None:
    """Schedule a websocket push from sync code (e.g. a request handler).

    Uses the running asyncio loop. If no loop is available (tests with sync
    TestClient + sqlite + a worker thread), the call is dropped silently — the
    persisted notification is still readable via the REST endpoint.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.create_task(manager.send_to_user(user_id, payload))
