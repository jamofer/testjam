from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user
from testjam.database import get_db
from testjam.models.testcase import TestSuite
from testjam.models.user import User
from testjam.schemas.testcase import TestSuiteCreate, TestSuiteOut, TestSuiteUpdate

projects_router = APIRouter(prefix="/projects", tags=["TestSuites"])
suites_router = APIRouter(prefix="/suites", tags=["TestSuites"])


def _suite_out(suite: TestSuite) -> TestSuiteOut:
    return TestSuiteOut(
        **{c.name: getattr(suite, c.name) for c in suite.__table__.columns},
        child_suite_ids=[c.id for c in suite.children],
        test_case_ids=[tc.id for tc in suite.cases],
    )


@projects_router.get("/{id}/suites", response_model=list[TestSuiteOut])
def list_suites(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    suites = db.query(TestSuite).filter(TestSuite.project_id == id, TestSuite.parent_suite_id == None).all()
    return [_suite_out(s) for s in suites]


@projects_router.post("/{id}/suites", response_model=TestSuiteOut, status_code=status.HTTP_201_CREATED)
def create_suite(id: int, body: TestSuiteCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
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
