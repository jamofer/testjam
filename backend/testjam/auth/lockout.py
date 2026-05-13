from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from testjam.models.user import User

MAX_FAILED_LOGINS = 5
LOCKOUT_DURATION_MINUTES = 15


def is_locked(user: User) -> bool:
    if user.locked_until is None:
        return False
    locked_until = _as_utc(user.locked_until)
    return locked_until > datetime.now(timezone.utc)


def seconds_until_unlock(user: User) -> int:
    if user.locked_until is None:
        return 0
    remaining = _as_utc(user.locked_until) - datetime.now(timezone.utc)
    return max(0, int(remaining.total_seconds()))


def register_failed_attempt(db: Session, user: User) -> None:
    user.failed_login_count = (user.failed_login_count or 0) + 1
    if user.failed_login_count >= MAX_FAILED_LOGINS:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        user.failed_login_count = 0
    db.commit()


def clear_lockout(db: Session, user: User) -> None:
    if user.failed_login_count == 0 and user.locked_until is None:
        return
    user.failed_login_count = 0
    user.locked_until = None
    db.commit()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
