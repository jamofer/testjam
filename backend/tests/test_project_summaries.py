from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import event

from testjam.models.execution import TestExecution
from tests.conftest import TestingSession, engine

EXECUTIONS_PER_PROJECT = 12
RECENT_EXECUTIONS_SHOWN = 10
SMALL_PROJECT_COUNT = 2
LARGE_PROJECT_COUNT = 6
BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.fixture
def seeded_project(auth_client):
    return _seed_project(auth_client, "Alpha", executions=EXECUTIONS_PER_PROJECT)


@pytest.fixture
def other_project(auth_client, seeded_project):
    return _seed_project(auth_client, "Beta", executions=1)


def test_project_list_reports_counts_per_project(auth_client, seeded_project, other_project):
    projects = {project["name"]: project for project in auth_client.get("/api/v1/projects").json()}

    counts = {
        name: (project["suite_count"], project["case_count"], project["execution_count"])
        for name, project in projects.items()
    }
    assert counts == {"Alpha": (1, 2, EXECUTIONS_PER_PROJECT), "Beta": (1, 2, 1)}


def test_project_list_shows_newest_executions_first(auth_client, seeded_project):
    [project] = auth_client.get("/api/v1/projects").json()

    titles = [execution["title"] for execution in project["recent_executions"]]
    assert titles == [f"Alpha run {index}" for index in range(EXECUTIONS_PER_PROJECT - 1, 1, -1)]
    assert len(titles) == RECENT_EXECUTIONS_SHOWN
    assert project["last_execution_at"].startswith("2026-01-01T00:11:00")


def test_project_list_counts_result_statuses_per_execution(auth_client, seeded_project):
    [project] = auth_client.get("/api/v1/projects").json()

    newest = project["recent_executions"][0]
    assert (newest["passed"], newest["failed"], newest["blocked"], newest["not_run"]) == (1, 0, 0, 1)


def test_single_project_read_includes_summary(auth_client, seeded_project):
    response = auth_client.get(f"/api/v1/projects/{seeded_project}")

    assert response.json()["execution_count"] == EXECUTIONS_PER_PROJECT


def test_project_list_query_count_does_not_grow_with_projects(auth_client):
    for index in range(SMALL_PROJECT_COUNT):
        _seed_project(auth_client, f"Small {index}", executions=2)
    small_queries = _count_select_queries(lambda: auth_client.get("/api/v1/projects"))

    for index in range(SMALL_PROJECT_COUNT, LARGE_PROJECT_COUNT):
        _seed_project(auth_client, f"Large {index}", executions=2)
    large_queries = _count_select_queries(lambda: auth_client.get("/api/v1/projects"))

    assert large_queries == small_queries


def _seed_project(client, name: str, executions: int) -> int:
    project_id = client.post("/api/v1/projects", json={"name": name}).json()["id"]
    suite_id = client.post(f"/api/v1/projects/{project_id}/suites", json={"name": "Suite"}).json()["id"]
    case_ids = [
        client.post(f"/api/v1/suites/{suite_id}/cases", json={"name": f"Case {index}", "suite_id": suite_id}).json()["id"]
        for index in range(2)
    ]
    for index in range(executions):
        execution_id = client.post(
            f"/api/v1/projects/{project_id}/executions",
            json={"title": f"{name} run {index}", "type": "manual", "test_case_ids": case_ids},
        ).json()["id"]
        first_result_id = client.get(f"/api/v1/executions/{execution_id}/results").json()[0]["id"]
        client.put(f"/api/v1/results/{first_result_id}", json={"status": "passed"})
        _set_created_at(execution_id, BASE_TIME + timedelta(minutes=index))
    return project_id


def _set_created_at(execution_id: int, created_at: datetime) -> None:
    with TestingSession() as db:
        db.get(TestExecution, execution_id).created_at = created_at
        db.commit()


def _count_select_queries(send_request) -> int:
    counter = {"selects": 0}

    def count_select(_connection, _cursor, statement, _parameters, _context, _executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            counter["selects"] += 1

    event.listen(engine, "before_cursor_execute", count_select)
    try:
        send_request()
    finally:
        event.remove(engine, "before_cursor_execute", count_select)
    return counter["selects"]
