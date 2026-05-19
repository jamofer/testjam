"""Watch / follow opt-in for bugs (P3.5.2.7)."""
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
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.add(ProjectMember(project_id=project_id, user_id=user.id, role=role))
        db.commit()
        return user.id


@pytest.fixture
def project_id(auth_client):
    return auth_client.post("/api/v1/projects", json={"name": "Watcher Project"}).json()["id"]


def _create_bug(client, project_id, **overrides):
    payload = {"title": "Watch me", "severity": "high"}
    payload.update(overrides)
    return client.post(f"/api/v1/projects/{project_id}/bugs", json=payload).json()


def _notifications_for(username: str) -> list[dict]:
    return _login(username).get("/api/v1/notifications").json()


def test_create_auto_watches_creator(auth_client, project_id):
    bug = _create_bug(auth_client, project_id)

    watchers = auth_client.get(f"/api/v1/bugs/{bug['id']}/watchers").json()

    creator_ids = {watcher["user"]["username"] for watcher in watchers}
    assert "u" in creator_ids
    assert bug["watcher_count"] == 1


def test_create_auto_watches_assignee(auth_client, project_id):
    alice_id = _seed_member(project_id, "alice")

    bug = _create_bug(auth_client, project_id, assigned_to_id=alice_id)

    watcher_ids = {w["user"]["username"] for w in auth_client.get(f"/api/v1/bugs/{bug['id']}/watchers").json()}
    assert "alice" in watcher_ids
    assert "u" in watcher_ids


def test_assign_auto_watches_new_assignee(auth_client, project_id):
    alice_id = _seed_member(project_id, "alice")
    bug = _create_bug(auth_client, project_id)

    auth_client.put(f"/api/v1/bugs/{bug['id']}", json={"assigned_to_id": alice_id})

    watcher_ids = {w["user"]["username"] for w in auth_client.get(f"/api/v1/bugs/{bug['id']}/watchers").json()}
    assert "alice" in watcher_ids


def test_comment_auto_watches_commenter(auth_client, project_id):
    _seed_member(project_id, "alice")
    alice = _login("alice")
    bug = _create_bug(auth_client, project_id)

    alice.post(f"/api/v1/bugs/{bug['id']}/comments", json={"body": "looking into this"})

    watcher_ids = {w["user"]["username"] for w in auth_client.get(f"/api/v1/bugs/{bug['id']}/watchers").json()}
    assert "alice" in watcher_ids


def test_watch_endpoint_subscribes_current_user(auth_client, project_id):
    _seed_member(project_id, "alice")
    alice = _login("alice")
    bug = _create_bug(auth_client, project_id)

    response = alice.post(f"/api/v1/bugs/{bug['id']}/watch")

    assert response.status_code == 200
    assert response.json()["watcher_count"] == 2
    watcher_ids = {w["user"]["username"] for w in auth_client.get(f"/api/v1/bugs/{bug['id']}/watchers").json()}
    assert "alice" in watcher_ids


def test_watch_endpoint_is_idempotent(auth_client, project_id):
    _seed_member(project_id, "alice")
    alice = _login("alice")
    bug = _create_bug(auth_client, project_id)

    alice.post(f"/api/v1/bugs/{bug['id']}/watch")
    alice.post(f"/api/v1/bugs/{bug['id']}/watch")

    assert auth_client.get(f"/api/v1/bugs/{bug['id']}").json()["watcher_count"] == 2


def test_unwatch_endpoint_removes_subscription(auth_client, project_id):
    _seed_member(project_id, "alice")
    alice = _login("alice")
    bug = _create_bug(auth_client, project_id)
    alice.post(f"/api/v1/bugs/{bug['id']}/watch")

    response = alice.delete(f"/api/v1/bugs/{bug['id']}/watch")

    assert response.status_code == 200
    assert response.json()["watcher_count"] == 1
    watcher_ids = {w["user"]["username"] for w in auth_client.get(f"/api/v1/bugs/{bug['id']}/watchers").json()}
    assert "alice" not in watcher_ids


def test_status_change_notifies_all_watchers(auth_client, project_id):
    alice_id = _seed_member(project_id, "alice")
    _seed_member(project_id, "bob")
    bob = _login("bob")
    bug = _create_bug(auth_client, project_id, assigned_to_id=alice_id)
    bob.post(f"/api/v1/bugs/{bug['id']}/watch")

    auth_client.post(f"/api/v1/bugs/{bug['id']}/status", json={"status": "in_progress"})

    assert any(n["type"] == "bug_status_changed" for n in _notifications_for("alice"))
    assert any(n["type"] == "bug_status_changed" for n in _notifications_for("bob"))


def test_status_change_skips_actor(auth_client, project_id):
    _seed_member(project_id, "alice")
    alice = _login("alice")
    bug = _create_bug(auth_client, project_id)
    alice.post(f"/api/v1/bugs/{bug['id']}/watch")

    alice.post(f"/api/v1/bugs/{bug['id']}/status", json={"status": "in_progress"})

    assert not [n for n in _notifications_for("alice") if n["type"] == "bug_status_changed"]


def test_comment_notifies_watchers_skipping_commenter(auth_client, project_id):
    _seed_member(project_id, "alice")
    _seed_member(project_id, "bob")
    bob = _login("bob")
    bug = _create_bug(auth_client, project_id)
    bob.post(f"/api/v1/bugs/{bug['id']}/watch")

    bob.post(f"/api/v1/bugs/{bug['id']}/comments", json={"body": "hello there"})

    assert any(n["type"] == "bug_commented" for n in _notifications_for("u"))
    assert not [n for n in _notifications_for("bob") if n["type"] == "bug_commented"]


def test_comment_notifies_skip_mentioned_users(auth_client, project_id):
    _seed_member(project_id, "alice")
    alice = _login("alice")
    bug = _create_bug(auth_client, project_id)
    alice.post(f"/api/v1/bugs/{bug['id']}/watch")

    auth_client.post(f"/api/v1/bugs/{bug['id']}/comments", json={"body": "ping @alice take a look"})

    alice_notifications = _notifications_for("alice")
    assert any(n["type"] == "mention_in_comment" for n in alice_notifications)
    assert not [n for n in alice_notifications if n["type"] == "bug_commented"]


def test_watch_requires_writer_role(auth_client, project_id):
    _seed_member(project_id, "viewer", "viewer")
    viewer = _login("viewer")
    bug = _create_bug(auth_client, project_id)

    response = viewer.post(f"/api/v1/bugs/{bug['id']}/watch")

    assert response.status_code == 403
