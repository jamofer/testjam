from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from testjam.models.user import User

MAX_FAILED_LOGINS = 5
LOCKOUT_DURATION_MINUTES = 15
LOCKOUT_MAX_MINUTES = 24 * 60


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
    """Increment the failure counter and lock the account every MAX failures.

    The counter is not reset on lockout, so successive lockouts double the
    duration (15, 30, 60, 120, … minutes, capped at 24 h). A successful
    login resets it back to zero via ``clear_lockout``.
    """
    user.failed_login_count = (user.failed_login_count or 0) + 1
    count = user.failed_login_count
    if count >= MAX_FAILED_LOGINS and count % MAX_FAILED_LOGINS == 0:
        round_number = count // MAX_FAILED_LOGINS
        minutes = min(LOCKOUT_DURATION_MINUTES * (2 ** (round_number - 1)), LOCKOUT_MAX_MINUTES)
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
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
