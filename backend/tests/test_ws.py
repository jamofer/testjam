"""Multi-topic WebSocket endpoint (P2.11.2)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from testjam.auth.security import hash_password
from testjam.models.execution import TestExecution
from testjam.models.project import Project
from testjam.models.user import User
from tests.conftest import TestingSession


def _login(client: TestClient, username: str, password: str = "pw") -> str:
    return client.post(
        "/api/v1/auth/login", data={"username": username, "password": password}
    ).json()["access_token"]


def _add_user(username: str) -> int:
    with TestingSession() as db:
        u = User(
            username=username, email=f"{username}@x.com",
            hashed_password=hash_password("pw"), is_active=True,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        return u.id


def _add_project(name: str = "P") -> int:
    with TestingSession() as db:
        p = Project(name=name)
        db.add(p)
        db.commit()
        db.refresh(p)
        return p.id


def _add_execution(project_id: int, title: str = "Run") -> int:
    with TestingSession() as db:
        e = TestExecution(project_id=project_id, title=title, type="manual")
        db.add(e)
        db.commit()
        db.refresh(e)
        return e.id


def test_ws_rejects_invalid_token(client: TestClient):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/ws?token=garbage"):
            pass


def test_subscribe_user_topic_for_self(client: TestClient):
    uid = _add_user("alice")
    token = _login(client, "alice")
    with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
        ws.send_json({"action": "subscribe", "topic": f"user:{uid}"})
        ack = ws.receive_json()
    assert ack == {"event": "subscribed", "topic": f"user:{uid}"}


def test_subscribe_other_user_topic_forbidden(client: TestClient):
    other = _add_user("bob")
    _add_user("alice")
    token = _login(client, "alice")
    with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
        ws.send_json({"action": "subscribe", "topic": f"user:{other}"})
        ack = ws.receive_json()
    assert ack["event"] == "error"
    assert ack["error"] == "forbidden"


def test_subscribe_project_topic_ok(client: TestClient):
    pid = _add_project()
    _add_user("alice")
    token = _login(client, "alice")
    with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
        ws.send_json({"action": "subscribe", "topic": f"project:{pid}"})
        ack = ws.receive_json()
    assert ack == {"event": "subscribed", "topic": f"project:{pid}"}


def test_subscribe_missing_project_topic_not_found(client: TestClient):
    _add_user("alice")
    token = _login(client, "alice")
    with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
        ws.send_json({"action": "subscribe", "topic": "project:9999"})
        ack = ws.receive_json()
    assert ack == {"event": "error", "topic": "project:9999", "error": "not_found"}


def test_subscribe_execution_topic_ok(client: TestClient):
    pid = _add_project()
    eid = _add_execution(pid)
    _add_user("alice")
    token = _login(client, "alice")
    with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
        ws.send_json({"action": "subscribe", "topic": f"execution:{eid}"})
        ack = ws.receive_json()
    assert ack == {"event": "subscribed", "topic": f"execution:{eid}"}


def test_subscribe_missing_execution_topic_not_found(client: TestClient):
    _add_user("alice")
    token = _login(client, "alice")
    with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
        ws.send_json({"action": "subscribe", "topic": "execution:9999"})
        ack = ws.receive_json()
    assert ack["error"] == "not_found"


def test_unknown_topic_kind_rejected(client: TestClient):
    _add_user("alice")
    token = _login(client, "alice")
    with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
        ws.send_json({"action": "subscribe", "topic": "nonsense:1"})
        ack = ws.receive_json()
    assert ack["error"] == "invalid_topic"


def test_malformed_topic_rejected(client: TestClient):
    _add_user("alice")
    token = _login(client, "alice")
    with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
        ws.send_json({"action": "subscribe", "topic": "no-colon"})
        ack = ws.receive_json()
    assert ack["error"] == "invalid_topic"

    with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
        ws.send_json({"action": "subscribe", "topic": "project:notanint"})
        ack = ws.receive_json()
    assert ack["error"] == "invalid_topic"


def test_unsubscribe_ack(client: TestClient):
    pid = _add_project()
    _add_user("alice")
    token = _login(client, "alice")
    with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
        ws.send_json({"action": "subscribe", "topic": f"project:{pid}"})
        ws.receive_json()
        ws.send_json({"action": "unsubscribe", "topic": f"project:{pid}"})
        ack = ws.receive_json()
    assert ack == {"event": "unsubscribed", "topic": f"project:{pid}"}


def test_invalid_action_acks_error(client: TestClient):
    _add_user("alice")
    token = _login(client, "alice")
    with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
        ws.send_json({"action": "explode", "topic": "user:1"})
        ack = ws.receive_json()
    assert ack == {"event": "error", "error": "invalid_action"}


def test_pong_action_is_silently_accepted(client: TestClient):
    user_id = _add_user("alice")
    token = _login(client, "alice")
    with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
        ws.send_json({"action": "pong"})
        ws.send_json({"action": "subscribe", "topic": f"user:{user_id}"})
        ack = ws.receive_json()
    assert ack["event"] == "subscribed"


# Broadcast-delivery tests are covered by tests/test_realtime.py against the
# ConnectionManager directly. TestClient.websocket_connect runs the server on
# a separate thread/loop, so calling `notify_project` from the test thread hits
# `_schedule`'s "no running loop" branch and is dropped — that path can't
# observe a real WS push without a full async harness, so we skip it here.
