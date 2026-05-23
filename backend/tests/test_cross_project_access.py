"""Cross-project access guards.

Non-admin users without membership must not access or mutate resources
that belong to another project, regardless of the route shape.
"""
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


def _seed_user(username: str) -> int:
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


def _seed_member_user(project_id: int, username: str, role: str = "tester") -> int:
    user_id = _seed_user(username)
    with TestingSession() as db:
        db.add(ProjectMember(project_id=project_id, user_id=user_id, role=role))
        db.commit()
    return user_id


@pytest.fixture
def project_id(auth_client):
    return auth_client.post("/api/v1/projects", json={"name": "Owned"}).json()["id"]


@pytest.fixture
def outsider_client():
    _seed_user("outsider")
    return _login("outsider")


def test_outsider_cannot_read_project_detail(outsider_client, project_id):
    response = outsider_client.get(f"/api/v1/projects/{project_id}")

    assert response.status_code == 403


def test_outsider_cannot_list_project_bugs(outsider_client, project_id):
    response = outsider_client.get(f"/api/v1/projects/{project_id}/bugs")

    assert response.status_code == 403


def test_outsider_cannot_list_project_suites(outsider_client, project_id):
    response = outsider_client.get(f"/api/v1/projects/{project_id}/suites")

    assert response.status_code == 403


def test_outsider_cannot_list_project_executions(outsider_client, project_id):
    response = outsider_client.get(f"/api/v1/projects/{project_id}/executions")

    assert response.status_code == 403


def test_outsider_cannot_list_project_versions(outsider_client, project_id):
    response = outsider_client.get(f"/api/v1/projects/{project_id}/versions")

    assert response.status_code == 403
