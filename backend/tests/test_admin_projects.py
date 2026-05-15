import pytest

from testjam.auth.security import hash_password
from testjam.models.execution import TestExecution
from testjam.models.project import ProjectMember
from testjam.models.testcase import TestCase
from testjam.models.user import User
from tests.conftest import TestingSession


@pytest.fixture
def world(auth_client):
    project_a = auth_client.post("/api/v1/projects", json={"name": "Alpha"}).json()
    project_b = auth_client.post("/api/v1/projects", json={"name": "Bravo"}).json()
    suite = auth_client.post(
        f"/api/v1/projects/{project_a['id']}/suites", json={"name": "S"},
    ).json()
    with TestingSession() as db:
        db.add_all([
            TestCase(suite_id=suite["id"], name="c1"),
            TestCase(suite_id=suite["id"], name="c2"),
            TestExecution(
                project_id=project_a["id"], title="r", type="manual", status="completed",
            ),
        ])
        db.commit()
    return {"alpha": project_a, "bravo": project_b}


@pytest.fixture
def alice(auth_client):
    return auth_client.post(
        "/api/v1/users",
        json={"username": "alice", "email": "alice@x.com", "password": "pw"},
    ).json()


def _login_plain(client) -> str:
    with TestingSession() as db:
        db.add(User(
            username="plain", email="plain@x.com",
            hashed_password=hash_password("pw"),
            is_active=True, is_admin=False,
        ))
        db.commit()
    return client.post(
        "/api/v1/auth/login", data={"username": "plain", "password": "pw"},
    ).json()["access_token"]


def _membership(project_id: int, user_id: int) -> ProjectMember | None:
    with TestingSession() as db:
        return (
            db.query(ProjectMember)
            .filter_by(project_id=project_id, user_id=user_id)
            .first()
        )


def test_admin_projects_returns_global_listing(auth_client, world):
    resp = auth_client.get("/api/v1/admin/projects")

    assert resp.status_code == 200
    names = [row["name"] for row in resp.json()]
    assert names == ["Alpha", "Bravo"]


def test_admin_projects_includes_owner_and_counts(auth_client, world):
    rows = auth_client.get("/api/v1/admin/projects").json()
    alpha = next(row for row in rows if row["name"] == "Alpha")

    assert alpha["owner_username"] == "u"
    assert alpha["member_count"] == 1
    assert alpha["case_count"] == 2
    assert alpha["last_execution_at"] is not None


def test_admin_projects_requires_admin(client):
    token = _login_plain(client)

    resp = client.get(
        "/api/v1/admin/projects",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403


def test_transfer_ownership_promotes_new_owner_and_demotes_old(auth_client, world, alice):
    project_id = world["alpha"]["id"]

    resp = auth_client.post(
        f"/api/v1/projects/{project_id}/transfer-ownership",
        json={"new_owner_id": alice["id"]},
    )

    assert resp.status_code == 200
    alice_membership = _membership(project_id, alice["id"])
    assert alice_membership.role == "owner"

    with TestingSession() as db:
        original_owner = db.query(User).filter_by(username="u").one()
        old_membership = _membership(project_id, original_owner.id)
    assert old_membership.role == "editor"


def test_transfer_ownership_rejects_unknown_user(auth_client, world):
    resp = auth_client.post(
        f"/api/v1/projects/{world['alpha']['id']}/transfer-ownership",
        json={"new_owner_id": 99999},
    )

    assert resp.status_code == 400


def test_transfer_ownership_idempotent_when_already_owner(auth_client, world):
    project_id = world["alpha"]["id"]
    with TestingSession() as db:
        current_owner = (
            db.query(ProjectMember)
            .filter_by(project_id=project_id, role="owner")
            .first()
        )
        owner_user_id = current_owner.user_id

    resp = auth_client.post(
        f"/api/v1/projects/{project_id}/transfer-ownership",
        json={"new_owner_id": owner_user_id},
    )

    assert resp.status_code == 200
    refreshed = _membership(project_id, owner_user_id)
    assert refreshed.role == "owner"


def test_transfer_ownership_requires_owner_or_admin(auth_client, world, alice):
    project_id = world["alpha"]["id"]
    with TestingSession() as db:
        db.add(User(
            username="stranger", email="s@x.com",
            hashed_password=hash_password("pw"),
            is_active=True, is_admin=False,
        ))
        db.commit()
    token = auth_client.post(
        "/api/v1/auth/login", data={"username": "stranger", "password": "pw"},
    ).json()["access_token"]

    resp = auth_client.post(
        f"/api/v1/projects/{project_id}/transfer-ownership",
        json={"new_owner_id": alice["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403
