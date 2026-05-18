import os
import shutil
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user, require_project_access, require_writable_project_access
from testjam.core.config import settings
from testjam.database import get_db
from testjam.models.user import User
from testjam.models.version import ProjectVersion, VersionAttachment
from testjam.schemas.version import (
    ProjectVersionCreate, ProjectVersionOut, ProjectVersionUpdate,
    VersionAttachmentOut,
)
from testjam.services.permissions import effective_role

VERSION_UPLOAD_DIR = os.path.join(settings.UPLOAD_DIR, "versions")

UPLOAD_ROLES = {"owner", "tester"}
DELETE_ROLES = {"owner"}

projects_router = APIRouter(prefix="/projects", tags=["Versions"])
versions_router = APIRouter(prefix="/versions", tags=["Versions"])


def _version_or_404(db: Session, version_id: int) -> ProjectVersion:
    version = db.get(ProjectVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Not found")
    return version


def _require_project_role(db: Session, project_id: int, user: User, allowed: set[str]) -> None:
    if user.is_admin:
        return
    role = effective_role(db, user.id, project_id)
    if role not in allowed:
        raise HTTPException(status_code=403, detail="Insufficient project role")


def _attachment_out(attachment: VersionAttachment) -> VersionAttachmentOut:
    return VersionAttachmentOut.model_validate(attachment)


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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Version '{data['name']}' already exists in this project",
        )
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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another version with this name already exists in this project",
        )
    db.refresh(v)
    return v


@versions_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_version(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    v = db.get(ProjectVersion, id)
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(v)
    db.commit()


@versions_router.get("/{id}/attachments", response_model=list[VersionAttachmentOut])
def list_version_attachments(
    id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    version = _version_or_404(db, id)
    _require_project_role(db, version.project_id, current, {"owner", "tester", "viewer"})
    rows = (
        db.query(VersionAttachment)
        .filter(VersionAttachment.version_id == id)
        .order_by(VersionAttachment.uploaded_at.desc(), VersionAttachment.id.desc())
        .all()
    )
    return [_attachment_out(a) for a in rows]


@versions_router.post(
    "/{id}/attachments",
    response_model=VersionAttachmentOut,
    status_code=status.HTTP_201_CREATED,
)
def upload_version_attachment(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    version = _version_or_404(db, id)
    _require_project_role(db, version.project_id, current, UPLOAD_ROLES)
    destination_directory = os.path.join(VERSION_UPLOAD_DIR, str(id))
    os.makedirs(destination_directory, exist_ok=True)
    destination_path = os.path.join(destination_directory, file.filename)
    with open(destination_path, "wb") as handle:
        shutil.copyfileobj(file.file, handle)
    attachment = VersionAttachment(
        version_id=id,
        filename=file.filename,
        content_type=file.content_type,
        size_bytes=os.path.getsize(destination_path),
        file_path=destination_path,
        uploaded_by_id=current.id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return _attachment_out(attachment)


@versions_router.get("/{id}/attachments/{attachment_id}/download")
def download_version_attachment(
    id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    version = _version_or_404(db, id)
    _require_project_role(db, version.project_id, current, {"owner", "tester", "viewer"})
    attachment = (
        db.query(VersionAttachment)
        .filter(VersionAttachment.id == attachment_id, VersionAttachment.version_id == id)
        .first()
    )
    if not attachment or not os.path.exists(attachment.file_path):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(
        attachment.file_path,
        filename=attachment.filename,
        media_type=attachment.content_type,
    )


@versions_router.delete(
    "/{id}/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_version_attachment(
    id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    version = _version_or_404(db, id)
    _require_project_role(db, version.project_id, current, DELETE_ROLES)
    attachment = (
        db.query(VersionAttachment)
        .filter(VersionAttachment.id == attachment_id, VersionAttachment.version_id == id)
        .first()
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="Not found")
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)
    db.delete(attachment)
    db.commit()
