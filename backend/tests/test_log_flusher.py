"""LogFlusher — per-execution batching of step_result.log_appended events."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from testjam.services import log_flusher as log_flusher_module


@pytest.fixture
def captured_broadcasts(monkeypatch):
    captured: list[tuple[str, dict]] = []

    async def fake_broadcast(topic, payload):
        captured.append((topic, payload))

    monkeypatch.setattr(log_flusher_module.manager, "broadcast", fake_broadcast)
    return captured


@pytest.fixture
def flusher():
    return log_flusher_module.LogFlusher()


def entry(step_result_id, message, level="INFO"):
    return {"step_result_id": step_result_id, "level": level, "message": message}


async def append_many(flusher, execution_id, *entries):
    for payload in entries:
        await flusher.append(execution_id, payload)


async def drain_pending(flusher):
    for task in list(flusher._pending.values()):
        await task


@pytest.mark.asyncio
async def test_batches_multiple_appends_within_window(captured_broadcasts, flusher):
    flusher.configure(50)

    await append_many(
        flusher, 7,
        entry(1, "a"), entry(1, "b"), entry(1, "c", level="FAIL"),
    )
    await drain_pending(flusher)

    assert len(captured_broadcasts) == 1
    topic, payload = captured_broadcasts[0]
    assert topic == "execution:7"
    assert payload["event"] == "step_result.log_appended"
    assert [item["message"] for item in payload["data"]["entries"]] == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_separate_executions_flush_independently(captured_broadcasts, flusher):
    flusher.configure(50)

    await flusher.append(1, entry(10, "x"))
    await flusher.append(2, entry(20, "y"))
    await drain_pending(flusher)

    topics = sorted(topic for topic, _ in captured_broadcasts)
    assert topics == ["execution:1", "execution:2"]


@pytest.mark.asyncio
async def test_flush_ms_zero_disables_batching(captured_broadcasts, flusher):
    flusher.configure(0)

    await append_many(flusher, 7, entry(1, "a"), entry(1, "b"))

    assert len(captured_broadcasts) == 2
    for _topic, payload in captured_broadcasts:
        assert len(payload["data"]["entries"]) == 1


def test_configure_clamps_negative_to_default(flusher):
    flusher.configure(-10)

    assert flusher.flush_ms == log_flusher_module.DEFAULT_FLUSH_MS


def test_configure_from_settings_reads_field():
    log_flusher_module.flusher.configure(log_flusher_module.DEFAULT_FLUSH_MS)

    log_flusher_module.configure_from_settings(SimpleNamespace(ws_log_flush_ms=250))

    assert log_flusher_module.flusher.flush_ms == 250
    log_flusher_module.flusher.configure(log_flusher_module.DEFAULT_FLUSH_MS)


def test_schedule_append_without_running_loop_is_silent():
    log_flusher_module.schedule_append(1, entry(1, "x"))
