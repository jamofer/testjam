from __future__ import annotations

from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testjam.database import Base
from testjam.models._types import UTCDateTime


class ProjectVersion(Base):
    __tablename__ = "project_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # "active" | "released" | "archived"
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    vcs_tag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="versions")
    executions: Mapped[list[TestExecution]] = relationship(back_populates="project_version")
