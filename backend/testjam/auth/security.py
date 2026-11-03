from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from testjam.core.config import settings
from testjam.models.user import User

UNKNOWN_ISSUE_TIME = 0.0


@dataclass(frozen=True)
class TokenClaims:
    subject: str
    issued_at: float


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def set_password(user: User, password: str) -> None:
    """Change the password and end every session opened with the previous one."""
    user.hashed_password = hash_password(password)
    user.password_changed_at = datetime.now(UTC)


def create_access_token(subject: str) -> str:
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": subject, "exp": expire, "iat": now.timestamp()},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str) -> TokenClaims | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None
    subject = payload.get("sub")
    if not subject:
        return None
    return TokenClaims(subject=subject, issued_at=payload.get("iat", UNKNOWN_ISSUE_TIME))


def is_session_current(user: User, claims: TokenClaims) -> bool:
    changed_at = user.password_changed_at
    return changed_at is None or claims.issued_at >= changed_at.timestamp()
