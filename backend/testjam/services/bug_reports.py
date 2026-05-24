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
from testjam.models.custom_field import CustomFieldDefinition
from testjam.models.project import Project
from testjam.models.user import User
from testjam.models.version import ProjectVersion
from testjam.schemas.mention import MentionTokenIn
from testjam.services.integrations.markdown_to_html import to_html as markdown_to_html
from testjam.services.mention_resolver import resolve as resolve_mentions
from testjam.services.mentions import Mention, enrich_html_with_mentions, parse as parse_mentions
from testjam.services.timezones import format_in_user_zone, user_zone_label


def _mention_cache_key(mention_or_token) -> tuple:
    return (
        mention_or_token.kind,
        getattr(mention_or_token, "slug", None),
        getattr(mention_or_token, "id", None),
        tuple(getattr(mention_or_token, "sub_ids", ()) or ()),
    )


def _collect_unique_tokens(bugs: list[Bug]) -> list[MentionTokenIn]:
    seen: dict[tuple, MentionTokenIn] = {}
    for bug in bugs:
        texts = [bug.description or ""]
        texts.extend((comment.body or "") for comment in bug.comments)
        for text in texts:
            for mention in parse_mentions(text):
                key = _mention_cache_key(mention)
                if key in seen:
                    continue
                seen[key] = MentionTokenIn(
                    kind=mention.kind, slug=mention.slug,
                    id=mention.id, sub_ids=list(mention.sub_ids),
                )
    return list(seen.values())


def _make_rich_renderer(db: Session, project_id: int, bugs: list[Bug]):
    tokens = _collect_unique_tokens(bugs)
    resolved = resolve_mentions(db, project_id, tokens) if tokens else []
    cache = {_mention_cache_key(token): result for token, result in zip(tokens, resolved)}

    def label_for(mention: Mention) -> str:
        cached = cache.get(_mention_cache_key(mention))
        if cached is not None and cached.accessible and cached.label:
            return cached.label
        return mention.raw

    def render_rich(text: str) -> str:
        return enrich_html_with_mentions(markdown_to_html(text), label_for=label_for)

    return render_rich


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _active_bug_custom_field_definitions(
    db: Session, project_id: int
) -> list[CustomFieldDefinition]:
    return (
        db.query(CustomFieldDefinition)
        .filter(
            CustomFieldDefinition.project_id == project_id,
            CustomFieldDefinition.entity_type == "bug",
            CustomFieldDefinition.archived_at.is_(None),
        )
        .order_by(
            CustomFieldDefinition.position.asc(),
            CustomFieldDefinition.id.asc(),
        )
        .all()
    )


def _format_custom_field_plain(definition: CustomFieldDefinition, value) -> str:
    if value is None or value == "":
        return ""
    if definition.type == "bool":
        return "Yes" if value else "No"
    if definition.type == "single_select":
        option = _option_for_value(definition, value)
        return (option.get("label") if option else None) or str(value)
    if definition.type == "multi_select":
        if not isinstance(value, list):
            return str(value)
        return ", ".join(_option_label(definition, item) for item in value)
    return str(value)


def _option_for_value(definition: CustomFieldDefinition, value) -> dict | None:
    for option in definition.options or []:
        if option.get("value") == value:
            return option
    return None


def _option_label(definition: CustomFieldDefinition, value) -> str:
    option = _option_for_value(definition, value)
    return (option.get("label") if option else None) or str(value)


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
    user: User | None,
    version_id: int | None = None,
    environment: str | None = None,
    *,
    viewer_label: str | None = None,
) -> str:
    bugs = _query_bugs(db, project.id, version_id, environment)
    bugs.sort(key=lambda bug: (SEVERITY_ORDER.get(bug.severity, 99), bug.number))
    custom_field_definitions = _active_bug_custom_field_definitions(db, project.id)

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

    actor_label = user.username if user is not None else (viewer_label or "shared link")
    render_rich = _make_rich_renderer(db, project.id, bugs)
    return _build_html(
        title, bugs, generated_at, timezone_label, user, actor_label,
        custom_field_definitions, render_rich,
    )


