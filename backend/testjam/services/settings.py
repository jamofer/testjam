"""AppSettings access helper. Lazy-creates the singleton row if missing."""
from __future__ import annotations

from sqlalchemy.orm import Session

from testjam.models.settings import AppSettings


def get_settings(db: Session) -> AppSettings:
    s = db.get(AppSettings, 1)
    if s is None:
        s = AppSettings(id=1)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s
