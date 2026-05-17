"""Autocomplete search backing the mention dropdown.

Returns up to ``limit`` candidates per kind, matched against either the
numeric id or the name/title (case-insensitive substring). Users are scoped to
project members; bugs / executions / cases are scoped to the current project.
"""
from __future__ import annotations

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from testjam.models.bug import Bug
from testjam.models.execution import TestExecution, TestResult
from testjam.models.project import ProjectMember
from testjam.models.testcase import TestCase, TestStep, TestSuite
from testjam.models.user import User
from testjam.schemas.mention import MentionSearchHit


def search_users(db: Session, project_id: int, query: str, limit: int) -> list[MentionSearchHit]:
    base = (
        db.query(User)
        .join(ProjectMember, ProjectMember.user_id == User.id)
        .filter(ProjectMember.project_id == project_id, User.is_active == True)  # noqa: E712
    )
    rows = _apply_text_filter(base, [User.username, User.full_name], query).limit(limit).all()
    return [
        MentionSearchHit(
            kind="user",
            id=user.id,
            slug=user.username,
            label=user.full_name or user.username,
            description=f"@{user.username}",
            url=f"/users/{user.username}",
        )
        for user in rows
    ]


def search_bugs(db: Session, project_id: int, query: str, limit: int) -> list[MentionSearchHit]:
    base = db.query(Bug).filter(Bug.project_id == project_id)
    rows = (
        _apply_numeric_or_text(base, Bug.number, [Bug.title], query)
        .order_by(Bug.number.desc())
        .limit(limit)
        .all()
    )
    return [
        MentionSearchHit(
            kind="bug",
            id=bug.number,
            label=f"#{bug.number} {bug.title}",
            description=bug.status,
            url=f"/projects/{project_id}/bugs/{bug.number}",
        )
        for bug in rows
    ]


def search_executions(db: Session, project_id: int, query: str, limit: int) -> list[MentionSearchHit]:
    base = db.query(TestExecution).filter(TestExecution.project_id == project_id)
    rows = (
        _apply_numeric_or_text(base, TestExecution.id, [TestExecution.title], query)
        .order_by(TestExecution.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        MentionSearchHit(
            kind="execution",
            id=execution.id,
            label=f"!{execution.id} {execution.title}",
            description=execution.environment,
            url=f"/executions/{execution.id}/run",
        )
        for execution in rows
    ]


def search_cases(db: Session, project_id: int, query: str, limit: int) -> list[MentionSearchHit]:
    base = (
        db.query(TestCase)
        .join(TestSuite, TestSuite.id == TestCase.suite_id)
        .options(selectinload(TestCase.suite))
        .filter(TestSuite.project_id == project_id)
    )
    rows = (
        _apply_numeric_or_text(base, TestCase.id, [TestCase.name], query)
        .order_by(TestCase.updated_at.desc())
        .limit(limit)
        .all()
    )
    return [
        MentionSearchHit(
            kind="case",
            id=case.id,
            label=f"~{case.id} {case.name}",
            description=case.suite.name if case.suite else None,
            url=f"/cases/{case.id}",
        )
        for case in rows
    ]


def search_results(
    db: Session, project_id: int, execution_id: int, query: str, limit: int,
) -> list[MentionSearchHit]:
    base = (
        db.query(TestResult, TestCase.name)
        .join(TestExecution, TestExecution.id == TestResult.execution_id)
        .join(TestCase, TestCase.id == TestResult.test_case_id)
        .filter(
            TestExecution.project_id == project_id,
            TestResult.execution_id == execution_id,
        )
    )
    rows = (
        _apply_numeric_or_text(base, TestResult.id, [TestCase.name], query)
        .order_by(TestResult.id.asc())
        .limit(limit)
        .all()
    )
    return [
        MentionSearchHit(
            kind="result",
            id=execution_id,
            sub_ids=[result.id],
            label=f"!{execution_id}/{result.id} {case_name}",
            description=result.status,
            url=f"/executions/{execution_id}/run#result-{result.id}",
        )
        for result, case_name in rows
    ]


def search_step_results(
    db: Session, project_id: int, execution_id: int, result_id: int, query: str, limit: int,
) -> list[MentionSearchHit]:
    result = (
        db.query(TestResult)
        .join(TestExecution, TestExecution.id == TestResult.execution_id)
        .filter(
            TestResult.id == result_id,
            TestResult.execution_id == execution_id,
            TestExecution.project_id == project_id,
        )
        .first()
    )
    if result is None:
        return []
    base = db.query(TestStep).filter(TestStep.test_case_id == result.test_case_id)
    rows = (
        _apply_numeric_or_text(base, TestStep.id, [TestStep.action], query)
        .order_by(TestStep.order.asc(), TestStep.id.asc())
        .limit(limit)
        .all()
    )
    return [
        MentionSearchHit(
            kind="step_result",
            id=execution_id,
            sub_ids=[result_id, step.id],
            label=f"!{execution_id}/{result_id}/{step.id} {step.action}",
            description=None,
            url=f"/executions/{execution_id}/run#result-{result_id}-step-{step.id}",
        )
        for step in rows
    ]


def _apply_text_filter(query_obj, columns, raw: str):
    if not raw:
        return query_obj
    pattern = f"%{raw.lower()}%"
    clauses = [func.lower(func.coalesce(column, "")).like(pattern) for column in columns]
    return query_obj.filter(or_(*clauses))


def _apply_numeric_or_text(query_obj, numeric_column, text_columns, raw: str):
    if not raw:
        return query_obj
    pattern = f"%{raw.lower()}%"
    text_clauses = [func.lower(func.coalesce(column, "")).like(pattern) for column in text_columns]
    try:
        numeric_value = int(raw)
    except ValueError:
        return query_obj.filter(or_(*text_clauses))
    return query_obj.filter(or_(numeric_column == numeric_value, *text_clauses))
