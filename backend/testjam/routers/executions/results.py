"""Manual result endpoints (CRUD, bulk update, step-result update)."""
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from testjam.auth.dependencies import get_current_user
from testjam.database import get_db
from testjam.models.execution import TestExecution, TestResult, TestStepResult
from testjam.models.user import User
from testjam.routers.executions import executions_router, results_router
from testjam.schemas.execution import (
    BulkResultCreate,
    BulkResultResponse,
    StepResultLogAppend,
    StepResultLogAppendResponse,
    TestResultCreate,
    TestResultOut,
    TestResultUpdate,
    TestStepResultOut,
    TestStepResultStartRunning,
    TestStepResultUpdate,
)
from testjam.services import execution_events

STEP_RESULT_LOG_SEPARATOR = "\n\n"
TERMINAL_EXECUTION_STATUSES = {"completed", "aborted"}


def _reject_if_terminal(execution: TestExecution | None) -> None:
    if execution is None:
        return
    if execution.status in TERMINAL_EXECUTION_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Execution is {execution.status}; results are read-only",
        )


def _result_out(result: TestResult) -> TestResultOut:
    out = TestResultOut.model_validate(result)
    out.test_case_title = result.test_case.name if result.test_case else None
    return out


def _format_log_entry(level: str, message: str) -> str:
    return f"**[{level}]** {message}"


def _append_log_output(step_result: TestStepResult, entry: str) -> None:
    if step_result.log_output:
        step_result.log_output = f"{step_result.log_output}{STEP_RESULT_LOG_SEPARATOR}{entry}"
    else:
        step_result.log_output = entry


def _load_step_result(db: Session, result_id: int, step_result_id: int) -> TestStepResult | None:
    return (
        db.query(TestStepResult)
        .filter(
            TestStepResult.id == step_result_id,
            TestStepResult.test_result_id == result_id,
        )
        .first()
    )


def _resolve_execution_id(db: Session, result_id: int) -> int | None:
    result = db.get(TestResult, result_id)
    return result.execution_id if result else None


