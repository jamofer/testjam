"""Manage and render public share tokens for reports.

A `PublicReport` row binds an opaque token to a specific report (bug-report
filtered by version+environment, or a single execution). Anyone holding the
raw token can fetch the rendered HTML via `/public/reports/{token}` without
authenticating. Hashes (sha256) are stored; raw tokens are returned only on
creation.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from testjam.models.execution import TestExecution
from testjam.models.project import Project
from testjam.models.public_report import PUBLIC_REPORT_KINDS, PublicReport
from testjam.models.user import User
from testjam.services import bug_reports, execution_reports
from testjam.services.settings import get_settings as get_app_settings


class PublicReportError(Exception):
    """Raised when a public report payload is invalid or unrenderable."""


def issue(
    db: Session,
    *,
    project: Project,
    kind: str,
    creator: User,
    label: str | None = None,
    execution_id: int | None = None,
    version_id: int | None = None,
    environment: str | None = None,
    expires_at: datetime | None = None,
) -> tuple[PublicReport, str]:
    if kind not in PUBLIC_REPORT_KINDS:
        raise PublicReportError(f"unknown kind '{kind}'")
    if kind == "execution":
        if execution_id is None:
            raise PublicReportError("execution_id is required for kind='execution'")
        execution = db.get(TestExecution, execution_id)
        if execution is None or execution.project_id != project.id:
            raise PublicReportError("execution not found in this project")

    raw, token_hash = PublicReport.generate_token()
    row = PublicReport(
        project_id=project.id,
        kind=kind,
        token_hash=token_hash,
        label=label,
        execution_id=execution_id,
        version_id=version_id,
        environment=environment,
        created_by_id=creator.id,
        expires_at=expires_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row, raw


def list_for_project(db: Session, project_id: int) -> list[PublicReport]:
    return (
        db.query(PublicReport)
        .filter(PublicReport.project_id == project_id)
        .order_by(PublicReport.created_at.desc())
        .all()
    )


def revoke(db: Session, report: PublicReport) -> PublicReport:
    if report.revoked_at is None:
        report.revoked_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(report)
    return report


def lookup_active(db: Session, raw_token: str) -> PublicReport | None:
    if not raw_token:
        return None
    token_hash = PublicReport.hash_token(raw_token)
    row = (
        db.query(PublicReport)
        .filter(PublicReport.token_hash == token_hash)
        .first()
    )
    if row is None or not is_active(row):
        return None
    return row


def is_active(report: PublicReport) -> bool:
    if report.revoked_at is not None:
        return False
    if report.expires_at is None:
        return True
    expires_at = report.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > datetime.now(timezone.utc)


def render(db: Session, report: PublicReport, *, base_url: str) -> str:
    if report.kind == "bug_report":
        project = db.get(Project, report.project_id)
        if project is None:
            raise PublicReportError("project not found")
        return bug_reports.render_html(
            db,
            project,
            None,
            version_id=report.version_id,
            environment=report.environment,
            viewer_label=_viewer_label(report),
        )
    if report.kind == "execution":
        execution = execution_reports.load_execution_for_report(db, report.execution_id or 0)
        if execution is None:
            raise PublicReportError("execution not found")
        return execution_reports.render_html(
            db,
            execution,
            base_url=base_url,
            viewer=None,
            viewer_label=_viewer_label(report),
            app_settings=get_app_settings(db),
        )
    raise PublicReportError(f"unsupported kind '{report.kind}'")


def record_view(db: Session, report: PublicReport) -> None:
    report.last_viewed_at = datetime.now(timezone.utc)
    report.view_count = (report.view_count or 0) + 1
    db.commit()


def url_path_for(report: PublicReport, raw_token: str) -> str:
    return f"/api/v1/public/reports/{raw_token}"


def _viewer_label(report: PublicReport) -> str:
    return report.label or "shared link"
