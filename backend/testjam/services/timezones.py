"""Helpers for rendering datetimes in a user's preferred IANA timezone."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from testjam.models.user import User

UTC = ZoneInfo("UTC")


def user_zone(user: User | None) -> ZoneInfo:
    name = getattr(user, "timezone", None) if user is not None else None
    if not name:
        return UTC
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return UTC


def format_in_user_zone(value: datetime | None, user: User | None, fmt: str) -> str:
    if value is None:
        return ""
    return value.astimezone(user_zone(user)).strftime(fmt)


def user_zone_label(user: User | None, now: datetime | None = None) -> str:
    zone = user_zone(user)
    moment = (now or datetime.now(zone)).astimezone(zone)
    abbreviation = moment.strftime("%Z").strip()
    return abbreviation or str(zone)
