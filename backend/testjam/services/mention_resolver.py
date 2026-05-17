"""Resolve mention tokens into enriched payloads.

Given a list of parsed tokens (kind + id/slug + sub_ids) and the project the
caller is browsing, the resolver looks up each target and returns a label, a
URL the frontend can navigate to, and an ``accessible`` flag.

Permission rule (strict): a token resolves only when the target belongs to the
current project. Cross-project mentions are not yet supported by the parser,
so anything that points outside this project is returned as ``accessible: False``.

User mentions resolve as long as the user exists; ``accessible`` reflects
whether that user is a project member. Inaccessible user mentions still render
as plain text without notification fan-out.
"""
from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from testjam.models.bug import Bug
from testjam.models.execution import TestExecution, TestResult, TestStepResult
from testjam.models.project import ProjectMember
from testjam.models.testcase import TestCase, TestSuite, TestStep
from testjam.models.user import User
from testjam.schemas.mention import MentionTokenIn, ResolvedMentionOut
from testjam.services.permissions import effective_role


def resolve(db: Session, project_id: int, tokens: list[MentionTokenIn]) -> list[ResolvedMentionOut]:
    return [_resolve_one(db, project_id, token) for token in tokens]


def _resolve_one(
    db: Session, project_id: int, token: MentionTokenIn,
) -> ResolvedMentionOut:
    if token.kind == "user" and token.slug:
        return _resolve_user(db, project_id, token.slug)
    if token.kind == "bug" and token.id is not None:
        return _resolve_bug(db, project_id, token.id)
    if token.kind == "execution" and token.id is not None:
        return _resolve_execution(db, project_id, token.id)
    if token.kind == "result" and token.id is not None and len(token.sub_ids) >= 1:
        return _resolve_result(db, project_id, token.id, token.sub_ids[0])
    if token.kind == "step_result" and token.id is not None and len(token.sub_ids) >= 2:
        return _resolve_step_result(
            db, project_id, token.id, token.sub_ids[0], token.sub_ids[1],
        )
    if token.kind == "case" and token.id is not None:
        return _resolve_case(db, project_id, token.id)
    return _unresolved(token)


def _resolve_user(db: Session, project_id: int, slug: str) -> ResolvedMentionOut:
    user = db.query(User).filter(User.username == slug).first()
    if user is None:
        return ResolvedMentionOut(kind="user", slug=slug, accessible=False)
    accessible = effective_role(db, user.id, project_id) is not None or user.is_admin
    return ResolvedMentionOut(
        kind="user",
        slug=user.username,
        id=user.id,
        label=user.full_name or user.username,
        description=f"@{user.username}",
        url=f"/users/{user.username}",
        accessible=accessible,
    )


def _resolve_bug(db: Session, project_id: int, number: int) -> ResolvedMentionOut:
    bug = (
        db.query(Bug)
        .filter(Bug.project_id == project_id, Bug.number == number)
        .first()
    )
    if bug is None:
        return ResolvedMentionOut(kind="bug", id=number, accessible=False)
    return ResolvedMentionOut(
        kind="bug",
        id=bug.number,
        label=f"#{bug.number} {bug.title}",
        description=bug.status,
        url=f"/projects/{project_id}/bugs/{bug.number}",
        accessible=True,
    )


def _resolve_execution(db: Session, project_id: int, execution_id: int) -> ResolvedMentionOut:
    execution = db.get(TestExecution, execution_id)
    if execution is None or execution.project_id != project_id:
        return ResolvedMentionOut(kind="execution", id=execution_id, accessible=False)
    return ResolvedMentionOut(
        kind="execution",
        id=execution.id,
        label=f"!{execution.id} {execution.title}",
        description=execution.environment,
        url=f"/executions/{execution.id}/run",
        accessible=True,
    )


def _resolve_result(
    db: Session, project_id: int, execution_id: int, result_id: int,
) -> ResolvedMentionOut:
    result = (
        db.query(TestResult)
        .options(selectinload(TestResult.execution), selectinload(TestResult.test_case))
        .filter(TestResult.id == result_id, TestResult.execution_id == execution_id)
        .first()
    )
    if result is None or result.execution.project_id != project_id:
        return ResolvedMentionOut(
            kind="result", id=execution_id, sub_ids=[result_id], accessible=False,
        )
    case_name = result.test_case.name if result.test_case else f"result {result.id}"
    return ResolvedMentionOut(
        kind="result",
        id=execution_id,
        sub_ids=[result.id],
        label=f"!{execution_id}/{result.id} {case_name}",
        description=result.status,
        url=f"/executions/{execution_id}/run#result-{result.id}",
        accessible=True,
    )


def _resolve_step_result(
    db: Session, project_id: int, execution_id: int, result_id: int, step_result_id: int,
) -> ResolvedMentionOut:
    step_result = (
        db.query(TestStepResult)
        .options(
            selectinload(TestStepResult.test_result).selectinload(TestResult.execution),
            selectinload(TestStepResult.step),
        )
        .filter(
            TestStepResult.id == step_result_id,
            TestStepResult.test_result_id == result_id,
        )
        .first()
    )
    if (
        step_result is None
        or step_result.test_result.execution_id != execution_id
        or step_result.test_result.execution.project_id != project_id
    ):
        return ResolvedMentionOut(
            kind="step_result", id=execution_id,
            sub_ids=[result_id, step_result_id], accessible=False,
        )
    step_action = step_result.step.action if step_result.step else f"step {step_result.id}"
    return ResolvedMentionOut(
        kind="step_result",
        id=execution_id,
        sub_ids=[result_id, step_result.id],
        label=f"!{execution_id}/{result_id}/{step_result.id} {step_action}",
        description=step_result.status,
        url=f"/executions/{execution_id}/run#step-{step_result.id}",
        accessible=True,
    )


def _resolve_case(db: Session, project_id: int, case_id: int) -> ResolvedMentionOut:
    case = (
        db.query(TestCase)
        .options(selectinload(TestCase.suite))
        .filter(TestCase.id == case_id)
        .first()
    )
    if case is None or case.suite.project_id != project_id:
        return ResolvedMentionOut(kind="case", id=case_id, accessible=False)
    return ResolvedMentionOut(
        kind="case",
        id=case.id,
        label=f"~{case.id} {case.name}",
        description=case.suite.name if case.suite else None,
        url=f"/cases/{case.id}",
        accessible=True,
    )


def _unresolved(token: MentionTokenIn) -> ResolvedMentionOut:
    return ResolvedMentionOut(
        kind=token.kind,
        slug=token.slug,
        id=token.id,
        sub_ids=token.sub_ids,
        accessible=False,
    )
