def _create_version(auth_client, project_id, name, status="active"):
    return auth_client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"name": name, "status": status},
    ).json()["id"]


def _create_execution_with_result(auth_client, project_id, case_ids, version_id, statuses):
    execution_id = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={
            "title": f"Run for v{version_id}",
            "type": "manual",
            "version_id": version_id,
            "test_case_ids": case_ids,
        },
    ).json()["id"]
    for case_id, status in zip(case_ids, statuses):
        auth_client.post(
            f"/api/v1/executions/{execution_id}/results",
            json={"test_case_id": case_id, "status": status},
        )
    return execution_id


def test_coverage_matrix_empty(auth_client, project_id):
    resp = auth_client.get(f"/api/v1/projects/{project_id}/coverage/matrix")

    assert resp.status_code == 200
    body = resp.json()
    assert body == {"versions": [], "cases": [], "cells": []}


def test_coverage_matrix_returns_last_status_per_case_version(auth_client, project_id, case_ids):
    v1 = _create_version(auth_client, project_id, "v1.0")
    v2 = _create_version(auth_client, project_id, "v2.0")
    _create_execution_with_result(auth_client, project_id, case_ids, v1, ["passed", "failed", "blocked"])
    _create_execution_with_result(auth_client, project_id, case_ids, v2, ["passed", "passed", "passed"])

    body = auth_client.get(f"/api/v1/projects/{project_id}/coverage/matrix").json()

    assert len(body["versions"]) == 2
    assert len(body["cases"]) == 3
    assert len(body["cells"]) == 6
    cells_by_key = {(c["case_id"], c["version_id"]): c["status"] for c in body["cells"]}
    assert cells_by_key[(case_ids[0], v1)] == "passed"
    assert cells_by_key[(case_ids[1], v1)] == "failed"
    assert cells_by_key[(case_ids[2], v1)] == "blocked"
    assert all(cells_by_key[(c, v2)] == "passed" for c in case_ids)


def test_coverage_matrix_picks_latest_run_when_multiple(auth_client, project_id, case_ids):
    v1 = _create_version(auth_client, project_id, "v1.0")
    _create_execution_with_result(auth_client, project_id, [case_ids[0]], v1, ["failed"])
    _create_execution_with_result(auth_client, project_id, [case_ids[0]], v1, ["passed"])

    body = auth_client.get(f"/api/v1/projects/{project_id}/coverage/matrix").json()

    cells = [c for c in body["cells"] if c["case_id"] == case_ids[0] and c["version_id"] == v1]
    assert len(cells) == 1
    assert cells[0]["status"] == "passed"


def test_coverage_matrix_excludes_archived_versions_by_default(auth_client, project_id, case_ids):
    active_id = _create_version(auth_client, project_id, "active-v")
    archived_id = _create_version(auth_client, project_id, "old-v", status="archived")
    _create_execution_with_result(auth_client, project_id, case_ids, active_id, ["passed"] * 3)
    _create_execution_with_result(auth_client, project_id, case_ids, archived_id, ["failed"] * 3)

    default_body = auth_client.get(f"/api/v1/projects/{project_id}/coverage/matrix").json()
    all_body = auth_client.get(f"/api/v1/projects/{project_id}/coverage/matrix", params={"include_archived": True}).json()

    assert [v["id"] for v in default_body["versions"]] == [active_id]
    assert {v["id"] for v in all_body["versions"]} == {active_id, archived_id}


def test_dashboard_versions_card(auth_client, project_id, case_ids):
    v1 = _create_version(auth_client, project_id, "v1.0")
    _create_version(auth_client, project_id, "ancient", status="archived")
    _create_execution_with_result(auth_client, project_id, case_ids, v1, ["passed", "passed", "failed"])

    body = auth_client.get(f"/api/v1/projects/{project_id}/dashboard", params={"cards": "versions"}).json()

    assert "versions" in body
    items = body["versions"]["items"]
    assert len(items) == 1
    item = items[0]
    assert item["id"] == v1
    assert item["total_runs"] == 1
    assert item["last_run_status"] == "pending"
    assert item["pass_rate"] == 2 / 3
