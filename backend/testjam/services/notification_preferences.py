"""User-notification preferences.

Stores per-user, per-event delivery toggles for the in-app and email channels.
Defaults are lazy-created on first fetch so a brand-new user can render the
preferences UI without an explicit "create defaults" step.

Only event types currently emitted by the backend get default rows. Reserved
events in `NotificationEvent` (password_reset, mention_in_comment, …) will be
filled in when their producers land.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from testjam.models.notification_preference import UserNotificationPreference
from testjam.services.notification_events import KNOWN_EVENT_TYPES, NotificationEvent

DEFAULT_PREFERENCES: dict[str, tuple[bool, bool]] = {
    NotificationEvent.EXECUTION_ASSIGNED.value: (True, True),
    NotificationEvent.EXECUTION_FINISHED.value: (True, False),
    NotificationEvent.EXECUTION_FAILED.value: (True, True),
}


def is_known_event(event_type: str) -> bool:
    return event_type in KNOWN_EVENT_TYPES


def _default_for(event_type: str) -> tuple[bool, bool]:
    return DEFAULT_PREFERENCES.get(event_type, (True, False))


def _find(db: Session, user_id: int, event_type: str) -> UserNotificationPreference | None:
    return (
        db.query(UserNotificationPreference)
        .filter(
            UserNotificationPreference.user_id == user_id,
            UserNotificationPreference.event_type == event_type,
        )
        .first()
    )


def _create_default(
    db: Session, user_id: int, event_type: str,
) -> UserNotificationPreference:
    in_app, email = _default_for(event_type)
    preference = UserNotificationPreference(
        user_id=user_id, event_type=event_type, in_app=in_app, email=email,
    )
    db.add(preference)
    db.flush()
    return preference


def get_or_create(
    db: Session, user_id: int, event_type: str,
) -> UserNotificationPreference:
    existing = _find(db, user_id, event_type)
    if existing is not None:
        return existing
    return _create_default(db, user_id, event_type)


def list_for_user(db: Session, user_id: int) -> list[UserNotificationPreference]:
    """Return all preferences for the user, lazy-creating any missing default rows."""
    existing = (
        db.query(UserNotificationPreference)
        .filter(UserNotificationPreference.user_id == user_id)
        .all()
    )
    already_present = {preference.event_type for preference in existing}
    created = [
        _create_default(db, user_id, event_type)
        for event_type in DEFAULT_PREFERENCES
        if event_type not in already_present
    ]
    if created:
        db.commit()
    return existing + created


def set_preference(
    db: Session,
    user_id: int,
    event_type: str,
    *,
    in_app: bool,
    email: bool,
) -> UserNotificationPreference:
    preference = _find(db, user_id, event_type)
    if preference is None:
        preference = UserNotificationPreference(
            user_id=user_id, event_type=event_type,
        )
        db.add(preference)
    preference.in_app = in_app
    preference.email = email
    db.commit()
    db.refresh(preference)
    return preference


def is_email_enabled(db: Session, user_id: int, event_type: str) -> bool:
    return get_or_create(db, user_id, event_type).email


def is_in_app_enabled(db: Session, user_id: int, event_type: str) -> bool:
    return get_or_create(db, user_id, event_type).in_app
