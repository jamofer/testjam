"""POST /results/{id}/report-external — creates a Bug and optionally pushes it."""
import pytest

from testjam.services.integrations.providers.fake import instance as fake_provider


@pytest.fixture(autouse=True)
def _reset_fake():
    fake_provider().reset()
    yield
    fake_provider().reset()


def _seed_result(auth_client, project_id):
    suite_id = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    case_id = auth_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "TC", "suite_id": suite_id},
    ).json()["id"]
    execution_id = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Smoke", "type": "manual", "test_case_ids": [case_id]},
    ).json()["id"]
    result_id = auth_client.get(
        f"/api/v1/executions/{execution_id}/results",
    ).json()[0]["id"]
    return result_id


def _seed_integration(auth_client, project_id, *, name="Primary"):
    return auth_client.post(
        f"/api/v1/projects/{project_id}/integrations",
        json={
            "provider": "fake",
            "name": name,
            "config": {"project_key": "DEMO"},
            "secret": "tok",
        },
    ).json()["id"]


def test_report_creates_bug_pre_populated_from_result(auth_client, project_id):
    result_id = _seed_result(auth_client, project_id)

    resp = auth_client.post(
        f"/api/v1/results/{result_id}/report-external",
        json={"title": "Crash on login", "description": "stack…", "severity": "high"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["bug_number"] >= 1
    assert body["external_link"] is None
    bug = auth_client.get(f"/api/v1/bugs/{body['bug_id']}").json()
    assert bug["title"] == "Crash on login"
    assert bug["severity"] == "high"
    assert bug["result_id"] == result_id
    assert bug["execution_id"] is not None


def test_report_with_integration_pushes_to_provider(auth_client, project_id):
    result_id = _seed_result(auth_client, project_id)
    integration_id = _seed_integration(auth_client, project_id)

    resp = auth_client.post(
        f"/api/v1/results/{result_id}/report-external",
        json={
            "title": "Login flake",
            "integration_id": integration_id,
            "labels": ["flaky"],
        },
    )

    assert resp.status_code == 201
    link = resp.json()["external_link"]
    assert link is not None
    assert link["provider"] == "fake"
    assert link["external_id"].startswith("DEMO-")
    assert link["status_normalized"] == "open"


def test_report_unknown_result_returns_404(auth_client):
    resp = auth_client.post(
        "/api/v1/results/99999/report-external", json={"title": "x"},
    )

    assert resp.status_code == 404


def test_report_rejects_integration_from_other_project(auth_client, project_id):
    result_id = _seed_result(auth_client, project_id)
    other_project_id = auth_client.post(
        "/api/v1/projects", json={"name": "Other"},
    ).json()["id"]
    other_integration_id = _seed_integration(auth_client, other_project_id, name="Foreign")

    resp = auth_client.post(
        f"/api/v1/results/{result_id}/report-external",
        json={"title": "x", "integration_id": other_integration_id},
    )

    assert resp.status_code == 400
