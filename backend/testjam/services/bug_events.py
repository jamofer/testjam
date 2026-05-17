"""Single dispatch point for bug lifecycle events.

Each `on_bug_*` helper fires after a router mutates the bug. Hooks:

1. Broadcast WS payloads to ``project:{id}`` (list-affecting events) and
   ``bug:{id}`` (detail-affecting events). Front uses these via
   ``useProjectBugsLive`` and ``useBugLive`` to update caches without refetch.
2. For ``bug_assigned`` / ``bug_resolved`` / ``bug_status_changed``, schedule
   per-user notifications through ``services.notifications.notify``.

Callers commit the session. This module never commits.
"""
from __future__ import annotations

from typing import Any

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session, selectinload

from testjam.models.bug import Bug, BugAttachment, BugComment, BugLink, BugStatusHistory
from testjam.models.user import User
from testjam.realtime import notify_bug, notify_project
from testjam.schemas.bug import (
    BugAttachmentOut,
    BugCommentOut,
    BugLinkOut,
    BugOut,
    BugStatusHistoryOut,
    TERMINAL_BUG_STATUSES,
)
from testjam.services import email_templates
from testjam.services.notification_events import NotificationEvent
from testjam.services.notifications import notify
from testjam.services.settings import get_settings as get_app_settings


def load_bug_full(db: Session, bug_id: int) -> Bug | None:
    return (
        db.query(Bug)
        .options(
            selectinload(Bug.assigned_to),
            selectinload(Bug.created_by),
            selectinload(Bug.updated_by),
            selectinload(Bug.version),
            selectinload(Bug.fixed_in_version),
        )
        .filter(Bug.id == bug_id)
        .first()
    )


def bug_out(bug: Bug) -> BugOut:
    payload = BugOut.model_validate(bug)
    payload.version_name = bug.version.name if bug.version else None
    payload.fixed_in_version_name = bug.fixed_in_version.name if bug.fixed_in_version else None
    return payload


def _build_public_link(site_url: str | None, path: str) -> str:
    if not site_url:
        return path
    return f"{site_url.rstrip('/')}{path}"


def _bug_payload(bug: Bug) -> dict[str, Any]:
    return bug_out(bug).model_dump(mode="json")


def _broadcast_project(event: str, bug: Bug) -> None:
    payload = {"event": event, "data": _bug_payload(bug)}
    notify_project(bug.project_id, payload)
    notify_bug(bug.id, payload)


def _broadcast_bug(event: str, bug_id: int, data: dict[str, Any]) -> None:
    notify_bug(bug_id, {"event": event, "data": data})


def _recipient_locale(db: Session, user_id: int) -> str | None:
    return db.query(User.locale).filter(User.id == user_id).scalar()


def _bug_link(bug: Bug) -> str:
    return f"/projects/{bug.project_id}/bugs/{bug.number}"


def _send_bug_email(
    db: Session,
    user_id: int,
    event: NotificationEvent,
    context: dict[str, Any],
    link: str,
    background: BackgroundTasks | None,
) -> None:
    subject, html, text, message = email_templates.render(
        event.value, context, locale=_recipient_locale(db, user_id),
    )
    notify(
        db,
        user_id,
        event,
        message=message,
        link=link,
        email_subject=subject,
        email_html=html,
        email_text=text,
        background=background,
    )


def _bug_email_context(db: Session, bug: Bug, actor: User | None = None) -> dict[str, Any]:
    settings_row = get_app_settings(db)
    return {
        "app_name": settings_row.app_name,
        "site_url": settings_row.site_url,
        "actor": actor.username if actor else "",
        "subject_object": f"#{bug.number} {bug.title}",
        "link_in_app": _build_public_link(settings_row.site_url, _bug_link(bug)),
        "severity": bug.severity,
        "status": bug.status,
    }


def on_bug_created(db: Session, bug: Bug, actor: User, background: BackgroundTasks | None) -> None:
    full = load_bug_full(db, bug.id) or bug
    _broadcast_project("bug.created", full)
    if full.assigned_to_id and full.assigned_to_id != actor.id:
        _send_bug_email(
            db,
            full.assigned_to_id,
            NotificationEvent.BUG_ASSIGNED,
            _bug_email_context(db, full, actor),
            _bug_link(full),
            background,
        )


