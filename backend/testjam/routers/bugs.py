"""Bug tracking endpoints.

Two routers mounted under `/api/v1`:

- `/projects/{id}/bugs` — list, create, report, lookup-by-number.
- `/bugs/{id}` and nested — detail, update, delete, status, comments,
  attachments, history.

Permissions:

- Create / comment / change status: any project member with role >= tester.
- Delete bug: project owner or admin.
- Delete own comment: author. Delete any comment: project owner or admin.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from testjam.auth.dependencies import (
    AuthContext,
    get_auth_context,
    get_current_user,
    require_project_access,
    require_writable_project_access,
)
from testjam.database import get_db
from testjam.models.bug import Bug, BugAttachment, BugComment, BugStatusHistory
from testjam.models.execution import TestExecution
from testjam.models.project import Project
from testjam.models.user import User
from testjam.schemas.bug import (
    BugAttachmentOut,
    BugCommentCreate,
    BugCommentOut,
    BugCommentUpdate,
    BugCreate,
    BugOut,
    BugStatusChange,
    BugStatusHistoryOut,
    BugUpdate,
    TERMINAL_BUG_STATUSES,
)
from fastapi.responses import HTMLResponse, StreamingResponse

from testjam.services import bug_events, bug_reports
from testjam.services.bug_numbering import next_bug_number
from testjam.services.environments import upsert_from_execution
from testjam.services.permissions import effective_role


WRITER_ROLES = {"tester", "owner"}
projects_router = APIRouter(prefix="/projects", tags=["Bugs"])
bugs_router = APIRouter(prefix="/bugs", tags=["Bugs"])


def _bug_out(bug: Bug) -> BugOut:
    return bug_events.bug_out(bug)


def _can_write_project(db: Session, user: User, project_id: int) -> bool:
    if user.is_admin:
        return True
    return effective_role(db, user.id, project_id) in WRITER_ROLES


def _can_delete_project_resource(db: Session, user: User, project_id: int) -> bool:
    if user.is_admin:
        return True
    return effective_role(db, user.id, project_id) == "owner"


def _require_writer(db: Session, user: User, project_id: int) -> None:
    if not _can_write_project(db, user, project_id):
        raise HTTPException(status_code=403, detail="Tester role or higher required")


def _require_owner_or_admin(db: Session, user: User, project_id: int) -> None:
    if not _can_delete_project_resource(db, user, project_id):
        raise HTTPException(status_code=403, detail="Project owner or admin required")


def _ensure_project_writable(db: Session, project_id: int) -> None:
    project = db.get(Project, project_id)
    if project is not None and project.archived_at is not None:
        raise HTTPException(status_code=409, detail="Project is archived")


def _get_bug(db: Session, bug_id: int) -> Bug:
    bug = db.get(Bug, bug_id)
    if bug is None:
        raise HTTPException(status_code=404, detail="Not found")
    return bug


def _authorize_bug_access(ctx: AuthContext, bug: Bug) -> None:
    if ctx.project_scope is not None and ctx.project_scope != bug.project_id:
        raise HTTPException(
            status_code=403, detail="API token is not authorized for this project"
        )


def _resolve_environment_from_execution(
    db: Session, project_id: int, execution_id: int | None, fallback: str | None
) -> str | None:
    if fallback:
        return upsert_from_execution(db, project_id, fallback)
    if execution_id is None:
        return None
    execution = db.get(TestExecution, execution_id)
    return execution.environment if execution else None


@projects_router.get("/{id}/bugs", response_model=list[BugOut])
def list_bugs(
    id: int,
    status: str | None = None,
    severity: str | None = None,
    version_id: int | None = None,
    assigned_to_id: int | None = None,
    tag: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    limit = min(limit, 200)
    query = db.query(Bug).filter(Bug.project_id == id)
    if status:
        query = query.filter(Bug.status == status)
    if severity:
        query = query.filter(Bug.severity == severity)
    if version_id is not None:
        query = query.filter(Bug.version_id == version_id)
    if assigned_to_id is not None:
        query = query.filter(Bug.assigned_to_id == assigned_to_id)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(func.lower(Bug.title).like(like))
    rows = query.order_by(Bug.number.desc()).offset(skip).limit(limit).all()
    if tag:
        rows = [bug for bug in rows if bug.tags and tag in bug.tags]
    return [_bug_out(bug) for bug in rows]


@projects_router.post(
    "/{id}/bugs", response_model=BugOut, status_code=status.HTTP_201_CREATED
)
def create_bug(
    id: int,
    body: BugCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    _require_writer(db, current, id)
    _ensure_project_writable(db, id)

    payload = body.model_dump()
    environment = _resolve_environment_from_execution(
        db, id, payload.get("execution_id"), payload.get("environment"),
    )
    bug = Bug(
        project_id=id,
        number=next_bug_number(db, id),
        title=payload["title"],
        description=payload.get("description"),
        severity=payload.get("severity", "medium"),
        status="open",
        tags=payload.get("tags") or None,
        result_id=payload.get("result_id"),
        execution_id=payload.get("execution_id"),
        version_id=payload.get("version_id"),
        environment=environment,
        assigned_to_id=payload.get("assigned_to_id"),
        created_by_id=current.id,
    )
    for attempt in range(5):
        try:
            db.add(bug)
            db.flush()
            break
        except IntegrityError:
            db.rollback()
            bug.number = next_bug_number(db, id)
    else:
        raise HTTPException(status_code=409, detail="Could not allocate bug number")

    history = BugStatusHistory(bug_id=bug.id, from_status=None, to_status="open", changed_by_id=current.id)
    db.add(history)
    db.commit()
    db.refresh(bug)
    bug_events.on_bug_created(db, bug, current, background)
    return _bug_out(bug)


@projects_router.get("/{id}/bugs/by-number/{number}", response_model=BugOut)
def get_bug_by_number(
    id: int,
    number: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    bug = db.query(Bug).filter(Bug.project_id == id, Bug.number == number).first()
    if bug is None:
        raise HTTPException(status_code=404, detail="Not found")
    return _bug_out(bug)


@bugs_router.get("/{id}", response_model=BugOut)
def get_bug(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    bug = _get_bug(db, id)
    _authorize_bug_access(ctx, bug)
    return _bug_out(bug)


@bugs_router.put("/{id}", response_model=BugOut)
def update_bug(
    id: int,
    body: BugUpdate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    bug = _get_bug(db, id)
    _require_writer(db, current, bug.project_id)
    _ensure_project_writable(db, bug.project_id)

    update_data = body.model_dump(exclude_unset=True)
    previous_assignee_id = bug.assigned_to_id
    if "environment" in update_data and update_data["environment"]:
        update_data["environment"] = upsert_from_execution(
            db, bug.project_id, update_data["environment"],
        )
    for field, value in update_data.items():
        setattr(bug, field, value)
    db.commit()
    db.refresh(bug)
    if "assigned_to_id" in update_data and bug.assigned_to_id != previous_assignee_id:
        bug_events.on_bug_assigned(db, bug, previous_assignee_id, current, background)
    else:
        bug_events.on_bug_updated(db, bug)
    return _bug_out(bug)


@bugs_router.post("/{id}/status", response_model=BugOut)
def change_bug_status(
    id: int,
    body: BugStatusChange,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    bug = _get_bug(db, id)
    _require_writer(db, current, bug.project_id)
    _ensure_project_writable(db, bug.project_id)

    previous_status = bug.status
    bug.status = body.status
    if body.status in TERMINAL_BUG_STATUSES and bug.resolved_at is None:
        bug.resolved_at = datetime.now(timezone.utc)
    elif body.status not in TERMINAL_BUG_STATUSES:
        bug.resolved_at = None
    history = BugStatusHistory(
        bug_id=bug.id,
        from_status=previous_status,
        to_status=body.status,
        note=body.note,
        changed_by_id=current.id,
    )
    db.add(history)
    db.commit()
    db.refresh(bug)
    db.refresh(history)
    bug_events.on_bug_status_changed(db, bug, history, current, background)
    return _bug_out(bug)


@bugs_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bug(
    id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    bug = _get_bug(db, id)
    _require_owner_or_admin(db, current, bug.project_id)
    project_id = bug.project_id
    bug_id = bug.id
    db.delete(bug)
    db.commit()
    bug_events.on_bug_deleted(project_id, bug_id)


@bugs_router.get("/{id}/comments", response_model=list[BugCommentOut])
def list_comments(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    bug = _get_bug(db, id)
    _authorize_bug_access(ctx, bug)
    return list(bug.comments)


@bugs_router.post(
    "/{id}/comments", response_model=BugCommentOut, status_code=status.HTTP_201_CREATED
)
def add_comment(
    id: int,
    body: BugCommentCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    bug = _get_bug(db, id)
    _require_writer(db, current, bug.project_id)
    _ensure_project_writable(db, bug.project_id)
    comment = BugComment(bug_id=bug.id, body=body.body, created_by_id=current.id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    bug_events.on_bug_comment_added(comment)
    return comment


@bugs_router.put("/{id}/comments/{comment_id}", response_model=BugCommentOut)
def update_comment(
    id: int,
    comment_id: int,
    body: BugCommentUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    comment = db.get(BugComment, comment_id)
    if comment is None or comment.bug_id != id:
        raise HTTPException(status_code=404, detail="Not found")
    if comment.created_by_id != current.id and not current.is_admin:
        raise HTTPException(status_code=403, detail="Only the author or admin can edit")
    comment.body = body.body
    db.commit()
    db.refresh(comment)
    bug_events.on_bug_comment_updated(comment)
    return comment


@bugs_router.delete("/{id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    comment = db.get(BugComment, comment_id)
    if comment is None or comment.bug_id != id:
        raise HTTPException(status_code=404, detail="Not found")
    bug = comment.bug
    is_author = comment.created_by_id == current.id
    if not is_author and not _can_delete_project_resource(db, current, bug.project_id):
        raise HTTPException(status_code=403, detail="Only the author or project owner can delete")
    db.delete(comment)
    db.commit()
    bug_events.on_bug_comment_deleted(bug.id, comment_id)


@bugs_router.get("/{id}/history", response_model=list[BugStatusHistoryOut])
def list_history(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    bug = _get_bug(db, id)
    _authorize_bug_access(ctx, bug)
    return list(bug.history)


@bugs_router.get("/{id}/attachments", response_model=list[BugAttachmentOut])
def list_attachments(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    bug = _get_bug(db, id)
    _authorize_bug_access(ctx, bug)
    return list(bug.attachments)


@projects_router.get("/{id}/bugs/report")
def download_bug_report(
    id: int,
    format: str = "html",
    version_id: int | None = None,
    environment: str | None = None,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    project = db.get(Project, id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if format == "xlsx":
        payload = bug_reports.render_xlsx(db, project, current, version_id, environment)
        return StreamingResponse(
            iter([payload]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="bugs-{project.name}.xlsx"'},
        )
    if format != "html":
        raise HTTPException(status_code=400, detail="format must be 'html' or 'xlsx'")
    html = bug_reports.render_html(db, project, current, version_id, environment)
    return HTMLResponse(content=html)
