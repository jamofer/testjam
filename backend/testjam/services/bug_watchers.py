"""Bug watch / follow registry.

A watcher is a user who has opted in to receive notifications for any change on
a specific bug — status changes, new comments, etc. Callers commit the session.

Auto-watch fires from `bug_events`:
- on create → creator + assignee
- on assign → new assignee
- on comment → commenter

Manual subscribe / unsubscribe lives at `POST/DELETE /bugs/{id}/watch`.
"""
from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from testjam.models.bug import Bug, BugWatcher


def list_watchers(database: Session, bug_id: int) -> list[BugWatcher]:
    return (
        database.query(BugWatcher)
        .options(selectinload(BugWatcher.user))
        .filter(BugWatcher.bug_id == bug_id)
        .order_by(BugWatcher.created_at.asc(), BugWatcher.user_id.asc())
        .all()
    )


def watcher_user_ids(database: Session, bug_id: int) -> set[int]:
    rows = (
        database.query(BugWatcher.user_id)
        .filter(BugWatcher.bug_id == bug_id)
        .all()
    )
    return {row[0] for row in rows}


def watcher_count(database: Session, bug_id: int) -> int:
    return (
        database.query(BugWatcher)
        .filter(BugWatcher.bug_id == bug_id)
        .count()
    )


def is_watching(database: Session, bug_id: int, user_id: int) -> bool:
    return (
        database.query(BugWatcher)
        .filter(BugWatcher.bug_id == bug_id, BugWatcher.user_id == user_id)
        .first()
        is not None
    )


def add_watcher(database: Session, bug_id: int, user_id: int) -> BugWatcher:
    existing = (
        database.query(BugWatcher)
        .filter(BugWatcher.bug_id == bug_id, BugWatcher.user_id == user_id)
        .first()
    )
    if existing is not None:
        return existing
    watcher = BugWatcher(bug_id=bug_id, user_id=user_id)
    database.add(watcher)
    database.flush()
    return watcher


def remove_watcher(database: Session, bug_id: int, user_id: int) -> bool:
    watcher = (
        database.query(BugWatcher)
        .filter(BugWatcher.bug_id == bug_id, BugWatcher.user_id == user_id)
        .first()
    )
    if watcher is None:
        return False
    database.delete(watcher)
    return True


def auto_watch(database: Session, bug: Bug, user_ids: list[int | None]) -> None:
    for user_id in user_ids:
        if user_id is None:
            continue
        add_watcher(database, bug.id, user_id)
