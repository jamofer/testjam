"""Fan-out mentions in a body to per-user notifications.

Called from any router that persists comment-like bodies. Strict permissions:
recipients are limited to project members so a comment author cannot leak the
existence of a private project by mentioning an outsider.

When a body is edited, callers pass the previous body so only *new* mentions
trigger a notification — re-saving an unchanged comment is silent. Removing a
mention does not retract historical notifications, matching GitLab.

Entity mentions (#bug / !run / ~case) fan out to the entity's participants
(assignee + creator/updater). Cross-project targets are ignored so the
permission perimeter holds.
"""
from __future__ import annotations

from typing import Any

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session, selectinload

from testjam.models.bug import Bug
from testjam.models.execution import TestExecution
from testjam.models.testcase import TestCase
from testjam.models.user import User
from testjam.services import email_templates
from testjam.services.mentions import Mention, parse
from testjam.services.notification_events import NotificationEvent
from testjam.services.notifications import notify
from testjam.services.permissions import effective_role
from testjam.services.settings import get_settings as get_app_settings


MAX_EXCERPT_LENGTH = 280


def notify_mentions(
    db: Session,
    *,
    project_id: int,
    body: str,
    previous_body: str | None,
    subject_object: str,
    link_path: str,
    actor: User,
    background: BackgroundTasks | None,
) -> list[int]:
    new_tokens = _new_mention_tokens(body, previous_body)
    if not new_tokens:
        return []
    recipients = _resolve_recipients(db, project_id, new_tokens, exclude_user_id=actor.id)
    if not recipients:
        return []
    settings_row = get_app_settings(db)
    excerpt = _build_excerpt(body)
    notified: list[int] = []
    for user_id in recipients:
        context = _build_context(settings_row, actor, subject_object, link_path, excerpt)
        _dispatch(db, user_id, context, link_path, background)
        notified.append(user_id)
    if notified:
        db.commit()
    return notified


def _token_key(token: Mention) -> tuple:
    return (token.kind, token.slug, token.id, token.sub_ids)


def _new_mention_tokens(body: str, previous_body: str | None) -> list[Mention]:
    current = parse(body)
    if not previous_body:
        return current
    prior_keys = {_token_key(token) for token in parse(previous_body)}
    return [token for token in current if _token_key(token) not in prior_keys]


def _resolve_recipients(
    db: Session, project_id: int, tokens: list[Mention], exclude_user_id: int,
) -> list[int]:
    candidate_ids: set[int] = set()
    user_slugs = {token.slug for token in tokens if token.kind == "user" and token.slug}
    bug_numbers = {token.id for token in tokens if token.kind == "bug" and token.id is not None}
    execution_ids = {
        token.id for token in tokens
        if token.kind in ("execution", "result", "step_result") and token.id is not None
    }
    case_ids = {token.id for token in tokens if token.kind == "case" and token.id is not None}

    candidate_ids.update(_user_ids_from_slugs(db, user_slugs))
    candidate_ids.update(_user_ids_from_bugs(db, project_id, bug_numbers))
    candidate_ids.update(_user_ids_from_executions(db, project_id, execution_ids))
    candidate_ids.update(_user_ids_from_cases(db, project_id, case_ids))

    candidate_ids.discard(exclude_user_id)
    if not candidate_ids:
        return []
    return _filter_members(db, project_id, candidate_ids)


def _user_ids_from_slugs(db: Session, slugs: set[str]) -> set[int]:
    if not slugs:
        return set()
    rows = (
        db.query(User.id)
        .filter(User.username.in_(slugs), User.is_active == True)  # noqa: E712
        .all()
    )
    return {row.id for row in rows}


def _user_ids_from_bugs(db: Session, project_id: int, numbers: set[int]) -> set[int]:
    if not numbers:
        return set()
    bugs = (
        db.query(Bug)
        .filter(Bug.project_id == project_id, Bug.number.in_(numbers))
        .all()
    )
    found: set[int] = set()
    for bug in bugs:
        if bug.assigned_to_id is not None:
            found.add(bug.assigned_to_id)
        if bug.created_by_id is not None:
            found.add(bug.created_by_id)
    return found


def _user_ids_from_executions(db: Session, project_id: int, ids: set[int]) -> set[int]:
    if not ids:
        return set()
    executions = (
        db.query(TestExecution)
        .filter(TestExecution.id.in_(ids), TestExecution.project_id == project_id)
        .all()
    )
    found: set[int] = set()
    for execution in executions:
        if execution.assigned_to_id is not None:
            found.add(execution.assigned_to_id)
        if execution.created_by_id is not None:
            found.add(execution.created_by_id)
    return found


def _user_ids_from_cases(db: Session, project_id: int, ids: set[int]) -> set[int]:
    if not ids:
        return set()
    cases = (
        db.query(TestCase)
        .options(selectinload(TestCase.suite))
        .filter(TestCase.id.in_(ids))
        .all()
    )
    found: set[int] = set()
    for case in cases:
        if case.suite is None or case.suite.project_id != project_id:
            continue
        if case.created_by_id is not None:
            found.add(case.created_by_id)
        if case.updated_by_id is not None:
            found.add(case.updated_by_id)
    return found


def _filter_members(db: Session, project_id: int, user_ids: set[int]) -> list[int]:
    users = (
        db.query(User)
        .filter(User.id.in_(user_ids), User.is_active == True)  # noqa: E712
        .all()
    )
    member_ids: list[int] = []
    for user in users:
        if user.is_admin or effective_role(db, user.id, project_id) is not None:
            member_ids.append(user.id)
    return member_ids


def _build_excerpt(body: str) -> str:
    text = body.strip()
    if len(text) <= MAX_EXCERPT_LENGTH:
        return text
    return text[: MAX_EXCERPT_LENGTH - 1].rstrip() + "…"


def _build_context(
    settings_row, actor: User, subject_object: str, link_path: str, excerpt: str,
) -> dict[str, Any]:
    site_url = settings_row.site_url
    return {
        "app_name": settings_row.app_name,
        "site_url": site_url,
        "actor": actor.username,
        "subject_object": subject_object,
        "link_in_app": _build_public_link(site_url, link_path),
        "excerpt": excerpt,
    }


def _build_public_link(site_url: str | None, path: str) -> str:
    if not site_url:
        return path
    return f"{site_url.rstrip('/')}{path}"


def _dispatch(
    db: Session,
    user_id: int,
    context: dict[str, Any],
    link_path: str,
    background: BackgroundTasks | None,
) -> None:
    locale = db.query(User.locale).filter(User.id == user_id).scalar()
    subject, html, text, message = email_templates.render(
        NotificationEvent.MENTION_IN_COMMENT.value, context, locale=locale,
    )
    notify(
        db,
        user_id,
        NotificationEvent.MENTION_IN_COMMENT,
        message=message,
        link=link_path,
        email_subject=subject,
        email_html=html,
        email_text=text,
        background=background,
    )
