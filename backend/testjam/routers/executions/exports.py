"""Export endpoints: HTML / XLSX for executions, XLSX for project cases."""
import io
from datetime import datetime, timezone
from typing import Iterator
from urllib.parse import urlparse

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from fastapi import Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user, require_project_access
from testjam.core.config import settings
from testjam.database import get_db
from testjam.models.testcase import TestCase, TestSuite
from testjam.models.user import User
from testjam.routers.executions import executions_router, projects_router
from testjam.routers.executions._helpers import load_execution_full
from testjam.services.execution_reports import load_execution_for_report, render_html
from testjam.services.settings import get_settings as get_app_settings
from testjam.services.timezones import format_in_user_zone, user_zone_label


def _enforce_export_cap(row_count: int, *, kind: str) -> None:
    cap = settings.MAX_EXPORT_RESULTS
    if row_count > cap:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Export refused: {row_count} {kind} exceeds the configured "
                f"cap of {cap}. Narrow the scope (filter by version, "
                f"environment, or suite) and retry."
            ),
        )


def _stream_bytes(payload: bytes) -> Iterator[bytes]:
    chunk = settings.EXPORT_STREAM_CHUNK_BYTES
    for start in range(0, len(payload), chunk):
        yield payload[start:start + chunk]


@executions_router.get("/{id}/export/xlsx")
def export_execution_xlsx(
    id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    ex = load_execution_full(db, id)
    if not ex:
        raise HTTPException(status_code=404, detail="Not found")
    _enforce_export_cap(len(ex.results), kind="results")

    wb = openpyxl.Workbook()
    tz_label = user_zone_label(current)

    # Summary sheet
    ws_sum = wb.active
    ws_sum.title = "Summary"
    launched_by = ex.token_name or (ex.created_by.username if ex.created_by else ex.triggered_by or "")
    ws_sum.append(["Title", ex.title])
    ws_sum.append(["Status", ex.status])
    ws_sum.append(["Type", ex.type])
    ws_sum.append(["Environment", ex.environment or ""])
    ws_sum.append(["Version", ex.project_version.name if ex.project_version else ""])
    ws_sum.append(["Launched by", launched_by])
    ws_sum.append([f"Started at ({tz_label})", format_in_user_zone(ex.started_at, current, "%Y-%m-%d %H:%M:%S")])
    ws_sum.append([f"Finished at ({tz_label})", format_in_user_zone(ex.finished_at, current, "%Y-%m-%d %H:%M:%S")])
    ws_sum.append([
        "Generated",
        f"{format_in_user_zone(datetime.now(timezone.utc), current, '%Y-%m-%d %H:%M %Z')} by {current.username}",
    ])

    # Results sheet
    ws_res = wb.create_sheet("Results")
    ws_res.append(["Test Case", "Status", "Executed by", f"Executed at ({tz_label})", "Duration (ms)", "Comment"])
    for r in ex.results:
        tc_name = r.test_case.name if r.test_case else str(r.test_case_id)
        ws_res.append([
            tc_name,
            r.status,
            r.executed_by or "",
            format_in_user_zone(r.executed_at, current, "%Y-%m-%d %H:%M:%S"),
            r.duration_ms or "",
            r.comment or "",
        ])

    buf = io.BytesIO()
    wb.save(buf)
    filename = f"execution_{id}.xlsx"
    return StreamingResponse(
        _stream_bytes(buf.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )



@executions_router.get("/{id}/export/html")
def export_execution_html(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    execution = load_execution_for_report(db, id)
    if not execution:
        raise HTTPException(status_code=404, detail="Not found")
    _enforce_export_cap(len(execution.results), kind="results")

    app_settings = get_app_settings(db)
    base_url = _resolve_base_url(request, app_settings.site_url)
    html = render_html(
        db,
        execution,
        base_url=base_url,
        viewer=current,
        app_settings=app_settings,
    )

    filename = f"execution_{id}_{execution.title.replace(' ', '_')}.html"
    return StreamingResponse(
        _stream_bytes(html.encode("utf-8")),
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _resolve_base_url(request: Request, configured_site_url: str | None) -> str:
    referer = request.headers.get("referer", "")
    if referer:
        try:
            parsed = urlparse(referer)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            pass
    if configured_site_url:
        return configured_site_url.rstrip("/")
    return f"{request.url.scheme}://{request.url.netloc}"


@projects_router.get("/{id}/cases/export/xlsx")
def export_cases_xlsx(
    id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    from testjam.models.project import Project
    project = db.get(Project, id)
    suites = db.query(TestSuite).filter(TestSuite.project_id == id, TestSuite.parent_suite_id == None).all()  # noqa: E711
    case_count = (
        db.query(func.count(TestCase.id))
        .join(TestSuite, TestSuite.id == TestCase.suite_id)
        .filter(TestSuite.project_id == id)
        .scalar()
        or 0
    )
    _enforce_export_cap(case_count, kind="test cases")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Test Cases"

    # ── Palette ──────────────────────────────────────────────────────────────
    NAVY   = "1E3A5F"
    WHITE  = "FFFFFF"
    GRAY50 = "F9FAFB"
    GRAY200= "E5E7EB"

    thin_border = Border(
        left=Side(style="thin", color=GRAY200),
        right=Side(style="thin", color=GRAY200),
        top=Side(style="thin", color=GRAY200),
        bottom=Side(style="thin", color=GRAY200),
    )

    # ── Title row ────────────────────────────────────────────────────────────
    ws.merge_cells("A1:H1")
    title_cell = ws["A1"]
    title_cell.value = f"Test Cases — {project.name if project else ''}"
    title_cell.font = Font(bold=True, size=13, color=WHITE)
    title_cell.fill = PatternFill("solid", fgColor=NAVY)
    title_cell.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[1].height = 22

    ws.merge_cells("A2:H2")
    generated_at = format_in_user_zone(
        datetime.now(timezone.utc), current, "%Y-%m-%d %H:%M %Z",
    )
    ws["A2"].value = f"Exported {generated_at} by {current.username}"
    ws["A2"].font = Font(size=8, color="6B7280")
    ws["A2"].alignment = Alignment(indent=1)
    ws.row_dimensions[2].height = 14

    # ── Header row ───────────────────────────────────────────────────────────
    HEADERS = ["Suite", "Test Case", "Preconditions", "Description", "Step #", "Type", "Action", "Expected Result"]
    for col, h in enumerate(HEADERS, start=1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.font = Font(bold=True, size=9, color=WHITE)
        cell.fill = PatternFill("solid", fgColor="374151")  # gray-700
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=False)
        cell.border = thin_border
    ws.row_dimensions[3].height = 16

    STEP_TYPE_COLORS = {"setup": "DBEAFE", "teardown": "FFEDD5", "action": "F9FAFB"}

    data_row = 4
    alt = False

    for suite in suites:
        cases = db.query(TestCase).filter(TestCase.suite_id == suite.id).all()
        for tc in cases:
            steps = sorted(tc.steps, key=lambda s: s.order) if tc.steps else []
            row_count = max(len(steps), 1)
            row_bg = GRAY50 if alt else WHITE
            alt = not alt

            for i in range(row_count):
                step = steps[i] if i < len(steps) else None
                values = [
                    suite.name if i == 0 else "",
                    tc.name if i == 0 else "",
                    tc.preconditions or "" if i == 0 else "",
                    tc.description or "" if i == 0 else "",
                    step.order if step else "",
                    step.step_type if step else "",
                    step.action if step else "",
                    step.expected_result or "" if step else "",
                ]
                step_bg = STEP_TYPE_COLORS.get(step.step_type, row_bg) if step else row_bg

                for col, val in enumerate(values, start=1):
                    cell = ws.cell(row=data_row, column=col, value=val)
                    bg = step_bg if col >= 5 else row_bg
                    cell.fill = PatternFill("solid", fgColor=bg)
                    cell.font = Font(size=9, bold=(col <= 2 and i == 0))
                    cell.alignment = Alignment(
                        vertical="top",
                        wrap_text=(col in (3, 4, 7, 8)),
                        horizontal="center" if col == 5 else "left",
                    )
                    cell.border = thin_border
                ws.row_dimensions[data_row].height = 15
                data_row += 1

    # ── Column widths ─────────────────────────────────────────────────────────
    col_widths = [20, 28, 22, 30, 6, 10, 40, 30]
    for i, w in enumerate(col_widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.freeze_panes = "A4"

    buf = io.BytesIO()
    wb.save(buf)
    filename = f"cases_{project.name.replace(' ', '_') if project else id}.xlsx"
    return StreamingResponse(
        _stream_bytes(buf.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
