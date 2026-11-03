import pytest
from fastapi.testclient import TestClient

from testjam.main import app
from testjam.models.user import GroupMember
from tests.conftest import TestingSession

OWNER_ONLY_REQUESTS = [
    ("POST", "/api/v1/projects/{project_id}/tokens", {"name": "ci"}),
    ("GET", "/api/v1/projects/{project_id}/tokens", None),
    ("POST", "/api/v1/projects/{project_id}/members", {"user_id": "{outsider_id}", "role": "viewer"}),
    ("POST", "/api/v1/projects/{project_id}/archive", None),
]


@pytest.fixture
def ids(auth_client):
    project_id = auth_client.post("/api/v1/projects", json={"name": "Atlas"}).json()["id"]
    group_id = auth_client.post("/api/v1/groups", json={"name": "leads"}).json()["id"]
    lead_id = _create_user(auth_client, "lead")
    outsider_id = _create_user(auth_client, "outsider")
    with TestingSession() as db:
        db.add(GroupMember(group_id=group_id, user_id=lead_id, role="member"))
        db.commit()
    auth_client.post(f"/api/v1/projects/{project_id}/groups", json={"group_id": group_id, "role": "owner"})
    return {"project_id": project_id, "outsider_id": outsider_id}


@pytest.fixture
def group_owner_client(ids):
    client = TestClient(app)
    token = client.post("/api/v1/auth/login", data={"username": "lead", "password": "pw"}).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.mark.parametrize("method,path,payload", OWNER_ONLY_REQUESTS)
def test_owner_through_a_group_can_manage_the_project(group_owner_client, ids, method, path, payload):
    body = {key: ids["outsider_id"] if value == "{outsider_id}" else value for key, value in (payload or {}).items()}

    response = group_owner_client.request(method, path.format(**ids), json=body or None)

    assert response.status_code < 400, response.text


def _create_user(client, username: str) -> int:
    return client.post(
        "/api/v1/users", json={"username": username, "email": f"{username}@test.com", "password": "pw"},
    ).json()["id"]
