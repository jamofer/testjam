from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from testjam.auth.dependencies import (
    get_current_user,
    require_project_access,
    require_project_writer,
    require_writable_project_access,
)
from testjam.database import get_db
from testjam.models.testcase import TestCase, TestSuite
from testjam.models.testplan import TestPlan
from testjam.models.user import User
from testjam.schemas.testplan import TestPlanCreate, TestPlanOut, TestPlanUpdate
from testjam.services.permissions import has_project_access


class PlanCaseIds(BaseModel):
    case_ids: list[int]

projects_router = APIRouter(prefix="/projects", tags=["TestPlans"])
plans_router = APIRouter(prefix="/plans", tags=["TestPlans"])


def _plan_out(plan: TestPlan) -> TestPlanOut:
    return TestPlanOut(
        id=plan.id,
        project_id=plan.project_id,
        title=plan.title,
        description=plan.description,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        test_case_ids=[c.id for c in plan.cases],
    )


@projects_router.get("/{id}/plans", response_model=list[TestPlanOut])
def list_plans(id: int, db: Session = Depends(get_db), _: User = Depends(require_project_access)):
    return [_plan_out(p) for p in db.query(TestPlan).filter(TestPlan.project_id == id).all()]


@projects_router.post("/{id}/plans", response_model=TestPlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(id: int, body: TestPlanCreate, db: Session = Depends(get_db), current: User = Depends(require_writable_project_access)):
    require_project_writer(db, current, id)
    plan = TestPlan(project_id=id, title=body.title, description=body.description)
    db.add(plan)
    db.flush()
    if body.test_case_ids:
        cases = db.query(TestCase).filter(TestCase.id.in_(body.test_case_ids)).all()
        plan.cases = cases
    db.commit()
    db.refresh(plan)
    return _plan_out(plan)


@plans_router.get("/{id}", response_model=TestPlanOut)
def get_plan(id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    plan = db.get(TestPlan, id)
    if not plan:
        raise HTTPException(status_code=404, detail="Not found")
    _require_plan_member(db, current, plan)
    return _plan_out(plan)


@plans_router.put("/{id}", response_model=TestPlanOut)
def update_plan(id: int, body: TestPlanUpdate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    plan = db.get(TestPlan, id)
    if not plan:
        raise HTTPException(status_code=404, detail="Not found")
    require_project_writer(db, current, plan.project_id)
    if body.title is not None:
        plan.title = body.title
    if body.description is not None:
        plan.description = body.description
    if body.test_case_ids is not None:
        plan.cases = _scoped_cases(db, plan.project_id, body.test_case_ids)
    db.commit()
    db.refresh(plan)
    return _plan_out(plan)


@plans_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    plan = db.get(TestPlan, id)
    if not plan:
        raise HTTPException(status_code=404, detail="Not found")
    require_project_writer(db, current, plan.project_id)
    db.delete(plan)
    db.commit()


@plans_router.post("/{id}/cases", response_model=TestPlanOut)
def add_cases_to_plan(id: int, body: PlanCaseIds, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    plan = db.get(TestPlan, id)
    if not plan:
        raise HTTPException(status_code=404, detail="Not found")
    require_project_writer(db, current, plan.project_id)
    existing_ids = {c.id for c in plan.cases}
    new_ids = [cid for cid in body.case_ids if cid not in existing_ids]
    if new_ids:
        new_cases = _scoped_cases(db, plan.project_id, new_ids)
        plan.cases.extend(new_cases)
        db.commit()
        db.refresh(plan)
    return _plan_out(plan)


def _scoped_cases(db: Session, project_id: int, case_ids: list[int]) -> list[TestCase]:
    return (
        db.query(TestCase)
        .join(TestSuite, TestSuite.id == TestCase.suite_id)
        .filter(TestCase.id.in_(case_ids), TestSuite.project_id == project_id)
        .all()
    )


def _require_plan_member(db: Session, user: User, plan: TestPlan) -> None:
    if not has_project_access(db, user, plan.project_id):
        raise HTTPException(status_code=403, detail="Not a project member")
