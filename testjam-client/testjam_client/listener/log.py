"""Log timestamps and the line format kept in ``log_output``.

Lines read ``2026-11-18T09:15:02.123Z [INFO] message``, the same shape the
server writes for streamed entries, so a run that fell back to batch mode
looks the same as a streamed one.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

ROBOT_LEGACY_TIMESTAMP_FORMAT = "%Y%m%d %H:%M:%S.%f"


def to_utc(timestamp: Any) -> datetime:
    """Robot's message time as an aware UTC datetime, or now if it has none.

    Robot 7 gives a naive datetime and Robot 6 a ``20240101 12:00:00.100``
    string, both in the runner's local time.
    """
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.strptime(timestamp, ROBOT_LEGACY_TIMESTAMP_FORMAT)
        except ValueError:
            timestamp = None
    if not isinstance(timestamp, datetime):
        return datetime.now(timezone.utc)
    return timestamp.astimezone(timezone.utc)


def format_log_timestamp(timestamp: datetime) -> str:
    utc = timestamp.astimezone(timezone.utc).replace(tzinfo=None)
    return utc.isoformat(timespec="milliseconds") + "Z"


def format_log_line(level: str, message: str, timestamp: datetime) -> str:
    return f"{format_log_timestamp(timestamp)} [{level}] {message}"
