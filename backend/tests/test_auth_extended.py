"""Additional auth cases not covered by test_auth.py."""
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from starlette.websockets import WebSocketDisconnect

from testjam.auth.security import hash_password
from testjam.core.config import settings
from testjam.models.user import User
from tests.conftest import TestingSession

OWNER_USERNAME = "password-owner"
OLD_PASSWORD = "old-password"
NEW_PASSWORD = "new-password"


@pytest.fixture
def password_owner(setup_db) -> int:
    with TestingSession() as db:
        user = User(
            username=OWNER_USERNAME,
            email=f"{OWNER_USERNAME}@example.com",
            hashed_password=hash_password(OLD_PASSWORD),
            is_active=True,
        )
        db.add(user)
        db.commit()
        return user.id


def _add_user(db, username="tester", active=True):
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=hash_password("secret"),
        is_active=active,
    )
    db.add(user)
    db.commit()
    return user


def test_login_unknown_user(client, setup_db):
    resp = client.post("/api/v1/auth/login", data={"username": "ghost", "password": "secret"})

    assert resp.status_code == 401


def test_login_inactive_user(client, setup_db):
    from tests.conftest import TestingSession
    with TestingSession() as db:
        _add_user(db, active=False)

    resp = client.post("/api/v1/auth/login", data={"username": "tester", "password": "secret"})

    assert resp.status_code == 403


def test_protected_route_without_token(client, setup_db):
    resp = client.get("/api/v1/projects")

    assert resp.status_code == 401


def test_protected_route_with_invalid_token(client, setup_db):
    resp = client.get("/api/v1/projects", headers={"Authorization": "Bearer garbage.token.here"})

    assert resp.status_code == 401


def test_api_key_wrong_key_rejected(client, setup_db):
    resp = client.get("/api/v1/users/me", headers={"X-API-Key": "wrong-key"})

    assert resp.status_code == 401


def test_password_change_ends_other_sessions(client, password_owner):
    stolen_session = _session_headers(client)
    client.put(
        "/api/v1/users/me/password",
        json={"current_password": OLD_PASSWORD, "new_password": NEW_PASSWORD},
        headers=_session_headers(client),
    )

    response = client.get("/api/v1/users/me", headers=stolen_session)

    assert response.status_code == 401


def test_password_change_returns_a_working_session(client, password_owner):
    response = client.put(
        "/api/v1/users/me/password",
        json={"current_password": OLD_PASSWORD, "new_password": NEW_PASSWORD},
        headers=_session_headers(client),
    )

    me = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {response.json()['access_token']}"},
    )
    assert me.status_code == 200


def test_login_after_password_change_works(client, password_owner):
    client.put(
        "/api/v1/users/me/password",
        json={"current_password": OLD_PASSWORD, "new_password": NEW_PASSWORD},
        headers=_session_headers(client),
    )

    headers = _session_headers(client, NEW_PASSWORD)

    assert client.get("/api/v1/users/me", headers=headers).status_code == 200


def test_admin_setting_a_password_ends_sessions(auth_client, client, password_owner):
    session = _session_headers(client)

    auth_client.put(f"/api/v1/users/{password_owner}", json={"password": NEW_PASSWORD})

    assert client.get("/api/v1/users/me", headers=session).status_code == 401


def test_token_without_issue_time_ends_on_password_change(client, password_owner):
    legacy_token = jwt.encode(
        {"sub": OWNER_USERNAME, "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    client.put(
        "/api/v1/users/me/password",
        json={"current_password": OLD_PASSWORD, "new_password": NEW_PASSWORD},
        headers=_session_headers(client),
    )

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {legacy_token}"})

    assert response.status_code == 401


def test_token_without_issue_time_works_until_password_changes(client, password_owner):
    legacy_token = jwt.encode(
        {"sub": OWNER_USERNAME, "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {legacy_token}"})

    assert response.status_code == 200


def test_websocket_rejects_session_ended_by_password_change(client, password_owner):
    token = _session_headers(client)["Authorization"].removeprefix("Bearer ")
    client.put(
        "/api/v1/users/me/password",
        json={"current_password": OLD_PASSWORD, "new_password": NEW_PASSWORD},
        headers=_session_headers(client),
    )

    with pytest.raises(WebSocketDisconnect), client.websocket_connect(f"/api/v1/ws?token={token}"):
        pass


def _session_headers(client, password: str = OLD_PASSWORD) -> dict[str, str]:
    token = client.post(
        "/api/v1/auth/login", data={"username": OWNER_USERNAME, "password": password},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

