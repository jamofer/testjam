"""Tests for the @user mention fan-out triggered by bug comments and description."""
import pytest
from fastapi.testclient import TestClient

from testjam.auth.security import hash_password
from testjam.main import app
from testjam.models.project import ProjectMember
from testjam.models.user import User
from tests.conftest import TestingSession


def _login(username: str, password: str = "pw") -> TestClient:
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login", data={"username": username, "password": password},
    )
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    return client


def _seed_member(project_id: int, username: str, role: str = "tester") -> int:
    with TestingSession() as db:
        user = User(
            username=username,
            email=f"{username}@x.com",
            hashed_password=hash_password("pw"),
            is_active=True,
            full_name=username.title(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.add(ProjectMember(project_id=project_id, user_id=user.id, role=role))
        db.commit()
        return user.id


def _seed_outsider(username: str) -> int:
    with TestingSession() as db:
        user = User(
            username=username,
            email=f"{username}@x.com",
            hashed_password=hash_password("pw"),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id


@pytest.fixture
def project_id(auth_client):
    return auth_client.post("/api/v1/projects", json={"name": "Mention Bugs"}).json()["id"]


def _bug(client, project_id, **overrides):
    payload = {"title": "Login crashes"}
    payload.update(overrides)
    return client.post(f"/api/v1/projects/{project_id}/bugs", json=payload).json()


def _notifications_for(username: str) -> list[dict]:
    return _login(username).get("/api/v1/notifications").json()


def test_comment_mention_notifies_member(auth_client, project_id):
    _seed_member(project_id, "alice")
    bug = _bug(auth_client, project_id)

    auth_client.post(
        f"/api/v1/bugs/{bug['id']}/comments", json={"body": "ping @alice please look"},
    )

    notifications = _notifications_for("alice")
    assert len(notifications) == 1
    assert notifications[0]["type"] == "mention_in_comment"
    assert "alice" not in notifications[0]["message"]
    assert "Login crashes" in notifications[0]["message"]
    assert notifications[0]["link"] == f"/projects/{project_id}/bugs/{bug['number']}"


def test_comment_mention_does_not_notify_outsider(auth_client, project_id):
    _seed_outsider("ghost")
    bug = _bug(auth_client, project_id)

    auth_client.post(
        f"/api/v1/bugs/{bug['id']}/comments", json={"body": "hello @ghost"},
    )

    assert _notifications_for("ghost") == []


def test_self_mention_does_not_notify_actor(auth_client, project_id):
    me = auth_client.get("/api/v1/users/me").json()
    bug = _bug(auth_client, project_id)

    auth_client.post(
        f"/api/v1/bugs/{bug['id']}/comments", json={"body": f"@{me['username']} note"},
    )

    assert auth_client.get("/api/v1/notifications").json() == []


def test_editing_comment_only_notifies_new_mentions(auth_client, project_id):
    _seed_member(project_id, "alice")
    _seed_member(project_id, "bob")
    bug = _bug(auth_client, project_id)
    comment = auth_client.post(
        f"/api/v1/bugs/{bug['id']}/comments", json={"body": "ping @alice"},
    ).json()

    auth_client.put(
        f"/api/v1/bugs/{bug['id']}/comments/{comment['id']}",
        json={"body": "ping @alice and @bob"},
    )

    assert len(_notifications_for("alice")) == 1
    assert len(_notifications_for("bob")) == 1


def test_description_mention_on_create_notifies(auth_client, project_id):
    _seed_member(project_id, "alice")

    _bug(
        auth_client, project_id, description="cc @alice for triage",
    )

    notifications = _notifications_for("alice")
    assert len(notifications) == 1
    assert notifications[0]["type"] == "mention_in_comment"


def test_description_mention_on_update_only_new(auth_client, project_id):
    _seed_member(project_id, "alice")
    _seed_member(project_id, "bob")
    bug = _bug(auth_client, project_id, description="cc @alice")

    auth_client.put(
        f"/api/v1/bugs/{bug['id']}",
        json={"description": "cc @alice and @bob"},
    )

    assert len(_notifications_for("alice")) == 1
    assert len(_notifications_for("bob")) == 1


def test_mention_inside_code_block_is_ignored(auth_client, project_id):
    _seed_member(project_id, "alice")
    bug = _bug(auth_client, project_id)

    auth_client.post(
        f"/api/v1/bugs/{bug['id']}/comments",
        json={"body": "see `@alice` in docs"},
    )

    assert _notifications_for("alice") == []


def test_bug_mention_notifies_assignee(auth_client, project_id):
    alice_id = _seed_member(project_id, "alice")
    target_bug = _bug(auth_client, project_id, title="Triage me", assigned_to_id=alice_id)
    host_bug = _bug(auth_client, project_id, title="Other thread")

    auth_client.post(
        f"/api/v1/bugs/{host_bug['id']}/comments",
        json={"body": f"see #{target_bug['number']} for context"},
    )

    notifications = _notifications_for("alice")
    assert len(notifications) == 1
    assert notifications[0]["link"] == f"/projects/{project_id}/bugs/{host_bug['number']}"


def test_execution_mention_notifies_assignee(auth_client, project_id):
    alice_id = _seed_member(project_id, "alice")
    suite_id = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    case_id = auth_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "TC", "suite_id": suite_id},
    ).json()["id"]
    execution = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={
            "title": "Smoke",
            "type": "manual",
            "test_case_ids": [case_id],
            "assigned_to_id": alice_id,
        },
    ).json()
    bug = _bug(auth_client, project_id)

    auth_client.post(
        f"/api/v1/bugs/{bug['id']}/comments",
        json={"body": f"saw it on !{execution['id']}"},
    )

    assert len(_notifications_for("alice")) == 1


def test_case_mention_notifies_creator(auth_client, project_id):
    alice = _seed_member(project_id, "alice")
    alice_client = _login("alice")
    suite_id = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    case_id = alice_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "TC", "suite_id": suite_id},
    ).json()["id"]
    bug = _bug(auth_client, project_id)

    auth_client.post(
        f"/api/v1/bugs/{bug['id']}/comments",
        json={"body": f"related to ~{case_id}"},
    )

    notifications = _notifications_for("alice")
    assert len(notifications) == 1
    assert alice  # silence linter


def test_bug_mention_for_unknown_number_does_not_crash(auth_client, project_id):
    _seed_member(project_id, "alice")
    host_bug = _bug(auth_client, project_id)

    response = auth_client.post(
        f"/api/v1/bugs/{host_bug['id']}/comments",
        json={"body": "check #9999 if you can"},
    )

    assert response.status_code == 201
    assert _notifications_for("alice") == []
