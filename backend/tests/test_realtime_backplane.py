"""Redis-backed cross-worker fan-out for the realtime ConnectionManager."""
from __future__ import annotations

import asyncio
from typing import Any

import fakeredis.aioredis
import pytest

from testjam.realtime import ConnectionManager
from testjam.realtime_backplane import RedisBackplane, get_backplane, set_backplane


CHANNEL_PREFIX = "rt-test"
DELIVERY_GRACE_SECONDS = 0.1


class StubWS:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    async def send_json(self, payload: dict[str, Any]) -> None:
        self.sent.append(payload)


@pytest.fixture
def fake_server():
    return fakeredis.aioredis.FakeServer()


@pytest.fixture(autouse=True)
def clear_global_backplane():
    yield
    set_backplane(None)


@pytest.mark.asyncio
async def test_backplane_fans_out_across_managers(fake_server):
    publisher_manager = ConnectionManager()
    subscriber_manager = ConnectionManager()
    publisher_backplane = await _start_backplane(fake_server, publisher_manager)
    subscriber_backplane = await _start_backplane(fake_server, subscriber_manager)

    ws = StubWS()
    await subscriber_manager.subscribe("project:1", ws)  # type: ignore[arg-type]
    set_backplane(publisher_backplane)

    await publisher_manager.broadcast("project:1", {"event": "execution.created"})
    await asyncio.sleep(DELIVERY_GRACE_SECONDS)

    assert ws.sent == [{"event": "execution.created"}]
    assert publisher_manager.subscribers("project:1") == 0

    await publisher_backplane.stop()
    await subscriber_backplane.stop()


@pytest.mark.asyncio
async def test_broadcast_falls_back_to_local_without_backplane():
    manager = ConnectionManager()
    ws = StubWS()
    await manager.subscribe("project:1", ws)  # type: ignore[arg-type]

    await manager.broadcast("project:1", {"event": "local-only"})

    assert ws.sent == [{"event": "local-only"}]
    assert get_backplane() is None


@pytest.mark.asyncio
async def test_backplane_isolates_topics(fake_server):
    publisher_manager = ConnectionManager()
    subscriber_manager = ConnectionManager()
    publisher_backplane = await _start_backplane(fake_server, publisher_manager)
    subscriber_backplane = await _start_backplane(fake_server, subscriber_manager)

    subscribed_ws, other_ws = StubWS(), StubWS()
    await subscriber_manager.subscribe("project:1", subscribed_ws)  # type: ignore[arg-type]
    await subscriber_manager.subscribe("project:2", other_ws)  # type: ignore[arg-type]
    set_backplane(publisher_backplane)

    await publisher_manager.broadcast("project:1", {"event": "x"})
    await asyncio.sleep(DELIVERY_GRACE_SECONDS)

    assert subscribed_ws.sent == [{"event": "x"}]
    assert other_ws.sent == []

    await publisher_backplane.stop()
    await subscriber_backplane.stop()


async def _start_backplane(server, manager: ConnectionManager) -> RedisBackplane:
    client = fakeredis.aioredis.FakeRedis(server=server, decode_responses=True)
    backplane = RedisBackplane(client, CHANNEL_PREFIX, manager.deliver_local)
    await backplane.start()
    return backplane
