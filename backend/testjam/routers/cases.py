import os
import shutil
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from testjam.auth.dependencies import (
    AuthContext,
    authorize_project,
    get_auth_context,
    get_current_user,
    require_project_access,
)
from testjam.core.config import settings
from testjam.database import get_db
from testjam.models.case_revision import CaseRevision
from testjam.models.testcase import Attachment, CaseComment, TestCase, TestStep, TestSuite
from testjam.models.testplan import TestPlan
from testjam.models.user import User
from testjam.schemas.case_revision import CaseRevisionDetail, CaseRevisionSummary
from testjam.schemas.testcase import (
    AttachmentOut, CaseCommentCreate, CaseCommentOut, CaseCommentUpdate,
    TestCaseCreate, TestCaseOut, TestCaseUpdate,
    TestStepCreate, TestStepOut, TestStepUpdate,
)
from testjam.services import case_events, mention_notify, uploads
from testjam.services import custom_fields as custom_field_service
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
    cf_key: str | None = None,
    cf_value: str | None = None,
    skip: int = 0,
    limit: int = 100,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    limit = min(limit, 500)
    query = db.query(TestCase).join(TestSuite, TestCase.suite_id == TestSuite.id).filter(TestSuite.project_id == id)
    if not include_archived:
        query = query.filter(TestCase.archived_at.is_(None))
    if q:
        like = f"%{q}%"
        query = query.filter(or_(TestCase.name.ilike(like), TestCase.description.ilike(like)))
    rows = query.order_by(TestCase.created_at.desc()).offset(skip).limit(limit).all()
    if tags:
        tagset = set(tags)
        rows = [c for c in rows if c.tags and tagset.intersection(c.tags)]
    if cf_key:
        rows = [c for c in rows if custom_field_service.matches_value(c.custom_fields, cf_key, cf_value)]
    return rows


