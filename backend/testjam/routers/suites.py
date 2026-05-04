from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user, require_project_access
from testjam.database import get_db
from testjam.models.testcase import SuiteStep, TestSuite
from testjam.models.user import User
from testjam.schemas.testcase import (
    SuiteStepCreate, SuiteStepOut, SuiteStepUpdate,
    TestSuiteCreate, TestSuiteOut, TestSuiteUpdate,
)

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
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    q = db.query(TestSuite).filter(TestSuite.project_id == id)
    if parent_suite_id is not None:
        q = q.filter(TestSuite.parent_suite_id == parent_suite_id)
    else:
        q = q.filter(TestSuite.parent_suite_id == None)
    if name is not None:
        q = q.filter(TestSuite.name == name)
    return [_suite_out(s) for s in q.all()]


@projects_router.post("/{id}/suites", response_model=TestSuiteOut, status_code=status.HTTP_201_CREATED)
def create_suite(id: int, body: TestSuiteCreate, db: Session = Depends(get_db), _: User = Depends(require_project_access)):
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
    suite = TestSuite(project_id=id, **body.model_dump())
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


# ── Suite steps ────────────────────────────────────────────────────────────────

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
