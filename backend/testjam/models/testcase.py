from __future__ import annotations

from datetime import datetime
from sqlalchemy import ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testjam.database import Base
from testjam.models._types import UTCDateTime


class TestSuite(Base):
    __tablename__ = "test_suites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    parent_suite_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_suites.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), onupdate=func.now())

    project: Mapped[Project] = relationship(back_populates="suites")
    children: Mapped[list[TestSuite]] = relationship(back_populates="parent")
    parent: Mapped[TestSuite | None] = relationship(
        back_populates="children", remote_side="TestSuite.id"
    )
    cases: Mapped[list[TestCase]] = relationship(back_populates="suite", cascade="all, delete-orphan")
    steps: Mapped[list[SuiteStep]] = relationship(
        back_populates="suite",
        cascade="all, delete-orphan",
        order_by="SuiteStep.order",
    )


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    suite_id: Mapped[int] = mapped_column(ForeignKey("test_suites.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    preconditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    setup: Mapped[str | None] = mapped_column(Text, nullable=True)
    teardown: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # used to match automated results (e.g. "tests/login.py::test_login" or "Suite.Test Name")
    external_id: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), onupdate=func.now())

    suite: Mapped[TestSuite] = relationship(back_populates="cases")
    steps: Mapped[list[TestStep]] = relationship(
        back_populates="test_case",
        cascade="all, delete-orphan",
        order_by="TestStep.order",
    )
    attachments: Mapped[list[Attachment]] = relationship(
        back_populates="test_case", cascade="all, delete-orphan"
    )
    revisions: Mapped[list["CaseRevision"]] = relationship(  # noqa: F821
        back_populates="test_case",
        cascade="all, delete-orphan",
        order_by="CaseRevision.created_at.desc(), CaseRevision.id.desc()",
    )
    comments: Mapped[list["CaseComment"]] = relationship(
        back_populates="test_case",
        cascade="all, delete-orphan",
        order_by="CaseComment.created_at.asc(), CaseComment.id.asc()",
    )
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_id])  # noqa: F821
    updated_by: Mapped["User | None"] = relationship(foreign_keys=[updated_by_id])  # noqa: F821


class CaseComment(Base):
    __tablename__ = "case_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    test_case_id: Mapped[int] = mapped_column(
        ForeignKey("test_cases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now(), onupdate=func.now()
    )

    test_case: Mapped[TestCase] = relationship(back_populates="comments")
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_id])  # noqa: F821


class TestStep(Base):
    __tablename__ = "test_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id", ondelete="CASCADE"))
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    # "setup" | "action" | "teardown"
    step_type: Mapped[str] = mapped_column(String(16), nullable=False, default="action")
    action: Mapped[str] = mapped_column(Text, nullable=False)
    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)

    test_case: Mapped[TestCase] = relationship(back_populates="steps")


class SuiteStep(Base):
    __tablename__ = "suite_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    suite_id: Mapped[int] = mapped_column(ForeignKey("test_suites.id", ondelete="CASCADE"))
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    # "setup" | "teardown"
    step_type: Mapped[str] = mapped_column(String(16), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)

    suite: Mapped[TestSuite] = relationship(back_populates="steps")


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    uploaded_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    test_case: Mapped[TestCase] = relationship(back_populates="attachments")
