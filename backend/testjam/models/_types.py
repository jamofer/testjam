"""Custom SQLAlchemy column types shared by every model."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    """Stores datetimes with timezone awareness; round-trips as UTC-aware.

    PostgreSQL stores ``TIMESTAMPTZ`` natively. SQLite (used in tests) has no
    timezone-aware type, so naive datetimes coming back from the driver are
    re-tagged as UTC on read — keeping the API contract (ISO 8601 with offset)
    consistent across backends.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
