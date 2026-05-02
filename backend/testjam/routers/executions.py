import os
import shutil
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user
from testjam.database import get_db
from testjam.models.execution import ResultAttachment, TestExecution, TestResult, TestStepResult
from testjam.models.user import User
from testjam.schemas.execution import (
    BulkResultCreate, BulkResultResponse,
    TestExecutionCreate, TestExecutionOut, TestExecutionUpdate,
    TestResultCreate, TestResultOut, TestResultUpdate,
    TestStepResultUpdate, TestStepResultOut,
    ExecutionSummary,
)
from testjam.schemas.testcase import AttachmentOut

UPLOAD_DIR = "/app/uploads/results"

projects_router = APIRouter(prefix="/projects", tags=["TestExecutions"])
executions_router = APIRouter(prefix="/executions", tags=["TestExecutions"])
results_router = APIRouter(prefix="/results", tags=["TestResults"])


def _compute_summary(execution: TestExecution) -> ExecutionSummary:
    counts = {"passed": 0, "failed": 0, "blocked": 0, "not_run": 0}
    for r in execution.results:
        counts[r.status] = counts.get(r.status, 0) + 1
    return ExecutionSummary(total=len(execution.results), **counts)


def _execution_out(ex: TestExecution) -> TestExecutionOut:
    data = TestExecutionOut.model_validate(ex)
    data.summary = _compute_summary(ex)
    return data


# ─── Executions ───────────────────────────────────────────────────────────────

@projects_router.get("/{id}/executions", response_model=list[TestExecutionOut])
def list_executions(
    id: int,
    type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(TestExecution).filter(TestExecution.project_id == id)
    if type:
        q = q.filter(TestExecution.type == type)
    if status:
        q = q.filter(TestExecution.status == status)
    return [_execution_out(ex) for ex in q.all()]


@projects_router.post("/{id}/executions", response_model=TestExecutionOut, status_code=status.HTTP_201_CREATED)
def create_execution(
    id: int,
    body: TestExecutionCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    data = body.model_dump(exclude={"test_case_ids"})
    data["project_id"] = id
    if body.type == "manual" and not data.get("triggered_by"):
        data["triggered_by"] = current.username
    ex = TestExecution(**data, started_at=datetime.now(timezone.utc))
    db.add(ex)
    db.flush()
    for tc_id in body.test_case_ids:
        db.add(TestResult(execution_id=ex.id, test_case_id=tc_id, status="not_run"))
    db.commit()
    db.refresh(ex)
    return _execution_out(ex)


@executions_router.get("/{id}", response_model=TestExecutionOut)
def get_execution(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    ex = db.get(TestExecution, id)
    if not ex:
        raise HTTPException(status_code=404, detail="Not found")
    return _execution_out(ex)


@executions_router.put("/{id}", response_model=TestExecutionOut)
def update_execution(id: int, body: TestExecutionUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    ex = db.get(TestExecution, id)
    if not ex:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(ex, field, value)
    db.commit()
    db.refresh(ex)
    return _execution_out(ex)


@executions_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_execution(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    ex = db.get(TestExecution, id)
    if not ex:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(ex)
    db.commit()


# ─── Results ──────────────────────────────────────────────────────────────────

@executions_router.get("/{id}/results", response_model=list[TestResultOut])
def list_results(id: int, status: str | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(TestResult).filter(TestResult.execution_id == id)
    if status:
        q = q.filter(TestResult.status == status)
    results = q.all()
    out = []
    for r in results:
        ro = TestResultOut.model_validate(r)
        ro.test_case_title = r.test_case.title if r.test_case else None
        out.append(ro)
    return out


@executions_router.post("/{id}/results", response_model=TestResultOut, status_code=status.HTTP_201_CREATED)
def create_result(id: int, body: TestResultCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    existing = db.query(TestResult).filter_by(execution_id=id, test_case_id=body.test_case_id).first()
    if existing:
        for field, value in body.model_dump(exclude={"step_results"}, exclude_none=True).items():
            setattr(existing, field, value)
        result = existing
    else:
        result = TestResult(**body.model_dump(exclude={"step_results"}), execution_id=id)
        db.add(result)
    db.flush()
    for sr in body.step_results:
        existing_sr = db.query(TestStepResult).filter_by(test_result_id=result.id, step_id=sr.step_id).first()
        if existing_sr:
            existing_sr.status = sr.status
            existing_sr.comment = sr.comment
        else:
            db.add(TestStepResult(test_result_id=result.id, **sr.model_dump()))
    db.commit()
    db.refresh(result)
    ro = TestResultOut.model_validate(result)
    ro.test_case_title = result.test_case.title if result.test_case else None
    return ro


@executions_router.post("/{id}/results/bulk", response_model=BulkResultResponse)
def bulk_results(id: int, body: BulkResultCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    created = updated = 0
    errors = []
    for item in body.results:
        try:
            existing = db.query(TestResult).filter_by(execution_id=id, test_case_id=item.test_case_id).first()
            if existing:
                for field, value in item.model_dump(exclude={"step_results"}, exclude_none=True).items():
                    setattr(existing, field, value)
                result = existing
                updated += 1
            else:
                result = TestResult(**item.model_dump(exclude={"step_results"}), execution_id=id)
                db.add(result)
                created += 1
            db.flush()
            for sr in item.step_results:
                existing_sr = db.query(TestStepResult).filter_by(test_result_id=result.id, step_id=sr.step_id).first()
                if existing_sr:
                    existing_sr.status = sr.status
                    existing_sr.comment = sr.comment
                else:
                    db.add(TestStepResult(test_result_id=result.id, **sr.model_dump()))
        except Exception as e:
            errors.append({"test_case_id": item.test_case_id, "error": str(e)})
    db.commit()
    return BulkResultResponse(created=created, updated=updated, errors=errors)


@results_router.get("/{id}", response_model=TestResultOut)
def get_result(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    result = db.get(TestResult, id)
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    ro = TestResultOut.model_validate(result)
    ro.test_case_title = result.test_case.title if result.test_case else None
    return ro


@results_router.put("/{id}", response_model=TestResultOut)
def update_result(id: int, body: TestResultUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    result = db.get(TestResult, id)
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(result, field, value)
    db.commit()
    db.refresh(result)
    ro = TestResultOut.model_validate(result)
    ro.test_case_title = result.test_case.title if result.test_case else None
    return ro


@results_router.put("/{id}/step-results/{step_result_id}", response_model=TestStepResultOut)
def update_step_result(id: int, step_result_id: int, body: TestStepResultUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    sr = db.query(TestStepResult).filter(TestStepResult.id == step_result_id, TestStepResult.test_result_id == id).first()
    if not sr:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(sr, field, value)
    db.commit()
    db.refresh(sr)
    return sr


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
def delete_result_attachment(id: int, attachment_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    att = db.query(ResultAttachment).filter(ResultAttachment.id == attachment_id, ResultAttachment.result_id == id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Not found")
    if os.path.exists(att.file_path):
        os.remove(att.file_path)
    db.delete(att)
    db.commit()
