import os
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from unicodedata import normalize

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user, require_project_access
from testjam.database import get_db
from testjam.models.execution import ExecutionAttachment, ResultAttachment, TestExecution, TestResult, TestStepResult
from testjam.models.user import User
from testjam.schemas.execution import (
    BulkResultCreate, BulkResultResponse,
    ExecutionAttachmentOut,
    TestExecutionCreate, TestExecutionOut, TestExecutionUpdate,
    TestResultCreate, TestResultOut, TestResultUpdate,
    TestStepResultUpdate, TestStepResultOut,
    ExecutionSummary,
)
from testjam.schemas.testcase import AttachmentOut

UPLOAD_DIR = "/app/uploads/results"
EXECUTION_UPLOAD_DIR = "/app/uploads/executions"

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
    data.attachments = [ExecutionAttachmentOut.model_validate(a) for a in ex.attachments]
    return data


# ─── Executions ───────────────────────────────────────────────────────────────

@projects_router.get("/{id}/executions", response_model=list[TestExecutionOut])
def list_executions(
    id: int,
    type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    q = db.query(TestExecution).filter(TestExecution.project_id == id)
    if type:
        q = q.filter(TestExecution.type == type)
    if status:
        q = q.filter(TestExecution.status == status)
    return [_execution_out(ex) for ex in q.order_by(TestExecution.created_at.desc()).all()]


@projects_router.post("/{id}/executions", response_model=TestExecutionOut, status_code=status.HTTP_201_CREATED)
def create_execution(
    id: int,
    body: TestExecutionCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
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


# ─── Execution attachments ────────────────────────────────────────────────────

@executions_router.get("/{id}/attachments", response_model=list[ExecutionAttachmentOut])
def list_execution_attachments(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(ExecutionAttachment).filter(ExecutionAttachment.execution_id == id).all()


@executions_router.post("/{id}/attachments", response_model=ExecutionAttachmentOut, status_code=status.HTTP_201_CREATED)
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
def delete_execution_attachment(id: int, attachment_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    att = db.query(ExecutionAttachment).filter(ExecutionAttachment.id == attachment_id, ExecutionAttachment.execution_id == id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Not found")
    if os.path.exists(att.file_path):
        os.remove(att.file_path)
    db.delete(att)
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
        ro.test_case_title = r.test_case.name if r.test_case else None
        out.append(ro)
    return out


@executions_router.post("/{id}/results", response_model=TestResultOut, status_code=status.HTTP_201_CREATED)
def create_result(id: int, body: TestResultCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
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
        existing_sr = db.query(TestStepResult).filter_by(test_result_id=result.id, step_id=sr.step_id).first()
        if existing_sr:
            existing_sr.status = sr.status
            existing_sr.comment = sr.comment
            existing_sr.log_output = sr.log_output
        else:
            db.add(TestStepResult(test_result_id=result.id, **sr.model_dump()))
    db.commit()
    db.refresh(result)
    ro = TestResultOut.model_validate(result)
    ro.test_case_title = result.test_case.name if result.test_case else None
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
    ro.test_case_title = result.test_case.name if result.test_case else None
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
    ro.test_case_title = result.test_case.name if result.test_case else None
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


# ─── Import helpers ───────────────────────────────────────────────────────────

def _normalize(s: str) -> str:
    return normalize("NFC", s).strip().lower()


def _build_result_index(execution: TestExecution) -> dict[str, TestResult]:
    """Return a dict keyed by external_id and by normalized title for fast lookup."""
    index: dict[str, TestResult] = {}
    for r in execution.results:
        tc = r.test_case
        if not tc:
            continue
        if tc.external_id:
            index[_normalize(tc.external_id)] = r
        index[_normalize(tc.name)] = r
    return index


def _rf_status(status_str: str) -> str:
    mapping = {"PASS": "passed", "FAIL": "failed", "SKIP": "blocked", "NOT RUN": "not_run"}
    return mapping.get(status_str.upper(), "not_run")


def _junit_status(tc_elem: ET.Element) -> str:
    if tc_elem.find("failure") is not None or tc_elem.find("error") is not None:
        return "failed"
    if tc_elem.find("skipped") is not None:
        return "blocked"
    return "passed"


def _rf_collect_messages(kw_elem: ET.Element) -> str:
    """Collect all log messages from a keyword element into markdown."""
    lines = []
    for msg in kw_elem.iter("msg"):
        level = msg.get("level", "INFO")
        text = (msg.text or "").strip()
        if text:
            lines.append(f"**[{level}]** {text}")
    return "\n\n".join(lines)


def _rf_kw_duration_ms(kw_elem: ET.Element) -> int | None:
    s = kw_elem.find("status")
    if s is None:
        return None
    start = s.get("starttime") or s.get("start")
    end = s.get("endtime") or s.get("end")
    if start and end:
        try:
            fmt = "%Y%m%d %H:%M:%S.%f"
            delta = datetime.strptime(end, fmt) - datetime.strptime(start, fmt)
            return int(delta.total_seconds() * 1000)
        except ValueError:
            return None
    return None


# ─── Import: JUnit XML ────────────────────────────────────────────────────────

@executions_router.post("/{id}/results/import/junit", response_model=BulkResultResponse)
def import_junit(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    ex = db.get(TestExecution, id)
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")

    try:
        tree = ET.parse(file.file)
    except ET.ParseError as e:
        raise HTTPException(status_code=400, detail=f"Invalid XML: {e}")

    root = tree.getroot()
    # Support both <testsuites><testsuite>... and bare <testsuite>...
    if root.tag == "testsuites":
        tc_elements = [tc for ts in root.findall("testsuite") for tc in ts.findall("testcase")]
    elif root.tag == "testsuite":
        tc_elements = root.findall("testcase")
    else:
        raise HTTPException(status_code=400, detail="Root element must be <testsuite> or <testsuites>")

    result_index = _build_result_index(ex)
    created = updated = 0
    errors: list[dict] = []
    now = datetime.now(timezone.utc)

    for tc_elem in tc_elements:
        name = tc_elem.get("name", "")
        classname = tc_elem.get("classname", "")
        # Try matching by classname.name, then just name
        candidates = [
            _normalize(f"{classname}.{name}") if classname else None,
            _normalize(f"{classname}::{name}") if classname else None,
            _normalize(name),
        ]

        result: TestResult | None = None
        for key in candidates:
            if key and key in result_index:
                result = result_index[key]
                break

        if result is None:
            errors.append({"name": name, "classname": classname, "error": "No matching test case found"})
            continue

        new_status = _junit_status(tc_elem)
        failure = tc_elem.find("failure") or tc_elem.find("error")
        comment = failure.get("message", "") if failure is not None else None
        duration_raw = tc_elem.get("time")
        duration_ms = int(float(duration_raw) * 1000) if duration_raw else None

        is_new = result.status == "not_run"
        result.status = new_status
        result.executed_at = now
        result.duration_ms = duration_ms
        if comment:
            result.comment = comment
        if is_new:
            created += 1
        else:
            updated += 1

    db.commit()
    return BulkResultResponse(created=created, updated=updated, errors=errors)


# ─── Import: Robot Framework output.xml ──────────────────────────────────────

@executions_router.post("/{id}/results/import/robotframework", response_model=BulkResultResponse)
def import_robotframework(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    ex = db.get(TestExecution, id)
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")

    try:
        tree = ET.parse(file.file)
    except ET.ParseError as e:
        raise HTTPException(status_code=400, detail=f"Invalid XML: {e}")

    root = tree.getroot()
    if root.tag not in ("robot", "suite"):
        raise HTTPException(status_code=400, detail="Root element must be <robot> or <suite>")

    result_index = _build_result_index(ex)
    created = updated = 0
    errors: list[dict] = []
    now = datetime.now(timezone.utc)

    def _process_suite(suite_elem: ET.Element, parent_path: str = "") -> None:
        nonlocal created, updated
        suite_name = suite_elem.get("name", "")
        suite_path = f"{parent_path}.{suite_name}" if parent_path else suite_name

        for test_elem in suite_elem.findall("test"):
            test_name = test_elem.get("name", "")
            full_path = f"{suite_path}.{test_name}"

            candidates = [
                _normalize(full_path),
                _normalize(test_name),
            ]
            result: TestResult | None = None
            for key in candidates:
                if key in result_index:
                    result = result_index[key]
                    break

            if result is None:
                errors.append({"name": test_name, "suite": suite_path, "error": "No matching test case found"})
                continue

            status_elem = test_elem.find("status")
            rf_status = status_elem.get("status", "NOT RUN") if status_elem is not None else "NOT RUN"
            new_status = _rf_status(rf_status)

            # Duration from status element
            duration_ms = None
            if status_elem is not None:
                start = status_elem.get("starttime") or status_elem.get("start")
                end = status_elem.get("endtime") or status_elem.get("end")
                if start and end:
                    try:
                        fmt = "%Y%m%d %H:%M:%S.%f"
                        delta = datetime.strptime(end, fmt) - datetime.strptime(start, fmt)
                        duration_ms = int(delta.total_seconds() * 1000)
                    except ValueError:
                        pass

            is_new = result.status == "not_run"
            result.status = new_status
            result.executed_at = now
            if duration_ms is not None:
                result.duration_ms = duration_ms

            # Collect status message as comment
            if status_elem is not None and status_elem.text:
                result.comment = status_elem.text.strip()

            db.flush()

            # Map keywords to step results if the test case has steps
            tc = result.test_case
            if tc and tc.steps:
                steps = sorted(tc.steps, key=lambda s: (
                    {"setup": 0, "action": 1, "teardown": 2}.get(s.step_type, 1), s.order
                ))
                kw_elems = list(test_elem.findall("kw"))

                for i, (step, kw) in enumerate(zip(steps, kw_elems)):
                    kw_status_elem = kw.find("status")
                    kw_rf_status = kw_status_elem.get("status", "NOT RUN") if kw_status_elem is not None else "NOT RUN"
                    kw_new_status = _rf_status(kw_rf_status)
                    log_output = _rf_collect_messages(kw)
                    kw_duration = _rf_kw_duration_ms(kw)

                    existing_sr = db.query(TestStepResult).filter_by(
                        test_result_id=result.id, step_id=step.id
                    ).first()
                    if existing_sr:
                        existing_sr.status = kw_new_status
                        existing_sr.log_output = log_output or None
                        existing_sr.duration_ms = kw_duration
                    else:
                        db.add(TestStepResult(
                            test_result_id=result.id,
                            step_id=step.id,
                            status=kw_new_status,
                            log_output=log_output or None,
                            duration_ms=kw_duration,
                        ))

            if is_new:
                created += 1
            else:
                updated += 1

        for child_suite in suite_elem.findall("suite"):
            _process_suite(child_suite, suite_path)

    top = root if root.tag == "suite" else root.find("suite")
    if top is not None:
        _process_suite(top)

    db.commit()
    return BulkResultResponse(created=created, updated=updated, errors=errors)
