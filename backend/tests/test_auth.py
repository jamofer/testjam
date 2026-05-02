from fastapi.testclient import TestClient
from testjam.auth.security import hash_password
from testjam.models.user import User


def _create_user(db, username="tester", password="secret"):
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=hash_password(password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def test_login_ok(client: TestClient, setup_db):
    from tests.conftest import TestingSession
    with TestingSession() as db:
        _create_user(db)

    resp = client.post("/api/v1/auth/login", data={"username": "tester", "password": "secret"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client: TestClient, setup_db):
    from tests.conftest import TestingSession
    with TestingSession() as db:
        _create_user(db)

    resp = client.post("/api/v1/auth/login", data={"username": "tester", "password": "wrong"})
    assert resp.status_code == 401


def test_get_me(client: TestClient, setup_db):
    from tests.conftest import TestingSession
    with TestingSession() as db:
        _create_user(db)

    token = client.post("/api/v1/auth/login", data={"username": "tester", "password": "secret"}).json()["access_token"]
    resp = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "tester"
