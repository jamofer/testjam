"""Tests for the public-report share token API."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from testjam.auth.security import hash_password
from testjam.main import app
from testjam.models.project import ProjectMember
from testjam.models.public_report import PublicReport
from testjam.models.user import User
from tests.conftest import TestingSession


PUBLIC_PATH = "/api/v1/public/reports"
PROJECT_PUBLIC_PATH = "/api/v1/projects/{project_id}/public-reports"


def _login(username: str, password: str = "pw") -> TestClient:
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login", data={"username": username, "password": password},
    )
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    return client


def _seed_member(project_id: int, username: str, role: str) -> int:
    with TestingSession() as db:
        user = User(
            username=username,
            email=f"{username}@x.com",
            hashed_password=hash_password("pw"),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.add(ProjectMember(project_id=project_id, user_id=user.id, role=role))
        db.commit()
        return user.id


@pytest.fixture
def project_id(auth_client):
    return auth_client.post("/api/v1/projects", json={"name": "PR Project"}).json()["id"]


@pytest.fixture
def tester_client(project_id):
    _seed_member(project_id, "tester", "tester")
    return _login("tester")


@pytest.fixture
def owner_client(project_id):
    _seed_member(project_id, "owner_member", "owner")
    return _login("owner_member")


@pytest.fixture
def execution_id(auth_client, project_id):
    suite = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "Suite"},
    ).json()
    case = auth_client.post(
        f"/api/v1/suites/{suite['id']}/cases",
        json={"name": "Case", "suite_id": suite["id"]},
    ).json()
    execution = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual", "test_case_ids": [case["id"]]},
    ).json()
    return execution["id"]


def _create_bug(client, project_id, **overrides):
    payload = {"title": "Login broken", "severity": "high"}
    payload.update(overrides)
    return client.post(f"/api/v1/projects/{project_id}/bugs", json=payload)


def test_create_bug_report_token_returns_raw_token_once(auth_client, project_id):
    _create_bug(auth_client, project_id)

    response = auth_client.post(
        PROJECT_PUBLIC_PATH.format(project_id=project_id),
        json={"kind": "bug_report", "label": "Sprint 7 release notes"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["kind"] == "bug_report"
    assert body["token"]
    assert body["url_path"] == f"/api/v1/public/reports/{body['token']}"
    assert body["label"] == "Sprint 7 release notes"

    listed = auth_client.get(PROJECT_PUBLIC_PATH.format(project_id=project_id)).json()
    assert len(listed) == 1
    assert "token" not in listed[0]


def test_create_requires_owner_role_for_non_admin(tester_client, project_id):
    response = tester_client.post(
        PROJECT_PUBLIC_PATH.format(project_id=project_id),
        json={"kind": "bug_report"},
    )

    assert response.status_code == 403


def test_owner_member_can_create_token(owner_client, project_id):
    response = owner_client.post(
        PROJECT_PUBLIC_PATH.format(project_id=project_id),
        json={"kind": "bug_report"},
    )

    assert response.status_code == 201
    assert response.json()["token"]


def test_execution_kind_requires_execution_id(auth_client, project_id):
    response = auth_client.post(
        PROJECT_PUBLIC_PATH.format(project_id=project_id),
        json={"kind": "execution"},
    )

    assert response.status_code == 422


def test_create_execution_token_validates_project_match(auth_client, project_id, execution_id):
    other = auth_client.post("/api/v1/projects", json={"name": "Other"}).json()

    response = auth_client.post(
        PROJECT_PUBLIC_PATH.format(project_id=other["id"]),
        json={"kind": "execution", "execution_id": execution_id},
    )

    assert response.status_code == 400


def test_public_bug_report_render_returns_html(client, auth_client, project_id):
    _create_bug(auth_client, project_id, title="Public bug", severity="critical")
    token = auth_client.post(
        PROJECT_PUBLIC_PATH.format(project_id=project_id),
        json={"kind": "bug_report"},
    ).json()["token"]

    response = client.get(f"{PUBLIC_PATH}/{token}")

    assert response.status_code == 200
    assert "Public bug" in response.text
    assert "Critical" in response.text


def test_public_execution_render_returns_html(client, auth_client, project_id, execution_id):
    token = auth_client.post(
        PROJECT_PUBLIC_PATH.format(project_id=project_id),
        json={"kind": "execution", "execution_id": execution_id, "label": "Run share"},
    ).json()["token"]

    response = client.get(f"{PUBLIC_PATH}/{token}")

    assert response.status_code == 200
    assert "Run" in response.text
    assert "shared" in response.text.lower() or "Run share" in response.text


def test_public_render_does_not_require_auth(client, auth_client, project_id):
    _create_bug(auth_client, project_id)
    token = auth_client.post(
        PROJECT_PUBLIC_PATH.format(project_id=project_id),
        json={"kind": "bug_report"},
    ).json()["token"]

    response = client.get(f"{PUBLIC_PATH}/{token}")

    assert response.status_code == 200


def test_unknown_token_returns_404(client):
    response = client.get(f"{PUBLIC_PATH}/not-a-real-token")

    assert response.status_code == 404


def test_revoked_token_stops_rendering(client, auth_client, project_id):
    _create_bug(auth_client, project_id)
    created = auth_client.post(
        PROJECT_PUBLIC_PATH.format(project_id=project_id),
        json={"kind": "bug_report"},
    ).json()
    token = created["token"]

    revoke = auth_client.delete(
        f"{PROJECT_PUBLIC_PATH.format(project_id=project_id)}/{created['id']}",
    )

    assert revoke.status_code == 204
    assert client.get(f"{PUBLIC_PATH}/{token}").status_code == 404


def test_expired_token_returns_404(client, auth_client, project_id):
    _create_bug(auth_client, project_id)
    created = auth_client.post(
        PROJECT_PUBLIC_PATH.format(project_id=project_id),
        json={"kind": "bug_report"},
    ).json()
    expired_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    with TestingSession() as db:
        row = db.get(PublicReport, created["id"])
        row.expires_at = expired_at
        db.commit()

    response = client.get(f"{PUBLIC_PATH}/{created['token']}")

    assert response.status_code == 404


def test_view_count_increments_on_each_render(client, auth_client, project_id):
    _create_bug(auth_client, project_id)
    created = auth_client.post(
        PROJECT_PUBLIC_PATH.format(project_id=project_id),
        json={"kind": "bug_report"},
    ).json()
    token = created["token"]

    client.get(f"{PUBLIC_PATH}/{token}")
    client.get(f"{PUBLIC_PATH}/{token}")

    listed = auth_client.get(PROJECT_PUBLIC_PATH.format(project_id=project_id)).json()
    assert listed[0]["view_count"] == 2
    assert listed[0]["last_viewed_at"] is not None


def test_list_requires_owner(tester_client, project_id):
    response = tester_client.get(PROJECT_PUBLIC_PATH.format(project_id=project_id))

    assert response.status_code == 403


def test_revoke_blocks_when_not_owner(tester_client, auth_client, project_id):
    created = auth_client.post(
        PROJECT_PUBLIC_PATH.format(project_id=project_id),
        json={"kind": "bug_report"},
    ).json()

    response = tester_client.delete(
        f"{PROJECT_PUBLIC_PATH.format(project_id=project_id)}/{created['id']}",
    )

    assert response.status_code == 403
