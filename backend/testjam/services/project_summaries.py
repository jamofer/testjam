"""Build `ProjectOut` rows with a fixed number of queries, whatever the project count."""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from testjam.models.execution import TestExecution, TestResult
from testjam.models.project import Project
from testjam.models.testcase import TestCase, TestSuite
from testjam.schemas.project import ProjectOut, RecentExecutionSummary

RECENT_EXECUTIONS_PER_PROJECT = 10
SUMMARY_STATUSES = ("passed", "failed", "blocked", "not_run")


def project_summaries(db: Session, projects: list[Project]) -> list[ProjectOut]:
    if not projects:
        return []
    project_ids = [project.id for project in projects]
    suite_counts = _suite_counts(db, project_ids)
    case_counts = _case_counts(db, project_ids)
    execution_stats = _execution_stats(db, project_ids)
    recent_executions = _recent_executions(db, project_ids)
    return [
        ProjectOut(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
            archived_at=project.archived_at,
            suite_count=suite_counts.get(project.id, 0),
            case_count=case_counts.get(project.id, 0),
            execution_count=execution_stats.get(project.id, (0, None))[0],
            last_execution_at=execution_stats.get(project.id, (0, None))[1],
            recent_executions=recent_executions.get(project.id, []),
        )
        for project in projects
    ]


def project_summary(db: Session, project: Project) -> ProjectOut:
    return project_summaries(db, [project])[0]


def _suite_counts(db: Session, project_ids: list[int]) -> dict[int, int]:
    rows = (
        db.query(TestSuite.project_id, func.count(TestSuite.id))
        .filter(TestSuite.project_id.in_(project_ids))
        .group_by(TestSuite.project_id)
    )
    return dict(rows.all())


def _case_counts(db: Session, project_ids: list[int]) -> dict[int, int]:
    rows = (
        db.query(TestSuite.project_id, func.count(TestCase.id))
        .join(TestCase, TestCase.suite_id == TestSuite.id)
        .filter(TestSuite.project_id.in_(project_ids))
        .group_by(TestSuite.project_id)
    )
    return dict(rows.all())


def _execution_stats(db: Session, project_ids: list[int]) -> dict[int, tuple]:
    rows = (
        db.query(TestExecution.project_id, func.count(TestExecution.id), func.max(TestExecution.created_at))
        .filter(TestExecution.project_id.in_(project_ids))
        .group_by(TestExecution.project_id)
    )
    return {project_id: (count, last_created_at) for project_id, count, last_created_at in rows.all()}


def _recent_executions(db: Session, project_ids: list[int]) -> dict[int, list[RecentExecutionSummary]]:
    position = (
        func.row_number()
        .over(partition_by=TestExecution.project_id, order_by=(TestExecution.created_at.desc(), TestExecution.id.desc()))
        .label("position")
    )
    ranked = (
        db.query(TestExecution.id.label("execution_id"), position)
        .filter(TestExecution.project_id.in_(project_ids))
        .subquery()
    )
    executions = (
        db.query(TestExecution)
        .join(ranked, ranked.c.execution_id == TestExecution.id)
        .filter(ranked.c.position <= RECENT_EXECUTIONS_PER_PROJECT)
        .order_by(TestExecution.project_id, ranked.c.position)
        .all()
    )
    status_counts = _result_status_counts(db, [execution.id for execution in executions])
    by_project: dict[int, list[RecentExecutionSummary]] = defaultdict(list)
    for execution in executions:
        by_project[execution.project_id].append(RecentExecutionSummary(
            id=execution.id,
            title=execution.title,
            status=execution.status,
            started_at=execution.started_at,
            **status_counts.get(execution.id, {}),
        ))
    return by_project


def _result_status_counts(db: Session, execution_ids: list[int]) -> dict[int, dict[str, int]]:
    if not execution_ids:
        return {}
    rows = (
        db.query(TestResult.execution_id, TestResult.status, func.count(TestResult.id))
        .filter(TestResult.execution_id.in_(execution_ids), TestResult.status.in_(SUMMARY_STATUSES))
        .group_by(TestResult.execution_id, TestResult.status)
    )
    counts: dict[int, dict[str, int]] = defaultdict(dict)
    for execution_id, status, count in rows.all():
        counts[execution_id][status] = count
    return counts
