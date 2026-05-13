"""Soft-delete + restore + login + listing for users."""
from datetime import datetime, timezone

import pytest

from testjam.auth.security import hash_password
from testjam.models.user import User
from testjam.services import password_reset as password_reset_service
from tests.conftest import TestingSession


@pytest.fixture
def user_factory():
    def _create(username: str = "alice", password: str = "secret-pw", is_admin: bool = False) -> User:
        with TestingSession() as db:
            user = User(
                username=username,
                email=f"{username}@x.com",
                hashed_password=hash_password(password),
                is_active=True,
                is_admin=is_admin,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

    return _create


def _read_user(user_id: int) -> User:
    with TestingSession() as db:
        return db.get(User, user_id)


def test_delete_marks_user_as_soft_deleted(admin_client, user_factory):
    target = user_factory()

    response = admin_client.delete(f"/api/v1/users/{target.id}")

    assert response.status_code == 204
    refreshed = _read_user(target.id)
    assert refreshed is not None
    assert refreshed.deleted_at is not None
    assert refreshed.is_active is False


def test_admin_cannot_delete_their_own_account(admin_client):
    me = admin_client.get("/api/v1/users/me").json()

    response = admin_client.delete(f"/api/v1/users/{me['id']}")

    assert response.status_code == 400


def test_default_listing_omits_deleted_users(admin_client, user_factory):
    target = user_factory("ghost")
    admin_client.delete(f"/api/v1/users/{target.id}")

    listing = admin_client.get("/api/v1/users").json()

    assert all(user["id"] != target.id for user in listing)


def test_admin_can_list_deleted_users_with_query_param(admin_client, user_factory):
    target = user_factory("ghost")
    admin_client.delete(f"/api/v1/users/{target.id}")

    listing = admin_client.get("/api/v1/users?include_deleted=true").json()

    deleted_ids = {user["id"] for user in listing if user["deleted_at"]}
    assert target.id in deleted_ids


def test_non_admin_cannot_request_deleted_users(client, user_factory):
    user_factory("regular", "pw")
    token = client.post("/api/v1/auth/login", data={"username": "regular", "password": "pw"}).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    response = client.get("/api/v1/users?include_deleted=true")

    assert response.status_code == 403


def test_soft_deleted_user_cannot_log_in(client, user_factory):
    target = user_factory("alice", "secret-pw")
    with TestingSession() as db:
        record = db.get(User, target.id)
        record.deleted_at = datetime.now(timezone.utc)
        record.is_active = False
        db.commit()

    response = client.post(
        "/api/v1/auth/login", data={"username": "alice", "password": "secret-pw"},
    )

    assert response.status_code == 401


def test_get_user_404s_for_non_admin_when_target_is_deleted(client, user_factory):
    target = user_factory("ghost", "pw")
    user_factory("regular", "rp")
    with TestingSession() as db:
        record = db.get(User, target.id)
        record.deleted_at = datetime.now(timezone.utc)
        db.commit()

    token = client.post("/api/v1/auth/login", data={"username": "regular", "password": "rp"}).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    response = client.get(f"/api/v1/users/{target.id}")

    assert response.status_code == 404


def test_admin_can_fetch_deleted_user_directly(admin_client, user_factory):
    target = user_factory("ghost")
    admin_client.delete(f"/api/v1/users/{target.id}")

    response = admin_client.get(f"/api/v1/users/{target.id}")

    assert response.status_code == 200
    assert response.json()["deleted_at"] is not None


def test_restore_clears_deleted_at_and_reactivates(admin_client, user_factory):
    target = user_factory("ghost")
    admin_client.delete(f"/api/v1/users/{target.id}")

    response = admin_client.post(f"/api/v1/users/{target.id}/restore")

    assert response.status_code == 200
    body = response.json()
    assert body["deleted_at"] is None
    assert body["is_active"] is True


def test_restore_404s_for_user_that_was_never_deleted(admin_client, user_factory):
    target = user_factory()

    response = admin_client.post(f"/api/v1/users/{target.id}/restore")

    assert response.status_code == 404


def test_password_reset_request_skips_deleted_users(admin_client, user_factory, monkeypatch):
    captured: list = []
    monkeypatch.setattr(
        password_reset_service, "send_email",
        lambda *args, **kwargs: captured.append(args) or True,
    )

    target = user_factory("ghost")
    admin_client.delete(f"/api/v1/users/{target.id}")

    response = admin_client.post(
        "/api/v1/auth/password-reset/request", json={"email": target.email},
    )

    assert response.status_code == 204
    assert captured == []
