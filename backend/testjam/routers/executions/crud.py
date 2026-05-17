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
from testjam.models.project import Project
from testjam.models.user import User
from testjam.models.version import ProjectVersion
from testjam.routers.executions import executions_router, projects_router
from testjam.routers.executions._helpers import (
    execution_out,
    load_execution_full,
)
from testjam.schemas.execution import (
    TestExecutionCreate,
    TestExecutionOut,
    TestExecutionUpdate,
)
from testjam.services import environments as env_service, execution_events
from testjam.services.permissions import effective_role

REOPENABLE_STATUSES = {"completed", "aborted"}


def _resolve_or_create_version(db: Session, project_id: int, name: str) -> ProjectVersion:
    existing = (
        db.query(ProjectVersion)
        .filter(ProjectVersion.project_id == project_id, ProjectVersion.name.ilike(name))
        .first()
    )
    if existing:
        return existing
    row = ProjectVersion(project_id=project_id, name=name, status="active")
    db.add(row)
    db.flush()
    return row


def _require_reopen_permission(db: Session, execution: TestExecution, user: User) -> None:
    if user.is_admin:
        return
    if execution.created_by_id == user.id:
        return
    if effective_role(db, user.id, execution.project_id) == "owner":
        return
    raise HTTPException(
        status_code=403,
        detail="Only admins, project owners, or the user who created the execution can reopen it",
    )


@projects_router.get("/{id}/executions", response_model=list[TestExecutionOut])
def list_executions(
    id: int,
    type: str | None = None,
    status: str | None = None,
    assigned_to_id: int | None = None,
    version_id: int | None = None,
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
            selectinload(TestExecution.project_version),
        )
        .filter(TestExecution.project_id == id)
    )
    if type:
        q = q.filter(TestExecution.type == type)
    if status:
        q = q.filter(TestExecution.status == status)
    if assigned_to_id is not None:
        q = q.filter(TestExecution.assigned_to_id == assigned_to_id)
    if version_id is not None:
        q = q.filter(TestExecution.version_id == version_id)
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
    project = db.get(Project, id)
    if project is not None and project.archived_at is not None:
        raise HTTPException(status_code=409, detail="Project is archived")
    data = body.model_dump(exclude={"test_case_ids"})
    data["project_id"] = id
    data["created_by_id"] = ctx.user.id
    data["token_name"] = ctx.token_name
    free_text_version = data.pop("version", None)
    if data.get("version_id") is None and free_text_version:
        name = free_text_version.strip()
        if name:
            data["version_id"] = _resolve_or_create_version(db, id, name).id
    data["environment"] = env_service.upsert_from_execution(db, id, data.get("environment"))
    if body.type == "manual" and not data.get("triggered_by"):
        data["triggered_by"] = ctx.user.username
    ex = TestExecution(**data, started_at=datetime.now(timezone.utc))
    db.add(ex)
    db.flush()
    for tc_id in body.test_case_ids:
        db.add(TestResult(execution_id=ex.id, test_case_id=tc_id, status="not_run"))
    db.flush()
    execution_events.on_execution_created(db, ex, ctx.user, background)
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
    previous_status = ex.status
    previous_assignee_id = ex.assigned_to_id
    update_data = body.model_dump(exclude_none=True)
    free_text_version = update_data.pop("version", None)
    if free_text_version and not update_data.get("version_id"):
        update_data["version_id"] = _resolve_or_create_version(db, ex.project_id, free_text_version.strip()).id
    if "environment" in update_data:
        update_data["environment"] = env_service.upsert_from_execution(
            db, ex.project_id, update_data["environment"]
        )
    for field, value in update_data.items():
        setattr(ex, field, value)
    db.flush()
    execution_events.on_execution_updated(
        db, ex, current, background,
        previous_status=previous_status,
        previous_assignee_id=previous_assignee_id,
    )
    db.commit()
    return execution_out(load_execution_full(db, ex.id))


@executions_router.post("/{id}/reopen", response_model=TestExecutionOut)
def reopen_execution(
    id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    ex = db.get(TestExecution, id)
    if not ex:
        raise HTTPException(status_code=404, detail="Not found")
    _require_reopen_permission(db, ex, current)
    if ex.status not in REOPENABLE_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Execution is {ex.status}; only completed or aborted runs can be reopened",
        )
    previous_status = ex.status
    ex.status = "in_progress"
    ex.finished_at = None
    db.flush()
    execution_events.on_execution_updated(
        db, ex, current, background,
        previous_status=previous_status,
        previous_assignee_id=ex.assigned_to_id,
    )
    db.commit()
    return execution_out(load_execution_full(db, ex.id))


@executions_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_execution(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    ex = db.get(TestExecution, id)
    if not ex:
        raise HTTPException(status_code=404, detail="Not found")
    execution_id = ex.id
    project_id = ex.project_id
    db.delete(ex)
    db.commit()
    execution_events.on_execution_deleted(execution_id, project_id)
