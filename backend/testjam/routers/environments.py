from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from testjam.auth.dependencies import (
    AuthContext,
    get_auth_context,
    get_current_user,
    require_project_access,
    require_writable_project_access,
)
from testjam.database import get_db
from testjam.models.environment import ProjectEnvironment
from testjam.models.execution import TestExecution
from testjam.models.project import Project
from testjam.models.user import User
from testjam.schemas.environment import (
    EnvironmentCreate,
    EnvironmentOut,
    EnvironmentReorder,
    EnvironmentUpdate,
)
from testjam.services import environments as env_service


projects_router = APIRouter(prefix="/projects", tags=["Environments"])
environments_router = APIRouter(prefix="/environments", tags=["Environments"])


def _get_environment(db: Session, env_id: int) -> ProjectEnvironment:
    env = db.get(ProjectEnvironment, env_id)
    if env is None:
        raise HTTPException(status_code=404, detail="Not found")
    return env


def _require_writable_for_environment(
    db: Session, env: ProjectEnvironment, ctx: AuthContext
) -> None:
    if ctx.project_scope is not None and ctx.project_scope != env.project_id:
        raise HTTPException(
            status_code=403, detail="API token is not authorized for this project"
        )
    project = db.get(Project, env.project_id)
    if project is not None and project.archived_at is not None:
        raise HTTPException(status_code=409, detail="Project is archived")


@projects_router.get("/{id}/environments", response_model=list[EnvironmentOut])
def list_environments(
    id: int,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    q = db.query(ProjectEnvironment).filter(ProjectEnvironment.project_id == id)
    if not include_archived:
        q = q.filter(ProjectEnvironment.archived_at.is_(None))
    return q.order_by(ProjectEnvironment.order.asc(), ProjectEnvironment.id.asc()).all()


@projects_router.post(
    "/{id}/environments",
    response_model=EnvironmentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_environment(
    id: int,
    body: EnvironmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_writable_project_access),
):
    env = ProjectEnvironment(
        project_id=id,
        name=body.name,
        slug=body.slug,
        description=body.description,
        host=body.host,
        color=body.color,
        order=env_service.next_order(db, id),
    )
    db.add(env)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Environment slug already exists")
    env_service.apply_default_state(db, id, env, body.is_default)
    db.commit()
    db.refresh(env)
    return env


@projects_router.post(
    "/{id}/environments/reorder", response_model=list[EnvironmentOut]
)
def reorder_environments(
    id: int,
    body: EnvironmentReorder,
    db: Session = Depends(get_db),
    _: User = Depends(require_writable_project_access),
):
    rows = (
        db.query(ProjectEnvironment)
        .filter(
            ProjectEnvironment.project_id == id,
            ProjectEnvironment.id.in_(body.ids),
        )
        .all()
    )
    if len(rows) != len(body.ids):
        raise HTTPException(
            status_code=400,
            detail="ids must reference environments of this project",
        )
    order_map = {env_id: index + 1 for index, env_id in enumerate(body.ids)}
    for row in rows:
        row.order = order_map[row.id]
    db.commit()
    return (
        db.query(ProjectEnvironment)
        .filter(ProjectEnvironment.project_id == id)
        .order_by(ProjectEnvironment.order.asc(), ProjectEnvironment.id.asc())
        .all()
    )


@environments_router.get("/{id}", response_model=EnvironmentOut)
def get_environment(
    id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return _get_environment(db, id)


@environments_router.put("/{id}", response_model=EnvironmentOut)
def update_environment(
    id: int,
    body: EnvironmentUpdate,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    env = _get_environment(db, id)
    _require_writable_for_environment(db, env, ctx)
    update_data = body.model_dump(exclude_unset=True)
    is_default = update_data.pop("is_default", None)
    previous_slug = env.slug
    new_slug = update_data.get("slug", previous_slug)
    if new_slug != previous_slug:
        if env.archived_at is None and _slug_in_use_by_executions(db, env.project_id, previous_slug):
            raise HTTPException(
                status_code=409,
                detail="Cannot rename slug while executions reference it",
            )
    for field, value in update_data.items():
        setattr(env, field, value)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Environment slug already exists")
    if is_default is not None:
        env_service.apply_default_state(db, env.project_id, env, is_default)
    db.commit()
    db.refresh(env)
    return env


@environments_router.post("/{id}/archive", response_model=EnvironmentOut)
def archive_environment(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    env = _get_environment(db, id)
    _require_writable_for_environment(db, env, ctx)
    if env.archived_at is None:
        env.archived_at = datetime.now(timezone.utc)
        if env.is_default:
            env.is_default = False
    db.commit()
    db.refresh(env)
    return env


@environments_router.post("/{id}/unarchive", response_model=EnvironmentOut)
def unarchive_environment(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    env = _get_environment(db, id)
    _require_writable_for_environment(db, env, ctx)
    env.archived_at = None
    db.commit()
    db.refresh(env)
    return env


@environments_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_environment(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    env = _get_environment(db, id)
    _require_writable_for_environment(db, env, ctx)
    if _slug_in_use_by_executions(db, env.project_id, env.slug):
        raise HTTPException(
            status_code=409,
            detail="Environment is referenced by executions. Archive it instead.",
        )
    db.delete(env)
    db.commit()


def _slug_in_use_by_executions(db: Session, project_id: int, slug: str) -> bool:
    count = (
        db.query(func.count(TestExecution.id))
        .filter(
            TestExecution.project_id == project_id,
            TestExecution.environment == slug,
        )
        .scalar()
    )
    return bool(count)
