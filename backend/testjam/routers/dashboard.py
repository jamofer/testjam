from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from testjam.auth.dependencies import require_project_access
from testjam.database import get_db
from testjam.models.execution import TestExecution, TestResult
from testjam.models.testcase import TestCase, TestSuite
from testjam.models.testplan import TestPlan
from testjam.models.user import User
from testjam.schemas.dashboard import (
    CountsCard,
    DashboardOut,
    PassRateCard,
    PassRatePoint,
    RecentExecutionItem,
    RecentExecutionsCard,
    TopFailCard,
    TopFailCase,
)

ALLOWED_RANGES = {7, 30, 90}
ALL_CARDS = {"counts", "pass_rate", "top_fail", "recent_executions"}
RECENT_LIMIT = 5
TOP_FAIL_LIMIT = 5
IN_FLIGHT_STATUSES = ("pending", "in_progress")
RESULT_STATUSES = ("passed", "failed", "blocked", "not_run")

router = APIRouter(prefix="/projects", tags=["Dashboard"])


@router.get("/{id}/dashboard", response_model=DashboardOut)
def get_dashboard(
    id: int,
    range: int = Query(30, description="Window in days. One of 7, 30, 90."),
    cards: str | None = Query(None, description="Comma-separated card names to include."),
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
) -> DashboardOut:
    if range not in ALLOWED_RANGES:
        raise HTTPException(status_code=400, detail="range must be one of 7, 30, 90")

    requested = _parse_cards(cards)
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=range)

    payload = DashboardOut(range_days=range, generated_at=now)
    if "counts" in requested:
        payload.counts = _counts_card(db, id, since)
    if "pass_rate" in requested:
        payload.pass_rate = _pass_rate_card(db, id, since)
    if "top_fail" in requested:
        payload.top_fail = _top_fail_card(db, id, since)
    if "recent_executions" in requested:
        payload.recent_executions = _recent_executions_card(db, id, since)
    return payload


def _parse_cards(raw: str | None) -> set[str]:
    if not raw:
        return set(ALL_CARDS)
    requested = {c.strip() for c in raw.split(",") if c.strip()}
    unknown = requested - ALL_CARDS
    if unknown:
        raise HTTPException(status_code=400, detail=f"unknown cards: {sorted(unknown)}")
    return requested


def _counts_card(db: Session, project_id: int, since: datetime) -> CountsCard:
    suites = db.query(func.count(TestSuite.id)).filter(TestSuite.project_id == project_id).scalar() or 0
    cases = (
        db.query(func.count(TestCase.id))
        .join(TestSuite, TestCase.suite_id == TestSuite.id)
        .filter(TestSuite.project_id == project_id)
        .scalar() or 0
    )
    plans = db.query(func.count(TestPlan.id)).filter(TestPlan.project_id == project_id).scalar() or 0
    in_flight = (
        db.query(func.count(TestExecution.id))
        .filter(
            TestExecution.project_id == project_id,
            TestExecution.status.in_(IN_FLIGHT_STATUSES),
        )
        .scalar() or 0
    )
    in_range = (
        db.query(func.count(TestExecution.id))
        .filter(
            TestExecution.project_id == project_id,
            TestExecution.created_at >= since,
        )
        .scalar() or 0
    )
    return CountsCard(
        suites=suites,
        cases=cases,
        plans=plans,
        executions_in_flight=in_flight,
        executions_in_range=in_range,
    )


def _pass_rate_card(db: Session, project_id: int, since: datetime) -> PassRateCard:
    rows = (
        db.query(TestExecution.created_at, TestResult.status, func.count(TestResult.id))
        .join(TestResult, TestResult.execution_id == TestExecution.id)
        .filter(
            TestExecution.project_id == project_id,
            TestExecution.created_at >= since,
        )
        .group_by(TestExecution.created_at, TestResult.status)
        .all()
    )

    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {s: 0 for s in RESULT_STATUSES})
    totals = {s: 0 for s in RESULT_STATUSES}
    for created_at, status, count in rows:
        day = created_at.date().isoformat()
        if status in totals:
            buckets[day][status] += count
            totals[status] += count

    series = [
        PassRatePoint(date=day, **buckets[day])
        for day in sorted(buckets.keys())
    ]
    completed = totals["passed"] + totals["failed"]
    overall = (totals["passed"] / completed) if completed else None
    total_results = sum(totals.values())
    return PassRateCard(series=series, overall_pass_rate=overall, total_results=total_results)


def _top_fail_card(db: Session, project_id: int, since: datetime) -> TopFailCard:
    rows = (
        db.query(
            TestCase.id,
            TestCase.name,
            TestSuite.id,
            TestSuite.name,
            func.count(TestResult.id).label("fail_count"),
        )
        .join(TestSuite, TestCase.suite_id == TestSuite.id)
        .join(TestResult, TestResult.test_case_id == TestCase.id)
        .join(TestExecution, TestExecution.id == TestResult.execution_id)
        .filter(
            TestSuite.project_id == project_id,
            TestResult.status == "failed",
            TestExecution.created_at >= since,
        )
        .group_by(TestCase.id, TestCase.name, TestSuite.id, TestSuite.name)
        .order_by(func.count(TestResult.id).desc(), TestCase.id.asc())
        .limit(TOP_FAIL_LIMIT)
        .all()
    )
    cases = [
        TopFailCase(case_id=cid, case_name=cname, suite_id=sid, suite_name=sname, fail_count=fail_count)
        for cid, cname, sid, sname, fail_count in rows
    ]
    return TopFailCard(cases=cases)


def _recent_executions_card(db: Session, project_id: int, since: datetime) -> RecentExecutionsCard:
    executions = (
        db.query(TestExecution)
        .filter(
            TestExecution.project_id == project_id,
            TestExecution.created_at >= since,
        )
        .order_by(TestExecution.created_at.desc())
        .limit(RECENT_LIMIT)
        .all()
    )
    if not executions:
        return RecentExecutionsCard(executions=[])

    ids = [ex.id for ex in executions]
    status_rows = (
        db.query(TestResult.execution_id, TestResult.status, func.count(TestResult.id))
        .filter(TestResult.execution_id.in_(ids))
        .group_by(TestResult.execution_id, TestResult.status)
        .all()
    )
    counts: dict[int, dict[str, int]] = {eid: {s: 0 for s in RESULT_STATUSES} for eid in ids}
    for eid, status, count in status_rows:
        if status in counts[eid]:
            counts[eid][status] = count

    items: list[RecentExecutionItem] = []
    for ex in executions:
        items.append(RecentExecutionItem(
            id=ex.id,
            title=ex.title,
            status=ex.status,
            version=ex.version,
            environment=ex.environment,
            created_at=ex.created_at,
            started_at=ex.started_at,
            finished_at=ex.finished_at,
            duration_ms=_duration_ms(ex.started_at, ex.finished_at),
            **counts[ex.id],
        ))
    return RecentExecutionsCard(executions=items)


def _duration_ms(started: datetime | None, finished: datetime | None) -> int | None:
    if not started or not finished:
        return None
    return int((finished - started).total_seconds() * 1000)
