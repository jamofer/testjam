"""Project archive/unarchive + read-only enforcement on archived projects."""
import pytest

from testjam.auth.security import hash_password
from testjam.models.project import Project, ProjectMember
from testjam.models.user import User
from tests.conftest import TestingSession


def _create_project(client, name: str) -> int:
    return client.post("/api/v1/projects", json={"name": name}).json()["id"]


def _archive(client, project_id: int):
    return client.post(f"/api/v1/projects/{project_id}/archive")


def _unarchive(client, project_id: int):
    return client.post(f"/api/v1/projects/{project_id}/unarchive")


def test_archive_marks_project_with_timestamp(admin_client):
    project_id = _create_project(admin_client, "ToArchive")

    response = _archive(admin_client, project_id)

    assert response.status_code == 200
    assert response.json()["archived_at"] is not None


def test_archive_is_idempotent(admin_client):
    project_id = _create_project(admin_client, "Twice")

    first = _archive(admin_client, project_id)
    second = _archive(admin_client, project_id)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["archived_at"] == second.json()["archived_at"]


def test_unarchive_clears_timestamp(admin_client):
    project_id = _create_project(admin_client, "Unarc")
    _archive(admin_client, project_id)

    response = _unarchive(admin_client, project_id)

    assert response.status_code == 200
    assert response.json()["archived_at"] is None


def test_default_listing_omits_archived(admin_client):
    keep = _create_project(admin_client, "Keep")
    drop = _create_project(admin_client, "Drop")
    _archive(admin_client, drop)

    listing = admin_client.get("/api/v1/projects").json()

    listed_ids = {p["id"] for p in listing}
    assert keep in listed_ids
    assert drop not in listed_ids


def test_include_archived_param_returns_all(admin_client):
    keep = _create_project(admin_client, "Keep2")
    drop = _create_project(admin_client, "Drop2")
    _archive(admin_client, drop)

    listing = admin_client.get("/api/v1/projects?include_archived=true").json()

    listed_ids = {p["id"] for p in listing}
    assert keep in listed_ids
    assert drop in listed_ids


def test_archived_project_rejects_update(admin_client):
    project_id = _create_project(admin_client, "Frozen")
    _archive(admin_client, project_id)

    response = admin_client.put(
        f"/api/v1/projects/{project_id}", json={"description": "new"},
    )

    assert response.status_code == 409
    assert "archived" in response.json()["detail"].lower()


def test_archived_project_rejects_new_suite(admin_client):
    project_id = _create_project(admin_client, "FrozenSuites")
    _archive(admin_client, project_id)

    response = admin_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    )

    assert response.status_code == 409


def test_archived_project_rejects_new_execution(admin_client):
    project_id = _create_project(admin_client, "FrozenExec")
    _archive(admin_client, project_id)

    response = admin_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual", "test_case_ids": []},
    )

    assert response.status_code == 409


def test_archived_project_rejects_new_version(admin_client):
    project_id = _create_project(admin_client, "FrozenVer")
    _archive(admin_client, project_id)

    response = admin_client.post(
        f"/api/v1/projects/{project_id}/versions", json={"name": "v1.0"},
    )

    assert response.status_code == 409


def test_archived_project_rejects_new_plan(admin_client):
    project_id = _create_project(admin_client, "FrozenPlan")
    _archive(admin_client, project_id)

    response = admin_client.post(
        f"/api/v1/projects/{project_id}/plans", json={"title": "P"},
    )

    assert response.status_code == 409


def test_unarchived_project_accepts_mutations_again(admin_client):
    project_id = _create_project(admin_client, "Thaw")
    _archive(admin_client, project_id)
    _unarchive(admin_client, project_id)

    response = admin_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    )

    assert response.status_code == 201


def test_non_owner_member_cannot_archive(admin_client):
    project_id = _create_project(admin_client, "OwnerOnly")
    with TestingSession() as db:
        member = User(
            username="member",
            email="member@x.com",
            hashed_password=hash_password("pw"),
            is_active=True,
        )
        db.add(member)
        db.commit()
        db.add(ProjectMember(project_id=project_id, user_id=member.id, role="member"))
        db.commit()

    token = admin_client.post(
        "/api/v1/auth/login", data={"username": "member", "password": "pw"},
    ).json()["access_token"]
    admin_client.headers["Authorization"] = f"Bearer {token}"

    response = _archive(admin_client, project_id)

    assert response.status_code == 403


def test_archive_unknown_project_returns_404(admin_client):
    response = _archive(admin_client, 99999)

    assert response.status_code in (403, 404)
