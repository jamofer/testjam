from __future__ import annotations

from datetime import datetime
from sqlalchemy import ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testjam.database import Base
from testjam.models._types import UTCDateTime


class Bug(Base):
    __tablename__ = "bugs"
    __table_args__ = (
        UniqueConstraint("project_id", "number", name="uq_bug_project_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open", index=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)

    result_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_results.id", ondelete="SET NULL"), nullable=True
    )
    execution_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_executions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    version_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_versions.id", ondelete="SET NULL"), nullable=True
    )
    environment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    external_ticket_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now(), onupdate=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="bugs")  # noqa: F821
    assigned_to: Mapped["User | None"] = relationship(foreign_keys=[assigned_to_id])  # noqa: F821
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_id])  # noqa: F821
    updated_by: Mapped["User | None"] = relationship(foreign_keys=[updated_by_id])  # noqa: F821
    result: Mapped["TestResult | None"] = relationship(foreign_keys=[result_id])  # noqa: F821
    execution: Mapped["TestExecution | None"] = relationship(foreign_keys=[execution_id])  # noqa: F821
    version: Mapped["ProjectVersion | None"] = relationship(foreign_keys=[version_id])  # noqa: F821
    comments: Mapped[list["BugComment"]] = relationship(
        back_populates="bug",
        cascade="all, delete-orphan",
        order_by="BugComment.created_at.asc(), BugComment.id.asc()",
    )
    attachments: Mapped[list["BugAttachment"]] = relationship(
        back_populates="bug", cascade="all, delete-orphan"
    )
    history: Mapped[list["BugStatusHistory"]] = relationship(
        back_populates="bug",
        cascade="all, delete-orphan",
        order_by="BugStatusHistory.changed_at.asc(), BugStatusHistory.id.asc()",
    )
    links: Mapped[list["BugLink"]] = relationship(
        back_populates="bug",
        cascade="all, delete-orphan",
        order_by="BugLink.created_at.asc(), BugLink.id.asc()",
        foreign_keys="BugLink.bug_id",
    )


class BugComment(Base):
    __tablename__ = "bug_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bug_id: Mapped[int] = mapped_column(
        ForeignKey("bugs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now(), onupdate=func.now()
    )

    bug: Mapped[Bug] = relationship(back_populates="comments")
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_id])  # noqa: F821


class BugAttachment(Base):
    __tablename__ = "bug_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bug_id: Mapped[int] = mapped_column(
        ForeignKey("bugs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    uploaded_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    bug: Mapped[Bug] = relationship(back_populates="attachments")
    uploaded_by: Mapped["User | None"] = relationship(foreign_keys=[uploaded_by_id])  # noqa: F821


class BugLink(Base):
    __tablename__ = "bug_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bug_id: Mapped[int] = mapped_column(
        ForeignKey("bugs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    execution_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_executions.id", ondelete="SET NULL"), nullable=True
    )
    test_case_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_cases.id", ondelete="SET NULL"), nullable=True
    )
    test_step_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_steps.id", ondelete="SET NULL"), nullable=True
    )
    target_bug_id: Mapped[int | None] = mapped_column(
        ForeignKey("bugs.id", ondelete="SET NULL"), nullable=True
    )
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())

    bug: Mapped[Bug] = relationship(back_populates="links", foreign_keys=[bug_id])
    execution: Mapped["TestExecution | None"] = relationship(foreign_keys=[execution_id])  # noqa: F821
    test_case: Mapped["TestCase | None"] = relationship(foreign_keys=[test_case_id])  # noqa: F821
    test_step: Mapped["TestStep | None"] = relationship(foreign_keys=[test_step_id])  # noqa: F821
    target_bug: Mapped["Bug | None"] = relationship(foreign_keys=[target_bug_id])
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_id])  # noqa: F821


class BugStatusHistory(Base):
    __tablename__ = "bug_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bug_id: Mapped[int] = mapped_column(
        ForeignKey("bugs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    to_status: Mapped[str] = mapped_column(String(16), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changed_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())

    bug: Mapped[Bug] = relationship(back_populates="history")
    changed_by: Mapped["User | None"] = relationship(foreign_keys=[changed_by_id])  # noqa: F821
