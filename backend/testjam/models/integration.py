from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Boolean, ForeignKey, Integer, JSON, LargeBinary, String, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testjam.database import Base
from testjam.models._types import UTCDateTime


class ProjectIntegration(Base):
    __tablename__ = "project_integrations"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "provider", "name",
            name="uq_project_integrations_project_provider_name",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status_mapping: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now(), onupdate=func.now(),
    )

    credential: Mapped["IntegrationCredential | None"] = relationship(
        back_populates="integration",
        uselist=False,
        cascade="all, delete-orphan",
    )
    # Deliberately no cascade: deleting an integration nullifies link.integration_id
    # so history rows survive (DB ON DELETE SET NULL + SA default behavior).
    external_links: Mapped[list["BugExternalLink"]] = relationship(
        back_populates="integration",
    )


class IntegrationCredential(Base):
    __tablename__ = "integration_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    integration_id: Mapped[int] = mapped_column(
        ForeignKey("project_integrations.id", ondelete="CASCADE"), unique=True,
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="api_token")
    secret_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now(), onupdate=func.now(),
    )

    integration: Mapped[ProjectIntegration] = relationship(back_populates="credential")


class BugExternalLink(Base):
    __tablename__ = "bug_external_links"
    __table_args__ = (
        UniqueConstraint(
            "bug_id", "integration_id", "external_id",
            name="uq_bug_external_links_bug_integration_external",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bug_id: Mapped[int] = mapped_column(ForeignKey("bugs.id", ondelete="CASCADE"), index=True)
    integration_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_integrations.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    status_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status_normalized: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown")
    last_synced_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())

    integration: Mapped["ProjectIntegration | None"] = relationship(back_populates="external_links")
    bug: Mapped["Bug"] = relationship(back_populates="external_links")  # noqa: F821
