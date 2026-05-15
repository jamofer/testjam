from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class CountsCard(BaseModel):
    suites: int
    cases: int
    plans: int
    executions_in_flight: int
    executions_in_range: int


class PassRatePoint(BaseModel):
    date: date
    passed: int
    failed: int
    blocked: int
    not_run: int


class PassRateCard(BaseModel):
    series: list[PassRatePoint]
    overall_pass_rate: float | None
    total_results: int


class TopFailCase(BaseModel):
    case_id: int
    case_name: str
    suite_id: int
    suite_name: str
    fail_count: int


class TopFailCard(BaseModel):
    cases: list[TopFailCase]


class RecentExecutionItem(BaseModel):
    id: int
    title: str
    status: str
    version: str | None
    environment: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    passed: int
    failed: int
    blocked: int
    not_run: int


class RecentExecutionsCard(BaseModel):
    executions: list[RecentExecutionItem]


class DashboardOut(BaseModel):
    range_days: int
    generated_at: datetime
    counts: CountsCard | None = None
    pass_rate: PassRateCard | None = None
    top_fail: TopFailCard | None = None
    recent_executions: RecentExecutionsCard | None = None
