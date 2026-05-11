"""Single dispatch point for execution-lifecycle events.

Each ``on_execution_*`` helper is invoked by a CRUD/result/import handler after
it has mutated the relevant rows. The hook then:

1. Broadcasts the matching WebSocket payload (``project:{id}`` for execution
   lifecycle, ``execution:{id}`` for result/step-result updates).
2. For ``execution_assigned`` / ``execution_finished`` / ``execution_failed``,
   schedules per-user in-app + email notifications through
   ``services.notifications.notify``.

The handlers commit the session; this module never commits. Notification rows
created via ``notify`` are flushed but their commit rides on the caller's.
"""
from __future__ import annotations

from typing import Any

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from testjam.models.execution import TestExecution
from testjam.models.user import User
from testjam.realtime import notify_execution, notify_project
from testjam.routers.executions._helpers import (
    compute_summary,
    execution_out,
    load_execution_full,
)
from testjam.services import email_templates
from testjam.services.log_flusher import schedule_append as schedule_log_append
from testjam.services.notification_events import NotificationEvent
from testjam.services.notifications import notify
from testjam.services.settings import get_settings as get_app_settings

EXECUTION_COMPLETED_STATUS = "completed"


def _build_public_link(site_url: str | None, path: str) -> str:
    if not site_url:
        return path
    return f"{site_url.rstrip('/')}{path}"


def _execution_payload(execution: TestExecution) -> dict[str, Any]:
    return execution_out(execution).model_dump(mode="json")


def _broadcast_project(event: str, execution: TestExecution) -> None:
    notify_project(
        execution.project_id,
        {"event": event, "data": _execution_payload(execution)},
    )


def _resolve_recipients(execution: TestExecution) -> list[int]:
    recipients: list[int] = []
    if execution.created_by_id:
        recipients.append(execution.created_by_id)
    if (
        execution.assigned_to_id
        and execution.assigned_to_id != execution.created_by_id
    ):
        recipients.append(execution.assigned_to_id)
    return recipients


def _completion_context(
    db: Session, execution: TestExecution, summary,
) -> dict[str, Any]:
    settings_row = get_app_settings(db)
    in_app_link = f"/executions/{execution.id}"
    public_link = _build_public_link(settings_row.site_url, in_app_link)
    return {
        "app_name": settings_row.app_name,
        "site_url": settings_row.site_url,
        "subject_object": execution.title,
        "link_in_app": public_link,
        "summary": summary.model_dump(),
    }


def _send_assignment_email(
    db: Session,
    execution: TestExecution,
    assignee_id: int,
    actor: User,
    background: BackgroundTasks | None,
) -> None:
    if assignee_id == actor.id:
        return
    settings_row = get_app_settings(db)
    in_app_link = f"/executions/{execution.id}/run"
    public_link = _build_public_link(settings_row.site_url, in_app_link)
    subject, html, text = email_templates.render(
        NotificationEvent.EXECUTION_ASSIGNED.value,
        {
            "app_name": settings_row.app_name,
            "site_url": settings_row.site_url,
            "actor": actor.username,
            "subject_object": execution.title,
            "link_in_app": public_link,
        },
    )
    notify(
        db,
        assignee_id,
        NotificationEvent.EXECUTION_ASSIGNED,
        message=f"{actor.username} assigned you to '{execution.title}'",
        link=in_app_link,
        email_subject=subject,
        email_html=html,
        email_text=text,
        background=background,
    )


def _send_finished_email(
    db: Session,
    user_id: int,
    execution: TestExecution,
    context: dict[str, Any],
    background: BackgroundTasks | None,
) -> None:
    subject, html, text = email_templates.render(
        NotificationEvent.EXECUTION_FINISHED.value, context,
    )
    notify(
        db,
        user_id,
        NotificationEvent.EXECUTION_FINISHED,
        message=f"Execution '{execution.title}' finished",
        link=f"/executions/{execution.id}",
        email_subject=subject,
        email_html=html,
        email_text=text,
        background=background,
    )


def _send_failed_email(
    db: Session,
    user_id: int,
    execution: TestExecution,
    context: dict[str, Any],
    background: BackgroundTasks | None,
) -> None:
    subject, html, text = email_templates.render(
        NotificationEvent.EXECUTION_FAILED.value, context,
    )
    notify(
        db,
        user_id,
        NotificationEvent.EXECUTION_FAILED,
        message=f"Failed tests in '{execution.title}'",
        link=f"/executions/{execution.id}",
        email_subject=subject,
        email_html=html,
        email_text=text,
        background=background,
    )


def on_execution_assigned(
    db: Session,
    execution: TestExecution,
    assignee_id: int,
    actor: User,
    background: BackgroundTasks | None = None,
) -> None:
    _send_assignment_email(db, execution, assignee_id, actor, background)


def on_execution_created(
    db: Session,
    execution: TestExecution,
    actor: User,
    background: BackgroundTasks | None = None,
) -> None:
    full = load_execution_full(db, execution.id) or execution
    _broadcast_project("execution.created", full)
    if full.assigned_to_id:
        _send_assignment_email(db, full, full.assigned_to_id, actor, background)


def on_execution_updated(
    db: Session,
    execution: TestExecution,
    actor: User,
    background: BackgroundTasks | None = None,
    *,
    previous_status: str | None,
    previous_assignee_id: int | None,
) -> None:
    full = load_execution_full(db, execution.id) or execution
    _broadcast_project("execution.updated", full)
    if (
        full.assigned_to_id
        and full.assigned_to_id != previous_assignee_id
    ):
        _send_assignment_email(db, full, full.assigned_to_id, actor, background)
    if (
        previous_status != EXECUTION_COMPLETED_STATUS
        and full.status == EXECUTION_COMPLETED_STATUS
    ):
        on_execution_completed(db, full, background)


def on_execution_completed(
    db: Session,
    execution: TestExecution,
    background: BackgroundTasks | None = None,
) -> None:
    summary = compute_summary(execution)
    context = _completion_context(db, execution, summary)
    recipients = _resolve_recipients(execution)
    for user_id in recipients:
        _send_finished_email(db, user_id, execution, context, background)
    if summary.failed > 0:
        for user_id in recipients:
            _send_failed_email(db, user_id, execution, context, background)


def on_execution_deleted(execution_id: int, project_id: int) -> None:
    notify_project(
        project_id,
        {
            "event": "execution.deleted",
            "data": {"id": execution_id, "project_id": project_id},
        },
    )


def on_results_bulk_updated(db: Session, execution_id: int) -> None:
    full = load_execution_full(db, execution_id)
    if not full:
        return
    _broadcast_project("execution.updated", full)


def on_result_updated(execution_id: int, payload: dict[str, Any]) -> None:
    notify_execution(execution_id, {"event": "result.updated", "data": payload})


def on_step_result_started(execution_id: int, payload: dict[str, Any]) -> None:
    notify_execution(
        execution_id, {"event": "step_result.started", "data": payload},
    )


def on_step_result_finished(execution_id: int, payload: dict[str, Any]) -> None:
    notify_execution(
        execution_id, {"event": "step_result.finished", "data": payload},
    )


def on_step_result_log_appended(execution_id: int, payload: dict[str, Any]) -> None:
    schedule_log_append(execution_id, payload)
