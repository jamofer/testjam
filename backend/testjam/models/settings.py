from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testjam.database import Base


class AppSettings(Base):
    """Singleton row holding global webapp configuration.

    Always has exactly one row with id == 1, seeded by migration.
    """

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    site_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    app_name: Mapped[str] = mapped_column(String(64), nullable=False, server_default="Testjam")
    allow_registration: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    default_environment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    default_version_pattern: Mapped[str | None] = mapped_column(String(64), nullable=True)

    max_upload_mb: Mapped[int] = mapped_column(Integer, nullable=False, server_default="20")
    notifications_retention_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="90"
    )

    smtp_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    smtp_user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_from: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_reply_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_use_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    ws_log_flush_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    updated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    updated_by: Mapped["User | None"] = relationship()  # noqa: F821
