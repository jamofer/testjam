"""WS broadcasts for project lifecycle events."""
from __future__ import annotations

from collections.abc import Iterable

from testjam.realtime import notify_bug, notify_execution, notify_project


def on_project_deleted(
    project_id: int,
    name: str,
    execution_ids: Iterable[int] = (),
    bug_ids: Iterable[int] = (),
) -> None:
    """Tell project pages and every open execution or bug page that it is gone."""
    notify_project(
        project_id,
        {
            "event": "project.deleted",
            "data": {"id": project_id, "name": name},
        },
    )
    for execution_id in execution_ids:
        notify_execution(
            execution_id,
            {"event": "execution.deleted", "data": {"id": execution_id, "project_id": project_id}},
        )
    for bug_id in bug_ids:
        notify_bug(bug_id, {"event": "bug.deleted", "data": {"id": bug_id}})
