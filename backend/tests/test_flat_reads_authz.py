import pytest
from fastapi.testclient import TestClient

from testjam.main import app

READ_ENDPOINTS = [
    ("GET", "/api/v1/suites/{suite_id}"),
    ("GET", "/api/v1/suites/{suite_id}/cases"),
    ("GET", "/api/v1/suites/{suite_id}/delete-impact"),
    ("GET", "/api/v1/cases/{case_id}"),
    ("GET", "/api/v1/cases/{case_id}/revisions"),
    ("GET", "/api/v1/cases/{case_id}/revisions/{revision_id}"),
    ("GET", "/api/v1/cases/{case_id}/steps"),
    ("GET", "/api/v1/cases/{case_id}/attachments"),
    ("GET", "/api/v1/cases/{case_id}/attachments/{case_attachment_id}/download"),
    ("GET", "/api/v1/environments/{environment_id}"),
    ("GET", "/api/v1/executions/{execution_id}/export/xlsx"),
    ("GET", "/api/v1/executions/{execution_id}/export/html"),
    ("GET", "/api/v1/executions/{execution_id}/attachments"),
    ("GET", "/api/v1/executions/{execution_id}/attachments/{execution_attachment_id}/download"),
    ("GET", "/api/v1/results/{result_id}/attachments"),
    ("GET", "/api/v1/results/{result_id}/attachments/{result_attachment_id}/download"),
]

WRITE_ENDPOINTS = [
    ("POST", "/api/v1/executions/{execution_id}/attachments"),
    ("DELETE", "/api/v1/executions/{execution_id}/attachments/{execution_attachment_id}"),
    ("POST", "/api/v1/results/{result_id}/attachments"),
    ("DELETE", "/api/v1/results/{result_id}/attachments/{result_attachment_id}"),
]

ALL_ENDPOINTS = READ_ENDPOINTS + WRITE_ENDPOINTS

ATTACHMENT = ("notes.txt", b"evidence", "text/plain")


@pytest.fixture
def owner_client(role_project):
    return role_project["clients"]["owner"]


@pytest.fixture
def outsider_client(role_project):
    return role_project["clients"]["outsider"]


@pytest.fixture
def resources(owner_client, role_project):
    project_id = role_project["project_id"]
    suite_id = owner_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    case_id = owner_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "TC", "suite_id": suite_id},
    ).json()["id"]
    owner_client.post(f"/api/v1/cases/{case_id}/steps", json={"action": "Login", "order": 1})
    revision_id = owner_client.get(f"/api/v1/cases/{case_id}/revisions").json()[0]["id"]
    case_attachment_id = owner_client.post(
        f"/api/v1/cases/{case_id}/attachments", files={"file": ATTACHMENT},
    ).json()["id"]
    environment_id = owner_client.post(
        f"/api/v1/projects/{project_id}/environments", json={"name": "Staging", "slug": "staging"},
    ).json()["id"]
    execution_id = owner_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual", "test_case_ids": [case_id]},
    ).json()["id"]
    execution_attachment_id = owner_client.post(
        f"/api/v1/executions/{execution_id}/attachments", files={"file": ATTACHMENT},
    ).json()["id"]
    result_id = owner_client.get(f"/api/v1/executions/{execution_id}/results").json()[0]["id"]
    result_attachment_id = owner_client.post(
        f"/api/v1/results/{result_id}/attachments", files={"file": ATTACHMENT},
    ).json()["id"]
    return {
        "suite_id": suite_id,
        "case_id": case_id,
        "revision_id": revision_id,
        "case_attachment_id": case_attachment_id,
        "environment_id": environment_id,
        "execution_id": execution_id,
        "execution_attachment_id": execution_attachment_id,
        "result_id": result_id,
        "result_attachment_id": result_attachment_id,
    }


@pytest.fixture
def outsider_suite_id(outsider_client):
    project_id = outsider_client.post("/api/v1/projects", json={"name": "Mine"}).json()["id"]
    return outsider_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "Loot"},
    ).json()["id"]


@pytest.fixture
def foreign_scoped_token_client(owner_client):
    other_project_id = owner_client.post("/api/v1/projects", json={"name": "Other"}).json()["id"]
    raw_token = owner_client.post(
        f"/api/v1/projects/{other_project_id}/tokens", json={"name": "ci"},
    ).json()["token"]
    client = TestClient(app)
    client.headers["X-API-Key"] = raw_token
    return client


@pytest.mark.parametrize("method,path", ALL_ENDPOINTS)
def test_outsider_is_forbidden(outsider_client, resources, method, path):
    response = _send(outsider_client, method, path, resources)

    assert response.status_code == 403


@pytest.mark.parametrize("method,path", WRITE_ENDPOINTS)
def test_viewer_cannot_write(role_project, resources, method, path):
    viewer = role_project["clients"]["viewer"]

    response = _send(viewer, method, path, resources)

    assert response.status_code == 403


@pytest.mark.parametrize("method,path", ALL_ENDPOINTS)
def test_token_scoped_to_another_project_is_forbidden(
    foreign_scoped_token_client, resources, method, path,
):
    response = _send(foreign_scoped_token_client, method, path, resources)

    assert response.status_code == 403


@pytest.mark.parametrize("method,path", READ_ENDPOINTS)
def test_viewer_can_read(role_project, resources, method, path):
    viewer = role_project["clients"]["viewer"]

    response = _send(viewer, method, path, resources)

    assert response.status_code == 200


@pytest.mark.parametrize("method,path", WRITE_ENDPOINTS)
def test_tester_can_manage_attachments(role_project, resources, method, path):
    tester = role_project["clients"]["tester"]

    response = _send(tester, method, path, resources)

    assert response.status_code in (201, 204)


def test_outsider_cannot_copy_foreign_case_into_own_suite(outsider_client, resources, outsider_suite_id):
    response = outsider_client.post(
        f"/api/v1/cases/{resources['case_id']}/copy", json={"target_suite_id": outsider_suite_id},
    )

    assert response.status_code == 403


def test_outsider_cannot_bulk_copy_foreign_cases_into_own_suite(outsider_client, resources, outsider_suite_id):
    response = outsider_client.post(
        "/api/v1/cases/bulk-copy",
        json={"case_ids": [resources["case_id"]], "target_suite_id": outsider_suite_id},
    )

    assert response.status_code == 403


def test_missing_suite_cases_returns_not_found(owner_client):
    response = owner_client.get("/api/v1/suites/99999/cases")

    assert response.status_code == 404


def _send(client: TestClient, method: str, path: str, resources: dict):
    url = path.format(**resources)
    if method == "POST":
        return client.post(url, files={"file": ATTACHMENT})
    return client.request(method, url)