@suites_router.get("/{id}/cases", response_model=list[TestCaseOut])
def list_cases(
    id: int,
    name: str | None = None,
    external_id: str | None = None,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    suite = db.get(TestSuite, id)
    if suite is None:
        raise HTTPException(status_code=404, detail="Suite not found")
    authorize_project(db, ctx, suite.project_id)
    q = db.query(TestCase).filter(TestCase.suite_id == id)
    if not include_archived:
        q = q.filter(TestCase.archived_at.is_(None))
    if name is not None:
        q = q.filter(TestCase.name == name)
    if external_id is not None:
        q = q.filter(TestCase.external_id == external_id)
    return q.order_by(TestCase.order, TestCase.id).all()


@suites_router.post("/{id}/cases", response_model=TestCaseOut, status_code=status.HTTP_201_CREATED)
def create_case(id: int, body: TestCaseCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    suite = db.get(TestSuite, id)
    if suite is None:
        raise HTTPException(status_code=404, detail="Suite not found")
    _require_case_writer(db, current, suite.project_id)
    duplicate = db.query(TestCase).filter(TestCase.suite_id == id, TestCase.name == body.name).first()
    if duplicate:
        raise HTTPException(status_code=409, detail=f"Test case '{body.name}' already exists")
    max_order = db.query(TestCase).filter(TestCase.suite_id == id).count()
    payload = body.model_dump(exclude={"suite_id", "custom_fields"})
    payload["custom_fields"] = custom_field_service.validate_payload(
        db, suite.project_id, "test_case", body.custom_fields, is_create=True,
    )
    case = TestCase(
        suite_id=id,
        order=max_order + 1,
        created_by_id=current.id,
        updated_by_id=current.id,
        **payload,
    )
    db.add(case)
    db.flush()
    write_revision(db, case, current, "created")
    db.commit()
    db.refresh(case)
    return case


@cases_router.get("/{id}", response_model=TestCaseOut)
def get_case(id: int, db: Session = Depends(get_db), ctx: AuthContext = Depends(get_auth_context)):
    return _authorized_case(db, ctx, id)


@cases_router.put("/{id}", response_model=TestCaseOut)
def update_case(id: int, body: TestCaseUpdate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    case = db.get(TestCase, id)
    if not case:
        raise HTTPException(status_code=404, detail="Not found")
    _require_case_writer(db, current, _project_id_for_case(case, db))
    update_data = body.model_dump(exclude_unset=True)
    incoming_custom_fields = update_data.pop("custom_fields", None)
    update_data = {key: value for key, value in update_data.items() if value is not None}
    if incoming_custom_fields is not None:
        update_data["custom_fields"] = custom_field_service.validate_payload(
            db,
            case.suite.project_id,
            "test_case",
            incoming_custom_fields,
            is_create=False,
            existing=case.custom_fields,
        )
    for field, value in update_data.items():
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
    ctx: AuthContext = Depends(get_auth_context),
):
    _authorized_case(db, ctx, id)
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
    ctx: AuthContext = Depends(get_auth_context),
):
    _authorized_case(db, ctx, id)
    rev = db.query(CaseRevision).filter(CaseRevision.id == rev_id, CaseRevision.case_id == id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Not found")
    return rev


@cases_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    case = db.get(TestCase, id)
    if not case:
        raise HTTPException(status_code=404, detail="Not found")
    _require_case_writer(db, current, _project_id_for_case(case, db))
    db.delete(case)
    db.commit()


@cases_router.post("/{id}/archive", response_model=TestCaseOut)
def archive_case(id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    from datetime import datetime, timezone

    case = db.get(TestCase, id)
    if not case:
        raise HTTPException(status_code=404, detail="Not found")
    _require_case_writer(db, current, _project_id_for_case(case, db))
    if case.archived_at is None:
        case.archived_at = datetime.now(timezone.utc)
        case.updated_by_id = current.id
        db.commit()
        db.refresh(case)
    return case


@cases_router.post("/{id}/unarchive", response_model=TestCaseOut)
def unarchive_case(id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    case = db.get(TestCase, id)
    if not case:
        raise HTTPException(status_code=404, detail="Not found")
    _require_case_writer(db, current, _project_id_for_case(case, db))
    if case.archived_at is not None:
        case.archived_at = None
        case.updated_by_id = current.id
        db.commit()
        db.refresh(case)
    return case


class CaseCopy(BaseModel):
    target_suite_id: int
    name: str | None = None


class BulkCaseCopy(BaseModel):
    case_ids: list[int]
    target_suite_id: int | None = None
    new_suite_name: str | None = None
    parent_suite_id: int | None = None


def _unique_case_name(db: Session, suite_id: int, base_name: str) -> str:
    existing = {
        row[0]
        for row in db.query(TestCase.name).filter(TestCase.suite_id == suite_id).all()
    }
    if base_name not in existing:
        return base_name
    for i in range(1, 100):
        candidate = f"{base_name} (copy {i})" if i > 1 else f"{base_name} (copy)"
        if candidate not in existing:
            return candidate
    return f"{base_name} (copy)"


def _clone_case(db: Session, source: TestCase, target_suite_id: int, name: str, current: User) -> TestCase:
    max_order = db.query(TestCase).filter(TestCase.suite_id == target_suite_id).count()
    copy = TestCase(
        suite_id=target_suite_id,
        name=name,
        description=source.description,
        preconditions=source.preconditions,
        setup=source.setup,
        teardown=source.teardown,
        tags=list(source.tags) if source.tags else [],
        custom_fields=dict(source.custom_fields) if source.custom_fields else {},
        order=max_order + 1,
        created_by_id=current.id,
        updated_by_id=current.id,
    )
    db.add(copy)
    db.flush()
    for step in source.steps:
        db.add(TestStep(
            test_case_id=copy.id,
            action=step.action,
            expected_result=step.expected_result,
            step_type=step.step_type,
            order=step.order,
        ))
    write_revision(db, copy, current, "created")
    return copy


@cases_router.post("/{id}/copy", response_model=TestCaseOut, status_code=status.HTTP_201_CREATED)
def copy_case(id: int, body: CaseCopy, db: Session = Depends(get_db), ctx: AuthContext = Depends(get_auth_context)):
    current = ctx.user
    source = _authorized_case(db, ctx, id)
    target_suite = db.get(TestSuite, body.target_suite_id)
    if not target_suite:
        raise HTTPException(status_code=404, detail="Target suite not found")
    _require_case_writer(db, current, target_suite.project_id)
    if body.name:
        name = body.name
    elif body.target_suite_id == source.suite_id:
        name = _unique_case_name(db, body.target_suite_id, source.name)
    else:
        name = source.name
    copy = _clone_case(db, source, body.target_suite_id, name, current)
    db.commit()
    db.refresh(copy)
    return copy


@cases_router.post("/bulk-copy", response_model=list[TestCaseOut], status_code=status.HTTP_201_CREATED)
def bulk_copy_cases(body: BulkCaseCopy, db: Session = Depends(get_db), ctx: AuthContext = Depends(get_auth_context)):
    current = ctx.user
    if not body.case_ids:
        return []
    if not body.target_suite_id and not body.new_suite_name:
        raise HTTPException(status_code=422, detail="Provide target_suite_id or new_suite_name")
    sources = db.query(TestCase).filter(TestCase.id.in_(body.case_ids)).all()
    if not sources:
        raise HTTPException(status_code=404, detail="No cases found")
    for source_project in {_project_id_for_case(source, db) for source in sources}:
        authorize_project(db, ctx, source_project)
    source_project_id = _project_id_for_case(sources[0], db)
    if body.new_suite_name:
        _require_case_writer(db, current, source_project_id)
        trimmed_name = body.new_suite_name.strip()
        existing_suite = (
            db.query(TestSuite)
            .filter(
                TestSuite.project_id == source_project_id,
                TestSuite.parent_suite_id == body.parent_suite_id,
                TestSuite.name == trimmed_name,
            )
            .first()
        )
        if existing_suite:
            raise HTTPException(status_code=409, detail=f"Suite '{trimmed_name}' already exists")
        suite = TestSuite(
            project_id=source_project_id,
            name=trimmed_name,
            parent_suite_id=body.parent_suite_id,
        )
        db.add(suite)
        db.flush()
        target_suite_id = suite.id
    else:
        target_suite = db.get(TestSuite, body.target_suite_id)
        if not target_suite:
            raise HTTPException(status_code=404, detail="Target suite not found")
        _require_case_writer(db, current, target_suite.project_id)
        target_suite_id = body.target_suite_id
    copies = []
    for source in sources:
        name = source.name if target_suite_id != source.suite_id else _unique_case_name(db, target_suite_id, source.name)
        copies.append(_clone_case(db, source, target_suite_id, name, current))
    db.commit()
    for copy in copies:
        db.refresh(copy)
    return copies


class BulkIds(BaseModel):
    ids: list[int]


class BulkAddToPlan(BaseModel):
    case_ids: list[int]


@cases_router.post("/bulk-delete", status_code=status.HTTP_200_OK)
def bulk_delete_cases(body: BulkIds, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if not body.ids:
        return {"deleted": 0}
    project_ids = {
        row[0]
        for row in db.query(TestSuite.project_id)
        .join(TestCase, TestCase.suite_id == TestSuite.id)
        .filter(TestCase.id.in_(body.ids))
        .distinct()
        .all()
    }
    for project_id in project_ids:
        _require_case_writer(db, current, project_id)
    deleted = db.query(TestCase).filter(TestCase.id.in_(body.ids)).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted}


class StepReorder(BaseModel):
    step_ids: list[int]


class CaseReorder(BaseModel):
    case_ids: list[int]


@suites_router.post("/{id}/cases/reorder", response_model=list[TestCaseOut])
def reorder_suite_cases(id: int, body: CaseReorder, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    suite = db.get(TestSuite, id)
    if not suite:
        raise HTTPException(status_code=404, detail="Not found")
    _require_case_writer(db, current, suite.project_id)
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
    _require_case_writer(db, current, _project_id_for_case(case, db))
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
def list_steps(id: int, db: Session = Depends(get_db), ctx: AuthContext = Depends(get_auth_context)):
    _authorized_case(db, ctx, id)
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
    case = _get_case(db, id)
    _require_case_writer(db, current, _project_id_for_case(case, db))
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
    _require_case_writer(db, current, _project_id_for_case(case, db))
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
    case = _get_case(db, id)
    _require_case_writer(db, current, _project_id_for_case(case, db))
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
    case = _get_case(db, id)
    _require_case_writer(db, current, _project_id_for_case(case, db))
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
    case = _get_case(db, id)
    _require_case_writer(db, current, _project_id_for_case(case, db))
    db.delete(step)
    db.flush()
    _touch_case_revision(db, id, current)
    db.commit()


# ─── Attachments ──────────────────────────────────────────────────────────────

@cases_router.get("/{id}/attachments", response_model=list[AttachmentOut])
def list_attachments(id: int, db: Session = Depends(get_db), ctx: AuthContext = Depends(get_auth_context)):
    _authorized_case(db, ctx, id)
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
    _require_case_writer(db, current, _project_id_for_case(case, db))
    payload = uploads.read_attachment(file)
    dest_dir = os.path.join(UPLOAD_DIR, str(id))
    os.makedirs(dest_dir, exist_ok=True)
    stored_filename = uploads.safe_filename(file.filename)
    dest_path = uploads.safe_join(dest_dir, file.filename)
    with open(dest_path, "wb") as f:
        f.write(payload)
    attachment = Attachment(
        test_case_id=id,
        filename=stored_filename,
        content_type=file.content_type,
        size_bytes=len(payload),
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
    ctx: AuthContext = Depends(get_auth_context),
):
    _authorized_case(db, ctx, id)
    att = db.query(Attachment).filter(Attachment.id == attachment_id, Attachment.test_case_id == id).first()
    if not att or not os.path.exists(att.file_path):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(att.file_path, filename=att.filename, media_type=att.content_type)


@cases_router.delete("/{id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(id: int, attachment_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    att = db.query(Attachment).filter(Attachment.id == attachment_id, Attachment.test_case_id == id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Not found")
    case = _get_case(db, id)
    _require_case_writer(db, current, _project_id_for_case(case, db))
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


def _authorized_case(db: Session, ctx: AuthContext, case_id: int) -> TestCase:
    case = _get_case(db, case_id)
    authorize_project(db, ctx, _project_id_for_case(case, db))
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
