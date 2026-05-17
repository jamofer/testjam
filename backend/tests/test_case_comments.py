"""Tests for /cases/{id}/comments + mention fan-out from case comments."""
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


def _seed_member(project_id: int, username: str, role: str = "tester") -> int:
    with TestingSession() as db:
        user = User(
            username=username,
            email=f"{username}@x.com",
            hashed_password=hash_password("pw"),
            is_active=True,
            full_name=username.title(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.add(ProjectMember(project_id=project_id, user_id=user.id, role=role))
        db.commit()
        return user.id


@pytest.fixture
def project_id(auth_client):
    return auth_client.post("/api/v1/projects", json={"name": "Case Comments"}).json()["id"]


@pytest.fixture
def case_id(auth_client, project_id):
    suite = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "Auth"},
    ).json()
    case = auth_client.post(
        f"/api/v1/suites/{suite['id']}/cases",
        json={"name": "Login flow", "suite_id": suite["id"]},
    ).json()
    return case["id"]


def test_case_comment_round_trip(auth_client, case_id):
    created = auth_client.post(
        f"/api/v1/cases/{case_id}/comments", json={"body": "Needs more steps"},
    )
    listing = auth_client.get(f"/api/v1/cases/{case_id}/comments").json()

    assert created.status_code == 201
    assert created.json()["body"] == "Needs more steps"
    assert len(listing) == 1


def test_case_comment_edit_by_author(auth_client, case_id):
    comment = auth_client.post(
        f"/api/v1/cases/{case_id}/comments", json={"body": "Original"},
    ).json()

    response = auth_client.put(
        f"/api/v1/cases/{case_id}/comments/{comment['id']}",
        json={"body": "Edited"},
    )

    assert response.status_code == 200
    assert response.json()["body"] == "Edited"


def test_case_comment_mention_notifies_member(auth_client, project_id, case_id):
    _seed_member(project_id, "alice")

    auth_client.post(
        f"/api/v1/cases/{case_id}/comments", json={"body": "ping @alice"},
    )

    notifications = _login("alice").get("/api/v1/notifications").json()
    assert len(notifications) == 1
    assert notifications[0]["type"] == "mention_in_comment"
    assert notifications[0]["link"] == f"/cases/{case_id}"


def test_case_comment_mention_excludes_outsider(auth_client, project_id, case_id):
    with TestingSession() as db:
        outsider = User(
            username="ghost", email="ghost@x.com",
            hashed_password=hash_password("pw"), is_active=True,
        )
        db.add(outsider)
        db.commit()

    auth_client.post(
        f"/api/v1/cases/{case_id}/comments", json={"body": "hi @ghost"},
    )

    assert _login("ghost").get("/api/v1/notifications").json() == []


def test_delete_case_comment_by_author(auth_client, case_id):
    comment = auth_client.post(
        f"/api/v1/cases/{case_id}/comments", json={"body": "drop me"},
    ).json()

    deleted = auth_client.delete(f"/api/v1/cases/{case_id}/comments/{comment['id']}")

    assert deleted.status_code == 204
    assert auth_client.get(f"/api/v1/cases/{case_id}/comments").json() == []
