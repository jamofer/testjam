import pytest

from testjam.models.user import GroupMember, User
from tests.conftest import TestingSession


@pytest.fixture
def project_id(auth_client):
    return auth_client.post("/api/v1/projects", json={"name": "Atlas"}).json()["id"]


@pytest.fixture
def group_id(auth_client):
    return auth_client.post("/api/v1/groups", json={"name": "qa-team"}).json()["id"]


@pytest.fixture
def alice(auth_client):
    return _create_user(auth_client, "alice")


@pytest.fixture
def bob(auth_client):
    return _create_user(auth_client, "bob")


def test_lists_direct_members_with_their_role(auth_client, project_id, alice):
    _add_member(auth_client, project_id, alice["id"], "viewer")

    members = _effective_members(auth_client, project_id)

    assert members["alice"] == "viewer"
    assert members["u"] == "owner"


def test_lists_users_with_access_through_a_group(auth_client, project_id, group_id, alice):
    _add_to_group(group_id, alice["id"])
    _assign_group(auth_client, project_id, group_id, "tester")

    members = _effective_members(auth_client, project_id)

    assert members["alice"] == "tester"


def test_keeps_the_highest_role_across_direct_and_group_access(auth_client, project_id, group_id, alice):
    _add_member(auth_client, project_id, alice["id"], "viewer")
    _add_to_group(group_id, alice["id"])
    _assign_group(auth_client, project_id, group_id, "tester")

    members = _effective_members(auth_client, project_id)

    assert members["alice"] == "tester"


def test_lists_each_user_once(auth_client, project_id, group_id, alice):
    _add_member(auth_client, project_id, alice["id"], "tester")
    _add_to_group(group_id, alice["id"])
    _assign_group(auth_client, project_id, group_id, "viewer")

    body = auth_client.get(f"/api/v1/projects/{project_id}/members/effective").json()

    assert [member["username"] for member in body].count("alice") == 1


def test_skips_inactive_users(auth_client, project_id, group_id, alice):
    _add_to_group(group_id, alice["id"])
    _assign_group(auth_client, project_id, group_id, "tester")
    with TestingSession() as db:
        db.get(User, alice["id"]).is_active = False
        db.commit()

    members = _effective_members(auth_client, project_id)

    assert "alice" not in members


def test_skips_users_without_access(auth_client, project_id, bob):
    members = _effective_members(auth_client, project_id)

    assert "bob" not in members


def test_unknown_project_returns_404(auth_client):
    response = auth_client.get("/api/v1/projects/9999/members/effective")

    assert response.status_code == 404


def _create_user(client, username: str) -> dict:
    return client.post(
        "/api/v1/users", json={"username": username, "email": f"{username}@test.com", "password": "pw"},
    ).json()


def _add_member(client, project_id: int, user_id: int, role: str) -> None:
    response = client.post(f"/api/v1/projects/{project_id}/members", json={"user_id": user_id, "role": role})
    assert response.status_code == 201


def _assign_group(client, project_id: int, group_id: int, role: str) -> None:
    response = client.post(f"/api/v1/projects/{project_id}/groups", json={"group_id": group_id, "role": role})
    assert response.status_code == 201


def _add_to_group(group_id: int, user_id: int) -> None:
    with TestingSession() as db:
        db.add(GroupMember(group_id=group_id, user_id=user_id, role="member"))
        db.commit()


def _effective_members(client, project_id: int) -> dict[str, str]:
    body = client.get(f"/api/v1/projects/{project_id}/members/effective").json()
    return {member["username"]: member["role"] for member in body}
