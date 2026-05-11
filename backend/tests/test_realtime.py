"""ConnectionManager — topic pub/sub semantics.

Pure-asyncio unit tests against a stub WebSocket. No FastAPI client involved.
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from testjam.realtime import ConnectionManager, _schedule, manager as global_manager


class StubWS:
    def __init__(self, *, fail: bool = False) -> None:
        self.sent: list[dict[str, Any]] = []
        self.fail = fail

    async def send_json(self, payload: dict[str, Any]) -> None:
        if self.fail:
            raise RuntimeError("socket dead")
        self.sent.append(payload)


@pytest.fixture
def mgr() -> ConnectionManager:
    return ConnectionManager()


@pytest.mark.asyncio
async def test_subscribe_then_broadcast_delivers(mgr: ConnectionManager):
    ws = StubWS()
    await mgr.subscribe("project:1", ws)  # type: ignore[arg-type]

    await mgr.broadcast("project:1", {"event": "execution.created", "data": {"id": 7}})

    assert ws.sent == [{"event": "execution.created", "data": {"id": 7}}]


@pytest.mark.asyncio
async def test_broadcast_isolated_per_topic(mgr: ConnectionManager):
    a, b = StubWS(), StubWS()
    await mgr.subscribe("project:1", a)  # type: ignore[arg-type]
    await mgr.subscribe("project:2", b)  # type: ignore[arg-type]

    await mgr.broadcast("project:1", {"event": "x"})

    assert a.sent == [{"event": "x"}]
    assert b.sent == []


@pytest.mark.asyncio
async def test_multiple_subscribers_same_topic(mgr: ConnectionManager):
    a, b = StubWS(), StubWS()
    await mgr.subscribe("execution:42", a)  # type: ignore[arg-type]
    await mgr.subscribe("execution:42", b)  # type: ignore[arg-type]

    await mgr.broadcast("execution:42", {"event": "result.updated"})

    assert a.sent == [{"event": "result.updated"}]
    assert b.sent == [{"event": "result.updated"}]


@pytest.mark.asyncio
async def test_one_ws_can_subscribe_to_many_topics(mgr: ConnectionManager):
    ws = StubWS()
    await mgr.subscribe("user:1", ws)  # type: ignore[arg-type]
    await mgr.subscribe("project:1", ws)  # type: ignore[arg-type]
    await mgr.subscribe("execution:9", ws)  # type: ignore[arg-type]

    await mgr.broadcast("project:1", {"event": "p"})
    await mgr.broadcast("execution:9", {"event": "e"})
    await mgr.broadcast("user:1", {"event": "u"})

    assert ws.sent == [{"event": "p"}, {"event": "e"}, {"event": "u"}]


@pytest.mark.asyncio
async def test_unsubscribe_stops_delivery(mgr: ConnectionManager):
    ws = StubWS()
    await mgr.subscribe("project:1", ws)  # type: ignore[arg-type]
    await mgr.unsubscribe("project:1", ws)  # type: ignore[arg-type]

    await mgr.broadcast("project:1", {"event": "x"})

    assert ws.sent == []
    assert mgr.subscribers("project:1") == 0


@pytest.mark.asyncio
async def test_unsubscribe_all_clears_every_topic(mgr: ConnectionManager):
    ws = StubWS()
    await mgr.subscribe("user:1", ws)  # type: ignore[arg-type]
    await mgr.subscribe("project:1", ws)  # type: ignore[arg-type]

    await mgr.unsubscribe_all(ws)  # type: ignore[arg-type]

    assert mgr.topics_for(ws) == set()  # type: ignore[arg-type]
    assert mgr.subscribers("user:1") == 0
    assert mgr.subscribers("project:1") == 0


@pytest.mark.asyncio
async def test_dead_socket_evicted_on_broadcast(mgr: ConnectionManager):
    alive, dead = StubWS(), StubWS(fail=True)
    await mgr.subscribe("project:1", alive)  # type: ignore[arg-type]
    await mgr.subscribe("project:1", dead)  # type: ignore[arg-type]

    await mgr.broadcast("project:1", {"event": "x"})

    assert alive.sent == [{"event": "x"}]
    assert mgr.subscribers("project:1") == 1
    assert mgr.topics_for(dead) == set()  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_broadcast_to_unknown_topic_is_noop(mgr: ConnectionManager):
    await mgr.broadcast("project:999", {"event": "x"})  # no raise
    assert mgr.subscribers("project:999") == 0


@pytest.mark.asyncio
async def test_legacy_connect_disconnect_round_trip(mgr: ConnectionManager):
    class AcceptableWS(StubWS):
        async def accept(self) -> None:
            self.accepted = True

    ws = AcceptableWS()
    await mgr.connect(7, ws)  # type: ignore[arg-type]
    assert ws.accepted is True
    assert mgr.subscribers("user:7") == 1

    await mgr.send_to_user(7, {"event": "notification"})
    assert ws.sent == [{"event": "notification"}]

    await mgr.disconnect(7, ws)  # type: ignore[arg-type]
    assert mgr.subscribers("user:7") == 0


def test_schedule_without_loop_drops_silently():
    # Sync context — no running loop. Must not raise, coro must be closed.
    coro = global_manager.broadcast("nobody", {"event": "x"})
    _schedule(coro)
    # If the coro was not closed, Python prints "coroutine ... was never awaited".
    # Re-closing is idempotent; if _schedule failed to close it, this raises.
    assert coro.cr_frame is None
