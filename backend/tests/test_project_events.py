"""project_events service — lifecycle hooks dispatching WS."""
from __future__ import annotations

from testjam.services import project_events


def test_on_project_deleted_broadcasts_project_topic(monkeypatch):
    pushed: list = []
    monkeypatch.setattr(
        project_events,
        "notify_project",
        lambda project_id, payload: pushed.append((project_id, payload)),
    )

    project_events.on_project_deleted(7, "Acme")

    assert pushed == [(7, {
        "event": "project.deleted",
        "data": {"id": 7, "name": "Acme"},
    })]


def test_delete_project_endpoint_emits_event(auth_client, monkeypatch):
    from testjam.routers import projects as projects_router

    pushed: list = []
    monkeypatch.setattr(
        projects_router,
        "on_project_deleted",
        lambda project_id, name, execution_ids, bug_ids: pushed.append((project_id, name)),
    )

    project_id = auth_client.post("/api/v1/projects", json={"name": "ToDelete"}).json()["id"]
    resp = auth_client.delete(f"/api/v1/projects/{project_id}")
    assert resp.status_code == 204

    assert pushed == [(project_id, "ToDelete")]


def test_on_project_deleted_tells_open_execution_and_bug_pages(monkeypatch):
    pushed: list = []
    monkeypatch.setattr(project_events, "notify_project", lambda project_id, payload: None)
    monkeypatch.setattr(
        project_events, "notify_execution",
        lambda execution_id, payload: pushed.append(("execution", execution_id, payload["event"])),
    )
    monkeypatch.setattr(
        project_events, "notify_bug",
        lambda bug_id, payload: pushed.append(("bug", bug_id, payload["event"])),
    )

    project_events.on_project_deleted(7, "Acme", execution_ids=[11, 12], bug_ids=[21])

    assert pushed == [
        ("execution", 11, "execution.deleted"),
        ("execution", 12, "execution.deleted"),
        ("bug", 21, "bug.deleted"),
    ]


def test_delete_project_endpoint_reports_its_executions_and_bugs(auth_client, project_id, case_ids, monkeypatch):
    from testjam.routers import projects as projects_router

    reported: dict = {}
    monkeypatch.setattr(
        projects_router,
        "on_project_deleted",
        lambda project_id, name, execution_ids, bug_ids: reported.update(executions=execution_ids, bugs=bug_ids),
    )
    execution_id = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual", "test_case_ids": case_ids},
    ).json()["id"]
    bug_id = auth_client.post(f"/api/v1/projects/{project_id}/bugs", json={"title": "Crash"}).json()["id"]

    auth_client.delete(f"/api/v1/projects/{project_id}")

    assert reported == {"executions": [execution_id], "bugs": [bug_id]}
