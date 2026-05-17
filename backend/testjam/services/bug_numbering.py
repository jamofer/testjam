"""Per-project sequential bug numbering (GitLab-style `#N`).

`SELECT MAX(number) + 1` with a retry loop on `IntegrityError` covers concurrent
inserts without coordinating via a dedicated counter table. Postgres-friendly,
SQLite-friendly (tests).
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from testjam.models.bug import Bug


MAX_NUMBERING_RETRIES = 5


def next_bug_number(db: Session, project_id: int) -> int:
    current = db.scalar(
        select(func.coalesce(func.max(Bug.number), 0)).where(Bug.project_id == project_id)
    )
    return (current or 0) + 1
