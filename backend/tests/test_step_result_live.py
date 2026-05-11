"""Live step-result endpoints: running state + log streaming."""
from __future__ import annotations

import pytest

from testjam.services import execution_events


@pytest.fixture(autouse=True)
def stub_websocket_broadcasts(monkeypatch):
    monkeypatch.setattr(execution_events, "notify_project", lambda *a, **kw: None)
    monkeypatch.setattr(execution_events, "notify_execution", lambda *a, **kw: None)
    monkeypatch.setattr(execution_events, "schedule_log_append", lambda *a, **kw: None)


def test_start_step_result_persists_running_state(auth_client, execution_with_step):
    _, result_id, step_id = execution_with_step

    response = auth_client.post(
        f"/api/v1/results/{result_id}/step-results", json={"step_id": step_id},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "running"
    assert body["step_id"] == step_id
    assert body["started_at"] is not None


def test_start_step_result_is_idempotent_on_same_step(auth_client, execution_with_step):
    _, result_id, step_id = execution_with_step

    first = auth_client.post(
        f"/api/v1/results/{result_id}/step-results", json={"step_id": step_id},
    ).json()
    second = auth_client.post(
        f"/api/v1/results/{result_id}/step-results", json={"step_id": step_id},
    ).json()

    assert second["id"] == first["id"]
    assert second["status"] == "running"


def test_start_step_result_404_for_missing_result(auth_client):
    response = auth_client.post(
        "/api/v1/results/99999/step-results", json={"step_id": 1},
    )
    assert response.status_code == 404


def test_log_append_creates_first_entry(auth_client, execution_with_step):
    _, result_id, step_id = execution_with_step
    step_result_id = auth_client.post(
        f"/api/v1/results/{result_id}/step-results", json={"step_id": step_id},
    ).json()["id"]

    response = auth_client.post(
        f"/api/v1/results/{result_id}/step-results/{step_result_id}/log",
        json={"level": "INFO", "message": "logging in"},
    )

    assert response.status_code == 200
    assert response.json() == {"step_result_id": step_result_id, "appended": 1}

    step_result = next(
        sr for sr in auth_client.get(
            f"/api/v1/executions/{execution_with_step[0]}/results",
        ).json()[0]["step_results"]
        if sr["id"] == step_result_id
    )
    assert step_result["log_output"] == "**[INFO]** logging in"


def test_log_append_concatenates_entries_with_separator(auth_client, execution_with_step):
    execution_id, result_id, step_id = execution_with_step
    step_result_id = auth_client.post(
        f"/api/v1/results/{result_id}/step-results", json={"step_id": step_id},
    ).json()["id"]

    auth_client.post(
        f"/api/v1/results/{result_id}/step-results/{step_result_id}/log",
        json={"level": "INFO", "message": "first"},
    )
    auth_client.post(
        f"/api/v1/results/{result_id}/step-results/{step_result_id}/log",
        json={"level": "WARN", "message": "second"},
    )

    step_result = next(
        sr for sr in auth_client.get(
            f"/api/v1/executions/{execution_id}/results",
        ).json()[0]["step_results"]
        if sr["id"] == step_result_id
    )
    assert step_result["log_output"] == "**[INFO]** first\n\n**[WARN]** second"


def test_log_append_404_for_missing_step_result(auth_client, execution_with_step):
    _, result_id, _ = execution_with_step

    response = auth_client.post(
        f"/api/v1/results/{result_id}/step-results/99999/log",
        json={"level": "INFO", "message": "hi"},
    )

    assert response.status_code == 404


def test_log_append_schedules_a_buffered_broadcast(monkeypatch, auth_client, execution_with_step):
    execution_id, result_id, step_id = execution_with_step
    step_result_id = auth_client.post(
        f"/api/v1/results/{result_id}/step-results", json={"step_id": step_id},
    ).json()["id"]
    captured: list = []
    monkeypatch.setattr(
        execution_events,
        "schedule_log_append",
        lambda topic_execution_id, payload: captured.append((topic_execution_id, payload)),
    )

    auth_client.post(
        f"/api/v1/results/{result_id}/step-results/{step_result_id}/log",
        json={"level": "FAIL", "message": "boom", "ts": "2026-05-11T19:00:00+00:00"},
    )

    assert captured == [(execution_id, {
        "step_result_id": step_result_id,
        "level": "FAIL",
        "message": "boom",
        "ts": "2026-05-11T19:00:00+00:00",
    })]


def test_step_result_accepts_running_status_via_update(auth_client, execution_with_step):
    _, result_id, step_id = execution_with_step
    step_result_id = auth_client.post(
        f"/api/v1/results/{result_id}/step-results", json={"step_id": step_id},
    ).json()["id"]

    response = auth_client.put(
        f"/api/v1/results/{result_id}/step-results/{step_result_id}",
        json={"status": "running"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "running"
