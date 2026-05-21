"""Log line formatting + timestamp normalisation."""
from __future__ import annotations

from typing import Any


def format_timestamp(timestamp: Any) -> str | None:
    if timestamp is None:
        return None
    if hasattr(timestamp, "strftime"):
        milliseconds = timestamp.microsecond // 1000 if hasattr(timestamp, "microsecond") else 0
        return timestamp.strftime("%Y-%m-%d %H:%M:%S.") + f"{milliseconds:03d}"
    return str(timestamp)


def format_log_line(level: str, message: str, timestamp: Any = None) -> str:
    timestamp_text = format_timestamp(timestamp)
    if timestamp_text:
        return f"{timestamp_text} [{level}] {message}"
    return f"[{level}] {message}"


def isoformat_timestamp(timestamp: Any) -> str | None:
    if timestamp is None:
        return None
    if hasattr(timestamp, "isoformat"):
        return timestamp.isoformat()
    return str(timestamp)
