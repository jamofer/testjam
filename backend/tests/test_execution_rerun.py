import pytest

RESULT_STATUSES = ["passed", "failed", "blocked"]


@pytest.fixture
def finished_execution(auth_client, project_id, case_ids):
    execution = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={
            "title": "Nightly",
            "description": "Full regression",
            "type": "manual",
            "environment": "staging",
            "test_case_ids": case_ids,
        },
    ).json()
    results = auth_client.get(f"/api/v1/executions/{execution['id']}/results").json()
    for result, status in zip(results, RESULT_STATUSES, strict=True):
        auth_client.put(f"/api/v1/results/{result['id']}", json={"status": status})
    auth_client.put(f"/api/v1/executions/{execution['id']}", json={"status": "completed"})
    return execution


def test_rerun_creates_a_pending_copy_with_every_case(auth_client, finished_execution, case_ids):
    response = auth_client.post(f"/api/v1/executions/{finished_execution['id']}/rerun", json={})

    assert response.status_code == 201
    rerun = response.json()
    assert rerun["id"] != finished_execution["id"]
    assert rerun["status"] == "pending"
    assert rerun["title"] == "Nightly"
    assert rerun["environment"] == "staging"
    results = auth_client.get(f"/api/v1/executions/{rerun['id']}/results").json()
    assert [result["test_case_id"] for result in results] == case_ids
    assert {result["status"] for result in results} == {"not_run"}


def test_rerun_not_passed_skips_passed_cases(auth_client, finished_execution, case_ids):
    response = auth_client.post(
        f"/api/v1/executions/{finished_execution['id']}/rerun", json={"cases": "not_passed"},
    )

    results = auth_client.get(f"/api/v1/executions/{response.json()['id']}/results").json()
    assert [result["test_case_id"] for result in results] == case_ids[1:]


def test_rerun_leaves_the_source_execution_untouched(auth_client, finished_execution):
    auth_client.post(f"/api/v1/executions/{finished_execution['id']}/rerun", json={})

    source = auth_client.get(f"/api/v1/executions/{finished_execution['id']}").json()
    assert source["status"] == "completed"
    assert source["summary"]["passed"] == 1


def test_rerun_skips_archived_cases(auth_client, finished_execution, case_ids):
    auth_client.post(f"/api/v1/cases/{case_ids[0]}/archive")

    response = auth_client.post(f"/api/v1/executions/{finished_execution['id']}/rerun", json={})

    results = auth_client.get(f"/api/v1/executions/{response.json()['id']}/results").json()
    assert [result["test_case_id"] for result in results] == case_ids[1:]


def test_rerun_rejects_when_no_case_is_left(auth_client, project_id, case_ids):
    execution = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Green", "type": "manual", "test_case_ids": case_ids[:1]},
    ).json()
    result = auth_client.get(f"/api/v1/executions/{execution['id']}/results").json()[0]
    auth_client.put(f"/api/v1/results/{result['id']}", json={"status": "passed"})

    response = auth_client.post(
        f"/api/v1/executions/{execution['id']}/rerun", json={"cases": "not_passed"},
    )

    assert response.status_code == 409


def test_rerun_rejects_unknown_scope(auth_client, finished_execution):
    response = auth_client.post(
        f"/api/v1/executions/{finished_execution['id']}/rerun", json={"cases": "failed_only"},
    )

    assert response.status_code == 422


def test_rerun_returns_404_for_missing_execution(auth_client):
    response = auth_client.post("/api/v1/executions/9999/rerun", json={})

    assert response.status_code == 404


@pytest.mark.parametrize(("role", "expected_status"), [("tester", 201), ("viewer", 403), ("outsider", 403)])
def test_rerun_requires_write_access(role_project, role, expected_status):
    owner = role_project["clients"]["owner"]
    project_id = role_project["project_id"]
    suite_id = owner.post(f"/api/v1/projects/{project_id}/suites", json={"name": "S"}).json()["id"]
    case_id = owner.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "C", "suite_id": suite_id},
    ).json()["id"]
    execution = owner.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual", "test_case_ids": [case_id]},
    ).json()

    response = role_project["clients"][role].post(f"/api/v1/executions/{execution['id']}/rerun", json={})

    assert response.status_code == expected_status
