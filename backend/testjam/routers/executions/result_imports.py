"""Import endpoints: JUnit XML and Robot Framework output.xml."""
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from unicodedata import normalize

from fastapi import BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user
from testjam.database import get_db
from testjam.models.execution import TestExecution, TestResult, TestStepResult
from testjam.models.user import User
from testjam.routers.executions import executions_router
from testjam.schemas.execution import BulkResultResponse
from testjam.services import execution_events


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
    background: BackgroundTasks,
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
    newly_failed_ids: list[int] = []

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
        failure = tc_elem.find("failure")
        if failure is None:
            failure = tc_elem.find("error")
        comment = failure.get("message", "") if failure is not None else None
        duration_raw = tc_elem.get("time")
        duration_ms = int(float(duration_raw) * 1000) if duration_raw else None

        previous_status = result.status
        is_new = previous_status == "not_run"
        result.status = new_status
        result.executed_at = now
        result.duration_ms = duration_ms
        if comment:
            result.comment = comment
        if new_status == "failed" and previous_status != "failed":
            db.flush()
            newly_failed_ids.append(result.id)
        if is_new:
            created += 1
        else:
            updated += 1

    db.commit()
    execution_events.on_results_bulk_updated(
        db, id, failed_result_ids=newly_failed_ids, background=background,
    )
    return BulkResultResponse(created=created, updated=updated, errors=errors)


# ─── Import: Robot Framework output.xml ──────────────────────────────────────

@executions_router.post("/{id}/results/import/robotframework", response_model=BulkResultResponse)
def import_robotframework(
    id: int,
    background: BackgroundTasks,
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
    newly_failed_ids: list[int] = []

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

            previous_status = result.status
            is_new = previous_status == "not_run"
            result.status = new_status
            result.executed_at = now
            if duration_ms is not None:
                result.duration_ms = duration_ms

            # Collect status message as comment
            if status_elem is not None and status_elem.text:
                result.comment = status_elem.text.strip()

            db.flush()
            if new_status == "failed" and previous_status != "failed":
                newly_failed_ids.append(result.id)

            # Map keywords to step results if the test case has steps
            tc = result.test_case
            if tc and tc.steps:
                steps = sorted(
                    tc.steps,
                    key=lambda s: ({"setup": 0, "action": 1, "teardown": 2}.get(s.step_type, 1), s.order),
                )
                kw_elems = list(test_elem.findall("kw"))

                for step, kw in zip(steps, kw_elems):
                    kw_status_elem = kw.find("status")
                    kw_rf_status = (
                        kw_status_elem.get("status", "NOT RUN") if kw_status_elem is not None else "NOT RUN"
                    )
                    kw_new_status = _rf_status(kw_rf_status)
                    log_output = _rf_collect_messages(kw)
                    kw_duration = _rf_kw_duration_ms(kw)

                    existing_sr = (
                        db.query(TestStepResult)
                        .filter_by(test_result_id=result.id, step_id=step.id)
                        .first()
                    )
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
    execution_events.on_results_bulk_updated(
        db, id, failed_result_ids=newly_failed_ids, background=background,
    )
    return BulkResultResponse(created=created, updated=updated, errors=errors)
