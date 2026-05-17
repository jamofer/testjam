"""Tests for /projects/{id}/webhooks + dispatch service."""
from __future__ import annotations

import asyncio
import json

import pytest

from testjam.services import webhook_dispatch, webhook_events
from testjam.models.webhook import Webhook
from tests.conftest import TestingSession


@pytest.fixture
def project_id(auth_client):
    return auth_client.post("/api/v1/projects", json={"name": "Hooks"}).json()["id"]


def _create_webhook(client, project_id, **overrides):
    payload = {
        "name": "Slack notifier",
        "url": "https://example.com/hook",
        "events": ["bug.created"],
        "is_active": True,
    }
    payload.update(overrides)
    return client.post(f"/api/v1/projects/{project_id}/webhooks", json=payload)


def test_webhook_round_trip_exposes_secret_once(auth_client, project_id):
    created = _create_webhook(auth_client, project_id).json()

    assert created["secret"]
    assert "secret" in created

    listed = auth_client.get(f"/api/v1/projects/{project_id}/webhooks").json()
    assert len(listed) == 1
    assert "secret" not in listed[0]


def test_update_and_delete_webhook(auth_client, project_id):
    webhook = _create_webhook(auth_client, project_id).json()

    updated = auth_client.put(
        f"/api/v1/webhooks/{webhook['id']}",
        json={"name": "Renamed", "is_active": False},
    ).json()
    assert updated["name"] == "Renamed"
    assert updated["is_active"] is False

    deleted = auth_client.delete(f"/api/v1/webhooks/{webhook['id']}")
    assert deleted.status_code == 204
    assert auth_client.get(f"/api/v1/projects/{project_id}/webhooks").json() == []


def test_create_rejects_invalid_event(auth_client, project_id):
    response = _create_webhook(auth_client, project_id, events=["banana"])
    assert response.status_code == 422


def test_signature_round_trip():
    body = b'{"event":"bug.created"}'
    secret = "deadbeef"
    signature = webhook_dispatch.sign(secret, body)

    assert signature.startswith("sha256=")
    expected = webhook_dispatch.sign(secret, body)
    assert signature == expected


def test_fire_event_dispatches_only_subscribed(auth_client, project_id, monkeypatch):
    _create_webhook(auth_client, project_id, name="A", events=["bug.created"])
    _create_webhook(auth_client, project_id, name="B", events=["bug.resolved"])

    scheduled: list[tuple[int, str]] = []
    monkeypatch.setattr(
        webhook_dispatch, "schedule_dispatch",
        lambda background, webhook_id, event_type, envelope: scheduled.append((webhook_id, event_type)),
    )

    with TestingSession() as db:
        count = webhook_events.fire_event(
            db, project_id, "bug.created", {"id": 1, "title": "Crash"}, background=None,
        )

    assert count == 1
    assert len(scheduled) == 1
    assert scheduled[0][1] == "bug.created"


def test_fire_event_skips_inactive(auth_client, project_id, monkeypatch):
    webhook = _create_webhook(auth_client, project_id, events=["bug.created"]).json()
    auth_client.put(f"/api/v1/webhooks/{webhook['id']}", json={"is_active": False})

    scheduled: list[int] = []
    monkeypatch.setattr(
        webhook_dispatch, "schedule_dispatch",
        lambda background, webhook_id, event_type, envelope: scheduled.append(webhook_id),
    )

    with TestingSession() as db:
        webhook_events.fire_event(db, project_id, "bug.created", {"id": 1}, background=None)

    assert scheduled == []


def test_creating_bug_fires_webhook(auth_client, project_id, monkeypatch):
    _create_webhook(auth_client, project_id, events=["bug.created"])

    captured: list[tuple[int, str, dict]] = []
    monkeypatch.setattr(
        webhook_dispatch, "schedule_dispatch",
        lambda background, webhook_id, event_type, envelope: captured.append((webhook_id, event_type, envelope)),
    )

    auth_client.post(
        f"/api/v1/projects/{project_id}/bugs",
        json={"title": "Boom"},
    )

    events = [evt for _, evt, _ in captured]
    assert "bug.created" in events
    payload_envelope = next(env for _, evt, env in captured if evt == "bug.created")
    assert payload_envelope["data"]["title"] == "Boom"
    assert payload_envelope["event"] == "bug.created"
    assert payload_envelope["project_id"] == project_id


