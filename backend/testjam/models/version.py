from __future__ import annotations

from datetime import date, datetime
from sqlalchemy import Date, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testjam.database import Base
from testjam.models._types import UTCDateTime


class ProjectVersion(Base):
    __tablename__ = "project_versions"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_project_versions_project_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # "active" | "released" | "archived"
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    vcs_tag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="versions")
    executions: Mapped[list[TestExecution]] = relationship(back_populates="project_version")
    attachments: Mapped[list[VersionAttachment]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )


class VersionAttachment(Base):
    __tablename__ = "version_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version_id: Mapped[int] = mapped_column(
        ForeignKey("project_versions.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    uploaded_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    version: Mapped[ProjectVersion] = relationship(back_populates="attachments")
    uploaded_by: Mapped["User | None"] = relationship(foreign_keys=[uploaded_by_id])  # noqa: F821
