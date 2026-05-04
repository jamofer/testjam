import pytest
from fastapi.testclient import TestClient

from testjam.auth.security import hash_password
from testjam.models.user import User
from testjam.models.project import ProjectMember


@pytest.fixture
def admin_client(client: TestClient):
    from tests.conftest import TestingSession
    with TestingSession() as db:
        db.add(User(username="owner", email="owner@x.com",
                    hashed_password=hash_password("pw"), is_active=True, is_admin=True))
        db.commit()
    token = client.post("/api/v1/auth/login", data={"username": "owner", "password": "pw"}).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def other_id(admin_client):
    from tests.conftest import TestingSession
    with TestingSession() as db:
        u = User(username="other", email="other@x.com",
                 hashed_password=hash_password("pw"), is_active=True)
        db.add(u)
        db.commit()
        db.refresh(u)
        return u.id


@pytest.fixture
def project_id(admin_client):
    return admin_client.post("/api/v1/projects", json={"name": "P"}).json()["id"]


def test_new_project_has_owner_as_member(admin_client, project_id):
    resp = admin_client.get(f"/api/v1/projects/{project_id}/members")
    assert resp.status_code == 200
    members = resp.json()
    assert len(members) == 1
    assert members[0]["role"] == "owner"
    assert members[0]["username"] == "owner"


def test_add_and_list_member(admin_client, project_id, other_id):
    resp = admin_client.post(f"/api/v1/projects/{project_id}/members",
                             json={"user_id": other_id, "role": "tester"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "other"
    assert data["role"] == "tester"
    assert data["user_id"] == other_id

    members = admin_client.get(f"/api/v1/projects/{project_id}/members").json()
    assert len(members) == 2  # owner + newly added tester


def test_duplicate_member_rejected(admin_client, project_id, other_id):
    admin_client.post(f"/api/v1/projects/{project_id}/members",
                      json={"user_id": other_id, "role": "tester"})
    resp = admin_client.post(f"/api/v1/projects/{project_id}/members",
                             json={"user_id": other_id, "role": "viewer"})
    assert resp.status_code == 409


def test_invalid_role_rejected(admin_client, project_id, other_id):
    resp = admin_client.post(f"/api/v1/projects/{project_id}/members",
                             json={"user_id": other_id, "role": "superuser"})
    assert resp.status_code == 400


def test_update_member_role(admin_client, project_id, other_id):
    admin_client.post(f"/api/v1/projects/{project_id}/members",
                      json={"user_id": other_id, "role": "tester"})
    resp = admin_client.put(f"/api/v1/projects/{project_id}/members/{other_id}",
                            json={"role": "viewer"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "viewer"


def test_remove_member(admin_client, project_id, other_id):
    admin_client.post(f"/api/v1/projects/{project_id}/members",
                      json={"user_id": other_id, "role": "tester"})
    resp = admin_client.delete(f"/api/v1/projects/{project_id}/members/{other_id}")
    assert resp.status_code == 204
    remaining = admin_client.get(f"/api/v1/projects/{project_id}/members").json()
    assert len(remaining) == 1  # only the owner remains
    assert remaining[0]["role"] == "owner"


def test_non_owner_cannot_manage_members(admin_client, project_id, other_id):
    """A tester-role member cannot add or remove members."""
    from tests.conftest import TestingSession
    # Add other_id as tester
    admin_client.post(f"/api/v1/projects/{project_id}/members",
                      json={"user_id": other_id, "role": "tester"})
    # Create a third user
    with TestingSession() as db:
        third = User(username="third", email="third@x.com",
                     hashed_password=hash_password("pw"), is_active=True)
        db.add(third)
        db.commit()
        db.refresh(third)
        third_id = third.id

    # Log in as tester
    token = admin_client.post("/api/v1/auth/login",
                              data={"username": "other", "password": "pw"}).json()["access_token"]
    admin_client.headers["Authorization"] = f"Bearer {token}"

    resp = admin_client.post(f"/api/v1/projects/{project_id}/members",
                             json={"user_id": third_id, "role": "viewer"})
    assert resp.status_code == 403

    resp = admin_client.delete(f"/api/v1/projects/{project_id}/members/{other_id}")
    assert resp.status_code == 403


def test_unknown_user_returns_404(admin_client, project_id):
    resp = admin_client.post(f"/api/v1/projects/{project_id}/members",
                             json={"user_id": 99999, "role": "viewer"})
    assert resp.status_code == 404
