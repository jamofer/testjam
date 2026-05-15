from __future__ import annotations

import secrets
import string

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from testjam.auth.lockout import clear_lockout
from testjam.auth.security import hash_password
from testjam.models.user import User
from testjam.services.password_reset import issue_reset_email_for_user

TEMPORARY_PASSWORD_LENGTH = 16
PASSWORD_ALPHABET = string.ascii_letters + string.digits


def issue_temporary_password(db: Session, user: User) -> str:
    raw = "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(TEMPORARY_PASSWORD_LENGTH))
    user.hashed_password = hash_password(raw)
    clear_lockout(db, user)
    db.commit()
    return raw


def send_reset_email(db: Session, user: User, background: BackgroundTasks | None) -> None:
    issue_reset_email_for_user(db, user, background=background)
