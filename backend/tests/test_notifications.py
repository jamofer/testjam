"""Notifications: assignment triggers, list/read, WS endpoint sanity."""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from testjam.auth.security import hash_password
from testjam.models.user import User
from tests.conftest import TestingSession


def _add_user(username: str) -> int:
    with TestingSession() as db:
        u = User(username=username, email=f"{username}@x.com",
                hashed_password=hash_password("pw"), is_active=True)
        db.add(u)
        db.commit()
        db.refresh(u)
        return u.id


def test_assigning_execution_creates_notification(auth_client: TestClient, project_id, case_ids):
    bob_id = _add_user("bob")

    resp = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Run", "type": "manual",
        "assigned_to_id": bob_id, "test_case_ids": case_ids,
    })
    assert resp.status_code == 201

    bob_token = auth_client.post("/api/v1/auth/login", data={"username": "bob", "password": "pw"}).json()["access_token"]
    listed = auth_client.get(
        "/api/v1/notifications", headers={"Authorization": f"Bearer {bob_token}"},
    ).json()

    assert len(listed) == 1
    assert listed[0]["type"] == "execution_assigned"
    assert "Run" in listed[0]["message"]
    assert listed[0]["link"].endswith("/run")
    assert listed[0]["is_read"] is False


def test_assigning_to_self_does_not_notify(auth_client, project_id, case_ids):
    me = auth_client.get("/api/v1/users/me").json()
    auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Run", "type": "manual",
        "assigned_to_id": me["id"], "test_case_ids": case_ids,
    })
    assert auth_client.get("/api/v1/notifications").json() == []


def test_changing_assignee_via_put_creates_notification(auth_client, project_id, case_ids):
    bob_id = _add_user("bob")
    exec_id = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Run", "type": "manual", "test_case_ids": case_ids,
    }).json()["id"]

    auth_client.put(f"/api/v1/executions/{exec_id}", json={"assigned_to_id": bob_id})

    bob_token = auth_client.post("/api/v1/auth/login", data={"username": "bob", "password": "pw"}).json()["access_token"]
    notes = auth_client.get(
        "/api/v1/notifications", headers={"Authorization": f"Bearer {bob_token}"},
    ).json()
    assert len(notes) == 1


def test_unread_count_and_mark_read(auth_client, project_id, case_ids):
    bob_id = _add_user("bob")
    auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "R1", "type": "manual",
        "assigned_to_id": bob_id, "test_case_ids": case_ids,
    })
    auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "R2", "type": "manual",
        "assigned_to_id": bob_id, "test_case_ids": case_ids,
    })

    bob_token = auth_client.post("/api/v1/auth/login", data={"username": "bob", "password": "pw"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {bob_token}"}

    assert auth_client.get("/api/v1/notifications/unread-count", headers=headers).json() == {"unread": 2}

    notes = auth_client.get("/api/v1/notifications", headers=headers).json()
    auth_client.post(f"/api/v1/notifications/{notes[0]['id']}/read", headers=headers)
    assert auth_client.get("/api/v1/notifications/unread-count", headers=headers).json() == {"unread": 1}

    auth_client.post("/api/v1/notifications/read-all", headers=headers)
    assert auth_client.get("/api/v1/notifications/unread-count", headers=headers).json() == {"unread": 0}


def test_notifications_isolated_per_user(auth_client, project_id, case_ids):
    bob_id = _add_user("bob")
    auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "R", "type": "manual",
        "assigned_to_id": bob_id, "test_case_ids": case_ids,
    })

    assert auth_client.get("/api/v1/notifications").json() == []


def test_ws_rejects_invalid_token(client: TestClient):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/notifications/ws?token=garbage"):
            pass


def test_ws_accepts_valid_token(client: TestClient):
    with TestingSession() as db:
        db.add(User(username="alice", email="a@x.com",
                    hashed_password=hash_password("pw"), is_active=True))
        db.commit()
    token = client.post("/api/v1/auth/login", data={"username": "alice", "password": "pw"}).json()["access_token"]

    with client.websocket_connect(f"/api/v1/notifications/ws?token={token}"):
        pass
