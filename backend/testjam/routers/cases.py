import os
import shutil
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user, require_project_access
from testjam.core.config import settings
from testjam.database import get_db
from testjam.models.case_revision import CaseRevision
from testjam.models.project import ProjectMember
from testjam.models.testcase import Attachment, CaseComment, TestCase, TestStep, TestSuite
from testjam.models.testplan import TestPlan
from testjam.models.user import User
from testjam.schemas.case_revision import CaseRevisionDetail, CaseRevisionSummary
from testjam.schemas.testcase import (
    AttachmentOut, CaseCommentCreate, CaseCommentOut, CaseCommentUpdate,
    TestCaseCreate, TestCaseOut, TestCaseUpdate,
    TestStepCreate, TestStepOut, TestStepUpdate,
)
from testjam.services import case_events, mention_notify
from testjam.services.case_revisions import write_revision
from testjam.services.permissions import effective_role

UPLOAD_DIR = os.path.join(settings.UPLOAD_DIR, "cases")

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
def create_case(id: int, body: TestCaseCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    duplicate = db.query(TestCase).filter(TestCase.suite_id == id, TestCase.name == body.name).first()
    if duplicate:
        raise HTTPException(status_code=409, detail=f"Test case '{body.name}' already exists")
    max_order = db.query(TestCase).filter(TestCase.suite_id == id).count()
    case = TestCase(
        suite_id=id,
        order=max_order + 1,
        created_by_id=current.id,
        updated_by_id=current.id,
        **body.model_dump(exclude={"suite_id"}),
    )
    db.add(case)
    db.flush()
    write_revision(db, case, current, "created")
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
def update_case(id: int, body: TestCaseUpdate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    case = db.get(TestCase, id)
    if not case:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(case, field, value)
    case.updated_by_id = current.id
    db.flush()
    write_revision(db, case, current, "updated")
    db.commit()
    db.refresh(case)
    return case


@cases_router.get("/{id}/revisions", response_model=list[CaseRevisionSummary])
def list_case_revisions(
    id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not db.get(TestCase, id):
        raise HTTPException(status_code=404, detail="Not found")
    limit = min(limit, 200)
    return (
        db.query(CaseRevision)
        .filter(CaseRevision.case_id == id)
        .order_by(CaseRevision.created_at.desc(), CaseRevision.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@cases_router.get("/{id}/revisions/{rev_id}", response_model=CaseRevisionDetail)
def get_case_revision(
    id: int, rev_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rev = db.query(CaseRevision).filter(CaseRevision.id == rev_id, CaseRevision.case_id == id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Not found")
    return rev


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
def reorder_case_steps(id: int, body: StepReorder, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    case = db.get(TestCase, id)
    if not case:
        raise HTTPException(status_code=404, detail="Not found")
    steps = {s.id: s for s in db.query(TestStep).filter(TestStep.test_case_id == id).all()}
    for new_order, step_id in enumerate(body.step_ids, start=1):
        step = steps.get(step_id)
        if step is None:
            raise HTTPException(status_code=400, detail=f"Step {step_id} not in case {id}")
        step.order = new_order
    case.updated_by_id = current.id
    db.flush()
    db.refresh(case)
    write_revision(db, case, current, "updated")
    db.commit()
    return db.query(TestStep).filter(TestStep.test_case_id == id).order_by(TestStep.order).all()


# ─── Steps ────────────────────────────────────────────────────────────────────

@cases_router.get("/{id}/steps", response_model=list[TestStepOut])
def list_steps(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(TestStep).filter(TestStep.test_case_id == id).order_by(TestStep.order).all()


def _touch_case_revision(db: Session, case_id: int, actor: User) -> None:
    case = db.get(TestCase, case_id)
    if case is None:
        return
    case.updated_by_id = actor.id
    db.flush()
    db.refresh(case)
    write_revision(db, case, actor, "updated")


@cases_router.delete("/{id}/steps", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_steps(id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    db.query(TestStep).filter(TestStep.test_case_id == id).delete()
    _touch_case_revision(db, id, current)
    db.commit()


class StepsReplace(BaseModel):
    steps: list[TestStepCreate]


@cases_router.post("/{id}/steps/replace", response_model=list[TestStepOut])
def replace_case_steps(
    id: int,
    body: StepsReplace,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    case = db.get(TestCase, id)
    if not case:
        raise HTTPException(status_code=404, detail="Not found")
    db.query(TestStep).filter(TestStep.test_case_id == id).delete()
    db.flush()
    for index, step in enumerate(body.steps, start=1):
        order = step.order if step.order is not None else index
        db.add(TestStep(
            test_case_id=id,
            order=order,
            action=step.action,
            expected_result=step.expected_result,
            step_type=step.step_type,
        ))
    case.updated_by_id = current.id
    db.flush()
    db.refresh(case)
    write_revision(db, case, current, "updated")
    db.commit()
    return db.query(TestStep).filter(TestStep.test_case_id == id).order_by(TestStep.order).all()


@cases_router.post("/{id}/steps", response_model=TestStepOut, status_code=status.HTTP_201_CREATED)
def create_step(id: int, body: TestStepCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    order = body.order
    if order is None:
        max_order = db.query(TestStep).filter(TestStep.test_case_id == id).count()
        order = max_order + 1
    step = TestStep(test_case_id=id, **{**body.model_dump(exclude={"order"}), "order": order})
    db.add(step)
    db.flush()
    _touch_case_revision(db, id, current)
    db.commit()
    db.refresh(step)
    return step


@cases_router.put("/{id}/steps/{step_id}", response_model=TestStepOut)
def update_step(id: int, step_id: int, body: TestStepUpdate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    step = db.query(TestStep).filter(TestStep.id == step_id, TestStep.test_case_id == id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(step, field, value)
    db.flush()
    _touch_case_revision(db, id, current)
    db.commit()
    db.refresh(step)
    return step


@cases_router.delete("/{id}/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_step(id: int, step_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    step = db.query(TestStep).filter(TestStep.id == step_id, TestStep.test_case_id == id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(step)
    db.flush()
    _touch_case_revision(db, id, current)
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


@cases_router.get("/{id}/attachments/{attachment_id}/download")
def download_case_attachment(
    id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    case = db.get(TestCase, id)
    if not case:
        raise HTTPException(status_code=404, detail="Not found")
    suite = db.get(TestSuite, case.suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail="Not found")
    if not current.is_admin:
        member = (
            db.query(ProjectMember)
            .filter_by(project_id=suite.project_id, user_id=current.id)
            .first()
        )
        if not member:
            raise HTTPException(status_code=403, detail="Not a project member")
    att = db.query(Attachment).filter(Attachment.id == attachment_id, Attachment.test_case_id == id).first()
    if not att or not os.path.exists(att.file_path):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(att.file_path, filename=att.filename, media_type=att.content_type)


@cases_router.delete("/{id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(id: int, attachment_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    att = db.query(Attachment).filter(Attachment.id == attachment_id, Attachment.test_case_id == id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Not found")
    if os.path.exists(att.file_path):
        os.remove(att.file_path)
    db.delete(att)
    db.commit()


COMMENT_WRITER_ROLES = {"tester", "owner"}


def _get_case(db: Session, case_id: int) -> TestCase:
    case = db.get(TestCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Not found")
    return case


def _project_id_for_case(case: TestCase, db: Session) -> int:
    suite = db.get(TestSuite, case.suite_id)
    return suite.project_id


def _require_case_writer(db: Session, user: User, project_id: int) -> None:
    if user.is_admin:
        return
    role = effective_role(db, user.id, project_id)
    if role not in COMMENT_WRITER_ROLES:
        raise HTTPException(status_code=403, detail="Tester role or higher required")


def _require_case_viewer(db: Session, user: User, project_id: int) -> None:
    if user.is_admin:
        return
    if effective_role(db, user.id, project_id) is None:
        raise HTTPException(status_code=403, detail="Not a project member")


def _case_mention_subject(case: TestCase) -> str:
    return f"case ~{case.id} {case.name}"


def _case_mention_link(case_id: int) -> str:
    return f"/cases/{case_id}"


def _fan_out_case_mentions(
    db: Session,
    case: TestCase,
    project_id: int,
    body: str | None,
    previous_body: str | None,
    actor: User,
    background: BackgroundTasks,
) -> None:
    if not body:
        return
    mention_notify.notify_mentions(
        db,
        project_id=project_id,
        body=body,
        previous_body=previous_body,
        subject_object=_case_mention_subject(case),
        link_path=_case_mention_link(case.id),
        actor=actor,
        background=background,
    )


@cases_router.get("/{id}/comments", response_model=list[CaseCommentOut])
def list_case_comments(
    id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    case = _get_case(db, id)
    project_id = _project_id_for_case(case, db)
    _require_case_viewer(db, current, project_id)
    return list(case.comments)


@cases_router.post(
    "/{id}/comments", response_model=CaseCommentOut, status_code=status.HTTP_201_CREATED,
)
def add_case_comment(
    id: int,
    body: CaseCommentCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    case = _get_case(db, id)
    project_id = _project_id_for_case(case, db)
    _require_case_writer(db, current, project_id)
    comment = CaseComment(test_case_id=case.id, body=body.body, created_by_id=current.id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    case_events.on_case_comment_added(comment)
    _fan_out_case_mentions(db, case, project_id, comment.body, None, current, background)
    return comment


@cases_router.put("/{id}/comments/{comment_id}", response_model=CaseCommentOut)
def update_case_comment(
    id: int,
    comment_id: int,
    body: CaseCommentUpdate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    comment = db.get(CaseComment, comment_id)
    if comment is None or comment.test_case_id != id:
        raise HTTPException(status_code=404, detail="Not found")
    if comment.created_by_id != current.id and not current.is_admin:
        raise HTTPException(status_code=403, detail="Only the author or admin can edit")
    previous_body = comment.body
    comment.body = body.body
    db.commit()
    db.refresh(comment)
    case_events.on_case_comment_updated(comment)
    case = _get_case(db, id)
    project_id = _project_id_for_case(case, db)
    _fan_out_case_mentions(db, case, project_id, comment.body, previous_body, current, background)
    return comment


@cases_router.delete("/{id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case_comment(
    id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    comment = db.get(CaseComment, comment_id)
    if comment is None or comment.test_case_id != id:
        raise HTTPException(status_code=404, detail="Not found")
    case = comment.test_case
    project_id = _project_id_for_case(case, db)
    is_author = comment.created_by_id == current.id
    is_owner = current.is_admin or effective_role(db, current.id, project_id) == "owner"
    if not is_author and not is_owner:
        raise HTTPException(status_code=403, detail="Only the author or project owner can delete")
    db.delete(comment)
    db.commit()
    case_events.on_case_comment_deleted(case.id, comment_id)
