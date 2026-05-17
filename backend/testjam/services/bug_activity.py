"""Bug activity log.

Field-level audit trail for bugs. Replaces the status-only history with a
generalized log that records:

- status transitions (creation + change)
- field edits (title, description, severity, tags, assignee, version,
  fixed-in version, environment, external ticket url)
- link add / delete

Each entry is one ``BugActivity`` row keyed by ``(bug_id, field, changed_at)``
with serialized ``from_value`` / ``to_value`` strings so the frontend timeline
can render every change uniformly.

Callers commit the session. This module never commits.
"""
from __future__ import annotations

import json
from typing import Any, Iterable

from sqlalchemy.orm import Session, selectinload

from testjam.models.bug import Bug, BugActivity, BugLink
from testjam.schemas.bug import BugActivityOut


TRACKED_FIELDS: tuple[str, ...] = (
    "title",
    "description",
    "severity",
    "tags",
    "assigned_to_id",
    "version_id",
    "fixed_in_version_id",
    "environment",
    "external_ticket_url",
)

ASSIGNED_FIELD = "assigned_to"
VERSION_FIELD = "version"
FIXED_IN_VERSION_FIELD = "fixed_in_version"

_FIELD_RENAMES: dict[str, str] = {
    "assigned_to_id": ASSIGNED_FIELD,
    "version_id": VERSION_FIELD,
    "fixed_in_version_id": FIXED_IN_VERSION_FIELD,
}


def snapshot(bug: Bug) -> dict[str, Any]:
    return {field: getattr(bug, field) for field in TRACKED_FIELDS}


def record_field_changes(
    db: Session,
    bug: Bug,
    previous: dict[str, Any],
    actor_id: int | None,
) -> list[BugActivity]:
    rows: list[BugActivity] = []
    for field in TRACKED_FIELDS:
        before = previous.get(field)
        after = getattr(bug, field)
        if _values_equal(before, after):
            continue
        rows.append(_build_row(
            bug_id=bug.id,
            field=_FIELD_RENAMES.get(field, field),
            from_value=_serialize(field, before),
            to_value=_serialize(field, after),
            actor_id=actor_id,
        ))
    for row in rows:
        db.add(row)
    return rows


def record_status_change(
    db: Session,
    bug_id: int,
    previous_status: str | None,
    new_status: str,
    actor_id: int | None,
    note: str | None = None,
) -> BugActivity:
    row = _build_row(
        bug_id=bug_id,
        field="status",
        from_value=previous_status,
        to_value=new_status,
        actor_id=actor_id,
        note=note,
    )
    db.add(row)
    return row


def record_link_added(
    db: Session,
    bug_id: int,
    link: BugLink,
    actor_id: int | None,
) -> BugActivity:
    row = _build_row(
        bug_id=bug_id,
        field="link",
        from_value=None,
        to_value=_link_descriptor(link),
        actor_id=actor_id,
    )
    db.add(row)
    return row


def record_link_deleted(
    db: Session,
    bug_id: int,
    link: BugLink,
    actor_id: int | None,
) -> BugActivity:
    row = _build_row(
        bug_id=bug_id,
        field="link",
        from_value=_link_descriptor(link),
        to_value=None,
        actor_id=actor_id,
    )
    db.add(row)
    return row


def load_with_actor(db: Session, activity_id: int) -> BugActivity | None:
    return (
        db.query(BugActivity)
        .options(selectinload(BugActivity.changed_by))
        .filter(BugActivity.id == activity_id)
        .first()
    )


def activity_out(activity: BugActivity) -> BugActivityOut:
    return BugActivityOut.model_validate(activity)


def serialize_rows(rows: Iterable[BugActivity]) -> list[dict[str, Any]]:
    return [activity_out(row).model_dump(mode="json") for row in rows]


def _build_row(
    *,
    bug_id: int,
    field: str,
    from_value: str | None,
    to_value: str | None,
    actor_id: int | None,
    note: str | None = None,
) -> BugActivity:
    return BugActivity(
        bug_id=bug_id,
        field=field,
        from_value=from_value,
        to_value=to_value,
        note=note,
        changed_by_id=actor_id,
    )


def _values_equal(before: Any, after: Any) -> bool:
    if before is None and after is None:
        return True
    if isinstance(before, list) or isinstance(after, list):
        return (before or []) == (after or [])
    return before == after


def _serialize(field: str, value: Any) -> str | None:
    if value is None:
        return None
    if field == "tags":
        return json.dumps(list(value)) if value else "[]"
    if isinstance(value, (int, float)):
        return str(value)
    return str(value)


def _link_descriptor(link: BugLink) -> str:
    payload: dict[str, Any] = {"id": link.id}
    if link.kind is not None:
        payload["kind"] = link.kind
    if link.target_bug_id is not None:
        payload["target_bug_id"] = link.target_bug_id
    if link.execution_id is not None:
        payload["execution_id"] = link.execution_id
    if link.test_case_id is not None:
        payload["test_case_id"] = link.test_case_id
    if link.test_step_id is not None:
        payload["test_step_id"] = link.test_step_id
    if link.url is not None:
        payload["url"] = link.url
    if link.label is not None:
        payload["label"] = link.label
    return json.dumps(payload)
