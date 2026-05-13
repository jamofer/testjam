"""Owner reassignment + self-delete + AppSettings gating on user delete."""
import pytest

from testjam.auth.security import hash_password
from testjam.models.project import Project, ProjectMember
from testjam.models.settings import AppSettings
from testjam.models.user import User
from tests.conftest import TestingSession


@pytest.fixture
def user_factory():
    def _create(username: str, password: str = "pw", is_admin: bool = False) -> User:
        with TestingSession() as db:
            user = User(
                username=username,
                email=f"{username}@x.com",
                hashed_password=hash_password(password),
                is_active=True,
                is_admin=is_admin,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

    return _create


def _grant_membership(project_id: int, user_id: int, role: str) -> None:
    with TestingSession() as db:
        db.add(ProjectMember(project_id=project_id, user_id=user_id, role=role))
        db.commit()


def _make_owner(project_id: int, user_id: int) -> None:
    with TestingSession() as db:
        existing = (
            db.query(ProjectMember)
            .filter_by(project_id=project_id, user_id=user_id)
            .first()
        )
        if existing:
            existing.role = "owner"
        else:
            db.add(ProjectMember(project_id=project_id, user_id=user_id, role="owner"))
        db.commit()


def _make_unique_owner(project_id: int, user_id: int) -> None:
    """Demote any other owners on the project, then promote `user_id`."""
    with TestingSession() as db:
        db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.role == "owner",
            ProjectMember.user_id != user_id,
        ).update({"role": "member"}, synchronize_session=False)
        existing = (
            db.query(ProjectMember)
            .filter_by(project_id=project_id, user_id=user_id)
            .first()
        )
        if existing:
            existing.role = "owner"
        else:
            db.add(ProjectMember(project_id=project_id, user_id=user_id, role="owner"))
        db.commit()


def _set_self_delete(allowed: bool) -> None:
    with TestingSession() as db:
        settings = db.get(AppSettings, 1)
        if settings is None:
            settings = AppSettings(id=1, allow_user_self_delete=allowed)
            db.add(settings)
        else:
            settings.allow_user_self_delete = allowed
        db.commit()


def test_delete_user_with_no_owned_projects_succeeds_without_body(admin_client, user_factory):
    target = user_factory("nobody")

    response = admin_client.delete(f"/api/v1/users/{target.id}")

    assert response.status_code == 204


def test_delete_user_with_shared_owner_succeeds_without_action(admin_client, user_factory):
    target = user_factory("co_owner")
    backup = user_factory("backup_owner")
    project_id = admin_client.post("/api/v1/projects", json={"name": "Shared"}).json()["id"]
    _make_owner(project_id, target.id)
    _make_owner(project_id, backup.id)

    response = admin_client.delete(f"/api/v1/users/{target.id}")

    assert response.status_code == 204


def test_delete_unique_owner_without_action_returns_409(admin_client, user_factory):
    target = user_factory("solo")
    project_id = admin_client.post("/api/v1/projects", json={"name": "SoloProj"}).json()["id"]
    _make_unique_owner(project_id, target.id)

    response = admin_client.delete(f"/api/v1/users/{target.id}")

    assert response.status_code == 409
    detail = response.json()["detail"]
    listed_ids = [project["project_id"] for project in detail["owned_projects"]]
    assert project_id in listed_ids


def test_reassign_action_promotes_target_member_to_owner(admin_client, user_factory):
    target = user_factory("departing")
    successor = user_factory("successor")
    project_id = admin_client.post("/api/v1/projects", json={"name": "Handover"}).json()["id"]
    _make_unique_owner(project_id, target.id)
    _grant_membership(project_id, successor.id, "member")

    response = admin_client.request(
        "DELETE", f"/api/v1/users/{target.id}",
        json={"owned_projects": [
            {"project_id": project_id, "action": "reassign", "new_owner_id": successor.id},
        ]},
    )

    assert response.status_code == 204
    with TestingSession() as db:
        new_owner = (
            db.query(ProjectMember)
            .filter_by(project_id=project_id, role="owner")
            .first()
        )
        assert new_owner is not None
        assert new_owner.user_id == successor.id


