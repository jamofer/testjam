import pytest

from testjam.auth.security import hash_password
from testjam.models.user import GroupMember, User
from testjam.services.permissions import accessible_project_ids, effective_role
from tests.conftest import TestingSession


@pytest.fixture
def project_id(auth_client):
    return auth_client.post("/api/v1/projects", json={"name": "Atlas"}).json()["id"]


@pytest.fixture
def group_id(auth_client):
    return auth_client.post("/api/v1/groups", json={"name": "qa-team"}).json()["id"]


@pytest.fixture
def alice(auth_client):
    user = auth_client.post(
        "/api/v1/users",
        json={"username": "alice", "email": "alice@x.com", "password": "pw"},
    ).json()
    return user


def _add_user_to_group(group_id: int, user_id: int) -> None:
    with TestingSession() as db:
        db.add(GroupMember(group_id=group_id, user_id=user_id, role="member"))
        db.commit()


def test_assign_group_to_project_persists_role(auth_client, project_id, group_id):
    resp = auth_client.post(
        f"/api/v1/projects/{project_id}/groups",
        json={"group_id": group_id, "role": "tester"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["group_name"] == "qa-team"
    assert body["role"] == "tester"


def test_assign_group_rejects_invalid_role(auth_client, project_id, group_id):
    resp = auth_client.post(
        f"/api/v1/projects/{project_id}/groups",
        json={"group_id": group_id, "role": "ninja"},
    )

    assert resp.status_code == 400


def test_assign_group_rejects_duplicate(auth_client, project_id, group_id):
    auth_client.post(
        f"/api/v1/projects/{project_id}/groups",
        json={"group_id": group_id, "role": "tester"},
    )

    resp = auth_client.post(
        f"/api/v1/projects/{project_id}/groups",
        json={"group_id": group_id, "role": "viewer"},
    )

    assert resp.status_code == 409


def test_list_groups_returns_role_and_member_count(auth_client, project_id, group_id, alice):
    _add_user_to_group(group_id, alice["id"])
    auth_client.post(
        f"/api/v1/projects/{project_id}/groups",
        json={"group_id": group_id, "role": "tester"},
    )

    body = auth_client.get(f"/api/v1/projects/{project_id}/groups").json()

    assert len(body) == 1
    assert body[0]["role"] == "tester"
    assert body[0]["member_count"] == 1


def test_update_assignment_changes_role(auth_client, project_id, group_id):
    auth_client.post(
        f"/api/v1/projects/{project_id}/groups",
        json={"group_id": group_id, "role": "viewer"},
    )

    resp = auth_client.put(
        f"/api/v1/projects/{project_id}/groups/{group_id}",
        json={"role": "tester"},
    )

    assert resp.status_code == 200
    assert resp.json()["role"] == "tester"


def test_remove_assignment_returns_204(auth_client, project_id, group_id):
    auth_client.post(
        f"/api/v1/projects/{project_id}/groups",
        json={"group_id": group_id, "role": "tester"},
    )

    resp = auth_client.delete(f"/api/v1/projects/{project_id}/groups/{group_id}")

    assert resp.status_code == 204
    assert auth_client.get(f"/api/v1/projects/{project_id}/groups").json() == []


def test_effective_role_returns_max_of_direct_and_group(auth_client, project_id, group_id, alice):
    _add_user_to_group(group_id, alice["id"])
    auth_client.post(
        f"/api/v1/projects/{project_id}/groups",
        json={"group_id": group_id, "role": "viewer"},
    )
    auth_client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": alice["id"], "role": "tester"},
    )

    with TestingSession() as db:
        role = effective_role(db, alice["id"], project_id)

    assert role == "tester"


def test_effective_role_returns_group_role_when_no_direct_membership(
    auth_client, project_id, group_id, alice,
):
    _add_user_to_group(group_id, alice["id"])
    auth_client.post(
        f"/api/v1/projects/{project_id}/groups",
        json={"group_id": group_id, "role": "viewer"},
    )

    with TestingSession() as db:
        role = effective_role(db, alice["id"], project_id)

    assert role == "viewer"


def test_accessible_project_ids_includes_group_projects(auth_client, group_id, alice):
    project_a = auth_client.post("/api/v1/projects", json={"name": "Direct"}).json()["id"]
    project_b = auth_client.post("/api/v1/projects", json={"name": "ViaGroup"}).json()["id"]
    _add_user_to_group(group_id, alice["id"])
    auth_client.post(
        f"/api/v1/projects/{project_b}/groups",
        json={"group_id": group_id, "role": "viewer"},
    )
    auth_client.post(
        f"/api/v1/projects/{project_a}/members",
        json={"user_id": alice["id"], "role": "tester"},
    )

    with TestingSession() as db:
        ids = accessible_project_ids(db, alice["id"])

    assert ids == {project_a, project_b}


def test_non_owner_cannot_assign_group(client, project_id, group_id):
    with TestingSession() as db:
        db.add(User(
            username="stranger", email="s@x.com",
            hashed_password=hash_password("pw"),
            is_active=True, is_admin=False,
        ))
        db.commit()
    token = client.post(
        "/api/v1/auth/login", data={"username": "stranger", "password": "pw"},
    ).json()["access_token"]

    resp = client.post(
        f"/api/v1/projects/{project_id}/groups",
        json={"group_id": group_id, "role": "viewer"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403


def test_list_projects_includes_those_reached_via_group(client, auth_client, group_id, alice):
    via_group_id = auth_client.post("/api/v1/projects", json={"name": "ViaGroup"}).json()["id"]
    _add_user_to_group(group_id, alice["id"])
    auth_client.post(
        f"/api/v1/projects/{via_group_id}/groups",
        json={"group_id": group_id, "role": "viewer"},
    )
    with TestingSession() as db:
        alice_user = db.get(User, alice["id"])
        alice_user.hashed_password = hash_password("pw")
        db.commit()
    token = client.post(
        "/api/v1/auth/login", data={"username": "alice", "password": "pw"},
    ).json()["access_token"]

    resp = client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    names = [project["name"] for project in resp.json()]
    assert names == ["ViaGroup"]


