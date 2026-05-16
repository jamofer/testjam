from datetime import datetime, timezone

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from testjam.auth.lockout import clear_lockout
from testjam.auth.security import hash_password
from testjam.models.password_reset import PASSWORD_RESET_TOKEN_TTL_HOURS, PasswordResetToken
from testjam.models.user import User
from testjam.services import email_templates
from testjam.services.email import send_email
from testjam.services.notification_events import NotificationEvent
from testjam.services.settings import get_settings as get_app_settings


def request_password_reset(
    db: Session,
    email: str,
    background: BackgroundTasks | None = None,
) -> None:
    user = (
        db.query(User)
        .filter(User.email == email, User.is_active == True, User.deleted_at.is_(None))
        .first()
    )
    if not user:
        return
    issue_reset_email_for_user(db, user, background)


def issue_reset_email_for_user(
    db: Session,
    user: User,
    background: BackgroundTasks | None = None,
) -> None:
    raw_token, _, _ = _create_reset_token(db, user)
    _dispatch_reset_email(db, user, raw_token, background)


def confirm_password_reset(db: Session, raw_token: str, new_password: str) -> bool:
    token = _load_active_token(db, raw_token)
    if token is None:
        return False
    user = db.get(User, token.user_id)
    if user is None or not user.is_active or user.deleted_at is not None:
        return False
    user.hashed_password = hash_password(new_password)
    token.used_at = datetime.now(timezone.utc)
    db.commit()
    clear_lockout(db, user)
    return True


def _create_reset_token(db: Session, user: User) -> tuple[str, str, datetime]:
    raw, token_hash, expires_at = PasswordResetToken.generate()
    record = PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
    db.add(record)
    db.commit()
    return raw, token_hash, expires_at


def _load_active_token(db: Session, raw_token: str) -> PasswordResetToken | None:
    record = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == PasswordResetToken.hash(raw_token))
        .first()
    )
    if record is None or record.used_at is not None:
        return None
    if _expires_at_utc(record) <= datetime.now(timezone.utc):
        return None
    return record


def _expires_at_utc(token: PasswordResetToken) -> datetime:
    if token.expires_at.tzinfo is None:
        return token.expires_at.replace(tzinfo=timezone.utc)
    return token.expires_at


def _dispatch_reset_email(
    db: Session,
    user: User,
    raw_token: str,
    background: BackgroundTasks | None,
) -> None:
    settings_row = get_app_settings(db)
    reset_url = _build_reset_url(settings_row.site_url, raw_token)
    context = {
        "app_name": settings_row.app_name,
        "site_url": settings_row.site_url,
        "username": user.username,
        "reset_url": reset_url,
        "ttl_hours": PASSWORD_RESET_TOKEN_TTL_HOURS,
    }
    subject, html, text, _message = email_templates.render(
        NotificationEvent.PASSWORD_RESET.value, context, locale=user.locale,
    )
    if background is not None:
        background.add_task(send_email, settings_row, user.email, subject, html, text)
    else:
        send_email(settings_row, user.email, subject, html, text)


def _build_reset_url(site_url: str | None, raw_token: str) -> str:
    base = (site_url or "").rstrip("/")
    return f"{base}/reset-password?token={raw_token}"
