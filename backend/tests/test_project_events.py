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
        lambda project_id, name: pushed.append((project_id, name)),
    )

    project_id = auth_client.post("/api/v1/projects", json={"name": "ToDelete"}).json()["id"]
    resp = auth_client.delete(f"/api/v1/projects/{project_id}")
    assert resp.status_code == 204

    assert pushed == [(project_id, "ToDelete")]
