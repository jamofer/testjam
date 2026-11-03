"""Per-IP failed-login tracker.

The per-user lockout already enforces 5 attempts → 15 min cooldown, but the
attacker still gets a 401 (no lockout) when probing usernames that don't
exist, which oracles whether a username is real. This module applies the
same lockout policy keyed by client IP, so repeated failures against any
username from the same address eventually trip the same 423 response and
remove the side channel.

Counters live in Redis when ``REDIS_URL`` is set, so every worker and
replica shares them; otherwise they stay in this process.
"""
from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from threading import Lock
from typing import Protocol

import redis
from sqlalchemy.orm import Session

from testjam.auth.lockout import (
    LOCKOUT_DURATION_MINUTES,
    LOCKOUT_MAX_MINUTES,
    MAX_FAILED_LOGINS,
)
from testjam.core.config import settings
from testjam.services.settings import get_settings as get_app_settings

FAILURE_MEMORY_SECONDS = 24 * 60 * 60
REDIS_KEY_PREFIX = "testjam:ip-throttle"

logger = logging.getLogger(__name__)


class ThrottleStore(Protocol):
    def add_failure(self, ip: str) -> int: ...
    def lock(self, ip: str, seconds: int) -> None: ...
    def lock_remaining_seconds(self, ip: str) -> int: ...
    def clear(self, ip: str) -> None: ...


def is_ip_locked(db: Session, ip: str | None) -> bool:
    return seconds_until_ip_unlock(db, ip) > 0


def seconds_until_ip_unlock(db: Session, ip: str | None) -> int:
    if not ip or not _enabled(db):
        return 0
    try:
        return _current_store().lock_remaining_seconds(ip)
    except redis.RedisError:
        logger.warning("ip throttle store unavailable; not enforcing lock", exc_info=True)
        return 0


def register_ip_failure(db: Session, ip: str | None) -> None:
    if not ip or not _enabled(db):
        return
    store = _current_store()
    try:
        count = store.add_failure(ip)
        if count % MAX_FAILED_LOGINS == 0:
            store.lock(ip, _lock_seconds(count // MAX_FAILED_LOGINS))
    except redis.RedisError:
        logger.warning("ip throttle store unavailable; failure not recorded", exc_info=True)


def clear_ip(ip: str | None) -> None:
    if not ip:
        return
    try:
        _current_store().clear(ip)
    except redis.RedisError:
        logger.warning("ip throttle store unavailable; counters not cleared", exc_info=True)


def use_store(store: ThrottleStore | None) -> None:
    """Replace the store; ``None`` picks the default again on next use."""
    global _store
    _store = store


class MemoryThrottleStore:
    def __init__(self) -> None:
        self._buckets: dict[str, _Bucket] = {}
        self._mutex = Lock()

    def add_failure(self, ip: str) -> int:
        with self._mutex:
            bucket = self._buckets.setdefault(ip, _Bucket())
            bucket.failed_count += 1
            return bucket.failed_count

    def lock(self, ip: str, seconds: int) -> None:
        with self._mutex:
            self._buckets.setdefault(ip, _Bucket()).locked_until = time.monotonic() + seconds

    def lock_remaining_seconds(self, ip: str) -> int:
        with self._mutex:
            bucket = self._buckets.get(ip)
            if bucket is None or bucket.locked_until is None:
                return 0
            return max(0, math.ceil(bucket.locked_until - time.monotonic()))

    def clear(self, ip: str) -> None:
        with self._mutex:
            self._buckets.pop(ip, None)


class RedisThrottleStore:
    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    def add_failure(self, ip: str) -> int:
        key = _redis_key(ip, "failures")
        with self._client.pipeline() as pipeline:
            pipeline.incr(key)
            pipeline.expire(key, FAILURE_MEMORY_SECONDS)
            count, _ = pipeline.execute()
        return int(count)

    def lock(self, ip: str, seconds: int) -> None:
        self._client.set(_redis_key(ip, "locked"), 1, ex=seconds)

    def lock_remaining_seconds(self, ip: str) -> int:
        return max(0, int(self._client.ttl(_redis_key(ip, "locked"))))

    def clear(self, ip: str) -> None:
        self._client.delete(_redis_key(ip, "failures"), _redis_key(ip, "locked"))


@dataclass
class _Bucket:
    failed_count: int = 0
    locked_until: float | None = None


_store: ThrottleStore | None = None


def _current_store() -> ThrottleStore:
    global _store
    if _store is None:
        _store = _default_store()
    return _store


def _default_store() -> ThrottleStore:
    if settings.REDIS_URL:
        return RedisThrottleStore(redis.Redis.from_url(settings.REDIS_URL))
    return MemoryThrottleStore()


def _enabled(db: Session) -> bool:
    return bool(get_app_settings(db).ip_throttle_enabled)


def _lock_seconds(round_number: int) -> int:
    minutes = min(LOCKOUT_DURATION_MINUTES * 2 ** (round_number - 1), LOCKOUT_MAX_MINUTES)
    return minutes * 60


def _redis_key(ip: str, kind: str) -> str:
    return f"{REDIS_KEY_PREFIX}:{ip}:{kind}"
