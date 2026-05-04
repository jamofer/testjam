import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from testjam.auth.security import hash_password
from testjam.models.execution import TestExecution
from testjam.models.user import User


@pytest.fixture
def admin_client(client: TestClient):
    from tests.conftest import TestingSession
    with TestingSession() as db:
        db.add(User(username="admin", email="admin@x.com",
                    hashed_password=hash_password("pw"), is_active=True, is_admin=True))
        db.commit()
    token = client.post("/api/v1/auth/login", data={"username": "admin", "password": "pw"}).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def project_id(admin_client):
    return admin_client.post("/api/v1/projects", json={"name": "P"}).json()["id"]


# ── User tokens ───────────────────────────────────────────────────────────────

def test_create_user_token(admin_client):
    resp = admin_client.post("/api/v1/users/me/tokens", json={"name": "CI Token"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "CI Token"
    assert data["token"].startswith("tj_")
    assert data["token"].startswith(data["prefix"])
    assert data["user_id"] is not None
    assert data["project_id"] is None


def test_list_user_tokens_hides_secret(admin_client):
    admin_client.post("/api/v1/users/me/tokens", json={"name": "T"})
    tokens = admin_client.get("/api/v1/users/me/tokens").json()
    assert len(tokens) == 1
    assert "token" not in tokens[0]  # secret not returned on list


def test_user_token_authenticates(admin_client):
    raw = admin_client.post("/api/v1/users/me/tokens", json={"name": "T"}).json()["token"]
    del admin_client.headers["Authorization"]
    admin_client.headers["X-API-Key"] = raw

    resp = admin_client.get("/api/v1/users/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"


def test_last_used_at_updated_on_auth(admin_client):
    raw = admin_client.post("/api/v1/users/me/tokens", json={"name": "T"}).json()["token"]
    assert admin_client.get("/api/v1/users/me/tokens").json()[0]["last_used_at"] is None

    del admin_client.headers["Authorization"]
    admin_client.headers["X-API-Key"] = raw
    admin_client.get("/api/v1/users/me")

    # Re-fetch via a fresh JWT to verify last_used_at was updated
    admin_client.headers.pop("X-API-Key", None)
    token = admin_client.post("/api/v1/auth/login",
                              data={"username": "admin", "password": "pw"}).json()["access_token"]
    admin_client.headers["Authorization"] = f"Bearer {token}"
    assert admin_client.get("/api/v1/users/me/tokens").json()[0]["last_used_at"] is not None


def test_revoked_token_cannot_authenticate(admin_client):
    raw = admin_client.post("/api/v1/users/me/tokens", json={"name": "T"}).json()["token"]
    token_id = admin_client.get("/api/v1/users/me/tokens").json()[0]["id"]
    admin_client.delete(f"/api/v1/users/me/tokens/{token_id}")

    del admin_client.headers["Authorization"]
    admin_client.headers["X-API-Key"] = raw
    assert admin_client.get("/api/v1/users/me").status_code == 401


def test_cannot_revoke_another_users_token(admin_client):
    from tests.conftest import TestingSession
    with TestingSession() as db:
        db.add(User(username="other", email="other@x.com",
                    hashed_password=hash_password("pw"), is_active=True))
        db.commit()
    token2 = admin_client.post("/api/v1/auth/login",
                               data={"username": "other", "password": "pw"}).json()["access_token"]
    admin_client.headers["Authorization"] = f"Bearer {token2}"
    other_token_id = admin_client.post("/api/v1/users/me/tokens", json={"name": "other"}).json()["id"]

    # Switch back to admin
    token = admin_client.post("/api/v1/auth/login",
                              data={"username": "admin", "password": "pw"}).json()["access_token"]
    admin_client.headers["Authorization"] = f"Bearer {token}"
    resp = admin_client.delete(f"/api/v1/users/me/tokens/{other_token_id}")
    assert resp.status_code == 404


# ── Project tokens ────────────────────────────────────────────────────────────

def test_create_project_token(admin_client, project_id):
    resp = admin_client.post(f"/api/v1/projects/{project_id}/tokens", json={"name": "Pipeline"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["project_id"] == project_id
    assert data["user_id"] is None
    assert data["token"].startswith("tj_")


def test_project_token_authenticates(admin_client, project_id):
    raw = admin_client.post(f"/api/v1/projects/{project_id}/tokens", json={"name": "CI"}).json()["token"]
    del admin_client.headers["Authorization"]
    admin_client.headers["X-API-Key"] = raw

    resp = admin_client.get("/api/v1/users/me")
    assert resp.status_code == 200


def test_revoke_project_token(admin_client, project_id):
    raw = admin_client.post(f"/api/v1/projects/{project_id}/tokens", json={"name": "T"}).json()["token"]
    token_id = admin_client.get(f"/api/v1/projects/{project_id}/tokens").json()[0]["id"]
    admin_client.delete(f"/api/v1/projects/{project_id}/tokens/{token_id}")

    del admin_client.headers["Authorization"]
    admin_client.headers["X-API-Key"] = raw
    assert admin_client.get("/api/v1/users/me").status_code == 401


def test_project_token_blocked_from_other_projects(admin_client):
    """A project-scoped token must not access endpoints of other projects."""
    project_a = admin_client.post("/api/v1/projects", json={"name": "A"}).json()["id"]
    project_b = admin_client.post("/api/v1/projects", json={"name": "B"}).json()["id"]
    raw = admin_client.post(f"/api/v1/projects/{project_a}/tokens", json={"name": "scope"}).json()["token"]

    del admin_client.headers["Authorization"]
    admin_client.headers["X-API-Key"] = raw

    # Same project: 200
    assert admin_client.get(f"/api/v1/projects/{project_a}/suites").status_code == 200
    assert admin_client.get(f"/api/v1/projects/{project_a}/executions").status_code == 200
    # Other project: 403
    assert admin_client.get(f"/api/v1/projects/{project_b}/suites").status_code == 403
    assert admin_client.get(f"/api/v1/projects/{project_b}").status_code == 403
    assert admin_client.get(f"/api/v1/projects/{project_b}/members").status_code == 403


def test_user_token_works_across_projects(admin_client):
    """A non-scoped user token should retain full access (regression check)."""
    project_a = admin_client.post("/api/v1/projects", json={"name": "A"}).json()["id"]
    project_b = admin_client.post("/api/v1/projects", json={"name": "B"}).json()["id"]
    raw = admin_client.post("/api/v1/users/me/tokens", json={"name": "user"}).json()["token"]

    del admin_client.headers["Authorization"]
    admin_client.headers["X-API-Key"] = raw

    assert admin_client.get(f"/api/v1/projects/{project_a}/suites").status_code == 200
    assert admin_client.get(f"/api/v1/projects/{project_b}/suites").status_code == 200


def test_non_owner_cannot_create_project_token(admin_client, project_id):
    from tests.conftest import TestingSession
    with TestingSession() as db:
        db.add(User(username="regular", email="regular@x.com",
                    hashed_password=hash_password("pw"), is_active=True))
        db.commit()
    token = admin_client.post("/api/v1/auth/login",
                              data={"username": "regular", "password": "pw"}).json()["access_token"]
    admin_client.headers["Authorization"] = f"Bearer {token}"
    resp = admin_client.post(f"/api/v1/projects/{project_id}/tokens", json={"name": "T"})
    assert resp.status_code == 403


# ── Execution ordering ────────────────────────────────────────────────────────

def test_executions_listed_newest_first(admin_client, project_id):
    """Executions endpoint returns results ordered by created_at descending."""
    from tests.conftest import TestingSession

    titles = ["First", "Second", "Third"]
    exec_ids = []
    for t in titles:
        resp = admin_client.post(f"/api/v1/projects/{project_id}/executions",
                                 json={"title": t, "type": "manual", "test_case_ids": []})
        exec_ids.append(resp.json()["id"])

    # SQLite has second-level precision — set distinct timestamps explicitly
    with TestingSession() as db:
        for i, eid in enumerate(exec_ids):
            ex = db.get(TestExecution, eid)
            ex.created_at = datetime(2024, 1, 1, 0, 0, i)
            db.commit()

    result = admin_client.get(f"/api/v1/projects/{project_id}/executions").json()
    assert len(result) == 3
    assert result[0]["title"] == "Third"
    assert result[1]["title"] == "Second"
    assert result[2]["title"] == "First"