def test_dispatch_succeeds_and_persists_delivery(auth_client, project_id, monkeypatch):
    webhook = _create_webhook(auth_client, project_id, events=["bug.created"]).json()

    class _OkResponse:
        status_code = 200
        text = "ok"

    class _Client:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return False
        async def post(self, url, content=None, headers=None):
            return _OkResponse()

    monkeypatch.setattr(webhook_dispatch.httpx, "AsyncClient", _Client)

    envelope = webhook_dispatch.build_envelope("bug.created", {"id": 1}, project_id)
    asyncio.run(webhook_dispatch._run_dispatch(webhook["id"], "bug.created", envelope))

    deliveries = auth_client.get(f"/api/v1/webhooks/{webhook['id']}/deliveries").json()
    assert len(deliveries) == 1
    assert deliveries[0]["succeeded"] is True
    assert deliveries[0]["status_code"] == 200
    assert deliveries[0]["attempt_count"] == 1


def test_dispatch_retries_on_5xx_then_records_failure(auth_client, project_id, monkeypatch):
    webhook = _create_webhook(auth_client, project_id, events=["bug.created"]).json()
    calls = {"n": 0}

    class _Failing:
        status_code = 503
        text = "down"

    class _Client:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return False
        async def post(self, url, content=None, headers=None):
            calls["n"] += 1
            return _Failing()

    monkeypatch.setattr(webhook_dispatch.httpx, "AsyncClient", _Client)
    monkeypatch.setattr(webhook_dispatch.asyncio, "sleep", _no_sleep)

    envelope = webhook_dispatch.build_envelope("bug.created", {"id": 1}, project_id)
    asyncio.run(webhook_dispatch._run_dispatch(webhook["id"], "bug.created", envelope))

    deliveries = auth_client.get(f"/api/v1/webhooks/{webhook['id']}/deliveries").json()
    assert calls["n"] == 4
    assert deliveries[0]["succeeded"] is False
    assert deliveries[0]["attempt_count"] == 4
    assert deliveries[0]["status_code"] == 503


async def _no_sleep(_seconds):
    return None


def test_updating_result_to_failed_fires_webhook(auth_client, project_id, monkeypatch):
    _create_webhook(auth_client, project_id, events=["test_result.failed"])

    suite = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "Auth"},
    ).json()
    case = auth_client.post(
        f"/api/v1/suites/{suite['id']}/cases",
        json={"name": "Login", "suite_id": suite["id"]},
    ).json()
    execution = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual", "test_case_ids": [case["id"]]},
    ).json()
    result_row = auth_client.get(f"/api/v1/executions/{execution['id']}/results").json()[0]

    captured: list[str] = []
    monkeypatch.setattr(
        webhook_dispatch, "schedule_dispatch",
        lambda background, webhook_id, event_type, envelope: captured.append(event_type),
    )

    auth_client.put(
        f"/api/v1/results/{result_row['id']}", json={"status": "failed"},
    )

    assert "test_result.failed" in captured


def test_updating_already_failed_does_not_refire(auth_client, project_id, monkeypatch):
    _create_webhook(auth_client, project_id, events=["test_result.failed"])

    suite = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "Auth"},
    ).json()
    case = auth_client.post(
        f"/api/v1/suites/{suite['id']}/cases",
        json={"name": "Login", "suite_id": suite["id"]},
    ).json()
    execution = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual", "test_case_ids": [case["id"]]},
    ).json()
    result_row = auth_client.get(f"/api/v1/executions/{execution['id']}/results").json()[0]
    auth_client.put(f"/api/v1/results/{result_row['id']}", json={"status": "failed"})

    captured: list[str] = []
    monkeypatch.setattr(
        webhook_dispatch, "schedule_dispatch",
        lambda background, webhook_id, event_type, envelope: captured.append(event_type),
    )

    auth_client.put(
        f"/api/v1/results/{result_row['id']}",
        json={"status": "failed", "comment": "still broken"},
    )

    assert "test_result.failed" not in captured


def test_dispatch_skips_4xx_without_retry(auth_client, project_id, monkeypatch):
    webhook = _create_webhook(auth_client, project_id, events=["bug.created"]).json()
    calls = {"n": 0}

    class _BadRequest:
        status_code = 400
        text = "bad"

    class _Client:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return False
        async def post(self, url, content=None, headers=None):
            calls["n"] += 1
            return _BadRequest()

    monkeypatch.setattr(webhook_dispatch.httpx, "AsyncClient", _Client)

    envelope = webhook_dispatch.build_envelope("bug.created", {"id": 1}, project_id)
    asyncio.run(webhook_dispatch._run_dispatch(webhook["id"], "bug.created", envelope))

    assert calls["n"] == 1
    deliveries = auth_client.get(f"/api/v1/webhooks/{webhook['id']}/deliveries").json()
    assert deliveries[0]["succeeded"] is False
    assert deliveries[0]["status_code"] == 400
    assert deliveries[0]["attempt_count"] == 1
