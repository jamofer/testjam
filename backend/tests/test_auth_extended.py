"""Additional auth cases not covered by test_auth.py."""
from testjam.auth.security import hash_password
from testjam.models.user import User


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


def test_api_key_authentication(client, setup_db):
    from tests.conftest import TestingSession
    with TestingSession() as db:
        user = _add_user(db)
        user.api_key = "test-api-key-12345"
        db.commit()

    resp = client.get("/api/v1/users/me", headers={"X-API-Key": "test-api-key-12345"})

    assert resp.status_code == 200
    assert resp.json()["username"] == "tester"


def test_api_key_wrong_key_rejected(client, setup_db):
    from tests.conftest import TestingSession
    with TestingSession() as db:
        user = _add_user(db)
        user.api_key = "correct-key"
        db.commit()

    resp = client.get("/api/v1/users/me", headers={"X-API-Key": "wrong-key"})

    assert resp.status_code == 401
