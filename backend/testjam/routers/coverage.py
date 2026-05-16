from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from testjam.auth.dependencies import require_project_access
from testjam.database import get_db
from testjam.models.execution import TestExecution, TestResult
from testjam.models.testcase import TestCase, TestSuite
from testjam.models.user import User
from testjam.models.version import ProjectVersion
from testjam.schemas.coverage import CoverageCase, CoverageCell, CoverageMatrix

router = APIRouter(prefix="/projects", tags=["Coverage"])

STATUS_PRIORITY = {"failed": 4, "blocked": 3, "passed": 2, "not_run": 1}


@router.get("/{id}/coverage/matrix", response_model=CoverageMatrix)
def coverage_matrix(
    id: int,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
) -> CoverageMatrix:
    version_query = db.query(ProjectVersion).filter(ProjectVersion.project_id == id)
    if not include_archived:
        version_query = version_query.filter(ProjectVersion.status != "archived")
    versions = version_query.order_by(ProjectVersion.status.asc(), ProjectVersion.created_at.desc()).all()

    cases = (
        db.query(TestCase.id, TestCase.name, TestSuite.id, TestSuite.name)
        .join(TestSuite, TestCase.suite_id == TestSuite.id)
        .filter(TestSuite.project_id == id)
        .order_by(TestSuite.name.asc(), TestCase.name.asc())
        .all()
    )

    rows = (
        db.query(
            TestResult.test_case_id,
            TestExecution.version_id,
            TestResult.status,
            TestResult.executed_at,
            TestExecution.started_at,
            TestExecution.created_at,
            TestResult.execution_id,
        )
        .join(TestExecution, TestExecution.id == TestResult.execution_id)
        .filter(
            TestExecution.project_id == id,
            TestExecution.version_id.is_not(None),
        )
        .all()
    )

    best: dict[tuple[int, int], tuple] = {}
    for case_id, version_id, status, executed_at, started_at, created_at, execution_id in rows:
        if status == "not_run":
            continue
        ts = executed_at or started_at or created_at
        key = (case_id, version_id)
        current = best.get(key)
        if current is None:
            best[key] = (ts, status, execution_id)
            continue
        current_ts = current[0]
        if ts is not None and (current_ts is None or ts > current_ts):
            best[key] = (ts, status, execution_id)

    cells = [
        CoverageCell(case_id=case_id, version_id=version_id, status=status, last_run_at=ts, execution_id=execution_id)
        for (case_id, version_id), (ts, status, execution_id) in best.items()
    ]
    cases_out = [
        CoverageCase(id=cid, name=cname, suite_id=sid, suite_name=sname)
        for cid, cname, sid, sname in cases
    ]
    return CoverageMatrix(versions=versions, cases=cases_out, cells=cells)