def render_xlsx(
    db: Session,
    project: Project,
    user: User,
    version_id: int | None = None,
    environment: str | None = None,
) -> bytes:
    bugs = _query_bugs(db, project.id, version_id, environment)
    bugs.sort(key=lambda bug: (SEVERITY_ORDER.get(bug.severity, 99), bug.number))
    custom_field_definitions = _active_bug_custom_field_definitions(db, project.id)

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Bugs"
    timezone_label = user_zone_label(user)

    header = [
        "#", "Title", "Severity", "Status", "Tags", "Version",
        "Environment", "Assigned to", "Created by",
        f"Created ({timezone_label})", f"Resolved ({timezone_label})",
    ]
    header.extend(definition.label for definition in custom_field_definitions)
    sheet.append(header)
    for cell in sheet[1]:
        cell.font = Font(bold=True)

    for bug in bugs:
        row = [
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
        ]
        row.extend(
            _format_custom_field_plain(definition, (bug.custom_fields or {}).get(definition.key))
            for definition in custom_field_definitions
        )
        sheet.append(row)

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
    title: str,
    bugs: list[Bug],
    generated_at: str,
    timezone_label: str,
    user: User | None,
    actor_label: str,
    custom_field_definitions: list[CustomFieldDefinition],
    render_rich,
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
        rendered = "\n".join(
            _render_row(bug, user, custom_field_definitions, render_rich) for bug in rows
        )
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
        ".comment-body { font-size: 13px; color: #1f2937; }\n"
        ".comment-body p { margin: 0 0 6px; }\n"
        ".comment-body p:last-child { margin-bottom: 0; }\n"
        ".comment-body pre { background: #f3f4f6; padding: 8px; border-radius: 4px; overflow-x: auto; }\n"
        ".comment-body code { background: #f3f4f6; padding: 1px 4px; border-radius: 3px; }\n"
        ".bug-description p { margin: 4px 0; }\n"
        ".bug-description pre { background: #f3f4f6; padding: 8px; border-radius: 4px; overflow-x: auto; }\n"
        ".bug-description code { background: #f3f4f6; padding: 1px 4px; border-radius: 3px; }\n"
        ".mention { display: inline-block; padding: 0 4px; margin: 0 1px; border-radius: 3px; "
        "font-size: 12px; font-weight: 500; border: 1px solid; line-height: 1.4; }\n"
        ".mention-user { background: #fff1f2; color: #be123c; border-color: #fecdd3; }\n"
        ".mention-bug { background: #fef2f2; color: #b91c1c; border-color: #fecaca; }\n"
        ".mention-execution { background: #f0f9ff; color: #0369a1; border-color: #bae6fd; }\n"
        ".mention-result, .mention-case { background: #fffbeb; color: #b45309; border-color: #fde68a; }\n"
        ".mention-step_result { background: #f3f4f6; color: #374151; border-color: #e5e7eb; }\n"
        ".cf-row { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 6px; }\n"
        ".cf-chip { font-size: 11px; padding: 2px 8px; border-radius: 10px; "
        "background: #f3f4f6; color: #374151; }\n"
        ".cf-chip-label { color: #6b7280; margin-right: 4px; }\n"
        ".empty { color: #9ca3af; font-style: italic; }\n"
        "</style>\n"
        "</head>\n<body>\n"
        f"<h1>{e(title)}</h1>\n"
        f"<p class='meta'>Generated {e(generated_at)} by {e(actor_label)}</p>\n"
        + "\n".join(sections)
        + "\n</body>\n</html>\n"
    )


