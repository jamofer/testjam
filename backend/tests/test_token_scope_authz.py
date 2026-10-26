import pytest
from fastapi.testclient import TestClient

from testjam.main import app

SCOPED_ENDPOINTS = [
    ("PUT", "/api/v1/suites/{suite_id}", {"name": "renamed"}),
    ("DELETE", "/api/v1/suites/{suite_id}", None),
    ("POST", "/api/v1/suites/{suite_id}/steps", {"action": "Boot", "step_type": "setup", "order": 1}),
    ("POST", "/api/v1/suites/{suite_id}/cases", {"name": "Injected", "suite_id": "{suite_id}"}),
    ("PUT", "/api/v1/cases/{case_id}", {"name": "renamed"}),
    ("DELETE", "/api/v1/cases/{case_id}", None),
    ("POST", "/api/v1/cases/{case_id}/steps", {"action": "Click", "order": 2}),
    ("POST", "/api/v1/cases/{case_id}/comments", {"body": "hi"}),
    ("GET", "/api/v1/cases/{case_id}/comments", None),
    ("POST", "/api/v1/projects/{project_id}/bugs", {"title": "Injected"}),
    ("GET", "/api/v1/bugs/{bug_id}", None),
    ("PUT", "/api/v1/bugs/{bug_id}", {"title": "renamed"}),
    ("DELETE", "/api/v1/bugs/{bug_id}", None),
    ("POST", "/api/v1/bugs/{bug_id}/comments", {"body": "hi"}),
    ("POST", "/api/v1/bugs/{bug_id}/watch", None),
    ("GET", "/api/v1/plans/{plan_id}", None),
    ("PUT", "/api/v1/plans/{plan_id}", {"title": "renamed"}),
    ("DELETE", "/api/v1/plans/{plan_id}", None),
    ("GET", "/api/v1/projects/{project_id}/webhooks", None),
    ("GET", "/api/v1/webhooks/{webhook_id}", None),
    ("DELETE", "/api/v1/webhooks/{webhook_id}", None),
    ("GET", "/api/v1/custom-fields/{custom_field_id}", None),
]

BUG_READ_ENDPOINTS = [
    "/api/v1/bugs/{bug_id}",
    "/api/v1/bugs/{bug_id}/comments",
    "/api/v1/bugs/{bug_id}/context",
    "/api/v1/bugs/{bug_id}/watchers",
    "/api/v1/bugs/{bug_id}/links",
    "/api/v1/bugs/{bug_id}/activity",
    "/api/v1/bugs/{bug_id}/attachments",
    "/api/v1/bugs/{bug_id}/attachments/{bug_attachment_id}/download",
]

ACCOUNT_ENDPOINTS = [
    ("POST", "/api/v1/users/me/tokens", {"name": "escape"}),
    ("GET", "/api/v1/users/me/tokens", None),
    ("PUT", "/api/v1/users/me", {"email": "taken-over@test.com"}),
    ("PUT", "/api/v1/users/me/password", {"current_password": "pw", "new_password": "pwned123"}),
    ("POST", "/api/v1/users", {"username": "backdoor", "email": "backdoor@test.com", "password": "pw"}),
]


@pytest.fixture
def owner_client(role_project):
    return role_project["clients"]["owner"]


@pytest.fixture
def resources(owner_client, role_project):
    project_id = role_project["project_id"]
    suite_id = owner_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    case_id = owner_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "TC", "suite_id": suite_id},
    ).json()["id"]
    bug_id = owner_client.post(
        f"/api/v1/projects/{project_id}/bugs", json={"title": "Crash"},
    ).json()["id"]
    bug_attachment_id = owner_client.post(
        f"/api/v1/bugs/{bug_id}/attachments", files={"file": ("log.txt", b"trace", "text/plain")},
    ).json()["id"]
    plan_id = owner_client.post(
        f"/api/v1/projects/{project_id}/plans", json={"title": "Release"},
    ).json()["id"]
    webhook_id = owner_client.post(
        f"/api/v1/projects/{project_id}/webhooks",
        json={"name": "CI", "url": "https://hooks.example/ci", "events": ["execution.created"]},
    ).json()["id"]
    custom_field_id = owner_client.post(
        f"/api/v1/projects/{project_id}/custom-fields",
        json={"entity_type": "bug", "key": "component", "label": "Component", "type": "text"},
    ).json()["id"]
    return {
        "project_id": project_id,
        "suite_id": suite_id,
        "case_id": case_id,
        "bug_id": bug_id,
        "bug_attachment_id": bug_attachment_id,
        "plan_id": plan_id,
        "webhook_id": webhook_id,
        "custom_field_id": custom_field_id,
    }


