"""End-to-end WebSocket flow: REST handler emits, subscribed client receives."""
from __future__ import annotations

from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from testjam.auth.security import hash_password
from testjam.models.user import User
from testjam.services import log_flusher
from tests.conftest import TestingSession


@pytest.fixture(autouse=True)
def immediate_log_flush():
    previous = log_flusher.flusher.flush_ms
    log_flusher.flusher.configure(0)
    yield
    log_flusher.flusher.configure(previous)


def _bearer_token(client):
    return client.headers.get("Authorization", "").removeprefix("Bearer ").strip()


@contextmanager
def _subscribed(client, topic):
    token = _bearer_token(client)
    with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
        ws.send_json({"action": "subscribe", "topic": topic})
        assert ws.receive_json() == {"event": "subscribed", "topic": topic}
        yield ws


def _start_step_result(auth_client, result_id, step_id):
    return auth_client.post(
        f"/api/v1/results/{result_id}/step-results", json={"step_id": step_id},
    ).json()["id"]


def test_log_endpoint_broadcasts_to_subscribed_client(auth_client, execution_with_step):
    execution_id, result_id, step_id = execution_with_step
    step_result_id = _start_step_result(auth_client, result_id, step_id)

    with _subscribed(auth_client, f"execution:{execution_id}") as ws:
        auth_client.post(
            f"/api/v1/results/{result_id}/step-results/{step_result_id}/log",
            json={"level": "INFO", "message": "logging in"},
        )
        frame = ws.receive_json()

    assert frame["event"] == "step_result.log_appended"
    assert frame["data"]["entries"] == [{
        "step_result_id": step_result_id,
        "level": "INFO",
        "message": "logging in",
        "ts": None,
    }]


def test_update_step_result_broadcasts_finished_event(auth_client, execution_with_step):
    execution_id, result_id, step_id = execution_with_step
    step_result_id = _start_step_result(auth_client, result_id, step_id)

    with _subscribed(auth_client, f"execution:{execution_id}") as ws:
        auth_client.put(
            f"/api/v1/results/{result_id}/step-results/{step_result_id}",
            json={"status": "passed", "duration_ms": 100},
        )
        frame = ws.receive_json()

    assert frame["event"] == "step_result.finished"
    assert frame["data"]["status"] == "passed"


def test_unsubscribed_topic_does_not_receive_broadcasts(auth_client, execution_with_step):
    execution_id, result_id, step_id = execution_with_step
    step_result_id = _start_step_result(auth_client, result_id, step_id)

    with _subscribed(auth_client, f"execution:{execution_id}") as ws:
        ws.send_json({"action": "unsubscribe", "topic": f"execution:{execution_id}"})
        assert ws.receive_json()["event"] == "unsubscribed"
        auth_client.post(
            f"/api/v1/results/{result_id}/step-results/{step_result_id}/log",
            json={"level": "INFO", "message": "ghost"},
        )
        ws.send_json({"action": "subscribe", "topic": f"execution:{execution_id}"})
        next_frame = ws.receive_json()

    assert next_frame["event"] == "subscribed"


def test_subscribing_to_another_users_topic_is_forbidden(client: TestClient):
    with TestingSession() as session:
        session.add_all([
            User(username="alice", email="a@x.com",
                 hashed_password=hash_password("pw"), is_active=True),
            User(username="bob", email="b@x.com",
                 hashed_password=hash_password("pw"), is_active=True),
        ])
        session.commit()
        bob_id = session.query(User).filter(User.username == "bob").one().id
    alice_token = client.post(
        "/api/v1/auth/login", data={"username": "alice", "password": "pw"},
    ).json()["access_token"]

    with client.websocket_connect(f"/api/v1/ws?token={alice_token}") as ws:
        ws.send_json({"action": "subscribe", "topic": f"user:{bob_id}"})
        frame = ws.receive_json()

    assert frame == {"event": "error", "topic": f"user:{bob_id}", "error": "forbidden"}
