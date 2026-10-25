import pytest
from fastapi.testclient import TestClient

from testjam.auth.security import hash_password
from testjam.main import app
from testjam.models.user import GroupMember, User
from testjam.services.permissions import effective_role
from tests.conftest import TestingSession


@pytest.fixture
def project_id(auth_client):
    return auth_client.post("/api/v1/projects", json={"name": "Atlas"}).json()["id"]


@pytest.fixture
def owner_group_id(auth_client, project_id):
    group_id = auth_client.post("/api/v1/groups", json={"name": "owners"}).json()["id"]
    auth_client.post(
        f"/api/v1/projects/{project_id}/groups",
        json={"group_id": group_id, "role": "owner"},
    )
    return group_id


@pytest.fixture
def mallory_id():
    return _seed_user("mallory")


@pytest.fixture
def mallory_client(mallory_id):
    return _login("mallory")


def test_non_admin_cannot_create_group(mallory_client):
    response = mallory_client.post("/api/v1/groups", json={"name": "rogue"})

    assert response.status_code == 403


def test_non_admin_cannot_update_group(mallory_client, owner_group_id):
    response = mallory_client.put(f"/api/v1/groups/{owner_group_id}", json={"name": "renamed"})

    assert response.status_code == 403


def test_non_admin_cannot_delete_group(mallory_client, owner_group_id):
    response = mallory_client.delete(f"/api/v1/groups/{owner_group_id}")

    assert response.status_code == 403


def test_non_admin_cannot_add_group_member(mallory_client, owner_group_id, mallory_id):
    response = mallory_client.post(
        f"/api/v1/groups/{owner_group_id}/members?user_id={mallory_id}&role=member",
    )

    assert response.status_code == 403


def test_non_admin_cannot_update_group_member(mallory_client, owner_group_id, mallory_id):
    _add_user_to_group(owner_group_id, mallory_id)

    response = mallory_client.put(
        f"/api/v1/groups/{owner_group_id}/members/{mallory_id}", json={"role": "lead"},
    )

    assert response.status_code == 403


def test_non_admin_cannot_remove_group_member(mallory_client, owner_group_id, mallory_id):
    _add_user_to_group(owner_group_id, mallory_id)

    response = mallory_client.delete(f"/api/v1/groups/{owner_group_id}/members/{mallory_id}")

    assert response.status_code == 403


def test_non_admin_cannot_escalate_to_project_owner_via_group(
    mallory_client, owner_group_id, mallory_id, project_id,
):
    mallory_client.post(f"/api/v1/groups/{owner_group_id}/members?user_id={mallory_id}&role=member")

    with TestingSession() as db:
        assert effective_role(db, mallory_id, project_id) is None


def test_non_admin_can_still_list_groups(mallory_client, owner_group_id):
    response = mallory_client.get("/api/v1/groups")

    assert response.status_code == 200
    assert [group["id"] for group in response.json()] == [owner_group_id]


def _seed_user(username: str) -> int:
    with TestingSession() as db:
        user = User(
            username=username,
            email=f"{username}@test.com",
            hashed_password=hash_password("pw"),
            is_active=True,
            is_admin=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id


def _login(username: str) -> TestClient:
    client = TestClient(app)
    response = client.post("/api/v1/auth/login", data={"username": username, "password": "pw"})
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    return client


def _add_user_to_group(group_id: int, user_id: int) -> None:
    with TestingSession() as db:
        db.add(GroupMember(group_id=group_id, user_id=user_id, role="member"))
        db.commit()
