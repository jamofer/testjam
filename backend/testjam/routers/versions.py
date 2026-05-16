from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user, require_project_access, require_writable_project_access
from testjam.database import get_db
from testjam.models.version import ProjectVersion
from testjam.models.user import User
from testjam.schemas.version import ProjectVersionCreate, ProjectVersionOut, ProjectVersionUpdate

projects_router = APIRouter(prefix="/projects", tags=["Versions"])
versions_router = APIRouter(prefix="/versions", tags=["Versions"])


@projects_router.get("/{id}/versions", response_model=list[ProjectVersionOut])
def list_versions(id: int, db: Session = Depends(get_db), _: User = Depends(require_project_access)):
    return db.query(ProjectVersion).filter(ProjectVersion.project_id == id).order_by(ProjectVersion.created_at.desc()).all()


@projects_router.post("/{id}/versions", response_model=ProjectVersionOut, status_code=status.HTTP_201_CREATED)
def create_version(id: int, body: ProjectVersionCreate, db: Session = Depends(get_db), _: User = Depends(require_writable_project_access)):
    data = body.model_dump()
    version = ProjectVersion(project_id=id, **data)
    if version.status == "released":
        version.released_at = datetime.now(timezone.utc)
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


@versions_router.get("/{id}", response_model=ProjectVersionOut)
def get_version(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    v = db.get(ProjectVersion, id)
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    return v


@versions_router.put("/{id}", response_model=ProjectVersionOut)
def update_version(id: int, body: ProjectVersionUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    v = db.get(ProjectVersion, id)
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    update_data = body.model_dump(exclude_unset=True)
    previous_status = v.status
    new_status = update_data.get("status")
    for field, value in update_data.items():
        setattr(v, field, value)
    if new_status == "released" and previous_status != "released":
        v.released_at = datetime.now(timezone.utc)
    elif new_status and new_status != "released" and previous_status == "released":
        v.released_at = None
    db.commit()
    db.refresh(v)
    return v


@versions_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_version(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    v = db.get(ProjectVersion, id)
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(v)
    db.commit()