def _render_row(
    bug: Bug,
    user: User | None,
    custom_field_definitions: list[CustomFieldDefinition],
    render_rich,
) -> str:
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
    description_block = (
        f"<div class='bug-description'>{render_rich(description)}</div>"
        if description
        else ""
    )
    return (
        "<li>"
        f"<span class='bug-number'>#{bug.number}</span>"
        + " ".join(parts)
        + f"<div class='bug-meta'>{meta_line}</div>"
        + description_block
        + _render_custom_fields_html(bug, custom_field_definitions)
        + _render_discussion(bug, user, render_rich)
        + "</li>"
    )


def _render_custom_fields_html(
    bug: Bug, definitions: list[CustomFieldDefinition]
) -> str:
    if not definitions:
        return ""
    e = html_lib.escape
    values = bug.custom_fields or {}
    chips: list[str] = []
    for definition in definitions:
        if definition.key not in values:
            continue
        raw = values[definition.key]
        if raw is None or raw == "":
            continue
        chips.extend(_render_custom_field_chip(definition, raw))
    if not chips:
        return ""
    return f"<div class='cf-row'>{''.join(chips)}</div>"


def _render_custom_field_chip(
    definition: CustomFieldDefinition, value
) -> list[str]:
    e = html_lib.escape
    label_html = f"<span class='cf-chip-label'>{e(definition.label)}:</span>"
    if definition.type == "single_select":
        option = _option_for_value(definition, value)
        chip_label = (option.get("label") if option else None) or str(value)
        color = option.get("color") if option else None
        style = _chip_color_style(color)
        return [
            f"<span class='cf-chip'{style}>{label_html} {e(chip_label)}</span>"
        ]
    if definition.type == "multi_select":
        if not isinstance(value, list) or not value:
            return []
        chips = [f"<span class='cf-chip'>{label_html}</span>"]
        for item in value:
            option = _option_for_value(definition, item)
            chip_label = (option.get("label") if option else None) or str(item)
            color = option.get("color") if option else None
            style = _chip_color_style(color)
            chips.append(f"<span class='cf-chip'{style}>{e(chip_label)}</span>")
        return chips
    plain = _format_custom_field_plain(definition, value)
    return [f"<span class='cf-chip'>{label_html} {e(plain)}</span>"]


def _chip_color_style(color: str | None) -> str:
    if not color:
        return ""
    safe = html_lib.escape(color, quote=True)
    return f" style=\"background:{safe};color:#fff;\""


def _render_discussion(bug: Bug, user: User | None, render_rich) -> str:
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
            f"<div class='comment-body'>{render_rich(comment.body or '')}</div>"
            "</li>"
        )
    return (
        "<div class='discussion'>"
        f"<h3>Discussion ({len(bug.comments)})</h3>"
        f"<ol>{''.join(items)}</ol>"
        "</div>"
    )


def render_release_notes_html(db: Session, project: Project, user: User) -> str:
    bugs = _query_release_notes_bugs(db, project.id)
    by_version_id: dict[int | None, list[Bug]] = {}
    for bug in bugs:
        by_version_id.setdefault(bug.fixed_in_version_id, []).append(bug)

    versions = _order_versions_for_release_notes(db, project.id, by_version_id.keys())
    generated_at = format_in_user_zone(
        datetime.now(timezone.utc), user, "%Y-%m-%d %H:%M %Z",
    )
    title = f"Release notes — {project.name}"
    return _build_release_notes_html(title, versions, by_version_id, generated_at, user)


def _query_release_notes_bugs(db: Session, project_id: int) -> list[Bug]:
    return (
        db.query(Bug)
        .options(
            selectinload(Bug.assigned_to),
            selectinload(Bug.fixed_in_version),
        )
        .filter(
            Bug.project_id == project_id,
            Bug.status == "resolved",
        )
        .order_by(Bug.number.asc())
        .all()
    )


