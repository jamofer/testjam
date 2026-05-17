"""Resolve enriched chain for a bug (or a BugLink): execution + breadcrumb.

Bug stores raw FKs (`result_id`, `execution_id`). This service walks the
chain so the frontend can render clickable links without N round-trips.
The same `suite_path_for_case` helper is reused by per-link enrichment.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from testjam.models.bug import Bug
from testjam.models.execution import TestExecution, TestResult
from testjam.models.testcase import TestCase, TestSuite
from testjam.models.version import ProjectVersion
from testjam.schemas.bug import (
    BugContextExecution,
    BugContextNode,
    BugContextOut,
    BugContextStep,
)


def build_bug_context(db: Session, bug: Bug) -> BugContextOut:
    execution = _execution_for(db, bug)
    case = _case_for(db, bug)
    suite_path = suite_path_for_case(db, case.suite_id) if case else []
    version = db.get(ProjectVersion, bug.version_id) if bug.version_id else None

    return BugContextOut(
        execution=(
            BugContextExecution(id=execution.id, title=execution.title)
            if execution
            else None
        ),
        suite_path=[BugContextNode(id=s.id, name=s.name) for s in suite_path],
        case=BugContextNode(id=case.id, name=case.name) if case else None,
        step=None,
        version_id=bug.version_id,
        version_name=version.name if version else None,
        environment=bug.environment,
    )


def suite_path_for_case(db: Session, suite_id: int | None) -> list[TestSuite]:
    if suite_id is None:
        return []
    path: list[TestSuite] = []
    current = db.get(TestSuite, suite_id)
    seen: set[int] = set()
    while current is not None and current.id not in seen:
        seen.add(current.id)
        path.append(current)
        if current.parent_suite_id is None:
            break
        current = db.get(TestSuite, current.parent_suite_id)
    path.reverse()
    return path


def _execution_for(db: Session, bug: Bug) -> TestExecution | None:
    if bug.execution_id is None:
        return None
    return db.get(TestExecution, bug.execution_id)


def _case_for(db: Session, bug: Bug) -> TestCase | None:
    if bug.result_id is None:
        return None
    result = db.get(TestResult, bug.result_id)
    if result is None:
        return None
    return db.get(TestCase, result.test_case_id)
