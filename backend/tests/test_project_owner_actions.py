import pytest
from fastapi.testclient import TestClient

from testjam.main import app


@pytest.fixture
def project_id(role_project):
    return role_project["project_id"]


@pytest.fixture
def owner_project_token_client(role_project, project_id):
    owner = role_project["clients"]["owner"]
    raw_token = owner.post(f"/api/v1/projects/{project_id}/tokens", json={"name": "ci"}).json()["token"]
    client = TestClient(app)
    client.headers["X-API-Key"] = raw_token
    return client


@pytest.mark.parametrize("role", ["tester", "viewer"])
def test_non_owner_cannot_delete_project(role_project, project_id, role):
    response = role_project["clients"][role].delete(f"/api/v1/projects/{project_id}")

    assert response.status_code == 403
    assert role_project["clients"]["owner"].get(f"/api/v1/projects/{project_id}").status_code == 200


@pytest.mark.parametrize("role", ["tester", "viewer"])
def test_non_owner_cannot_rename_project(role_project, project_id, role):
    response = role_project["clients"][role].put(f"/api/v1/projects/{project_id}", json={"name": "Hijacked"})

    assert response.status_code == 403


def test_owner_can_rename_project(role_project, project_id):
    response = role_project["clients"]["owner"].put(f"/api/v1/projects/{project_id}", json={"name": "Renamed"})

    assert response.json()["name"] == "Renamed"


def test_owner_can_delete_project(role_project, project_id):
    response = role_project["clients"]["owner"].delete(f"/api/v1/projects/{project_id}")

    assert response.status_code == 204


def test_project_token_cannot_delete_its_project(owner_project_token_client, project_id):
    response = owner_project_token_client.delete(f"/api/v1/projects/{project_id}")

    assert response.status_code == 403