def _order_versions_for_release_notes(
    db: Session, project_id: int, seen_ids,
) -> list[ProjectVersion | None]:
    relevant = [version_id for version_id in seen_ids if version_id is not None]
    rows: list[ProjectVersion] = []
    if relevant:
        rows = (
            db.query(ProjectVersion)
            .filter(
                ProjectVersion.project_id == project_id,
                ProjectVersion.id.in_(relevant),
            )
            .order_by(
                ProjectVersion.release_date.desc().nulls_last(),
                ProjectVersion.created_at.desc(),
            )
            .all()
        )
    ordered: list[ProjectVersion | None] = list(rows)
    if None in seen_ids:
        ordered.append(None)
    return ordered


def _build_release_notes_html(
    title: str,
    versions: list[ProjectVersion | None],
    by_version_id: dict[int | None, list[Bug]],
    generated_at: str,
    user: User,
) -> str:
    e = html_lib.escape
    sections: list[str] = []
    for version in versions:
        version_id = version.id if version is not None else None
        bugs = by_version_id.get(version_id, [])
        if not bugs:
            continue
        heading = e(version.name) if version is not None else "Unassigned"
        date_line = ""
        if version is not None and version.release_date is not None:
            date_line = f" <span class='version-date'>{e(version.release_date.isoformat())}</span>"
        sections.append(
            f"<section class='version'>"
            f"<h2>{heading}{date_line} <span class='count'>({len(bugs)})</span></h2>"
            f"<ul>{''.join(_render_release_notes_row(bug) for bug in bugs)}</ul>"
            "</section>"
        )
    if not sections:
        sections.append("<p class='empty'>No resolved bugs to report.</p>")

    return (
        "<!doctype html>\n<html lang='en'>\n<head>\n"
        "<meta charset='utf-8' />\n"
        f"<title>{e(title)}</title>\n"
        "<style>\n"
        "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; "
        "max-width: 960px; margin: 32px auto; padding: 0 16px; color: #1f2937; }\n"
        "h1 { margin: 0 0 4px; font-size: 22px; }\n"
        ".meta { color: #6b7280; font-size: 13px; margin-bottom: 24px; }\n"
        ".version { margin-bottom: 32px; }\n"
        ".version h2 { font-size: 18px; margin-bottom: 12px; padding-bottom: 4px; "
        "border-bottom: 1px solid #e5e7eb; }\n"
        ".version-date { color: #6b7280; font-size: 13px; font-weight: normal; margin-left: 6px; }\n"
        ".count { color: #9ca3af; font-size: 14px; font-weight: normal; }\n"
        "ul { list-style: none; padding-left: 0; }\n"
        "li { padding: 8px 0; border-bottom: 1px solid #f3f4f6; }\n"
        ".bug-number { font-family: monospace; color: #6b7280; margin-right: 6px; }\n"
        ".bug-severity { display: inline-block; padding: 1px 6px; border-radius: 4px; "
        "font-size: 11px; margin-left: 6px; }\n"
        ".sev-critical { background: #fee2e2; color: #991b1b; }\n"
        ".sev-high { background: #ffedd5; color: #9a3412; }\n"
        ".sev-medium { background: #fef3c7; color: #92400e; }\n"
        ".sev-low { background: #f3f4f6; color: #4b5563; }\n"
        ".empty { color: #9ca3af; font-style: italic; }\n"
        "</style>\n"
        "</head>\n<body>\n"
        f"<h1>{e(title)}</h1>\n"
        f"<p class='meta'>Generated {e(generated_at)} by {e(user.username)}</p>\n"
        + "\n".join(sections)
        + "\n</body>\n</html>\n"
    )


def _render_release_notes_row(bug: Bug) -> str:
    e = html_lib.escape
    severity_class = f"sev-{bug.severity}"
    return (
        "<li>"
        f"<span class='bug-number'>#{bug.number}</span>"
        f"<strong>{e(bug.title)}</strong>"
        f"<span class='bug-severity {severity_class}'>{e(bug.severity)}</span>"
        "</li>"
    )
