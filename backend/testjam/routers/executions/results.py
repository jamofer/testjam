"""Manual result endpoints (CRUD, bulk update, step-result update)."""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from testjam.auth.dependencies import get_current_user
from testjam.database import get_db
from testjam.models.execution import TestResult, TestStepResult
from testjam.models.user import User
from testjam.routers.executions import executions_router, results_router
from testjam.schemas.execution import (
    BulkResultCreate,
    BulkResultResponse,
    TestResultCreate,
    TestResultOut,
    TestResultUpdate,
    TestStepResultOut,
    TestStepResultUpdate,
)


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
    ro = TestResultOut.model_validate(result)
    ro.test_case_title = result.test_case.name if result.test_case else None
    return ro


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
    return BulkResultResponse(created=created, updated=updated, errors=errors)


@results_router.get("/{id}", response_model=TestResultOut)
def get_result(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    result = db.get(TestResult, id)
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    ro = TestResultOut.model_validate(result)
    ro.test_case_title = result.test_case.name if result.test_case else None
    return ro


@results_router.put("/{id}", response_model=TestResultOut)
def update_result(
    id: int, body: TestResultUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    result = db.get(TestResult, id)
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(result, field, value)
    db.commit()
    db.refresh(result)
    ro = TestResultOut.model_validate(result)
    ro.test_case_title = result.test_case.name if result.test_case else None
    return ro


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
    sr = (
        db.query(TestStepResult)
        .filter(TestStepResult.id == step_result_id, TestStepResult.test_result_id == id)
        .first()
    )
    if not sr:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(sr, field, value)
    db.commit()
    db.refresh(sr)
    return sr
