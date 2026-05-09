"""CRUD endpoints for `TestExecution`."""
from datetime import datetime, timezone

from fastapi import BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from testjam.auth.dependencies import (
    AuthContext,
    get_current_user,
    require_project_access,
    require_project_access_ctx,
)
from testjam.database import get_db
from testjam.models.execution import TestExecution, TestResult
from testjam.models.user import User
from testjam.routers.executions import executions_router, projects_router
from testjam.routers.executions._helpers import (
    execution_out,
    load_execution_full,
    push_assignment_notification,
)
from testjam.schemas.execution import (
    TestExecutionCreate,
    TestExecutionOut,
    TestExecutionUpdate,
)


@projects_router.get("/{id}/executions", response_model=list[TestExecutionOut])
def list_executions(
    id: int,
    type: str | None = None,
    status: str | None = None,
    assigned_to_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    limit = min(limit, 200)
    q = (
        db.query(TestExecution)
        .options(
            selectinload(TestExecution.results),
            selectinload(TestExecution.attachments),
        )
        .filter(TestExecution.project_id == id)
    )
    if type:
        q = q.filter(TestExecution.type == type)
    if status:
        q = q.filter(TestExecution.status == status)
    if assigned_to_id is not None:
        q = q.filter(TestExecution.assigned_to_id == assigned_to_id)
    rows = q.order_by(TestExecution.created_at.desc()).offset(skip).limit(limit).all()
    return [execution_out(ex) for ex in rows]


@projects_router.post(
    "/{id}/executions", response_model=TestExecutionOut, status_code=status.HTTP_201_CREATED
)
def create_execution(
    id: int,
    body: TestExecutionCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(require_project_access_ctx),
):
    data = body.model_dump(exclude={"test_case_ids"})
    data["project_id"] = id
    data["created_by_id"] = ctx.user.id
    data["token_name"] = ctx.token_name
    if body.type == "manual" and not data.get("triggered_by"):
        data["triggered_by"] = ctx.user.username
    ex = TestExecution(**data, started_at=datetime.now(timezone.utc))
    db.add(ex)
    db.flush()
    for tc_id in body.test_case_ids:
        db.add(TestResult(execution_id=ex.id, test_case_id=tc_id, status="not_run"))
    if ex.assigned_to_id:
        push_assignment_notification(db, ex, ex.assigned_to_id, ctx.user, background)
    db.commit()
    return execution_out(load_execution_full(db, ex.id))


@executions_router.get("/{id}", response_model=TestExecutionOut)
def get_execution(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    ex = load_execution_full(db, id)
    if not ex:
        raise HTTPException(status_code=404, detail="Not found")
    return execution_out(ex)


@executions_router.put("/{id}", response_model=TestExecutionOut)
def update_execution(
    id: int,
    body: TestExecutionUpdate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    ex = db.get(TestExecution, id)
    if not ex:
        raise HTTPException(status_code=404, detail="Not found")
    prev_assignee = ex.assigned_to_id
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(ex, field, value)
    if ex.assigned_to_id and ex.assigned_to_id != prev_assignee:
        push_assignment_notification(db, ex, ex.assigned_to_id, current, background)
    db.commit()
    return execution_out(load_execution_full(db, ex.id))


@executions_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_execution(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    ex = db.get(TestExecution, id)
    if not ex:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(ex)
    db.commit()
