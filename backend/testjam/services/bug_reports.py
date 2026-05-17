"""Bug report generators (HTML + XLSX).

Filtering: by `version_id` and / or `environment`. Output groups bugs by
severity so the report doubles as release notes (critical first).
PDF is produced client-side from the HTML view, mirroring the execution
export flow in ``hooks/useExportExecution``.
"""
from __future__ import annotations

import html as html_lib
import io
from datetime import datetime, timezone

import openpyxl
from openpyxl.styles import Font
from sqlalchemy.orm import Session, selectinload

from testjam.models.bug import Bug, BugComment
from testjam.models.project import Project
from testjam.models.user import User
from testjam.services.timezones import format_in_user_zone, user_zone_label


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _query_bugs(
    db: Session, project_id: int, version_id: int | None, environment: str | None
):
    query = (
        db.query(Bug)
        .options(
            selectinload(Bug.assigned_to),
            selectinload(Bug.created_by),
            selectinload(Bug.version),
            selectinload(Bug.comments).selectinload(BugComment.created_by),
        )
        .filter(Bug.project_id == project_id)
    )
    if version_id is not None:
        query = query.filter(Bug.version_id == version_id)
    if environment:
        query = query.filter(Bug.environment == environment)
    return query.order_by(Bug.number.asc()).all()


def render_html(
    db: Session,
    project: Project,
    user: User,
    version_id: int | None = None,
    environment: str | None = None,
) -> str:
    bugs = _query_bugs(db, project.id, version_id, environment)
    bugs.sort(key=lambda bug: (SEVERITY_ORDER.get(bug.severity, 99), bug.number))

    timezone_label = user_zone_label(user)
    generated_at = format_in_user_zone(
        datetime.now(timezone.utc), user, "%Y-%m-%d %H:%M %Z",
    )
    title_parts = [f"Bug report — {project.name}"]
    if version_id is not None:
        version_name = next((bug.version.name for bug in bugs if bug.version), None)
        if version_name:
            title_parts.append(f"version {version_name}")
    if environment:
        title_parts.append(f"environment {environment}")
    title = " · ".join(title_parts)

    return _build_html(title, bugs, generated_at, timezone_label, user)


def render_xlsx(
    db: Session,
    project: Project,
    user: User,
    version_id: int | None = None,
    environment: str | None = None,
) -> bytes:
    bugs = _query_bugs(db, project.id, version_id, environment)
    bugs.sort(key=lambda bug: (SEVERITY_ORDER.get(bug.severity, 99), bug.number))

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Bugs"
    timezone_label = user_zone_label(user)

    header = [
        "#", "Title", "Severity", "Status", "Tags", "Version",
        "Environment", "Assigned to", "Created by",
        f"Created ({timezone_label})", f"Resolved ({timezone_label})",
    ]
    sheet.append(header)
    for cell in sheet[1]:
        cell.font = Font(bold=True)

    for bug in bugs:
        sheet.append([
            f"#{bug.number}",
            bug.title,
            bug.severity,
            bug.status,
            ", ".join(bug.tags or []),
            bug.version.name if bug.version else "",
            bug.environment or "",
            bug.assigned_to.username if bug.assigned_to else "",
            bug.created_by.username if bug.created_by else "",
            format_in_user_zone(bug.created_at, user, "%Y-%m-%d %H:%M"),
            format_in_user_zone(bug.resolved_at, user, "%Y-%m-%d %H:%M"),
        ])

    sheet.append([])
    sheet.append([
        f"Exported {format_in_user_zone(datetime.now(timezone.utc), user, '%Y-%m-%d %H:%M %Z')} "
        f"by {user.username}",
    ])

    _append_comments_sheet(workbook, bugs, user, timezone_label)

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _append_comments_sheet(workbook, bugs: list[Bug], user: User, timezone_label: str) -> None:
    sheet = workbook.create_sheet("Comments")
    header = ["Bug #", "Bug title", "Author", f"Created ({timezone_label})", "Body"]
    sheet.append(header)
    for cell in sheet[1]:
        cell.font = Font(bold=True)

    for bug in bugs:
        for comment in bug.comments:
            sheet.append([
                f"#{bug.number}",
                bug.title,
                comment.created_by.username if comment.created_by else "",
                format_in_user_zone(comment.created_at, user, "%Y-%m-%d %H:%M"),
                comment.body,
            ])


