import pytest


@pytest.fixture
def executed_step(auth_client, execution_with_step):
    execution_id, result_id, step_id = execution_with_step
    auth_client.post(
        f"/api/v1/executions/{execution_id}/results",
        json={
            "test_case_id": _case_id(auth_client, result_id),
            "status": "passed",
            "step_results": [{"step_id": step_id, "status": "passed"}],
        },
    )
    return execution_id, result_id, step_id


def test_result_keeps_case_title_after_case_is_renamed(auth_client, executed_step):
    _, result_id, _ = executed_step

    auth_client.put(f"/api/v1/cases/{_case_id(auth_client, result_id)}", json={"name": "Renamed"})

    result = auth_client.get(f"/api/v1/results/{result_id}").json()
    assert result["test_case_title"] == "TC"


def test_result_survives_case_deletion(auth_client, executed_step):
    execution_id, result_id, _ = executed_step

    auth_client.delete(f"/api/v1/cases/{_case_id(auth_client, result_id)}")

    results = auth_client.get(f"/api/v1/executions/{execution_id}/results").json()
    assert [(result["id"], result["test_case_title"], result["status"]) for result in results] == [
        (result_id, "TC", "passed"),
    ]


def test_step_result_keeps_step_text_after_step_is_edited(auth_client, executed_step):
    _, result_id, step_id = executed_step
    case_id = _case_id(auth_client, result_id)

    auth_client.put(
        f"/api/v1/cases/{case_id}/steps/{step_id}",
        json={"action": "Logout", "expected_result": "Signed out", "order": 1},
    )

    step_result = auth_client.get(f"/api/v1/results/{result_id}").json()["step_results"][0]
    assert (step_result["step_action"], step_result["step_expected_result"]) == ("Login", None)


def test_step_result_survives_step_deletion(auth_client, executed_step):
    _, result_id, step_id = executed_step

    auth_client.delete(f"/api/v1/cases/{_case_id(auth_client, result_id)}/steps/{step_id}")

    step_results = auth_client.get(f"/api/v1/results/{result_id}").json()["step_results"]
    assert [(step_result["step_action"], step_result["status"]) for step_result in step_results] == [
        ("Login", "passed"),
    ]


def _case_id(client, result_id: int) -> int:
    return client.get(f"/api/v1/results/{result_id}").json()["test_case_id"]