@executions_router.get("/{id}/results", response_model=list[TestResultOut])
def list_results(
    id: int, status: str | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    q = (
        db.query(TestResult)
        .options(
            selectinload(TestResult.test_case),
            selectinload(TestResult.step_results),
            selectinload(TestResult.attachments),
        )
        .filter(TestResult.execution_id == id)
    )
    if status:
        q = q.filter(TestResult.status == status)
    results = q.order_by(TestResult.id).all()
    out = []
    for r in results:
        ro = TestResultOut.model_validate(r)
        ro.test_case_title = r.test_case.name if r.test_case else None
        out.append(ro)
    return out


@executions_router.post(
    "/{id}/results", response_model=TestResultOut, status_code=status.HTTP_201_CREATED
)
def create_result(
    id: int, body: TestResultCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    existing = db.query(TestResult).filter_by(execution_id=id, test_case_id=body.test_case_id).first()
    if existing:
        for field, value in body.model_dump(exclude={"step_results"}, exclude_unset=True).items():
            setattr(existing, field, value)
        result = existing
    else:
        result = TestResult(**body.model_dump(exclude={"step_results"}), execution_id=id)
        db.add(result)
    db.flush()
    for sr in body.step_results:
        existing_sr = (
            db.query(TestStepResult).filter_by(test_result_id=result.id, step_id=sr.step_id).first()
        )
        if existing_sr:
            existing_sr.status = sr.status
            existing_sr.comment = sr.comment
            existing_sr.log_output = sr.log_output
            if sr.duration_ms is not None:
                existing_sr.duration_ms = sr.duration_ms
        else:
            db.add(TestStepResult(test_result_id=result.id, **sr.model_dump()))
    db.commit()
    db.refresh(result)
    out = _result_out(result)
    execution_events.on_result_updated(id, out.model_dump(mode="json"))
    return out


@executions_router.post("/{id}/results/bulk", response_model=BulkResultResponse)
def bulk_results(
    id: int, body: BulkResultCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    created = updated = 0
    errors = []
    for item in body.results:
        try:
            existing = (
                db.query(TestResult).filter_by(execution_id=id, test_case_id=item.test_case_id).first()
            )
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
                existing_sr = (
                    db.query(TestStepResult)
                    .filter_by(test_result_id=result.id, step_id=sr.step_id)
                    .first()
                )
                if existing_sr:
                    existing_sr.status = sr.status
                    existing_sr.comment = sr.comment
                    if sr.duration_ms is not None:
                        existing_sr.duration_ms = sr.duration_ms
                else:
                    db.add(TestStepResult(test_result_id=result.id, **sr.model_dump()))
        except Exception as e:
            errors.append({"test_case_id": item.test_case_id, "error": str(e)})
    db.commit()
    execution_events.on_results_bulk_updated(db, id)
    return BulkResultResponse(created=created, updated=updated, errors=errors)


@results_router.get("/{id}", response_model=TestResultOut)
def get_result(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    result = db.get(TestResult, id)
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    return _result_out(result)


@results_router.put("/{id}", response_model=TestResultOut)
def update_result(
    id: int, body: TestResultUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    result = db.get(TestResult, id)
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    _reject_if_terminal(db.get(TestExecution, result.execution_id))
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(result, field, value)
    db.commit()
    db.refresh(result)
    out = _result_out(result)
    execution_events.on_result_updated(result.execution_id, out.model_dump(mode="json"))
    return out


@results_router.post(
    "/{id}/step-results",
    response_model=TestStepResultOut,
    status_code=status.HTTP_201_CREATED,
)
def start_step_result(
    id: int,
    body: TestStepResultStartRunning,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = db.get(TestResult, id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    _reject_if_terminal(db.get(TestExecution, result.execution_id))

    now = datetime.now(timezone.utc)
    existing = (
        db.query(TestStepResult)
        .filter_by(test_result_id=id, step_id=body.step_id)
        .first()
    )
    if existing:
        existing.status = "running"
        existing.started_at = now
        step_result = existing
    else:
        step_result = TestStepResult(
            test_result_id=id,
            step_id=body.step_id,
            status="running",
            started_at=now,
        )
        db.add(step_result)
    result_promoted = False
    if result.status == "not_run":
        result.status = "running"
        result_promoted = True
    execution = db.get(TestExecution, result.execution_id)
    execution_promoted = False
    if execution and execution.status == "pending":
        execution.status = "in_progress"
        execution_promoted = True
    db.commit()
    db.refresh(step_result)
    execution_id = _resolve_execution_id(db, id)
    if execution_id is not None:
        execution_events.on_step_result_started(
            execution_id,
            TestStepResultOut.model_validate(step_result).model_dump(mode="json"),
        )
        if result_promoted:
            db.refresh(result)
            execution_events.on_result_updated(
                execution_id,
                _result_out(result).model_dump(mode="json"),
            )
        if execution_promoted:
            db.refresh(execution)
            execution_events.on_execution_status_changed(db, execution)
    return step_result


@results_router.put(
    "/{id}/step-results/{step_result_id}", response_model=TestStepResultOut
)
def update_step_result(
    id: int,
    step_result_id: int,
    body: TestStepResultUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    sr = _load_step_result(db, id, step_result_id)
    if not sr:
        raise HTTPException(status_code=404, detail="Not found")
    execution_id = _resolve_execution_id(db, id)
    _reject_if_terminal(db.get(TestExecution, execution_id) if execution_id else None)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(sr, field, value)
    db.commit()
    db.refresh(sr)
    step_payload = TestStepResultOut.model_validate(sr).model_dump(mode="json")
    execution_id = _resolve_execution_id(db, id)
    if execution_id is not None:
        execution_events.on_step_result_finished_with_refresh(execution_id, step_payload)
    return sr


@results_router.post(
    "/{id}/step-results/{step_result_id}/log",
    response_model=StepResultLogAppendResponse,
)
def append_step_result_log(
    id: int,
    step_result_id: int,
    body: StepResultLogAppend,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    step_result = _load_step_result(db, id, step_result_id)
    if not step_result:
        raise HTTPException(status_code=404, detail="Not found")
    execution_id_pre = _resolve_execution_id(db, id)
    _reject_if_terminal(db.get(TestExecution, execution_id_pre) if execution_id_pre else None)

    entry = _format_log_entry(body.level, body.message)
    _append_log_output(step_result, entry)
    db.commit()

    execution_id = _resolve_execution_id(db, id)
    if execution_id is not None:
        execution_events.on_step_result_log_appended(
            execution_id,
            {
                "step_result_id": step_result_id,
                "level": body.level,
                "message": body.message,
                "ts": body.ts.isoformat() if body.ts else None,
            },
        )
    return StepResultLogAppendResponse(step_result_id=step_result_id, appended=1)
