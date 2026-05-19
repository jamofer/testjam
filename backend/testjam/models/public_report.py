from __future__ import annotations

import hashlib
import secrets
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testjam.database import Base
from testjam.models._types import UTCDateTime

PUBLIC_REPORT_KINDS = {"bug_report", "execution"}


class PublicReport(Base):
    __tablename__ = "public_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    execution_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_executions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    version_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_versions.id", ondelete="SET NULL"), nullable=True
    )
    environment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    last_viewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    project = relationship("Project")
    execution = relationship("TestExecution")
    version = relationship("ProjectVersion")
    created_by = relationship("User", foreign_keys=[created_by_id])

    @staticmethod
    def generate_token() -> tuple[str, str]:
        raw = secrets.token_urlsafe(32)
        return raw, hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def hash_token(raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()
