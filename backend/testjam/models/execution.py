from __future__ import annotations

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testjam.database import Base


class TestExecution(Base):
    __tablename__ = "test_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    test_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_plans.id", ondelete="SET NULL"), nullable=True
    )
    version_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_versions.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    environment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    triggered_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="executions")
    test_plan: Mapped[TestPlan | None] = relationship(back_populates="executions")
    project_version: Mapped[ProjectVersion | None] = relationship(back_populates="executions")
    assigned_to: Mapped[User | None] = relationship()
    results: Mapped[list[TestResult]] = relationship(
        back_populates="execution", cascade="all, delete-orphan"
    )
    attachments: Mapped[list[ExecutionAttachment]] = relationship(
        back_populates="execution", cascade="all, delete-orphan"
    )


class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    execution_id: Mapped[int] = mapped_column(ForeignKey("test_executions.id", ondelete="CASCADE"))
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="not_run")
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    execution: Mapped[TestExecution] = relationship(back_populates="results")
    test_case: Mapped[TestCase] = relationship()
    step_results: Mapped[list[TestStepResult]] = relationship(
        back_populates="test_result", cascade="all, delete-orphan"
    )
    attachments: Mapped[list[ResultAttachment]] = relationship(
        back_populates="result", cascade="all, delete-orphan"
    )


class TestStepResult(Base):
    __tablename__ = "test_step_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    test_result_id: Mapped[int] = mapped_column(ForeignKey("test_results.id", ondelete="CASCADE"))
    step_id: Mapped[int] = mapped_column(ForeignKey("test_steps.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="not_run")
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    # markdown execution log — populated by automated runners (Robot Framework, CI)
    log_output: Mapped[str | None] = mapped_column(Text, nullable=True)

    test_result: Mapped[TestResult] = relationship(back_populates="step_results")
    step: Mapped[TestStep] = relationship()


class ResultAttachment(Base):
    __tablename__ = "result_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    result_id: Mapped[int] = mapped_column(ForeignKey("test_results.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    uploaded_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    result: Mapped[TestResult] = relationship(back_populates="attachments")


class ExecutionAttachment(Base):
    __tablename__ = "execution_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    execution_id: Mapped[int] = mapped_column(ForeignKey("test_executions.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    uploaded_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    execution: Mapped[TestExecution] = relationship(back_populates="attachments")
