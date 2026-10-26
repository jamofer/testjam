import pytest
from sqlalchemy.exc import IntegrityError

from testjam.routers.executions import results as results_module

INTERNAL_ERROR_DETAIL = "duplicate key value violates unique constraint"


@pytest.fixture
def execution_id(auth_client, project_id, case_ids):
    return auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "automatic", "test_case_ids": []},
    ).json()["id"]


@pytest.fixture
def foreign_case_id(auth_client):
    project_id = auth_client.post("/api/v1/projects", json={"name": "Other"}).json()["id"]
    suite_id = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={"name": "S"}).json()["id"]
    return auth_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "Foreign", "suite_id": suite_id},
    ).json()["id"]


@pytest.fixture
def failing_case_id(case_ids, monkeypatch):
    failing_id = case_ids[1]
    original_upsert = results_module._upsert_bulk_item

    def upsert_or_fail(db, execution_id, item):
        result = original_upsert(db, execution_id, item)
        if item.test_case_id == failing_id:
            raise IntegrityError("INSERT", {}, Exception(INTERNAL_ERROR_DETAIL))
        return result

    monkeypatch.setattr(results_module, "_upsert_bulk_item", upsert_or_fail)
    return failing_id


def test_failing_item_does_not_discard_the_rest(auth_client, execution_id, case_ids, failing_case_id):
    response = _bulk(auth_client, execution_id, [(case_id, "passed") for case_id in case_ids])

    assert (response["created"], response["errors"]) == (
        2, [{"test_case_id": failing_case_id, "error": "Could not save result"}],
    )
    assert _saved_case_ids(auth_client, execution_id) == [case_ids[0], case_ids[2]]


def test_failing_item_error_does_not_leak_database_detail(auth_client, execution_id, case_ids, failing_case_id):
    response = _bulk(auth_client, execution_id, [(failing_case_id, "passed")])

    assert INTERNAL_ERROR_DETAIL not in str(response["errors"])


def test_case_from_another_project_is_rejected(auth_client, execution_id, case_ids, foreign_case_id):
    response = _bulk(auth_client, execution_id, [(foreign_case_id, "passed"), (case_ids[0], "passed")])

    assert (response["created"], response["errors"]) == (
        1, [{"test_case_id": foreign_case_id, "error": "Test case not found in this project"}],
    )


def test_unknown_case_is_rejected(auth_client, execution_id):
    response = _bulk(auth_client, execution_id, [(999999, "passed")])

    assert response["errors"] == [{"test_case_id": 999999, "error": "Test case not found in this project"}]


def test_step_from_another_case_is_rejected(auth_client, execution_id, case_ids):
    foreign_step_id = auth_client.post(
        f"/api/v1/cases/{case_ids[1]}/steps", json={"action": "Click", "order": 1},
    ).json()["id"]

    response = auth_client.post(
        f"/api/v1/executions/{execution_id}/results/bulk",
        json={"results": [{
            "test_case_id": case_ids[0], "status": "passed",
            "step_results": [{"step_id": foreign_step_id, "status": "passed"}],
        }]},
    ).json()

    assert response["errors"] == [
        {"test_case_id": case_ids[0], "error": "Step does not belong to this test case"},
    ]


def _bulk(client, execution_id: int, items: list[tuple[int, str]]) -> dict:
    return client.post(
        f"/api/v1/executions/{execution_id}/results/bulk",
        json={"results": [{"test_case_id": case_id, "status": status} for case_id, status in items]},
    ).json()


def _saved_case_ids(client, execution_id: int) -> list[int]:
    return [result["test_case_id"] for result in client.get(f"/api/v1/executions/{execution_id}/results").json()]
