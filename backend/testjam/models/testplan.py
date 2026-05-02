from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testjam.database import Base

# Association table — plain Column() required here, not mapped_column()
test_plan_cases = Table(
    "test_plan_cases",
    Base.metadata,
    Column("test_plan_id", Integer, ForeignKey("test_plans.id", ondelete="CASCADE"), primary_key=True),
    Column("test_case_id", Integer, ForeignKey("test_cases.id", ondelete="CASCADE"), primary_key=True),
)


class TestPlan(Base):
    __tablename__ = "test_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    project: Mapped[Project] = relationship(back_populates="plans")
    cases: Mapped[list[TestCase]] = relationship(secondary=test_plan_cases)
    executions: Mapped[list[TestExecution]] = relationship(back_populates="test_plan")
