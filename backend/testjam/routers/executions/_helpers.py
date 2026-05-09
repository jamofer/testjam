"""Shared helpers used across execution submodules."""
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session, selectinload

from testjam.models.execution import ExecutionAttachment, TestExecution, TestResult
from testjam.models.notification import Notification
from testjam.models.user import User
from testjam.realtime import notify_user
from testjam.services.email import send_email, smtp_configured
from testjam.services.settings import get_settings as get_app_settings
from testjam.schemas.execution import ExecutionAttachmentOut, ExecutionSummary, TestExecutionOut


def push_assignment_notification(
    db: Session,
    execution: TestExecution,
    assignee_id: int,
    actor: User,
    background: BackgroundTasks | None = None,
) -> None:
    if assignee_id == actor.id:
        return
    n = Notification(
        user_id=assignee_id,
        type="execution_assigned",
        message=f"{actor.username} assigned you to '{execution.title}'",
        link=f"/executions/{execution.id}/run",
    )
    db.add(n)
    db.flush()
    payload = {
        "id": n.id,
        "type": n.type,
        "message": n.message,
        "link": n.link,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }
    notify_user(assignee_id, {"event": "notification", "data": payload})

    settings_row = get_app_settings(db)
    if not smtp_configured(settings_row) or background is None:
        return
    assignee = db.get(User, assignee_id)
    if not assignee or not assignee.email:
        return
    link = f"{settings_row.site_url.rstrip('/')}{n.link}" if settings_row.site_url else n.link
    subject = f"[{settings_row.app_name}] You were assigned to '{execution.title}'"
    html = (
        f"<p>{actor.username} assigned you to "
        f"<strong>{execution.title}</strong>.</p>"
        f"<p><a href='{link}'>Open the execution</a></p>"
    )
    text = f"{actor.username} assigned you to '{execution.title}'. Open: {link}"
    background.add_task(send_email, settings_row, assignee.email, subject, html, text)


def compute_summary(execution: TestExecution) -> ExecutionSummary:
    counts = {"passed": 0, "failed": 0, "blocked": 0, "not_run": 0}
    for r in execution.results:
        counts[r.status] = counts.get(r.status, 0) + 1
    return ExecutionSummary(total=len(execution.results), **counts)


def execution_out(ex: TestExecution) -> TestExecutionOut:
    data = TestExecutionOut.model_validate(ex)
    data.summary = compute_summary(ex)
    data.attachments = [ExecutionAttachmentOut.model_validate(a) for a in ex.attachments]
    return data


def load_execution_full(db: Session, ex_id: int) -> TestExecution | None:
    """Eager-load relationships used by `execution_out` and the xlsx export
    to avoid N+1 lazy queries on results / step_results / attachments / test_case."""
    return (
        db.query(TestExecution)
        .options(
            selectinload(TestExecution.results).selectinload(TestResult.test_case),
            selectinload(TestExecution.results).selectinload(TestResult.step_results),
            selectinload(TestExecution.results).selectinload(TestResult.attachments),
            selectinload(TestExecution.attachments),
        )
        .filter(TestExecution.id == ex_id)
        .first()
    )
