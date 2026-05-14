"""Centralized notification dispatcher.

`notify()` is the single entry point for emitting a per-user notification across
all delivery channels:

1. In-app — persists a `Notification` row + pushes via WebSocket.
2. Email — schedules a background SMTP send.

Each channel is gated by the user's `UserNotificationPreference` for the event.
Callers render the email body via `services/email_templates.py` so HTML is
auto-escaped.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from testjam.models.notification import Notification
from testjam.models.user import User
from testjam.realtime import notify_user as ws_notify_user
from testjam.services import notification_preferences
from testjam.services.email import send_email, smtp_configured
from testjam.services.notification_events import NotificationEvent
from testjam.services.settings import get_settings as get_app_settings

log = logging.getLogger("testjam.notifications")

DEDUPE_WINDOW_SECONDS = 60


def _persist_and_push(
    db: Session,
    user_id: int,
    event_type: str,
    message: str,
    link: str | None,
) -> Notification:
    notification = Notification(
        user_id=user_id, type=event_type, message=message, link=link,
    )
    db.add(notification)
    db.flush()
    payload: dict[str, Any] = {
        "id": notification.id,
        "type": notification.type,
        "message": notification.message,
        "link": notification.link,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
    }
    ws_notify_user(user_id, {"event": "notification", "data": payload})
    return notification


def _recent_duplicate_exists(
    db: Session, user_id: int, event_type: str, link: str | None,
) -> bool:
    threshold = datetime.now(timezone.utc) - timedelta(seconds=DEDUPE_WINDOW_SECONDS)
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.type == event_type,
            Notification.link == link,
            Notification.created_at >= threshold,
        )
        .first()
        is not None
    )


def _can_send_email(
    db: Session,
    user_id: int,
    email_subject: str | None,
    email_html: str | None,
    background: BackgroundTasks | None,
) -> tuple[bool, User | None, Any]:
    if not (email_subject and email_html and background is not None):
        return False, None, None
    settings_row = get_app_settings(db)
    if not smtp_configured(settings_row):
        return False, None, None
    user = db.get(User, user_id)
    if not user or not user.email:
        return False, None, None
    return True, user, settings_row


def notify(
    db: Session,
    user_id: int,
    event_type: NotificationEvent | str,
    *,
    message: str,
    link: str | None = None,
    email_subject: str | None = None,
    email_html: str | None = None,
    email_text: str | None = None,
    background: BackgroundTasks | None = None,
) -> Notification | None:
    """Dispatch a notification across the channels enabled by the user's prefs.

    Returns the `Notification` row when persisted (in-app enabled), or None when
    the user has opted out of in-app for this event type. The caller is
    responsible for committing the session.
    """
    event_key = str(event_type)
    if _recent_duplicate_exists(db, user_id, event_key, link):
        log.info(
            "notification.deduped event=%s user_id=%s link=%s", event_key, user_id, link,
        )
        return None

    preference = notification_preferences.get_or_create(db, user_id, event_key)

    notification: Notification | None = None
    if preference.in_app:
        notification = _persist_and_push(db, user_id, event_key, message, link)

    if not preference.email:
        return notification

    can_send, user, settings_row = _can_send_email(
        db, user_id, email_subject, email_html, background,
    )
    if not can_send:
        return notification

    background.add_task(
        send_email, settings_row, user.email, email_subject, email_html, email_text,
    )
    log.info("email.scheduled event=%s user_id=%s", event_key, user_id)
    return notification