def test_reassign_to_user_not_yet_a_member_adds_them_as_owner(admin_client, user_factory):
    target = user_factory("departing")
    successor = user_factory("outsider")
    project_id = admin_client.post("/api/v1/projects", json={"name": "GiveAway"}).json()["id"]
    _make_unique_owner(project_id, target.id)

    response = admin_client.request(
        "DELETE", f"/api/v1/users/{target.id}",
        json={"owned_projects": [
            {"project_id": project_id, "action": "reassign", "new_owner_id": successor.id},
        ]},
    )

    assert response.status_code == 204
    with TestingSession() as db:
        owner = db.query(ProjectMember).filter_by(project_id=project_id, role="owner").first()
        assert owner.user_id == successor.id


def test_archive_action_archives_the_project(admin_client, user_factory):
    target = user_factory("departing")
    project_id = admin_client.post("/api/v1/projects", json={"name": "Frozen"}).json()["id"]
    _make_unique_owner(project_id, target.id)

    response = admin_client.request(
        "DELETE", f"/api/v1/users/{target.id}",
        json={"owned_projects": [{"project_id": project_id, "action": "archive"}]},
    )

    assert response.status_code == 204
    with TestingSession() as db:
        project = db.get(Project, project_id)
        assert project.archived_at is not None


def test_reassign_without_new_owner_id_returns_400(admin_client, user_factory):
    target = user_factory("departing")
    project_id = admin_client.post("/api/v1/projects", json={"name": "BadReassign"}).json()["id"]
    _make_unique_owner(project_id, target.id)

    response = admin_client.request(
        "DELETE", f"/api/v1/users/{target.id}",
        json={"owned_projects": [{"project_id": project_id, "action": "reassign"}]},
    )

    assert response.status_code == 400


def test_reassign_to_target_themselves_returns_400(admin_client, user_factory):
    target = user_factory("departing")
    project_id = admin_client.post("/api/v1/projects", json={"name": "SelfReassign"}).json()["id"]
    _make_unique_owner(project_id, target.id)

    response = admin_client.request(
        "DELETE", f"/api/v1/users/{target.id}",
        json={"owned_projects": [
            {"project_id": project_id, "action": "reassign", "new_owner_id": target.id},
        ]},
    )

    assert response.status_code == 400


def test_deleted_user_loses_all_project_memberships(admin_client, user_factory):
    target = user_factory("multi")
    project_a = admin_client.post("/api/v1/projects", json={"name": "A"}).json()["id"]
    project_b = admin_client.post("/api/v1/projects", json={"name": "B"}).json()["id"]
    _grant_membership(project_a, target.id, "member")
    _grant_membership(project_b, target.id, "member")

    response = admin_client.delete(f"/api/v1/users/{target.id}")

    assert response.status_code == 204
    with TestingSession() as db:
        remaining = (
            db.query(ProjectMember).filter(ProjectMember.user_id == target.id).count()
        )
        assert remaining == 0


def test_self_delete_disabled_by_default(admin_client, user_factory):
    user_factory("selfie", "pw")
    token = admin_client.post(
        "/api/v1/auth/login", data={"username": "selfie", "password": "pw"},
    ).json()["access_token"]
    admin_client.headers["Authorization"] = f"Bearer {token}"

    response = admin_client.delete("/api/v1/users/me")

    assert response.status_code == 403


def test_self_delete_works_when_admin_enables_setting(admin_client, user_factory):
    target = user_factory("selfie", "pw")
    _set_self_delete(True)
    token = admin_client.post(
        "/api/v1/auth/login", data={"username": "selfie", "password": "pw"},
    ).json()["access_token"]
    admin_client.headers["Authorization"] = f"Bearer {token}"

    response = admin_client.delete("/api/v1/users/me")

    assert response.status_code == 204
    with TestingSession() as db:
        record = db.get(User, target.id)
        assert record.deleted_at is not None


def test_self_delete_blocks_unique_owner_without_action(admin_client, user_factory):
    target = user_factory("solo_self", "pw")
    project_id = admin_client.post("/api/v1/projects", json={"name": "SelfSolo"}).json()["id"]
    _make_unique_owner(project_id, target.id)
    _set_self_delete(True)
    token = admin_client.post(
        "/api/v1/auth/login", data={"username": "solo_self", "password": "pw"},
    ).json()["access_token"]
    admin_client.headers["Authorization"] = f"Bearer {token}"

    response = admin_client.delete("/api/v1/users/me")

    assert response.status_code == 409


def test_public_settings_exposes_self_delete_flag(client):
    _set_self_delete(True)

    body = client.get("/api/v1/settings/public").json()

    assert body["allow_user_self_delete"] is True
