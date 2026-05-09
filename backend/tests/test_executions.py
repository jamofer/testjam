import pytest
from testjam.auth.security import hash_password
from testjam.models.user import User


@pytest.fixture
def project_with_cases(auth_client):
    project_id = auth_client.post("/api/v1/projects", json={"name": "P"}).json()["id"]
    suite_id = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={"name": "S"}).json()["id"]
    case_ids = []
    for i in range(3):
        case_id = auth_client.post(
            f"/api/v1/suites/{suite_id}/cases", json={"name": f"TC-{i}", "suite_id": suite_id}
        ).json()["id"]
        case_ids.append(case_id)
    return project_id, case_ids


def test_create_manual_execution(auth_client, project_with_cases):
    project_id, case_ids = project_with_cases
    resp = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Sprint 1",
        "type": "manual",
        "version": "1.0.0",
        "environment": "staging",
        "test_case_ids": case_ids,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "manual"
    assert data["status"] == "pending"
    assert data["summary"]["total"] == 3
    assert data["summary"]["not_run"] == 3


def test_register_result(auth_client, project_with_cases):
    project_id, case_ids = project_with_cases
    exec_id = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Run", "type": "manual", "test_case_ids": case_ids,
    }).json()["id"]

    resp = auth_client.post(f"/api/v1/executions/{exec_id}/results", json={
        "test_case_id": case_ids[0],
        "status": "passed",
        "comment": "All good",
    })
    assert resp.status_code == 201
    assert resp.json()["status"] == "passed"

    execution = auth_client.get(f"/api/v1/executions/{exec_id}").json()
    assert execution["summary"]["passed"] == 1


def test_create_execution_with_assignee(auth_client, project_with_cases):
    project_id, case_ids = project_with_cases
    me = auth_client.get("/api/v1/users/me").json()
    resp = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Assigned run", "type": "manual",
        "assigned_to_id": me["id"], "test_case_ids": case_ids,
    })
    assert resp.status_code == 201
    assert resp.json()["assigned_to"]["id"] == me["id"]
    assert resp.json()["assigned_to"]["username"] == "u"


def test_filter_executions_by_assignee(auth_client, project_with_cases):
    from tests.conftest import TestingSession
    project_id, case_ids = project_with_cases
    me = auth_client.get("/api/v1/users/me").json()

    with TestingSession() as db:
        db.add(User(username="other", email="other@x.com",
                    hashed_password=hash_password("pw"), is_active=True))
        db.commit()
        other_id = db.query(User).filter_by(username="other").first().id

    auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Mine", "type": "manual",
        "assigned_to_id": me["id"], "test_case_ids": case_ids,
    })
    auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Theirs", "type": "manual",
        "assigned_to_id": other_id, "test_case_ids": case_ids,
    })
    auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Unassigned", "type": "manual", "test_case_ids": case_ids,
    })

    resp = auth_client.get(f"/api/v1/projects/{project_id}/executions",
                           params={"assigned_to_id": me["id"]}).json()
    assert len(resp) == 1
    assert resp[0]["title"] == "Mine"

    resp = auth_client.get(f"/api/v1/projects/{project_id}/executions",
                           params={"assigned_to_id": other_id}).json()
    assert len(resp) == 1
    assert resp[0]["title"] == "Theirs"


def test_list_executions_pagination(auth_client, project_with_cases):
    project_id, case_ids = project_with_cases
    for i in range(5):
        auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
            "title": f"Run {i}", "type": "manual", "test_case_ids": case_ids,
        })

    page1 = auth_client.get(f"/api/v1/projects/{project_id}/executions",
                            params={"skip": 0, "limit": 3}).json()
    assert len(page1) == 3

    page2 = auth_client.get(f"/api/v1/projects/{project_id}/executions",
                            params={"skip": 3, "limit": 3}).json()
    assert len(page2) == 2

    ids_p1 = {e["id"] for e in page1}
    ids_p2 = {e["id"] for e in page2}
    assert ids_p1.isdisjoint(ids_p2)


def test_list_executions_limit_capped(auth_client, project_with_cases):
    project_id, _ = project_with_cases
    resp = auth_client.get(f"/api/v1/projects/{project_id}/executions",
                           params={"limit": 9999}).json()
    assert isinstance(resp, list)


def test_bulk_results(auth_client, project_with_cases):
    project_id, case_ids = project_with_cases
    exec_id = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "CI Run", "type": "automatic", "triggered_by": "github-actions", "test_case_ids": case_ids,
    }).json()["id"]

    resp = auth_client.post(f"/api/v1/executions/{exec_id}/results/bulk", json={
        "results": [
            {"test_case_id": case_ids[0], "status": "passed"},
            {"test_case_id": case_ids[1], "status": "failed", "comment": "Assertion error"},
            {"test_case_id": case_ids[2], "status": "not_run"},
        ]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] + data["updated"] == 3
    assert data["errors"] == []
