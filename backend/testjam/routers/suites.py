from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user, require_project_access, require_writable_project_access
from testjam.database import get_db
from testjam.models.execution import TestResult
from testjam.models.testcase import SuiteStep, TestCase, TestSuite
from testjam.models.user import User
from testjam.schemas.testcase import (
    SuiteArchiveResult, SuiteDeleteImpact,
    SuiteStepCreate, SuiteStepOut, SuiteStepUpdate,
    TestSuiteCreate, TestSuiteOut, TestSuiteUpdate,
)


def _collect_subtree_suite_ids(db: Session, root_id: int) -> list[int]:
    visited: list[int] = []
    queue = [root_id]
    while queue:
        suite_id = queue.pop()
        visited.append(suite_id)
        children = db.query(TestSuite.id).filter(TestSuite.parent_suite_id == suite_id).all()
        queue.extend(row.id for row in children)
    return visited


def _subtree_case_ids(db: Session, suite_ids: list[int]) -> list[int]:
    if not suite_ids:
        return []
    rows = db.query(TestCase.id).filter(TestCase.suite_id.in_(suite_ids)).all()
    return [row.id for row in rows]

projects_router = APIRouter(prefix="/projects", tags=["TestSuites"])
suites_router = APIRouter(prefix="/suites", tags=["TestSuites"])


def _suite_out(suite: TestSuite) -> TestSuiteOut:
    return TestSuiteOut(
        **{c.name: getattr(suite, c.name) for c in suite.__table__.columns},
        child_suite_ids=[c.id for c in suite.children],
        test_case_ids=[tc.id for tc in suite.cases],
        steps=[SuiteStepOut.model_validate(s) for s in suite.steps],
    )


