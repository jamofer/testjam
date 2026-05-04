from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user, require_project_access
from testjam.database import get_db
from testjam.models.testcase import TestCase
from testjam.models.testplan import TestPlan
from testjam.models.user import User
from testjam.schemas.testplan import TestPlanCreate, TestPlanOut, TestPlanUpdate

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
def create_plan(id: int, body: TestPlanCreate, db: Session = Depends(get_db), _: User = Depends(require_project_access)):
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
def get_plan(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    plan = db.get(TestPlan, id)
    if not plan:
        raise HTTPException(status_code=404, detail="Not found")
    return _plan_out(plan)


@plans_router.put("/{id}", response_model=TestPlanOut)
def update_plan(id: int, body: TestPlanUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    plan = db.get(TestPlan, id)
    if not plan:
        raise HTTPException(status_code=404, detail="Not found")
    if body.title is not None:
        plan.title = body.title
    if body.description is not None:
        plan.description = body.description
    if body.test_case_ids is not None:
        plan.cases = db.query(TestCase).filter(TestCase.id.in_(body.test_case_ids)).all()
    db.commit()
    db.refresh(plan)
    return _plan_out(plan)


@plans_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    plan = db.get(TestPlan, id)
    if not plan:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(plan)
    db.commit()
