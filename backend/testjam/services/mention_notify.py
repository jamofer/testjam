"""Fan-out @user mentions in a body to per-user notifications.

Called from any router that persists comment-like bodies. Strict permissions:
recipients are limited to project members so a comment author cannot leak the
existence of a private project by mentioning an outsider.

When a body is edited, callers pass the previous body so only *new* mentions
trigger a notification — re-saving an unchanged comment is silent. Removing a
mention does not retract historical notifications, matching GitLab.
"""
from __future__ import annotations

from typing import Any

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from testjam.models.user import User
from testjam.services import email_templates
from testjam.services.mentions import parse
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
    new_slugs = _new_mention_slugs(body, previous_body)
    if not new_slugs:
        return []
    recipients = _resolve_member_ids(db, project_id, new_slugs, exclude_user_id=actor.id)
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


def _new_mention_slugs(body: str, previous_body: str | None) -> set[str]:
    current = {token.slug for token in parse(body) if token.kind == "user" and token.slug}
    if not previous_body:
        return current
    prior = {token.slug for token in parse(previous_body) if token.kind == "user" and token.slug}
    return current - prior


def _resolve_member_ids(
    db: Session, project_id: int, slugs: set[str], exclude_user_id: int,
) -> list[int]:
    if not slugs:
        return []
    users = (
        db.query(User)
        .filter(User.username.in_(slugs), User.is_active == True)  # noqa: E712
        .all()
    )
    member_ids: list[int] = []
    for user in users:
        if user.id == exclude_user_id:
            continue
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
