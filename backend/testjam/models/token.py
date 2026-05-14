from __future__ import annotations

import hashlib
import secrets
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from testjam.database import Base
from testjam.models._types import UTCDateTime


class ApiToken(Base):
    __tablename__ = "api_tokens"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_api_tokens_user_name"),
        UniqueConstraint("project_id", "name", name="uq_api_tokens_project_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

    @staticmethod
    def generate() -> tuple[str, str, str]:
        """Returns (raw_token, token_hash, prefix). Store only the hash."""
        raw = "tj_" + secrets.token_urlsafe(32)
        return raw, hashlib.sha256(raw.encode()).hexdigest(), raw[:12]

    @staticmethod
    def hash(raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()
