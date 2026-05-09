"""Attachment endpoints for executions and test results."""
import os
import shutil

from fastapi import Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user
from testjam.database import get_db
from testjam.models.execution import ExecutionAttachment, ResultAttachment, TestExecution, TestResult
from testjam.models.user import User
from testjam.routers.executions import (
    EXECUTION_UPLOAD_DIR,
    UPLOAD_DIR,
    executions_router,
    results_router,
)
from testjam.schemas.execution import ExecutionAttachmentOut
from testjam.schemas.testcase import AttachmentOut


# ─── Execution attachments ────────────────────────────────────────────────────

@executions_router.get("/{id}/attachments", response_model=list[ExecutionAttachmentOut])
def list_execution_attachments(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(ExecutionAttachment).filter(ExecutionAttachment.execution_id == id).all()


@executions_router.post(
    "/{id}/attachments", response_model=ExecutionAttachmentOut, status_code=status.HTTP_201_CREATED
)
def upload_execution_attachment(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if not db.get(TestExecution, id):
        raise HTTPException(status_code=404, detail="Not found")
    dest_dir = os.path.join(EXECUTION_UPLOAD_DIR, str(id))
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, file.filename)
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    att = ExecutionAttachment(
        execution_id=id,
        filename=file.filename,
        content_type=file.content_type,
        size_bytes=os.path.getsize(dest_path),
        file_path=dest_path,
        uploaded_by=current.username,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


@executions_router.delete("/{id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_execution_attachment(
    id: int, attachment_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
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
def list_result_attachments(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(ResultAttachment).filter(ResultAttachment.result_id == id).all()


@results_router.post("/{id}/attachments", status_code=status.HTTP_201_CREATED)
def upload_result_attachment(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if not db.get(TestResult, id):
        raise HTTPException(status_code=404, detail="Not found")
    dest_dir = os.path.join(UPLOAD_DIR, str(id))
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, file.filename)
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    att = ResultAttachment(
        result_id=id,
        filename=file.filename,
        content_type=file.content_type,
        size_bytes=os.path.getsize(dest_path),
        file_path=dest_path,
        uploaded_by=current.username,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


@results_router.delete("/{id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_result_attachment(
    id: int, attachment_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
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
