from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user, require_project_access
from testjam.database import get_db
from testjam.models.execution import TestExecution, TestResult
from testjam.models.project import Project, ProjectMember
from testjam.models.testcase import TestCase, TestSuite
from testjam.models.user import User
from testjam.schemas.project import (
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    RecentExecutionSummary,
    TransferOwnershipRequest,
)
from testjam.services.permissions import accessible_project_ids, effective_role
from testjam.services.project_export import cleanup_archive, export_project
from testjam.services.project_ownership import transfer_ownership

router = APIRouter(prefix="/projects", tags=["Projects"])


def _project_out(project: Project, db: Session) -> ProjectOut:
    suite_count = db.query(func.count(TestSuite.id)).filter(TestSuite.project_id == project.id).scalar() or 0
    case_count = (
        db.query(func.count(TestCase.id))
        .join(TestSuite, TestCase.suite_id == TestSuite.id)
        .filter(TestSuite.project_id == project.id)
        .scalar() or 0
    )
    execution_count = (
        db.query(func.count(TestExecution.id)).filter(TestExecution.project_id == project.id).scalar() or 0
    )
    last_execution_at = (
        db.query(func.max(TestExecution.created_at)).filter(TestExecution.project_id == project.id).scalar()
    )
    recent_rows = (
        db.query(TestExecution)
        .filter(TestExecution.project_id == project.id)
        .order_by(TestExecution.created_at.desc())
        .limit(10)
        .all()
    )
    recent: list[RecentExecutionSummary] = []
    for ex in recent_rows:
        counts = {"passed": 0, "failed": 0, "blocked": 0, "not_run": 0}
        for r in db.query(TestResult.status).filter(TestResult.execution_id == ex.id).all():
            counts[r[0]] = counts.get(r[0], 0) + 1
        recent.append(RecentExecutionSummary(
            id=ex.id,
            title=ex.title,
            status=ex.status,
            started_at=ex.started_at,
            **counts,
        ))
    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        archived_at=project.archived_at,
        suite_count=suite_count,
        case_count=case_count,
        execution_count=execution_count,
        last_execution_at=last_execution_at,
        recent_executions=recent,
    )


@router.get("", response_model=list[ProjectOut])
def list_projects(
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    query = db.query(Project)
    if not current.is_admin:
        accessible_ids = accessible_project_ids(db, current.id)
        if not accessible_ids:
            return []
        query = query.filter(Project.id.in_(accessible_ids))
    if not include_archived:
        query = query.filter(Project.archived_at.is_(None))
    return [_project_out(p, db) for p in query.all()]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(body: ProjectCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if db.query(Project).filter(Project.name == body.name).first():
        raise HTTPException(status_code=409, detail=f"Project '{body.name}' already exists")
    project = Project(**body.model_dump())
    db.add(project)
    db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=current.id, role="owner"))
    db.commit()
    db.refresh(project)
    return _project_out(project, db)


@router.get("/{id}", response_model=ProjectOut)
def get_project(id: int, db: Session = Depends(get_db), _: User = Depends(require_project_access)):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    return _project_out(project, db)


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
    return _project_out(project, db)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(id: int, db: Session = Depends(get_db), _: User = Depends(require_project_access)):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(project)
    db.commit()


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
    return _project_out(project, db)


@router.get("/{id}/export")
def export_project_zip(
    id: int,
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
    return _project_out(project, db)


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
    return _project_out(project, db)


def _reject_if_archived(project: Project) -> None:
    if project.archived_at is not None:
        raise HTTPException(status_code=409, detail="Project is archived")


def _require_owner_or_admin(project: Project, current: User, db: Session) -> None:
    if current.is_admin:
        return
    if effective_role(db, current.id, project.id) == "owner":
        return
    raise HTTPException(status_code=403, detail="Project owner or admin required")
