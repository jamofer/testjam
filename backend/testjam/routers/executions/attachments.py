"""Attachment endpoints for executions and test results."""
import os
import shutil

from fastapi import Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from testjam.auth.dependencies import AuthContext, get_auth_context
from testjam.database import get_db
from testjam.models.execution import ExecutionAttachment, ResultAttachment
from testjam.routers.executions import (
    EXECUTION_UPLOAD_DIR,
    UPLOAD_DIR,
    executions_router,
    results_router,
)
from testjam.routers.executions._helpers import authorized_execution, authorized_result
from testjam.schemas.execution import ExecutionAttachmentOut
from testjam.schemas.testcase import AttachmentOut
from testjam.services import uploads
from testjam.services.permissions import WRITER_ROLES




# ─── Execution attachments ────────────────────────────────────────────────────

@executions_router.get("/{id}/attachments", response_model=list[ExecutionAttachmentOut])
def list_execution_attachments(id: int, db: Session = Depends(get_db), ctx: AuthContext = Depends(get_auth_context)):
    authorized_execution(db, ctx, id)
    return db.query(ExecutionAttachment).filter(ExecutionAttachment.execution_id == id).all()


@executions_router.post(
    "/{id}/attachments", response_model=ExecutionAttachmentOut, status_code=status.HTTP_201_CREATED
)
def upload_execution_attachment(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    authorized_execution(db, ctx, id, WRITER_ROLES)
    payload = uploads.read_attachment(file)
    dest_dir = os.path.join(EXECUTION_UPLOAD_DIR, str(id))
    os.makedirs(dest_dir, exist_ok=True)
    stored_filename = uploads.safe_filename(file.filename)
    dest_path = uploads.safe_join(dest_dir, file.filename)
    with open(dest_path, "wb") as f:
        f.write(payload)
    att = ExecutionAttachment(
        execution_id=id,
        filename=stored_filename,
        content_type=file.content_type,
        size_bytes=len(payload),
        file_path=dest_path,
        uploaded_by=ctx.user.username,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


@executions_router.get("/{id}/attachments/{attachment_id}/download")
def download_execution_attachment(
    id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    authorized_execution(db, ctx, id)
    att = (
        db.query(ExecutionAttachment)
        .filter(ExecutionAttachment.id == attachment_id, ExecutionAttachment.execution_id == id)
        .first()
    )
    if not att or not os.path.exists(att.file_path):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(att.file_path, filename=att.filename, media_type=att.content_type)


@executions_router.delete("/{id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_execution_attachment(
    id: int, attachment_id: int, db: Session = Depends(get_db), ctx: AuthContext = Depends(get_auth_context)
):
    authorized_execution(db, ctx, id, WRITER_ROLES)
    att = (
        db.query(ExecutionAttachment)
        .filter(ExecutionAttachment.id == attachment_id, ExecutionAttachment.execution_id == id)
        .first()
    )
    if not att:
        raise HTTPException(status_code=404, detail="Not found")
    if os.path.exists(att.file_path):
        os.remove(att.file_path)
    db.delete(att)
    db.commit()


# ─── Result attachments ───────────────────────────────────────────────────────

@results_router.get("/{id}/attachments", response_model=list[AttachmentOut])
def list_result_attachments(id: int, db: Session = Depends(get_db), ctx: AuthContext = Depends(get_auth_context)):
    authorized_result(db, ctx, id)
    return db.query(ResultAttachment).filter(ResultAttachment.result_id == id).all()


@results_router.post("/{id}/attachments", status_code=status.HTTP_201_CREATED)
def upload_result_attachment(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    authorized_result(db, ctx, id, WRITER_ROLES)
    payload = uploads.read_attachment(file)
    dest_dir = os.path.join(UPLOAD_DIR, str(id))
    os.makedirs(dest_dir, exist_ok=True)
    stored_filename = uploads.safe_filename(file.filename)
    dest_path = uploads.safe_join(dest_dir, file.filename)
    with open(dest_path, "wb") as f:
        f.write(payload)
    att = ResultAttachment(
        result_id=id,
        filename=stored_filename,
        content_type=file.content_type,
        size_bytes=len(payload),
        file_path=dest_path,
        uploaded_by=ctx.user.username,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


@results_router.get("/{id}/attachments/{attachment_id}/download")
def download_result_attachment(
    id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    authorized_result(db, ctx, id)
    att = (
        db.query(ResultAttachment)
        .filter(ResultAttachment.id == attachment_id, ResultAttachment.result_id == id)
        .first()
    )
    if not att or not os.path.exists(att.file_path):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(att.file_path, filename=att.filename, media_type=att.content_type)


@results_router.delete("/{id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_result_attachment(
    id: int, attachment_id: int, db: Session = Depends(get_db), ctx: AuthContext = Depends(get_auth_context)
):
    authorized_result(db, ctx, id, WRITER_ROLES)
    att = (
        db.query(ResultAttachment)
        .filter(ResultAttachment.id == attachment_id, ResultAttachment.result_id == id)
        .first()
    )
    if not att:
        raise HTTPException(status_code=404, detail="Not found")
    if os.path.exists(att.file_path):
        os.remove(att.file_path)
    db.delete(att)
    db.commit()
