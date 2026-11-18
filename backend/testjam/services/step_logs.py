"""One format for every log line stored in ``TestStepResult.log_output``.

``2026-11-18T09:15:02.123Z [INFO] message`` — the timestamp is ISO 8601 with
millisecond precision so the UI can show it in the viewer's time zone and the
plain text still reads well in exports. Aware timestamps are stored in UTC;
naive ones (older listeners, output.xml imports) are kept as the runner wrote
them, without an offset.
"""
from __future__ import annotations

from datetime import UTC, datetime


def format_log_timestamp(ts: datetime) -> str:
    if ts.tzinfo is not None:
        return ts.astimezone(UTC).replace(tzinfo=None).isoformat(timespec="milliseconds") + "Z"
    return ts.isoformat(timespec="milliseconds")


def format_log_entry(level: str, message: str, ts: datetime | None = None) -> str:
    if ts is None:
        return f"[{level}] {message}"
    return f"{format_log_timestamp(ts)} [{level}] {message}"
