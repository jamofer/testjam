"""Manual result endpoints (CRUD, bulk update, step-result update)."""
from datetime import datetime, timezone

from fastapi import BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from testjam.auth.dependencies import AuthContext, get_auth_context
from testjam.database import get_db
from testjam.models.execution import TestExecution, TestResult, TestStepResult
from testjam.models.testcase import TestCase, TestSuite
from testjam.routers.executions import executions_router, results_router
from testjam.routers.executions._helpers import authorized_execution, authorized_result
from testjam.schemas.execution import (
    BulkResultCreate,
    BulkResultItem,
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
from testjam.services.permissions import WRITER_ROLES

STEP_RESULT_LOG_SEPARATOR = "\n\n"
TERMINAL_EXECUTION_STATUSES = {"completed", "aborted"}
BULK_ITEM_SAVE_ERROR = "Could not save result"




def _project_id_for_execution(db: Session, execution_id: int) -> int | None:
    execution = db.get(TestExecution, execution_id)
    return execution.project_id if execution else None


def _reject_if_terminal(execution: TestExecution | None) -> None:
    if execution is None:
        return
    if execution.status in TERMINAL_EXECUTION_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Execution is {execution.status}; results are read-only",
        )


def _result_out(result: TestResult) -> TestResultOut:
    return TestResultOut.model_validate(result)


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


def _bulk_item_rejection(db: Session, project_id: int, item: BulkResultItem) -> str | None:
    case = (
        db.query(TestCase)
        .join(TestSuite, TestSuite.id == TestCase.suite_id)
        .filter(TestCase.id == item.test_case_id, TestSuite.project_id == project_id)
        .first()
    )
    if case is None:
        return "Test case not found in this project"
    case_step_ids = {step.id for step in case.steps}
    if any(step_result.step_id not in case_step_ids for step_result in item.step_results):
        return "Step does not belong to this test case"
    return None


def _upsert_bulk_item(db: Session, execution_id: int, item: BulkResultItem) -> tuple[TestResult, str | None]:
    result = db.query(TestResult).filter_by(execution_id=execution_id, test_case_id=item.test_case_id).first()
    previous_status = result.status if result else None
    if result:
        for field, value in item.model_dump(exclude={"step_results"}, exclude_none=True).items():
            setattr(result, field, value)
    else:
        result = TestResult(**item.model_dump(exclude={"step_results"}), execution_id=execution_id)
        db.add(result)
    db.flush()
    for step_result in item.step_results:
        existing_step_result = (
            db.query(TestStepResult)
            .filter_by(test_result_id=result.id, step_id=step_result.step_id)
            .first()
        )
        if existing_step_result:
            existing_step_result.status = step_result.status
            existing_step_result.comment = step_result.comment
            if step_result.duration_ms is not None:
                existing_step_result.duration_ms = step_result.duration_ms
        else:
            db.add(TestStepResult(test_result_id=result.id, **step_result.model_dump()))
    db.flush()
    return result, previous_status


def _resolve_execution_id(db: Session, result_id: int) -> int | None:
    result = db.get(TestResult, result_id)
    return result.execution_id if result else None


@executions_router.get("/{id}/results", response_model=list[TestResultOut])
def list_results(
    id: int, status: str | None = None, db: Session = Depends(get_db), ctx: AuthContext = Depends(get_auth_context)
):
    authorized_execution(db, ctx, id)
    q = (
        db.query(TestResult)
        .options(
            selectinload(TestResult.step_results),
            selectinload(TestResult.attachments),
        )
        .filter(TestResult.execution_id == id)
    )
    if status:
        q = q.filter(TestResult.status == status)
    return [_result_out(result) for result in q.order_by(TestResult.id).all()]


@executions_router.post(
    "/{id}/results", response_model=TestResultOut, status_code=status.HTTP_201_CREATED
)
def create_result(
    id: int, body: TestResultCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db), ctx: AuthContext = Depends(get_auth_context),
):
    _reject_if_terminal(authorized_execution(db, ctx, id, WRITER_ROLES))
    existing = db.query(TestResult).filter_by(execution_id=id, test_case_id=body.test_case_id).first()
    previous_status = existing.status if existing else None
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
    execution_events.on_result_updated(
        id, out.model_dump(mode="json"),
        db=db, project_id=_project_id_for_execution(db, id),
        previous_status=previous_status, background=background,
    )
    return out


@executions_router.post("/{id}/results/bulk", response_model=BulkResultResponse)
def bulk_results(
    id: int, body: BulkResultCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db), ctx: AuthContext = Depends(get_auth_context),
):
    execution = authorized_execution(db, ctx, id, WRITER_ROLES)
    _reject_if_terminal(execution)
    created = updated = 0
    errors = []
    newly_failed_ids: list[int] = []
    for item in body.results:
        rejection = _bulk_item_rejection(db, execution.project_id, item)
        if rejection:
            errors.append({"test_case_id": item.test_case_id, "error": rejection})
            continue
        try:
            with db.begin_nested():
                result, previous_status = _upsert_bulk_item(db, id, item)
        except SQLAlchemyError:
            errors.append({"test_case_id": item.test_case_id, "error": BULK_ITEM_SAVE_ERROR})
            continue
        if previous_status is None:
            created += 1
        else:
            updated += 1
        if result.status == "failed" and previous_status != "failed":
            newly_failed_ids.append(result.id)
    db.commit()
    execution_events.on_results_bulk_updated(
        db, id, failed_result_ids=newly_failed_ids, background=background,
    )
    return BulkResultResponse(created=created, updated=updated, errors=errors)


@results_router.get("/{id}", response_model=TestResultOut)
def get_result(id: int, db: Session = Depends(get_db), ctx: AuthContext = Depends(get_auth_context)):
    return _result_out(authorized_result(db, ctx, id))


@results_router.put("/{id}", response_model=TestResultOut)
def update_result(
    id: int, body: TestResultUpdate,
    background: BackgroundTasks,
    db: Session = Depends(get_db), ctx: AuthContext = Depends(get_auth_context),
):
    result = authorized_result(db, ctx, id, WRITER_ROLES)
    _reject_if_terminal(result.execution)
    previous_status = result.status
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(result, field, value)
    db.commit()
    db.refresh(result)
    out = _result_out(result)
    execution_events.on_result_updated(
        result.execution_id, out.model_dump(mode="json"),
        db=db, project_id=_project_id_for_execution(db, result.execution_id),
        previous_status=previous_status, background=background,
    )
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
    ctx: AuthContext = Depends(get_auth_context),
):
    result = authorized_result(db, ctx, id, WRITER_ROLES)
    _reject_if_terminal(result.execution)

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
    ctx: AuthContext = Depends(get_auth_context),
):
    authorized_result(db, ctx, id, WRITER_ROLES)
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
    ctx: AuthContext = Depends(get_auth_context),
):
    authorized_result(db, ctx, id, WRITER_ROLES)
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
