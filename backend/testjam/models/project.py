from __future__ import annotations

from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testjam.database import Base
from testjam.models._types import UTCDateTime


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), onupdate=func.now())
    archived_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True, index=True)

    members: Mapped[list[ProjectMember]] = relationship(back_populates="project", cascade="all, delete-orphan")
    group_assignments: Mapped[list[ProjectGroup]] = relationship(back_populates="project", cascade="all, delete-orphan")
    suites: Mapped[list[TestSuite]] = relationship(back_populates="project", cascade="all, delete-orphan")
    plans: Mapped[list[TestPlan]] = relationship(back_populates="project", cascade="all, delete-orphan")
    executions: Mapped[list[TestExecution]] = relationship(back_populates="project", cascade="all, delete-orphan")
    versions: Mapped[list[ProjectVersion]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    added_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="project_memberships")


class ProjectGroup(Base):
    __tablename__ = "project_groups"
    __table_args__ = (UniqueConstraint("project_id", "group_id", name="uq_project_groups_project_group"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    added_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="group_assignments")
    group: Mapped["Group"] = relationship(back_populates="project_assignments")  # noqa: F821
