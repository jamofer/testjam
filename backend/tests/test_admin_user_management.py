import pytest

from testjam.auth.security import hash_password, verify_password
from testjam.models.execution import TestExecution
from testjam.models.testcase import TestCase
from testjam.models.user import User
from tests.conftest import TestingSession


@pytest.fixture
def target_user(auth_client):
    return auth_client.post(
        "/api/v1/users",
        json={"username": "target", "email": "target@x.com", "password": "pw", "full_name": "Target"},
    ).json()


def _load_user(user_id: int) -> User:
    with TestingSession() as db:
        return db.get(User, user_id)


def test_admin_update_user_supports_username_and_admin_flag(auth_client, target_user):
    resp = auth_client.put(
        f"/api/v1/users/{target_user['id']}",
        json={"username": "renamed", "is_admin": True, "is_active": False},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "renamed"
    assert body["is_admin"] is True
    assert body["is_active"] is False


def test_admin_update_user_rejects_duplicate_username(auth_client, target_user):
    auth_client.post(
        "/api/v1/users",
        json={"username": "other", "email": "other@x.com", "password": "pw"},
    )

    resp = auth_client.put(
        f"/api/v1/users/{target_user['id']}",
        json={"username": "other"},
    )

    assert resp.status_code == 409


def test_admin_reset_password_temporary_returns_new_password(auth_client, target_user):
    resp = auth_client.post(
        f"/api/v1/users/{target_user['id']}/reset-password",
        json={"mode": "temporary_password"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "temporary_password"
    assert body["temporary_password"]

    refreshed = _load_user(target_user["id"])
    assert verify_password(body["temporary_password"], refreshed.hashed_password)


def test_admin_reset_password_email_does_not_change_password(auth_client, target_user):
    before = _load_user(target_user["id"]).hashed_password

    resp = auth_client.post(
        f"/api/v1/users/{target_user['id']}/reset-password",
        json={"mode": "email"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "email"
    assert body["temporary_password"] is None
    assert _load_user(target_user["id"]).hashed_password == before


def test_admin_reset_password_requires_admin(client):
    with TestingSession() as db:
        target = User(
            username="t2", email="t2@x.com",
            hashed_password=hash_password("pw"),
            is_active=True, is_admin=False,
        )
        plain = User(
            username="plain", email="plain@x.com",
            hashed_password=hash_password("pw"),
            is_active=True, is_admin=False,
        )
        db.add_all([target, plain])
        db.commit()
        target_id = target.id
    token = client.post(
        "/api/v1/auth/login", data={"username": "plain", "password": "pw"},
    ).json()["access_token"]

    resp = client.post(
        f"/api/v1/users/{target_id}/reset-password",
        json={"mode": "temporary_password"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403


def test_user_activity_returns_executions_and_cases(auth_client, target_user):
    project_id = auth_client.post("/api/v1/projects", json={"name": "P"}).json()["id"]
    suite_id = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    with TestingSession() as db:
        db.add_all([
            TestCase(suite_id=suite_id, name="Authored", created_by_id=target_user["id"]),
            TestExecution(
                project_id=project_id,
                title="Launched by target",
                type="manual",
                status="completed",
                created_by_id=target_user["id"],
            ),
        ])
        db.commit()

    resp = auth_client.get(f"/api/v1/users/{target_user['id']}/activity")

    assert resp.status_code == 200
    body = resp.json()
    assert [c["name"] for c in body["recent_cases"]] == ["Authored"]
    assert [e["title"] for e in body["recent_executions"]] == ["Launched by target"]


def test_user_activity_records_last_login(client):
    with TestingSession() as db:
        db.add(User(
            username="actor", email="actor@x.com",
            hashed_password=hash_password("pw"),
            is_active=True, is_admin=True,
        ))
        db.commit()

    client.post("/api/v1/auth/login", data={"username": "actor", "password": "pw"})

    with TestingSession() as db:
        actor = db.query(User).filter_by(username="actor").one()
        assert actor.last_login_at is not None
