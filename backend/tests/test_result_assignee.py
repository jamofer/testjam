import pytest

from testjam.models.user import User
from tests.conftest import TestingSession


@pytest.fixture
def project_results(role_project):
    owner = role_project["clients"]["owner"]
    project_id = role_project["project_id"]
    suite_id = owner.post(f"/api/v1/projects/{project_id}/suites", json={"name": "S"}).json()["id"]
    case_ids = [
        owner.post(f"/api/v1/suites/{suite_id}/cases", json={"name": name, "suite_id": suite_id}).json()["id"]
        for name in ("Login", "Logout")
    ]
    execution = owner.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual", "test_case_ids": case_ids},
    ).json()
    results = owner.get(f"/api/v1/executions/{execution['id']}/results").json()
    return {"owner": owner, "execution": execution, "results": results}


@pytest.fixture
def user_ids():
    with TestingSession() as db:
        return {user.username: user.id for user in db.query(User).all()}


def test_assign_result_to_project_member(project_results, user_ids):
    owner = project_results["owner"]
    result_id = project_results["results"][0]["id"]

    response = owner.put(f"/api/v1/results/{result_id}", json={"assigned_to_id": user_ids["matrix_tester"]})

    assert response.status_code == 200
    assert response.json()["assigned_to_id"] == user_ids["matrix_tester"]


def test_unassign_result_with_null(project_results, user_ids):
    owner = project_results["owner"]
    result_id = project_results["results"][0]["id"]
    owner.put(f"/api/v1/results/{result_id}", json={"assigned_to_id": user_ids["matrix_tester"]})

    response = owner.put(f"/api/v1/results/{result_id}", json={"assigned_to_id": None})

    assert response.json()["assigned_to_id"] is None


def test_status_update_keeps_the_assignee(project_results, user_ids):
    owner = project_results["owner"]
    result_id = project_results["results"][0]["id"]
    owner.put(f"/api/v1/results/{result_id}", json={"assigned_to_id": user_ids["matrix_tester"]})

    response = owner.put(f"/api/v1/results/{result_id}", json={"status": "passed"})

    assert response.json()["assigned_to_id"] == user_ids["matrix_tester"]


def test_assign_rejects_users_outside_the_project(project_results, user_ids):
    owner = project_results["owner"]
    result_id = project_results["results"][0]["id"]

    response = owner.put(f"/api/v1/results/{result_id}", json={"assigned_to_id": user_ids["matrix_outsider"]})

    assert response.status_code == 422


def test_assign_rejects_unknown_users(project_results):
    owner = project_results["owner"]
    result_id = project_results["results"][0]["id"]

    response = owner.put(f"/api/v1/results/{result_id}", json={"assigned_to_id": 9999})

    assert response.status_code == 422


def test_list_results_filters_by_assignee(project_results, user_ids):
    owner = project_results["owner"]
    first, second = project_results["results"]
    owner.put(f"/api/v1/results/{first['id']}", json={"assigned_to_id": user_ids["matrix_tester"]})

    response = owner.get(
        f"/api/v1/executions/{project_results['execution']['id']}/results",
        params={"assigned_to_id": user_ids["matrix_tester"]},
    )

    assert [result["id"] for result in response.json()] == [first["id"]]


def test_rerun_keeps_each_result_assignee(project_results, user_ids):
    owner = project_results["owner"]
    first, second = project_results["results"]
    owner.put(f"/api/v1/results/{first['id']}", json={"assigned_to_id": user_ids["matrix_tester"]})

    rerun = owner.post(f"/api/v1/executions/{project_results['execution']['id']}/rerun", json={}).json()

    results = owner.get(f"/api/v1/executions/{rerun['id']}/results").json()
    assert [result["assigned_to_id"] for result in results] == [user_ids["matrix_tester"], None]
