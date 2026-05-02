import os
import shutil
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user
from testjam.database import get_db
from testjam.models.testcase import Attachment, TestCase, TestStep
from testjam.models.user import User
from testjam.schemas.testcase import (
    AttachmentOut, TestCaseCreate, TestCaseOut, TestCaseUpdate,
    TestStepCreate, TestStepOut, TestStepUpdate,
)

UPLOAD_DIR = "/app/uploads/cases"

suites_router = APIRouter(prefix="/suites", tags=["TestCases"])
cases_router = APIRouter(prefix="/cases", tags=["TestCases"])


@suites_router.get("/{id}/cases", response_model=list[TestCaseOut])
def list_cases(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(TestCase).filter(TestCase.suite_id == id).all()


@suites_router.post("/{id}/cases", response_model=TestCaseOut, status_code=status.HTTP_201_CREATED)
def create_case(id: int, body: TestCaseCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    case = TestCase(suite_id=id, **body.model_dump(exclude={"suite_id"}))
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@cases_router.get("/{id}", response_model=TestCaseOut)
def get_case(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    case = db.get(TestCase, id)
    if not case:
        raise HTTPException(status_code=404, detail="Not found")
    return case


@cases_router.put("/{id}", response_model=TestCaseOut)
def update_case(id: int, body: TestCaseUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    case = db.get(TestCase, id)
    if not case:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(case, field, value)
    db.commit()
    db.refresh(case)
    return case


@cases_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    case = db.get(TestCase, id)
    if not case:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(case)
    db.commit()


# ─── Steps ────────────────────────────────────────────────────────────────────

@cases_router.get("/{id}/steps", response_model=list[TestStepOut])
def list_steps(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(TestStep).filter(TestStep.test_case_id == id).order_by(TestStep.order).all()


@cases_router.post("/{id}/steps", response_model=TestStepOut, status_code=status.HTTP_201_CREATED)
def create_step(id: int, body: TestStepCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    step = TestStep(test_case_id=id, **body.model_dump())
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


@cases_router.put("/{id}/steps/{step_id}", response_model=TestStepOut)
def update_step(id: int, step_id: int, body: TestStepUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    step = db.query(TestStep).filter(TestStep.id == step_id, TestStep.test_case_id == id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(step, field, value)
    db.commit()
    db.refresh(step)
    return step


@cases_router.delete("/{id}/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_step(id: int, step_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    step = db.query(TestStep).filter(TestStep.id == step_id, TestStep.test_case_id == id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(step)
    db.commit()


# ─── Attachments ──────────────────────────────────────────────────────────────

@cases_router.get("/{id}/attachments", response_model=list[AttachmentOut])
def list_attachments(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Attachment).filter(Attachment.test_case_id == id).all()


@cases_router.post("/{id}/attachments", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
def upload_attachment(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    case = db.get(TestCase, id)
    if not case:
        raise HTTPException(status_code=404, detail="Not found")
    dest_dir = os.path.join(UPLOAD_DIR, str(id))
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, file.filename)
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    size = os.path.getsize(dest_path)
    attachment = Attachment(
        test_case_id=id,
        filename=file.filename,
        content_type=file.content_type,
        size_bytes=size,
        file_path=dest_path,
        uploaded_by=current.username,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@cases_router.delete("/{id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(id: int, attachment_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    att = db.query(Attachment).filter(Attachment.id == attachment_id, Attachment.test_case_id == id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Not found")
    if os.path.exists(att.file_path):
        os.remove(att.file_path)
    db.delete(att)
    db.commit()
