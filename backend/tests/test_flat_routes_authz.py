import pytest
from fastapi.testclient import TestClient

from testjam.main import app

READ_ENDPOINTS = [
    ("GET", "/api/v1/versions/{version_id}", None),
    ("GET", "/api/v1/executions/{execution_id}", None),
    ("GET", "/api/v1/executions/{execution_id}/results", None),
    ("GET", "/api/v1/results/{result_id}", None),
]

WRITE_ENDPOINTS = [
    ("PUT", "/api/v1/versions/{version_id}", {"description": "changed"}),
    ("DELETE", "/api/v1/versions/{version_id}", None),
    ("PUT", "/api/v1/executions/{execution_id}", {"title": "changed"}),
    ("DELETE", "/api/v1/executions/{execution_id}", None),
    ("POST", "/api/v1/executions/{execution_id}/results", {"test_case_id": "{case_id}", "status": "passed"}),
    ("POST", "/api/v1/executions/{execution_id}/results/bulk", {"results": [{"test_case_id": "{case_id}", "status": "passed"}]}),
    ("PUT", "/api/v1/results/{result_id}", {"status": "passed"}),
    ("POST", "/api/v1/results/{result_id}/step-results", {"step_id": "{step_id}"}),
    ("PUT", "/api/v1/results/{result_id}/step-results/{step_result_id}", {"status": "passed"}),
    ("POST", "/api/v1/results/{result_id}/step-results/{step_result_id}/log", {"level": "INFO", "message": "hi"}),
    ("POST", "/api/v1/executions/{execution_id}/results/import/junit", "file"),
    ("POST", "/api/v1/executions/{execution_id}/results/import/robotframework", "file"),
]

ALL_ENDPOINTS = READ_ENDPOINTS + WRITE_ENDPOINTS


@pytest.fixture
def owner_client(role_project):
    return role_project["clients"]["owner"]


@pytest.fixture
def resources(owner_client, role_project):
    project_id = role_project["project_id"]
    version_id = owner_client.post(
        f"/api/v1/projects/{project_id}/versions", json={"name": "1.0"},
    ).json()["id"]
    suite_id = owner_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    case_id = owner_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "TC", "suite_id": suite_id},
    ).json()["id"]
    step_id = owner_client.post(
        f"/api/v1/cases/{case_id}/steps", json={"action": "Login", "order": 1},
    ).json()["id"]
    execution_id = owner_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual", "test_case_ids": [case_id]},
    ).json()["id"]
    result_id = owner_client.get(f"/api/v1/executions/{execution_id}/results").json()[0]["id"]
    step_result_id = owner_client.post(
        f"/api/v1/results/{result_id}/step-results", json={"step_id": step_id},
    ).json()["id"]
    return {
        "version_id": version_id,
        "case_id": case_id,
        "step_id": step_id,
        "execution_id": execution_id,
        "result_id": result_id,
        "step_result_id": step_result_id,
    }


@pytest.fixture
def foreign_scoped_token_client(owner_client):
    other_project_id = owner_client.post("/api/v1/projects", json={"name": "Other"}).json()["id"]
    raw_token = owner_client.post(
        f"/api/v1/projects/{other_project_id}/tokens", json={"name": "ci"},
    ).json()["token"]
    client = TestClient(app)
    client.headers["X-API-Key"] = raw_token
    return client


@pytest.mark.parametrize("method,path,payload", ALL_ENDPOINTS)
def test_outsider_is_forbidden(role_project, resources, method, path, payload):
    outsider = role_project["clients"]["outsider"]

    response = _send(outsider, method, path, payload, resources)

    assert response.status_code == 403


@pytest.mark.parametrize("method,path,payload", WRITE_ENDPOINTS)
def test_viewer_cannot_write(role_project, resources, method, path, payload):
    viewer = role_project["clients"]["viewer"]

    response = _send(viewer, method, path, payload, resources)

    assert response.status_code == 403


@pytest.mark.parametrize("method,path,payload", ALL_ENDPOINTS)
def test_token_scoped_to_another_project_is_forbidden(
    foreign_scoped_token_client, resources, method, path, payload,
):
    response = _send(foreign_scoped_token_client, method, path, payload, resources)

    assert response.status_code == 403


@pytest.mark.parametrize("method,path,payload", READ_ENDPOINTS)
def test_viewer_can_read(role_project, resources, method, path, payload):
    viewer = role_project["clients"]["viewer"]

    response = _send(viewer, method, path, payload, resources)

    assert response.status_code == 200


def test_tester_can_record_result(role_project, resources):
    tester = role_project["clients"]["tester"]

    response = tester.put(f"/api/v1/results/{resources['result_id']}", json={"status": "failed"})

    assert response.status_code == 200
    assert response.json()["status"] == "failed"


def test_tester_can_update_version(role_project, resources):
    tester = role_project["clients"]["tester"]

    response = tester.put(f"/api/v1/versions/{resources['version_id']}", json={"description": "notes"})

    assert response.status_code == 200


def test_missing_execution_returns_not_found(owner_client):
    response = owner_client.get("/api/v1/executions/99999/results")

    assert response.status_code == 404


def _send(client: TestClient, method: str, path: str, payload, resources: dict):
    url = path.format(**resources)
    if payload == "file":
        return client.request(method, url, files={"file": ("report.xml", b"<testsuite/>", "text/xml")})
    if payload is None:
        return client.request(method, url)
    return client.request(method, url, json=_fill(payload, resources))


def _fill(value, resources: dict):
    if isinstance(value, dict):
        return {key: _fill(item, resources) for key, item in value.items()}
    if isinstance(value, list):
        return [_fill(item, resources) for item in value]
    if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
        return resources[value[1:-1]]
    return value
