"""Tests for /mentions/resolve and /mentions/search."""
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
    return auth_client.post("/api/v1/projects", json={"name": "Mentions Project"}).json()["id"]


def _resolve(client, project_id, tokens):
    return client.post(
        f"/api/v1/projects/{project_id}/mentions/resolve",
        json={"tokens": tokens},
    ).json()


def test_resolve_user_member_is_accessible(auth_client, project_id):
    _seed_member(project_id, "alice")

    result = _resolve(auth_client, project_id, [{"kind": "user", "slug": "alice"}])

    mention = result["mentions"][0]
    assert mention["accessible"] is True
    assert mention["slug"] == "alice"
    assert mention["label"] == "Alice"


def test_resolve_user_unknown_returns_inaccessible(auth_client, project_id):
    result = _resolve(auth_client, project_id, [{"kind": "user", "slug": "ghost"}])

    assert result["mentions"][0]["accessible"] is False


def test_resolve_bug_in_project(auth_client, project_id):
    bug = auth_client.post(
        f"/api/v1/projects/{project_id}/bugs", json={"title": "Crash"},
    ).json()

    result = _resolve(auth_client, project_id, [{"kind": "bug", "id": bug["number"]}])

    mention = result["mentions"][0]
    assert mention["accessible"] is True
    assert mention["url"] == f"/projects/{project_id}/bugs/{bug['number']}"


def test_resolve_bug_in_other_project_inaccessible(auth_client, project_id):
    other = auth_client.post("/api/v1/projects", json={"name": "Other"}).json()["id"]
    bug = auth_client.post(
        f"/api/v1/projects/{other}/bugs", json={"title": "Elsewhere"},
    ).json()

    result = _resolve(auth_client, project_id, [{"kind": "bug", "id": bug["number"]}])

    assert result["mentions"][0]["accessible"] is False


def test_resolve_execution_and_step_chain(auth_client, project_id):
    suite = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "Auth"},
    ).json()
    case = auth_client.post(
        f"/api/v1/suites/{suite['id']}/cases",
        json={"name": "Login", "suite_id": suite["id"]},
    ).json()
    execution = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Sprint 1", "type": "manual", "test_case_ids": [case["id"]]},
    ).json()
    result = auth_client.get(f"/api/v1/executions/{execution['id']}/results").json()[0]

    resolved = _resolve(auth_client, project_id, [
        {"kind": "execution", "id": execution["id"]},
        {"kind": "result", "id": execution["id"], "sub_ids": [result["id"]]},
        {"kind": "case", "id": case["id"]},
    ])

    assert all(item["accessible"] for item in resolved["mentions"])
    assert resolved["mentions"][2]["label"].startswith(f"~{case['id']}")


def test_search_users_by_name(auth_client, project_id):
    _seed_member(project_id, "alice")
    _seed_member(project_id, "bob")

    response = auth_client.get(
        f"/api/v1/projects/{project_id}/mentions/search?kind=user&q=ali",
    ).json()

    assert [hit["slug"] for hit in response["hits"]] == ["alice"]


def test_search_bugs_by_number_or_title(auth_client, project_id):
    auth_client.post(
        f"/api/v1/projects/{project_id}/bugs",
        json={"title": "Login crash"},
    )
    auth_client.post(
        f"/api/v1/projects/{project_id}/bugs",
        json={"title": "Footer typo"},
    )

    by_text = auth_client.get(
        f"/api/v1/projects/{project_id}/mentions/search?kind=bug&q=login",
    ).json()
    by_id = auth_client.get(
        f"/api/v1/projects/{project_id}/mentions/search?kind=bug&q=1",
    ).json()

    assert any("Login" in hit["label"] for hit in by_text["hits"])
    assert by_id["hits"][0]["id"] == 1


def test_search_rejects_unknown_kind(auth_client, project_id):
    response = auth_client.get(
        f"/api/v1/projects/{project_id}/mentions/search?kind=banana&q=x",
    )

    assert response.status_code == 422
