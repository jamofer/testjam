"""WS broadcasts for project lifecycle events."""
from __future__ import annotations

from testjam.realtime import notify_project


def on_project_deleted(project_id: int, name: str) -> None:
    notify_project(
        project_id,
        {
            "event": "project.deleted",
            "data": {"id": project_id, "name": name},
        },
    )
