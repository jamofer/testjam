import os
import shutil
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user, require_project_access
from testjam.database import get_db
from testjam.models.testcase import Attachment, TestCase, TestStep, TestSuite
from testjam.models.testplan import TestPlan
from testjam.models.user import User
from testjam.schemas.testcase import (
    AttachmentOut, TestCaseCreate, TestCaseOut, TestCaseUpdate,
    TestStepCreate, TestStepOut, TestStepUpdate,
)

UPLOAD_DIR = "/app/uploads/cases"

projects_router = APIRouter(prefix="/projects", tags=["TestCases"])
suites_router = APIRouter(prefix="/suites", tags=["TestCases"])
cases_router = APIRouter(prefix="/cases", tags=["TestCases"])


@projects_router.get("/{id}/cases", response_model=list[TestCaseOut])
def search_project_cases(
    id: int,
    q: str | None = None,
    tags: list[str] | None = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    limit = min(limit, 500)
    query = db.query(TestCase).join(TestSuite, TestCase.suite_id == TestSuite.id).filter(TestSuite.project_id == id)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(TestCase.name.ilike(like), TestCase.description.ilike(like)))
    rows = query.order_by(TestCase.created_at.desc()).offset(skip).limit(limit).all()
    if tags:
        tagset = set(tags)
        rows = [c for c in rows if c.tags and tagset.intersection(c.tags)]
    return rows


@suites_router.get("/{id}/cases", response_model=list[TestCaseOut])
def list_cases(
    id: int,
    name: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(TestCase).filter(TestCase.suite_id == id)
    if name is not None:
        q = q.filter(TestCase.name == name)
    return q.order_by(TestCase.order, TestCase.id).all()


@suites_router.post("/{id}/cases", response_model=TestCaseOut, status_code=status.HTTP_201_CREATED)
def create_case(id: int, body: TestCaseCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    duplicate = db.query(TestCase).filter(TestCase.suite_id == id, TestCase.name == body.name).first()
    if duplicate:
        raise HTTPException(status_code=409, detail=f"Test case '{body.name}' already exists")
    max_order = db.query(TestCase).filter(TestCase.suite_id == id).count()
    case = TestCase(suite_id=id, order=max_order + 1, **body.model_dump(exclude={"suite_id"}))
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


class BulkIds(BaseModel):
    ids: list[int]


class BulkAddToPlan(BaseModel):
    case_ids: list[int]


@cases_router.post("/bulk-delete", status_code=status.HTTP_200_OK)
def bulk_delete_cases(body: BulkIds, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if not body.ids:
        return {"deleted": 0}
    deleted = db.query(TestCase).filter(TestCase.id.in_(body.ids)).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted}


class StepReorder(BaseModel):
    step_ids: list[int]


class CaseReorder(BaseModel):
    case_ids: list[int]


@suites_router.post("/{id}/cases/reorder", response_model=list[TestCaseOut])
def reorder_suite_cases(id: int, body: CaseReorder, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(TestCase).filter(TestCase.suite_id == id).all()
    by_id = {c.id: c for c in rows}
    if set(body.case_ids) != set(by_id.keys()):
        raise HTTPException(status_code=400, detail="case_ids must include exactly all cases of the suite")
    for new_order, cid in enumerate(body.case_ids, start=1):
        by_id[cid].order = new_order
    db.commit()
    return db.query(TestCase).filter(TestCase.suite_id == id).order_by(TestCase.order, TestCase.id).all()


@cases_router.post("/{id}/steps/reorder", response_model=list[TestStepOut])
def reorder_case_steps(id: int, body: StepReorder, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if not db.get(TestCase, id):
        raise HTTPException(status_code=404, detail="Not found")
    steps = {s.id: s for s in db.query(TestStep).filter(TestStep.test_case_id == id).all()}
    for new_order, step_id in enumerate(body.step_ids, start=1):
        step = steps.get(step_id)
        if step is None:
            raise HTTPException(status_code=400, detail=f"Step {step_id} not in case {id}")
        step.order = new_order
    db.commit()
    return db.query(TestStep).filter(TestStep.test_case_id == id).order_by(TestStep.order).all()


# ─── Steps ────────────────────────────────────────────────────────────────────

@cases_router.get("/{id}/steps", response_model=list[TestStepOut])
def list_steps(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(TestStep).filter(TestStep.test_case_id == id).order_by(TestStep.order).all()


@cases_router.delete("/{id}/steps", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_steps(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    db.query(TestStep).filter(TestStep.test_case_id == id).delete()
    db.commit()


@cases_router.post("/{id}/steps", response_model=TestStepOut, status_code=status.HTTP_201_CREATED)
def create_step(id: int, body: TestStepCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    order = body.order
    if order is None:
        max_order = db.query(TestStep).filter(TestStep.test_case_id == id).count()
        order = max_order + 1
    step = TestStep(test_case_id=id, **{**body.model_dump(exclude={"order"}), "order": order})
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