def on_bug_updated(db: Session, bug: Bug) -> None:
    full = load_bug_full(db, bug.id) or bug
    _broadcast_project("bug.updated", full)


def on_bug_assigned(
    db: Session, bug: Bug, previous_assignee_id: int | None, actor: User,
    background: BackgroundTasks | None,
) -> None:
    full = load_bug_full(db, bug.id) or bug
    _broadcast_project("bug.assigned", full)
    new_assignee = full.assigned_to_id
    if not new_assignee or new_assignee == previous_assignee_id or new_assignee == actor.id:
        return
    _send_bug_email(
        db, new_assignee, NotificationEvent.BUG_ASSIGNED,
        _bug_email_context(db, full, actor), _bug_link(full), background,
    )


def on_bug_status_changed(
    db: Session, bug: Bug, history_row: BugStatusHistory, actor: User,
    background: BackgroundTasks | None,
) -> None:
    full = load_bug_full(db, bug.id) or bug
    _broadcast_project("bug.status_changed", full)
    _broadcast_bug(
        "bug.history.added", full.id, BugStatusHistoryOut.model_validate(history_row).model_dump(mode="json"),
    )

    recipients: set[int] = set()
    if full.created_by_id and full.created_by_id != actor.id:
        recipients.add(full.created_by_id)
    if full.assigned_to_id and full.assigned_to_id != actor.id:
        recipients.add(full.assigned_to_id)

    is_terminal = history_row.to_status in TERMINAL_BUG_STATUSES
    event = NotificationEvent.BUG_RESOLVED if is_terminal else NotificationEvent.BUG_STATUS_CHANGED
    for user_id in recipients:
        _send_bug_email(
            db, user_id, event,
            _bug_email_context(db, full, actor), _bug_link(full), background,
        )


def on_bug_deleted(project_id: int, bug_id: int) -> None:
    notify_project(project_id, {"event": "bug.deleted", "data": {"id": bug_id}})


def on_bug_comment_added(comment: BugComment) -> None:
    _broadcast_bug(
        "bug.comment.added", comment.bug_id,
        BugCommentOut.model_validate(comment).model_dump(mode="json"),
    )


def on_bug_comment_updated(comment: BugComment) -> None:
    _broadcast_bug(
        "bug.comment.updated", comment.bug_id,
        BugCommentOut.model_validate(comment).model_dump(mode="json"),
    )


def on_bug_comment_deleted(bug_id: int, comment_id: int) -> None:
    _broadcast_bug("bug.comment.deleted", bug_id, {"id": comment_id})


def on_bug_attachment_added(attachment: BugAttachment) -> None:
    _broadcast_bug(
        "bug.attachment.added", attachment.bug_id,
        BugAttachmentOut.model_validate(attachment).model_dump(mode="json"),
    )


def on_bug_attachment_deleted(bug_id: int, attachment_id: int) -> None:
    _broadcast_bug("bug.attachment.deleted", bug_id, {"id": attachment_id})


def on_bug_link_added(link: BugLink, db: Session | None = None) -> None:
    _broadcast_bug(
        "bug.link.added", link.bug_id,
        link_out(link, db).model_dump(mode="json"),
    )


def on_bug_link_deleted(bug_id: int, link_id: int) -> None:
    _broadcast_bug("bug.link.deleted", bug_id, {"id": link_id})


def link_out(link: BugLink, db: Session | None = None) -> BugLinkOut:
    from testjam.models.version import ProjectVersion
    from testjam.schemas.bug import BugContextNode
    from testjam.services.bug_context import suite_path_for_case

    payload = BugLinkOut.model_validate(link)
    if link.execution is not None:
        payload.execution_title = link.execution.title
        payload.execution_environment = link.execution.environment
        payload.execution_version_id = link.execution.version_id
        if db is not None and link.execution.version_id is not None:
            version = db.get(ProjectVersion, link.execution.version_id)
            payload.execution_version_name = version.name if version else None
    if link.test_case is not None:
        payload.test_case_name = link.test_case.name
        if db is not None:
            suite_path = suite_path_for_case(db, link.test_case.suite_id)
            payload.suite_path = [BugContextNode(id=s.id, name=s.name) for s in suite_path]
    if link.test_step is not None:
        payload.test_step_action = link.test_step.action
    if link.target_bug is not None:
        payload.target_bug_number = link.target_bug.number
        payload.target_bug_title = link.target_bug.title
    return payload