@projects_router.get("/{id}/suites", response_model=list[TestSuiteOut])
def list_suites(
    id: int,
    name: str | None = None,
    parent_suite_id: int | None = None,
    all: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    q = db.query(TestSuite).filter(TestSuite.project_id == id)
    if not all:
        if parent_suite_id is not None:
            q = q.filter(TestSuite.parent_suite_id == parent_suite_id)
        else:
            q = q.filter(TestSuite.parent_suite_id == None)
    if name is not None:
        q = q.filter(TestSuite.name == name)
    rows = q.order_by(TestSuite.order, TestSuite.id).all()
    return [_suite_out(s) for s in rows]


@projects_router.post("/{id}/suites", response_model=TestSuiteOut, status_code=status.HTTP_201_CREATED)
def create_suite(id: int, body: TestSuiteCreate, db: Session = Depends(get_db), _: User = Depends(require_writable_project_access)):
    duplicate = (
        db.query(TestSuite)
        .filter(
            TestSuite.project_id == id,
            TestSuite.name == body.name,
            TestSuite.parent_suite_id == body.parent_suite_id,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=409, detail=f"Suite '{body.name}' already exists")
    max_order = (
        db.query(TestSuite)
        .filter(TestSuite.project_id == id, TestSuite.parent_suite_id == body.parent_suite_id)
        .count()
    )
    suite = TestSuite(project_id=id, order=max_order + 1, **body.model_dump())
    db.add(suite)
    db.commit()
    db.refresh(suite)
    return _suite_out(suite)


@suites_router.get("/{id}", response_model=TestSuiteOut)
def get_suite(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    suite = db.get(TestSuite, id)
    if not suite:
        raise HTTPException(status_code=404, detail="Not found")
    return _suite_out(suite)


@suites_router.put("/{id}", response_model=TestSuiteOut)
def update_suite(id: int, body: TestSuiteUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    suite = db.get(TestSuite, id)
    if not suite:
        raise HTTPException(status_code=404, detail="Not found")
    if body.name is not None and body.name != suite.name:
        duplicate = (
            db.query(TestSuite)
            .filter(
                TestSuite.project_id == suite.project_id,
                TestSuite.name == body.name,
                TestSuite.parent_suite_id == suite.parent_suite_id,
                TestSuite.id != id,
            )
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail=f"Suite '{body.name}' already exists")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(suite, field, value)
    db.commit()
    db.refresh(suite)
    return _suite_out(suite)


@suites_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_suite(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    suite = db.get(TestSuite, id)
    if not suite:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(suite)
    db.commit()


@suites_router.get("/{id}/delete-impact", response_model=SuiteDeleteImpact)
def delete_suite_impact(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    suite = db.get(TestSuite, id)
    if not suite:
        raise HTTPException(status_code=404, detail="Not found")
    suite_ids = _collect_subtree_suite_ids(db, id)
    case_ids = _subtree_case_ids(db, suite_ids)
    if case_ids:
        results = db.query(TestResult.execution_id).filter(TestResult.test_case_id.in_(case_ids)).all()
        result_count = len(results)
        execution_count = len({row.execution_id for row in results})
    else:
        result_count = 0
        execution_count = 0
    return SuiteDeleteImpact(
        suite_count=len(suite_ids),
        case_count=len(case_ids),
        result_count=result_count,
        execution_count=execution_count,
    )


@suites_router.post("/{id}/archive", response_model=SuiteArchiveResult)
def archive_suite(id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    suite = db.get(TestSuite, id)
    if not suite:
        raise HTTPException(status_code=404, detail="Not found")
    suite_ids = _collect_subtree_suite_ids(db, id)
    cases = (
        db.query(TestCase)
        .filter(TestCase.suite_id.in_(suite_ids), TestCase.archived_at.is_(None))
        .all()
    )
    now = datetime.now(timezone.utc)
    for case in cases:
        case.archived_at = now
        case.updated_by_id = current.id
    db.commit()
    return SuiteArchiveResult(suite_count=len(suite_ids), archived_case_count=len(cases))


# ── Suite steps ────────────────────────────────────────────────────────────────

class StepReorder(BaseModel):
    step_ids: list[int]


class SuiteReorder(BaseModel):
    suite_ids: list[int]


@projects_router.post("/{id}/suites/reorder", response_model=list[TestSuiteOut])
def reorder_project_suites(
    id: int,
    body: SuiteReorder,
    parent_suite_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_writable_project_access),
):
    """Reorder siblings (suites sharing the same parent_suite_id)."""
    rows = db.query(TestSuite).filter(
        TestSuite.project_id == id,
        TestSuite.parent_suite_id == parent_suite_id,
    ).all()
    by_id = {s.id: s for s in rows}
    if set(body.suite_ids) != set(by_id.keys()):
        raise HTTPException(
            status_code=400,
            detail="suite_ids must include exactly all siblings of the given parent",
        )
    for new_order, sid in enumerate(body.suite_ids, start=1):
        by_id[sid].order = new_order
    db.commit()
    out = db.query(TestSuite).filter(
        TestSuite.project_id == id,
        TestSuite.parent_suite_id == parent_suite_id,
    ).order_by(TestSuite.order, TestSuite.id).all()
    return [_suite_out(s) for s in out]


@suites_router.post("/{id}/steps/reorder", response_model=list[SuiteStepOut])
def reorder_suite_steps(id: int, body: StepReorder, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if not db.get(TestSuite, id):
        raise HTTPException(status_code=404, detail="Not found")
    steps = {s.id: s for s in db.query(SuiteStep).filter(SuiteStep.suite_id == id).all()}
    for new_order, step_id in enumerate(body.step_ids, start=1):
        step = steps.get(step_id)
        if step is None:
            raise HTTPException(status_code=400, detail=f"Step {step_id} not in suite {id}")
        step.order = new_order
    db.commit()
    return db.query(SuiteStep).filter(SuiteStep.suite_id == id).order_by(SuiteStep.order).all()


@suites_router.post("/{id}/steps", response_model=SuiteStepOut, status_code=status.HTTP_201_CREATED)
def create_suite_step(id: int, body: SuiteStepCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if not db.get(TestSuite, id):
        raise HTTPException(status_code=404, detail="Not found")
    step = SuiteStep(suite_id=id, **body.model_dump())
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


@suites_router.put("/{id}/steps/{step_id}", response_model=SuiteStepOut)
def update_suite_step(id: int, step_id: int, body: SuiteStepUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    step = db.query(SuiteStep).filter(SuiteStep.id == step_id, SuiteStep.suite_id == id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(step, field, value)
    db.commit()
    db.refresh(step)
    return step


@suites_router.delete("/{id}/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_suite_step(id: int, step_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    step = db.query(SuiteStep).filter(SuiteStep.id == step_id, SuiteStep.suite_id == id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(step)
    db.commit()


@suites_router.delete("/{id}/steps", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_suite_steps(id: int, step_type: str | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(SuiteStep).filter(SuiteStep.suite_id == id)
    if step_type:
        q = q.filter(SuiteStep.step_type == step_type)
    q.delete()
    db.commit()
