from datetime import datetime, timedelta, timezone

import pytest

from testjam.models.execution import TestExecution, TestResult
from testjam.models.testcase import TestCase, TestSuite
from testjam.models.testplan import TestPlan
from tests.conftest import TestingSession


@pytest.fixture
def project_id(auth_client):
    return auth_client.post("/api/v1/projects", json={"name": "P"}).json()["id"]


def _seed_results(project_id: int, days_ago_to_statuses: dict[int, list[str]]) -> None:
    now = datetime.now(timezone.utc)
    with TestingSession() as db:
        suite = TestSuite(project_id=project_id, name="S")
        db.add(suite)
        db.flush()
        case = TestCase(suite_id=suite.id, name="C")
        db.add(case)
        db.flush()
        for days_ago, statuses in days_ago_to_statuses.items():
            execution = TestExecution(
                project_id=project_id,
                title=f"Run -{days_ago}d",
                type="manual",
                status="completed",
                created_at=now - timedelta(days=days_ago),
                started_at=now - timedelta(days=days_ago, minutes=5),
                finished_at=now - timedelta(days=days_ago),
            )
            db.add(execution)
            db.flush()
            for status in statuses:
                db.add(TestResult(execution_id=execution.id, test_case_id=case.id, status=status))
        db.commit()


def test_dashboard_counts_card_reflects_project_state(auth_client, project_id):
    suite_id = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    auth_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "C", "suite_id": suite_id},
    )
    with TestingSession() as db:
        db.add(TestPlan(project_id=project_id, title="Plan"))
        db.add(TestExecution(
            project_id=project_id, title="In flight", type="manual", status="in_progress",
        ))
        db.commit()

    body = auth_client.get(f"/api/v1/projects/{project_id}/dashboard").json()

    counts = body["counts"]
    assert counts["suites"] == 1
    assert counts["cases"] == 1
    assert counts["plans"] == 1
    assert counts["executions_in_flight"] == 1


def test_dashboard_pass_rate_computes_overall(auth_client, project_id):
    _seed_results(project_id, {1: ["passed", "passed", "failed"]})

    body = auth_client.get(f"/api/v1/projects/{project_id}/dashboard").json()

    pass_rate = body["pass_rate"]
    assert pass_rate["overall_pass_rate"] == pytest.approx(2 / 3, rel=1e-3)
    assert pass_rate["total_results"] == 3
    assert len(pass_rate["series"]) == 1


def test_dashboard_top_fail_orders_by_failure_count(auth_client, project_id):
    suite_id = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    case_a = auth_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "Alpha", "suite_id": suite_id},
    ).json()["id"]
    case_b = auth_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "Bravo", "suite_id": suite_id},
    ).json()["id"]
    now = datetime.now(timezone.utc)
    with TestingSession() as db:
        execution = TestExecution(
            project_id=project_id, title="run", type="manual", status="completed",
            created_at=now - timedelta(hours=1),
        )
        db.add(execution)
        db.flush()
        db.add(TestResult(execution_id=execution.id, test_case_id=case_a, status="failed"))
        db.add(TestResult(execution_id=execution.id, test_case_id=case_a, status="failed"))
        db.add(TestResult(execution_id=execution.id, test_case_id=case_b, status="failed"))
        db.commit()

    body = auth_client.get(f"/api/v1/projects/{project_id}/dashboard").json()

    top = body["top_fail"]["cases"]
    assert [row["case_name"] for row in top] == ["Alpha", "Bravo"]
    assert top[0]["fail_count"] == 2


def test_dashboard_recent_executions_limit_and_counts(auth_client, project_id):
    _seed_results(project_id, {
        1: ["passed", "failed"],
        2: ["passed"],
        3: ["passed"],
        4: ["passed"],
        5: ["passed"],
        6: ["passed"],
    })

    body = auth_client.get(f"/api/v1/projects/{project_id}/dashboard").json()

    items = body["recent_executions"]["executions"]
    assert len(items) == 5
    most_recent = items[0]
    assert most_recent["passed"] == 1
    assert most_recent["failed"] == 1
    assert most_recent["duration_ms"] is not None


def test_dashboard_rejects_invalid_range(auth_client, project_id):
    resp = auth_client.get(f"/api/v1/projects/{project_id}/dashboard?range=42")

    assert resp.status_code == 400


def test_dashboard_cards_filter_returns_only_requested(auth_client, project_id):
    body = auth_client.get(
        f"/api/v1/projects/{project_id}/dashboard?cards=counts",
    ).json()

    assert body["counts"] is not None
    assert body["pass_rate"] is None
    assert body["top_fail"] is None
    assert body["recent_executions"] is None


def test_dashboard_rejects_unknown_card_name(auth_client, project_id):
    resp = auth_client.get(
        f"/api/v1/projects/{project_id}/dashboard?cards=unicorn",
    )

    assert resp.status_code == 400
