"""Public-share tokens for reports (bug reports + execution reports).

Two routers:

- `/projects/{id}/public-reports` — auth'd CRUD (owner or admin only).
- `/public/reports/{token}` — anonymous read-only HTML render.
"""
from __future__ import annotations

from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user, require_project_access
from testjam.database import get_db
from testjam.models.project import Project
from testjam.models.public_report import PublicReport
from testjam.models.user import User
from testjam.schemas.public_report import (
    PublicReportCreate,
    PublicReportCreated,
    PublicReportOut,
)
from testjam.services import public_reports
from testjam.services.permissions import effective_role
from testjam.services.settings import get_settings as get_app_settings


projects_router = APIRouter(prefix="/projects", tags=["PublicReports"])
public_router = APIRouter(prefix="/public", tags=["PublicReports"])


def _require_owner_or_admin(db: Session, user: User, project_id: int) -> None:
    if user.is_admin:
        return
    if effective_role(db, user.id, project_id) == "owner":
        return
    raise HTTPException(status_code=403, detail="Project owner or admin required")


def _get_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@projects_router.get("/{id}/public-reports", response_model=list[PublicReportOut])
def list_public_reports(
    id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    _require_owner_or_admin(db, current, id)
    return public_reports.list_for_project(db, id)


@projects_router.post(
    "/{id}/public-reports",
    response_model=PublicReportCreated,
    status_code=status.HTTP_201_CREATED,
)
def create_public_report(
    id: int,
    body: PublicReportCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    _require_owner_or_admin(db, current, id)
    project = _get_project(db, id)
    try:
        row, raw_token = public_reports.issue(
            db,
            project=project,
            kind=body.kind,
            creator=current,
            label=body.label,
            execution_id=body.execution_id,
            version_id=body.version_id,
            environment=body.environment,
            expires_at=body.expires_at,
        )
    except public_reports.PublicReportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    out = PublicReportCreated.model_validate(row, from_attributes=True).model_copy(
        update={
            "token": raw_token,
            "url_path": public_reports.url_path_for(row, raw_token),
        }
    )
    return out


@projects_router.delete(
    "/{id}/public-reports/{public_report_id}", status_code=status.HTTP_204_NO_CONTENT
)
def revoke_public_report(
    id: int,
    public_report_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    _require_owner_or_admin(db, current, id)
    row = db.get(PublicReport, public_report_id)
    if row is None or row.project_id != id:
        raise HTTPException(status_code=404, detail="Not found")
    public_reports.revoke(db, row)
    return None


@public_router.get("/reports/{token}", include_in_schema=True)
def view_public_report(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    row = public_reports.lookup_active(db, token)
    if row is None:
        raise HTTPException(status_code=404, detail="Report not available")

    app_settings = get_app_settings(db)
    base_url = _public_base_url(request, app_settings.site_url)
    try:
        html = public_reports.render(db, row, base_url=base_url)
    except public_reports.PublicReportError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc

    public_reports.record_view(db, row)
    return HTMLResponse(content=html)


def _public_base_url(request: Request, configured_site_url: str | None) -> str:
    if configured_site_url:
        return configured_site_url.rstrip("/")
    referer = request.headers.get("referer", "")
    if referer:
        try:
            parsed = urlparse(referer)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            pass
    return f"{request.url.scheme}://{request.url.netloc}"
