"""Cross-worker pub/sub backplane for realtime broadcasts.

Without a backplane, each ``ConnectionManager`` only knows about WebSockets
attached to the same worker process. Once API is run with ``--workers > 1``
a publisher in worker A cannot reach subscribers in worker B.

This module provides a Redis-backed fan-out: every worker subscribes to a
shared pattern (``{prefix}:*``); ``broadcast`` publishes to that channel; each
worker's consumer task forwards the payload to its local sockets.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable

import redis.asyncio as redis_async

log = logging.getLogger("testjam.realtime")

LocalDeliver = Callable[[str, dict[str, Any]], Awaitable[None]]


class RedisBackplane:
    def __init__(
        self,
        client: redis_async.Redis,
        channel_prefix: str,
        local_deliver: LocalDeliver,
    ) -> None:
        self._client = client
        self._prefix = channel_prefix.rstrip(":")
        self._pattern = f"{self._prefix}:*"
        self._local_deliver = local_deliver
        self._pubsub: redis_async.client.PubSub | None = None
        self._consumer: asyncio.Task[None] | None = None

    @property
    def enabled(self) -> bool:
        return self._pubsub is not None and self._consumer is not None

    async def start(self) -> None:
        if self.enabled:
            return
        self._pubsub = self._client.pubsub()
        await self._pubsub.psubscribe(self._pattern)
        self._consumer = asyncio.create_task(self._consume(), name="rt-backplane-consumer")

    async def stop(self) -> None:
        if self._consumer is not None:
            self._consumer.cancel()
            try:
                await self._consumer
            except (asyncio.CancelledError, Exception):
                pass
            self._consumer = None
        if self._pubsub is not None:
            try:
                await self._pubsub.punsubscribe(self._pattern)
                await self._pubsub.aclose()
            except Exception:
                log.exception("Failed to close backplane pubsub cleanly")
            self._pubsub = None
        try:
            await self._client.aclose()
        except Exception:
            log.exception("Failed to close backplane redis client")

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        await self._client.publish(f"{self._prefix}:{topic}", json.dumps(payload))

    async def _consume(self) -> None:
        assert self._pubsub is not None
        prefix_len = len(self._prefix) + 1
        async for message in self._pubsub.listen():
            if message.get("type") != "pmessage":
                continue
            channel = message.get("channel") or ""
            data = message.get("data")
            if not channel or data is None:
                continue
            topic = channel[prefix_len:]
            try:
                payload = json.loads(data)
            except (TypeError, ValueError):
                log.warning("Discarded non-JSON backplane message on %s", channel)
                continue
            try:
                await self._local_deliver(topic, payload)
            except Exception:
                log.exception("Local fan-out failed for topic %s", topic)


_active: RedisBackplane | None = None


def get_backplane() -> RedisBackplane | None:
    return _active


def set_backplane(backplane: RedisBackplane | None) -> None:
    global _active
    _active = backplane


def build_backplane(url: str, channel_prefix: str, local_deliver: LocalDeliver) -> RedisBackplane:
    client = redis_async.from_url(url, decode_responses=True)
    return RedisBackplane(client, channel_prefix, local_deliver)
