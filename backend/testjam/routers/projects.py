from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from testjam.auth.dependencies import (
    AuthContext,
    get_auth_context,
    get_unscoped_user,
    require_project_access,
)
from testjam.core.rate_limit import EXPORT_RATE_LIMIT, limiter
from testjam.database import get_db
from testjam.models.project import Project, ProjectMember
from testjam.models.user import User
from testjam.schemas.project import (
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    TransferOwnershipRequest,
)
from testjam.services.permissions import accessible_project_ids, effective_role
from testjam.services.project_events import on_project_deleted
from testjam.services.project_export import cleanup_archive, export_project
from testjam.services.project_ownership import transfer_ownership
from testjam.services.project_summaries import project_summaries, project_summary

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(
    include_archived: bool = False,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    query = db.query(Project)
    if ctx.project_scope is not None:
        query = query.filter(Project.id == ctx.project_scope)
    if not ctx.user.is_admin:
        query = query.filter(Project.id.in_(accessible_project_ids(db, ctx.user.id)))
    if not include_archived:
        query = query.filter(Project.archived_at.is_(None))
    return project_summaries(db, query.all())


def _find_project_by_name(db: Session, name: str) -> Project | None:
    return db.query(Project).filter(Project.name == name).first()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(body: ProjectCreate, db: Session = Depends(get_db), current: User = Depends(get_unscoped_user)):
    if _find_project_by_name(db, body.name):
        raise HTTPException(status_code=409, detail=f"Project '{body.name}' already exists")
    project = Project(**body.model_dump())
    db.add(project)
    try:
        db.flush()
        db.add(ProjectMember(project_id=project.id, user_id=current.id, role="owner"))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail=f"Project '{body.name}' already exists",
        )
    db.refresh(project)
    return project_summary(db, project)


@router.get("/{id}", response_model=ProjectOut)
def get_project(id: int, db: Session = Depends(get_db), _: User = Depends(require_project_access)):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    return project_summary(db, project)


@router.put("/{id}", response_model=ProjectOut)
def update_project(id: int, body: ProjectUpdate, db: Session = Depends(get_db), _: User = Depends(require_project_access)):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    _reject_if_archived(project)
    payload = body.model_dump(exclude_none=True)
    if "name" in payload and payload["name"] != project.name:
        clash = db.query(Project).filter(Project.name == payload["name"], Project.id != id).first()
        if clash:
            raise HTTPException(status_code=409, detail=f"Project '{payload['name']}' already exists")
    for field, value in payload.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project_summary(db, project)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(id: int, db: Session = Depends(get_db), _: User = Depends(require_project_access)):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    project_name = project.name
    db.delete(project)
    db.commit()
    on_project_deleted(id, project_name)


@router.post("/{id}/archive", response_model=ProjectOut)
def archive_project(id: int, db: Session = Depends(get_db), current: User = Depends(require_project_access)):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    _require_owner_or_admin(project, current, db)
    if project.archived_at is None:
        project.archived_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(project)
    return project_summary(db, project)


@router.get("/{id}/export")
@limiter.limit(EXPORT_RATE_LIMIT)
def export_project_zip(
    id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    artifact = export_project(db, project)
    background_tasks.add_task(cleanup_archive, artifact.path)
    return FileResponse(artifact.path, media_type="application/zip", filename=artifact.filename)


@router.post("/{id}/transfer-ownership", response_model=ProjectOut)
def transfer_project_ownership(
    id: int,
    body: TransferOwnershipRequest,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    _require_owner_or_admin(project, current, db)
    transfer_ownership(db, project, body.new_owner_id)
    db.refresh(project)
    return project_summary(db, project)


@router.post("/{id}/unarchive", response_model=ProjectOut)
def unarchive_project(id: int, db: Session = Depends(get_db), current: User = Depends(require_project_access)):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    _require_owner_or_admin(project, current, db)
    if project.archived_at is not None:
        project.archived_at = None
        db.commit()
        db.refresh(project)
    return project_summary(db, project)


def _reject_if_archived(project: Project) -> None:
    if project.archived_at is not None:
        raise HTTPException(status_code=409, detail="Project is archived")


def _require_owner_or_admin(project: Project, current: User, db: Session) -> None:
    if current.is_admin:
        return
    if effective_role(db, current.id, project.id) == "owner":
        return
    raise HTTPException(status_code=403, detail="Project owner or admin required")
