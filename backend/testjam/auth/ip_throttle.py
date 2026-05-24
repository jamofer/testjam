"""Per-IP failed-login tracker.

The per-user lockout already enforces 5 attempts → 15 min cooldown, but the
attacker still gets a 401 (no lockout) when probing usernames that don't
exist, which oracles whether a username is real. This module applies the
same lockout policy keyed by client IP, so repeated failures against any
username from the same address eventually trip the same 423 response and
remove the side channel.

In-memory store. For multi-worker deployments behind a load balancer the
counter is best-effort per worker — Redis-backed promotion is a future
hardening item.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock

from sqlalchemy.orm import Session

from testjam.auth.lockout import (
    LOCKOUT_DURATION_MINUTES,
    LOCKOUT_MAX_MINUTES,
    MAX_FAILED_LOGINS,
)
from testjam.services.settings import get_settings as get_app_settings


@dataclass
class _Bucket:
    failed_count: int = 0
    locked_until: datetime | None = None


_buckets: dict[str, _Bucket] = {}
_buckets_mutex = Lock()


def _enabled(db: Session) -> bool:
    return bool(get_app_settings(db).ip_throttle_enabled)


def is_ip_locked(db: Session, ip: str | None) -> bool:
    if not ip or not _enabled(db):
        return False
    with _buckets_mutex:
        bucket = _buckets.get(ip)
        if bucket is None or bucket.locked_until is None:
            return False
        return bucket.locked_until > datetime.now(timezone.utc)


def seconds_until_ip_unlock(db: Session, ip: str | None) -> int:
    if not ip or not _enabled(db):
        return 0
    with _buckets_mutex:
        bucket = _buckets.get(ip)
        if bucket is None or bucket.locked_until is None:
            return 0
        remaining = bucket.locked_until - datetime.now(timezone.utc)
        return max(0, int(remaining.total_seconds()))


def register_ip_failure(db: Session, ip: str | None) -> None:
    if not ip or not _enabled(db):
        return
    with _buckets_mutex:
        bucket = _buckets.setdefault(ip, _Bucket())
        bucket.failed_count += 1
        count = bucket.failed_count
        if count >= MAX_FAILED_LOGINS and count % MAX_FAILED_LOGINS == 0:
            round_number = count // MAX_FAILED_LOGINS
            minutes = min(
                LOCKOUT_DURATION_MINUTES * (2 ** (round_number - 1)),
                LOCKOUT_MAX_MINUTES,
            )
            bucket.locked_until = datetime.now(timezone.utc) + timedelta(minutes=minutes)


def clear_ip(ip: str | None) -> None:
    if not ip:
        return
    with _buckets_mutex:
        _buckets.pop(ip, None)


def _reset_for_tests() -> None:
    """Test-only escape hatch. Drops every bucket without locking guarantees."""
    with _buckets_mutex:
        _buckets.clear()