@pytest.fixture
def foreign_scoped_token_client(owner_client):
    other_project_id = owner_client.post("/api/v1/projects", json={"name": "Other"}).json()["id"]
    return _token_client(owner_client, other_project_id)


@pytest.fixture
def admin_project_token_client(auth_client):
    project_id = auth_client.post("/api/v1/projects", json={"name": "CI"}).json()["id"]
    return _token_client(auth_client, project_id)


@pytest.mark.parametrize("method,path,payload", SCOPED_ENDPOINTS)
def test_token_scoped_to_another_project_is_forbidden(
    foreign_scoped_token_client, resources, method, path, payload,
):
    response = _send(foreign_scoped_token_client, method, path, payload, resources)

    assert response.status_code == 403


@pytest.mark.parametrize("path", BUG_READ_ENDPOINTS)
def test_outsider_cannot_read_bug(role_project, resources, path):
    outsider = role_project["clients"]["outsider"]

    response = outsider.get(path.format(**resources))

    assert response.status_code == 403


@pytest.mark.parametrize("path", BUG_READ_ENDPOINTS)
def test_viewer_can_read_bug(role_project, resources, path):
    viewer = role_project["clients"]["viewer"]

    response = viewer.get(path.format(**resources))

    assert response.status_code == 200


def test_viewer_cannot_watch_bug(role_project, resources):
    viewer = role_project["clients"]["viewer"]

    response = viewer.post(f"/api/v1/bugs/{resources['bug_id']}/watch")

    assert response.status_code == 403


def test_tester_cannot_delete_bug(role_project, resources):
    tester = role_project["clients"]["tester"]

    response = tester.delete(f"/api/v1/bugs/{resources['bug_id']}")

    assert response.status_code == 403


def test_tester_cannot_manage_webhooks(role_project, resources):
    tester = role_project["clients"]["tester"]

    response = tester.get(f"/api/v1/webhooks/{resources['webhook_id']}")

    assert response.status_code == 403


def test_removed_member_cannot_edit_own_bug_comment(role_project, resources, owner_client):
    tester = role_project["clients"]["tester"]
    comment_id = tester.post(
        f"/api/v1/bugs/{resources['bug_id']}/comments", json={"body": "mine"},
    ).json()["id"]
    tester_id = tester.get("/api/v1/users/me").json()["id"]
    owner_client.delete(f"/api/v1/projects/{resources['project_id']}/members/{tester_id}")

    response = tester.put(
        f"/api/v1/bugs/{resources['bug_id']}/comments/{comment_id}", json={"body": "edited"},
    )

    assert response.status_code == 403


@pytest.mark.parametrize("method,path,payload", ACCOUNT_ENDPOINTS)
def test_admin_project_token_cannot_reach_account_routes(
    admin_project_token_client, method, path, payload,
):
    response = _send(admin_project_token_client, method, path, payload, {})

    assert response.status_code == 403


def test_admin_project_token_can_still_read_own_identity(admin_project_token_client):
    response = admin_project_token_client.get("/api/v1/users/me")

    assert response.status_code == 200


def test_admin_personal_token_can_still_administer(auth_client):
    raw_token = auth_client.post("/api/v1/users/me/tokens", json={"name": "personal"}).json()["token"]
    client = TestClient(app)
    client.headers["X-API-Key"] = raw_token

    response = client.post(
        "/api/v1/users", json={"username": "newbie", "email": "newbie@test.com", "password": "pw"},
    )

    assert response.status_code == 201


def _token_client(owner: TestClient, project_id: int) -> TestClient:
    raw_token = owner.post(f"/api/v1/projects/{project_id}/tokens", json={"name": "ci"}).json()["token"]
    client = TestClient(app)
    client.headers["X-API-Key"] = raw_token
    return client


def _send(client: TestClient, method: str, path: str, payload, resources: dict):
    url = path.format(**resources)
    if payload is None:
        return client.request(method, url)
    return client.request(method, url, json=_fill(payload, resources))


def _fill(value, resources: dict):
    if isinstance(value, dict):
        return {key: _fill(item, resources) for key, item in value.items()}
    if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
        return resources[value[1:-1]]
    return value