def _build_html(
    title: str, bugs: list[Bug], generated_at: str, timezone_label: str, user: User,
) -> str:
    e = html_lib.escape
    groups: dict[str, list[Bug]] = {}
    for bug in bugs:
        groups.setdefault(bug.severity, []).append(bug)

    sections: list[str] = []
    for severity in ("critical", "high", "medium", "low"):
        rows = groups.get(severity, [])
        if not rows:
            continue
        rendered = "\n".join(_render_row(bug, user) for bug in rows)
        sections.append(
            f"<section class='severity severity-{severity}'>"
            f"<h2>{severity.title()} ({len(rows)})</h2>"
            f"<ul>{rendered}</ul></section>"
        )

    if not sections:
        sections.append("<p class='empty'>No bugs match this filter.</p>")

    return (
        "<!doctype html>\n<html lang='en'>\n<head>\n"
        "<meta charset='utf-8' />\n"
        f"<title>{e(title)}</title>\n"
        "<style>\n"
        "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; "
        "max-width: 960px; margin: 32px auto; padding: 0 16px; color: #1f2937; }\n"
        "h1 { margin: 0 0 4px; font-size: 22px; }\n"
        ".meta { color: #6b7280; font-size: 13px; margin-bottom: 24px; }\n"
        ".severity { margin-bottom: 32px; }\n"
        ".severity h2 { font-size: 16px; margin-bottom: 12px; padding-bottom: 4px; "
        "border-bottom: 1px solid #e5e7eb; }\n"
        ".severity-critical h2 { color: #b91c1c; }\n"
        ".severity-high h2 { color: #c2410c; }\n"
        ".severity-medium h2 { color: #b45309; }\n"
        ".severity-low h2 { color: #4b5563; }\n"
        "ul { list-style: none; padding-left: 0; }\n"
        "li { padding: 12px 0; border-bottom: 1px solid #f3f4f6; }\n"
        ".bug-number { font-family: monospace; color: #6b7280; margin-right: 6px; }\n"
        ".bug-status { display: inline-block; padding: 2px 8px; border-radius: 12px; "
        "font-size: 11px; background: #e5e7eb; color: #374151; margin-left: 8px; }\n"
        ".bug-meta { font-size: 12px; color: #6b7280; margin-top: 4px; }\n"
        ".discussion { margin-top: 10px; padding: 10px 12px; background: #f9fafb; "
        "border-left: 3px solid #d1d5db; border-radius: 4px; }\n"
        ".discussion h3 { margin: 0 0 8px; font-size: 12px; color: #4b5563; "
        "text-transform: uppercase; letter-spacing: 0.04em; }\n"
        ".discussion ol { list-style: none; padding-left: 0; margin: 0; }\n"
        ".discussion li { padding: 6px 0; border-bottom: 1px dashed #e5e7eb; }\n"
        ".discussion li:last-child { border-bottom: none; }\n"
        ".comment-meta { font-size: 11px; color: #6b7280; margin-bottom: 2px; }\n"
        ".comment-body { font-size: 13px; color: #1f2937; white-space: pre-wrap; }\n"
        ".empty { color: #9ca3af; font-style: italic; }\n"
        "</style>\n"
        "</head>\n<body>\n"
        f"<h1>{e(title)}</h1>\n"
        f"<p class='meta'>Generated {e(generated_at)} by {e(user.username)}</p>\n"
        + "\n".join(sections)
        + "\n</body>\n</html>\n"
    )


def _render_row(bug: Bug, user: User) -> str:
    e = html_lib.escape
    assignee = bug.assigned_to.username if bug.assigned_to else "unassigned"
    parts = [
        f"<strong>{e(bug.title)}</strong>",
        f"<span class='bug-status'>{e(bug.status)}</span>",
    ]
    meta_bits = [
        f"version {e(bug.version.name)}" if bug.version else None,
        f"env {e(bug.environment)}" if bug.environment else None,
        f"assignee {e(assignee)}",
    ]
    meta_line = " · ".join(part for part in meta_bits if part)
    description = (bug.description or "").strip()
    description_block = f"<p>{e(description)}</p>" if description else ""
    return (
        "<li>"
        f"<span class='bug-number'>#{bug.number}</span>"
        + " ".join(parts)
        + f"<div class='bug-meta'>{meta_line}</div>"
        + description_block
        + _render_discussion(bug, user)
        + "</li>"
    )


def _render_discussion(bug: Bug, user: User) -> str:
    if not bug.comments:
        return ""
    e = html_lib.escape
    items = []
    for comment in bug.comments:
        author = comment.created_by.username if comment.created_by else "unknown"
        when = format_in_user_zone(comment.created_at, user, "%Y-%m-%d %H:%M")
        items.append(
            "<li>"
            f"<div class='comment-meta'>{e(author)} · {e(when)}</div>"
            f"<div class='comment-body'>{e(comment.body)}</div>"
            "</li>"
        )
    return (
        "<div class='discussion'>"
        f"<h3>Discussion ({len(bug.comments)})</h3>"
        f"<ol>{''.join(items)}</ol>"
        "</div>"
    )
