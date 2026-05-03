import pytest
from fastapi.testclient import TestClient
from testjam.auth.security import hash_password
from testjam.models.user import User


@pytest.fixture
def auth_client(client: TestClient, setup_db):
    from tests.conftest import TestingSession
    with TestingSession() as db:
        db.add(User(username="u", email="u@x.com", hashed_password=hash_password("pw"), is_active=True))
        db.commit()

    token = client.post("/api/v1/auth/login", data={"username": "u", "password": "pw"}).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


def test_create_and_list_project(auth_client):
    resp = auth_client.post("/api/v1/projects", json={"name": "My Project"})
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    resp = auth_client.get("/api/v1/projects")
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()]
    assert project_id in ids


def test_create_suite_and_case(auth_client):
    project_id = auth_client.post("/api/v1/projects", json={"name": "P"}).json()["id"]

    suite = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={"name": "Suite A"})
    assert suite.status_code == 201
    suite_id = suite.json()["id"]

    case = auth_client.post(f"/api/v1/suites/{suite_id}/cases", json={"name": "TC-001", "suite_id": suite_id})
    assert case.status_code == 201
    assert case.json()["name"] == "TC-001"


def test_delete_project(auth_client):
    project_id = auth_client.post("/api/v1/projects", json={"name": "ToDelete"}).json()["id"]
    resp = auth_client.delete(f"/api/v1/projects/{project_id}")
    assert resp.status_code == 204
    resp = auth_client.get(f"/api/v1/projects/{project_id}")
    assert resp.status_code == 404
